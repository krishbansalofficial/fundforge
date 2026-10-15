"""FundForgeEnv: one partner seat as a Gymnasium environment (ML_CONTRACTS.md section 2).

The agent plays one seat and the deterministic ``bot:v1`` plays the other, through ordinary
``Session.handle`` commands: the same roles, package digests, countersignatures, mandate checks
and logs as a human. The agent never touches the engine. Its observation is built only from
``contracts.observe`` (the partner's as-of view), and the action mask only from that observation.

One step is one decision point: the agent takes zero or one material action, then marks ready
(voting to skip quiet windows); the bot countersigns, readies and time advances. Trades are
proposed as joint packages so the partner's signature is always required. A command the engine
still rejects is a normal outcome: nothing changes and ``info["reject"]`` says why.

Reward (``REWARD_VERSION``): zero until the run finishes, then the engine's own score (excess
return over the passive opening book, minus forced-action penalties) in percent, plus a tier
bonus. Optional dense shaping adds the change in observed NAV, in percent of opening NAV.
"""

import hashlib
import math
from collections.abc import Callable
from typing import Any

import gymnasium as gym
import numpy as np
import numpy.typing as npt
from fundforge import bot
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session

from . import worlds
from .contracts import SEATS, hidden_paths, observe
from .encoding import ENCODER_VERSION, LIVE, encode, layout_for

ACTION_VERSION = "actions-v1"
REWARD_VERSION = "reward-v1"
FRACTIONS = (0.25, 0.5, 1.0)
TIER_BONUS = {"WIN": 5.0, "SURVIVAL": 0.0, "DISTRESS": -10.0}
USERS = {"pm": "agent-pm", "mp": "agent-mp"}
MAX_STEPS = 400  # far above any Case1 run; a stuck run is truncated, not looped forever

WorldFn = Callable[[dict[str, Any], np.random.Generator], worlds.World]


def default_world(options: dict[str, Any], rng: np.random.Generator) -> worlds.World:
    names = worlds.variant_names()
    variant = options.get("variant") or names[int(rng.integers(len(names)))]
    return worlds.world(options.get("gen_seed"), variant, bool(options.get("gate", True)))


