# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""M4 exploratory re-analysis of the committed EXP-003 result (no inference, no timing).

EXPLORATORY. This script reads only the committed confirmatory result
``results/confirmatory/RUN-EXP-003-0001/result.json`` and writes
``results/exploratory/M4-EXPL-0001/``. It sends no request to any runtime and
measures nothing; it re-analyses records that already exist. Nothing it prints
changes or replaces the frozen EXP-003 verdict (H0 not rejected).

Checks (journal JRN-0009, decision DL-012):
  E1  latency ratio Q8/Q4 with bootstrap intervals over items, under both
      readings of protocol section 8 (DL-011 gap 1): ratio of the two medians
      of per-item medians, and median of the per-item ratios;
  E2  decode-throughput ratio and runtime-memory ratio (point values, and a
      bootstrap interval for decode over items);
  E3  warm-up prompt reuse: the discarded warm-up request of each block uses the
      block's first item, so the first measured request repeats it; effect of
      dropping those records on the per-item median latency;
  E4  prefill duration by prompt length (32-token bins);
  E5  discordant items and strict format failures (does format compliance
      drive the accuracy difference?);
  E6  arm position within a repetition (first or second block) and latency;
  E7  interval width actually observed versus the planned assumption;
  E8  prompt token counts per item between arms (tokenizer check).

Usage: .venv/bin/python -I scripts/m4_exploratory_exp003.py --repo .
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

N_BOOT = 10_000
SEED = 7
RESULT = "results/confirmatory/RUN-EXP-003-0001/result.json"
OUT = "results/exploratory/M4-EXPL-0001"


def per_item(records, key, reducer):
    by = defaultdict(list)
    for r in records:
        if r[key] is not None:
            by[r["item_id"]].append(r[key])
    return {k: float(reducer(v)) for k, v in by.items()}


