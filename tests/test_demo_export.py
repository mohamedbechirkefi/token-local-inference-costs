# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""M5 consistency test (master prompt 11.6): the demo shows the manuscript's numbers.

1. Re-running the export in memory gives exactly the committed
   ``demo/public/data/results.json``.
2. Every ``display`` and ``interval_display`` string appears verbatim in
   ``research/paper/manuscript.md`` (whitespace runs collapsed to one space), or is a
   documented exception listed in ``display_exceptions`` with a reason.
3. Every registered experiment is exported with its status, verdict and claim ids.
4. The sandbox fixture is regenerated identically by the Python engine.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "demo/public/data/results.json"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _data() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _manuscript() -> str:
    return _norm((ROOT / "research/paper/manuscript.md").read_text(encoding="utf-8"))


def test_committed_results_json_is_reproduced_exactly():
    exp = _load("export_demo_data", "scripts/export_demo_data.py")
    assert exp.render(exp.build()) == DATA.read_text(encoding="utf-8")


def test_every_display_string_is_in_the_manuscript_or_a_documented_exception():
    data = _data()
    manuscript = _manuscript()
    exceptions = {x["text"]: x["reason"] for x in data["display_exceptions"]}
    assert all(reason.strip() for reason in exceptions.values())
    checked, missing = 0, []
    for e in data["experiments"]:
        for x in e["estimates"]:
            for key in ("display", "interval_display"):
                s = x[key]
                if s is None:
                    continue
                checked += 1
                if _norm(s) not in manuscript and s not in exceptions:
                    missing.append(f"{e['id']} {x['label']} {key}={s!r}")
    for a in data["frontier"]["arms"]:
        for key in ("accuracy_display", "memory_display", "latency_display", "latency_iqr_display", "decode_display"):
            checked += 1
            if _norm(a[key]) not in manuscript:
                missing.append(f"frontier {a['arm']} {key}={a[key]!r}")
    for row in data["sensitivity"]:
        checked += 1
        if _norm(row["result"]) not in manuscript:
            missing.append(f"sensitivity {row['check']!r}")
    assert checked > 40
    assert missing == []


def test_exceptions_are_really_absent_from_the_manuscript():
    manuscript = _manuscript()
    for x in _data()["display_exceptions"]:
        assert _norm(x["text"]) not in manuscript, f"{x['text']!r} is printed; remove the exception"


def test_every_registered_experiment_is_exported_with_status_verdict_and_claims():
    data = _data()
    with (ROOT / "research/experiment_registry.csv").open(encoding="utf-8", newline="") as fh:
        registered = [r["exp_id"] for r in csv.DictReader(fh)]
    with (ROOT / "research/claims_register.csv").open(encoding="utf-8", newline="") as fh:
        claim_ids = {r["claim_id"] for r in csv.DictReader(fh)}
    exported = {e["id"]: e for e in data["experiments"]}
    assert sorted(exported) == sorted(registered)
    for e in exported.values():
        assert e["status"] and e["verdict"] and e["claim_ids"]
        assert set(e["claim_ids"]) <= claim_ids
    # EXP-001: failure under the stopping rule as written, status pending the owner (DL-016);
    # EXP-002: complete on the rerun, H1 supported under the frozen rule.
    assert exported["EXP-001"]["outcome"] == "failed"
    assert "pending owner decision" in exported["EXP-001"]["verdict"]
    assert exported["EXP-002"]["outcome"] == "positive"
    assert exported["EXP-002"]["verdict"].startswith("H1 supported")
    assert exported["EXP-003"]["verdict"] == "H0 not rejected: no detected difference, not equivalence"


def test_pending_owner_decisions_are_shown_with_every_reading():
    pend = {p["id"]: p for p in _data()["pending_owner_decisions"]}
    assert set(pend) == {"TOKEN-EXP-001-STATUS", "TOKEN-TITLE"}
    assert all(p["status"] == "pending owner decision" for p in pend.values())
    assert len(pend["TOKEN-EXP-001-STATUS"]["readings"]) == 3
    assert len(pend["TOKEN-TITLE"]["readings"]) == 2


def test_no_timestamp_and_sources_hashed():
    text = DATA.read_text(encoding="utf-8")
    assert not re.search(r"20\d\d-\d\d-\d\dT\d\d:\d\d", text)
    for s in _data()["sources"]:
        assert re.fullmatch(r"[0-9a-f]{64}", s["sha256"])


def test_sandbox_fixture_is_reproduced_exactly():
    fx = _load("export_sandbox_fixture", "scripts/export_sandbox_fixture.py")
    committed = (ROOT / "demo/src/engine.fixture.json").read_text(encoding="utf-8")
    assert fx.render(fx.build()) == committed
