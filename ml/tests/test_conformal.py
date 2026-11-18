"""Split conformal: coverage holds on exchangeable synthetic data, Mondrian holds per class, sets are exact."""

import numpy as np

from fundforge_ml import conformal as C


def test_marginal_and_class_conditional_coverage_on_synthetic_data() -> None:
    rng = np.random.default_rng(3)
    n = 40_000
    p_true = rng.beta(0.6, 1.2, n)
    y = (rng.random(n) < p_true).astype(int)
    p = np.clip(p_true + rng.normal(0, 0.15, n), 0, 1)  # a miscalibrated forecaster
    cal, test = slice(0, n // 2), slice(n // 2, n)
    for alpha in (0.05, 0.1, 0.2):
        m = C.evaluate(C.sets(p[test], C.calibrate(p[cal], y[cal], alpha)), y[test])
        assert abs(m["coverage"] - (1 - alpha)) < 0.01, (alpha, m)
        mm = C.evaluate(C.sets(p[test], C.calibrate(p[cal], y[cal], alpha, mondrian=True)), y[test])
        assert min(mm["coverage_calm"], mm["coverage_stressed"]) > 1 - alpha - 0.015, (alpha, mm)


def test_sets_and_quantile_are_exact_on_a_tiny_case() -> None:
    s = np.array([0.1, 0.2, 0.3, 0.4])
    assert C.qhat(s, 0.5) == 0.3  # k = ceil(5 * 0.5) = 3: the third smallest score
    assert C.qhat(s, 0.01) == 1.0  # too few points for 99%: the set is everything
    got = C.sets(np.array([0.05, 0.5, 0.95]), 0.3)
    assert got.tolist() == [[True, False], [False, False], [False, True]]
