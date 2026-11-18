"""OPE estimators on a tiny bandit-like MDP with a known answer."""

import numpy as np

from fundforge_ml.ope import Step, ess, fqe, pdis, ratios

A = 2


class LinearRegression:
    """Ordinary least squares with an intercept (numpy only)."""

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.w = np.linalg.lstsq(np.hstack([x, np.ones((len(x), 1))]), y, rcond=None)[0]

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.hstack([x, np.ones((len(x), 1))]) @ self.w


MASK = np.ones(A, dtype=bool)


def make(n: int, rng: np.random.Generator) -> list[list[Step]]:
    """Two steps; action 1 pays 1, action 0 pays 0; behaviour is uniform (mu = 0.5)."""
    eps = []
    for _ in range(n):
        ep = []
        for t in range(2):
            a = int(rng.integers(0, A))
            ep.append(Step(np.array([float(t)], dtype=np.float32), a, float(a), MASK, 0.5))
        eps.append(ep)
    return eps


def always_one(obs: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return np.array([0.0, 1.0])


def test_estimators_recover_the_value_of_a_deterministic_target() -> None:
    eps = make(4000, np.random.default_rng(0))
    rho = ratios(eps, always_one)  # true value 2.0
    assert abs(pdis(eps, rho) - 2.0) < 0.15
    assert abs(pdis(eps, rho, weighted=True) - 2.0) < 1e-9  # WPDIS is exact here
    assert 800 < ess(rho) < 1200  # about n/4: only episodes taking action 1 twice keep weight
    v, _ = fqe(eps, always_one, A, LinearRegression, rounds=2)
    assert abs(v - 2.0) < 0.05


def test_on_policy_weights_are_one() -> None:
    eps = make(200, np.random.default_rng(1))
    rho = ratios(eps, lambda o, m: np.array([0.5, 0.5]))
    assert all(np.allclose(p, 1.0) for p in rho) and abs(ess(rho) - 200) < 1e-9
