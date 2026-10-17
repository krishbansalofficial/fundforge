"""Evaluate trained MaskablePPO seats on held-out worlds against baselines, and run the two-seat check.

Run from ml/ (training venv, see docs/ML_RL.md):
    uv run --group train python scripts/eval_seats.py --split test --models results/ppo_pm_s0.zip ...

Single seat (one agent seat, bot:v1 plays the other through ordinary commands):
  ``ppo``      MaskablePPO, deterministic, masked.
  ``random``   uniform over masked-valid actions, 5 seeds per world.
  ``wait``     always waits (the partner bot still does its own duties).
  ``bot_seat`` the hand-written bot:v1 rules play the agent's own seat.

Two seat (the PM seat and the MP seat both driven by a model, no bot seat):
  ``ppo_pm+ppo_mp``   PPO-PM with PPO-MP as partner. Compared with ``ppo_pm+bot:v1``, the single-seat
  ``ppo`` row for the same PM model. Both seats use the same observation, mask and command path as
  the single seat. Countersigning and statement resolution are performed by a minimal duty step
  (``duties``) for both seats; the bot's research, sharing and replacement choices are not used,
  so those are decided by the model. ``duties`` is a documented simplification.

Statistics: each world's reward is the mean over its runs. Intervals are percentile bootstraps over
seed FAMILIES (both variants of a family stay together) with 10,000 resamples and a fixed RNG seed.
"""

import argparse
import contextlib
import hashlib
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from fundforge import bot
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from sb3_contrib import MaskablePPO

from fundforge_ml import worlds
from fundforge_ml.contracts import observe
from fundforge_ml.env import MAX_STEPS, USERS, FundForgeEnv

ML = Path(__file__).parents[1]
RESULTS = ML / "results"
RANDOM_RUNS = 5
BOOT = 10_000


def _world(seed: str, variant: str) -> worlds.World:
    return worlds.world(seed, variant, gate=False)


def play_single(
    role: str, seed: str, variant: str, policy: str, model: MaskablePPO | None, rng_seed: int
) -> dict[str, Any]:
    env = FundForgeEnv(role, policy_id=policy, world_fn=lambda o, r: _world(seed, variant))
    obs, info = env.reset(seed=rng_seed, options={"episode_tag": f"{policy}-{rng_seed}"})
    rng = np.random.default_rng(rng_seed)
    total, done, k = 0.0, False, 0
    while not done:
        k += 1
        if policy == "ppo":
            assert model is not None
            a, _ = model.predict(obs, deterministic=True, action_masks=env.action_masks())
            a = int(a)
        elif policy == "random":
            a = int(rng.choice(np.flatnonzero(info["action_mask"])))
        elif policy == "bot_seat":
            assert env.s is not None
            bot.act(env.s, role, env.user, f"seat-{k}")
            env.view = env.s.view(env.user)
            a = 0
        else:  # wait
            a = 0
        obs, r, term, trunc, info = env.step(a)
        total += r
        done = term or trunc
    out = info.get("outcome")
    if out is None:  # stalled or truncated: no terminal reward, as the env gives none
        return {"reward": total, "score": float("nan"), "label": "STALLED" if info.get("stalled") else "TRUNCATED"}
    return {"reward": total, "score": float(out["score"]), "label": out["label"]}


def duties(s: Session, role: str, user: str, key: str) -> None:
    """Countersign the partner's packages and resolve broker statements; nothing economic."""
    e = s.e
    for p in list(s.packages.values()):
        if p.status == "PENDING_APPROVAL" and p.proposer != role and p.kind != "gate":
            with contextlib.suppress(CommandRejected):
                s.handle(
                    user, f"{key}-sign-{p.package_id}", {"type": "sign", "package_id": p.package_id, "digest": p.digest}
                )
    if role == "mp" and e.at_barrier():
        for issue in e.broker.queue(e.ev.date):
            if issue["can_resolve"]:
                with contextlib.suppress(CommandRejected):
                    s.handle(
                        user,
                        f"{key}-resolve-{issue['id']}",
                        {
                            "type": "resolve_statement",
                            "statement_id": issue["id"],
                            "revision": issue["revision"],
                            "version": s.version,
                        },
                    )


