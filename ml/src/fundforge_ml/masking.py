"""The no-mask arm of the masking ablation: let the policy pick any action and charge for invalid ones.

The env already rejects an invalid command (the window passes as if waiting); this wrapper only adds a
fixed reward penalty and counts the invalid picks, so the two arms see the same game.
"""

from typing import Any

import gymnasium as gym
import numpy as np

PENALTY = 0.1  # reward units; a WIN tier bonus is several units, so one invalid pick is cheap but not free


class InvalidActionPenalty(gym.Wrapper[Any, int, Any, int]):
    def __init__(self, env: gym.Env[Any, int], penalty: float = PENALTY) -> None:
        super().__init__(env)
        self.penalty, self.invalid = penalty, 0

    def step(self, action: int) -> tuple[Any, float, bool, bool, dict[str, Any]]:
        bad = not bool(np.asarray(self.env.unwrapped.action_masks())[int(action)])  # type: ignore[attr-defined]
        self.invalid += bad
        obs, r, term, trunc, info = self.env.step(0 if bad else action)
        return obs, float(r) - (self.penalty if bad else 0.0), term, trunc, {**info, "invalid_action": bad}
