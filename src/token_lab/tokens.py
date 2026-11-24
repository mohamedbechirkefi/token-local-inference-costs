# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Token counts and throughput from runtime counters (protocol section 5).

Counts are the runtime's own (model tokenizer) counters, never re-tokenised
here. Durations are in nanoseconds. Throughput is tokens per second.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

COUNTER_FIELDS = (
    "prompt_eval_count",
    "eval_count",
    "prompt_eval_duration",
    "eval_duration",
    "load_duration",
    "total_duration",
)


class CounterError(ValueError):
    """A runtime counter is present but invalid (negative or non-integer)."""


@dataclass(frozen=True)
class Counters:
    prompt_eval_count: int | None
    eval_count: int | None
    prompt_eval_duration_ns: int | None
    eval_duration_ns: int | None
    load_duration_ns: int | None
    total_duration_ns: int | None


def parse_counters(final_chunk: Mapping[str, object]) -> Counters:
    """Read counters from the final (``done: true``) chunk.

    Missing counters become None (the runtime omits ``prompt_eval_count`` when
    the prompt is fully cached). Present but invalid counters raise.
    """
    vals: dict[str, int | None] = {}
    for f in COUNTER_FIELDS:
        v = final_chunk.get(f)
        if v is None:
            vals[f] = None
            continue
        if isinstance(v, bool) or not isinstance(v, int):
            raise CounterError(f"{f} must be an integer, got {v!r}")
        if v < 0:
            raise CounterError(f"{f} must be non-negative, got {v}")
        vals[f] = v
    return Counters(
        vals["prompt_eval_count"],
        vals["eval_count"],
        vals["prompt_eval_duration"],
        vals["eval_duration"],
        vals["load_duration"],
        vals["total_duration"],
    )


def throughput_tps(count: int | None, duration_ns: int | None) -> float | None:
    """count / duration x 1e9 in tokens/s; None if either is missing or duration is 0."""
    if count is None or duration_ns is None:
        return None
    if count < 0 or duration_ns < 0:
        raise CounterError("count and duration must be non-negative")
    if duration_ns == 0:
        return None
    return count / duration_ns * 1e9


def ns_to_ms(ns: int | None) -> float | None:
    return None if ns is None else ns / 1e6
