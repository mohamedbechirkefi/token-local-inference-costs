# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""EXP-002 cold/warm mode: config validation, trial sequence, cold checks,
stopping rule and the frozen config. Simulated backend and local HTTP stub
only; Ollama is never contacted."""

import copy
import hashlib
import json

import pytest

from token_lab import cli
from token_lab.config import ConfigError, ProtocolNotFrozen, load_config, parse_config, require_frozen_if_confirmatory
from token_lab.items import load_items, seeded_subset
from token_lab.runner import cold_warm_sequence, execute
from token_lab.runtime import OllamaBackend, SimulatedBackend
from token_lab.schema import import_result


def cw_config(repo, **over):
    """The frozen EXP-002 config made exploratory on the simulated backend and fixture."""
    raw = json.loads((repo / "experiments" / "EXP-002.json").read_text())
    raw.update(mode="exploratory", backend={"name": "simulated", "track_loading": True})
    raw["items"] = {"path": "data/fixtures/synthetic_mc.jsonl", "synthetic": True,
                    "subset_size": 1, "subset_seed": 20261124}
    for k, v in over.items():
        if k == "cold_warm":
            raw["cold_warm"] = {**raw["cold_warm"], **v}
        else:
            raw[k] = v
    return raw


def test_frozen_exp002_config_matches_protocol(repo):
    cfg = load_config(repo / "experiments" / "EXP-002.json")
    cw = cfg.cold_warm
    assert cfg.exp_id == "EXP-002" and cfg.mode == "confirmatory" and cfg.design == "cold_warm"
    assert [(a.arm_id, a.model) for a in cfg.arms] == [
        ("A0", "phi4-mini:3.8b"), ("A1", "llama3.1:8b"), ("A2", "ministral-3:8b")]
    assert cw.trials_per_state == 10 and cw.arm_order_seed == 2002 and cw.wall_cap_s == 3600  # items 7, 12, 18
    assert cfg.runtime_seeds == (0,)  # item 12
    d = cfg.decoding
    assert (d.temperature, d.num_predict, d.num_ctx) == (0, 8, 2048)  # item 9
    assert cfg.subset_size == 1 and "validation" in cfg.items_path  # one fixed validation-split prompt
    assert len(cfg.arms) * 2 * cw.trials_per_state == 60  # item 14: 60 requests
    rec = json.loads((repo / "research" / "freeze.json").read_text())["experiments"]["EXP-002"]
    assert rec["config_canonical_sha256"] == cfg.sha256
    assert rec["config_file_sha256"] == hashlib.sha256((repo / "experiments" / "EXP-002.json").read_bytes()).hexdigest()
    assert rec["fixed_item_ids_sha256"] == hashlib.sha256(
        (repo / rec["fixed_item_ids_path"]).read_bytes()).hexdigest()


def test_frozen_exp002_fixed_item(repo):
    ids = json.loads((repo / "data" / "arc_challenge_validation_exp002_ids.json").read_text())
    assert ids["item_ids"] == ["Mercury_192290"] and ids["subset_seed"] == 20261124
    cfg = load_config(repo / "experiments" / "EXP-002.json")
    assert cfg.items_source_sha256 == ids["jsonl_sha256"]
    arc = repo / cfg.items_path
    if arc.is_file():  # the raw file is not committed; check it when present
        items, sha = load_items(arc)
        assert sha == ids["jsonl_sha256"]
        assert [i.item_id for i in seeded_subset(items, 1, 20261124)] == ids["item_ids"]


@pytest.mark.parametrize("change", [
    lambda c: c["cold_warm"].update(trials_per_state=20),
    lambda c: c["cold_warm"].update(arm_order_seed=1),
    lambda c: c.update(runtime_seeds=[1]),
    lambda c: c["decoding"].update(num_ctx=4096),
])
def test_freeze_guard_refuses_changed_exp002(repo, change):
    raw = json.loads((repo / "experiments" / "EXP-002.json").read_text())
    change(raw)
    with pytest.raises(ProtocolNotFrozen, match="config differs"):
        require_frozen_if_confirmatory(parse_config(raw), repo)


def test_cli_run_accepts_frozen_exp002_without_runtime(repo, monkeypatch, capsys, dead_url):
    from token_lab import runner
    monkeypatch.setattr(runner, "make_backend", lambda spec: OllamaBackend(dead_url, 1))
    assert cli.main(["run", "--config", str(repo / "experiments" / "EXP-002.json")]) == 3
    assert "runtime unavailable" in capsys.readouterr().err


@pytest.mark.parametrize("over,msg", [
    ({"design": "grid"}, "design"),
    ({"warmup": True}, "warmup"),
    ({"max_retries": 1}, "max_retries"),
    ({"repetitions": 2, "runtime_seeds": [0, 1]}, "repetitions"),
    ({"cold_warm": {"trials_per_state": 0}}, "trials_per_state"),
    ({"cold_warm": {"wall_cap_s": 0}}, "wall_cap_s"),
    ({"cold_warm": {"unload_poll_s": True}}, "unload_poll_s"),
])
def test_cold_warm_config_rejections(repo, over, msg):
    with pytest.raises(ConfigError, match=msg):
        parse_config(cw_config(repo, **over))


def test_cold_warm_config_needs_one_prompt_and_block(repo):
    raw = cw_config(repo)
    raw["items"]["subset_size"] = 2
    with pytest.raises(ConfigError, match="one fixed prompt"):
        parse_config(raw)
    raw = cw_config(repo)
    del raw["cold_warm"]
    with pytest.raises(ConfigError, match="cold_warm"):
        parse_config(raw)
    raw = json.loads((repo / "experiments" / "EXP-001.json").read_text())
    raw["cold_warm"] = {}
    with pytest.raises(ConfigError, match="needs design cold_warm"):
        parse_config(raw)


def test_sequence_alternates_cold_first_and_arm_order_seeded():
    arms, states = cold_warm_sequence(3, 10, 2002)
    assert sorted(arms) == [0, 1, 2] and arms == cold_warm_sequence(3, 10, 2002)[0]
    assert states == ["cold", "warm"] * 10
    with pytest.raises(ValueError):
        cold_warm_sequence(3, 0, 2002)


def test_cold_warm_simulated_end_to_end(repo, tmp_path):
    cfg = parse_config(cw_config(repo))
    be = SimulatedBackend(track_loading=True)
    doc, path = execute(cfg, repo, backend=be, out_root=tmp_path)
    recs = doc["records"]
    assert len(recs) == 60 and len(doc["blocks"]) == 3
    assert len({r["item_id"] for r in recs}) == 1  # one fixed prompt
    assert all(r["runtime_seed"] == 0 and r["template"] == "T1" for r in recs)
    arm_order = doc["manifest"]["cold_warm"]["arm_order"]
    assert arm_order == [cfg.arms[i].arm_id for i in cold_warm_sequence(3, 10, 2002)[0]]
    for arm in arm_order:
        rs = sorted((r for r in recs if r["arm"] == arm), key=lambda r: r["order_index"])
        assert [r["start_state"] for r in rs] == ["cold", "warm"] * 10
        assert [r["trial_index"] for r in rs] == [i // 2 for i in range(20)]
    # arm blocks are contiguous and in the seeded order
    seen = []
    for r in recs:
        if not seen or seen[-1] != r["arm"]:
            seen.append(r["arm"])
    assert seen == arm_order
    assert all(r["state_valid"] for r in recs) and doc["manifest"]["cold_warm"]["n_invalid_state"] == 0
    cold = [r for r in recs if r["start_state"] == "cold"]
    assert all(r["state_check"]["loaded_before_request"] == [] and r["state_check"]["unload_error"] is None
               for r in cold)
    assert all(r["state_check"]["previous_request_completed"] for r in recs if r["start_state"] == "warm")
    # one unload per cold trial, none for warm trials, plus the previous arm's model at
    # each arm switch (the protocol requires that no model at all is loaded)
    assert len(be.unload_calls) == 30 + 2
    firsts = [r for r in cold if r["trial_index"] == 0]
    assert [len(r["state_check"]["unloaded"]) for r in firsts] == [1, 2, 2]
    assert not doc["failures"] and doc["manifest"]["design"] == "cold_warm"
    assert import_result(path)["records"][0]["start_state"] == "cold"


def test_cold_trial_invalid_when_unload_not_honoured(repo, tmp_path):
    cfg = parse_config(cw_config(repo, cold_warm={"trials_per_state": 2, "unload_confirm_timeout_s": 0.01,
                                                  "unload_poll_s": 0.001}))
    doc, _ = execute(cfg, repo, backend=SimulatedBackend(track_loading=True, ignore_unload=True), out_root=tmp_path)
    by_arm = {}
    for r in doc["records"]:
        by_arm.setdefault(r["arm"], []).append(r)
    first = doc["manifest"]["cold_warm"]["arm_order"][0]
    # the very first cold trial of the run starts with nothing loaded; every later cold trial
    # still sees a model loaded, so it is kept but marked invalid (protocol items 10 and 17)
    assert by_arm[first][0]["state_valid"] is True
    invalid = [r for r in doc["records"] if r["start_state"] == "cold" and not r["state_valid"]]
    assert len(invalid) == 3 * 2 - 1
    assert all(r["state_check"]["loaded_before_request"] for r in invalid)
    assert len([f for f in doc["failures"] if f["stage"] == "cold_check"]) == 5
    assert doc["manifest"]["cold_warm"]["n_invalid_state"] == 5


def test_warm_trial_invalid_after_failed_request(repo, tmp_path):
    cfg = parse_config(cw_config(repo, cold_warm={"trials_per_state": 2}))
    doc, _ = execute(cfg, repo, backend=SimulatedBackend(fail_models=("llama3.1:8b",), track_loading=True),
                     out_root=tmp_path)
    bad = [r for r in doc["records"] if r["arm"] == "A1"]
    assert all(r["error"] and r["attempts"] == 1 for r in bad)  # no retries
    assert all(not r["state_valid"] for r in bad if r["start_state"] == "warm")
    good = [r for r in doc["records"] if r["arm"] != "A1"]
    assert all(r["state_valid"] for r in good)


def test_wall_cap_stops_new_trials(repo, tmp_path):
    cfg = parse_config(cw_config(repo, cold_warm={"wall_cap_s": 1e-9}))
    doc, _ = execute(cfg, repo, backend=SimulatedBackend(track_loading=True), out_root=tmp_path)
    assert doc["records"] == [] and doc["manifest"]["cold_warm"]["stopped_by_wall_cap"] is True
    assert [f["stage"] for f in doc["failures"]] == ["stopping_rule"]


def test_ollama_unload_request_against_stub(repo, tmp_path, stub_ollama):
    be = OllamaBackend(stub_ollama.url, 5)
    be.unload("m")
    assert stub_ollama.bodies[-1] == {"model": "m", "keep_alive": 0, "stream": False}
    # the stub's /api/ps always lists a model: every cold trial is flagged, none is dropped
    raw = cw_config(repo, backend={"name": "ollama"}, cold_warm={"trials_per_state": 1, "unload_confirm_timeout_s": 0.01,
                                                                 "unload_poll_s": 0.001})
    doc, _ = execute(parse_config(raw), repo, backend=be, out_root=tmp_path)
    assert len(doc["records"]) == 6 and stub_ollama.calls == 6
    unloads = [b for b in stub_ollama.bodies if b.get("keep_alive") == 0]
    assert len(unloads) == 1 + 3 * 2  # each cold trial unloads its arm's model and the listed "m"
    assert all(not r["state_valid"] for r in doc["records"] if r["start_state"] == "cold")
    assert all(r["state_valid"] for r in doc["records"] if r["start_state"] == "warm")
    assert all(b["options"]["seed"] == 0 and b["options"]["num_predict"] == 8
               for b in stub_ollama.bodies if "prompt" in b)


def test_matrix_records_unchanged_by_schema_extension(repo, tmp_path):
    raw = json.loads((repo / "experiments" / "smoke-simulated.json").read_text())
    raw.update(repetitions=1, runtime_seeds=[0])
    doc, _ = execute(parse_config(raw), repo, out_root=tmp_path)
    assert all("start_state" not in r for r in doc["records"]) and doc["manifest"]["design"] == "matrix"
    bad = copy.deepcopy(doc)
    bad["records"][0]["start_state"] = "cold"  # partial cold/warm fields are rejected
    from token_lab.schema import ResultValidationError, validate
    with pytest.raises(ResultValidationError):
        validate(bad)
