"""Evaluation statistics: IQM, bootstrap intervals, paired comparison and P(X > Y)."""

import numpy as np
import pytest

from fundforge_ml import evals


def test_iqm_drops_the_outer_quartiles():
    assert evals.iqm([0, 1, 2, 3, 4, 5, 6, 1000]) == 3.5


def test_bootstrap_interval_contains_point_and_is_deterministic():
    x = np.random.default_rng(1).normal(2.0, 1.0, size=(5, 40))
    a, b = evals.bootstrap_ci(x, reps=500, seed=7), evals.bootstrap_ci(x, reps=500, seed=7)
    assert a == b
    assert a["lo"] <= a["point"] <= a["hi"]
    assert 1.5 < a["point"] < 2.5


def test_constant_scores_give_a_zero_width_interval():
    ci = evals.bootstrap_ci(np.full((3, 10), 4.0), evals.mean, reps=200)
    assert ci == {"point": 4.0, "lo": 4.0, "hi": 4.0}


def test_prob_improvement_counts_ties_as_half_and_is_complementary():
    x = np.array([[1.0, 2.0, 3.0]])
    y = np.array([[0.0, 2.0, 5.0], [0.0, 2.0, 1.0]])
    # world 0: x always wins (1); world 1: always ties (0.5); world 2: wins 1 of 2 (0.5)
    assert evals.prob_improvement(x, y) == pytest.approx(2 / 3)
    assert evals.prob_improvement(x, y) + evals.prob_improvement(y, x) == pytest.approx(1.0)


def test_compare_is_paired_by_world():
    worlds = np.random.default_rng(2).normal(0, 10, size=50)  # large world-to-world spread
    x, y = (worlds + 1.0).reshape(1, -1), worlds.reshape(1, -1)
    c = evals.compare(x, y, reps=500)
    assert c["diff"]["lo"] == c["diff"]["hi"] == pytest.approx(1.0)  # pairing removes the world spread
    assert c["x_better_worlds"] == 50 and c["prob_improvement"] == 1.0


def test_mismatched_worlds_are_refused():
    with pytest.raises(ValueError):
        evals.prob_improvement(np.zeros((1, 3)), np.zeros((1, 4)))
