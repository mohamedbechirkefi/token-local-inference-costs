# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Report generator: tables and figures built only from a validated result file.

PDF route (DL-002): pandoc Markdown to Typst with ``-V mainfont="Libertinus
Serif"``, compiled by the ``typst`` Python package of the shared tools
environment. The PDF is optional and its build failure is reported, never hidden.
"""

from __future__ import annotations

import csv
import html
import subprocess
from pathlib import Path

from .analysis import arm_summaries, contrasts, projection
from .schema import import_result

PANDOC = "/Users/bechir/research/labs/.tools/pandoc"
TYPST_PY = "/Users/bechir/research/labs/.tools/py/bin/python"

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


def build_report(result_path: str | Path, out_dir: str | Path | None = None, pdf: bool = False) -> dict:
    doc = import_result(result_path)  # fail closed on malformed input
    rp = Path(result_path)
    out = Path(out_dir) if out_dir else rp.parent
    out.mkdir(parents=True, exist_ok=True)
    sums = arm_summaries(doc)
    cons = contrasts(doc, "strict") + contrasts(doc, "lenient")
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
        "## Per-arm metrics", "",
        "Accuracy: per-item mean over repetitions, then mean over items. Latency: per-item median "
        "over repetitions, then median [Q1, Q3] over items (ms).", "",
        "| Arm | Model | n | Acc. strict | Acc. lenient | Chance | Errors | Format fail (strict) | "
        "Latency median [Q1, Q3] ms | TTFT ms | Decode tok/s | Determinism | Peak RSS MiB |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in sums:
        if not s["n_records"]:
            lines.append(f"| {s['arm']} | | 0 | | | | | | | | | | |")
            continue
        lines.append(
            f"| {s['arm']} | {s['model']} | {s['n_items']} | {_fmt(s['accuracy_strict'])} | "
            f"{_fmt(s['accuracy_lenient'])} | {_fmt(s['chance'])} | {s['errors']} | {s['format_fail_strict']} | "
            f"{_fmt(s['latency_ms_median'], 2)} [{_fmt(s['latency_ms_q1'], 2)}, {_fmt(s['latency_ms_q3'], 2)}] | "
            f"{_fmt(s['ttft_ms_median'], 2)} | {_fmt(s['decode_tps_median'], 1)} | {_fmt(s['determinism'], 2)} | "
            f"{_fmt(s['peak_rss_mib'], 1)} |")
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
    if pdf:
        info.update(build_pdf(md))
    return info


def build_pdf(md: Path) -> dict:
    typ = md.with_suffix(".typ")
    pdf = md.with_suffix(".pdf")
    try:
        subprocess.run([PANDOC, str(md), "-s", "-t", "typst", "-V", 'mainfont=Libertinus Serif', "-o", str(typ)],
                       check=True, capture_output=True, text=True, timeout=120)
        subprocess.run([TYPST_PY, "-c", "import sys, typst; typst.compile(sys.argv[1], output=sys.argv[2])",
                        str(typ), str(pdf)], check=True, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        err = getattr(exc, "stderr", None) or str(exc)
        return {"pdf": None, "pdf_error": str(err)[:500]}
    finally:
        if typ.exists():
            typ.unlink()
    return {"pdf": str(pdf), "pdf_error": None}
