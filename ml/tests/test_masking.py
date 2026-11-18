"""The no-mask arm: an invalid pick becomes a wait and costs the penalty; a valid pick passes through."""

from typing import Any

import gymnasium as gym
import numpy as np

from fundforge_ml.masking import PENALTY, InvalidActionPenalty


class Toy(gym.Env[Any, int]):
    observation_space = gym.spaces.Box(0, 1, (1,), np.float32)
    action_space = gym.spaces.Discrete(3)

    def __init__(self) -> None:
        self.taken: list[int] = []

    def action_masks(self) -> np.ndarray:
        return np.array([True, True, False])

    def reset(self, *, seed: int | None = None, options: dict | None = None) -> tuple[Any, dict]:
        return np.zeros(1, np.float32), {}

    def step(self, action: int) -> tuple[Any, float, bool, bool, dict]:
        self.taken.append(action)
        return np.zeros(1, np.float32), 1.0, False, False, {}


def test_invalid_pick_waits_and_is_charged() -> None:
    env = InvalidActionPenalty(Toy())
    env.reset()
    _, r, *_, info = env.step(2)
    assert env.unwrapped.taken == [0] and r == 1.0 - PENALTY and info["invalid_action"] and env.invalid == 1
    _, r, *_, info = env.step(1)
    assert env.unwrapped.taken == [0, 1] and r == 1.0 and not info["invalid_action"] and env.invalid == 1
