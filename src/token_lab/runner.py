# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Experiment runner: config to validated result file plus run manifest.

Order design (protocol section 6): in repetition r, arm order and item order
are permutations drawn from ``default_rng(order_seed_base + r)``; the item
order is identical for every arm in that repetition (common random numbers).
One discarded warm-up request precedes each arm block when ``warmup`` is set.

The matrix design enforces the frozen block exclusion and stopping rules of
research/protocol.md section 9 (quoted with the code below; DL-017), and
``execute_block_repeat`` re-executes named blocks of an existing run into a
new run id, which ``combine_repeat`` merges for the frozen analysis.

EXP-002 uses the ``cold_warm`` design instead (``run_cold_warm``).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from .config import RunConfig, require_frozen_if_confirmatory
from .hardware import (MemorySampler, git_state, harness_peak_rss_bytes, host_info, name_matcher, now_utc,
                       package_versions, power_state, swap_used_bytes)
from .items import Item, load_items, seeded_subset
from .prompts import render
from .runtime import Backend, BackendError, RuntimeUnavailable, make_backend, model_fingerprint
from .schema import SCHEMA_VERSION, export_result, import_result
from .scoring import extract, is_correct


def schedule(n_arms: int, n_items: int, repetition: int, order_seed_base: int) -> tuple[list[int], list[int]]:
    """Return (arm order, item order) for one repetition."""
    if n_arms < 1 or n_items < 1:
        raise ValueError("need at least one arm and one item")
    rng = np.random.default_rng(order_seed_base + repetition)
    arm_order = [int(i) for i in rng.permutation(n_arms)]
    item_order = [int(i) for i in rng.permutation(n_items)]
    return arm_order, item_order


def next_run_id(out_root: Path, exp_id: str) -> str:
    pat = re.compile(rf"^RUN-{re.escape(exp_id)}-(\d{{4}})$")
    nums = [int(m.group(1)) for p in out_root.glob(f"RUN-{exp_id}-*") if (m := pat.match(p.name))]
    return f"RUN-{exp_id}-{(max(nums) + 1 if nums else 1):04d}"


def _request(backend: Backend, model: str, prompt: str, cfg: RunConfig, seed: int):
    """Call with up to ``max_retries`` retries. Returns (generation or None, error, attempts)."""
    last = None
    for attempt in range(1, cfg.max_retries + 2):
        try:
            return backend.generate(model, prompt, cfg.decoding, seed), None, attempt
        except RuntimeUnavailable:
            raise
        except BackendError as exc:
            last = f"{type(exc).__name__}: {exc}"
    return None, last, cfg.max_retries + 1


def _safe_loaded(backend: Backend) -> list | None:
    try:
        return [{"name": m.get("name"), "size": m.get("size"), "size_vram": m.get("size_vram")}
                for m in backend.loaded_models()]
    except BackendError:
        return None


def verify_items(cfg: RunConfig, items_sha: str, items: list[Item], repo: Path) -> None:
    """Fail closed if the item file or the drawn subset differs from what was frozen."""
    if cfg.items_source_sha256 is not None and items_sha != cfg.items_source_sha256:
        raise ValueError(f"item file SHA-256 {items_sha} differs from the frozen {cfg.items_source_sha256}")
    if cfg.subset_ids_path is not None:
        p = Path(cfg.subset_ids_path)
        p = p if p.is_absolute() else repo / p
        frozen = json.loads(p.read_text(encoding="utf-8"))
        ids = frozen["item_ids"] if isinstance(frozen, dict) else frozen
        if sorted(ids) != sorted(it.item_id for it in items):
            raise ValueError(f"drawn subset differs from the frozen item IDs in {cfg.subset_ids_path}")


def arm_fingerprints(cfg: RunConfig, backend: Backend) -> dict:
    """Per-arm hashes of chat template, system prompt, parameters and Modelfile.

    A confirmatory run aborts before any request if a model cannot be
    described; an exploratory run records the error instead.
    """
    out = {}
    for arm in cfg.arms:
        try:
            out[arm.arm_id] = {"model": arm.model, **model_fingerprint(backend.show(arm.model))}
        except RuntimeUnavailable:
            raise
        except BackendError as exc:
            if cfg.mode == "confirmatory":
                raise
            out[arm.arm_id] = {"model": arm.model, "error": f"{type(exc).__name__}: {exc}"}
    return out


