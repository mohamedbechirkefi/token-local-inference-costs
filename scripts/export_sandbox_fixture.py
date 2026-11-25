# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Sandbox fixture for the demo's vitest (M5): Python engine output on committed data.

Runs the research engine's paired statistics (``token_lab.stats.paired_compare``:
paired bootstrap over items, 10,000 resamples, seed 7, and the exact McNemar test)
on the per-item correctness exported in ``demo/public/data/results.json`` for the
three sandbox scenarios, plus ``mcnemar_exact`` on a small grid of discordant counts.
Writes ``demo/src/engine.fixture.json``. One process, under a second of compute; no
inference and no runtime contact.

Usage: ``.venv/bin/python scripts/export_sandbox_fixture.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from token_lab.stats import mcnemar_exact, paired_compare  # noqa: E402

DATA = ROOT / "demo/public/data/results.json"
OUT = ROOT / "demo/src/engine.fixture.json"

SCENARIOS = [
    ("strict", "all"),
    ("lenient", "all"),
    ("strict", "exclude_strict_miss"),
]


def build() -> dict:
    items = json.loads(DATA.read_text(encoding="utf-8"))["items"]
    rows = []
    for extraction, subset in SCENARIOS:
        keep = [r for r in items if subset == "all" or not r["strict_miss_any"]]
        cand = [r[f"q8_{extraction}"] for r in keep]
        base = [r[f"q4_{extraction}"] for r in keep]
        pd = paired_compare(cand, base, n_boot=10_000, seed=7)
        rows.append({"extraction": extraction, "subset": subset, "n": pd.n,
                     "delta": pd.delta, "ci_low": pd.ci_low, "ci_high": pd.ci_high,
                     "b": pd.b, "c": pd.c, "mcnemar_p": pd.mcnemar_p})
    grid = [{"b": b, "c": c, "p": mcnemar_exact(b, c)}
            for b, c in ((0, 0), (1, 0), (11, 6), (6, 11), (5, 5), (20, 3), (0, 25), (40, 31))]
    return {"generator": "scripts/export_sandbox_fixture.py (token_lab.stats, numpy default_rng(7))",
            "n_boot": 10_000, "seed": 7, "scenarios": rows, "mcnemar_grid": grid}


def render(data: dict) -> str:
    return json.dumps(data, indent=1) + "\n"


if __name__ == "__main__":
    OUT.write_text(render(build()), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
