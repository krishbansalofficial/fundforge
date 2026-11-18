"""Split conformal prediction sets for the binary regime forecast (Angelopoulos and Bates, arXiv 2107.07511).

Score: s = 1 - p(true class). On a calibration set of n scores, qhat is the k-th smallest score with
k = ceil((n+1)(1-alpha)); the prediction set for a new point is every class c with 1 - p(c) <= qhat.
If calibration and test points are exchangeable, P(true class in set) >= 1 - alpha. ``mondrian`` calibrates
each class separately, which gives the same guarantee conditional on the true class.
"""

import math

import numpy as np


def qhat(scores: np.ndarray, alpha: float) -> float:
    """The k-th smallest score, k = ceil((n+1)(1-alpha)); 1.0 (every class) when k > n.

    Taken as an order statistic: np.quantile(..., k/n, method="higher") picks the next one up and over-covers.
    """
    n = len(scores)
    k = math.ceil((n + 1) * (1 - alpha))
    return 1.0 if k > n else float(np.sort(scores)[k - 1])


def scores(p_stressed: np.ndarray, y: np.ndarray) -> np.ndarray:
    """1 - probability given to the true class (y = 1 means stressed)."""
    return np.where(y == 1, 1 - p_stressed, p_stressed)


def sets(p_stressed: np.ndarray, q: float | tuple[float, float]) -> np.ndarray:
    """(n, 2) boolean: column 0 = calm in set, column 1 = stressed in set. A tuple is (q_calm, q_stressed)."""
    q0, q1 = q if isinstance(q, tuple) else (q, q)
    return np.column_stack([p_stressed <= q0, 1 - p_stressed <= q1])


def calibrate(p: np.ndarray, y: np.ndarray, alpha: float, mondrian: bool = False) -> float | tuple[float, float]:
    if not mondrian:
        return qhat(scores(p, y), alpha)
    return qhat(scores(p[y == 0], y[y == 0]), alpha), qhat(scores(p[y == 1], y[y == 1]), alpha)


def evaluate(s: np.ndarray, y: np.ndarray) -> dict[str, float]:
    covered = s[np.arange(len(y)), y.astype(int)]
    size = s.sum(axis=1)
    return {"coverage": float(covered.mean()), "mean_size": float(size.mean()),
            "share_empty": float((size == 0).mean()), "share_singleton": float((size == 1).mean()),
            "share_both": float((size == 2).mean()),
            "coverage_calm": float(covered[y == 0].mean()) if (y == 0).any() else math.nan,
            "coverage_stressed": float(covered[y == 1].mean()) if (y == 1).any() else math.nan}
