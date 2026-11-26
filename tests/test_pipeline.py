# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Config validation, freeze guard, runner integration, schema, hardware logs, report and CLI."""

import copy
import csv
import hashlib
import json
import os
import shutil

import pytest

from token_lab import cli
from token_lab.analysis import arm_summaries, contrasts, projection
from token_lab.config import ConfigError, ProtocolNotFrozen, frozen_protocol_hash, parse_config, require_frozen_if_confirmatory
from token_lab.hardware import MemorySampler, git_state, host_info, package_versions
from token_lab.report import build_report
from token_lab.runner import execute, next_run_id, schedule
from token_lab.runtime import OllamaBackend, RuntimeUnavailable, SimulatedBackend
from token_lab.schema import ResultValidationError, export_result, import_result, validate


def base_config(**over):
    cfg = json.loads(open(os.path.join(os.path.dirname(__file__), "..", "experiments", "smoke-simulated.json")).read())
    cfg["repetitions"] = 2
    cfg["runtime_seeds"] = [0, 1]
    cfg.update(over)
    return cfg


# ---- config and freeze guard ----

@pytest.mark.parametrize("over,msg", [
    ({"exp_id": "EXP-1"}, "exp_id"),
    ({"mode": "final"}, "mode"),
    ({"mode": "confirmatory"}, "SMOKE"),
    ({"exp_id": "EXP-001", "mode": "confirmatory"}, "simulated"),
    ({"arms": []}, "arm"),
    ({"arms": [{"arm_id": "A", "model": "m"}, {"arm_id": "A", "model": "n"}]}, "duplicate"),
    ({"template": "T7"}, "template"),
    ({"repetitions": 0, "runtime_seeds": []}, "repetitions"),
    ({"runtime_seeds": [0]}, "runtime_seeds"),
    ({"decoding": {"temperature": 0}}, "decoding"),
    ({"backend": {"name": "openai"}}, "backend"),
    ({"max_retries": -1}, "max_retries"),
])
def test_config_rejections(over, msg):
    with pytest.raises(ConfigError, match=msg):
        parse_config(base_config(**over))


def test_config_hash_canonical():
    a = parse_config(base_config())
    raw = dict(reversed(list(base_config().items())))
    assert parse_config(raw).sha256 == a.sha256
    assert parse_config(base_config(template="T2")).sha256 != a.sha256