def _record(cfg: RunConfig, arm, item: Item, rp, rep: int, pos: int, seed: int, gen, err, attempts) -> dict:
    text = gen.text if gen else None
    ex = extract(text, rp.display_to_source) if text is not None else None
    s = ex.strict if ex else None
    l = ex.lenient if ex else None  # noqa: E741
    c = gen.counters if gen else None
    return {
        "arm": arm.arm_id, "model": arm.model, "item_id": item.item_id,
        "repetition": rep, "order_index": pos, "runtime_seed": seed,
        "template": cfg.template, "response": text,
        "extracted_strict": s, "extracted_lenient": l,
        "answer_key": item.answer_key, "n_choices": len(item.labels),
        "correct_strict": is_correct(s, item.answer_key),
        "correct_lenient": is_correct(l, item.answer_key),
        "error": err, "attempts": attempts,
        "latency_ms": gen.latency_ms if gen else None,
        "ttft_ms": gen.ttft_ms if gen else None,
        "stream_chunks": gen.stream_chunks if gen else None,
        "prompt_eval_count": c.prompt_eval_count if c else None,
        "eval_count": c.eval_count if c else None,
        "prompt_eval_duration_ns": c.prompt_eval_duration_ns if c else None,
        "eval_duration_ns": c.eval_duration_ns if c else None,
        "load_duration_ns": c.load_duration_ns if c else None,
        "total_duration_ns": c.total_duration_ns if c else None,
    }


# ---- frozen block rules (research/protocol.md section 9, v1.0, frozen 2026-11-24) ----
#
# Implemented on the owner's instruction of 2026-11-26 (follow-up answers in
# labs/_shared/owner-approvals-2026-11-26.md; DL-017), closing DL-011 gap 2 for
# the matrix design. The frozen wording, quoted verbatim:
#
#   Controls: "no other Ollama client active and no foreign model loaded
#   (`ollama ps` checked before and after each arm)".
#   Exclusion: "A run (arm x repetition block) is excluded and repeated once if:
#   a foreign model was loaded, the machine was on battery, swap grew by more
#   than 512 MiB, or the runtime version changed. Exclusions are logged with the
#   reason and never silently dropped."
#   Stopping: "Wall-clock cap of 4 hours per experiment. If reached, the run
#   stops, the completed blocks are kept and reported, and the experiment is
#   marked incomplete."
#   Stopping: "Abort on any sign of memory exhaustion (runner killed or swap
#   growth above 2 GiB); report as a failure."
#
# Operational reading (recorded in DL-017, no frozen value changed):
# - "foreign model": a model listed by /api/ps before or after the block that is
#   not one of the config's arm models;
# - "on battery": the power source read before or after the block is battery;
# - "swap grew": the block's swap delta (swap used at block end minus at block
#   start, the protocol section 5 "Swap delta" metric) above 512 MiB;
# - "runtime version changed": /api/version after the block differs from the
#   version read at the start of the run;
# - "swap growth above 2 GiB": swap used minus swap used at block start above
#   2,048 MiB, read before every request, by the sampler, and at block end;
# - "runner killed": the runtime becomes unreachable during the run, or a
#   request error names a terminated or killed runner process;
# - an excluded block is repeated once, immediately, with the same seed, item
#   order and warm-up; a repeat that again meets a criterion is recorded and not
#   repeated again (the block is then missing and the run is incomplete);
# - excluded, aborted and cap-interrupted blocks keep their records in
#   ``excluded_records`` and ``excluded_blocks``; ``records`` and ``blocks``
#   hold only the blocks kept for the analysis.

SWAP_EXCLUDE_MIB = 512.0
SWAP_ABORT_MIB = 2048.0
WALL_CAP_S = 4 * 3600.0
RULES_VERSION = "protocol-v1.0-section-9"
RULES_QUOTED = {
    "controls": "no other Ollama client active and no foreign model loaded (`ollama ps` checked before and after each arm)",
    "exclusion": ("A run (arm x repetition block) is excluded and repeated once if: a foreign model was loaded, "
                  "the machine was on battery, swap grew by more than 512 MiB, or the runtime version changed. "
                  "Exclusions are logged with the reason and never silently dropped."),
    "wall_cap": ("Wall-clock cap of 4 hours per experiment. If reached, the run stops, the completed blocks are "
                 "kept and reported, and the experiment is marked incomplete."),
    "memory_abort": ("Abort on any sign of memory exhaustion (runner killed or swap growth above 2 GiB); "
                     "report as a failure."),
}
_KILLED = re.compile(r"runner process (has terminated|no longer running)|signal: killed|exit status 137", re.I)


@dataclass
class Probes:
    """Machine readings used by the block rules (injectable for tests)."""

    power_source: Callable[[], str | None] = field(default=lambda: power_state()["source"])
    swap_used_bytes: Callable[[], int] = swap_used_bytes
    clock: Callable[[], float] = time.perf_counter


def default_probes() -> Probes:
    return Probes()


