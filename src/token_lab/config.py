# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Run configuration: validation, canonical hash and the protocol-freeze guard."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .prompts import TEMPLATE_IDS
from .runtime import Decoding


class ConfigError(ValueError):
    pass


class ProtocolNotFrozen(RuntimeError):
    """Raised when a confirmatory run is requested for an unfrozen protocol (G-FREEZE)."""


@dataclass(frozen=True)
class Arm:
    arm_id: str
    model: str


@dataclass(frozen=True)
class ColdWarm:
    """EXP-002 cold/warm design (EXP-002 protocol items 9 to 12, 14, 17 and 18).

    Per arm: ``trials_per_state`` pairs, each an unload confirmed by ``/api/ps``
    followed by a cold request, then a warm request immediately after it (cold
    first, strictly alternating). Arm order is a permutation from
    ``default_rng(arm_order_seed)``. ``wall_cap_s`` is the stopping rule.
    """

    trials_per_state: int
    arm_order_seed: int
    unload_confirm_timeout_s: float
    unload_poll_s: float
    wall_cap_s: float


@dataclass(frozen=True)
class RunConfig:
    raw: dict
    exp_id: str
    mode: str
    backend: dict
    arms: tuple[Arm, ...]
    items_path: str
    items_synthetic: bool
    subset_size: int | None
    subset_seed: int
    template: str
    repetitions: int
    runtime_seeds: tuple[int, ...]
    order_seed_base: int
    decoding: Decoding
    max_retries: int
    warmup: bool
    memory_sample_hz: float
    process_match: str
    items_source_sha256: str | None = None
    subset_ids_path: str | None = None
    design: str = "matrix"
    cold_warm: ColdWarm | None = None

    @property
    def sha256(self) -> str:
        return config_sha256(self.raw)


def config_sha256(raw: dict) -> str:
    canon = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canon.encode()).hexdigest()


def _req(d: dict, key: str, typ, where: str = "config"):
    if key not in d:
        raise ConfigError(f"{where}: missing '{key}'")
    v = d[key]
    if typ is int and isinstance(v, bool):
        raise ConfigError(f"{where}.{key}: expected int")
    if not isinstance(v, typ):
        raise ConfigError(f"{where}.{key}: expected {typ}")
    return v


