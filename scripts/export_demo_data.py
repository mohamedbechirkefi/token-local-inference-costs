# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Export the published results for the static demo (M5).

Writes ``demo/public/data/results.json`` in the shared lab demo schema
(``lab-demo-results`` 1.0.0) from committed files only: the confirmatory EXP-003
result, its ``metrics.csv`` and ``contrasts.csv``, the M4 exploratory re-analysis,
the freeze record, the experiment registry, the claims register, the artifact
manifest and the manuscript. No inference runs and no runtime is contacted.

Fail closed: every ``display`` and ``interval_display`` string is formatted from the
raw value read here, compared with the text the manuscript prints (the expected
string is written out below), and must also appear in the ``values`` text of the
named artifact-manifest entry. Any mismatch aborts the export. Per-item values are
recomputed from the records and must reproduce the committed ``metrics.csv`` and
``contrasts.csv``. The output contains no timestamp, so the export is deterministic.

Usage: ``.venv/bin/python scripts/export_demo_data.py [--check]``. With ``--check``
nothing is written; the exit status is 1 if the committed file differs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo/public/data/results.json"

RUN = "RUN-EXP-003-0001"
RUN_DIR = f"results/confirmatory/{RUN}"
EXPL = "results/exploratory/M4-EXPL-0001/exploratory_exp003.json"

SOURCES = [
    f"{RUN_DIR}/result.json",
    f"{RUN_DIR}/metrics.csv",
    f"{RUN_DIR}/contrasts.csv",
    EXPL,
    "research/freeze.json",
    "research/experiment_registry.csv",
    "research/claims_register.csv",
    "research/publication/artifact_manifest.json",
    "research/paper/manuscript.md",
]


class ExportError(RuntimeError):
    pass


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _json(rel: str):
    return json.loads(_text(rel))


def _csv(rel: str) -> list[dict]:
    with (ROOT / rel).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _sha256(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _revision() -> str:
    """Last commit that touched any source file (the commit of the results)."""
    out = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", *SOURCES],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", out):
        raise ExportError(f"could not determine the results revision: {out!r}")
    return out


class Checker:
    """Checks each formatted string against the manuscript and the manifest."""

    def __init__(self) -> None:
        self.manuscript = _norm(_text("research/paper/manuscript.md"))
        man = _json("research/publication/artifact_manifest.json")
        self.manifest = {a["id"]: a for a in man["artifacts"]}

    def text(self, formatted: str, expected: str, manifest_ids: tuple[str, ...] = ()) -> str:
        if formatted != expected:
            raise ExportError(f"formatted {formatted!r}, the manuscript prints {expected!r}")
        if _norm(formatted) not in self.manuscript:
            raise ExportError(f"{formatted!r} does not appear in the manuscript")
        for mid in manifest_ids:
            entry = self.manifest.get(mid)
            if entry is None:
                raise ExportError(f"manifest entry {mid} missing")
            core = formatted.strip("[]")
            if core.split(", ")[0] not in entry["values"]:
                raise ExportError(f"{formatted!r} not in manifest {mid} values {entry['values']!r}")
        return formatted


def est(label, kind, value, display, *, ci=None, ci_level=None, interval_kind=None,
        interval_display=None, unit="", manifest_ids=()):
    lo, hi = ci if ci is not None else (None, None)
    return {
        "label": label,
        "kind": kind,
        "estimate": value,
        "ci_low": lo,
        "ci_high": hi,
        "ci_level": ci_level,
        "interval_kind": interval_kind,
        "unit": unit,
        "display": display,
        "interval_display": interval_display,
        "manifest_ids": list(manifest_ids),
    }


def f1(x: float) -> str:
    return f"{x:.1f}"


def f1c(x: float) -> str:
    return f"{x:,.1f}"


def f3(x: float) -> str:
    return f"{x:.3f}"


def pp(x: float) -> str:
    return f"{x:+.2f}"


