# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Experiment runner: config to validated result file plus run manifest.

Order design (protocol section 6): in repetition r, arm order and item order
are permutations drawn from ``default_rng(order_seed_base + r)``; the item
order is identical for every arm in that repetition (common random numbers).
One discarded warm-up request precedes each arm block when ``warmup`` is set.

EXP-002 uses the ``cold_warm`` design instead (``run_cold_warm``).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np

from .config import RunConfig, require_frozen_if_confirmatory
from .hardware import MemorySampler, git_state, harness_peak_rss_bytes, host_info, name_matcher, now_utc, package_versions
from .items import Item, load_items, seeded_subset
from .prompts import render
from .runtime import Backend, BackendError, RuntimeUnavailable, make_backend, model_fingerprint
from .schema import SCHEMA_VERSION, export_result
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


def run_matrix(cfg: RunConfig, backend: Backend, items: list[Item]) -> tuple[list, list, list]:
    """EXP-001/EXP-003 matrix: repetitions x arms x items (module docstring)."""
    records: list[dict] = []
    blocks: list[dict] = []
    failures: list[dict] = []
    for rep in range(cfg.repetitions):
        seed = cfg.runtime_seeds[rep]
        arm_order, item_order = schedule(len(cfg.arms), len(items), rep, cfg.order_seed_base)
        for ai in arm_order:
            arm = cfg.arms[ai]
            loaded_before = _safe_loaded(backend)
            block_start = now_utc()
            tb = time.perf_counter()
            with MemorySampler(name_matcher(cfg.process_match), cfg.memory_sample_hz) as mem:
                if cfg.warmup:
                    _gen, err, _ = _request(backend, arm.model, render(items[item_order[0]], cfg.template).text, cfg, seed)
                    if err:
                        failures.append({"arm": arm.arm_id, "repetition": rep, "item_id": None,
                                         "stage": "warmup", "error": err})
                for pos, ii in enumerate(item_order):
                    item = items[ii]
                    rp = render(item, cfg.template)
                    gen, err, attempts = _request(backend, arm.model, rp.text, cfg, seed)
                    records.append(_record(cfg, arm, item, rp, rep, pos, seed, gen, err, attempts))
                    if err:
                        failures.append({"arm": arm.arm_id, "repetition": rep, "item_id": item.item_id,
                                         "stage": "request", "error": err})
            blocks.append({
                "arm": arm.arm_id, "repetition": rep, "start_utc": block_start,
                "wall_s": time.perf_counter() - tb, "memory": mem.summary(),
                "loaded_before": loaded_before, "loaded_after": _safe_loaded(backend),
            })
    return records, blocks, failures


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


def execute(cfg: RunConfig, repo: Path, backend: Backend | None = None, out_root: Path | None = None) -> tuple[dict, Path]:
    """Run ``cfg`` and export a validated result. Raises before any request if
    a confirmatory config is not frozen, or if the runtime is unreachable."""
    protocol_hash = require_frozen_if_confirmatory(cfg, repo)
    backend = backend or make_backend(cfg.backend)
    runtime_version = backend.version()  # raises RuntimeUnavailable if down

    items_path = (repo / cfg.items_path) if not Path(cfg.items_path).is_absolute() else Path(cfg.items_path)
    all_items, items_sha = load_items(items_path)
    items: list[Item] = seeded_subset(all_items, cfg.subset_size, cfg.subset_seed)
    verify_items(cfg, items_sha, items, repo)
    fingerprints = arm_fingerprints(cfg, backend)

    label = cfg.mode
    out_root = out_root or (repo / "results" / ("exploratory" if label == "exploratory" else "confirmatory"))
    out_root.mkdir(parents=True, exist_ok=True)
    run_id = next_run_id(out_root, cfg.exp_id)

    start_utc = now_utc()
    t_start = time.perf_counter()
    host_before = host_info()
    extra: dict = {}
    if cfg.design == "cold_warm":
        records, blocks, failures, extra = run_cold_warm(cfg, backend, items[0], t_start)
    else:
        records, blocks, failures = run_matrix(cfg, backend, items)

    runtime_s = time.perf_counter() - t_start
    manifest = {
        "run_id": run_id, "exp_id": cfg.exp_id, "label": label,
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
        "schema_version": SCHEMA_VERSION, "kind": "token-lab-result", "label": label,
        "exp_id": cfg.exp_id, "run_id": run_id, "config": cfg.raw, "config_sha256": cfg.sha256,
        "backend": {"name": backend.name, "simulated": backend.simulated, "runtime_version": runtime_version},
        "items_source": {"path": cfg.items_path, "sha256": items_sha, "n_items": len(items),
                         "synthetic": cfg.items_synthetic},
        "records": records, "blocks": blocks, "failures": failures, "manifest": manifest,
    }
    run_dir = out_root / run_id
    path = export_result(doc, run_dir / "result.json")
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "config.json").write_text(json.dumps(cfg.raw, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return doc, path