def _seat_env(role: str, s: Session, world: worlds.World, episode_id: str) -> FundForgeEnv:
    """A FundForgeEnv used only as a seat's observation, mask and command builder over a shared session."""
    env = FundForgeEnv(role, world_fn=lambda o, r: world)
    env.s, env.world, env.episode_id, env.steps = s, world, episode_id, 0
    env.user = USERS[role]
    env.view = observe(s, env.user)
    env.opening = env.view
    return env


def play_two(pm_model: MaskablePPO, mp_model: MaskablePPO, seed: str, variant: str, rng_seed: int) -> dict[str, Any]:
    world = _world(seed, variant)
    e = Engine(world.tape)
    e.advance()
    s = Session(e, {"pm": USERS["pm"], "mp": USERS["mp"]})
    episode_id = hashlib.sha256(f"two|{seed}|{variant}|{rng_seed}".encode()).hexdigest()
    seats = {
        "pm": (_seat_env("pm", s, world, episode_id), pm_model),
        "mp": (_seat_env("mp", s, world, episode_id), mp_model),
    }
    duties(s, "pm", USERS["pm"], f"{episode_id[:12]}-open")
    duties(s, "mp", USERS["mp"], f"{episode_id[:12]}-open")
    steps, stuck = 0, False
    while not s.e.finished() and steps < MAX_STEPS:
        steps += 1
        for _role, (env, model) in seats.items():
            env.steps = steps
            env.view = observe(s, env.user)
            obs = env._obs()
            a, _ = model.predict(obs, deterministic=True, action_masks=env.action_masks())
            cmd = env._command(int(a))
            if cmd is not None:
                with contextlib.suppress(CommandRejected):  # all-or-nothing: unchanged, as with the single seat
                    env._send(cmd)
        for role in ("pm", "mp"):
            duties(s, role, USERS[role], f"{episode_id[:12]}-{steps}")
        cursor = s.e.cursor
        try:
            s.handle(
                USERS["pm"],
                f"{episode_id[:12]}-{steps}-pm-ready",
                {"type": "ready", "version": s.version, "skip": True},
            )
        except CommandRejected:
            s.handle(USERS["pm"], f"{episode_id[:12]}-{steps}-pm-ready2", {"type": "ready", "version": s.version})
        try:
            s.handle(
                USERS["mp"],
                f"{episode_id[:12]}-{steps}-mp-ready",
                {"type": "ready", "version": s.version, "skip": True},
            )
        except CommandRejected:
            s.handle(USERS["mp"], f"{episode_id[:12]}-{steps}-mp-ready2", {"type": "ready", "version": s.version})
        if s.e.cursor == cursor and not s.e.finished():
            stuck = True
            break
    if not s.e.finished():
        return {"reward": 0.0, "score": float("nan"), "label": "STALLED" if stuck else "TRUNCATED", "stuck": stuck}
    out = observe(s, USERS["pm"])["outcome"]
    return {
        "reward": float(out["score"]) / 100.0 + {"WIN": 5.0, "SURVIVAL": 0.0, "DISTRESS": -10.0}[out["label"]],
        "score": float(out["score"]),
        "label": out["label"],
        "stuck": stuck,
    }


def family_bootstrap(per_family: dict[str, list[float]], seed: int = 0) -> dict[str, float]:
    """Percentile 95% CI of the mean over families, resampling families with replacement."""
    fams = list(per_family)
    means = np.array([statistics.fmean(per_family[f]) for f in fams])
    rng = np.random.default_rng(seed)
    idx = rng.integers(len(fams), size=(BOOT, len(fams)))
    boot = means[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"lo": round(float(lo), 3), "hi": round(float(hi), 3)}