class FundForgeEnv(gym.Env[npt.NDArray[np.float32], int]):
    metadata = {"render_modes": []}  # noqa: RUF012

    def __init__(self, role: str = "pm", *, shaping: bool = False, policy_id: str = "agent",
                 world_fn: WorldFn = default_world) -> None:
        if role not in SEATS:
            raise ValueError(f"role must be one of {SEATS}")
        self.role, self.partner = role, next(r for r in SEATS if r != role)
        self.user, self.partner_user = USERS[role], f"bot:{self.partner}"
        self.shaping, self.policy_id, self.world_fn = shaping, policy_id, world_fn
        raw = worlds.skeleton()
        self.topics = tuple(sorted(raw["research"]["assignments"]))
        self.layout = layout_for(raw, self.topics)
        self.actions: list[tuple[str, Any]] = [("wait", None)]
        self.actions += [("reduce", (s, f)) for s in self.layout.instruments for f in FRACTIONS]
        self.actions += [("research", t) for t in self.topics]
        self.actions += [("share", t) for t in self.topics]
        self.actions += [("accept_replacement", None)]
        self.action_space: gym.spaces.Discrete = gym.spaces.Discrete(len(self.actions))  # type: ignore[assignment]
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (self.layout.size,), np.float32)
        self.s: Session | None = None

    # ---------- gym API ----------
    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None
              ) -> tuple[npt.NDArray[np.float32], dict[str, Any]]:
        super().reset(seed=seed)
        options = dict(options or {})
        self.world = self.world_fn(options, self.np_random)
        if set(self.world.tape.raw["instruments"]) != set(self.layout.instruments):
            raise ValueError("world instruments differ from the encoder layout")
        e = Engine(self.world.tape)
        e.advance()
        partners = {self.role: self.user, self.partner: self.partner_user}
        self.s = Session(e, partners, bots=frozenset({self.partner}))
        tag = str(options.get("episode_tag", "0"))
        self.episode_id = hashlib.sha256(
            f"{self.world.seed_family}|{self.world.variant}|{self.policy_id}|{tag}|{ENCODER_VERSION}|"
            f"{ACTION_VERSION}|{REWARD_VERSION}".encode()).hexdigest()
        self.steps = 0
        self._bot("open")
        self.view = observe(self.s, self.user)
        self.opening = self.view
        self.last_nav = float(self.view["fund"]["nav"])
        return self._obs(), self._info(None)

    def step(self, action: int) -> tuple[npt.NDArray[np.float32], float, bool, bool, dict[str, Any]]:
        if self.s is None:
            raise RuntimeError("call reset() first")
        if self.s.e.finished():
            raise RuntimeError("episode finished; call reset()")
        s = self.s
        self.steps += 1
        reject = None
        cmd = self._command(int(action))
        if cmd is not None:
            try:
                self._send(cmd)
            except CommandRejected as ex:
                reject = str(ex)
        self._bot("sign")  # the partner reviews any package before time moves
        cursor = s.e.cursor
        try:
            self._send({"type": "ready", "version": s.version, "skip": True})
        except CommandRejected:  # e.g. a package the partner refused is still pending: no skip
            self._send({"type": "ready", "version": s.version})
        self._bot("ready")
        if s.e.cursor == cursor and not s.e.finished():
            raise RuntimeError("time did not advance after both seats were ready")
        self.view = observe(s, self.user)
        nav = float(self.view["fund"]["nav"])
        reward = 0.0
        if self.shaping:
            reward += (nav - self.last_nav) / float(self.opening["fund"]["nav"]) * 100.0
        self.last_nav = nav
        terminated = s.e.finished()
        truncated = not terminated and self.steps >= MAX_STEPS
        info = self._info(reject)
        if terminated:
            outcome = self.view["outcome"]
            reward += float(outcome["score"]) / 100.0 + TIER_BONUS[outcome["label"]]
            info["outcome"] = outcome
            info["journal_digest"] = outcome["journal_digest"]
        return self._obs(), reward, terminated, truncated, info

    # ---------- masks ----------
    def action_masks(self) -> npt.NDArray[np.bool_]:
        """Valid actions, from the observation and public rules only (sb3-contrib MaskablePPO API)."""
        v = self.view
        pos = {p["sym"]: p["qty"] for p in v["positions"]}
        live = {o["sym"] for o in v["orders"] if o["status"] in LIVE}
        research = v["research"]
        mine_used = [u for u in research["used"] if u.get("owner") == self.role]
        committed = v["attention"]["committed"]
        mask = np.zeros(len(self.actions), dtype=bool)
        for i, (kind, arg) in enumerate(self.actions):
            if kind == "wait":
                ok = True
            elif kind == "reduce":
                sym, frac = arg
                ok = pos.get(sym, 0) != 0 and sym not in live and self._qty(pos[sym], frac) > 0
            elif kind == "research":
                ok = (arg in research["topics"] and not committed and len(mine_used) < research["budget"]
                      and all(u["topic"] != arg for u in mine_used))
            elif kind == "share":
                ok = arg not in research["shared"] and any(
                    u["topic"] == arg and u["reveal_day"] <= v["clock"]["day"] for u in mine_used)
            else:  # accept_replacement
                r = v["recall"]
                ok = self.role == "mp" and r["offer_visible"] and not r["replacement_accepted"] and bool(r["open"])
            mask[i] = ok
        return mask

    # ---------- internals ----------
    @staticmethod
    def _qty(position: int, frac: float) -> int:
        return math.ceil(abs(position) * frac)

    def _command(self, action: int) -> dict[str, Any] | None:
        kind, arg = self.actions[action]
        if kind == "wait":
            return None
        if kind == "reduce":
            sym, frac = arg
            q = next((p["qty"] for p in self.view["positions"] if p["sym"] == sym), 0)
            pid = f"{self.episode_id[:12]}-{self.steps}"
            side = "SELL" if q > 0 else "COVER"
            return {"type": "propose", "package_id": pid,
                    "orders": [{"order_id": f"{pid}-{sym}", "sym": sym, "side": side, "qty": self._qty(q, frac)}]}
        if kind == "research":
            return {"type": "research", "topic": arg}
        if kind == "share":
            return {"type": "share_research", "topic": arg}
        return {"type": "accept_replacement"}

    def _send(self, cmd: dict[str, Any]) -> dict[str, Any]:
        assert self.s is not None
        self._n = getattr(self, "_n", 0) + 1
        key = f"{self.episode_id}:{self.role}:{self.steps}:{self._n}"  # ML_CONTRACTS idempotency keys
        return self.s.handle(self.user, key, cmd)

    def _bot(self, stage: str) -> None:
        assert self.s is not None
        bot.act(self.s, self.partner, self.partner_user, f"{self.episode_id[:12]}-{self.steps}-{stage}")

    def _obs(self) -> npt.NDArray[np.float32]:
        return encode(self.view, self.layout, self.opening)

    def _info(self, reject: str | None) -> dict[str, Any]:
        info: dict[str, Any] = {"reject": reject, "action_mask": self.action_masks(),
                                "day": self.view["clock"]["day"], "phase": self.view["clock"]["phase"],
                                "episode_id": self.episode_id}
        leaks = list(hidden_paths({k: v for k, v in info.items() if k != "action_mask"}))
        if leaks:
            raise AssertionError(f"hidden keys in info: {leaks}")
        return info
