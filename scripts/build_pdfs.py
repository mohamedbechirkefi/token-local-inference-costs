# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Build the committed PDFs and the generated LaTeX source (M6, DL-014).

Builds, with the repository builder ``token_lab.report.build_pdf`` (pandoc to
Typst, compiled by the ``typst`` package of the shared tools, DL-002):

- ``research/paper/manuscript.pdf`` (Typst root ``research/``, because FIG-001
  is referenced as ``../experiments/EXP-003/figures/...``);
- ``research/paper/supplementary.pdf``;
- ``research/experiments/EXP-NNN/report.pdf`` for every experiment report;

and regenerates ``research/paper/manuscript.tex`` with pandoc (not compiled;
no TeX distribution, DL-002), with an SPDX comment as its first line.

Usage: ``.venv/bin/python -I scripts/build_pdfs.py`` from the repository root.
Prints one line per file with its page count; exit code 1 if any build fails.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from token_lab.report import PANDOC, build_pdf  # noqa: E402

SPDX_TEX = "% SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0\n"


def targets() -> list[tuple[Path, Path]]:
    paper = ROOT / "research" / "paper"
    out = [(paper / "manuscript.md", ROOT / "research"), (paper / "supplementary.md", paper)]
    for rep in sorted((ROOT / "research" / "experiments").glob("EXP-*/report.md")):
        out.append((rep, rep.parent))
    return out


def main() -> int:
    failed = 0
    for md, root in targets():
        info = build_pdf(md, root=root)
        rel = md.with_suffix(".pdf").relative_to(ROOT)
        if info["pdf"] is None:
            failed += 1
            print(f"FAIL {rel}: {info['pdf_error']}")
        else:
            print(f"built {rel}: {info['pages']} pages")
    paper = ROOT / "research" / "paper"
    subprocess.run([PANDOC, "manuscript.md", "-s", "-t", "latex", "-o", "manuscript.tex"], check=True, cwd=str(paper))
    tex = paper / "manuscript.tex"
    tex.write_text(SPDX_TEX + tex.read_text(encoding="utf-8"), encoding="utf-8")
    print("wrote research/paper/manuscript.tex")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