def iv(lo: float, hi: float, fmt) -> str:
    return f"[{fmt(lo)}, {fmt(hi)}]"


# ------------------------------------------------------------------ records


def per_item(doc: dict) -> dict[str, dict]:
    """Per arm and item: mean correctness over repetitions and median latency."""
    by: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in doc["records"]:
        by[(r["arm"], r["item_id"])].append(r)
    out: dict[str, dict] = defaultdict(dict)
    for (arm, item), recs in by.items():
        if len(recs) != 5 or any(r["error"] for r in recs):
            raise ExportError(f"{arm} {item}: expected 5 error-free records")
        out[item][arm] = {
            "strict": sum(r["correct_strict"] for r in recs) / 5,
            "lenient": sum(r["correct_lenient"] for r in recs) / 5,
            "latency_ms": statistics.median(r["latency_ms"] for r in recs),
            "strict_miss": any(r["extracted_strict"] is None for r in recs),
        }
    return out


def quantile(xs: list[float], q: float) -> float:
    """numpy.quantile, default linear method."""
    s = sorted(xs)
    h = (len(s) - 1) * q
    lo = int(h // 1)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


# ------------------------------------------------------------------ build


def claims_for(config_hashes: dict[str, str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in config_hashes}
    for r in _csv("research/claims_register.csv"):
        for exp, h in config_hashes.items():
            if h in r["config_sha256"]:
                out[exp].append(r["claim_id"])
    for exp, ids in out.items():
        if not ids:
            raise ExportError(f"no claim registered for {exp}")
    return {k: sorted(v) for k, v in out.items()}


def manuscript_table(title_start: str) -> list[list[str]]:
    """Rows of the Markdown table whose bold caption starts with ``title_start``."""
    lines = _text("research/paper/manuscript.md").splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"**{title_start}"):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    if rows:
                        break
                    continue
                cells = [c.strip() for c in row.strip("|").split("|")]
                if set("".join(cells)) <= set("-: "):
                    continue
                rows.append(cells)
            return rows[1:]
    raise ExportError(f"table {title_start!r} not found in the manuscript")


def manuscript_limitations() -> list[str]:
    text = _text("research/paper/manuscript.md")
    m = re.search(r"^# 7\. Limitations and threats to validity\n(.*?)^# 8\.", text, re.S | re.M)
    if m is None:
        raise ExportError("manuscript section 7 not found")
    items = [re.sub(r"\*\*", "", ln[2:]).strip() for ln in m.group(1).splitlines() if ln.startswith("- ")]
    if len(items) < 5:
        raise ExportError("manuscript section 7 has too few items")
    return items


def build() -> dict:
    ck = Checker()
    doc = _json(f"{RUN_DIR}/result.json")
    if doc["run_id"] != RUN or doc["label"] != "confirmatory" or doc["backend"]["simulated"]:
        raise ExportError("unexpected EXP-003 result document")
    metrics = {r["arm"]: r for r in _csv(f"{RUN_DIR}/metrics.csv")}
    contrasts = {r["extraction"]: r for r in _csv(f"{RUN_DIR}/contrasts.csv")}
    expl = _json(EXPL)
    freeze = _json("research/freeze.json")
    registry = {r["exp_id"]: r for r in _csv("research/experiment_registry.csv")}
    hashes = {k: v["config_canonical_sha256"] for k, v in freeze["experiments"].items()}
    if doc["config_sha256"] != hashes["EXP-003"]:
        raise ExportError("EXP-003 result config hash differs from the freeze record")
    claims = claims_for(hashes)

    items = per_item(doc)
    ids = sorted(items)
    if len(ids) != 300:
        raise ExportError(f"expected 300 items, found {len(ids)}")

    # Recompute and cross-check the committed per-arm summaries.
    for arm in ("Q4", "Q8"):
        m = metrics[arm]
        acc = sum(items[i][arm]["strict"] for i in ids) / 300
        lat = [items[i][arm]["latency_ms"] for i in ids]
        if not close(acc, float(m["accuracy_strict"])):
            raise ExportError(f"{arm}: recomputed accuracy {acc} differs from metrics.csv")
        for q, key in ((0.5, "latency_ms_median"), (0.25, "latency_ms_q1"), (0.75, "latency_ms_q3")):
            if not close(quantile(lat, q), float(m[key])):
                raise ExportError(f"{arm}: recomputed {key} differs from metrics.csv")
    d_items = [items[i]["Q8"]["strict"] - items[i]["Q4"]["strict"] for i in ids]
    if not close(sum(d_items) / 3, float(contrasts["strict"]["delta_pp"])):
        raise ExportError("recomputed strict delta differs from contrasts.csv")
    b = sum(items[i]["Q8"]["strict"] >= 0.5 and items[i]["Q4"]["strict"] < 0.5 for i in ids)
    c = sum(items[i]["Q8"]["strict"] < 0.5 and items[i]["Q4"]["strict"] >= 0.5 for i in ids)
    if (b, c) != (int(contrasts["strict"]["b"]), int(contrasts["strict"]["c"])):
        raise ExportError("recomputed discordant counts differ from contrasts.csv")

    sizes = {}
    for blk in doc["blocks"]:
        for mm in blk["loaded_after"]:
            sizes[mm["name"]] = max(sizes.get(mm["name"], 0), mm["size"])
    mem = {"Q4": sizes["llama3.1:8b"] / 2**20, "Q8": sizes["llama3.1:8b-instruct-q8_0"] / 2**20}
    wall = sum(blk["wall_s"] for blk in doc["blocks"])

    q4, q8 = metrics["Q4"], metrics["Q8"]
    cs, cl = contrasts["strict"], contrasts["lenient"]
    e1 = expl["E1_latency_ratio"]
    e2 = expl["E2_decode_and_memory"]
    e5 = expl["E5_discordance_and_format"]

    def acc_row(label, arm, key, expected, mid):
        v = float(metrics[arm][key])
        return est(label, "confirmatory, measured", v, ck.text(f3(v), expected, (mid,)),
                   interval_kind="none published per arm (the paired difference carries the interval)",
                   unit="proportion of 300 items", manifest_ids=[mid])

    exp003_est = [
        est("Strict accuracy difference, Q8_0 minus Q4_K_M (primary)", "confirmatory, measured",
            float(cs["delta_pp"]), ck.text(pp(float(cs["delta_pp"])), "+1.67", ("N-002",)),
            ci=(float(cs["ci_low_pp"]), float(cs["ci_high_pp"])), ci_level=0.95,
            interval_kind="95 % paired bootstrap interval over items (10,000 resamples, seed 7)",
            interval_display=ck.text(iv(float(cs["ci_low_pp"]), float(cs["ci_high_pp"]), pp),
                                     "[-1.00, +4.33]", ("N-002",)),
            unit="percentage points", manifest_ids=["N-002"]),
        est("Exact McNemar p (strict), discordant b = 11, c = 6", "confirmatory, measured",
            float(cs["mcnemar_p"]), ck.text(f3(float(cs["mcnemar_p"])), "0.332", ("N-002",)),
            interval_kind="test statistic, no interval", unit="p-value", manifest_ids=["N-002"]),
        est("Lenient accuracy difference (S2)", "confirmatory, measured",
            float(cl["delta_pp"]), ck.text(pp(float(cl["delta_pp"])), "+1.67", ("N-002",)),
            ci=(float(cl["ci_low_pp"]), float(cl["ci_high_pp"])), ci_level=0.95,
            interval_kind="95 % paired bootstrap interval over items",
            interval_display=ck.text(iv(float(cl["ci_low_pp"]), float(cl["ci_high_pp"]), pp),
                                     "[-1.00, +4.33]", ("N-002",)),
            unit="percentage points", manifest_ids=["N-002"]),
        acc_row("Strict accuracy, Q4_K_M (baseline)", "Q4", "accuracy_strict", "0.717", "N-001"),
        acc_row("Strict accuracy, Q8_0", "Q8", "accuracy_strict", "0.733", "N-001"),
        acc_row("Lenient accuracy, Q4_K_M", "Q4", "accuracy_lenient", "0.720", "N-001"),
        acc_row("Lenient accuracy, Q8_0", "Q8", "accuracy_lenient", "0.737", "N-001"),
    ]
    for arm, name, exp_med, exp_iqr in (("Q4", "Q4_K_M", "477.5", "[472.9, 603.2]"),
                                        ("Q8", "Q8_0", "437.7", "[434.3, 547.2]")):
        m = metrics[arm]
        lo, hi = float(m["latency_ms_q1"]), float(m["latency_ms_q3"])
        exp003_est.append(est(
            f"Median of per-item median end-to-end latency, {name}", "confirmatory, measured, descriptive",
            float(m["latency_ms_median"]), ck.text(f1(float(m["latency_ms_median"])), exp_med, ("N-004",)),
            ci=(lo, hi), interval_kind="interquartile range over the 300 items, not a confidence interval",
            interval_display=ck.text(iv(lo, hi, f1), exp_iqr, ("N-004",)), unit="ms", manifest_ids=["N-004"]))
    for label, key, exp4, exp8, fmt, unit, mid in (
        ("Median time to first token over records", "ttft_ms_median", "440.9", "388.7", f1, "ms", "N-005"),
        ("Median decode throughput over records", "decode_tps_median", "53.9", "40.1", f1, "tokens/s", "N-005"),
        ("Median prefill throughput over records", "prefill_tps_median", "214.4", "245.3", f1, "tokens/s", "N-005"),
    ):
        for arm, name, expected in (("Q4", "Q4_K_M", exp4), ("Q8", "Q8_0", exp8)):
            v = float(metrics[arm][key])
            exp003_est.append(est(f"{label}, {name}", "confirmatory, measured, descriptive", v,
                                  ck.text(fmt(v), expected, (mid,)),
                                  interval_kind="no interval published (descriptive median)",
                                  unit=unit, manifest_ids=[mid]))
    for arm, name, expected in (("Q4", "Q4_K_M", "5,872.0"), ("Q8", "Q8_0", "9,162.4")):
        if not close(mem[arm], e2["runtime_model_mib"][doc["manifest"]["arm_runtime"][arm]["model"]]):
            raise ExportError(f"{arm}: memory differs between result.json and the exploratory file")
        exp003_est.append(est(f"Runtime-reported model memory, {name}", "confirmatory, measured (runtime-reported)",
                              mem[arm], ck.text(f1c(mem[arm]), expected, ("N-006",)),
                              interval_kind="deterministic runtime report, no interval",
                              unit="MiB", manifest_ids=["N-006"]))
    exp003_est += [
        est("Latency ratio Q8_0 / Q4_K_M, ratio of medians (exploratory, pending owner reading)",
            "exploratory re-analysis", e1["ratio_of_medians"], ck.text(f3(e1["ratio_of_medians"]), "0.917"),
            ci=tuple(e1["ratio_of_medians_ci"]), ci_level=0.95,
            interval_kind="95 % bootstrap interval over items within one session (exploratory)",
            interval_display=ck.text(iv(*e1["ratio_of_medians_ci"], f3), "[0.916, 0.918]"), unit="ratio"),
        est("Latency ratio Q8_0 / Q4_K_M, median of per-item ratios (exploratory, pending owner reading)",
            "exploratory re-analysis", e1["median_of_item_ratios"], ck.text(f3(e1["median_of_item_ratios"]), "0.916"),
            ci=tuple(e1["median_of_item_ratios_ci"]), ci_level=0.95,
            interval_kind="95 % bootstrap interval over items within one session (exploratory)",
            interval_display=ck.text(iv(*e1["median_of_item_ratios_ci"], f3), "[0.916, 0.917]"), unit="ratio"),
        est("Decode ratio Q8_0 / Q4_K_M over item medians (exploratory)", "exploratory re-analysis",
            e2["decode_ratio_item_medians"], ck.text(f3(e2["decode_ratio_item_medians"]), "0.744", ("N-005",)),
            ci=tuple(e2["decode_ratio_item_medians_ci"]), ci_level=0.95,
            interval_kind="95 % bootstrap interval over items within one session (exploratory)",
            interval_display=ck.text(iv(*e2["decode_ratio_item_medians_ci"], f3), "[0.743, 0.744]"),
            unit="ratio", manifest_ids=["N-005"]),
        est("Strict difference excluding the 5 items with any strict format failure (exploratory, post hoc)",
            "exploratory re-analysis", e5["delta_pp_excluding_items_with_any_strict_format_failure"],
            ck.text(pp(e5["delta_pp_excluding_items_with_any_strict_format_failure"]), "+1.36"),
            interval_kind="no interval (post hoc, not a valid confirmatory analysis)",
            unit="percentage points on 295 items"),
    ]

    sent_001 = est("Requests sent of planned", "confirmatory attempt, failed", 0,
                   ck.text("0 of 4,500 requests", "0 of 4,500 requests", ("N-019",)),
                   interval_kind="no result exists", unit="requests", manifest_ids=["N-019"])
    sent_002 = est("Requests sent of planned", "confirmatory attempt, failed", 0,
                   ck.text("0 of 60 requests", "0 of 60 requests"),
                   interval_kind="no result exists", unit="requests", manifest_ids=["N-019"])

    def reg(e: str) -> dict:
        r = registry[e]
        return {"title": r["title"], "report_path": r["report_path"], "registry_status": r["status"]}

    pending_001 = ("Pending owner decision (DL-011): (a) upgrade Ollama and run the frozen matrices "
                   "unchanged, recording the new runtime version; (b) a new freeze without A2 or with "
                   "another arm; (c) keep both recorded as failed. This page chooses none of them.")
    experiments = [
        {"id": "EXP-001", **{k: v for k, v in reg("EXP-001").items() if k != "registry_status"},
         "status": "confirmatory, failed before any request", "outcome": "failed",
         "verdict": "not testable; experiment failed",
         "estimates": [sent_001], "claim_ids": claims["EXP-001"],
         "notes": ["The run aborted at the per-arm /api/show fingerprint (F8): Ollama 0.9.6 cannot render "
                   "the chat template of ministral-3:8b (HTTP 500, function currentDate not defined). "
                   "No generation request was sent. The study has no evidence on the primary question.",
                   pending_001]},
        {"id": "EXP-002", **{k: v for k, v in reg("EXP-002").items() if k != "registry_status"},
         "status": "confirmatory, failed before any request", "outcome": "failed",
         "verdict": "not testable; experiment failed",
         "estimates": [sent_002], "claim_ids": claims["EXP-002"],
         "notes": ["EXP-002 aborted at the same step for the same reason. No cold-start penalty was "
                   "measured and its ordering hypothesis is untested.", pending_001]},
        {"id": "EXP-003", **{k: v for k, v in reg("EXP-003").items() if k != "registry_status"},
         "status": "confirmatory, complete (3,000 of 3,000 requests)", "outcome": "null",
         "verdict": "H0 not rejected: no detected difference, not equivalence",
         "estimates": exp003_est, "claim_ids": claims["EXP-003"],
         "notes": ["No equivalence margin was frozen, so the interval is not evidence of equivalence. "
                   "Per-arm accuracies carry no published interval; the paired difference does.",
                   "Latency, throughput and memory are secondary and descriptive. Rows labelled "
                   "exploratory come from a re-analysis of committed records (JRN-0009) and carry no "
                   "confirmatory weight."]},
    ]

    arms_meta = doc["manifest"]["arm_runtime"]
    frontier = {
        "note": "Measured values from RUN-EXP-003-0001 only. Accuracy is strict accuracy on 300 items. "
                "Memory is the runtime-reported /api/ps size. Latency is the median of per-item medians "
                "with the interquartile range over items.",
        "arms": [
            {"arm": arm, "model": arms_meta[arm]["model"], "quantization": arms_meta[arm]["quantization_level"],
             "accuracy_strict": float(metrics[arm]["accuracy_strict"]),
             "accuracy_display": f3(float(metrics[arm]["accuracy_strict"])),
             "memory_mib": mem[arm], "memory_display": f1c(mem[arm]),
             "latency_ms": float(metrics[arm]["latency_ms_median"]),
             "latency_q1_ms": float(metrics[arm]["latency_ms_q1"]),
             "latency_q3_ms": float(metrics[arm]["latency_ms_q3"]),
             "latency_display": f1(float(metrics[arm]["latency_ms_median"])),
             "latency_iqr_display": iv(float(metrics[arm]["latency_ms_q1"]), float(metrics[arm]["latency_ms_q3"]), f1),
             "decode_tps": float(metrics[arm]["decode_tps_median"]),
             "decode_display": f1(float(metrics[arm]["decode_tps_median"]))}
            for arm in ("Q4", "Q8")
        ],
        "not_measured": [
            {"arm": "A0", "model": "phi4-mini:3.8b (Q4_K_M)", "experiment": "EXP-001, EXP-002",
             "reason": "experiment failed before any request"},
            {"arm": "A1", "model": "llama3.1:8b (Q4_K_M)", "experiment": "EXP-001, EXP-002",
             "reason": "experiment failed before any request (the same model is the EXP-003 baseline, "
                       "but EXP-001 results do not exist)"},
            {"arm": "A2", "model": "ministral-3:8b (Q4_K_M)", "experiment": "EXP-001, EXP-002",
             "reason": "Ollama 0.9.6 cannot render its chat template"},
        ],
    }
    for a in frontier["arms"]:
        for key in ("accuracy_display", "memory_display", "latency_display", "latency_iqr_display", "decode_display"):
            ck.text(a[key], a[key])

    item_rows = [
        {"id": i,
         "q4_strict": items[i]["Q4"]["strict"], "q8_strict": items[i]["Q8"]["strict"],
         "q4_lenient": items[i]["Q4"]["lenient"], "q8_lenient": items[i]["Q8"]["lenient"],
         "q4_latency_ms": items[i]["Q4"]["latency_ms"], "q8_latency_ms": items[i]["Q8"]["latency_ms"],
         "strict_miss_any": items[i]["Q4"]["strict_miss"] or items[i]["Q8"]["strict_miss"]}
        for i in ids
    ]
    if sum(r["strict_miss_any"] for r in item_rows) != 300 - e5["n_items_kept"]:
        raise ExportError("strict-miss items differ from the exploratory E5 count")

    sens = [{"check": r[0], "status": r[1], "result": r[2]}
            for r in manuscript_table("Table 4. Sensitivity analyses")]
    if len(sens) < 4:
        raise ExportError("sensitivity table too short")

    pending = [
        {"id": "TOKEN-EXP-001-002", "title": "Next step for EXP-001 and EXP-002",
         "status": "pending owner decision",
         "readings": ["(a) upgrade Ollama and run the frozen matrices unchanged, recording the new runtime version",
                      "(b) a new freeze without A2 or with another arm",
                      "(c) keep both recorded as failed"],
         "source": "DL-011, DL-012; manuscript section 5.2"},
        {"id": "TOKEN-LATENCY-RATIO", "title": "Reading of the frozen latency-ratio interval (protocol section 8)",
         "status": "pending owner decision",
         "readings": [f"ratio of medians: {f3(e1['ratio_of_medians'])} {iv(*e1['ratio_of_medians_ci'], f3)} (exploratory)",
                      f"median of per-item ratios: {f3(e1['median_of_item_ratios'])} "
                      f"{iv(*e1['median_of_item_ratios_ci'], f3)} (exploratory)"],
         "source": "DL-011 gap 1; manuscript sections 4.5 and 5.4"},
    ]
    for p in pending[1]["readings"]:
        ck.text(p.split(": ", 1)[1].replace(" (exploratory)", ""), p.split(": ", 1)[1].replace(" (exploratory)", ""))

    assumptions = [
        {"name": "Runtime and machine", "value": "Ollama 0.9.6 on one Apple M1 Pro laptop (16 GB), AC power",
         "source": "measured setting, RUN-EXP-003-0001 run manifest"},
        {"name": "Decoding", "value": "template T1, temperature 0, num_predict 8, num_ctx 2048, runtime seeds 0 to 4",
         "source": "frozen EXP-003 config"},
        {"name": "Benchmark subset", "value": "300 ARC-Challenge test items drawn once with seed 20261124",
         "source": "frozen protocol; data/arc_challenge_test_subset_ids.json"},
        {"name": "Planning discordant proportion", "value": "0.25 (planning value, not a measurement)",
         "source": "main protocol section 7"},
        {"name": "Minimum detectable difference", "value": "about 9 points at 80 % power (planning value)",
         "source": "main protocol section 7"},
        {"name": "Equivalence margin", "value": "none frozen, so no equivalence test is possible",
         "source": "main protocol section 2; DL-012"},
        {"name": "Power draw for modelled energy", "value": "none stated in the frozen protocol; S4 was not run",
         "source": "DL-012 decision 4; the modelled-energy panel uses only a value the visitor enters"},
    ]

    return {
        "schema": "lab-demo-results",
        "schema_version": "1.0.0",
        "project": "TOKEN",
        "question": "How do local model configurations trade off quality, latency and resource use?",
        "status_label": ("Independent research manuscript / preprint draft, not peer-reviewed. One confirmatory "
                         "experiment complete (EXP-003, null result); two failed before any request (EXP-001, "
                         "EXP-002). Owner decisions pending."),
        "code_revision": _revision(),
        "run_code_revision": doc["manifest"]["git"]["revision"],
        "run_wall_s": wall,
        "sources": [{"path": p, "sha256": _sha256(p)} for p in SOURCES],
        "experiments": experiments,
        "assumptions": assumptions,
        "limitations": manuscript_limitations(),
        "frontier": frontier,
        "items": item_rows,
        "sandbox_reference": {
            "note": "Published Python results the sandbox can be compared with (contrasts.csv).",
            "strict": {"delta_pp": float(cs["delta_pp"]), "ci_low_pp": float(cs["ci_low_pp"]),
                       "ci_high_pp": float(cs["ci_high_pp"]), "b": int(cs["b"]), "c": int(cs["c"]),
                       "mcnemar_p": float(cs["mcnemar_p"])},
            "lenient": {"delta_pp": float(cl["delta_pp"]), "ci_low_pp": float(cl["ci_low_pp"]),
                        "ci_high_pp": float(cl["ci_high_pp"]), "b": int(cl["b"]), "c": int(cl["c"]),
                        "mcnemar_p": float(cl["mcnemar_p"])},
        },
        "sensitivity": sens,
        "pending_owner_decisions": pending,
        "display_exceptions": [],
    }


def render(data: dict) -> str:
    return json.dumps(data, indent=1, sort_keys=False, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    text = render(build())
    if "--check" in argv:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("results.json up to date" if same else "results.json differs from the export")
        return 0 if same else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
