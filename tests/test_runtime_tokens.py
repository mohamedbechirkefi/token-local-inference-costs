# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Token counting and runtime error handling against a local stub server."""

import pytest

from conftest import final_chunk
from token_lab.runtime import (
    Decoding,
    MalformedResponse,
    OllamaBackend,
    RuntimeReportedError,
    RuntimeTimeout,
    RuntimeUnavailable,
    SimulatedBackend,
    make_backend,
)
from token_lab.tokens import CounterError, ns_to_ms, parse_counters, throughput_tps

DEC = Decoding(0.0, 8, 2048)


def test_counters_hand_counted():
    c = parse_counters(final_chunk())
    assert (c.prompt_eval_count, c.eval_count) == (40, 2)
    # 2 tokens in 50 ms -> 40 tok/s; 40 tokens in 100 ms -> 400 tok/s
    assert throughput_tps(c.eval_count, c.eval_duration_ns) == pytest.approx(40.0)
    assert throughput_tps(c.prompt_eval_count, c.prompt_eval_duration_ns) == pytest.approx(400.0)
    assert ns_to_ms(c.total_duration_ns) == 500.0


def test_counters_missing_and_invalid():
    c = parse_counters({"done": True, "eval_count": 3})
    assert c.prompt_eval_count is None and c.eval_duration_ns is None
    assert throughput_tps(c.eval_count, c.eval_duration_ns) is None
    assert throughput_tps(5, 0) is None
    for bad in ({"eval_count": -1}, {"eval_count": 1.5}, {"eval_count": True}, {"eval_duration": "7"}):
        with pytest.raises(CounterError):
            parse_counters(bad)
    with pytest.raises(CounterError):
        throughput_tps(-1, 10)


def test_ollama_ok_stream(stub_ollama):
    b = OllamaBackend(stub_ollama.url, timeout_s=5)
    assert b.version() == "stub-0.0"
    assert b.loaded_models()[0]["size_vram"] == 100
    g = b.generate("m", "p", DEC, seed=0)
    assert g.text == "B."
    assert g.stream_chunks == 2
    assert g.counters.eval_count == 2
    assert g.ttft_ms is not None and 0 <= g.ttft_ms <= g.latency_ms
    assert not g.simulated


def test_runtime_down(dead_url):
    b = OllamaBackend(dead_url, timeout_s=2)
    with pytest.raises(RuntimeUnavailable):
        b.version()
    with pytest.raises(RuntimeUnavailable):
        b.generate("m", "p", DEC, 0)


def test_timeout(stub_ollama):
    stub_ollama.mode = "sleep"
    stub_ollama.sleep_s = 1.5
    with pytest.raises(RuntimeTimeout):
        OllamaBackend(stub_ollama.url, timeout_s=0.3).generate("m", "p", DEC, 0)


@pytest.mark.parametrize("mode,exc", [
    ("malformed", MalformedResponse),
    ("no_done", MalformedResponse),
    ("bad_counter", MalformedResponse),
    ("error", RuntimeReportedError),
    ("http500", RuntimeReportedError),
])
def test_malformed_and_errors(stub_ollama, mode, exc):
    stub_ollama.mode = mode
    with pytest.raises(exc):
        OllamaBackend(stub_ollama.url, timeout_s=5).generate("m", "p", DEC, 0)


def test_decoding_and_backend_validation():
    with pytest.raises(ValueError):
        Decoding(-0.1, 8, 2048)
    with pytest.raises(ValueError):
        Decoding(0, 0, 2048)
    with pytest.raises(ValueError):
        OllamaBackend("http://x", timeout_s=0)
    with pytest.raises(ValueError):
        make_backend({"name": "hosted-api"})


def test_simulated_is_deterministic_and_labelled():
    b = SimulatedBackend()
    p = "Question: q\nA. x\nB. y\nReply with the label of the correct choice only (A, B). Do not explain."
    g1, g2 = b.generate("m", p, DEC, 0), b.generate("m", p, DEC, 4)
    assert g1.text == g2.text and g1.simulated
    assert g1.text in ("A", "B", "I cannot determine this.")
    with pytest.raises(RuntimeReportedError):
        SimulatedBackend(fail_models=("m",)).generate("m", p, DEC, 0)
