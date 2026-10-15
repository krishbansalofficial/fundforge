"""MaskablePPO can train on FundForgeEnv and only ever picks masked-valid actions.

Needs the optional training group (`uv sync --group train`); skipped otherwise, as in CI.
"""

import numpy as np
import pytest

pytest.importorskip("sb3_contrib")

from sb3_contrib import MaskablePPO

from fundforge_ml import worlds
from fundforge_ml.env import FundForgeEnv


def test_maskable_ppo_trains_and_respects_masks():
    env = FundForgeEnv("pm", world_fn=lambda o, r: worlds.world(None, "base"))
    model = MaskablePPO("MlpPolicy", env, n_steps=64, batch_size=32, seed=0, verbose=0, device="cpu")
    model.learn(total_timesteps=128)
    obs, info = env.reset(seed=0)
    done = False
    while not done:
        mask = env.action_masks()
        a, _ = model.predict(obs, deterministic=True, action_masks=mask)
        assert mask[int(a)], "policy chose an action the mask forbids"
        obs, _, term, trunc, info = env.step(int(a))
        done = term or trunc
    assert info["outcome"]["label"] in ("WIN", "SURVIVAL", "DISTRESS")
    assert np.isfinite(obs).all()
