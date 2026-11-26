# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Report generator: tables and figures built only from a validated result file.

PDF route (DL-002): pandoc Markdown to Typst with ``-V mainfont="Libertinus
Serif"``, compiled by the ``typst`` Python package of the shared tools
environment. The PDF is optional and its build failure is reported, never hidden.
"""

from __future__ import annotations

import csv
import html
import os
import re
import subprocess
from pathlib import Path

from .analysis import arm_summaries, cold_warm_ordering, cold_warm_penalties, contrasts, projection
from .schema import import_result

# Shared zero-cost toolchain (DL-002) in the labs folder that contains this repository (src/token_lab/ -> repo -> labs);
# override with TOKEN_PANDOC / TOKEN_TYPST_PYTHON on other machines.
_TOOLS = Path(__file__).resolve().parents[3] / ".tools"
PANDOC = os.environ.get("TOKEN_PANDOC", str(_TOOLS / "pandoc"))
TYPST_PY = os.environ.get("TOKEN_TYPST_PYTHON", str(_TOOLS / "py" / "bin" / "python"))

METRIC_COLUMNS = [
    "arm", "model", "n_records", "n_items", "accuracy_strict", "accuracy_lenient", "chance", "errors",
    "format_fail_strict", "format_fail_lenient", "latency_ms_median", "latency_ms_q1", "latency_ms_q3",
    "ttft_ms_median", "decode_tps_median", "prefill_tps_median", "determinism", "peak_rss_mib",
    "swap_delta_mib_max", "rep_latency_cv",
]


def _fmt(v, nd: int = 3) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        if v != 0 and abs(v) < 10 ** (-nd):
            return f"{v:.3g}"
        return f"{v:.{nd}f}"
    return str(v)


def latency_svg(summaries: list[dict], title: str) -> str:
    """Strip plot of per-item median latency (ms) per arm, log-free linear axis."""
    w, left, right, top, bottom = 640, 150, 30, 50, 50
    h = top + 60 * len(summaries) + 20 + bottom
    vals = [v for s in summaries for v in s.get("item_latency_ms", [])]
    vmax = max(vals) if vals else 1.0
    vmax = vmax * 1.05 if vmax > 0 else 1.0
    sx = lambda v: left + (w - left - right) * v / vmax  # noqa: E731
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
             f'font-family="Helvetica, Arial, sans-serif" font-size="12">',
             f'<title>{html.escape(title)}</title>',
             f'<rect width="{w}" height="{h}" fill="white"/>',
             f'<text x="{left}" y="24" font-size="13">{html.escape(title)}</text>']
    y_axis = h - bottom
    parts.append(f'<line x1="{left}" y1="{y_axis}" x2="{w - right}" y2="{y_axis}" stroke="#333"/>')
    for k in range(6):
        v = vmax * k / 5
        x = sx(v)
        parts.append(f'<line x1="{x:.1f}" y1="{y_axis}" x2="{x:.1f}" y2="{y_axis + 4}" stroke="#333"/>')
        parts.append(f'<text x="{x:.1f}" y="{y_axis + 18}" text-anchor="middle">{v:.3g}</text>')
    parts.append(f'<text x="{(left + w - right) / 2}" y="{h - 10}" text-anchor="middle">'
                 'per-item median latency (ms)</text>')
    for i, s in enumerate(summaries):
        y = top + 30 + 60 * i
        parts.append(f'<text x="{left - 10}" y="{y + 4}" text-anchor="end">'
                     f'{html.escape(s["arm"])} {html.escape(s.get("model", ""))}</text>')
        for v in s.get("item_latency_ms", []):
            parts.append(f'<circle cx="{sx(v):.1f}" cy="{y}" r="3" fill="#1f4e79" fill-opacity="0.6"/>')
        if s.get("latency_ms_median") is not None:
            x = sx(s["latency_ms_median"])
            parts.append(f'<line x1="{x:.1f}" y1="{y - 12}" x2="{x:.1f}" y2="{y + 12}" stroke="#b03a2e" stroke-width="2"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


COLD_WARM_COLUMNS = [
    "arm", "model", "n_cold", "n_warm", "n_cold_records", "n_warm_records", "n_cold_invalid", "n_warm_invalid",
    "n_cold_error", "n_warm_error", "cold_ttft_ms_median", "cold_ci_low", "cold_ci_high", "warm_ttft_ms_median",
    "warm_ci_low", "warm_ci_high", "penalty_ms", "penalty_ci_low", "penalty_ci_high", "cold_load_ms_median",
    "warm_load_ms_median", "cold_latency_ms_median", "warm_latency_ms_median",
]


def cold_warm_svg(rows: list[dict], title: str) -> str:
    """Raw trial TTFT (ms) per arm and start state (EXP-002 item 16), linear axis."""
    w, left, right, top, bottom = 640, 170, 30, 50, 50
    h = top + 40 * 2 * len(rows) + 20 + bottom
    vals = [v for r in rows for v in r["cold_ttft_ms"] + r["warm_ttft_ms"]]
    vmax = max(vals) * 1.05 if vals and max(vals) > 0 else 1.0
    sx = lambda v: left + (w - left - right) * v / vmax  # noqa: E731
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
             f'font-family="Helvetica, Arial, sans-serif" font-size="12">',
             f'<title>{html.escape(title)}</title>', f'<rect width="{w}" height="{h}" fill="white"/>',
             f'<text x="{left}" y="24" font-size="13">{html.escape(title)}</text>']
    y_axis = h - bottom
    parts.append(f'<line x1="{left}" y1="{y_axis}" x2="{w - right}" y2="{y_axis}" stroke="#333"/>')
    for k in range(6):
        v = vmax * k / 5
        x = sx(v)
        parts.append(f'<line x1="{x:.1f}" y1="{y_axis}" x2="{x:.1f}" y2="{y_axis + 4}" stroke="#333"/>')
        parts.append(f'<text x="{x:.1f}" y="{y_axis + 18}" text-anchor="middle">{v:.4g}</text>')
    parts.append(f'<text x="{(left + w - right) / 2}" y="{h - 10}" text-anchor="middle">'
                 'time to first token per trial (ms)</text>')
    i = 0
    for r in rows:
        for st, colour in (("cold", "#1f4e79"), ("warm", "#b9770e")):
            y = top + 30 + 40 * i
            i += 1
            parts.append(f'<text x="{left - 10}" y="{y + 4}" text-anchor="end">'
                         f'{html.escape(r["arm"])} {html.escape(r["model"])} {st}</text>')
            for v in r[f"{st}_ttft_ms"]:
                parts.append(f'<circle cx="{sx(v):.1f}" cy="{y}" r="3" fill="{colour}" fill-opacity="0.6"/>')
            med, lo, hi = r[f"{st}_ttft_ms_median"], r[f"{st}_ci_low"], r[f"{st}_ci_high"]
            if med is not None:
                parts.append(f'<line x1="{sx(lo):.1f}" y1="{y + 9}" x2="{sx(hi):.1f}" y2="{y + 9}" stroke="#b03a2e"/>')
                parts.append(f'<line x1="{sx(med):.1f}" y1="{y - 9}" x2="{sx(med):.1f}" y2="{y + 9}" '
                             f'stroke="#b03a2e" stroke-width="2"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _rules_lines(doc: dict) -> list[str]:
    """Block-rule provenance (protocol section 9; DL-017). Empty for runs made
    before the rules were enforced, so their reports regenerate unchanged."""
    m = doc["manifest"]
    br, ro, comb = m.get("block_rules"), m.get("repeat_of"), m.get("combination")
    if not (br or ro or comb):
        return []
    out = ["## Block rules (protocol section 9)", ""]
    if comb:
        rb = ", ".join(f"block {b['block_index']} ({b['arm']}, repetition {b['repetition']})"
                       for b in comb["replaced_blocks"])
        out += [f"- Combined analysis input: {comb['source_run_id']} with {rb} replaced by the repeat run "
                f"{comb['repeat_run_id']} ({comb['rule']}). Source result SHA-256 `{comb['source_result_sha256']}`.",
                f"- Blocks in the analysis: {comb['n_blocks']} of {comb['n_planned_blocks']} planned; missing: "
                f"{', '.join(str(k) for k in comb['blocks_missing']) or 'none'}. Status: **{comb['status']}**. "
                f"Total runtime of both runs: {comb['runtime_s_total']:.1f} s."]
    elif ro:
        rb = ", ".join(f"block {b['block_index']} ({b['arm']}, repetition {b['repetition']})"
                       for b in ro["replaced_blocks"])
        out += [f"- Block repeat of {ro['source_run_id']} (SHA-256 `{ro['source_result_sha256']}`): {rb}."]
        for b in ro["replaced_blocks"]:
            crit = "; ".join(b["source_exclusion"] + ([b["source_stopping"]] if b["source_stopping"] else []))
            out.append(f"- Source block {b['block_index']} criteria: {crit}.")
    if br:
        out.append(f"- Rule outcome: **{br['status']}**" + (f" ({br['status_reason']})" if br["status_reason"] else "")
                   + f". Thresholds: swap growth above {br['thresholds']['swap_exclude_mib']:.0f} MiB excludes, "
                   f"above {br['thresholds']['swap_abort_mib']:.0f} MiB aborts; wall-clock cap "
                   f"{br['thresholds']['wall_cap_s']:.0f} s.")
        for e in br["exclusions"]:
            out.append(f"- Block {e['block_index']} ({e['arm']}, repetition {e['repetition']}, attempt {e['attempt']}): "
                       f"{e['outcome']}; {'; '.join(e['reasons']) or 'no criterion'}.")
    out += ["", "| Block | Arm | Repetition | Origin | Status | Swap delta (MiB) | Peak swap growth (MiB) | "
            "Loaded before | Loaded after |", "|---|---|---|---|---|---|---|---|---|"]
    for pos, b in enumerate(doc["blocks"] + doc.get("excluded_blocks", []), start=1):
        mem = b["memory"]
        names = lambda lst: ", ".join(x.get("name") or "?" for x in (lst or [])) or "none"  # noqa: E731
        pk = mem.get("peak_swap_growth_mib")
        out.append(f"| {b.get('block_index', pos)} | {b['arm']} | {b['repetition']} | {b.get('origin', doc['run_id'])} | "
                   f"{b.get('status', 'included (rules not enforced)')} | {mem.get('swap_delta_mib', 0.0):.1f} | "
                   f"{'n/a' if pk is None else f'{pk:.1f}'} | {names(b['loaded_before'])} | {names(b['loaded_after'])} |")
    return out + [""]


def build_report(result_path: str | Path, out_dir: str | Path | None = None, pdf: bool = False) -> dict:
    doc = import_result(result_path)  # fail closed on malformed input
    rp = Path(result_path)
    out = Path(out_dir) if out_dir else rp.parent
    out.mkdir(parents=True, exist_ok=True)
    sums = arm_summaries(doc)
    cold_warm = doc["manifest"].get("design") == "cold_warm"
    # accuracy contrasts on EXP-002's single fixed prompt carry no information
    cons = [] if cold_warm else contrasts(doc, "strict") + contrasts(doc, "lenient")
    cw_rows = cold_warm_penalties(doc) if cold_warm else []
    proj = projection(doc)
    sim = doc["backend"]["simulated"]

    with open(out / "metrics.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=METRIC_COLUMNS, extrasaction="ignore")
        wr.writeheader()
        for s in sums:
            wr.writerow({k: s.get(k) for k in METRIC_COLUMNS})
    if cons:
        with open(out / "contrasts.csv", "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(cons[0].keys()))
            wr.writeheader()
            wr.writerows(cons)
    if cold_warm:
        with open(out / "cold_warm.csv", "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=COLD_WARM_COLUMNS, extrasaction="ignore")
            wr.writeheader()
            for r in cw_rows:
                wr.writerow({k: r.get(k) for k in COLD_WARM_COLUMNS})
        cw_title = f"{doc['run_id']}: cold and warm TTFT" + (" (SIMULATED backend)" if sim else "")
        (out / "cold_warm.svg").write_text(cold_warm_svg(cw_rows, cw_title), encoding="utf-8")
    fig_title = f"{doc['run_id']}: per-item latency" + (" (SIMULATED backend)" if sim else "")
    (out / "latency.svg").write_text(latency_svg(sums, fig_title), encoding="utf-8")

    banner = [f"**Label: {doc['label'].upper()}.**"]
    if doc["label"] == "exploratory":
        banner.append("Exploratory output; not a finding and not usable for confirmatory analysis.")
    if sim:
        banner.append("Backend is SIMULATED: no model ran. Accuracy values are artefacts of a hash "
                      "function and latencies measure the harness only.")
    if doc["items_source"]["synthetic"]:
        banner.append("Items are a synthetic fixture, not a benchmark.")
    m = doc["manifest"]
    lines = [
        "<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->",
        f"# Run report {doc['run_id']}", "",
        " ".join(banner), "",
        "## Provenance", "",
        f"- Experiment: {doc['exp_id']}; run: {doc['run_id']}; schema {doc['schema_version']}",
        f"- Config SHA-256: `{doc['config_sha256']}`",
        f"- Protocol SHA-256: `{m.get('protocol_sha256')}`",
        f"- Git revision: `{m['git'].get('revision')}` (dirty: {m['git'].get('dirty')})",
        f"- Backend: {doc['backend']['name']} (simulated: {sim}), runtime version {doc['backend']['runtime_version']}",
        f"- Items: `{doc['items_source']['path']}`, {doc['items_source']['n_items']} items, "
        f"SHA-256 `{doc['items_source']['sha256']}`",
        f"- Host: {m['host']['before'].get('cpu')}, {m['host']['before'].get('os')}, "
        f"power {m['host']['before'].get('power', {}).get('source')}, "
        f"load average at start {[round(x, 2) for x in m['host']['before'].get('load_avg_1_5_15', [])]}",
        f"- Start {m['start_utc']}, end {m['end_utc']}, runtime {m['runtime_s']:.3f} s, "
        f"{m['n_requests']} requests, {m['n_failures']} failures",
        f"- Harness peak RSS: {m['harness_peak_rss_mib']:.1f} MiB", "",
        *_rules_lines(doc),
        "## Per-arm metrics", "",
        "Accuracy: per-item mean over repetitions, then mean over items. Latency: per-item median "
        "over repetitions, then median [Q1, Q3] over items (ms).", "",
        "| Arm | Model | n items | Acc. strict | Acc. lenient | Chance | Errors | Format fail strict | Format fail lenient |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in sums:
        if not s["n_records"]:
            lines.append(f"| {s['arm']} | | 0 | | | | | | |")
            continue
        lines.append(
            f"| {s['arm']} | {s['model']} | {s['n_items']} | {_fmt(s['accuracy_strict'])} | "
            f"{_fmt(s['accuracy_lenient'])} | {_fmt(s['chance'])} | {s['errors']} | {s['format_fail_strict']} | "
            f"{s['format_fail_lenient']} |")
    lines += ["", "| Arm | Latency median [Q1, Q3] (ms) | TTFT median (ms) | Decode (tok/s) | Prefill (tok/s) | "
              "Determinism | Peak RSS (MiB) | Max swap delta (MiB) |", "|---|---|---|---|---|---|---|---|"]
    for s in sums:
        if s["n_records"]:
            lines.append(
                f"| {s['arm']} | {_fmt(s['latency_ms_median'], 2)} [{_fmt(s['latency_ms_q1'], 2)}, "
                f"{_fmt(s['latency_ms_q3'], 2)}] | {_fmt(s['ttft_ms_median'], 2)} | {_fmt(s['decode_tps_median'], 1)} | "
                f"{_fmt(s['prefill_tps_median'], 1)} | {_fmt(s['determinism'], 2)} | {_fmt(s['peak_rss_mib'], 1)} | "
                f"{_fmt(s['swap_delta_mib_max'], 1)} |")
    lines += ["", "## Spread between repetitions (seeds)", "",
              "| Arm | Accuracy per repetition | Median latency per repetition (ms) | CV of repetition medians |",
              "|---|---|---|---|"]
    for s in sums:
        if s["n_records"]:
            lines.append(f"| {s['arm']} | {', '.join(_fmt(x) for x in s['rep_accuracy_strict'])} | "
                         f"{', '.join(_fmt(x, 2) for x in s['rep_latency_ms_median'])} | {_fmt(s['rep_latency_cv'])} |")
    if cons:
        lines += ["", "## Paired contrasts against the baseline", "",
                  "Paired bootstrap over items (10,000 resamples, seed 7, percentile 95 % CI); exact McNemar; "
                  "Holm within each extraction rule.", "",
                  "| Arm vs baseline | Extraction | n | Delta (pp) | 95 % CI (pp) | b | c | McNemar p | Holm p |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for c in cons:
            lines.append(f"| {c['arm']} vs {c['baseline']} | {c['extraction']} | {c['n']} | {c['delta_pp']:.1f} | "
                         f"[{c['ci_low_pp']:.1f}, {c['ci_high_pp']:.1f}] | {c['b']} | {c['c']} | "
                         f"{c['mcnemar_p']:.3g} | {c['holm_p']:.3g} |")
    if cold_warm:
        od = cold_warm_ordering(cw_rows)
        lines += ["", "## Cold-start penalty (EXP-002 items 5, 6 and 16)", "",
                  "Penalty = median cold TTFT minus median warm TTFT (ms) over the valid trials of each arm. "
                  "Percentile 95 % bootstrap CIs over trials (10,000 resamples, seed 7; cold and warm trials "
                  "resampled independently). Load duration and end-to-end latency medians are descriptive.", "",
                  "| Arm | Model | Valid cold / warm | Invalid cold / warm | Cold TTFT median [95 % CI] (ms) | "
                  "Warm TTFT median [95 % CI] (ms) | Penalty [95 % CI] (ms) |", "|---|---|---|---|---|---|---|"]
        for r in cw_rows:
            def iv(m, lo, hi):
                return "n/a" if m is None else f"{m:.1f} [{lo:.1f}, {hi:.1f}]"
            lines.append(f"| {r['arm']} | {r['model']} | {r['n_cold']} / {r['n_warm']} | {r['n_cold_invalid']} / "
                         f"{r['n_warm_invalid']} | {iv(r['cold_ttft_ms_median'], r['cold_ci_low'], r['cold_ci_high'])} | "
                         f"{iv(r['warm_ttft_ms_median'], r['warm_ci_low'], r['warm_ci_high'])} | "
                         f"{iv(r['penalty_ms'], r['penalty_ci_low'], r['penalty_ci_high'])} |")
        lines += ["", "| Arm | Cold load median (ms) | Warm load median (ms) | Cold latency median (ms) | "
                  "Warm latency median (ms) |", "|---|---|---|---|---|"]
        for r in cw_rows:
            lines.append(f"| {r['arm']} | {_fmt(r['cold_load_ms_median'], 1)} | {_fmt(r['warm_load_ms_median'], 1)} | "
                         f"{_fmt(r['cold_latency_ms_median'], 1)} | {_fmt(r['warm_latency_ms_median'], 1)} |")
        lines += ["", f"Ordering check by file size ({' < '.join(od['order'])}): **{od['verdict']}**. "
                  f"Reversal: {od['reversal']}; adjacent CI overlap: {od['overlap']}.", "",
                  f"![{cw_title}. Dots: raw trials; red bar: median; red line: 95 % CI.](cold_warm.svg)"]
    lines += ["", "## Projection of planned matrices", "",
              f"Measured seconds per request in this run (block wall time including warm-ups): "
              f"{_fmt(proj['seconds_per_request'], 4)}."
              + (" The backend is simulated, so this projection says nothing about inference time." if sim else ""),
              "", "| Planned experiment | Planned requests | Projected hours |", "|---|---|---|"]
    from .analysis import PLANNED_REQUESTS
    for k, v in PLANNED_REQUESTS.items():
        lines.append(f"| {k} | {v} | {_fmt(proj['projected_hours'][k], 4)} |")
    if doc["failures"]:
        lines += ["", "## Failures", ""]
        for f in doc["failures"]:
            lines.append(f"- {f.get('stage')} {f.get('arm')} rep {f.get('repetition')} item {f.get('item_id')}: {f.get('error')}")
    lines += ["", "## Figure", "",
              f"![{fig_title}. Dots: per-item median latency in ms; red bar: median over items. "
              f"n = {sums[0].get('n_items', 0) if sums else 0} items per arm.](latency.svg)", ""]
    md = out / "report.md"
    md.write_text("\n".join(lines), encoding="utf-8")
    info = {"report_md": str(md), "metrics_csv": str(out / "metrics.csv"), "figure": str(out / "latency.svg"),
            "pdf": None, "pdf_error": None}
    if cold_warm:
        info.update({"cold_warm_csv": str(out / "cold_warm.csv"), "cold_warm_figure": str(out / "cold_warm.svg")})
    if pdf:
        info.update(build_pdf(md))
    return info


# M6 layout rules (DL-014): long tables may break across pages; table and list cells are not justified;
# table text is 9 pt so that 64-character hashes fit their column.
TYPST_PREAMBLE = ("#show figure.where(kind: table): set block(breakable: true)\n"
                  "#show table: set par(justify: false)\n"
                  "#show list: set par(justify: false)\n"
                  "#show table: set text(size: 9pt)\n")


def pdf_title(md: str) -> str | None:
    """PDF metadata title: the first level-1 heading of a Markdown file without a
    YAML ``title`` (pandoc sets that one itself)."""
    if md.startswith("---") and re.search(r"^title:", md.split("\n---", 1)[0], re.M):
        return None
    m = re.search(r"^# (.+)$", md, re.M)
    return m.group(1).strip() if m else None


def typst_layout_fixes(typ: str, title: str | None = None) -> str:
    """Return pandoc's Typst source with the M6 layout rules and, if given, the title."""
    if title:
        esc = title.replace("\\", "\\\\").replace('"', '\\"')
        typ, n = re.subn(r"(set document\(\s*title: )title,", lambda m: f'{m.group(1)}"{esc}",', typ, count=1)
        if n == 0:
            raise ValueError("pandoc Typst template: set document(title: ...) not found")
    return TYPST_PREAMBLE + typ


