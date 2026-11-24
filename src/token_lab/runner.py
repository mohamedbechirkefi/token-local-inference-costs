# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Experiment runner: config to validated result file plus run manifest.

Order design (protocol section 6): in repetition r, arm order and item order
are permutations drawn from ``default_rng(order_seed_base + r)``; the item
order is identical for every arm in that repetition (common random numbers).
One discarded warm-up request precedes each arm block when ``warmup`` is set.
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
                    text = gen.text if gen else None
                    ex = extract(text, rp.display_to_source) if text is not None else None
                    s = ex.strict if ex else None
                    l = ex.lenient if ex else None
                    c = gen.counters if gen else None
                    rec = {
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
                    records.append(rec)
                    if err:
                        failures.append({"arm": arm.arm_id, "repetition": rep, "item_id": item.item_id,
                                         "stage": "request", "error": err})
            blocks.append({
                "arm": arm.arm_id, "repetition": rep, "start_utc": block_start,
                "wall_s": time.perf_counter() - tb, "memory": mem.summary(),
                "loaded_before": loaded_before, "loaded_after": _safe_loaded(backend),
            })

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
        "schema_version": SCHEMA_VERSION,
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