def summarize(rows: list[dict[str, Any]], per_world: dict[str, list[float]]) -> dict[str, Any]:
    rewards = [r["reward"] for r in rows]
    scores = [r["score"] for r in rows if r["score"] == r["score"]]  # finished runs only (NaN = stalled)
    return {
        "n_runs": len(rows),
        "n_worlds": len(per_world),
        "n_families": len({k.split("/")[0] for k in per_world}),
        "mean_reward": round(statistics.fmean(rewards), 3),
        "std_reward": round(statistics.stdev(rewards), 3) if len(rewards) > 1 else 0.0,
        "ci95_family_bootstrap": family_bootstrap(_by_family(per_world)),
        "mean_score_bps": round(statistics.fmean(scores), 1),
        "labels": dict(Counter(r["label"] for r in rows)),
    }


def _by_family(per_world: dict[str, list[float]]) -> dict[str, list[float]]:
    fams: dict[str, list[float]] = {}
    for key, vals in per_world.items():
        fams.setdefault(key.split("/")[0], []).extend(vals)
    return fams


def evaluate(role: str, model: MaskablePPO, pairs: list[tuple[str, str]], policies: tuple[str, ...]) -> dict[str, Any]:
    """Single-seat rows for the given policies over (family, variant) pairs."""
    report: dict[str, Any] = {}
    for policy in policies:
        rows: list[dict[str, Any]] = []
        per_world: dict[str, list[float]] = {}
        for seed, variant in pairs:
            runs = range(RANDOM_RUNS) if policy == "random" else range(1)
            got = [play_single(role, seed, variant, policy, model, k) for k in runs]
            rows += got
            per_world[f"{seed}/{variant}"] = [g["reward"] for g in got]
        report[policy] = summarize(rows, per_world)
    return report


def evaluate_two(pm_model: MaskablePPO, mp_model: MaskablePPO, pairs: list[tuple[str, str]]) -> dict[str, Any]:
    rows, per_world, stuck = [], {}, 0
    for seed, variant in pairs:
        r = play_two(pm_model, mp_model, seed, variant, 0)
        stuck += int(r.get("stuck", False))
        rows.append(r)
        per_world[f"{seed}/{variant}"] = [r["reward"]]
    rep = summarize(rows, per_world)
    rep["stuck_runs"] = stuck
    return rep


def pairs_of(split: str, families: dict[str, list[str]]) -> list[tuple[str, str]]:
    return [(s, v) for s in families[split] for v in worlds.variant_names()]


def load_model(path: Path) -> MaskablePPO:
    return MaskablePPO.load(path, device="cpu")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["val", "test"])
    ap.add_argument("--families", type=int, default=400)
    ap.add_argument("--pm", type=Path, help="PM model zip")
    ap.add_argument("--mp", type=Path, help="MP model zip (for the two-seat check)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--policies", default="ppo,random,wait,bot_seat")
    args = ap.parse_args()
    sys.path.insert(0, str(ML / "scripts"))
    from train_ppo import load_splits  # the cached split is the single source of truth

    split = load_splits(args.families)
    pairs = pairs_of(args.split, split["splits"])
    t0 = time.perf_counter()
    result: dict[str, Any] = {
        "split": args.split,
        "families_drawn": args.families,
        "split_sizes": split["counts"],
        "n_worlds": len(pairs),
        "worlds": [f"{s}/{v}" for s, v in pairs],
        "models": {},
    }
    if args.pm:
        pm = load_model(args.pm)
        result["models"]["pm"] = {"file": args.pm.name, "sha256": hashlib.sha256(args.pm.read_bytes()).hexdigest()}
        result["single_seat_pm"] = evaluate("pm", pm, pairs, tuple(args.policies.split(",")))
    if args.mp:
        mp = load_model(args.mp)
        result["models"]["mp"] = {"file": args.mp.name, "sha256": hashlib.sha256(args.mp.read_bytes()).hexdigest()}
        result["single_seat_mp"] = evaluate("mp", mp, pairs, tuple(args.policies.split(",")))
    if args.pm and args.mp:
        result["two_seat"] = {"ppo_pm+ppo_mp": evaluate_two(pm, mp, pairs)}
    result["eval_seconds"] = round(time.perf_counter() - t0, 1)
    result["reproduce"] = "uv run --group train python " + " ".join(sys.argv)
    args.out.parent.mkdir(exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