def build_pdf(md: Path, pdf_path: Path | None = None, root: Path | None = None) -> dict:
    """Markdown to Typst (pandoc) to PDF (typst package). ``root`` is the Typst
    project root and pandoc resource path (default: the Markdown file's folder);
    figures referenced outside it need a wider root. Returns pdf path, page count
    or the error, never raises on a toolchain failure."""
    md = Path(md).resolve()
    pdf = Path(pdf_path).resolve() if pdf_path else md.with_suffix(".pdf")
    res = Path(root).resolve() if root else md.parent
    typ = md.parent / (pdf.stem + ".m6tmp.typ")
    code = ("import sys, typst, pypdf\n"
            "typst.compile(sys.argv[1], output=sys.argv[2], root=sys.argv[3])\n"
            "print(len(pypdf.PdfReader(sys.argv[2]).pages))\n")
    try:
        subprocess.run([PANDOC, str(md), "-s", "-t", "typst", "-V", 'mainfont=Libertinus Serif', "--wrap=none",
                        "--resource-path", str(md.parent), "-o", str(typ)],
                       check=True, capture_output=True, text=True, timeout=120, cwd=str(md.parent))
        typ.write_text(typst_layout_fixes(typ.read_text(encoding="utf-8"), pdf_title(md.read_text(encoding="utf-8"))),
                       encoding="utf-8")
        out = subprocess.run([TYPST_PY, "-I", "-c", code, str(typ), str(pdf), str(res)],
                             check=True, capture_output=True, text=True, timeout=300, cwd=str(md.parent))
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        err = getattr(exc, "stderr", None) or str(exc)
        return {"pdf": None, "pdf_error": str(err)[:500], "pages": None}
    finally:
        if typ.exists():
            typ.unlink()
    return {"pdf": str(pdf), "pdf_error": None, "pages": int(out.stdout.strip().splitlines()[-1])}
