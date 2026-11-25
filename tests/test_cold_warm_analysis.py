# SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0
"""EXP-002 penalty analysis (protocol items 5, 6 and 16): two-sample median
bootstrap, per-arm penalties with trial validity, the ordering rule, and the
report on the simulated backend. Ollama is never contacted."""

import csv
import json

import numpy as np
import pytest

from token_lab.analysis import EXP002_SIZE_ORDER, cold_warm_ordering, cold_warm_penalties
from token_lab.config import parse_config
from token_lab.report import build_report
from token_lab.runner import execute
from token_lab.runtime import SimulatedBackend
from token_lab.stats import bootstrap_median_diff


# ---- statistics -------------------------------------------------------------

def test_median_diff_point_estimates_hand_computed():
    md = bootstrap_median_diff([10, 30, 20, 40], [1, 2, 3], n_boot=200)
    assert md.median_x == 25.0 and md.median_y == 2.0 and md.diff == 23.0
    assert (md.n_x, md.n_y) == (4, 3)
    assert md.ci_x[0] <= md.median_x <= md.ci_x[1]
    assert md.ci_y[0] <= md.median_y <= md.ci_y[1]
    assert md.ci_diff[0] <= md.diff <= md.ci_diff[1]
    # bootstrap medians stay inside the observed range
    assert 10 <= md.ci_x[0] and md.ci_x[1] <= 40 and 1 <= md.ci_y[0] and md.ci_y[1] <= 3


def test_median_diff_constant_samples_zero_width():
    md = bootstrap_median_diff([500.0] * 10, [50.0] * 10, n_boot=300)
    assert md.diff == 450.0 and md.ci_diff == (450.0, 450.0)
    assert md.ci_x == (500.0, 500.0) and md.ci_y == (50.0, 50.0)


def test_median_diff_deterministic_and_matches_reference():
    rng = np.random.default_rng(11)
    x, y = rng.normal(900, 50, 10), rng.normal(80, 5, 10)
    a = bootstrap_median_diff(x, y, n_boot=10_000, seed=7)
    assert a == bootstrap_median_diff(x, y, n_boot=10_000, seed=7)
    # independent reference implementation of the documented draw order
    g = np.random.default_rng(7)
    ix = g.integers(0, 10, size=(10_000, 10))
    iy = g.integers(0, 10, size=(10_000, 10))
    d = np.median(x[ix], axis=1) - np.median(y[iy], axis=1)
    assert a.ci_diff == pytest.approx((np.quantile(d, 0.025), np.quantile(d, 0.975)))
    assert a.diff == pytest.approx(np.median(x) - np.median(y))


@pytest.mark.parametrize("x,y", [([], [1.0]), ([1.0], []), ([float("nan")], [1.0]), ([[1.0]], [1.0])])
def test_median_diff_rejects_bad_input(x, y):
    with pytest.raises(ValueError):
        bootstrap_median_diff(x, y, n_boot=10)


# ---- per-arm penalties --------------------------------------------------------

def _rec(arm, state, ttft, valid=True, error=None, i=0):
    return {"arm": arm, "model": f"m-{arm}", "start_state": state, "trial_index": i, "state_valid": valid,
            "state_check": {}, "error": error, "ttft_ms": ttft, "latency_ms": None if ttft is None else ttft + 5,
            "load_duration_ns": None if ttft is None else int(ttft * 1e6) if state == "cold" else 1_000_000}


def _doc(values: dict, extra=()):
    """values: arm -> (cold list, warm list)."""
    recs = []
    for arm, (cold, warm) in values.items():
        for i, (c, w) in enumerate(zip(cold, warm)):
            recs += [_rec(arm, "cold", c, i=i), _rec(arm, "warm", w, i=i)]
    recs += list(extra)
    arms = [{"arm_id": a, "model": f"m-{a}"} for a in values]
    return {"config": {"arms": arms}, "records": recs}


def test_penalties_known_values_and_validity_filter():
    values = {"A0": ([100, 110, 120], [10, 10, 10]), "A1": ([300, 310, 320], [20, 20, 20])}
    bad = [_rec("A0", "cold", 9999.0, valid=False), _rec("A0", "warm", 9999.0, error="boom"),
           _rec("A1", "cold", None, error="timeout")]
    rows = {r["arm"]: r for r in cold_warm_penalties(_doc(values, bad), n_boot=500)}
    a0, a1 = rows["A0"], rows["A1"]
    assert (a0["cold_ttft_ms_median"], a0["warm_ttft_ms_median"], a0["penalty_ms"]) == (110.0, 10.0, 100.0)
    assert a1["penalty_ms"] == 290.0
    assert (a0["n_cold"], a0["n_warm"], a0["n_cold_records"], a0["n_warm_records"]) == (3, 3, 4, 4)
    assert (a0["n_cold_invalid"], a0["n_warm_error"]) == (1, 1)
    assert (a1["n_cold"], a1["n_cold_error"]) == (3, 1)
    assert 9999.0 not in a0["cold_ttft_ms"] + a0["warm_ttft_ms"]  # excluded, but counted above
    assert a0["warm_load_ms_median"] == pytest.approx(1.0) and a0["cold_latency_ms_median"] == 115.0