class _Abort(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def block_criteria(block: dict, arm_models: set[str], run_version: str | None) -> list[str]:
    """Exclusion criteria (frozen wording above) that ``block`` meets, from its record."""
    reasons = []
    names = {m.get("name") for m in (block.get("loaded_before") or []) + (block.get("loaded_after") or [])}
    foreign = sorted(n for n in names if isinstance(n, str) and n not in arm_models)
    if foreign:
        reasons.append(f"foreign model loaded: {', '.join(foreign)}")
    power = [block.get("power_before"), block.get("power_after")]
    if "battery" in power:
        reasons.append("machine on battery")
    sw = block["memory"].get("swap_delta_mib", 0.0)
    if sw > SWAP_EXCLUDE_MIB:
        reasons.append(f"swap grew by {sw:.1f} MiB (more than {SWAP_EXCLUDE_MIB:.0f} MiB)")
    if "runtime_version_after" in block and block["runtime_version_after"] != run_version:
        reasons.append(f"runtime version changed: {run_version} -> {block['runtime_version_after']}")
    return reasons


def stop_criterion(block: dict) -> str | None:
    """The memory-exhaustion stopping criterion, from a block record (swap part)."""
    mem = block["memory"]
    growth = max(mem.get("swap_delta_mib", 0.0), mem.get("peak_swap_growth_mib", 0.0))
    if growth > SWAP_ABORT_MIB:
        return f"swap growth {growth:.1f} MiB above 2 GiB (memory exhaustion)"
    return None


def planned_blocks(cfg: RunConfig, n_items: int) -> list[tuple[int, int]]:
    """(repetition, arm index) of every planned block, in execution order; block
    ``k`` (1-based) is element ``k - 1``."""
    out = []
    for rep in range(cfg.repetitions):
        arm_order, _ = schedule(len(cfg.arms), n_items, rep, cfg.order_seed_base)
        out += [(rep, ai) for ai in arm_order]
    return out


def _run_block(cfg: RunConfig, backend: Backend, items: list[Item], rep: int, ai: int, block_index: int,
               attempt: int, run_version: str | None, probes: Probes, t_start: float, cap_s: float) -> dict:
    """Run one arm x repetition block; returns {block, records, failures, status, reasons}.

    status: "included", "excluded", "cap" (cap reached inside the block) or
    "aborted" (memory-exhaustion stopping rule).
    """
    seed = cfg.runtime_seeds[rep]
    _, item_order = schedule(len(cfg.arms), len(items), rep, cfg.order_seed_base)
    arm = cfg.arms[ai]
    recs: list[dict] = []
    fails: list[dict] = []
    status, abort_reason = "included", None
    power_before = probes.power_source()
    loaded_before = _safe_loaded(backend)
    block_start = now_utc()
    tb = time.perf_counter()
    with MemorySampler(name_matcher(cfg.process_match), cfg.memory_sample_hz,
                       swap_reader=probes.swap_used_bytes) as mem:
        try:
            def guard() -> bool:
                if probes.clock() - t_start >= cap_s:
                    return False
                if mem.swap_growth_bytes() / 2**20 > SWAP_ABORT_MIB:
                    raise _Abort(f"swap growth {mem.swap_growth_bytes() / 2**20:.1f} MiB above 2 GiB "
                                 "(memory exhaustion)")
                return True

            if cfg.warmup:
                if not guard():
                    status = "cap"
                else:
                    _gen, err, _ = _request(backend, arm.model, render(items[item_order[0]], cfg.template).text,
                                            cfg, seed)
                    if err:
                        fails.append({"arm": arm.arm_id, "repetition": rep, "item_id": None,
                                      "stage": "warmup", "error": err})
                        if _KILLED.search(err):
                            raise _Abort(f"runner killed: {err}")
            if status != "cap":
                for pos, ii in enumerate(item_order):
                    if not guard():
                        status = "cap"
                        break
                    item = items[ii]
                    rp = render(item, cfg.template)
                    gen, err, attempts = _request(backend, arm.model, rp.text, cfg, seed)
                    recs.append(_record(cfg, arm, item, rp, rep, pos, seed, gen, err, attempts))
                    if err:
                        fails.append({"arm": arm.arm_id, "repetition": rep, "item_id": item.item_id,
                                      "stage": "request", "error": err})
                        if _KILLED.search(err):
                            raise _Abort(f"runner killed: {err}")
        except RuntimeUnavailable as exc:
            status, abort_reason = "aborted", f"runner killed or runtime unreachable: {exc}"
        except _Abort as exc:
            status, abort_reason = "aborted", exc.reason
    wall_s = time.perf_counter() - tb  # the rule readings below are not part of the block's wall time
    try:
        version_after = backend.version()
    except BackendError as exc:
        version_after = None
        if status != "aborted":
            status, abort_reason = "aborted", f"runner killed or runtime unreachable: {exc}"
    block = {
        "arm": arm.arm_id, "repetition": rep, "start_utc": block_start,
        "wall_s": wall_s, "memory": mem.summary(),
        "loaded_before": loaded_before, "loaded_after": _safe_loaded(backend),
        "block_index": block_index, "attempt": attempt,
        "power_before": power_before, "power_after": probes.power_source(),
        "runtime_version_after": version_after,
    }
    reasons: list[str] = []
    if status == "included":
        stop = stop_criterion(block)
        if stop:
            status, abort_reason = "aborted", stop
    if status in ("included", "aborted"):
        reasons = block_criteria(block, {a.model for a in cfg.arms}, run_version)
        if status == "included" and reasons:
            status = "excluded"
    block["status"] = status
    block["exclusion_reasons"] = reasons
    if abort_reason:
        block["abort_reason"] = abort_reason
    return {"block": block, "records": recs, "failures": fails, "status": status, "reasons": reasons,
            "abort_reason": abort_reason}


def run_blocks(cfg: RunConfig, backend: Backend, items: list[Item], targets: list[int], run_version: str | None,
               probes: Probes, t_start: float, cap_s: float, repeat_allowed: bool) -> dict:
    """Run the planned blocks ``targets`` (1-based indices) under the frozen rules.

    With ``repeat_allowed`` an excluded block is repeated once at once; without
    it (block-repeat mode, where the one repeat is the block itself) an
    excluded block is recorded and not repeated.
    """
    plan = planned_blocks(cfg, len(items))
    out = {"records": [], "blocks": [], "excluded_records": [], "excluded_blocks": [], "failures": [],
           "exclusions": [], "status": "complete", "status_reason": None}
    for k in targets:
        rep, ai = plan[k - 1]
        attempts = 2 if repeat_allowed else 1
        for attempt in range(1, attempts + 1):
            if probes.clock() - t_start >= cap_s:
                out["status"] = "incomplete"
                out["status_reason"] = (f"wall-clock cap of {cap_s:.0f} s reached before block {k}; "
                                        "remaining blocks not run")
                return out
            res = _run_block(cfg, backend, items, rep, ai, k, attempt, run_version, probes, t_start, cap_s)
            out["failures"] += res["failures"]
            b = res["block"]
            if res["status"] == "included":
                out["records"] += res["records"]
                out["blocks"].append(b)
                break
            out["excluded_records"] += [dict(r, block_index=k, attempt=attempt) for r in res["records"]]
            out["excluded_blocks"].append(b)
            if res["status"] == "aborted":
                out["exclusions"].append({"block_index": k, "arm": b["arm"], "repetition": rep, "attempt": attempt,
                                          "outcome": "aborted", "reasons": [res["abort_reason"]] + res["reasons"]})
                out["failures"].append({"arm": b["arm"], "repetition": rep, "item_id": None,
                                        "stage": "stopping_rule", "error": res["abort_reason"]})
                out["status"] = "failure"
                out["status_reason"] = (f"stopping rule (memory exhaustion) at block {k}: {res['abort_reason']}; "
                                        "reported as a failure")
                return out
            if res["status"] == "cap":
                out["exclusions"].append({"block_index": k, "arm": b["arm"], "repetition": rep, "attempt": attempt,
                                          "outcome": "interrupted by the wall-clock cap", "reasons": []})
                out["failures"].append({"arm": b["arm"], "repetition": rep, "item_id": None,
                                        "stage": "stopping_rule", "error": f"wall-clock cap {cap_s:.0f} s reached"})
                out["status"] = "incomplete"
                out["status_reason"] = f"wall-clock cap of {cap_s:.0f} s reached during block {k}"
                return out
            last = attempt == attempts
            out["exclusions"].append({"block_index": k, "arm": b["arm"], "repetition": rep, "attempt": attempt,
                                      "outcome": "excluded, not repeated again" if last else "excluded, repeated once",
                                      "reasons": res["reasons"]})
            out["failures"].append({"arm": b["arm"], "repetition": rep, "item_id": None, "stage": "block_exclusion",
                                    "error": "; ".join(res["reasons"])})
            if last:
                out["status"] = "incomplete"
                out["status_reason"] = (f"block {k} met an exclusion criterion again after its one repeat; "
                                        "no further repeat (protocol section 9)")
    return out


def run_matrix(cfg: RunConfig, backend: Backend, items: list[Item], run_version: str | None = None,
               probes: Probes | None = None, t_start: float | None = None) -> dict:
    """EXP-001/EXP-003 matrix: repetitions x arms x items (module docstring), with
    the frozen block rules enforced."""
    probes = probes or default_probes()
    t_start = probes.clock() if t_start is None else t_start
    n = len(planned_blocks(cfg, len(items)))
    return run_blocks(cfg, backend, items, list(range(1, n + 1)), run_version, probes, t_start, WALL_CAP_S,
                      repeat_allowed=True)


def cold_warm_sequence(n_arms: int, trials_per_state: int, arm_order_seed: int) -> tuple[list[int], list[str]]:
    """Arm order (permutation from ``default_rng(arm_order_seed)``) and the fixed
    per-arm trial order: cold, warm, cold, warm, ... (EXP-002 protocol item 12)."""
    if n_arms < 1 or trials_per_state < 1:
        raise ValueError("need at least one arm and one trial per state")
    arm_order = [int(i) for i in np.random.default_rng(arm_order_seed).permutation(n_arms)]
    return arm_order, ["cold", "warm"] * trials_per_state


def confirm_unloaded(backend: Backend, timeout_s: float, poll_s: float) -> tuple[list | None, int]:
    """Poll ``/api/ps`` until no model is loaded or ``timeout_s`` passes.
    Returns (last loaded list or None if unreadable, number of polls)."""
    deadline = time.perf_counter() + timeout_s
    polls = 0
    while True:
        loaded = _safe_loaded(backend)
        polls += 1
        if loaded == [] or time.perf_counter() >= deadline:
            return loaded, polls
        time.sleep(poll_s)


def run_cold_warm(cfg: RunConfig, backend: Backend, item: Item, t_start: float) -> tuple[list, list, list, dict]:
    """EXP-002 cold/warm mode, exactly as the frozen EXP-002 protocol defines it.

    One fixed prompt (``item`` rendered with ``cfg.template``), decoding and
    runtime seed from the config. Per arm, in the seeded arm order, the trials
    alternate cold, warm, starting cold. A cold trial unloads the arm's model,
    and any other model ``/api/ps`` lists, with ``keep_alive: 0``, confirms with ``/api/ps`` that no model is loaded,
    then sends the request; it is marked invalid (``state_valid`` false, kept
    in the records) if ``/api/ps`` still lists any model or cannot be read just
    before the request (items 10 and 17). A warm trial is sent immediately
    after the preceding request to the same arm completed; it is marked
    invalid if that request failed. No retries and no discarded warm-up.
    Stopping rule (item 18): no new trial starts once ``wall_cap_s`` has
    elapsed since the run started; the stop is recorded as a failure.
    """
    cw = cfg.cold_warm
    assert cw is not None
    seed = cfg.runtime_seeds[0]
    rp = render(item, cfg.template)
    arm_order, states = cold_warm_sequence(len(cfg.arms), cw.trials_per_state, cw.arm_order_seed)
    records: list[dict] = []
    blocks: list[dict] = []
    failures: list[dict] = []
    stopped = False
    for ai in arm_order:
        if stopped:
            break
        arm = cfg.arms[ai]
        loaded_before = _safe_loaded(backend)
        block_start = now_utc()
        tb = time.perf_counter()
        prev_ok = False
        with MemorySampler(name_matcher(cfg.process_match), cfg.memory_sample_hz) as mem:
            for pos, state in enumerate(states):
                if time.perf_counter() - t_start >= cw.wall_cap_s:
                    stopped = True
                    failures.append({"arm": arm.arm_id, "repetition": 0, "item_id": item.item_id,
                                     "stage": "stopping_rule",
                                     "error": f"wall-clock cap {cw.wall_cap_s} s reached; remaining trials not run"})
                    break
                check: dict
                if state == "cold":
                    unload_error = None
                    # unload this arm's model and any other listed model (the protocol
                    # requires that no model is loaded, not only this arm's)
                    targets = [arm.model] + [m["name"] for m in (_safe_loaded(backend) or [])
                                             if isinstance(m.get("name"), str) and m["name"] != arm.model]
                    for name in targets:
                        try:
                            backend.unload(name)
                        except RuntimeUnavailable:
                            raise
                        except BackendError as exc:
                            unload_error = f"{type(exc).__name__}: {exc}"
                    confirmed, polls = confirm_unloaded(backend, cw.unload_confirm_timeout_s, cw.unload_poll_s)
                    loaded_now = _safe_loaded(backend)  # immediately before the request
                    valid = unload_error is None and loaded_now == []
                    check = {"unload_error": unload_error, "unloaded": targets, "confirm_polls": polls,
                             "loaded_at_confirm": confirmed, "loaded_before_request": loaded_now}
                    if not valid:
                        failures.append({"arm": arm.arm_id, "repetition": 0, "item_id": item.item_id,
                                         "stage": "cold_check", "trial_index": pos,
                                         "error": unload_error or f"models loaded before the cold request: {loaded_now}"})
                else:
                    valid = prev_ok
                    check = {"previous_request_completed": prev_ok}
                gen, err, attempts = _request(backend, arm.model, rp.text, cfg, seed)
                prev_ok = err is None
                rec = _record(cfg, arm, item, rp, 0, pos, seed, gen, err, attempts)
                rec.update({"start_state": state, "trial_index": pos // 2,
                            "state_valid": bool(valid), "state_check": check})
                records.append(rec)
                if err:
                    failures.append({"arm": arm.arm_id, "repetition": 0, "item_id": item.item_id,
                                     "stage": "request", "trial_index": pos, "error": err})
        blocks.append({
            "arm": arm.arm_id, "repetition": 0, "start_utc": block_start,
            "wall_s": time.perf_counter() - tb, "memory": mem.summary(),
            "loaded_before": loaded_before, "loaded_after": _safe_loaded(backend),
        })
    extra = {"cold_warm": {"arm_order": [cfg.arms[i].arm_id for i in arm_order],
                           "trial_states": states, "fixed_item_id": item.item_id,
                           "trials_per_state": cw.trials_per_state, "arm_order_seed": cw.arm_order_seed,
                           "wall_cap_s": cw.wall_cap_s, "stopped_by_wall_cap": stopped,
                           "n_invalid_state": sum(1 for r in records if not r["state_valid"])}}
    return records, blocks, failures, extra


def _prepare(cfg: RunConfig, repo: Path, backend: Backend | None):
    protocol_hash = require_frozen_if_confirmatory(cfg, repo)
    backend = backend or make_backend(cfg.backend)
    runtime_version = backend.version()  # raises RuntimeUnavailable if down
    items_path = (repo / cfg.items_path) if not Path(cfg.items_path).is_absolute() else Path(cfg.items_path)
    all_items, items_sha = load_items(items_path)
    items: list[Item] = seeded_subset(all_items, cfg.subset_size, cfg.subset_seed)
    verify_items(cfg, items_sha, items, repo)
    return protocol_hash, backend, runtime_version, items, items_sha


def _rules_manifest(res: dict, cap_s: float) -> dict:
    return {"version": RULES_VERSION, "quoted": RULES_QUOTED,
            "thresholds": {"swap_exclude_mib": SWAP_EXCLUDE_MIB, "swap_abort_mib": SWAP_ABORT_MIB,
                           "wall_cap_s": cap_s},
            "status": res["status"], "status_reason": res["status_reason"], "exclusions": res["exclusions"],
            "n_excluded_blocks": len(res["excluded_blocks"]), "n_excluded_records": len(res["excluded_records"])}


def _write(cfg: RunConfig, repo: Path, backend: Backend, out_root: Path, run_id: str, protocol_hash: str | None,
           runtime_version, items, items_sha, fingerprints, start_utc, t_start, host_before, records, blocks,
           failures, extra: dict, top_extra: dict) -> tuple[dict, Path]:
    runtime_s = time.perf_counter() - t_start
    manifest = {
        "run_id": run_id, "exp_id": cfg.exp_id, "label": cfg.mode,
        "config_sha256": cfg.sha256, "protocol_sha256": protocol_hash,
        "seeds": {"runtime": list(cfg.runtime_seeds), "order_seed_base": cfg.order_seed_base,
                  "subset_seed": cfg.subset_seed},
        "git": git_state(repo), "packages": package_versions(),
        "host": {"before": host_before, "after": host_info()},
        "backend": {"name": backend.name, "simulated": backend.simulated, "runtime_version": runtime_version},
        "start_utc": start_utc, "end_utc": now_utc(), "runtime_s": runtime_s,
        "harness_peak_rss_mib": harness_peak_rss_bytes() / 2**20,
        "arm_runtime": fingerprints,
        "n_requests": len(records), "n_failures": len(failures),
        "schema_version": SCHEMA_VERSION, "design": cfg.design, **extra,
    }
    doc = {
        "schema_version": SCHEMA_VERSION, "kind": "token-lab-result", "label": cfg.mode,
        "exp_id": cfg.exp_id, "run_id": run_id, "config": cfg.raw, "config_sha256": cfg.sha256,
        "backend": {"name": backend.name, "simulated": backend.simulated, "runtime_version": runtime_version},
        "items_source": {"path": cfg.items_path, "sha256": items_sha, "n_items": len(items),
                         "synthetic": cfg.items_synthetic},
        "records": records, "blocks": blocks, "failures": failures, "manifest": manifest, **top_extra,
    }
    run_dir = out_root / run_id
    path = export_result(doc, run_dir / "result.json")
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "config.json").write_text(json.dumps(cfg.raw, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return doc, path


def execute(cfg: RunConfig, repo: Path, backend: Backend | None = None, out_root: Path | None = None,
            probes: Probes | None = None) -> tuple[dict, Path]:
    """Run ``cfg`` and export a validated result. Raises before any request if
    a confirmatory config is not frozen, or if the runtime is unreachable.
    A matrix run enforces the frozen block rules; its status ("complete",
    "incomplete" or "failure") is ``manifest["block_rules"]["status"]``."""
    protocol_hash, backend, runtime_version, items, items_sha = _prepare(cfg, repo, backend)
    fingerprints = arm_fingerprints(cfg, backend)
    probes = probes or default_probes()

    out_root = out_root or (repo / "results" / ("exploratory" if cfg.mode == "exploratory" else "confirmatory"))
    out_root.mkdir(parents=True, exist_ok=True)
    run_id = next_run_id(out_root, cfg.exp_id)

    start_utc = now_utc()
    t_start = time.perf_counter()
    host_before = host_info()
    extra: dict = {}
    top_extra: dict = {}
    if cfg.design == "cold_warm":
        records, blocks, failures, extra = run_cold_warm(cfg, backend, items[0], t_start)
    else:
        res = run_matrix(cfg, backend, items, runtime_version, probes, probes.clock())
        records, blocks, failures = res["records"], res["blocks"], res["failures"]
        extra = {"block_rules": _rules_manifest(res, WALL_CAP_S)}
        top_extra = {"excluded_records": res["excluded_records"], "excluded_blocks": res["excluded_blocks"]}
    return _write(cfg, repo, backend, out_root, run_id, protocol_hash, runtime_version, items, items_sha,
                  fingerprints, start_utc, t_start, host_before, records, blocks, failures, extra, top_extra)


# ---- block-repeat mode (owner instruction 2026-11-26, DL-017) ----

def source_block_check(source: dict) -> list[dict]:
    """Every block of an existing matrix run against the frozen criteria, from its
    records. Blocks are numbered 1.. in execution order. A run made before the
    rules were enforced has no per-block power reading; the run's power readings
    before and after are used for every block."""
    arm_models = {a["model"] for a in source["config"]["arms"]}
    host = source["manifest"]["host"]
    run_power = [host["before"].get("power", {}).get("source"), host["after"].get("power", {}).get("source")]
    version = source["backend"]["runtime_version"]
    out = []
    for pos, b in enumerate(source["blocks"], start=1):
        bb = dict(b)
        bb.setdefault("power_before", run_power[0])
        bb.setdefault("power_after", run_power[1])
        out.append({"block_index": b.get("block_index", pos), "arm": b["arm"], "repetition": b["repetition"],
                    "exclusion": block_criteria(bb, arm_models, version), "stopping": stop_criterion(bb)})
    return out


def execute_block_repeat(cfg: RunConfig, repo: Path, source_dir: Path, block_indices: list[int],
                         backend: Backend | None = None, out_root: Path | None = None,
                         probes: Probes | None = None) -> tuple[dict, Path]:
    """Re-execute the named blocks of an existing matrix run (its own result is
    never modified) with their original runtime seed, item order and warm-up, and
    write a new run that records which blocks of the source run it replaces.

    Refuses (ValueError, before any request) if the source does not belong to
    this config, if a named block does not exist, if the source run already
    enforced the rules (its repeats are then spent), or if a named block meets no
    frozen exclusion criterion in its own records (no repeat by choice). Each
    named block runs once under the frozen rules; a block that meets a criterion
    again is recorded and not repeated again. The wall-clock cap counts the
    source run's own duration ("4 hours per experiment").
    """
    if cfg.design != "matrix":
        raise ValueError("block repeat applies to the matrix design only")
    src_path = Path(source_dir) / "result.json"
    raw = src_path.read_bytes()
    source = import_result(src_path)
    if source["config_sha256"] != cfg.sha256 or source["exp_id"] != cfg.exp_id:
        raise ValueError("the source run was made from a different config")
    if source["label"] != cfg.mode:
        raise ValueError("the source run has a different label")
    if "block_rules" in source["manifest"]:
        raise ValueError("the source run enforced the block rules; its one repeat per block is already spent")
    checks = {c["block_index"]: c for c in source_block_check(source)}
    targets = sorted(set(int(k) for k in block_indices))
    if not targets:
        raise ValueError("name at least one block")
    for k in targets:
        if k not in checks:
            raise ValueError(f"block {k} does not exist in {source['run_id']}")
        if not checks[k]["exclusion"]:
            raise ValueError(f"block {k} of {source['run_id']} meets no frozen exclusion criterion; not repeated")

    protocol_hash, backend, runtime_version, items, items_sha = _prepare(cfg, repo, backend)
    plan = planned_blocks(cfg, len(items))
    for k in targets:
        rep, ai = plan[k - 1]
        c = checks[k]
        if (c["arm"], c["repetition"]) != (cfg.arms[ai].arm_id, rep):
            raise ValueError(f"block {k} of the source is {c['arm']} rep {c['repetition']}, "
                             f"the schedule gives {cfg.arms[ai].arm_id} rep {rep}")
    fingerprints = arm_fingerprints(cfg, backend)
    probes = probes or default_probes()
    out_root = out_root or Path(source_dir).parent
    out_root.mkdir(parents=True, exist_ok=True)
    run_id = next_run_id(out_root, cfg.exp_id)

    start_utc = now_utc()
    t_start = time.perf_counter()
    host_before = host_info()
    cap_s = max(0.0, WALL_CAP_S - float(source["manifest"]["runtime_s"]))
    res = run_blocks(cfg, backend, items, targets, runtime_version, probes, probes.clock(), cap_s,
                     repeat_allowed=False)
    repeat_of = {
        "source_run_id": source["run_id"], "source_result": str(src_path.relative_to(repo)) if
        src_path.is_relative_to(repo) else str(src_path),
        "source_result_sha256": hashlib.sha256(raw).hexdigest(),
        "source_runtime_version": source["backend"]["runtime_version"],
        "replaced_blocks": [{"block_index": k, "arm": checks[k]["arm"], "repetition": checks[k]["repetition"],
                             "source_exclusion": checks[k]["exclusion"], "source_stopping": checks[k]["stopping"]}
                            for k in targets],
        "note": "Each named block runs once with its original runtime seed, item order and warm-up; the source "
                "run is not modified. A repeated block that meets a criterion again is not repeated again.",
    }
    extra = {"block_rules": _rules_manifest(res, cap_s), "repeat_of": repeat_of}
    top_extra = {"excluded_records": res["excluded_records"], "excluded_blocks": res["excluded_blocks"]}
    return _write(cfg, repo, backend, out_root, run_id, protocol_hash, runtime_version, items, items_sha,
                  fingerprints, start_utc, t_start, host_before, res["records"], res["blocks"], res["failures"],
                  extra, top_extra)


def combine_repeat(source: dict, repeat: dict) -> dict:
    """Frozen-analysis input after a block repeat: the source run's records and
    blocks, with every replaced block's records and block entry removed and the
    repeat run's included blocks put in their place (protocol section 9: an
    excluded block is repeated once). Blocks are ordered by their planned index.
    The combined document carries the repeat run's id and a ``combination``
    record; the experiment status is taken from both runs' rule outcomes."""
    ro = repeat["manifest"].get("repeat_of")
    if not ro or ro["source_run_id"] != source["run_id"]:
        raise ValueError("the repeat run does not name this source run")
    if source["config_sha256"] != repeat["config_sha256"]:
        raise ValueError("source and repeat runs come from different configs")
    replaced = {(b["arm"], b["repetition"]) for b in ro["replaced_blocks"]}
    idx = {(b["arm"], b["repetition"]): b["block_index"] for b in ro["replaced_blocks"]}
    src_blocks = []
    for pos, b in enumerate(source["blocks"], start=1):
        if (b["arm"], b["repetition"]) not in replaced:
            src_blocks.append(dict(b, block_index=b.get("block_index", pos), origin=source["run_id"]))
    new_blocks = [dict(b, origin=repeat["run_id"]) for b in repeat["blocks"]]
    blocks = sorted(src_blocks + new_blocks, key=lambda b: b["block_index"])
    records = [r for r in source["records"] if (r["arm"], r["repetition"]) not in replaced] + list(repeat["records"])
    order = {(b["arm"], b["repetition"]): i for i, b in enumerate(blocks)}
    records.sort(key=lambda r: (order.get((r["arm"], r["repetition"]), 10**6), r["order_index"]))
    rules = repeat["manifest"]["block_rules"]
    n_planned = len(source["config"]["arms"]) * source["config"]["repetitions"]
    missing = sorted(idx[k] for k in replaced if k not in {(b["arm"], b["repetition"]) for b in repeat["blocks"]})
    status = rules["status"]
    if status == "complete" and (missing or len(blocks) != n_planned):
        status = "incomplete"
    sm, rm = source["manifest"], repeat["manifest"]
    manifest = dict(rm)
    manifest.update({
        # provenance spans both runs: source start to repeat end, summed runtime
        "start_utc": sm["start_utc"], "end_utc": rm["end_utc"],
        "runtime_s": float(sm["runtime_s"]) + float(rm["runtime_s"]),
        "host": {"before": sm["host"]["before"], "after": rm["host"]["after"]},
        "n_requests": len(records),
        "combination": {
            "source_run_id": source["run_id"], "repeat_run_id": repeat["run_id"],
            "source_result_sha256": ro["source_result_sha256"],
            "source_git": sm["git"], "repeat_git": rm["git"],
            "source_window": [sm["start_utc"], sm["end_utc"]], "repeat_window": [rm["start_utc"], rm["end_utc"]],
            "replaced_blocks": ro["replaced_blocks"], "blocks_missing": missing,
            "n_blocks": len(blocks), "n_planned_blocks": n_planned, "status": status,
            "rule": "the repeated blocks replace the excluded ones (protocol section 9)",
            "runtime_s_total": float(source["manifest"]["runtime_s"]) + float(repeat["manifest"]["runtime_s"]),
        },
    })
    doc = {k: v for k, v in repeat.items() if k not in ("records", "blocks", "manifest", "failures")}
    doc.update({"records": records, "blocks": blocks, "manifest": manifest,
                "failures": list(source["failures"]) + list(repeat["failures"])})
    return doc
