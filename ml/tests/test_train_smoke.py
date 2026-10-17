"""Training smoke: MaskablePPO trains through train_ppo.train, saves, reloads and respects masks.

Needs the optional training group (`uv sync --group train`); skipped otherwise, as in CI.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sb3_contrib")

from sb3_contrib import MaskablePPO

from fundforge_ml import worlds
from fundforge_ml.env import FundForgeEnv

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from train_ppo import DEFAULT_HP, train


def test_train_then_save_reload_respects_masks(tmp_path: Path):
    model, secs = train("pm", [None], 128, 0, {**DEFAULT_HP, "n_steps": 64, "batch_size": 32, "width": 32}, workers=1)  # type: ignore[list-item]  # None = the authored Case1 world
    assert secs > 0
    path = tmp_path / "m.zip"
    model.save(path)
    loaded = MaskablePPO.load(path, device="cpu")
    env = FundForgeEnv("pm", world_fn=lambda o, r: worlds.world(None, "base"))
    obs, info = env.reset(seed=0)
    done = False
    while not done:
        mask = env.action_masks()
        a, _ = loaded.predict(obs, deterministic=True, action_masks=mask)
        assert mask[int(a)], "policy chose an action the mask forbids"
        obs, _, term, trunc, info = env.step(int(a))
        done = term or trunc
    assert info["outcome"]["label"] in ("WIN", "SURVIVAL", "DISTRESS")
    assert np.isfinite(obs).all()
