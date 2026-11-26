# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Frozen block rules (research/protocol.md section 9) and the block-repeat mode (DL-017).

Everything runs on the SIMULATED backend with injected machine readings
(``machine`` fixture in conftest.py): no model, no runtime, no real swap.
"""

import hashlib
import json
import shutil

import pytest

from token_lab import cli, runner
from token_lab.config import parse_config
from token_lab.report import build_report
from token_lab.runner import (Probes, block_criteria, combine_repeat, execute, execute_block_repeat, planned_blocks,
                              source_block_check)
from token_lab.runtime import RuntimeReportedError, RuntimeUnavailable, SimulatedBackend
from token_lab.schema import export_result, import_result

from test_pipeline import base_config

MIB = 2**20
MODELS = {"A0": "phi4-mini:3.8b", "A1": "llama3.1:8b", "A2": "ministral-3:8b"}


class Trigger(SimulatedBackend):
    """Simulated backend that acts on the machine during chosen blocks.

    ``targets`` maps (model, runtime seed) of a block to an action applied at the
    first request of that block, for the first ``times`` occurrences of it:
    ("swap", MiB) adds swap, ("battery",) makes the power reading after the block
    say battery, ("foreign",) makes /api/ps after the block list a model outside
    the config, ("version",) changes the
    runtime version, ("kill",) makes the runtime report a killed runner,
    ("down",) makes the runtime unreachable.
    """

    def __init__(self, machine, targets: dict, times: int = 1):
        super().__init__(track_loading=True)
        self.machine = machine
        self.targets = targets
        self.times = times
        self.count: dict = {}
        self.seen: dict = {}
        self.version_value = "simulated-0"
        self.killed = False
        self.down = False
        self.foreign_reads = 0
        self.calls = []

    def loaded_models(self):
        out = super().loaded_models()
        if self.foreign_reads > 0:
            self.foreign_reads -= 1
            out.append({"name": "qwen3.5:4b", "size": None, "size_vram": None})
        return out

    def version(self):
        if self.down:
            raise RuntimeUnavailable("connection refused")
        return self.version_value

    def generate(self, model, prompt, decoding, seed):
        key = (model, seed)
        n = self.count.get(key, 0)
        self.count[key] = n + 1
        if n % 11 == 0:  # first request of a block (its warm-up): one warm-up and ten items per block
            self.seen[key] = self.seen.get(key, 0) + 1
            act = self.targets.get(key)
            if act and self.seen[key] <= self.times:
                kind = act[0]
                if kind == "swap":
                    self.machine.swap += int(act[1] * MIB)
                elif kind == "battery":
                    self.machine.battery_reads = 1  # the reading after this block says battery
                elif kind == "foreign":
                    self.foreign_reads = 1  # /api/ps after this block lists a foreign model
                elif kind == "version":
                    self.version_value = "simulated-1"
                elif kind == "kill":
                    self.killed = True
                elif kind == "down":
                    self.down = True
        if self.killed:
            raise RuntimeReportedError("llama runner process has terminated: signal: killed")
        if self.down:
            raise RuntimeUnavailable("connection refused")
        self.calls.append((model, seed, prompt))
        return super().generate(model, prompt, decoding, seed)


def cfg3(**over):
    return parse_config(base_config(repetitions=3, runtime_seeds=[0, 1, 2], **over))


def block_key(cfg, k):
    rep, ai = planned_blocks(cfg, 10)[k - 1]
    return (cfg.arms[ai].model, cfg.runtime_seeds[rep]), cfg.arms[ai].arm_id, rep


def rules(doc):
    return doc["manifest"]["block_rules"]


# ---- rule constants carry the frozen wording ----

def test_frozen_wording_and_thresholds(repo):
    text = (repo / "research" / "protocol.md").read_text(encoding="utf-8")
    for quote in runner.RULES_QUOTED.values():
        assert quote in text
    assert (runner.SWAP_EXCLUDE_MIB, runner.SWAP_ABORT_MIB, runner.WALL_CAP_S) == (512, 2048, 14400)


def test_real_probes_read_the_machine():
    p = Probes()
    assert p.power_source() in ("ac", "battery", "unknown", None)
    assert isinstance(p.swap_used_bytes(), int) and p.swap_used_bytes() >= 0
    assert p.clock() <= p.clock()


# ---- no criterion met ----

def test_quiet_run_is_complete_and_unchanged_in_shape(repo, tmp_path, machine):
    cfg = cfg3()
    doc, path = execute(cfg, repo, backend=Trigger(machine, {}), out_root=tmp_path)
    assert rules(doc)["status"] == "complete" and rules(doc)["exclusions"] == []
    assert len(doc["records"]) == 3 * 3 * 10 and len(doc["blocks"]) == 9
    assert [b["block_index"] for b in doc["blocks"]] == list(range(1, 10))
    assert all(b["status"] == "included" and b["attempt"] == 1 for b in doc["blocks"])
    assert doc["excluded_records"] == [] and doc["excluded_blocks"] == []
    assert import_result(path)["manifest"]["block_rules"]["quoted"] == runner.RULES_QUOTED


# ---- exclusion: repeated once ----

@pytest.mark.parametrize("action,reason", [
    (("swap", 600), "swap grew by 600.0 MiB"),
    (("battery",), "machine on battery"),
    (("foreign",), "foreign model loaded: qwen3.5:4b"),
    (("version",), "runtime version changed"),
])
def test_excluded_block_is_repeated_once(repo, tmp_path, machine, action, reason):
    cfg = cfg3()
    key, arm, rep = block_key(cfg, 4)
    be = Trigger(machine, {key: action})
    doc, _ = execute(cfg, repo, backend=be, out_root=tmp_path)
    r = rules(doc)
    if action[0] == "version":
        # the version stays changed: every later block meets the criterion too
        assert r["exclusions"][0]["block_index"] == 4 and reason in r["exclusions"][0]["reasons"][0]
        return
    assert r["status"] == "complete"
    assert len(r["exclusions"]) == 1
    e = r["exclusions"][0]
    assert (e["block_index"], e["arm"], e["repetition"], e["attempt"]) == (4, arm, rep, 1)
    assert e["outcome"] == "excluded, repeated once" and reason in e["reasons"][0]
    # the analysis set is the full matrix; the excluded block is kept apart, not dropped
    assert len(doc["records"]) == 90 and len(doc["blocks"]) == 9
    kept = [b for b in doc["blocks"] if b["block_index"] == 4]
    assert kept[0]["attempt"] == 2 and kept[0]["status"] == "included"
    assert len(doc["excluded_blocks"]) == 1 and doc["excluded_blocks"][0]["status"] == "excluded"
    assert len(doc["excluded_records"]) == 10
    assert {(x["block_index"], x["attempt"]) for x in doc["excluded_records"]} == {(4, 1)}
    # the repeat uses the same seed, item order and warm-up as the excluded attempt
    seq = lambda recs: [(x["order_index"], x["item_id"], x["runtime_seed"]) for x in recs]  # noqa: E731
    again = [x for x in doc["records"] if x["arm"] == arm and x["repetition"] == rep]
    assert seq(again) == seq(doc["excluded_records"])
    warmups = [c for c in be.calls if (c[0], c[1]) == key]
    assert len(warmups) == 2 * 11 and warmups[0] == warmups[11]
    assert any(f["stage"] == "block_exclusion" for f in doc["failures"])


def test_block_excluded_twice_is_not_repeated_again(repo, tmp_path, machine):
    cfg = cfg3()
    key, arm, rep = block_key(cfg, 2)
    doc, _ = execute(cfg, repo, backend=Trigger(machine, {key: ("swap", 700)}, times=5), out_root=tmp_path)
    r = rules(doc)
    assert r["status"] == "incomplete" and "again after its one repeat" in r["status_reason"]
    assert [e["outcome"] for e in r["exclusions"]] == ["excluded, repeated once", "excluded, not repeated again"]
    assert len(doc["blocks"]) == 8 and 2 not in [b["block_index"] for b in doc["blocks"]]
    assert len(doc["excluded_blocks"]) == 2 and len(doc["excluded_records"]) == 20
    assert len(doc["records"]) == 80  # the run continues with the other blocks


def test_swap_at_exactly_512_is_not_excluded():
    b = {"memory": {"swap_delta_mib": 512.0}, "loaded_before": [], "loaded_after": []}
    assert block_criteria(b, set(MODELS.values()), "v") == []
    b["memory"]["swap_delta_mib"] = 512.1
    assert block_criteria(b, set(MODELS.values()), "v")


# ---- stopping rules ----

def test_swap_growth_above_2_gib_aborts_as_failure(repo, tmp_path, machine):
    cfg = cfg3()
    key, arm, rep = block_key(cfg, 5)
    doc, path = execute(cfg, repo, backend=Trigger(machine, {key: ("swap", 2100)}), out_root=tmp_path)
    r = rules(doc)
    assert r["status"] == "failure" and "stopping rule (memory exhaustion) at block 5" in r["status_reason"]
    assert r["exclusions"][-1]["outcome"] == "aborted"
    assert len(doc["blocks"]) == 4  # blocks 1 to 4 kept; nothing after block 5 ran
    ab = doc["excluded_blocks"][0]
    assert ab["status"] == "aborted" and ab["block_index"] == 5 and "2 GiB" in ab["abort_reason"]
    # the abort happens before the next request: only the warm-up of block 5 ran
    assert len([x for x in doc["excluded_records"] if x["block_index"] == 5]) == 0
    assert any(f["stage"] == "stopping_rule" for f in doc["failures"])
    assert import_result(path)  # the result is written and valid


def test_runner_killed_aborts_as_failure(repo, tmp_path, machine):
    cfg = cfg3()
    key, _, _ = block_key(cfg, 3)
    doc, _ = execute(cfg, repo, backend=Trigger(machine, {key: ("kill",)}), out_root=tmp_path)
    assert rules(doc)["status"] == "failure" and "runner killed" in rules(doc)["status_reason"]
    assert len(doc["blocks"]) == 2


def test_runtime_lost_mid_run_aborts_as_failure(repo, tmp_path, machine):
    cfg = cfg3()
    key, _, _ = block_key(cfg, 6)
    doc, _ = execute(cfg, repo, backend=Trigger(machine, {key: ("down",)}), out_root=tmp_path)
    assert rules(doc)["status"] == "failure" and "unreachable" in rules(doc)["status_reason"]
    assert len(doc["blocks"]) == 5


def test_wall_clock_cap_keeps_completed_blocks(repo, tmp_path, machine, monkeypatch):
    monkeypatch.setattr(runner, "WALL_CAP_S", 100.0)
    machine.tick = 1.0  # every clock read advances one simulated second
    cfg = cfg3()
    doc, _ = execute(cfg, repo, backend=Trigger(machine, {}), out_root=tmp_path)
    r = rules(doc)
    assert r["status"] == "incomplete" and "wall-clock cap" in r["status_reason"]
    assert r["thresholds"]["wall_cap_s"] == 100.0
    n = len(doc["blocks"])
    assert 1 <= n < 9 and len(doc["records"]) == 10 * n  # only complete blocks are kept
    assert all(b["status"] == "included" for b in doc["blocks"])
    if doc["excluded_blocks"]:
        assert doc["excluded_blocks"][0]["status"] == "cap"


def test_cli_exit_code_4_on_failure(repo, tmp_path, monkeypatch, capsys, machine):
    fake = tmp_path / "repo"
    (fake / "data" / "fixtures").mkdir(parents=True)
    shutil.copy(repo / "data" / "fixtures" / "synthetic_mc.jsonl", fake / "data" / "fixtures")
    monkeypatch.setattr(cli, "REPO", fake)
    cfg = cfg3()
    key, _, _ = block_key(cfg, 1)
    monkeypatch.setattr(runner, "make_backend", lambda spec: Trigger(machine, {key: ("swap", 3000)}))
    p = tmp_path / "c.json"
    p.write_text(json.dumps(cfg.raw))
    assert cli.main(["smoke", "--config", str(p)]) == 4
    assert json.loads(capsys.readouterr().out)["block_rules_status"] == "failure"


# ---- block-repeat mode ----

def legacy_source(repo, tmp_path, machine, swaps: dict) -> tuple:
    """A run in the shape the runner wrote before the rules (no rule fields),
    with chosen block swap deltas, like RUN-SMOKE/RUN-EXP-001-0001."""
    cfg = cfg3()
    doc, path = execute(cfg, repo, backend=SimulatedBackend(), out_root=tmp_path)
    doc["manifest"].pop("block_rules")
    doc.pop("excluded_records")
    doc.pop("excluded_blocks")
    for b in doc["blocks"]:
        for k in ("block_index", "attempt", "power_before", "power_after", "runtime_version_after", "status",
                  "exclusion_reasons"):
            b.pop(k)
        b["memory"].pop("peak_swap_growth_mib")
    for k, mib in swaps.items():
        doc["blocks"][k - 1]["memory"]["swap_delta_mib"] = mib
    export_result(doc, path)
    return cfg, doc, path


def test_source_block_check_reads_the_criteria(repo, tmp_path, machine):
    _, doc, _ = legacy_source(repo, tmp_path, machine, {3: 734.1, 7: 2778.1})
    checks = {c["block_index"]: c for c in source_block_check(doc)}
    assert checks[3]["exclusion"] and checks[3]["stopping"] is None
    assert checks[7]["exclusion"] and "2 GiB" in checks[7]["stopping"]
    assert all(not checks[k]["exclusion"] for k in checks if k not in (3, 7))


def test_repeat_blocks_writes_a_new_run_and_leaves_the_source(repo, tmp_path, machine):
    cfg, src, path = legacy_source(repo, tmp_path, machine, {3: 734.1, 7: 2778.1})
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    be = Trigger(machine, {})
    doc, newp = execute_block_repeat(cfg, repo, path.parent, [7, 3], backend=be, out_root=tmp_path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before  # source untouched
    assert doc["run_id"] == "RUN-SMOKE-0002" and newp.parent.name == "RUN-SMOKE-0002"
    ro = doc["manifest"]["repeat_of"]
    assert ro["source_run_id"] == "RUN-SMOKE-0001" and ro["source_result_sha256"] == before
    assert [b["block_index"] for b in ro["replaced_blocks"]] == [3, 7]
    assert "2 GiB" in ro["replaced_blocks"][1]["source_stopping"]
    assert rules(doc)["status"] == "complete" and [b["block_index"] for b in doc["blocks"]] == [3, 7]
    # same seed, item order, warm-up and (deterministic backend) responses as the source blocks
    for b in doc["blocks"]:
        sb = src["blocks"][b["block_index"] - 1]
        assert (b["arm"], b["repetition"]) == (sb["arm"], sb["repetition"])
        key = lambda d: [(r["order_index"], r["item_id"], r["runtime_seed"], r["response"])  # noqa: E731
                         for r in d["records"] if (r["arm"], r["repetition"]) == (b["arm"], b["repetition"])]
        assert key(doc) == key(src)
    assert len(be.calls) == 2 * 11  # one warm-up and ten items per block, nothing else


def test_repeat_blocks_refusals(repo, tmp_path, machine):
    cfg, src, path = legacy_source(repo, tmp_path, machine, {3: 734.1})
    with pytest.raises(ValueError, match="meets no frozen exclusion criterion"):
        execute_block_repeat(cfg, repo, path.parent, [2], backend=SimulatedBackend(), out_root=tmp_path)
    with pytest.raises(ValueError, match="does not exist"):
        execute_block_repeat(cfg, repo, path.parent, [10], backend=SimulatedBackend(), out_root=tmp_path)
    with pytest.raises(ValueError, match="different config"):
        execute_block_repeat(parse_config(base_config(repetitions=3, runtime_seeds=[0, 1, 5])), repo, path.parent,
                             [3], backend=SimulatedBackend(), out_root=tmp_path)
    with pytest.raises(ValueError, match="at least one block"):
        execute_block_repeat(cfg, repo, path.parent, [], backend=SimulatedBackend(), out_root=tmp_path)
    # a run made with the rules enforced has spent its repeats
    doc, p2 = execute(cfg, repo, backend=SimulatedBackend(), out_root=tmp_path / "new")
    with pytest.raises(ValueError, match="already spent"):
        execute_block_repeat(cfg, repo, p2.parent, [1], backend=SimulatedBackend(), out_root=tmp_path / "new")
    assert sorted(p.name for p in tmp_path.iterdir() if p.name.startswith("RUN-")) == ["RUN-SMOKE-0001"]


def test_repeated_block_meeting_a_criterion_again_is_not_repeated(repo, tmp_path, machine):
    cfg, src, path = legacy_source(repo, tmp_path, machine, {3: 734.1, 7: 900.0})
    key3, _, _ = block_key(cfg, 3)
    doc, _ = execute_block_repeat(cfg, repo, path.parent, [3, 7], backend=Trigger(machine, {key3: ("swap", 800)}),
                                  out_root=tmp_path)
    r = rules(doc)
    assert r["status"] == "incomplete"
    assert [(e["block_index"], e["outcome"]) for e in r["exclusions"]] == [(3, "excluded, not repeated again")]
    assert [b["block_index"] for b in doc["blocks"]] == [7]
    comb = combine_repeat(src, doc)
    c = comb["manifest"]["combination"]
    assert c["status"] == "incomplete" and c["blocks_missing"] == [3] and len(comb["records"]) == 80


def test_repeat_stopping_rule_is_a_failure(repo, tmp_path, machine):
    cfg, src, path = legacy_source(repo, tmp_path, machine, {3: 734.1, 7: 2778.1})
    key3, _, _ = block_key(cfg, 3)
    doc, _ = execute_block_repeat(cfg, repo, path.parent, [3, 7], backend=Trigger(machine, {key3: ("swap", 2500)}),
                                  out_root=tmp_path)
    assert rules(doc)["status"] == "failure" and doc["blocks"] == []  # block 7 never ran
    assert combine_repeat(src, doc)["manifest"]["combination"]["status"] == "failure"


def test_repeat_cap_counts_the_source_runtime(repo, tmp_path, machine, monkeypatch):
    cfg, src, path = legacy_source(repo, tmp_path, machine, {3: 734.1})
    src["manifest"]["runtime_s"] = runner.WALL_CAP_S - 0.5
    export_result(src, path)
    machine.tick = 1.0
    doc, _ = execute_block_repeat(cfg, repo, path.parent, [3], backend=Trigger(machine, {}), out_root=tmp_path)
    assert rules(doc)["status"] == "incomplete" and rules(doc)["thresholds"]["wall_cap_s"] == pytest.approx(0.5)
    assert doc["records"] == []


def test_combine_replaces_exactly_the_repeated_blocks(repo, tmp_path, machine):
    cfg, src, path = legacy_source(repo, tmp_path, machine, {3: 734.1, 7: 2778.1})
    rep, rp = execute_block_repeat(cfg, repo, path.parent, [3, 7], backend=Trigger(machine, {}), out_root=tmp_path)
    comb = combine_repeat(src, rep)
    out = tmp_path / "combined"
    p = export_result(comb, out / "result.json")
    back = import_result(p)
    assert len(back["records"]) == len(src["records"]) == 90
    assert [b["block_index"] for b in back["blocks"]] == list(range(1, 10))
    origins = {b["block_index"]: b["origin"] for b in back["blocks"]}
    assert origins[3] == origins[7] == "RUN-SMOKE-0002"
    assert all(origins[k] == "RUN-SMOKE-0001" for k in origins if k not in (3, 7))
    swap = {b["block_index"]: b["memory"]["swap_delta_mib"] for b in back["blocks"]}
    assert swap[3] == 0.0 and swap[7] == 0.0  # the repeat's readings, not the excluded ones
    c = back["manifest"]["combination"]
    assert c["status"] == "complete" and c["blocks_missing"] == [] and c["n_blocks"] == 9
    # replaced records come from the repeat run (compare by object identity of content)
    rep_keys = {(r["arm"], r["repetition"], r["item_id"], r["latency_ms"]) for r in rep["records"]}
    for r in back["records"]:
        b = [x for x in back["blocks"] if (x["arm"], x["repetition"]) == (r["arm"], r["repetition"])][0]
        if b["block_index"] in (3, 7):
            assert (r["arm"], r["repetition"], r["item_id"], r["latency_ms"]) in rep_keys
    with pytest.raises(ValueError):
        combine_repeat(rep, rep)
    # the generator accepts the combined input and states the combination
    info = build_report(p, out)
    text = open(info["report_md"]).read()
    assert "Combined analysis input: RUN-SMOKE-0001 with block 3" in text and "Status: **complete**" in text
    # a run made before the rules regenerates with no block-rules section
    legacy = build_report(path, tmp_path / "legacy")
    assert "Block rules" not in open(legacy["report_md"]).read()


def test_cli_repeat_blocks_and_combine(repo, tmp_path, monkeypatch, capsys, machine):
    fake = tmp_path / "repo"
    (fake / "data" / "fixtures").mkdir(parents=True)
    shutil.copy(repo / "data" / "fixtures" / "synthetic_mc.jsonl", fake / "data" / "fixtures")
    monkeypatch.setattr(cli, "REPO", fake)
    cfg, src, path = legacy_source(fake, fake / "results" / "exploratory", machine, {3: 734.1, 7: 2778.1})
    monkeypatch.setattr(runner, "make_backend", lambda spec: Trigger(machine, {}))
    cp = tmp_path / "c.json"
    cp.write_text(json.dumps(cfg.raw))
    assert cli.main(["repeat-blocks", "--config", str(cp), "--source", str(path.parent), "--blocks", "x"]) == 2
    assert cli.main(["repeat-blocks", "--config", str(cp), "--source", str(path.parent), "--blocks", "2"]) == 2
    capsys.readouterr()
    assert cli.main(["repeat-blocks", "--config", str(cp), "--source", str(path.parent), "--blocks", "3,7"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["run_id"] == "RUN-SMOKE-0002" and out["requests"] == 20 and out["block_rules_status"] == "complete"
    rdir = path.parent.parent / "RUN-SMOKE-0002"
    assert cli.main(["combine", "--source", str(path.parent), "--repeat", str(rdir),
                     "--out", str(rdir / "combined")]) == 0
    c = json.loads(capsys.readouterr().out)
    assert c["requests"] == 90 and c["blocks"] == 9 and c["status"] == "complete"
    assert cli.main(["report", "--result", str(rdir / "combined" / "result.json")]) == 0
