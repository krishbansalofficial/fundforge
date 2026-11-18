"""Off-policy evaluation estimators (Voloshin, Le, Jiang and Yue, arXiv 1911.06854), undiscounted episodes.

Logged episodes come from a known behaviour policy ``mu``; ``pi`` is the policy to evaluate. Per step we keep the
probability each policy gave the logged action, so:

- per-decision importance sampling (PDIS): sum_t r_t * prod_{k<=t} pi_k / mu_k, averaged over episodes;
- weighted PDIS (WPDIS): the same with each step's weights normalised by their mean over episodes (biased, lower
  variance);
- fitted Q evaluation (FQE): regress Q(s, a) on r + E_{a'~pi}[Q(s', a')] for H rounds, then average
  E_{a~pi}[Q(s0, a)] over logged start states. ``fit`` is any regressor factory with fit/predict.

``ess`` is the effective sample size of the full-episode weights, (sum w)^2 / sum w^2.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class Step:
    obs: np.ndarray
    action: int
    reward: float
    mask: np.ndarray  # valid actions at obs
    mu: float  # behaviour probability of `action`


def ratios(episodes: list[list[Step]], pi: Callable[[np.ndarray, np.ndarray], np.ndarray]) -> list[np.ndarray]:
    """Per-step pi(a|s) / mu(a|s) for each episode."""
    return [np.array([pi(s.obs, s.mask)[s.action] / s.mu for s in ep]) for ep in episodes]


def pdis(episodes: list[list[Step]], rho: list[np.ndarray], weighted: bool = False) -> float:
    horizon = max(len(ep) for ep in episodes)
    w = np.zeros((len(episodes), horizon))
    r = np.zeros((len(episodes), horizon))
    for i, (ep, p) in enumerate(zip(episodes, rho, strict=True)):
        w[i, : len(ep)] = np.cumprod(p)
        r[i, : len(ep)] = [s.reward for s in ep]
    if weighted:  # normalise over the episodes that reach each step (episodes differ in length)
        alive = np.zeros_like(w, dtype=bool)
        for i, ep in enumerate(episodes):
            alive[i, : len(ep)] = True
        mean = np.divide(w.sum(axis=0), alive.sum(axis=0), out=np.zeros(horizon), where=alive.sum(axis=0) > 0)
        w = np.divide(w, mean, out=np.zeros_like(w), where=mean > 0)
    return float((w * r).sum(axis=1).mean())


def ess(rho: list[np.ndarray]) -> float:
    w = np.array([np.prod(p) for p in rho])
    return float(w.sum() ** 2 / (w**2).sum()) if (w**2).sum() > 0 else 0.0


def fqe(episodes: list[list[Step]], pi: Callable[[np.ndarray, np.ndarray], np.ndarray], n_actions: int,
        fit: Callable[[], Any], rounds: int) -> tuple[float, np.ndarray]:
    """Returns (mean start-state value, per-episode start values)."""
    eye = np.eye(n_actions, dtype=np.float32)
    s = [st for ep in episodes for st in ep]
    nxt = [ep[t + 1] if t + 1 < len(ep) else None for ep in episodes for t in range(len(ep))]
    x = np.hstack([np.stack([st.obs for st in s]), eye[[st.action for st in s]]])
    r = np.array([st.reward for st in s])

    def v(states: list[Step], model: Any) -> np.ndarray:
        """E_{a~pi}[Q(s, a)] for each state, over its valid actions."""
        if model is None or not states:
            return np.zeros(len(states))
        probs = np.stack([pi(st.obs, st.mask) for st in states])  # (n, A)
        obs = np.repeat(np.stack([st.obs for st in states]), n_actions, axis=0)
        q = model.predict(np.hstack([obs, np.tile(eye, (len(states), 1))])).reshape(len(states), n_actions)
        return (probs * q).sum(axis=1)

    live = [i for i, n in enumerate(nxt) if n is not None]
    model = None
    for _ in range(rounds):
        target = r.copy()
        target[live] += v([nxt[i] for i in live], model)
        model = fit()
        model.fit(x, target)
    starts = v([ep[0] for ep in episodes], model)
    return float(starts.mean()), starts
