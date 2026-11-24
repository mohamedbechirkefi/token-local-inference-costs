# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Ingestion: multiple-choice items, file hashing and seeded subsets.

Accepted file format ("hf-arc-jsonl"): one JSON object per line with the
fields of the Hugging Face ``allenai/ai2_arc`` rows::

    {"id": str, "question": str,
     "choices": {"text": [str, ...], "label": [str, ...]},
     "answerKey": str}

Ingestion is pure apart from reading the file; every malformed row raises
``ItemFormatError`` with its line number (fail closed).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


class ItemFormatError(ValueError):
    """A row of an item file does not satisfy the expected schema."""


@dataclass(frozen=True)
class Item:
    """One multiple-choice item. ``labels`` and ``texts`` are aligned."""

    item_id: str
    question: str
    labels: tuple[str, ...]
    texts: tuple[str, ...]
    answer_key: str

    def __post_init__(self) -> None:
        if not self.item_id:
            raise ItemFormatError("item_id must be non-empty")
        if not self.question.strip():
            raise ItemFormatError(f"{self.item_id}: empty question")
        if len(self.labels) != len(self.texts):
            raise ItemFormatError(f"{self.item_id}: labels and texts differ in length")
        if len(self.labels) < 2:
            raise ItemFormatError(f"{self.item_id}: fewer than two choices")
        if len(set(self.labels)) != len(self.labels):
            raise ItemFormatError(f"{self.item_id}: duplicate labels")
        if any(not lab.strip() for lab in self.labels):
            raise ItemFormatError(f"{self.item_id}: empty label")
        if self.answer_key not in self.labels:
            raise ItemFormatError(f"{self.item_id}: answerKey {self.answer_key!r} not among labels")

    @property
    def chance(self) -> float:
        """Expected accuracy of uniform guessing over this item's options."""
        return 1.0 / len(self.labels)


def sha256_file(path: str | Path) -> str:
    """SHA-256 hex digest of a file's bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def parse_item(row: object, where: str = "row") -> Item:
    """Convert one decoded JSON row into an ``Item`` or raise ``ItemFormatError``."""
    if not isinstance(row, dict):
        raise ItemFormatError(f"{where}: not a JSON object")
    try:
        choices = row["choices"]
        texts = choices["text"]
        labels = choices["label"]
        item_id = row["id"]
        question = row["question"]
        answer = row["answerKey"]
    except (KeyError, TypeError) as exc:
        raise ItemFormatError(f"{where}: missing field {exc}") from None
    if not all(isinstance(x, str) for x in (item_id, question, answer)):
        raise ItemFormatError(f"{where}: id, question and answerKey must be strings")
    if not isinstance(texts, list) or not isinstance(labels, list):
        raise ItemFormatError(f"{where}: choices.text and choices.label must be lists")
    if not all(isinstance(x, str) for x in texts + labels):
        raise ItemFormatError(f"{where}: choice texts and labels must be strings")
    try:
        return Item(item_id, question, tuple(labels), tuple(texts), answer)
    except ItemFormatError as exc:
        raise ItemFormatError(f"{where}: {exc}") from None


def load_items(path: str | Path) -> tuple[list[Item], str]:
    """Load all items of a JSONL file. Returns (items, sha256 of the file bytes)."""
    p = Path(path)
    items: list[Item] = []
    seen: set[str] = set()
    with open(p, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ItemFormatError(f"{p}:{lineno}: invalid JSON ({exc.msg})") from None
            item = parse_item(row, f"{p}:{lineno}")
            if item.item_id in seen:
                raise ItemFormatError(f"{p}:{lineno}: duplicate id {item.item_id}")
            seen.add(item.item_id)
            items.append(item)
    if not items:
        raise ItemFormatError(f"{p}: no items")
    return items, sha256_file(p)


def seeded_subset(items: list[Item], n: int | None, seed: int) -> list[Item]:
    """Simple random sample without replacement, returned in file order.

    ``n=None`` returns all items. The sample depends only on (item ids, n, seed):
    ids are sorted before sampling so file order does not change the subset.
    """
    if n is None:
        return list(items)
    if n <= 0 or n > len(items):
        raise ValueError(f"subset size {n} outside 1..{len(items)}")
    ids = sorted(it.item_id for it in items)
    rng = np.random.default_rng(seed)
    chosen = set(ids[i] for i in rng.choice(len(ids), size=n, replace=False))
    return [it for it in items if it.item_id in chosen]
