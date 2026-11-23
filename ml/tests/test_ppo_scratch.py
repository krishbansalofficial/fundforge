"""From-scratch PPO (fundforge_ml.ppo): GAE by hand, masks never sampled, the clip, and a short training run.

Needs the optional training group (torch); skipped otherwise, as in CI.
"""

import numpy as np
import pytest

pytest.importorskip("torch")

import torch

from fundforge_ml import ppo, worlds
from fundforge_ml.env import FundForgeEnv


def test_gae_matches_hand_computation():
    # one env, 3 steps, episode ends after step 1; gamma 0.5, lambda 0.5
    r = torch.tensor([[1.0], [2.0], [3.0]])
    v = torch.tensor([[0.5], [1.0], [2.0]])
    done = torch.tensor([[0.0], [1.0], [0.0]])
    adv, ret = ppo.compute_gae(r, v, done, torch.tensor([4.0]), 0.5, 0.5)
    d2 = 3 + 0.5 * 4 - 2  # 3.0, bootstraps from last_value
    d1 = 2 - 1.0  # 1.0, terminal: no bootstrap, and step 2 must not leak back
    d0 = 1 + 0.5 * 1.0 - 0.5  # 1.0
    want = [d0 + 0.25 * d1, d1, d2]
    assert adv.squeeze(-1).tolist() == pytest.approx(want)
    assert ret.squeeze(-1).tolist() == pytest.approx([a + b for a, b in zip(want, [0.5, 1.0, 2.0], strict=True)])


def test_masked_actions_are_never_sampled():
    torch.manual_seed(0)
    net = ppo.ActorCritic(4, 6)
    mask = torch.tensor([[False, True, False, False, True, False]] * 2000)
    a = net.dist(torch.randn(2000, 4), mask).sample()
    assert set(a.tolist()) <= {1, 4}


def test_clipped_loss_equals_plain_surrogate_inside_the_clip():
    old = torch.log(torch.tensor([0.5, 0.5]))
    new = torch.log(torch.tensor([0.55, 0.45]))  # ratios 1.1 and 0.9, inside [0.8, 1.2]
    adv = torch.tensor([1.0, -1.0])
    loss = ppo.clipped_policy_loss(new, old, adv, 0.2)
    assert loss.shape == ()
    assert float(loss) == pytest.approx(-(1.1 * 1.0 + 0.9 * -1.0) / 2)


def test_clip_removes_the_gradient_once_the_ratio_has_moved_far_enough():
    old = torch.log(torch.tensor([0.5, 0.5]))
    new = torch.log(torch.tensor([0.9, 0.1])).requires_grad_()  # ratios 1.8 and 0.2
    adv = torch.tensor([1.0, -1.0])  # good action already pushed up, bad action already pushed down
    loss = ppo.clipped_policy_loss(new, old, adv, 0.2)
    assert float(loss) == pytest.approx(-(1.2 * 1.0 + 0.8 * -1.0) / 2)
    loss.backward()
    assert new.grad is not None and torch.all(new.grad == 0)


def test_clip_is_pessimistic_when_the_update_went_the_wrong_way():
    old = torch.log(torch.tensor([0.5]))
    new = torch.log(torch.tensor([0.1])).requires_grad_()  # ratio 0.2 on a GOOD action: keep the full penalty
    loss = ppo.clipped_policy_loss(new, old, torch.tensor([1.0]), 0.2)
    assert float(loss) == pytest.approx(-0.2)
    loss.backward()
    assert float(new.grad.abs().sum()) > 0


def test_short_training_run_respects_masks_and_finishes_episodes():
    def make():
        return FundForgeEnv("pm", world_fn=lambda o, r: worlds.world(None, "base"))

    cfg = ppo.Config(n_steps=32, batch_size=32, n_epochs=2)
    net, history = ppo.train([make, make], 128, cfg, seed=0)
    assert len(history) == 2 and all(np.isfinite(h["v_loss"]) for h in history)
    env = make()
    obs, _ = env.reset(seed=0)
    done = False
    while not done:
        mask = env.action_masks()
        a = net.act(obs, mask)
        assert mask[a]
        obs, _, term, trunc, info = env.step(a)
        done = term or trunc
    assert info["outcome"]["label"] in ("WIN", "SURVIVAL", "DISTRESS")
