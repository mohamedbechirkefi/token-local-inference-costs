# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""Statistics: hand-computed McNemar and Holm, bootstrap properties, differential checks."""

from itertools import product
from math import comb

import numpy as np
import pytest

from token_lab.stats import cv, holm, mcnemar_exact, median_iqr, paired_bootstrap_ci, paired_compare


def test_mcnemar_hand_computed():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(3, 0) == pytest.approx(0.25)  # 2 * (1/8)
    assert mcnemar_exact(1, 5) == pytest.approx(14 / 64)  # 2 * (1 + 6) / 64
    assert mcnemar_exact(5, 1) == mcnemar_exact(1, 5)
    assert mcnemar_exact(4, 4) == 1.0
    with pytest.raises(ValueError):
        mcnemar_exact(-1, 2)


def test_mcnemar_differential_brute_force():
    # Reference: sum probabilities of all outcomes at least as extreme as observed.
    for b, c in product(range(8), range(8)):
        n = b + c
        if n == 0:
            continue
        obs = abs(b - c)
        ref = sum(comb(n, k) for k in range(n + 1) if abs(k - (n - k)) >= obs) / 2**n
        assert mcnemar_exact(b, c) == pytest.approx(min(1.0, ref))


def test_holm_hand_computed():
    assert holm([0.01, 0.04]) == pytest.approx([0.02, 0.04])
    assert holm([0.04, 0.01]) == pytest.approx([0.04, 0.02])
    assert holm([0.03, 0.02, 0.5]) == pytest.approx([0.06, 0.06, 0.5])  # monotone step-down
    assert holm([0.9, 0.8]) == pytest.approx([1.0, 1.0])
    assert holm([]) == []
    with pytest.raises(ValueError):
        holm([1.2])


def test_holm_invariants():
    rng = np.random.default_rng(3)
    for _ in range(200):
        p = list(rng.uniform(0, 1, size=rng.integers(1, 6)))
        a = holm(p)
        assert all(ai >= pi - 1e-12 and ai <= 1 for ai, pi in zip(a, p))
        order = np.argsort(p)
        assert all(a[order[i]] <= a[order[i + 1]] + 1e-12 for i in range(len(p) - 1))


def test_bootstrap_identical_arms_zero():
    x = [1, 0, 1, 1, 0]
    d, lo, hi = paired_bootstrap_ci(x, x, n_boot=500)
    assert d == lo == hi == 0.0


def test_bootstrap_bounds_and_determinism():
    rng = np.random.default_rng(1)
    a, b = rng.integers(0, 2, 50), rng.integers(0, 2, 50)
    r1 = paired_bootstrap_ci(a, b, n_boot=2000, seed=7)
    r2 = paired_bootstrap_ci(a, b, n_boot=2000, seed=7)
    assert r1 == r2
    d, lo, hi = r1
    assert -1 <= lo <= hi <= 1
    assert d == pytest.approx(np.mean(a) - np.mean(b))
    with pytest.raises(ValueError):
        paired_bootstrap_ci([1, 0], [1], n_boot=10)
    with pytest.raises(ValueError):
        paired_bootstrap_ci([2], [1])


def test_bootstrap_constant_shift():
    # every item: candidate right, baseline wrong -> delta exactly 1 with zero-width CI
    d, lo, hi = paired_bootstrap_ci([1] * 20, [0] * 20, n_boot=300)
    assert (d, lo, hi) == (1.0, 1.0, 1.0)


def test_paired_compare_discordance():
    cand = [1, 1, 1, 0, 0, 1]
    base = [0, 0, 1, 1, 0, 1]
    pd = paired_compare(cand, base, n_boot=200)
    assert (pd.b, pd.c, pd.n) == (2, 1, 6)
    assert pd.mcnemar_p == pytest.approx(1.0)
    assert pd.delta == pytest.approx(1 / 6)


def test_median_iqr_and_cv():
    assert median_iqr([1, 2, 3, 4, 5]) == (3.0, 2.0, 4.0)
    assert cv([2, 2, 2]) == 0.0
    assert cv([1]) is None
    assert cv([1, 3]) == pytest.approx(np.std([1, 3], ddof=1) / 2)
    with pytest.raises(ValueError):
        median_iqr([])
