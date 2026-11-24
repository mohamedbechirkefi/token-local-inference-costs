# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Inference backends.

``OllamaBackend`` talks to an already running local Ollama server with the
standard library only (streaming ``/api/generate``; time to first token is
measured on the client). It never starts, stops, pulls or unloads models;
unloading for EXP-002 is a separate, explicit call that the runner only makes
in an owner-scheduled window.

``SimulatedBackend`` is a deterministic stand-in for testing the harness. Its
outputs are SIMULATED: they contain no model output and no inference timing.
"""

from __future__ import annotations

import hashlib
import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .tokens import CounterError, Counters, parse_counters


class BackendError(RuntimeError):
    """Base class for backend failures."""


class RuntimeUnavailable(BackendError):
    """The runtime could not be reached (connection refused, DNS, etc.)."""


class RuntimeTimeout(BackendError):
    """The request exceeded its timeout."""


class MalformedResponse(BackendError):
    """The runtime replied with something that does not follow the API."""


class RuntimeReportedError(BackendError):
    """The runtime replied with an explicit error object."""


@dataclass(frozen=True)
class Decoding:
    temperature: float
    num_predict: int
    num_ctx: int

    def __post_init__(self) -> None:
        if self.temperature < 0:
            raise ValueError("temperature must be >= 0")
        if self.num_predict < 1 or self.num_ctx < 1:
            raise ValueError("num_predict and num_ctx must be >= 1")


@dataclass(frozen=True)
class Generation:
    text: str
    latency_ms: float  # client wall-clock, request sent to response complete
    ttft_ms: float | None  # client wall-clock to first non-empty chunk
    stream_chunks: int  # non-empty streamed chunks (diagnostic only)
    counters: Counters
    simulated: bool


class Backend(Protocol):
    name: str
    simulated: bool

    def generate(self, model: str, prompt: str, decoding: Decoding, seed: int) -> Generation: ...

    def version(self) -> str | None: ...

    def loaded_models(self) -> list[dict]: ...

    def show(self, model: str) -> dict: ...


def _sha(value) -> str | None:
    if value is None:
        return None
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def model_fingerprint(show: dict) -> dict:
    """SHA-256 of each model's chat template, default system prompt, default
    parameters and Modelfile as reported by ``/api/show`` (protocol amendment
    A5, owner-approved 2026-11-24). A missing field hashes to None, never to a
    made-up value; the raw texts are not stored."""
    details = show.get("details") if isinstance(show.get("details"), dict) else {}
    return {
        "template_sha256": _sha(show.get("template")),
        "system_sha256": _sha(show.get("system")),
        "parameters_sha256": _sha(show.get("parameters")),
        "modelfile_sha256": _sha(show.get("modelfile")),
        "format": details.get("format"),
        "quantization_level": details.get("quantization_level"),
        "parameter_size": details.get("parameter_size"),
    }


class OllamaBackend:
    name = "ollama"
    simulated = False

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout_s: float = 120.0):
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _open(self, path: str, body: dict | None = None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        try:
            return urllib.request.urlopen(req, timeout=self.timeout_s)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:200]
            raise RuntimeReportedError(f"HTTP {exc.code}: {detail}") from None
        except (socket.timeout, TimeoutError):
            raise RuntimeTimeout(f"timeout after {self.timeout_s}s on {path}") from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                raise RuntimeTimeout(f"timeout after {self.timeout_s}s on {path}") from None
            raise RuntimeUnavailable(f"{self.base_url}{path}: {exc.reason}") from None
        except ConnectionError as exc:
            raise RuntimeUnavailable(f"{self.base_url}{path}: {exc}") from None

    def _get_json(self, path: str) -> dict:
        with self._open(path) as resp:
            raw = resp.read()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            raise MalformedResponse(f"{path}: not JSON") from None
        if not isinstance(obj, dict):
            raise MalformedResponse(f"{path}: not a JSON object")
        return obj

    def version(self) -> str | None:
        v = self._get_json("/api/version").get("version")
        return v if isinstance(v, str) else None

    def loaded_models(self) -> list[dict]:
        models = self._get_json("/api/ps").get("models", [])
        if not isinstance(models, list):
            raise MalformedResponse("/api/ps: models is not a list")
        return [m for m in models if isinstance(m, dict)]

    def show(self, model: str) -> dict:
        """``POST /api/show`` for one model (read-only; loads nothing)."""
        with self._open("/api/show", {"model": model}) as resp:
            raw = resp.read()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            raise MalformedResponse("/api/show: not JSON") from None
        if not isinstance(obj, dict):
            raise MalformedResponse("/api/show: not a JSON object")
        return obj

    def generate(self, model: str, prompt: str, decoding: Decoding, seed: int) -> Generation:
        body = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": decoding.temperature,
                "num_predict": decoding.num_predict,
                "num_ctx": decoding.num_ctx,
                "seed": seed,
            },
        }
        t0 = time.perf_counter_ns()
        ttft_ns: int | None = None
        parts: list[str] = []
        chunks = 0
        final: dict | None = None
        resp = self._open("/api/generate", body)
        try:
            for line in resp:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    raise MalformedResponse("stream line is not JSON") from None
                if not isinstance(obj, dict):
                    raise MalformedResponse("stream line is not a JSON object")
                if "error" in obj:
                    raise RuntimeReportedError(str(obj["error"])[:200])
                piece = obj.get("response", "")
                if not isinstance(piece, str):
                    raise MalformedResponse("response field is not a string")
                if piece:
                    chunks += 1
                    if ttft_ns is None:
                        ttft_ns = time.perf_counter_ns() - t0
                    parts.append(piece)
                if obj.get("done") is True:
                    final = obj
                    break
        except (socket.timeout, TimeoutError):
            raise RuntimeTimeout(f"timeout after {self.timeout_s}s while streaming") from None
        finally:
            resp.close()
        t1 = time.perf_counter_ns()
        if final is None:
            raise MalformedResponse("stream ended without a done chunk")
        try:
            counters = parse_counters(final)
        except CounterError as exc:
            raise MalformedResponse(str(exc)) from None
        return Generation(
            text="".join(parts),
            latency_ms=(t1 - t0) / 1e6,
            ttft_ms=None if ttft_ns is None else ttft_ns / 1e6,
            stream_chunks=chunks,
            counters=counters,
            simulated=False,
        )


class SimulatedBackend:
    """Deterministic harness stand-in. SIMULATED: no model, no inference.

    The reply is a pure function of (model, prompt): one of the displayed
    labels found in the prompt's instruction line, or, for about 1 prompt in
    10, an unparseable sentence (to exercise format-failure handling). The
    seed is ignored, mimicking greedy decoding. Counters are synthetic and the
    reported latency is the harness's own wall-clock for this call.
    """

    name = "simulated"
    simulated = True

    def __init__(self, fail_models: tuple[str, ...] = ()):
        self.fail_models = fail_models

    def version(self) -> str | None:
        return "simulated-0"

    def loaded_models(self) -> list[dict]:
        return []

    def show(self, model: str) -> dict:
        return {"template": f"SIMULATED template for {model}", "system": None,
                "parameters": None, "modelfile": None, "details": {"format": "simulated"}}

    def generate(self, model: str, prompt: str, decoding: Decoding, seed: int) -> Generation:
        t0 = time.perf_counter_ns()
        if model in self.fail_models:
            raise RuntimeReportedError(f"simulated failure for {model}")
        digest = hashlib.sha256(f"{model}\x00{prompt}".encode()).digest()
        last = prompt.rstrip().splitlines()[-1]
        inside = last[last.find("(") + 1 : last.find(")")] if "(" in last else ""
        if not inside and "one of " in last:
            inside = last.split("one of ", 1)[1].split(".")[0]
        labels = [x.strip() for x in inside.split(",") if x.strip()]
        if digest[0] % 10 == 0 or not labels:
            text = "I cannot determine this."
        else:
            text = labels[digest[1] % len(labels)]
        n_prompt = max(1, len(prompt.split()))
        n_out = max(1, len(text.split()))
        t1 = time.perf_counter_ns()
        return Generation(
            text=text,
            latency_ms=(t1 - t0) / 1e6,
            ttft_ms=(t1 - t0) / 1e6,
            stream_chunks=n_out,
            counters=Counters(n_prompt, n_out, 1_000 * n_prompt, 1_000 * n_out, 0, t1 - t0),
            simulated=True,
        )


def make_backend(spec: dict) -> Backend:
    name = spec.get("name")
    if name == "ollama":
        return OllamaBackend(spec.get("base_url", "http://127.0.0.1:11434"), float(spec.get("timeout_s", 120)))
    if name == "simulated":
        return SimulatedBackend(tuple(spec.get("fail_models", ())))
    raise ValueError(f"unknown backend {name!r}")
