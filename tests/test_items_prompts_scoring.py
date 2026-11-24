# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Ingestion, prompt rendering and scoring with known answers."""

import hashlib
import json

import pytest

from token_lab.items import Item, ItemFormatError, load_items, parse_item, seeded_subset
from token_lab.prompts import render
from token_lab.scoring import accuracy, chance_accuracy, extract_lenient, extract_strict, is_correct

FIXTURE = "data/fixtures/synthetic_mc.jsonl"
ABCD = {"A": "A", "B": "B", "C": "C", "D": "D"}


def _row(**kw):
    row = {"id": "x1", "question": "Q?", "choices": {"text": ["a", "b"], "label": ["A", "B"]}, "answerKey": "A"}
    row.update(kw)
    return row


def test_fixture_loads_with_hash(repo):
    items, sha = load_items(repo / FIXTURE)
    assert len(items) == 10
    assert sha == hashlib.sha256((repo / FIXTURE).read_bytes()).hexdigest()
    assert items[5].labels == ("1", "2", "3", "4")


@pytest.mark.parametrize("bad", [
    {"id": "x"},
    _row(answerKey="C"),
    _row(choices={"text": ["a"], "label": ["A"]}),
    _row(choices={"text": ["a", "b"], "label": ["A", "A"]}),
    _row(choices={"text": ["a", "b", "c"], "label": ["A", "B"]}),
    _row(question="   "),
    _row(id=""),
    _row(id=3),
    "not an object",
])
def test_invalid_rows_rejected(bad):
    with pytest.raises(ItemFormatError):
        parse_item(bad)


def test_bad_files_rejected(tmp_path):
    p = tmp_path / "f.jsonl"
    p.write_text("{not json}\n")
    with pytest.raises(ItemFormatError, match="invalid JSON"):
        load_items(p)
    p.write_text(json.dumps(_row()) + "\n" + json.dumps(_row()) + "\n")
    with pytest.raises(ItemFormatError, match="duplicate id"):
        load_items(p)
    p.write_text("\n\n")
    with pytest.raises(ItemFormatError, match="no items"):
        load_items(p)


def test_subset_deterministic_and_order_invariant(repo):
    items, _ = load_items(repo / FIXTURE)
    a = [i.item_id for i in seeded_subset(items, 4, 20261124)]
    b = [i.item_id for i in seeded_subset(list(reversed(items)), 4, 20261124)]
    assert sorted(a) == sorted(b) and len(set(a)) == 4
    assert seeded_subset(items, None, 1) == items
    with pytest.raises(ValueError):
        seeded_subset(items, 11, 1)
    with pytest.raises(ValueError):
        seeded_subset(items, 0, 1)


def test_render_templates():
    it = Item("i", "Which?", ("A", "B", "C"), ("x", "y", "z"), "B")
    t1 = render(it, "T1")
    assert t1.text == "Question: Which?\nA. x\nB. y\nC. z\nReply with the label of the correct choice only (A, B, C). Do not explain."
    t3 = render(it, "T3")
    assert t3.display_to_source == {"1": "A", "2": "B", "3": "C"}
    assert "1. x" in t3.text
    with pytest.raises(ValueError):
        render(it, "T9")


@pytest.mark.parametrize("resp,strict,lenient", [
    ("B", "B", "B"),
    (" b.\n", "B", "B"),
    ("(C)", "C", "C"),
    ("**D**", "D", "D"),
    ("Answer: C", None, "C"),
    ("The answer is (A).", None, "A"),
    ("I think B is right", None, "B"),
    ("A plant needs light, so D", None, "A"),  # documented lenient weakness
    ("none of these", None, None),
    ("", None, None),
    ("E", None, None),
    ("AB", None, None),
])
def test_extraction_known_cases(resp, strict, lenient):
    assert extract_strict(resp, ABCD) == strict
    assert extract_lenient(resp, ABCD) == lenient


def test_numbered_mapping_back_to_source():
    display = {"1": "A", "2": "B", "3": "C"}
    assert extract_strict("2", display) == "B"
    assert extract_lenient("Answer: 3", display) == "C"
    assert extract_strict("12", display) is None


def test_scoring_hand_computed():
    assert is_correct("B", "B") == 1
    assert is_correct("A", "B") == 0
    assert is_correct(None, "B") == 0  # format failure scores 0
    assert accuracy([1, 0, 1, 1]) == 0.75
    assert chance_accuracy([4, 4, 3, 5]) == pytest.approx((0.25 + 0.25 + 1 / 3 + 0.2) / 4)
    with pytest.raises(ValueError):
        accuracy([])
    with pytest.raises(ValueError):
        accuracy([2])
    with pytest.raises(TypeError):
        extract_strict(None, ABCD)


def test_property_strict_implies_lenient():
    import random

    rng = random.Random(0)
    alphabet = "ABCDE abcde.:()*1234answerisxyz"
    for _ in range(2000):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
        st = extract_strict(s, ABCD)
        if st is not None:
            assert extract_lenient(s, ABCD) == st
        le = extract_lenient(s, ABCD)
        assert le is None or le in ABCD.values()
