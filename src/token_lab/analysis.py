# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Analysis of a validated result document (pure functions, no I/O)."""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from .stats import bootstrap_median_diff, cv, holm, median_iqr, paired_compare
from .tokens import throughput_tps

# Planned request counts from research/protocol.md section 10 (v1.0, frozen 2026-11-24).
PLANNED_REQUESTS = {"EXP-001": 4500, "EXP-002": 60, "EXP-003": 3000}


def _per_item(records: list[dict], key: str) -> dict[str, float]:
    by: dict[str, list[float]] = defaultdict(list)
    for r in records:
        by[r["item_id"]].append(r[key])
    return {k: float(np.mean(v)) for k, v in by.items()}


def _median_or_none(values: list[float]):
    vals = [v for v in values if v is not None]
    return median_iqr(vals) if vals else None


def arm_summaries(doc: dict) -> list[dict]:
    arms = [a["arm_id"] for a in doc["config"]["arms"]]
    out = []
    for arm in arms:
        recs = [r for r in doc["records"] if r["arm"] == arm]
        if not recs:
            out.append({"arm": arm, "n_records": 0})
            continue
        model = recs[0]["model"]
        acc_s = float(np.mean(list(_per_item(recs, "correct_strict").values())))
        acc_l = float(np.mean(list(_per_item(recs, "correct_lenient").values())))
        errors = sum(1 for r in recs if r["error"])
        fmt_fail = sum(1 for r in recs if not r["error"] and r["extracted_strict"] is None)
        fmt_fail_l = sum(1 for r in recs if not r["error"] and r["extracted_lenient"] is None)
        # latency: per-item median over repetitions, then summarised over items
        lat_by: dict[str, list[float]] = defaultdict(list)
        for r in recs:
            if r["latency_ms"] is not None:
                lat_by[r["item_id"]].append(r["latency_ms"])
        item_lat = [float(np.median(v)) for v in lat_by.values()]
        ttft = _median_or_none([r["ttft_ms"] for r in recs])
        dec = _median_or_none([throughput_tps(r["eval_count"], r["eval_duration_ns"]) for r in recs])
        pre = _median_or_none([throughput_tps(r["prompt_eval_count"], r["prompt_eval_duration_ns"]) for r in recs])
        # determinism: identical response text across repetitions per item
        resp_by: dict[str, set] = defaultdict(set)
        for r in recs:
            resp_by[r["item_id"]].add(r["response"])
        determ = float(np.mean([len(s) == 1 for s in resp_by.values()]))
        blocks = [b for b in doc["blocks"] if b["arm"] == arm]
        # Primary memory metric (amendment A2, owner-approved 2026-11-24):
        # runtime-reported model memory, the largest ``size`` that /api/ps reports
        # for this arm's model at the end of its blocks. Runtime-reported, not
        # sampled; RSS, system used memory and swap stay secondary.
        rt_sizes = [m.get("size") for b in blocks for m in (b.get("loaded_after") or [])
                    if m.get("name") == model and isinstance(m.get("size"), (int, float))]
        rss = [b["memory"].get("peak_rss_mib") for b in blocks if b["memory"].get("peak_rss_mib") is not None]
        swap = [b["memory"].get("swap_delta_mib", 0.0) for b in blocks]
        # per-repetition spread
        reps = sorted({r["repetition"] for r in recs})
        rep_acc = [float(np.mean([r["correct_strict"] for r in recs if r["repetition"] == k])) for k in reps]
        rep_lat = []
        for k in reps:
            v = [r["latency_ms"] for r in recs if r["repetition"] == k and r["latency_ms"] is not None]
            rep_lat.append(float(np.median(v)) if v else None)
        lat_summary = median_iqr(item_lat) if item_lat else None
        out.append({
            "arm": arm, "model": model, "n_records": len(recs), "n_items": len(lat_by) or len(resp_by),
            "accuracy_strict": acc_s, "accuracy_lenient": acc_l,
            "chance": float(np.mean([1.0 / r["n_choices"] for r in recs])),
            "errors": errors, "format_fail_strict": fmt_fail, "format_fail_lenient": fmt_fail_l,
            "latency_ms_median": lat_summary[0] if lat_summary else None,
            "latency_ms_q1": lat_summary[1] if lat_summary else None,
            "latency_ms_q3": lat_summary[2] if lat_summary else None,
            "ttft_ms_median": ttft[0] if ttft else None,
            "decode_tps_median": dec[0] if dec else None,
            "prefill_tps_median": pre[0] if pre else None,
            "determinism": determ,
            "runtime_model_mib": max(rt_sizes) / 2**20 if rt_sizes else None,
            "peak_rss_mib": max(rss) if rss else None,
            "swap_delta_mib_max": max(swap) if swap else None,
            "block_wall_s": [b["wall_s"] for b in blocks],
            "rep_accuracy_strict": rep_acc,
            "rep_latency_ms_median": rep_lat,
            "rep_latency_cv": cv([x for x in rep_lat if x is not None]),
            "item_latency_ms": item_lat,
        })
    return out


