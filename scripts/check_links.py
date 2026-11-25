# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Check that every relative link in the tracked Markdown files resolves.

A link is ``[text](target)`` or ``![alt](target)`` outside fenced code blocks
and inline code. External targets (``http:``, ``https:``, ``mailto:``) are
skipped. A relative target must name an existing file or folder, relative to
the Markdown file; a ``#fragment`` must match a heading of the target Markdown
file, slugged as GitHub does (lower case, punctuation removed, spaces to
hyphens). Pandoc attributes after the link (``{width=62%}``) are ignored.

Adapted at M6 from the owner's BLOCK lab repository (same author). Usage:
``.venv/bin/python -I scripts/check_links.py .``; exit code 1 and one
line per broken link if any link fails.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")
EXTERNAL = ("http://", "https://", "mailto:", "ftp://")


def tracked_markdown(root: Path) -> list[Path]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "*.md"], check=True,
                         capture_output=True, text=True).stdout.split()
    return [root / p for p in out if "node_modules/" not in p]


def slug(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def anchors(md: Path) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    in_fence = False
    for line in md.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m and not in_fence:
            base = slug(re.sub(r"[`*_]", "", m.group(1)))
            n = counts.get(base, 0)
            found.add(base if n == 0 else f"{base}-{n}")
            counts[base] = n + 1
        for explicit in re.findall(r"\{#([\w\-]+)\}", line):
            found.add(explicit)
    return found


def links(md: Path) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in LINK.finditer(INLINE_CODE.sub("", line)):
            out.append((i, m.group(1)))
    return out


def check(root: Path) -> tuple[int, list[str]]:
    root = root.resolve()
    n = 0
    broken: list[str] = []
    for md in tracked_markdown(root):
        for line, target in links(md):
            if target.startswith(EXTERNAL):
                continue
            n += 1
            path, _, frag = target.partition("#")
            dest = md if path == "" else (md.parent / path).resolve()
            where = f"{md.relative_to(root)}:{line}: {target}"
            if not dest.exists():
                broken.append(f"{where} (missing file)")
            elif frag and dest.suffix == ".md" and frag not in anchors(dest):
                broken.append(f"{where} (missing anchor)")
    return n, broken


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".")
    n, broken = check(root)
    for b in broken:
        print(b)
    print(f"relative links checked: {n}; broken: {len(broken)}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
