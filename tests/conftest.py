# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Shared fixtures, including a local stub of the Ollama HTTP API (no real runtime)."""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo() -> Path:
    return REPO


def final_chunk(**over):
    d = {"model": "m", "response": "", "done": True, "total_duration": 500_000_000,
         "load_duration": 10_000_000, "prompt_eval_count": 40, "prompt_eval_duration": 100_000_000,
         "eval_count": 2, "eval_duration": 50_000_000}
    d.update(over)
    return d


class StubState:
    def __init__(self):
        self.mode = "ok"  # ok | malformed | no_done | error | sleep | bad_counter | http500
        self.reply = ["B", "."]
        self.calls = 0
        self.sleep_s = 2.0
        self.show_calls = 0
        self.show_mode = "ok"  # ok | error
        self.bodies = []  # every POST /api/generate body, in order


@pytest.fixture
def stub_ollama():
    state = StubState()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body: bytes, code=200):
            self.send_response(code)
            self.send_header("Content-Type", "application/x-ndjson")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/api/version":
                self._send(json.dumps({"version": "stub-0.0"}).encode())
            elif self.path == "/api/ps":
                self._send(json.dumps({"models": [{"name": "m", "size": 123, "size_vram": 100}]}).encode())
            else:
                self._send(b"{}", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n))
            if self.path == "/api/show":
                state.show_calls += 1
                if state.show_mode == "error":
                    self._send(b'{"error":"model not found"}', 404)
                    return
                self._send(json.dumps({"template": "{{ .Prompt }}", "system": "",
                                       "parameters": "stop <eot>", "modelfile": f"FROM {body.get('model')}",
                                       "details": {"format": "gguf", "quantization_level": "Q4_K_M",
                                                   "parameter_size": "8.0B"}}).encode())
                return
            state.bodies.append(body)
            if body.get("keep_alive") == 0 and "prompt" not in body:  # unload request
                self._send(json.dumps({"model": body.get("model"), "done": True,
                                       "done_reason": "unload"}).encode())
                return
            state.calls += 1
            m = state.mode
            if m == "http500":
                self._send(b'{"error":"boom"}', 500)
                return
            if m == "sleep":
                time.sleep(state.sleep_s)
            if m == "malformed":
                self._send(b"this is not json\n")
                return
            lines = [json.dumps({"response": p, "done": False}) for p in state.reply]
            if m == "error":
                lines = [json.dumps({"error": "model not found"})]
            elif m == "bad_counter":
                lines.append(json.dumps(final_chunk(eval_count=-1)))
            elif m != "no_done":
                lines.append(json.dumps(final_chunk()))
            self._send(("\n".join(lines) + "\n").encode())

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    state.url = f"http://127.0.0.1:{srv.server_address[1]}"
    yield state
    srv.shutdown()
    srv.server_close()


@pytest.fixture
def dead_url():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # nothing listens on this port now
    return f"http://127.0.0.1:{port}"
