# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Paired inference (protocol section 8): paired bootstrap, exact McNemar, Holm."""

from __future__ import annotations

from dataclasses import dataclass
from math import comb

import numpy as np


@dataclass(frozen=True)
class PairedDiff:
    delta: float  # mean(candidate - baseline), proportion units
    ci_low: float
    ci_high: float
    n: int
    b: int  # candidate correct, baseline wrong
    c: int  # candidate wrong, baseline correct
    mcnemar_p: float


def _as01(x, name: str) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if a.ndim != 1 or a.size == 0:
        raise ValueError(f"{name} must be a non-empty 1-D sequence")
    if np.any((a < 0) | (a > 1)):
        raise ValueError(f"{name} must lie in [0, 1]")
    return a


def paired_bootstrap_ci(cand, base, n_boot: int = 10_000, seed: int = 7, level: float = 0.95):
    """Percentile CI of mean(cand - base) resampling items (the independent unit)."""
    a, b = _as01(cand, "cand"), _as01(base, "base")
    if a.size != b.size:
        raise ValueError("paired vectors must have equal length")
    if n_boot < 1 or not 0 < level < 1:
        raise ValueError("n_boot >= 1 and 0 < level < 1 required")
    d = a - b
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n_boot, d.size))
    means = d[idx].mean(axis=1)
    alpha = (1 - level) / 2
    return float(d.mean()), float(np.quantile(means, alpha)), float(np.quantile(means, 1 - alpha))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from discordant counts b and c."""
    if b < 0 or c < 0:
        raise ValueError("discordant counts must be non-negative")
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def holm(pvalues: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, in the input order."""
    m = len(pvalues)
    if any(not 0 <= p <= 1 for p in pvalues):
        raise ValueError("p-values must lie in [0, 1]")
    order = sorted(range(m), key=lambda i: pvalues[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adj[i] = running
    return adj


def paired_compare(cand, base, n_boot: int = 10_000, seed: int = 7) -> PairedDiff:
    a, bb = _as01(cand, "cand"), _as01(base, "base")
    delta, lo, hi = paired_bootstrap_ci(a, bb, n_boot, seed)
    # Discordance on binarised correctness (majority over repetitions).
    ab, bb2 = a >= 0.5, bb >= 0.5
    b = int(np.sum(ab & ~bb2))
    c = int(np.sum(~ab & bb2))
    return PairedDiff(delta, lo, hi, int(a.size), b, c, mcnemar_exact(b, c))


def median_iqr(x) -> tuple[float, float, float]:
    a = np.asarray(x, dtype=float)
    if a.size == 0:
        raise ValueError("empty sample")
    q1, med, q3 = np.quantile(a, [0.25, 0.5, 0.75])
    return float(med), float(q1), float(q3)


def cv(x) -> float | None:
    """Coefficient of variation (sample sd / mean); None if undefined."""
    a = np.asarray(x, dtype=float)
    if a.size < 2 or a.mean() == 0:
        return None
    return float(a.std(ddof=1) / a.mean())
