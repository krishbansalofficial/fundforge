"""PPO with action masking, from scratch (Stage 2 of docs/ML_SHOWCASE.md).

Single file, CleanRL style, written to match the SB3 MaskablePPO settings used by scripts/eval_ppo.py so the two
can be compared on the same worlds and seeds: separate 128x128 tanh actor and critic, orthogonal init,
Adam (eps 1e-5), n_steps 256 per env, batch 256, 10 epochs, GAE lambda 0.95, clip 0.2, value coef 0.5,
grad-norm clip 0.5, per-minibatch advantage normalisation, truncated episodes bootstrapped with V(final obs).

References: Schulman et al. 2017 (arXiv 1707.06347); GAE, Schulman et al. 2015 (arXiv 1506.02438);
Huang et al. 2022, "The 37 implementation details of PPO"; Huang & Ontañón 2020 on invalid action masking.

Needs the ``train`` dependency group (torch).
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt
import torch
from torch import nn
from torch.distributions import Categorical

MASKED = -1e8  # logit for invalid actions: exp(-1e8) == 0 in float32, so they are never sampled


@dataclass(frozen=True)
class Config:
    n_steps: int = 256  # rollout length per env
    batch_size: int = 256
    n_epochs: int = 10
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip: float = 0.2
    learning_rate: float = 1e-4
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    hidden: int = 128


def _layer(n_in: int, n_out: int, gain: float) -> nn.Linear:
    layer = nn.Linear(n_in, n_out)
    nn.init.orthogonal_(layer.weight, gain)
    nn.init.zeros_(layer.bias)
    return layer


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int, hidden: int = 128) -> None:
        super().__init__()
        g = 2**0.5
        self.actor = nn.Sequential(_layer(obs_dim, hidden, g), nn.Tanh(), _layer(hidden, hidden, g), nn.Tanh(),
                                   _layer(hidden, n_actions, 0.01))
        self.critic = nn.Sequential(_layer(obs_dim, hidden, g), nn.Tanh(), _layer(hidden, hidden, g), nn.Tanh(),
                                    _layer(hidden, 1, 1.0))

    def dist(self, obs: torch.Tensor, mask: torch.Tensor) -> Categorical:
        return Categorical(logits=masked_logits(self.actor(obs), mask))

    def value(self, obs: torch.Tensor) -> torch.Tensor:
        return self.critic(obs).squeeze(-1)

    @torch.no_grad()
    def act(self, obs: npt.NDArray[np.float32], mask: npt.NDArray[np.bool_]) -> int:
        """Deterministic action for evaluation: the most likely valid action."""
        logits = masked_logits(self.actor(torch.as_tensor(obs)), torch.as_tensor(mask))
        return int(logits.argmax())


def masked_logits(logits: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    return torch.where(mask, logits, torch.full_like(logits, MASKED))


def compute_gae(rewards: torch.Tensor, values: torch.Tensor, dones: torch.Tensor, last_value: torch.Tensor,
                gamma: float, lam: float) -> tuple[torch.Tensor, torch.Tensor]:
    """Generalised advantage estimation over a (T, n_envs) rollout.

    ``dones[t]`` is 1 when the episode ended after step t (the env was reset), so nothing from step t+1
    leaks back across the boundary. ``last_value`` is V(obs after the final step). Returns (advantages, returns).
    """
    adv = torch.zeros_like(rewards)
    running = torch.zeros_like(last_value)
    for t in reversed(range(len(rewards))):
        nonterminal = 1.0 - dones[t]
        next_value = last_value if t == len(rewards) - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_value * nonterminal - values[t]
        running = delta + gamma * lam * nonterminal * running
        adv[t] = running
    return adv, adv + values


def clipped_policy_loss(new_logp: torch.Tensor, old_logp: torch.Tensor, adv: torch.Tensor,
                        clip: float) -> torch.Tensor:
    """PPO's clipped surrogate objective, returned as a loss to minimise (a scalar).

    new_logp: log pi_theta(a|s) under the current network (has gradients).
    old_logp: log pi_old(a|s) recorded when the rollout was collected (no gradients).
    adv:      normalised advantages for the same samples.
    clip:     epsilon, e.g. 0.2.
    """
    ratio = (new_logp - old_logp).exp()
    # min of the two makes the objective pessimistic: the clip only removes gradient once the ratio has
    # already moved in the direction the advantage wants; a move the wrong way keeps its full penalty
    return -torch.min(ratio * adv, ratio.clamp(1 - clip, 1 + clip) * adv).mean()


EnvFn = Callable[[], Any]  # returns a FundForgeEnv-like env with action_masks()


def train(env_fns: Sequence[EnvFn], total_steps: int, cfg: Config | None = None, seed: int = 0,
          log: Callable[[dict[str, float]], None] | None = None) -> tuple[ActorCritic, list[dict[str, float]]]:
    """Train on len(env_fns) envs stepped in lock-step. Returns the network and one stats row per update."""
    cfg = cfg or Config()
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    envs = [f() for f in env_fns]
    n, d = len(envs), envs[0].observation_space.shape[0]
    net = ActorCritic(d, int(envs[0].action_space.n), cfg.hidden)
    opt = torch.optim.Adam(net.parameters(), lr=cfg.learning_rate, eps=1e-5)
    obs = torch.as_tensor(np.stack([e.reset(seed=1000 * seed + i)[0] for i, e in enumerate(envs)]))
    T = cfg.n_steps
    buf_obs = torch.zeros((T, n, d))
    buf_mask = torch.zeros((T, n, int(envs[0].action_space.n)), dtype=torch.bool)
    buf_act, buf_logp, buf_rew, buf_done, buf_val = (torch.zeros((T, n)) for _ in range(5))
    ep_return, finished = np.zeros(n), []
    history: list[dict[str, float]] = []
    steps = 0
    while steps < total_steps:
        for t in range(T):
            mask = torch.as_tensor(np.stack([e.action_masks() for e in envs]))
            with torch.no_grad():
                dist = net.dist(obs, mask)
                action = dist.sample()
                buf_logp[t], buf_val[t] = dist.log_prob(action), net.value(obs)
            buf_obs[t], buf_mask[t], buf_act[t] = obs, mask, action
            nxt = []
            for i, e in enumerate(envs):
                o, r, term, trunc, _ = e.step(int(action[i]))
                if trunc and not term:  # time limit, not a real end: bootstrap like SB3
                    with torch.no_grad():
                        r += cfg.gamma * float(net.value(torch.as_tensor(o)))
                ep_return[i] += r
                if term or trunc:
                    finished.append(ep_return[i])
                    ep_return[i] = 0.0
                    o, _ = e.reset(seed=int(rng.integers(2**31)))
                buf_rew[t, i], buf_done[t, i] = r, float(term or trunc)
                nxt.append(o)
            obs = torch.as_tensor(np.stack(nxt))
        steps += T * n
        with torch.no_grad():
            adv, ret = compute_gae(buf_rew, buf_val, buf_done, net.value(obs), cfg.gamma, cfg.gae_lambda)
        stats = _update(net, opt, cfg, rng, buf_obs.reshape(T * n, d), buf_mask.reshape(T * n, -1),
                        buf_act.reshape(-1), buf_logp.reshape(-1), adv.reshape(-1), ret.reshape(-1))
        stats |= {"steps": steps, "episodes": len(finished),
                  "ep_reward": float(np.mean(finished[-100:])) if finished else float("nan")}
        history.append(stats)
        if log:
            log(stats)
    return net, history


def _update(net: ActorCritic, opt: torch.optim.Optimizer, cfg: Config, rng: np.random.Generator,
            obs: torch.Tensor, mask: torch.Tensor, act: torch.Tensor, old_logp: torch.Tensor,
            adv: torch.Tensor, ret: torch.Tensor) -> dict[str, float]:
    clipfrac, approx_kl, pg_l, v_l, ent = [], [], [], [], []
    for _ in range(cfg.n_epochs):
        for idx in np.array_split(rng.permutation(len(obs)), max(1, len(obs) // cfg.batch_size)):
            i = torch.as_tensor(idx)
            dist = net.dist(obs[i], mask[i])
            logp = dist.log_prob(act[i])
            a = adv[i]
            a = (a - a.mean()) / (a.std() + 1e-8)
            pg = clipped_policy_loss(logp, old_logp[i], a, cfg.clip)
            vloss = ((net.value(obs[i]) - ret[i]) ** 2).mean()
            entropy = dist.entropy().mean()
            loss = pg - cfg.ent_coef * entropy + cfg.vf_coef * vloss
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), cfg.max_grad_norm)
            opt.step()
            with torch.no_grad():
                log_ratio = logp - old_logp[i]
                approx_kl.append(float(((log_ratio.exp() - 1) - log_ratio).mean()))
                clipfrac.append(float(((log_ratio.exp() - 1).abs() > cfg.clip).float().mean()))
            pg_l.append(pg.item())
            v_l.append(vloss.item())
            ent.append(entropy.item())
    return {"pg_loss": float(np.mean(pg_l)), "v_loss": float(np.mean(v_l)), "entropy": float(np.mean(ent)),
            "approx_kl": float(np.mean(approx_kl)), "clipfrac": float(np.mean(clipfrac))}
