"""Reference numbers for FundForgeEnv: speed, gate acceptance, and two non-learned baselines.

Run from ml/:  uv run python scripts/env_baselines.py [--seeds 40] [--episodes 20]

1. Draws generated worlds (seed families ``base-<n>``), keeps those that pass the balance gate
   for both variants, records the rest with their failure codes, and splits families with
   ``split_of`` (only test-split families are used below).
2. Plays two baselines for each seat on those worlds: ``wait`` (never acts; the bot partner
   still handles its own duties) and ``random`` (uniform over masked-valid actions, seeded).
3. Reports env steps per second, mean reward with a 95% normal interval, and outcome labels.
Numbers are for this machine and these seeds only.
"""

import argparse
import statistics
import time
from collections import Counter

import numpy as np

from fundforge_ml import worlds
from fundforge_ml.contracts import split_of
from fundforge_ml.env import FundForgeEnv


def accepted_worlds(n: int) -> tuple[list[str], dict[str, list[str]]]:
    ok, rejected = [], {}
    for i in range(n):
        seed = f"base-{i}"
        try:
            for v in worlds.variant_names():
                worlds.world(seed, v)
            ok.append(seed)
        except worlds.WorldRejected as ex:
            rejected[seed] = ex.failures
    return ok, rejected


def run(role: str, policy: str, seeds: list[str], episodes: int) -> dict[str, object]:
    env = FundForgeEnv(role, policy_id=policy)
    rng = np.random.default_rng(12345)
    rewards, labels, steps = [], Counter(), 0
    t0 = time.perf_counter()
    for k in range(episodes):
        seed = seeds[k % len(seeds)]
        _, info = env.reset(seed=k, options={"gen_seed": seed, "episode_tag": str(k)})
        total, done = 0.0, False
        while not done:
            valid = np.flatnonzero(info["action_mask"])
            a = 0 if policy == "wait" else int(rng.choice(valid))
            _, r, term, trunc, info = env.step(a)
            total += r
            steps += 1
            done = term or trunc
        rewards.append(total)
        labels[info["outcome"]["label"]] += 1
    dt = time.perf_counter() - t0
    mean = statistics.fmean(rewards)
    half = 1.96 * statistics.stdev(rewards) / len(rewards) ** 0.5 if len(rewards) > 1 else 0.0
    return {"role": role, "policy": policy, "episodes": episodes, "mean_reward": round(mean, 2),
            "ci95": round(half, 2), "labels": dict(labels), "steps_per_s": round(steps / dt, 1),
            "steps_per_episode": round(steps / episodes, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--episodes", type=int, default=20)
    args = ap.parse_args()
    t0 = time.perf_counter()
    ok, rejected = accepted_worlds(args.seeds)
    print(f"gate: {len(ok)}/{args.seeds} seed families accepted for both variants "
          f"({time.perf_counter() - t0:.1f}s); rejected: {dict(Counter(f for v in rejected.values() for f in v))}")
    test = [s for s in ok if split_of(worlds.world(s, "base").seed_family) == "test"] or ok
    print(f"test-split families used: {len(test)}")
    for role in ("pm", "mp"):
        for policy in ("wait", "random"):
            print(run(role, policy, test, args.episodes))


if __name__ == "__main__":
    main()
