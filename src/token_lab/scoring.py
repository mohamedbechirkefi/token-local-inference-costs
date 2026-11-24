# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Answer extraction and scoring (protocol sections 4 and S2).

Strict extraction: after trimming whitespace, one trailing period and
enclosing parentheses or asterisks, the whole response must equal one
displayed label (letters compared case-insensitively).

Lenient extraction: an explicit "answer is X" / "Answer: X" pattern if
present, otherwise the first standalone displayed label in the response.
Known weakness, kept deliberately and documented: a leading English article
"A" is read as label A under lenient extraction.

A response with no extractable label is a format failure and scores 0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Extraction:
    strict: str | None  # source label or None
    lenient: str | None


def _canon(token: str, display: Mapping[str, str]) -> str | None:
    for d, src in display.items():
        if token == d or (d.isalpha() and token.upper() == d.upper()):
            return src
    return None


def extract_strict(response: str, display: Mapping[str, str]) -> str | None:
    if not isinstance(response, str):
        raise TypeError("response must be a string")
    s = response.strip()
    if s.endswith("."):
        s = s[:-1].strip()
    s = s.strip("*").strip()
    if len(s) >= 2 and s[0] == "(" and s[-1] == ")":
        s = s[1:-1].strip()
    return _canon(s, display)


def extract_lenient(response: str, display: Mapping[str, str]) -> str | None:
    if not isinstance(response, str):
        raise TypeError("response must be a string")
    strict = extract_strict(response, display)
    if strict is not None:
        return strict
    alts = "|".join(re.escape(d) for d in sorted(display, key=len, reverse=True))
    if not alts:
        return None
    m = re.search(rf"answer\s*(?:is|:)?\s*[\(\*]*\s*({alts})\b", response, flags=re.IGNORECASE)
    if m:
        return _canon(m.group(1), display)
    m = re.search(rf"(?<![A-Za-z0-9])({alts})(?![A-Za-z0-9])", response)
    if m:
        return _canon(m.group(1), display)
    return None


def extract(response: str, display: Mapping[str, str]) -> Extraction:
    return Extraction(extract_strict(response, display), extract_lenient(response, display))


def is_correct(extracted: str | None, answer_key: str) -> int:
    """1 if the extracted source label equals the key, else 0 (format failure is 0)."""
    return int(extracted is not None and extracted == answer_key)


def accuracy(correct: list[int]) -> float:
    if len(correct) == 0:
        raise ValueError("accuracy of an empty list is undefined")
    if any(c not in (0, 1) for c in correct):
        raise ValueError("correctness values must be 0 or 1")
    return sum(correct) / len(correct)


def chance_accuracy(n_choices: list[int]) -> float:
    """Expected accuracy of uniform guessing: mean of 1/k over items."""
    if not n_choices or any(k < 1 for k in n_choices):
        raise ValueError("need at least one item with k >= 1 choices")
    return sum(1.0 / k for k in n_choices) / len(n_choices)
