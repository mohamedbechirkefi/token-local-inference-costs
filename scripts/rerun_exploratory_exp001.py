# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Exploratory checks of the committed EXP-001 rerun (no inference, no timing).

EXPLORATORY. Reads only ``results/confirmatory/RUN-EXP-001-0001/result.json``
and writes ``results/exploratory/RERUN-EXPL-0001/exploratory_exp001.json``. It
sends no request to any runtime. Nothing it computes changes the frozen EXP-001
analysis (``token-lab report``) or its verdict.

Checks (journal JRN-0013, decisions DL-015 and DL-016):
  B   every block against the frozen exclusion and stopping criteria (main
      protocol section 9; DL-011 gap 2: not implemented in the runner);
  R   per-repetition strict and lenient accuracy per arm (do the blocks that
      meet a criterion change any accuracy value?);
  E1  latency ratio of each arm to the baseline A0 with bootstrap intervals over
      items under both readings of protocol section 8 (DL-011 gap 1; owner
      decision R-TOKEN-2: both stay shown): ratio of the medians of per-item
      medians, and median of per-item ratios;
  M   runtime-reported model memory per arm (largest /api/ps size);
  P   per-block median prefill duration (prompt reuse between consecutive
      blocks of the same arm);
  F   strict format failures per arm and the most frequent failing responses.

A second file, ``prompts_and_rss.json``, adds descriptive values read from
``RUN-EXP-002-0001`` and ``RUN-SMOKE-0005`` as well:
  L   prompt length (prompt_eval_count) per arm, median and range, EXP-001 and
      EXP-002; EXP-002 cold and warm prefill medians of valid trials;
  S   peak RSS per block (minimum and maximum) per run, to show which runtime
      process the frozen process filter covers.

Usage: .venv/bin/python -I scripts/rerun_exploratory_exp001.py --repo .
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

N_BOOT = 10_000
SEED = 7
RESULT = "results/confirmatory/RUN-EXP-001-0001/result.json"
RESULT_002 = "results/confirmatory/RUN-EXP-002-0001/result.json"
SMOKE_096 = "results/exploratory/RUN-SMOKE-0005/result.json"
OUT = "results/exploratory/RERUN-EXPL-0001"
SWAP_EXCLUDE_MIB = 512
SWAP_ABORT_MIB = 2048