def contrasts(doc: dict, extraction: str = "strict", n_boot: int = 10_000, seed: int = 7) -> list[dict]:
    """Paired contrasts of every arm against the baseline (first arm), Holm-adjusted."""
    arms = [a["arm_id"] for a in doc["config"]["arms"]]
    if len(arms) < 2:
        return []
    key = f"correct_{extraction}"
    base_arm = doc["config"].get("baseline_arm", arms[0])
    base = _per_item([r for r in doc["records"] if r["arm"] == base_arm], key)
    rows = []
    for arm in arms:
        if arm == base_arm:
            continue
        cand = _per_item([r for r in doc["records"] if r["arm"] == arm], key)
        common = sorted(set(base) & set(cand))
        if not common:
            continue
        pd = paired_compare([cand[i] for i in common], [base[i] for i in common], n_boot, seed)
        rows.append({"arm": arm, "baseline": base_arm, "extraction": extraction, "n": pd.n,
                     "delta_pp": 100 * pd.delta, "ci_low_pp": 100 * pd.ci_low, "ci_high_pp": 100 * pd.ci_high,
                     "b": pd.b, "c": pd.c, "mcnemar_p": pd.mcnemar_p})
    adj = holm([r["mcnemar_p"] for r in rows]) if rows else []
    for r, a in zip(rows, adj):
        r["holm_p"] = a
    return rows


def projection(doc: dict) -> dict:
    """Seconds per request measured in this run (block wall time incl. warm-ups)
    times the planned request counts. Meaningless for a simulated backend."""
    total_wall = sum(b["wall_s"] for b in doc["blocks"])
    n_req = len(doc["records"]) + (len(doc["blocks"]) if doc["config"].get("warmup", True) else 0)
    spr = total_wall / n_req if n_req else None
    return {
        "seconds_per_request": spr,
        "simulated_backend": doc["backend"]["simulated"],
        "projected_hours": {k: (None if spr is None else spr * v / 3600) for k, v in PLANNED_REQUESTS.items()},
    }


# EXP-002 protocol item 5 (v1.0, frozen 2026-11-24): the H1 ordering is by model
# file size, A0 phi4-mini:3.8b 2.49 GB < A1 llama3.1:8b 4.92 GB < A2 ministral-3:8b 6.02 GB.
EXP002_SIZE_ORDER = (("A0", 2.49), ("A1", 4.92), ("A2", 6.02))


def _cw_values(recs: list[dict], state: str, key: str) -> list[float]:
    """Values of ``key`` from the valid trials in ``state`` (protocol item 17).

    A trial enters the analysis only if its start state was confirmed
    (``state_valid``), the request succeeded and the value exists. Invalid
    and failed trials are kept in the raw file and counted, never dropped silently.
    """
    return [float(r[key]) for r in recs
            if r.get("start_state") == state and r.get("state_valid") and not r["error"] and r[key] is not None]


