"""Belief observation wrapper for the value-of-information experiment.

``BeliefWrapper`` appends one feature to ``FundForgeEnv``'s observation: P(stressed) for the latest
published Street activity period. Three modes share one observation shape:

- ``none``: a constant 0.0, so the policy gets no belief;
- ``learned``: a forecaster trained on train families only (``forecast.features`` -> probability);
- ``exact``: ``forecast.bayes``, the exact forward filter, i.e. the Bayes-optimal posterior.

The belief reads only the seat terminal's ``macro`` rows at the observation's as-of day:
``forecast.macro_rows(tape, view["clock"]["day"])`` is the same expression as
``terminal.snapshot(engine, role)["macro"]`` (parity is tested in tests/test_belief.py), and
``forecast.features``/``bayes`` drop again any row published after the as-of day. Before the first
print there is no question yet; the belief is 0.0 there in every mode (the generator starts calm).
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np
import numpy.typing as npt

from . import forecast
from .env import FundForgeEnv

BELIEF_VERSION = "belief-v1"
MODES = ("none", "learned", "exact")
NO_BELIEF = 0.0

Forecaster = Callable[[npt.NDArray[np.float64]], float]


@dataclass(frozen=True)
class Logistic:
    """P(stressed) from ``forecast.features``; ``w`` is ``scripts/train_forecast.logreg`` output (bias last)."""

    w: npt.NDArray[np.float64]

    def __call__(self, x: npt.NDArray[np.float64]) -> float:
        return float(1.0 / (1.0 + np.exp(-(float(x @ self.w[:-1]) + float(self.w[-1])))))


def belief(rows: Iterable[forecast.Row], as_of: int, mode: str, forecaster: Forecaster | None = None) -> float:
    """The belief feature from published macro rows at ``as_of`` (pure; rows published later are ignored)."""
    rows = list(rows)
    if mode == "none" or not forecast.known(rows, as_of):
        return NO_BELIEF
    if mode == "exact":
        return forecast.bayes(rows, as_of)[1]
    if forecaster is None:
        raise ValueError("mode 'learned' needs a forecaster")
    return float(forecaster(forecast.features(rows, as_of)))


class BeliefWrapper(gym.ObservationWrapper[npt.NDArray[np.float32], int, npt.NDArray[np.float32]]):
    def __init__(self, env: FundForgeEnv, mode: str, forecaster: Forecaster | None = None) -> None:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if (mode == "learned") != (forecaster is not None):
            raise ValueError("a forecaster is required for, and only for, mode 'learned'")
        super().__init__(env)
        self.base, self.mode, self.forecaster = env, mode, forecaster
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (env.layout.size + 1,), np.float32)

    def rows(self) -> list[dict[str, Any]]:
        """The seat terminal's macro rows at the current observation's as-of day."""
        return forecast.macro_rows(self.base.world.tape, self.base.view["clock"]["day"])

    def belief(self) -> float:
        if self.mode == "none":
            return NO_BELIEF
        return belief(self.rows(), self.base.view["clock"]["day"], self.mode, self.forecaster)

    def observation(self, observation: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        return np.append(observation, np.float32(self.belief())).astype(np.float32)

    def action_masks(self) -> npt.NDArray[np.bool_]:
        return self.base.action_masks()