def pct_ci(v) -> list[float]:
    return [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    repo = Path(ap.parse_args().repo)
    raw = (repo / RESULT).read_bytes()
    doc = json.loads(raw)
    recs = doc["records"]
    arm_models = {a["arm_id"]: a["model"] for a in doc["config"]["arms"]}
    out: dict = {
        "label": "exploratory",
        "note": "Checks of committed records only; no inference and no timing measurement were run. Does not change the frozen EXP-001 analysis or verdict.",
        "source": RESULT,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "generator": "scripts/rerun_exploratory_exp001.py",
        "bootstrap": {"n_boot": N_BOOT, "seed": SEED, "interval": "percentile 95 %", "unit": "item"},
        "runtime_version": doc["manifest"]["backend"]["runtime_version"],
    }

    # B: blocks against the frozen criteria
    blocks = []
    power = {doc["manifest"]["host"]["before"]["power"]["source"], doc["manifest"]["host"]["after"]["power"]["source"]}
    for pos, b in enumerate(doc["blocks"]):
        names = {m["name"] for m in (b["loaded_before"] or []) + (b["loaded_after"] or [])}
        foreign = sorted(names - set(arm_models.values()))
        sw = b["memory"]["swap_delta_mib"]
        crit = []
        if foreign:
            crit.append(f"foreign model loaded: {foreign}")
        if sw > SWAP_EXCLUDE_MIB:
            crit.append(f"exclusion: swap growth {sw:.1f} MiB above {SWAP_EXCLUDE_MIB} MiB")
        if sw > SWAP_ABORT_MIB:
            crit.append(f"stopping rule: swap growth {sw:.1f} MiB above 2 GiB (memory exhaustion, abort)")
        blocks.append({"position": pos + 1, "arm": b["arm"], "repetition": b["repetition"],
                       "wall_s": b["wall_s"], "swap_delta_mib": sw,
                       "loaded_before": [m["name"] for m in b["loaded_before"] or []],
                       "loaded_after": [m["name"] for m in b["loaded_after"] or []],
                       "criteria_met": crit})
    out["B_blocks"] = {
        "power_sources_at_run_start_and_end": sorted(power),
        "power_note": "power is recorded at run start and end only, not per block",
        "runtime_version_note": "one server process (started by the rerun session) served the whole run; version read once",
        "blocks": blocks,
        "n_blocks": len(blocks),
        "n_blocks_meeting_a_criterion": sum(1 for b in blocks if b["criteria_met"]),
        "first_stopping_rule_block": next((b["position"] for b in blocks
                                           if any(c.startswith("stopping rule") for c in b["criteria_met"])), None),
    }

    # R: per-repetition accuracy
    by_rep = defaultdict(list)
    for r in recs:
        by_rep[(r["arm"], r["repetition"])].append(r)
    out["R_accuracy_per_repetition"] = {
        f"{a}_rep{k}": {"strict": sum(r["correct_strict"] for r in v) / len(v),
                        "lenient": sum(r["correct_lenient"] for r in v) / len(v), "n": len(v)}
        for (a, k), v in sorted(by_rep.items())
    }

    # E1: latency ratios, both readings
    lat = defaultdict(lambda: defaultdict(list))
    for r in recs:
        if r["latency_ms"] is not None:
            lat[r["arm"]][r["item_id"]].append(r["latency_ms"])
    med = {a: {i: float(np.median(v)) for i, v in d.items()} for a, d in lat.items()}
    e1 = {}
    for arm in ("A1", "A2"):
        ids = sorted(set(med["A0"]) & set(med[arm]))
        a0 = np.array([med["A0"][i] for i in ids])
        ak = np.array([med[arm][i] for i in ids])
        rng = np.random.default_rng(SEED)
        idx = rng.integers(0, len(ids), size=(N_BOOT, len(ids)))
        rom = np.median(ak[idx], axis=1) / np.median(a0[idx], axis=1)
        mor = np.median((ak / a0)[idx], axis=1)
        e1[f"{arm}/A0"] = {"n_items": len(ids),
                           "ratio_of_medians": float(np.median(ak) / np.median(a0)),
                           "ratio_of_medians_ci": pct_ci(rom),
                           "median_of_item_ratios": float(np.median(ak / a0)),
                           "median_of_item_ratios_ci": pct_ci(mor),
                           "items_arm_slower": int(np.sum(ak > a0))}
    out["E1_latency_ratio"] = e1

    # M: runtime-reported model memory
    sizes: dict[str, int] = {}
    for b in doc["blocks"]:
        for m in b["loaded_after"] or []:
            sizes[m["name"]] = max(sizes.get(m["name"], 0), m["size"])
    out["M_runtime_model_mib"] = {a: sizes[m] / 2**20 for a, m in arm_models.items() if m in sizes}

    # P: per-block median prefill duration
    out["P_block_prefill_ms_median"] = {
        f"{a}_rep{k}": float(np.median([r["prompt_eval_duration_ns"] / 1e6 for r in v
                                        if r["prompt_eval_duration_ns"] is not None]))
        for (a, k), v in sorted(by_rep.items())
    }

    # F: strict format failures
    f = {}
    for arm in arm_models:
        fails = [r["response"] for r in recs if r["arm"] == arm and r["extracted_strict"] is None]
        f[arm] = {"n_records": len(fails), "n_items": len({r["item_id"] for r in recs
                                                            if r["arm"] == arm and r["extracted_strict"] is None}),
                  "most_frequent": Counter(fails).most_common(5)}
    out["F_strict_format_failures"] = f

    dest = repo / OUT
    dest.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    (dest / "exploratory_exp001.json").write_text(text, encoding="utf-8")
    print(json.dumps({"written": f"{OUT}/exploratory_exp001.json",
                      "sha256": hashlib.sha256(text.encode()).hexdigest()}))

    # L and S: second file
    doc2 = json.loads((repo / RESULT_002).read_bytes())
    smoke = json.loads((repo / SMOKE_096).read_bytes())
    sec: dict = {"label": "exploratory (descriptive values from committed records)",
                 "sources": {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in (RESULT, RESULT_002, SMOKE_096)},
                 "generator": "scripts/rerun_exploratory_exp001.py"}
    lens = {}
    for name, d in (("EXP-001", doc), ("EXP-002", doc2)):
        for arm in arm_models:
            v = [r["prompt_eval_count"] for r in d["records"] if r["arm"] == arm and r["prompt_eval_count"] is not None]
            lens[f"{name}_{arm}"] = {"median": float(np.median(v)), "min": int(min(v)), "max": int(max(v))}
    sec["L_prompt_eval_count"] = lens
    sec["L_exp002_prefill_ms_median"] = {
        f"{arm}_{state}": float(np.median([r["prompt_eval_duration_ns"] / 1e6 for r in doc2["records"]
                                           if r["arm"] == arm and r["start_state"] == state and r["state_valid"]]))
        for arm in arm_models for state in ("cold", "warm")}
    sec["S_peak_rss_mib_per_block"] = {
        run: {"min": min(b["memory"]["peak_rss_mib"] for b in d["blocks"]),
              "max": max(b["memory"]["peak_rss_mib"] for b in d["blocks"]),
              "runtime_version": d["manifest"]["backend"]["runtime_version"]}
        for run, d in (("RUN-EXP-001-0001", doc), ("RUN-EXP-002-0001", doc2), ("RUN-SMOKE-0005", smoke))}
    text2 = json.dumps(sec, indent=1, sort_keys=True) + "\n"
    (dest / "prompts_and_rss.json").write_text(text2, encoding="utf-8")
    print(json.dumps({"written": f"{OUT}/prompts_and_rss.json",
                      "sha256": hashlib.sha256(text2.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
