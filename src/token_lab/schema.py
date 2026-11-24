# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Versioned JSON result schema, validated at export and at import (fail closed)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

SCHEMA_VERSION = "1.0.0"

_num_or_null = {"type": ["number", "null"]}
_int_or_null = {"type": ["integer", "null"], "minimum": 0}

RECORD_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "arm", "model", "item_id", "repetition", "order_index", "runtime_seed", "template",
        "response", "extracted_strict", "extracted_lenient", "answer_key", "n_choices",
        "correct_strict", "correct_lenient", "error", "attempts", "latency_ms", "ttft_ms",
        "stream_chunks", "prompt_eval_count", "eval_count", "prompt_eval_duration_ns",
        "eval_duration_ns", "load_duration_ns", "total_duration_ns",
    ],
    "properties": {
        "arm": {"type": "string", "minLength": 1},
        "model": {"type": "string", "minLength": 1},
        "item_id": {"type": "string", "minLength": 1},
        "repetition": {"type": "integer", "minimum": 0},
        "order_index": {"type": "integer", "minimum": 0},
        "runtime_seed": {"type": "integer"},
        "template": {"enum": ["T1", "T2", "T3"]},
        "response": {"type": ["string", "null"]},
        "extracted_strict": {"type": ["string", "null"]},
        "extracted_lenient": {"type": ["string", "null"]},
        "answer_key": {"type": "string"},
        "n_choices": {"type": "integer", "minimum": 2},
        "correct_strict": {"enum": [0, 1]},
        "correct_lenient": {"enum": [0, 1]},
        "error": {"type": ["string", "null"]},
        "attempts": {"type": "integer", "minimum": 1},
        "latency_ms": {"type": ["number", "null"], "minimum": 0},
        "ttft_ms": {"type": ["number", "null"], "minimum": 0},
        "stream_chunks": _int_or_null,
        "prompt_eval_count": _int_or_null,
        "eval_count": _int_or_null,
        "prompt_eval_duration_ns": _int_or_null,
        "eval_duration_ns": _int_or_null,
        "load_duration_ns": _int_or_null,
        "total_duration_ns": _int_or_null,
        # EXP-002 cold/warm design only (optional, additive; matrix records omit them)
        "start_state": {"enum": ["cold", "warm"]},
        "trial_index": {"type": "integer", "minimum": 0},
        "state_valid": {"type": "boolean"},
        "state_check": {"type": "object"},
    },
    "dependentRequired": {"start_state": ["trial_index", "state_valid", "state_check"]},
}

BLOCK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["arm", "repetition", "start_utc", "wall_s", "memory", "loaded_before", "loaded_after"],
    "properties": {
        "arm": {"type": "string"},
        "repetition": {"type": "integer", "minimum": 0},
        "start_utc": {"type": "string"},
        "wall_s": {"type": "number", "minimum": 0},
        "memory": {"type": "object"},
        "loaded_before": {"type": ["array", "null"]},
        "loaded_after": {"type": ["array", "null"]},
    },
}

RESULT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "token-lab result",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "kind", "label", "exp_id", "run_id", "config", "config_sha256",
                 "backend", "items_source", "records", "blocks", "failures", "manifest"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "kind": {"const": "token-lab-result"},
        "label": {"enum": ["exploratory", "confirmatory"]},
        "exp_id": {"type": "string", "pattern": r"^(EXP-\d{3}|SMOKE)$"},
        "run_id": {"type": "string", "pattern": r"^RUN-(EXP-\d{3}|SMOKE)-\d{4}$"},
        "config": {"type": "object"},
        "config_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "backend": {
            "type": "object",
            "required": ["name", "simulated", "runtime_version"],
            "properties": {
                "name": {"type": "string"},
                "simulated": {"type": "boolean"},
                "runtime_version": {"type": ["string", "null"]},
            },
        },
        "items_source": {
            "type": "object",
            "required": ["path", "sha256", "n_items", "synthetic"],
            "properties": {
                "path": {"type": "string"},
                "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                "n_items": {"type": "integer", "minimum": 1},
                "synthetic": {"type": "boolean"},
            },
        },
        "records": {"type": "array", "items": RECORD_SCHEMA},
        "blocks": {"type": "array", "items": BLOCK_SCHEMA},
        "failures": {"type": "array", "items": {"type": "object"}},
        "manifest": {"type": "object", "required": ["config_sha256", "git", "packages", "host",
                                                    "start_utc", "end_utc", "runtime_s"]},
    },
}


class ResultValidationError(ValueError):
    pass


def validate(doc: dict) -> None:
    try:
        jsonschema.validate(doc, RESULT_SCHEMA)
    except jsonschema.ValidationError as exc:
        path = "/".join(str(p) for p in exc.absolute_path)
        raise ResultValidationError(f"result invalid at '{path}': {exc.message}") from None
    if doc["label"] == "confirmatory" and doc["backend"]["simulated"]:
        raise ResultValidationError("a simulated backend can never produce a confirmatory result")
    if doc["exp_id"] not in doc["run_id"]:
        raise ResultValidationError("run_id does not belong to exp_id")


def export_result(doc: dict, path: str | Path) -> Path:
    validate(doc)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return p


def import_result(path: str | Path) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ResultValidationError(f"{path}: not JSON ({exc.msg})") from None
    if not isinstance(doc, dict):
        raise ResultValidationError(f"{path}: not a JSON object")
    validate(doc)
    return doc