def parse_config(raw: dict) -> RunConfig:
    if not isinstance(raw, dict):
        raise ConfigError("config must be a JSON object")
    exp_id = _req(raw, "exp_id", str)
    if not re.fullmatch(r"EXP-\d{3}|SMOKE", exp_id):
        raise ConfigError("exp_id must be EXP-NNN or SMOKE")
    mode = _req(raw, "mode", str)
    if mode not in ("exploratory", "confirmatory"):
        raise ConfigError("mode must be exploratory or confirmatory")
    if mode == "confirmatory" and exp_id == "SMOKE":
        raise ConfigError("a SMOKE config cannot be confirmatory")
    backend = _req(raw, "backend", dict)
    if backend.get("name") not in ("ollama", "simulated"):
        raise ConfigError("backend.name must be ollama or simulated")
    if mode == "confirmatory" and backend["name"] == "simulated":
        raise ConfigError("a simulated backend cannot be confirmatory")
    arms_raw = _req(raw, "arms", list)
    if not arms_raw:
        raise ConfigError("at least one arm required")
    arms = []
    for i, a in enumerate(arms_raw):
        if not isinstance(a, dict):
            raise ConfigError(f"arms[{i}] must be an object")
        arms.append(Arm(_req(a, "arm_id", str, f"arms[{i}]"), _req(a, "model", str, f"arms[{i}]")))
    if len({a.arm_id for a in arms}) != len(arms):
        raise ConfigError("duplicate arm_id")
    items = _req(raw, "items", dict)
    subset = items.get("subset_size")
    if subset is not None and (isinstance(subset, bool) or not isinstance(subset, int) or subset < 1):
        raise ConfigError("items.subset_size must be a positive int or null")
    src_sha = items.get("source_sha256")
    if src_sha is not None and (not isinstance(src_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", src_sha)):
        raise ConfigError("items.source_sha256 must be 64 lowercase hex characters")
    ids_path = items.get("subset_ids_path")
    if ids_path is not None and not isinstance(ids_path, str):
        raise ConfigError("items.subset_ids_path must be a string")
    if mode == "confirmatory" and (src_sha is None or (subset is not None and ids_path is None)):
        raise ConfigError("a confirmatory config must pin items.source_sha256 and items.subset_ids_path")
    template = _req(raw, "template", str)
    if template not in TEMPLATE_IDS:
        raise ConfigError(f"template must be one of {TEMPLATE_IDS}")
    reps = _req(raw, "repetitions", int)
    if reps < 1:
        raise ConfigError("repetitions must be >= 1")
    seeds = _req(raw, "runtime_seeds", list)
    if len(seeds) != reps or not all(isinstance(s, int) and not isinstance(s, bool) for s in seeds):
        raise ConfigError("runtime_seeds must list one int per repetition")
    dec = _req(raw, "decoding", dict)
    try:
        decoding = Decoding(float(dec["temperature"]), int(dec["num_predict"]), int(dec["num_ctx"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigError(f"decoding invalid: {exc}") from None
    retries = raw.get("max_retries", 2)
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
        raise ConfigError("max_retries must be a non-negative int")
    hz = raw.get("memory_sample_hz", 10)
    if not isinstance(hz, (int, float)) or hz <= 0:
        raise ConfigError("memory_sample_hz must be positive")
    design = raw.get("design", "matrix")
    if design not in ("matrix", "cold_warm"):
        raise ConfigError("design must be matrix or cold_warm")
    cold_warm = _parse_cold_warm(raw, subset, reps, retries) if design == "cold_warm" else None
    if design == "matrix" and "cold_warm" in raw:
        raise ConfigError("a cold_warm block needs design cold_warm")
    return RunConfig(
        raw=raw,
        exp_id=exp_id,
        mode=mode,
        backend=backend,
        arms=tuple(arms),
        items_path=_req(items, "path", str, "items"),
        items_synthetic=bool(items.get("synthetic", False)),
        subset_size=subset,
        subset_seed=int(items.get("subset_seed", 20261124)),
        template=template,
        repetitions=reps,
        runtime_seeds=tuple(seeds),
        order_seed_base=int(raw.get("order_seed_base", 1000)),
        decoding=decoding,
        max_retries=retries,
        warmup=bool(raw.get("warmup", True)),
        memory_sample_hz=float(hz),
        process_match=str(raw.get("process_match", "ollama")),
        items_source_sha256=src_sha,
        subset_ids_path=ids_path,
        design=design,
        cold_warm=cold_warm,
    )


def _pos_num(d: dict, key: str) -> float:
    v = d.get(key)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
        raise ConfigError(f"cold_warm.{key} must be a positive number")
    return float(v)


def _parse_cold_warm(raw: dict, subset, reps: int, retries: int) -> ColdWarm:
    """Validate the cold/warm design against the frozen EXP-002 constraints:
    one fixed prompt (subset of 1), one runtime seed, no discarded warm-up and
    no retries (a retried cold request would no longer be cold)."""
    cw = _req(raw, "cold_warm", dict)
    if subset != 1:
        raise ConfigError("cold_warm needs exactly one fixed prompt (items.subset_size = 1)")
    if reps != 1:
        raise ConfigError("cold_warm needs repetitions = 1 (one runtime seed)")
    if raw.get("warmup", True) is not False:
        raise ConfigError("cold_warm needs warmup = false (the trial sequence defines every request)")
    if retries != 0:
        raise ConfigError("cold_warm needs max_retries = 0 (a retry changes the start state)")
    n = _req(cw, "trials_per_state", int, "cold_warm")
    if n < 1:
        raise ConfigError("cold_warm.trials_per_state must be >= 1")
    return ColdWarm(
        trials_per_state=n,
        arm_order_seed=_req(cw, "arm_order_seed", int, "cold_warm"),
        unload_confirm_timeout_s=_pos_num(cw, "unload_confirm_timeout_s"),
        unload_poll_s=_pos_num(cw, "unload_poll_s"),
        wall_cap_s=_pos_num(cw, "wall_cap_s"),
    )


def load_config(path: str | Path) -> RunConfig:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path}: invalid JSON ({exc.msg})") from None
    return parse_config(raw)


def frozen_protocol_hash(repo: Path, exp_id: str) -> str | None:
    """Return the recorded protocol hash if the experiment is frozen and the file matches it.

    Frozen means: the registry row has a 64-hex ``protocol_hash`` and the
    SHA-256 of ``protocol_path`` equals it. Anything else returns None.
    """
    reg = repo / "research" / "experiment_registry.csv"
    if not reg.exists():
        return None
    with open(reg, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("exp_id") != exp_id:
                continue
            h = (row.get("protocol_hash") or "").strip().lower()
            if not re.fullmatch(r"[0-9a-f]{64}", h):
                return None
            proto = repo / (row.get("protocol_path") or "")
            if not proto.is_file():
                return None
            actual = hashlib.sha256(proto.read_bytes()).hexdigest()
            return h if actual == h else None
    return None


FREEZE_RECORD = Path("research") / "freeze.json"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_freeze_record(repo: Path) -> dict | None:
    p = repo / FREEZE_RECORD
    if not p.is_file():
        return None
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return rec if isinstance(rec, dict) else None


def require_frozen_if_confirmatory(cfg: RunConfig, repo: Path) -> str | None:
    """Fail closed unless every frozen artifact still matches the freeze record.

    A confirmatory run needs: (1) a registry row whose 64-hex protocol hash
    equals the SHA-256 of the experiment protocol; (2) ``research/freeze.json``
    whose main-protocol hash equals the SHA-256 of ``research/protocol.md``;
    (3) an entry for the experiment with the same protocol hash; and (4) the
    canonical SHA-256 of the requested config equal to the frozen config hash.
    Any edit to a protocol or config after the freeze makes the run refused.
    """
    if cfg.mode != "confirmatory":
        return None
    h = frozen_protocol_hash(repo, cfg.exp_id)
    if h is None:
        raise ProtocolNotFrozen(
            f"{cfg.exp_id}: protocol is not frozen (no matching SHA-256 in the registry). "
            "Confirmatory runs are refused until the owner freezes it (G-FREEZE)."
        )
    rec = load_freeze_record(repo)
    if rec is None:
        raise ProtocolNotFrozen(f"{cfg.exp_id}: no freeze record at {FREEZE_RECORD} (G-FREEZE)")
    main = rec.get("main_protocol") or {}
    main_path = repo / str(main.get("path", "research/protocol.md"))
    if not main_path.is_file() or _sha256_file(main_path) != main.get("sha256"):
        raise ProtocolNotFrozen(f"{cfg.exp_id}: research/protocol.md differs from the frozen version")
    entry = (rec.get("experiments") or {}).get(cfg.exp_id)
    if not isinstance(entry, dict) or entry.get("protocol_sha256") != h:
        raise ProtocolNotFrozen(f"{cfg.exp_id}: not listed in the freeze record with this protocol hash")
    if entry.get("config_canonical_sha256") != cfg.sha256:
        raise ProtocolNotFrozen(
            f"{cfg.exp_id}: config differs from the frozen config "
            f"(canonical SHA-256 {cfg.sha256}, frozen {entry.get('config_canonical_sha256')})"
        )
    return h