def cold_warm_penalties(doc: dict, n_boot: int = 10_000, seed: int = 7) -> list[dict]:
    """EXP-002 estimand (items 6 and 16): per arm, Penalty_k = median cold TTFT
    minus median warm TTFT (ms), with percentile 95 % bootstrap CIs over trials
    (10,000 resamples, seed 7) for both medians and the penalty. Each arm's
    bootstrap starts from ``default_rng(seed)``, as the EXP-001 contrasts do.
    Load duration and end-to-end latency medians per state are descriptive."""
    rows = []
    for a in doc["config"]["arms"]:
        arm = a["arm_id"]
        recs = [r for r in doc["records"] if r["arm"] == arm and "start_state" in r]
        counts = {st: {"planned_or_run": sum(1 for r in recs if r["start_state"] == st),
                       "invalid_state": sum(1 for r in recs if r["start_state"] == st and not r["state_valid"]),
                       "request_error": sum(1 for r in recs if r["start_state"] == st and r["error"])}
                  for st in ("cold", "warm")}
        cold = _cw_values(recs, "cold", "ttft_ms")
        warm = _cw_values(recs, "warm", "ttft_ms")
        row = {"arm": arm, "model": a["model"], "n_cold": len(cold), "n_warm": len(warm),
               "n_cold_records": counts["cold"]["planned_or_run"], "n_warm_records": counts["warm"]["planned_or_run"],
               "n_cold_invalid": counts["cold"]["invalid_state"], "n_warm_invalid": counts["warm"]["invalid_state"],
               "n_cold_error": counts["cold"]["request_error"], "n_warm_error": counts["warm"]["request_error"]}
        if cold and warm:
            md = bootstrap_median_diff(cold, warm, n_boot, seed)
            row.update({"cold_ttft_ms_median": md.median_x, "cold_ci_low": md.ci_x[0], "cold_ci_high": md.ci_x[1],
                        "warm_ttft_ms_median": md.median_y, "warm_ci_low": md.ci_y[0], "warm_ci_high": md.ci_y[1],
                        "penalty_ms": md.diff, "penalty_ci_low": md.ci_diff[0], "penalty_ci_high": md.ci_diff[1]})
        else:
            row.update({k: None for k in ("cold_ttft_ms_median", "cold_ci_low", "cold_ci_high", "warm_ttft_ms_median",
                                          "warm_ci_low", "warm_ci_high", "penalty_ms", "penalty_ci_low",
                                          "penalty_ci_high")})
        for st in ("cold", "warm"):
            load = _cw_values(recs, st, "load_duration_ns")
            lat = _cw_values(recs, st, "latency_ms")
            row[f"{st}_load_ms_median"] = float(np.median(load)) / 1e6 if load else None
            row[f"{st}_latency_ms_median"] = float(np.median(lat)) if lat else None
        row["cold_ttft_ms"] = cold
        row["warm_ttft_ms"] = warm
        rows.append(row)
    return rows


def cold_warm_ordering(rows: list[dict]) -> dict:
    """EXP-002 decision rule (item 5). H1: penalty(A0) < penalty(A1) < penalty(A2).

    Two conditions are evaluated and both are reported: a reversal of the
    ordering in the point estimates (any adjacent pair, in file-size order, whose
    penalty does not increase), and overlapping 95 % CIs between adjacent arms
    (reported as unresolved). H1 is supported only if neither occurs. An exact
    tie of point estimates is not defined by the frozen text and is reported as
    such (``tie``), not classified. Descriptive evidence only; no scaling law.
    """
    by = {r["arm"]: r for r in rows}
    order = [a for a, _ in EXP002_SIZE_ORDER]
    pens = [by.get(a, {}).get("penalty_ms") for a in order]
    if any(p is None for p in pens):
        return {"order": order, "evaluable": False, "verdict": "not evaluable (an arm has no valid cold or warm trial)",
                "reversal": None, "overlap": None, "tie": None, "pairs": []}
    pairs = []
    for lo_arm, hi_arm in zip(order, order[1:]):
        lo, hi = by[lo_arm], by[hi_arm]
        pairs.append({"lower": lo_arm, "higher": hi_arm,
                      "increase": hi["penalty_ms"] > lo["penalty_ms"],
                      "tie": hi["penalty_ms"] == lo["penalty_ms"],
                      "ci_overlap": lo["penalty_ci_high"] >= hi["penalty_ci_low"]
                      and hi["penalty_ci_high"] >= lo["penalty_ci_low"]})
    tie = any(p["tie"] for p in pairs)
    reversal = any((not p["increase"]) and not p["tie"] for p in pairs)
    overlap = any(p["ci_overlap"] for p in pairs)
    if tie:
        verdict = "tie in point estimates: not classified by the frozen rule (reported to the owner)"
    elif not reversal and not overlap:
        verdict = "H1 supported (ordering holds and adjacent CIs do not overlap)"
    elif reversal and overlap:
        verdict = "H1 not supported: reversal of the ordering in the point estimates, and overlapping adjacent CIs"
    elif reversal:
        verdict = "H1 not supported: reversal of the ordering in the point estimates"
    else:
        verdict = "H1 not supported: unresolved (ordering holds in the point estimates, adjacent CIs overlap)"
    return {"order": order, "evaluable": True, "verdict": verdict, "reversal": reversal, "overlap": overlap,
            "tie": tie, "pairs": pairs}
