# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""M6 release-candidate checks (DL-014): relative Markdown links resolve, the
numbers in the README, articles, demo README and CITATION.cff are printed in the
manuscript, CITATION.cff is structurally valid CFF 1.2.0 for a release
candidate, and the PDF builder's layout rules hold."""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

from token_lab.report import TYPST_PREAMBLE, pdf_title, typst_layout_fixes

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("check_links", ROOT / "scripts" / "check_links.py")
check_links = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_links)

# a number with a decimal point or a thousands separator, optionally signed
NUM = re.compile(r"(?<![\w.\-])[+\-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.\-])[+\-]?\d+\.\d+")


def test_every_relative_link_in_the_repository_resolves():
    n, broken = check_links.check(ROOT)
    assert n > 0
    assert broken == []


def test_link_checker_reports_missing_files_and_anchors(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "a.md").write_text("# Title\n\n## Second part\n", encoding="utf-8")
    (tmp_path / "b.md").write_text(
        "[ok](a.md) [anchor](a.md#second-part) [web](https://example.org/x)\n"
        "[gone](missing.md) [bad](a.md#nowhere) `[code](missing2.md)`\n"
        "```\n[fenced](missing3.md)\n```\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.md", "b.md"], check=True)
    n, broken = check_links.check(tmp_path)
    assert n == 4
    assert broken == ["b.md:2: missing.md (missing file)", "b.md:2: a.md#nowhere (missing anchor)"]


@pytest.mark.parametrize("rel", ["README.md", "articles/medium.md", "articles/linkedin.md", "articles/README.md",
                                 "demo/README.md", "CITATION.cff"])
def test_numbers_outside_the_manuscript_are_printed_in_the_manuscript(rel):
    ms = (ROOT / "research" / "paper" / "manuscript.md").read_text(encoding="utf-8")
    text = (ROOT / rel).read_text(encoding="utf-8")
    text = "\n".join(line for line in text.splitlines() if not line.startswith(("cff-version:", "version:")))
    missing = sorted({n for n in NUM.findall(text) if n not in ms and n.lstrip("+") not in ms})
    assert missing == []


def _cff_top_level(text: str) -> dict[str, str]:
    keys: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z][a-z-]*):\s*(.*)$", line)
        if m:
            assert m.group(1) not in keys, f"duplicate key {m.group(1)}"
            keys[m.group(1)] = m.group(2)
    return keys


def test_citation_cff_is_a_structurally_valid_release_candidate():
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    keys = _cff_top_level(text)
    for required in ("cff-version", "message", "title", "authors"):
        assert required in keys
    assert keys["cff-version"] == "1.2.0"
    allowed = {"abstract", "authors", "cff-version", "commit", "contact", "date-released", "doi", "identifiers",
               "keywords", "license", "license-url", "message", "preferred-citation", "references", "repository",
               "repository-artifact", "repository-code", "title", "type", "url", "version"}
    assert set(keys) <= allowed
    assert keys["type"] in ("software", "dataset")
    assert "date-released" not in keys  # removed until a release exists (owner-approvals-2026-11-25e)
    assert re.fullmatch(r'"?\d+\.\d+\.\d+-rc\d+"?', keys["version"])
    assert re.search(r"^  - family-names: \S", text, re.M) and re.search(r"^    given-names: \S", text, re.M)
    assert "@" not in text


def test_pdf_title_and_typst_layout_rules():
    assert pdf_title("<!-- SPDX -->\n# EXP-009 report\n\n## 1. Part\n") == "EXP-009 report"
    assert pdf_title('---\ntitle: "T"\n---\n\n# Abstract\n') is None
    assert pdf_title("no heading\n") is None
    typ = '#let conf(title: none, doc) = {\n  set document(\n    title: title,\n  )\n}\n'
    out = typst_layout_fixes(typ, 'Say "hi"')
    assert out.startswith(TYPST_PREAMBLE)
    assert "set block(breakable: true)" in out and "set text(size: 9pt)" in out
    assert 'title: "Say \\"hi\\"",' in out
    assert typst_layout_fixes("x", None).endswith("x")
    with pytest.raises(ValueError):
        typst_layout_fixes("no template here", "T")


def test_builder_disables_pandoc_line_wrapping():
    # pandoc's wrapped Typst output can start a line with "2018." which Typst reads as a list item (M6 finding)
    src = (ROOT / "src" / "token_lab" / "report.py").read_text(encoding="utf-8")
    assert '"--wrap=none"' in src
