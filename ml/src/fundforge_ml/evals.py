"""Interval estimates for policy comparisons (numpy only).

Follows Agarwal et al. 2021, "Deep RL at the Edge of the Statistical Precipice": with few
training seeds, report a bootstrap interval, the interquartile mean (IQM) and the probability
of improvement instead of a mean with a normal interval.

Scores are arrays of shape ``(runs, worlds)``: one row per training seed (or random-play seed),
one column per deterministic evaluation world. Columns are the pairing unit, so two policies
must be scored on the same worlds in the same column order.
"""

from collections.abc import Callable
from typing import Any

import numpy as np
import numpy.typing as npt

Scores = npt.NDArray[np.float64]
Stat = Callable[[Scores], float]


def _2d(x: npt.ArrayLike) -> Scores:
    a = np.asarray(x, dtype=np.float64)
    a = a.reshape(1, -1) if a.ndim == 1 else a
    if a.ndim != 2 or a.size == 0:
        raise ValueError(f"scores must be (runs, worlds) and non-empty, got shape {a.shape}")
    return a


def iqm(x: npt.ArrayLike) -> float:
    """Mean of the middle 50% of all scores (scipy.stats.trim_mean with 0.25 cut)."""
    s = np.sort(np.asarray(x, dtype=np.float64).ravel())
    k = int(0.25 * len(s))
    return float(s[k:len(s) - k].mean())


def mean(x: npt.ArrayLike) -> float:
    return float(np.asarray(x, dtype=np.float64).mean())


def bootstrap_ci(scores: npt.ArrayLike, stat: Stat = iqm, *, reps: int = 2000, seed: int = 0,
                 alpha: float = 0.05) -> dict[str, float]:
    """Percentile interval, resampling worlds and runs independently with replacement."""
    a = _2d(scores)
    rng = np.random.default_rng(seed)
    runs, cols = a.shape
    boot = np.empty(reps)
    for i in range(reps):
        boot[i] = stat(a[rng.integers(runs, size=runs)][:, rng.integers(cols, size=cols)])
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    return {"point": stat(a), "lo": float(lo), "hi": float(hi)}


def prob_improvement(x: npt.ArrayLike, y: npt.ArrayLike) -> float:
    """P(X > Y): chance a run of X beats a run of Y on the same world, averaged over worlds.

    Both arrays are ``(runs, worlds)``; run counts may differ, world columns must match.
    """
    a, b = _2d(x), _2d(y)
    if a.shape[1] != b.shape[1]:
        raise ValueError("x and y must be scored on the same worlds")
    xa, yb = a[:, None, :], b[None, :, :]  # (runs_x, runs_y, worlds)
    return float(((xa > yb) + 0.5 * (xa == yb)).mean())


def compare(x: npt.ArrayLike, y: npt.ArrayLike, *, reps: int = 2000, seed: int = 0) -> dict[str, Any]:
    """Paired comparison of X against Y on the same worlds: per-world mean difference and P(X > Y)."""
    a, b = _2d(x), _2d(y)
    d = a.mean(axis=0) - b.mean(axis=0)
    return {"n_worlds": len(d), "diff": bootstrap_ci(d, mean, reps=reps, seed=seed),
            "x_better_worlds": int((d > 0).sum()), "ties": int((d == 0).sum()),
            "prob_improvement": prob_improvement(a, b)}


def summary(scores: npt.ArrayLike, *, reps: int = 2000, seed: int = 0) -> dict[str, Any]:
    a = _2d(scores)
    return {"runs": a.shape[0], "worlds": a.shape[1], "mean": bootstrap_ci(a, mean, reps=reps, seed=seed),
            "iqm": bootstrap_ci(a, iqm, reps=reps, seed=seed)}