def test_penalties_arm_without_valid_trials_is_reported_not_dropped():
    doc = _doc({"A0": ([100], [10])}, [_rec("A1", "cold", 50.0, valid=False), _rec("A1", "warm", 5.0)])
    doc["config"]["arms"].append({"arm_id": "A1", "model": "m-A1"})
    rows = {r["arm"]: r for r in cold_warm_penalties(doc, n_boot=50)}
    assert rows["A1"]["penalty_ms"] is None and rows["A1"]["n_cold_invalid"] == 1 and rows["A1"]["n_warm"] == 1


# ---- ordering rule (item 5) ---------------------------------------------------

def _row(arm, pen, lo, hi):
    return {"arm": arm, "penalty_ms": pen, "penalty_ci_low": lo, "penalty_ci_high": hi}


def test_size_order_is_the_protocol_order():
    assert [a for a, _ in EXP002_SIZE_ORDER] == ["A0", "A1", "A2"]
    assert [s for _, s in EXP002_SIZE_ORDER] == sorted(s for _, s in EXP002_SIZE_ORDER)


def test_ordering_supported():
    od = cold_warm_ordering([_row("A2", 900, 850, 950), _row("A0", 100, 90, 110), _row("A1", 500, 450, 550)])
    assert od["verdict"].startswith("H1 supported") and not od["reversal"] and not od["overlap"]


def test_ordering_unresolved_by_overlap():
    od = cold_warm_ordering([_row("A0", 100, 90, 300), _row("A1", 500, 250, 550), _row("A2", 900, 850, 950)])
    assert od["overlap"] and not od["reversal"] and "unresolved" in od["verdict"]
    assert [p["ci_overlap"] for p in od["pairs"]] == [True, False]


def test_ordering_reversal_reported_with_and_without_overlap():
    od = cold_warm_ordering([_row("A0", 100, 90, 110), _row("A1", 900, 850, 950), _row("A2", 500, 450, 550)])
    assert od["reversal"] and not od["overlap"] and od["verdict"].endswith("point estimates")
    od = cold_warm_ordering([_row("A0", 100, 90, 110), _row("A1", 600, 450, 700), _row("A2", 550, 500, 650)])
    assert od["reversal"] and od["overlap"] and "and overlapping" in od["verdict"]


def test_ordering_tie_and_missing_are_not_classified():
    od = cold_warm_ordering([_row("A0", 100, 90, 110), _row("A1", 100, 95, 105), _row("A2", 900, 850, 950)])
    assert od["tie"] and "not classified" in od["verdict"]
    od = cold_warm_ordering([_row("A0", 100, 90, 110), _row("A1", None, None, None), _row("A2", 900, 850, 950)])
    assert od["evaluable"] is False and "not evaluable" in od["verdict"]


# ---- end to end on the simulated backend --------------------------------------

def test_cold_warm_report_simulated(repo, tmp_path):
    raw = json.loads((repo / "experiments" / "EXP-002.json").read_text())
    raw.update(mode="exploratory", backend={"name": "simulated", "track_loading": True})
    raw["items"] = {"path": "data/fixtures/synthetic_mc.jsonl", "synthetic": True, "subset_size": 1,
                    "subset_seed": 20261124}
    doc, path = execute(parse_config(raw), repo, backend=SimulatedBackend(track_loading=True), out_root=tmp_path)
    info = build_report(path)
    rows = list(csv.DictReader(open(info["cold_warm_csv"], encoding="utf-8")))
    assert [r["arm"] for r in rows] == ["A0", "A1", "A2"]
    assert all(r["n_cold"] == "10" and r["n_warm"] == "10" and r["n_cold_invalid"] == "0" for r in rows)
    pen = cold_warm_penalties(doc)
    assert all(p["penalty_ms"] is not None and p["penalty_ci_low"] <= p["penalty_ms"] <= p["penalty_ci_high"]
               for p in pen)
    md = open(info["report_md"], encoding="utf-8").read()
    assert "Cold-start penalty (EXP-002" in md and "Ordering check by file size" in md
    assert "Paired contrasts against the baseline" not in md  # no accuracy contrast on one prompt
    assert open(info["cold_warm_figure"], encoding="utf-8").read().startswith("<svg")


def test_matrix_report_has_no_cold_warm_outputs(repo, tmp_path):
    raw = json.loads((repo / "experiments" / "smoke-simulated.json").read_text())
    raw.update(repetitions=1, runtime_seeds=[0])
    _, path = execute(parse_config(raw), repo, out_root=tmp_path)
    info = build_report(path)
    assert "cold_warm_csv" not in info and not (path.parent / "cold_warm.csv").exists()
