# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Analysis of a validated result document (pure functions, no I/O)."""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from .stats import cv, holm, median_iqr, paired_compare
from .tokens import throughput_tps

# Planned request counts from research/protocol.md section 10 (draft v0.1).
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