def pct_ci(v):
    return [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    repo = Path(ap.parse_args().repo)
    src = repo / RESULT
    raw = src.read_bytes()
    doc = json.loads(raw)
    recs = doc["records"]
    q4 = [r for r in recs if r["arm"] == "Q4"]
    q8 = [r for r in recs if r["arm"] == "Q8"]
    out: dict = {
        "label": "exploratory",
        "note": "Re-analysis of committed records only; no inference and no timing measurement were run. Does not change the frozen EXP-003 verdict.",
        "source": RESULT,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "generator": "scripts/m4_exploratory_exp003.py",
        "bootstrap": {"n_boot": N_BOOT, "seed": SEED, "interval": "percentile 95 %", "unit": "item"},
    }

    # E1: latency ratio under both readings
    l4 = per_item(q4, "latency_ms", np.median)
    l8 = per_item(q8, "latency_ms", np.median)
    ids = sorted(set(l4) & set(l8))
    a4 = np.array([l4[i] for i in ids])
    a8 = np.array([l8[i] for i in ids])
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(ids), size=(N_BOOT, len(ids)))
    rom = np.median(a8[idx], axis=1) / np.median(a4[idx], axis=1)
    mor = np.median((a8 / a4)[idx], axis=1)
    out["E1_latency_ratio"] = {
        "n_items": len(ids),
        "ratio_of_medians": float(np.median(a8) / np.median(a4)),
        "ratio_of_medians_ci": pct_ci(rom),
        "median_of_item_ratios": float(np.median(a8 / a4)),
        "median_of_item_ratios_ci": pct_ci(mor),
        "items_where_q8_faster": int(np.sum(a8 < a4)),
        "note": "Both readings of protocol section 8 computed because the frozen text does not choose (DL-011 gap 1). Same bootstrap draws for both. Exploratory, descriptive.",
    }

    # E2: decode throughput ratio and memory ratio
    def tps(r, c, d):
        return r[c] / r[d] * 1e9 if r[c] and r[d] else None

    for r in recs:
        r["_dec"] = tps(r, "eval_count", "eval_duration_ns")
        r["_pre"] = tps(r, "prompt_eval_count", "prompt_eval_duration_ns")
    d4 = per_item(q4, "_dec", np.median)
    d8 = per_item(q8, "_dec", np.median)
    dids = sorted(set(d4) & set(d8))
    b4 = np.array([d4[i] for i in dids])
    b8 = np.array([d8[i] for i in dids])
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(dids), size=(N_BOOT, len(dids)))
    dr = np.median(b8[idx], axis=1) / np.median(b4[idx], axis=1)
    rec_dec_ratio = float(np.median([r["_dec"] for r in q8 if r["_dec"]]) / np.median([r["_dec"] for r in q4 if r["_dec"]]))
    size = {}
    for b in doc["blocks"]:
        for m in b.get("loaded_after") or []:
            size[m["name"]] = max(size.get(m["name"], 0), m["size"])
    out["E2_decode_and_memory"] = {
        "decode_ratio_record_medians": rec_dec_ratio,
        "decode_ratio_item_medians": float(np.median(b8) / np.median(b4)),
        "decode_ratio_item_medians_ci": pct_ci(dr),
        "runtime_model_mib": {k: v / 2**20 for k, v in size.items()},
        "memory_ratio": size["llama3.1:8b-instruct-q8_0"] / size["llama3.1:8b"],
        "memory_difference_mib": (size["llama3.1:8b-instruct-q8_0"] - size["llama3.1:8b"]) / 2**20,
        "note": "The committed metrics.csv decode value is a median over records (1,500 per arm); the item-median version is shown for comparison. Memory is the runtime-reported /api/ps size, deterministic per model, no interval.",
    }

    # E3: warm-up prompt reuse
    first = [r for r in recs if r["order_index"] == 0]
    rest = [r for r in recs if r["order_index"] > 0]
    e3 = {"records_at_order_index_0": len(first),
          "first_record_latency_ms": {a: sorted(round(r["latency_ms"], 1) for r in first if r["arm"] == a) for a in ("Q4", "Q8")},
          "other_records_latency_ms_min": {a: round(min(r["latency_ms"] for r in rest if r["arm"] == a), 1) for a in ("Q4", "Q8")}}
    for a, rr in (("Q4", q4), ("Q8", q8)):
        full = per_item(rr, "latency_ms", np.median)
        drop = per_item([r for r in rr if r["order_index"] > 0], "latency_ms", np.median)
        e3[f"{a}_median_of_item_medians_all"] = float(np.median(list(full.values())))
        e3[f"{a}_median_of_item_medians_without_first"] = float(np.median(list(drop.values())))
    e3["first_item_same_across_arms_within_rep"] = all(
        len({r["item_id"] for r in first if r["repetition"] == k}) == 1 for k in range(5))
    e3["note"] = "runner.run_matrix sends the discarded warm-up with the block's first item, so the first measured request repeats a prompt the runtime has just processed; its prefill is much faster. One of five repetitions of one item per block, same item in both arms of a repetition."
    out["E3_warmup_prompt_reuse"] = e3

    # E4: prefill duration by prompt length
    bins = [(0, 64), (64, 96), (96, 128), (128, 160), (160, 192)]
    e4 = []
    for a, rr in (("Q4", q4), ("Q8", q8)):
        rr = [r for r in rr if r["order_index"] > 0]
        pc = np.array([r["prompt_eval_count"] for r in rr])
        pdur = np.array([r["prompt_eval_duration_ns"] / 1e6 for r in rr])
        for lo, hi in bins:
            m = (pc > lo) & (pc <= hi)
            if m.sum():
                e4.append({"arm": a, "prompt_tokens": f"{lo + 1}-{hi}", "n_records": int(m.sum()),
                           "prefill_ms_median": float(np.median(pdur[m]))})
    out["E4_prefill_by_prompt_length"] = {
        "rows": e4,
        "note": "Records with order_index 0 removed (E3). Prefill time rises in steps across 32-token prompt-length bins in both arms; the mechanism is not verified here. Prefill tokens/s is therefore a function of prompt length, not a constant of the arm.",
    }

    # E5: discordant items and format failures
    c4 = per_item(q4, "correct_strict", np.mean)
    c8 = per_item(q8, "correct_strict", np.mean)
    disc_b = sorted(i for i in ids if c8[i] >= 0.5 and c4[i] < 0.5)
    disc_c = sorted(i for i in ids if c8[i] < 0.5 and c4[i] >= 0.5)
    ff = {a: sorted({r["item_id"] for r in rr if r["extracted_strict"] is None}) for a, rr in (("Q4", q4), ("Q8", q8))}
    ff_any = set(ff["Q4"]) | set(ff["Q8"])
    keep = [i for i in ids if i not in ff_any]
    d_keep = float(np.mean([c8[i] - c4[i] for i in keep])) * 100
    out["E5_discordance_and_format"] = {
        "b_q8_right_q4_wrong": len(disc_b), "c_q8_wrong_q4_right": len(disc_c),
        "b_items": disc_b, "c_items": disc_c,
        "strict_format_failure_items": ff,
        "format_failure_items_in_discordant_set": sorted(ff_any & (set(disc_b) | set(disc_c))),
        "delta_pp_excluding_items_with_any_strict_format_failure": d_keep,
        "n_items_kept": len(keep),
        "non_majority_items": int(sum(1 for i in ids if c4[i] not in (0.0, 1.0) or c8[i] not in (0.0, 1.0))),
        "note": "Post hoc exclusion is exploratory and is not a valid confirmatory analysis (protocol section 9 forbids excluding items after outputs).",
    }

    # E6: arm position within a repetition
    order = defaultdict(list)
    for b in doc["blocks"]:
        order[b["repetition"]].append(b["arm"])
    e6 = []
    for a, rr in (("Q4", q4), ("Q8", q8)):
        for pos in (0, 1):
            reps = [k for k, arms in order.items() if arms[pos] == a]
            v = [r["latency_ms"] for r in rr if r["repetition"] in reps and r["order_index"] > 0]
            e6.append({"arm": a, "position": pos + 1, "repetitions": reps,
                       "median_record_latency_ms": float(np.median(v)) if v else None})
    out["E6_arm_position"] = {"block_order": {str(k): v for k, v in sorted(order.items())}, "rows": e6}

    # E7: interval width observed versus planned assumption
    n = len(ids)
    import csv
    with open(repo / "results/confirmatory/RUN-EXP-003-0001/contrasts.csv", newline="") as fh:
        row = next(r for r in csv.DictReader(fh) if r["extraction"] == "strict")
    obs_ci = [float(row["ci_low_pp"]), float(row["ci_high_pp"])]
    disc = (len(disc_b) + len(disc_c)) / n
    out["E7_precision"] = {
        "assumed_discordant_proportion": 0.25,
        "observed_discordant_proportion": disc,
        "planned_ci_half_width_pp": 100 * 1.96 * (0.25 / n) ** 0.5,
        "observed_ci_pp": obs_ci,
        "observed_ci_half_width_pp": (obs_ci[1] - obs_ci[0]) / 2,
        "note": "Observed strict interval read from the committed contrasts.csv. The frozen protocols define no equivalence margin, so the interval is not an equivalence test.",
    }

    # E8: tokenizer check (prompt token counts per item and repetition)
    pt = defaultdict(dict)
    for r in recs:
        pt[(r["item_id"], r["repetition"])][r["arm"]] = r["prompt_eval_count"]
    out["E8_prompt_tokens"] = {
        "pairs": len(pt),
        "pairs_with_equal_prompt_tokens": sum(1 for v in pt.values() if v.get("Q4") == v.get("Q8")),
        "eval_count_values": {a: {str(k): int(n) for k, n in zip(*np.unique([r["eval_count"] for r in rr], return_counts=True))}
                              for a, rr in (("Q4", q4), ("Q8", q8))},
    }

    od = repo / OUT
    od.mkdir(parents=True, exist_ok=True)
    (od / "exploratory_exp003.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