def _fake_repo(tmp_path, protocol_text="frozen protocol v1\n", recorded=None):
    (tmp_path / "research" / "experiments" / "EXP-001").mkdir(parents=True)
    proto = tmp_path / "research" / "experiments" / "EXP-001" / "protocol.md"
    proto.write_text(protocol_text)
    h = recorded if recorded is not None else hashlib.sha256(protocol_text.encode()).hexdigest()
    with open(tmp_path / "research" / "experiment_registry.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["exp_id", "protocol_path", "protocol_hash"])
        w.writerow(["EXP-001", "research/experiments/EXP-001/protocol.md", h])
    return proto


@pytest.mark.parametrize("exp", ["EXP-001", "EXP-002", "EXP-003"])
def test_freeze_guard_real_repo_accepts_frozen_configs(repo, exp):
    cfg = parse_config(json.loads((repo / "experiments" / f"{exp}.json").read_text()))
    h = require_frozen_if_confirmatory(cfg, repo)
    assert h == hashlib.sha256((repo / "research" / "experiments" / exp / "protocol.md").read_bytes()).hexdigest()


@pytest.mark.parametrize("change", [
    lambda c: c["decoding"].update(num_predict=16),
    lambda c: c.update(repetitions=4, runtime_seeds=[0, 1, 2, 3]),
    lambda c: c["arms"].append({"arm_id": "A3", "model": "qwen3.5:4b"}),
    lambda c: c["items"].update(subset_seed=1),
])
def test_freeze_guard_refuses_changed_config(repo, change):
    raw = json.loads((repo / "experiments" / "EXP-001.json").read_text())
    change(raw)
    with pytest.raises(ProtocolNotFrozen, match="config differs"):
        require_frozen_if_confirmatory(parse_config(raw), repo)


def _frozen_copy(repo, tmp_path):
    fake = tmp_path / "repo"
    for rel in ["research/protocol.md", "research/freeze.json", "research/experiment_registry.csv",
                "research/experiments/EXP-001/protocol.md", "experiments/EXP-001.json"]:
        (fake / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(repo / rel, fake / rel)
    return fake


def test_freeze_guard_refuses_edited_protocols_and_missing_record(repo, tmp_path):
    cfg = parse_config(json.loads((repo / "experiments" / "EXP-001.json").read_text()))
    fake = _frozen_copy(repo, tmp_path)
    assert require_frozen_if_confirmatory(cfg, fake)
    main = fake / "research" / "protocol.md"
    main.write_text(main.read_text() + "\nedited after the freeze\n")
    with pytest.raises(ProtocolNotFrozen, match="protocol.md differs"):
        require_frozen_if_confirmatory(cfg, fake)
    fake2 = _frozen_copy(repo, tmp_path / "b")
    exp = fake2 / "research" / "experiments" / "EXP-001" / "protocol.md"
    exp.write_text(exp.read_text() + "x")
    with pytest.raises(ProtocolNotFrozen, match="not frozen"):
        require_frozen_if_confirmatory(cfg, fake2)
    fake3 = _frozen_copy(repo, tmp_path / "c")
    (fake3 / "research" / "freeze.json").unlink()
    with pytest.raises(ProtocolNotFrozen, match="no freeze record"):
        require_frozen_if_confirmatory(cfg, fake3)


def test_freeze_guard_exp002_refuses_other_configs(repo):
    raw = json.loads((repo / "experiments" / "EXP-001.json").read_text())
    raw["exp_id"] = "EXP-002"
    with pytest.raises(ProtocolNotFrozen, match="config differs"):
        require_frozen_if_confirmatory(parse_config(raw), repo)


def test_freeze_guard_hash_logic(tmp_path):
    proto = _fake_repo(tmp_path)
    assert frozen_protocol_hash(tmp_path, "EXP-001") == hashlib.sha256(proto.read_bytes()).hexdigest()
    proto.write_text("edited after freeze\n")  # any touch after the freeze unfreezes
    assert frozen_protocol_hash(tmp_path, "EXP-001") is None
    assert frozen_protocol_hash(tmp_path, "EXP-002") is None


def test_freeze_guard_placeholder_hash(tmp_path):
    _fake_repo(tmp_path, recorded="none (not frozen)")
    assert frozen_protocol_hash(tmp_path, "EXP-001") is None


def test_cli_run_accepts_frozen_and_refuses_changed(repo, tmp_path, monkeypatch, capsys, dead_url):
    # The guard runs before any runtime contact. Point the backend at a dead port so
    # the accepted config stops at "runtime unavailable" (exit 3) without touching Ollama.
    from token_lab import runner
    monkeypatch.setattr(runner, "make_backend", lambda spec: OllamaBackend(dead_url, 1))
    assert cli.main(["run", "--config", str(repo / "experiments" / "EXP-001.json")]) == 3
    assert "runtime unavailable" in capsys.readouterr().err
    raw = json.loads((repo / "experiments" / "EXP-001.json").read_text())
    raw["repetitions"], raw["runtime_seeds"] = 3, [0, 1, 2]
    p = tmp_path / "changed.json"
    p.write_text(json.dumps(raw))
    assert cli.main(["run", "--config", str(p)]) == 2
    assert "config differs" in capsys.readouterr().err


def test_cli_smoke_refuses_confirmatory(repo, tmp_path, capsys):
    p = tmp_path / "c.json"
    p.write_text(json.dumps(json.loads((repo / "experiments" / "EXP-001.json").read_text())))
    assert cli.main(["smoke", "--config", str(p)]) == 2


# ---- scheduling ----

def test_schedule_crn_and_determinism():
    a1, i1 = schedule(3, 10, 0, 1000)
    a2, i2 = schedule(3, 10, 0, 1000)
    assert (a1, i1) == (a2, i2)
    assert sorted(a1) == [0, 1, 2] and sorted(i1) == list(range(10))
    assert schedule(3, 10, 1, 1000) != (a1, i1)
    with pytest.raises(ValueError):
        schedule(0, 3, 0, 1000)


def test_next_run_id(tmp_path):
    assert next_run_id(tmp_path, "SMOKE") == "RUN-SMOKE-0001"
    (tmp_path / "RUN-SMOKE-0007").mkdir()
    (tmp_path / "RUN-SMOKE-junk").mkdir()
    assert next_run_id(tmp_path, "SMOKE") == "RUN-SMOKE-0008"


# ---- runner integration ----

def test_simulated_run_end_to_end(repo, tmp_path):
    cfg = parse_config(base_config())
    doc, path = execute(cfg, repo, out_root=tmp_path)
    assert doc["label"] == "exploratory" and doc["backend"]["simulated"]
    assert len(doc["records"]) == 3 * 10 * 2
    assert len(doc["blocks"]) == 3 * 2
    assert import_result(path)["run_id"] == "RUN-SMOKE-0001"
    for name in ("run_manifest.json", "config.json"):
        assert (path.parent / name).exists()
    m = doc["manifest"]
    assert m["config_sha256"] == cfg.sha256 and m["git"]["revision"]
    # same item order for every arm in a repetition (common random numbers)
    for rep in (0, 1):
        orders = {}
        for r in doc["records"]:
            if r["repetition"] == rep:
                orders.setdefault(r["arm"], []).append((r["order_index"], r["item_id"]))
        seqs = [tuple(x for _, x in sorted(v)) for v in orders.values()]
        assert len(set(seqs)) == 1
    # accuracy is recomputable from records
    for s in arm_summaries(doc):
        recs = [r for r in doc["records"] if r["arm"] == s["arm"]]
        assert s["accuracy_strict"] == pytest.approx(sum(r["correct_strict"] for r in recs) / len(recs))
        assert s["determinism"] == 1.0  # simulated backend ignores the seed
    # second run gets the next id and identical scored content
    doc2, _ = execute(cfg, repo, out_root=tmp_path)
    assert doc2["run_id"] == "RUN-SMOKE-0002"
    key = lambda d: sorted((r["arm"], r["item_id"], r["repetition"], r["response"]) for r in d["records"])  # noqa: E731
    assert key(doc) == key(doc2)


def test_runner_records_persistent_errors(repo, tmp_path):
    cfg = parse_config(base_config(repetitions=1, runtime_seeds=[0]))
    doc, _ = execute(cfg, repo, backend=SimulatedBackend(fail_models=("llama3.1:8b",)), out_root=tmp_path)
    bad = [r for r in doc["records"] if r["arm"] == "A1"]
    assert all(r["error"] and r["attempts"] == 3 and r["correct_strict"] == 0 for r in bad)
    assert len([f for f in doc["failures"] if f["stage"] == "request"]) == 10
    assert any(f["stage"] == "warmup" for f in doc["failures"])


def test_runner_runtime_down_writes_nothing(repo, tmp_path, dead_url):
    cfg = parse_config(base_config())
    with pytest.raises(RuntimeUnavailable):
        execute(cfg, repo, backend=OllamaBackend(dead_url, 1), out_root=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_runner_against_stub_ollama(repo, tmp_path, stub_ollama):
    cfg = parse_config(base_config(repetitions=1, runtime_seeds=[0], backend={"name": "ollama"}))
    # an arm model, so the block rules see no foreign model (see test_block_rules.py)
    stub_ollama.ps_models = [{"name": "phi4-mini:3.8b", "size": 123, "size_vram": 100}]
    doc, _ = execute(cfg, repo, backend=OllamaBackend(stub_ollama.url, 5), out_root=tmp_path)
    assert not doc["backend"]["simulated"] and doc["backend"]["runtime_version"] == "stub-0.0"
    assert all(r["eval_count"] == 2 and r["response"] == "B." for r in doc["records"])
    assert doc["blocks"][0]["loaded_before"][0]["size_vram"] == 100
    assert stub_ollama.calls == 3 * 10 + 3  # requests plus one warm-up per block


def test_cli_smoke_end_to_end(repo, monkeypatch, tmp_path, capsys):
    # run the CLI against a copy of the repository layout so real results are not touched
    fake = tmp_path / "repo"
    (fake / "data" / "fixtures").mkdir(parents=True)
    shutil.copy(repo / "data" / "fixtures" / "synthetic_mc.jsonl", fake / "data" / "fixtures")
    monkeypatch.setattr(cli, "REPO", fake)
    cfgp = tmp_path / "c.json"
    cfgp.write_text(json.dumps(base_config()))
    assert cli.main(["smoke", "--config", str(cfgp)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["simulated"] and out["requests"] == 60
    assert cli.main(["report", "--result", out["result"]]) == 0


# ---- schema ----

def _valid_doc(repo, tmp_path):
    doc, _ = execute(parse_config(base_config(repetitions=1, runtime_seeds=[0])), repo, out_root=tmp_path)
    return doc


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(schema_version="0.9.0"),
    lambda d: d.update(label="final"),
    lambda d: d.update(run_id="RUN-EXP-001-0001"),
    lambda d: d.update(label="confirmatory"),  # simulated backend can never be confirmatory
    lambda d: d["records"][0].update(correct_strict=2),
    lambda d: d["records"][0].update(latency_ms=-1.0),
    lambda d: d["records"][0].pop("item_id"),
    lambda d: d["records"][0].update(extra_field=1),
    lambda d: d.pop("manifest"),
    lambda d: d.update(config_sha256="abc"),
])
def test_schema_rejects_malformed(repo, tmp_path, mutate):
    doc = copy.deepcopy(_valid_doc(repo, tmp_path))
    mutate(doc)
    with pytest.raises(ResultValidationError):
        validate(doc)
    with pytest.raises(ResultValidationError):
        export_result(doc, tmp_path / "x.json")
    assert not (tmp_path / "x.json").exists()


def test_import_rejects_bad_files(tmp_path):
    p = tmp_path / "r.json"
    p.write_text("{oops")
    with pytest.raises(ResultValidationError):
        import_result(p)
    p.write_text("[]")
    with pytest.raises(ResultValidationError):
        import_result(p)


def test_report_fails_closed(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"schema_version": "1.0.0"}))
    with pytest.raises(ResultValidationError):
        build_report(p)
    assert cli.main(["report", "--result", str(p)]) == 2


# ---- analysis and report ----

def test_analysis_hand_example(repo, tmp_path):
    doc = copy.deepcopy(_valid_doc(repo, tmp_path))
    # Overwrite correctness: A0 right on items 0-4, A1 right on all, A2 right on none.
    ids = sorted({r["item_id"] for r in doc["records"]})
    for r in doc["records"]:
        k = ids.index(r["item_id"])
        r["correct_strict"] = {"A0": int(k < 5), "A1": 1, "A2": 0}[r["arm"]]
    rows = {c["arm"]: c for c in contrasts(doc, "strict", n_boot=500)}
    assert rows["A1"]["delta_pp"] == pytest.approx(50.0) and (rows["A1"]["b"], rows["A1"]["c"]) == (5, 0)
    assert rows["A2"]["delta_pp"] == pytest.approx(-50.0) and (rows["A2"]["b"], rows["A2"]["c"]) == (0, 5)
    assert rows["A1"]["mcnemar_p"] == pytest.approx(2 / 32)
    assert rows["A1"]["holm_p"] == pytest.approx(min(1, 2 * 2 / 32))
    proj = projection(doc)
    assert proj["simulated_backend"] and proj["projected_hours"]["EXP-001"] >= 0


def test_report_outputs(repo, tmp_path):
    doc = _valid_doc(repo, tmp_path)
    path = tmp_path / doc["run_id"] / "result.json"
    info = build_report(path)
    md = open(info["report_md"]).read()
    assert "EXPLORATORY" in md and "SIMULATED" in md and "synthetic fixture" in md
    assert chr(0x2014) not in md  # no em dashes
    svg = open(info["figure"]).read()
    assert svg.startswith("<svg") and "<title>" in svg
    with open(info["metrics_csv"]) as fh:
        rows = list(csv.DictReader(fh))
    assert [r["arm"] for r in rows] == ["A0", "A1", "A2"]


# ---- hardware logs ----

def test_hardware_logs(repo):
    h = host_info()
    for k in ("os", "cpu", "cpu_count_logical", "memory_total_bytes", "power", "load_avg_1_5_15"):
        assert k in h
    assert h["memory_total_bytes"] > 0 and h["cpu_count_logical"] >= 1
    assert h["power"]["source"] in ("ac", "battery", "unknown", None)
    g = git_state(repo)
    assert g["revision"] and len(g["revision"]) == 40
    v = package_versions()
    assert v["numpy"] and v["psutil"] and v["python"]


def test_memory_sampler_sees_own_process():
    me = os.getpid()
    with MemorySampler(lambda p: p.pid == me, hz=50) as s:
        buf = bytearray(64 * 2**20)
        buf[::4096] = b"x" * len(buf[::4096])
    summ = s.summary()
    assert summ["peak_rss_mib"] is not None and summ["peak_rss_mib"] > 64
    assert s.samples >= 2
    del buf
    with MemorySampler(lambda p: False, hz=50) as s2:
        pass
    assert s2.summary()["peak_rss_mib"] is None  # never imputed
    with pytest.raises(ValueError):
        MemorySampler(lambda p: True, hz=0)


# ---- freeze amendments (owner-approved 2026-11-24) ----

from token_lab.analysis import arm_summaries as _arm_summaries  # noqa: E402
from token_lab.runner import arm_fingerprints, verify_items  # noqa: E402
from token_lab.runtime import RuntimeReportedError, model_fingerprint  # noqa: E402


def test_model_fingerprint_hashes_and_missing_fields():
    fp = model_fingerprint({"template": "{{ .Prompt }}", "parameters": "stop x", "details": {"format": "gguf"}})
    assert fp["template_sha256"] == hashlib.sha256(b"{{ .Prompt }}").hexdigest()
    assert fp["parameters_sha256"] == hashlib.sha256(b"stop x").hexdigest()
    assert fp["system_sha256"] is None and fp["modelfile_sha256"] is None  # never imputed
    assert fp["format"] == "gguf"
    assert model_fingerprint({"template": "a"})["template_sha256"] != model_fingerprint({"template": "b"})["template_sha256"]


def test_runner_records_template_hashes_from_stub(repo, tmp_path, stub_ollama):
    cfg = parse_config(base_config(repetitions=1, runtime_seeds=[0], backend={"name": "ollama"}))
    doc, path = execute(cfg, repo, backend=OllamaBackend(stub_ollama.url, 5), out_root=tmp_path)
    ar = doc["manifest"]["arm_runtime"]
    assert set(ar) == {"A0", "A1", "A2"} and stub_ollama.show_calls == 3
    assert ar["A0"]["template_sha256"] == hashlib.sha256(b"{{ .Prompt }}").hexdigest()
    assert ar["A1"]["modelfile_sha256"] == hashlib.sha256(b"FROM llama3.1:8b").hexdigest()
    assert json.loads((path.parent / "run_manifest.json").read_text())["arm_runtime"] == ar


class _NoShow(SimulatedBackend):
    def show(self, model):
        raise RuntimeReportedError("no such model")


def test_fingerprint_failure_exploratory_recorded_confirmatory_aborts():
    cfg = parse_config(base_config())
    out = arm_fingerprints(cfg, _NoShow())
    assert all("error" in v for v in out.values())
    raw = json.loads(json.dumps(base_config()))
    conf = parse_config({**raw, "exp_id": "EXP-001", "mode": "confirmatory", "backend": {"name": "ollama"},
                         "items": {**raw["items"], "source_sha256": "0" * 64, "subset_ids_path": "x.json"}})
    with pytest.raises(RuntimeReportedError):
        arm_fingerprints(conf, _NoShow())


def test_confirmatory_config_must_pin_items():
    raw = base_config(exp_id="EXP-001", mode="confirmatory", backend={"name": "ollama"})
    raw["items"] = {**raw["items"], "subset_size": 5}
    with pytest.raises(ConfigError, match="pin"):
        parse_config(raw)
    raw["items"]["source_sha256"] = "XYZ"
    with pytest.raises(ConfigError, match="source_sha256"):
        parse_config(raw)


def test_verify_items_fails_closed(repo, tmp_path):
    from token_lab.items import load_items, seeded_subset
    items, sha = load_items(repo / "data" / "fixtures" / "synthetic_mc.jsonl")
    sub = seeded_subset(items, 5, 20261124)
    ids = tmp_path / "ids.json"
    ids.write_text(json.dumps({"item_ids": sorted(i.item_id for i in sub)}))
    raw = base_config()
    raw["items"] = {**raw["items"], "subset_size": 5, "source_sha256": sha, "subset_ids_path": str(ids)}
    verify_items(parse_config(raw), sha, sub, repo)  # matches: no error
    with pytest.raises(ValueError, match="SHA-256"):
        verify_items(parse_config({**raw, "items": {**raw["items"], "source_sha256": "f" * 64}}), sha, sub, repo)
    ids.write_text(json.dumps({"item_ids": sorted(i.item_id for i in items[:5])[::-1] + ["other"]}))
    with pytest.raises(ValueError, match="item IDs"):
        verify_items(parse_config(raw), sha, sub, repo)


def test_frozen_subset_ids_match_committed_manifest(repo):
    ids = json.loads((repo / "data" / "arc_challenge_test_subset_ids.json").read_text())
    assert ids["subset_size"] == len(ids["item_ids"]) == len(set(ids["item_ids"])) == 300
    assert ids["subset_seed"] == 20261124 and ids["license"] == "CC-BY-SA-4.0"
    cfg = json.loads((repo / "experiments" / "EXP-001.json").read_text())
    assert cfg["items"]["source_sha256"] == ids["jsonl_sha256"]
    assert "question" not in json.dumps(ids["item_ids"])  # IDs only, no texts
    arc = repo / "results" / "raw" / "arc" / "ARC-Challenge-test.jsonl"
    if arc.is_file():  # the raw file is not committed; check it when present
        from token_lab.items import load_items, seeded_subset
        items, sha = load_items(arc)
        assert sha == ids["jsonl_sha256"]
        assert sorted(i.item_id for i in seeded_subset(items, 300, 20261124)) == ids["item_ids"]


def test_named_memory_metric_runtime_reported(repo, tmp_path, stub_ollama):
    cfg = parse_config(base_config(repetitions=1, runtime_seeds=[0], backend={"name": "ollama"},
                                   arms=[{"arm_id": "A0", "model": "m"}, {"arm_id": "A1", "model": "n"}]))
    doc, _ = execute(cfg, repo, backend=OllamaBackend(stub_ollama.url, 5), out_root=tmp_path)
    s = {x["arm"]: x for x in _arm_summaries(doc)}
    assert s["A0"]["runtime_model_mib"] == pytest.approx(123 / 2**20)  # stub /api/ps reports model "m"
    assert s["A1"]["runtime_model_mib"] is None  # not reported, never imputed


def test_mcnemar_majority_rule_over_repetitions():
    from token_lab.stats import paired_compare
    # item means over five repetitions: 0.6 -> correct, 0.4 -> incorrect (majority rule)
    pd = paired_compare([0.6, 0.4, 1.0, 0.0], [0.4, 0.6, 1.0, 0.0], n_boot=200, seed=7)
    assert (pd.b, pd.c) == (1, 1)
    assert pd.delta == pytest.approx(0.0)
