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


def test_freeze_guard_real_repo_refuses(repo):
    cfg = parse_config(json.loads((repo / "experiments" / "EXP-001.json").read_text()))
    assert frozen_protocol_hash(repo, "EXP-001") is None
    with pytest.raises(ProtocolNotFrozen):
        require_frozen_if_confirmatory(cfg, repo)


def test_freeze_guard_hash_logic(tmp_path):
    proto = _fake_repo(tmp_path)
    assert frozen_protocol_hash(tmp_path, "EXP-001") == hashlib.sha256(proto.read_bytes()).hexdigest()
    proto.write_text("edited after freeze\n")  # any touch after the freeze unfreezes
    assert frozen_protocol_hash(tmp_path, "EXP-001") is None
    assert frozen_protocol_hash(tmp_path, "EXP-002") is None


def test_freeze_guard_placeholder_hash(tmp_path):
    _fake_repo(tmp_path, recorded="none (not frozen)")
    assert frozen_protocol_hash(tmp_path, "EXP-001") is None


def test_cli_run_refuses_confirmatory(repo, capsys):
    assert cli.main(["run", "--config", str(repo / "experiments" / "EXP-001.json")]) == 2
    assert "not frozen" in capsys.readouterr().err


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
    assert "—" not in md  # no em dashes
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
