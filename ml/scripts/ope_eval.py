"""Stage 5.4: off-policy evaluation checked against the simulator's ground truth.

Run from ml/:  uv run --group train --group forecast python scripts/ope_eval.py --procs 4

Behaviour data: random-valid play (mu(a|s) = 1 / number of valid actions, known exactly from the mask) on the
published hard test split (results/ppo_pm_hard.json ``test_world_order``), --log-runs episodes per world.
Targets, from closest to the behaviour to farthest: random (on-policy sanity), epsilon-greedy PPO (eps 0.5, 0.2),
greedy PPO (hard checkpoint s0, sha256 checked) and always-wait (action 0). Truth: each target played on-policy
on the same worlds with disjoint seeds, --truth-runs episodes per world. Estimators (fundforge_ml.ope): PDIS,
WPDIS and FQE with a LightGBM regressor. 95% intervals bootstrap whole worlds; FQE's interval resamples
start-state values from one fitted model, so it omits model-fit variance.
"""

import argparse
import functools
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import torch
from eval_ppo import ML, _git, _model, build

from fundforge_ml.env import FundForgeEnv
from fundforge_ml.ope import Step, ess, fqe, pdis, ratios

CHECKPOINT = "ppo_pm_hard_lr1e-4_ent0.01_s0.zip"
TARGETS = ("random", "ppo_eps0.5", "ppo_eps0.2", "ppo_greedy", "wait")
_MODEL: Any = None


def model() -> Any:
    global _MODEL
    if _MODEL is None:
        torch.set_num_threads(1)
        _MODEL = _model(str(ML / "results" / CHECKPOINT))
    return _MODEL


def probs(target: str, obs: np.ndarray, mask: np.ndarray) -> np.ndarray:
    uniform = mask / mask.sum()
    if target == "random":
        return uniform
    one = np.zeros(len(mask))
    if target == "wait":
        one[0] = 1.0
        return one
    a, _ = model().predict(obs, deterministic=True, action_masks=mask)
    one[int(a)] = 1.0
    eps = {"ppo_greedy": 0.0, "ppo_eps0.5": 0.5, "ppo_eps0.2": 0.2}[target]
    return (1 - eps) * one + eps * uniform


def episode(job: tuple[str, str, str, int]) -> tuple[tuple[str, str, str, int], list[Step]]:
    """One episode of ``policy`` (behaviour = "random"); every step keeps obs, action, reward, mask, mu."""
    seed, variant, policy, rng_seed = job
    w = build(seed, "hard", variant)
    env = FundForgeEnv("pm", policy_id=policy, world_fn=lambda o, r: w)
    obs, info = env.reset(seed=rng_seed, options={"episode_tag": f"{policy}-{rng_seed}"})
    rng, steps, done = np.random.default_rng(rng_seed), [], False
    while not done:
        mask = np.asarray(info["action_mask"], dtype=bool)
        p = probs(policy, obs, mask)
        a = int(rng.choice(len(p), p=p))
        nxt, r, term, trunc, info = env.step(a)
        steps.append(Step(obs.astype(np.float32), a, float(r), mask, 1.0 / mask.sum()))
        obs, done = nxt, term or trunc
    return job, steps


def boot(per_world: dict[str, list[float]], rng: np.random.Generator, n: int = 2000) -> list[float]:
    vals = [np.mean(v) for v in per_world.values()]
    draws = rng.integers(0, len(vals), (n, len(vals)))
    means = np.asarray(vals)[draws].mean(axis=1)
    return [round(float(np.quantile(means, 0.025)), 4), round(float(np.quantile(means, 0.975)), 4)]


def main() -> dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--log-runs", type=int, default=10)
    ap.add_argument("--truth-runs", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=str(ML / "results" / "ope.json"))
    a = ap.parse_args()
    src = json.loads((ML / "results" / "ppo_pm_hard.json").read_text(encoding="utf-8"))
    sha = next(r["sha256"] for r in src["grid"]["lr1e-4_ent0.01"]["runs"] if r["seed"] == 0)
    if hashlib.sha256((ML / "results" / CHECKPOINT).read_bytes()).hexdigest() != sha:
        raise SystemExit(f"{CHECKPOINT} does not match ppo_pm_hard.json")
    ws = [tuple(x.split("/")) for x in src["test_world_order"]]
    ws = ws[: a.limit] if a.limit else ws
    t0 = time.perf_counter()
    log_jobs = [(s, v, "random", 10_000 + k) for s, v in ws for k in range(a.log_runs)]
    truth_jobs = [(s, v, t, 20_000 + k) for t in TARGETS for s, v in ws for k in range(a.truth_runs)]
    with ProcessPoolExecutor(a.procs) as pool:
        logged = dict(pool.map(episode, log_jobs, chunksize=8))
        truth_eps = dict(pool.map(episode, truth_jobs, chunksize=8))
    episodes = [logged[j] for j in log_jobs]
    world_of = [f"{j[0]}/{j[1]}" for j in log_jobs]
    rng = np.random.default_rng(20261118)
    out: dict[str, Any] = {}
    for t in TARGETS:
        pi = functools.lru_cache(maxsize=None)(lambda ob, mk, t=t: probs(t, np.frombuffer(ob, np.float32),
                                                                     np.frombuffer(mk, bool)))

        def p(obs: np.ndarray, mask: np.ndarray, pi: Any = pi) -> np.ndarray:
            return pi(obs.astype(np.float32).tobytes(), mask.astype(bool).tobytes())

        truth: dict[str, list[float]] = {}
        for j in truth_jobs:
            if j[2] == t:
                truth.setdefault(f"{j[0]}/{j[1]}", []).append(sum(s.reward for s in truth_eps[j]))
        rho = ratios(episodes, p)
        est: dict[str, Any] = {}
        for name, weighted in (("pdis", False), ("wpdis", True)):
            per_world: dict[str, list[float]] = {}
            for i, w in enumerate(world_of):
                per_world.setdefault(w, []).append(i)
            point = pdis(episodes, rho, weighted)
            keys = list(per_world)  # world bootstrap of the estimator itself
            reps = []
            for _ in range(300):
                pick = [i for k in rng.choice(keys, len(keys)) for i in per_world[k]]
                reps.append(pdis([episodes[i] for i in pick], [rho[i] for i in pick], weighted))
            est[name] = {"value": round(point, 4), "ci95": [round(float(np.quantile(reps, 0.025)), 4),
                                                             round(float(np.quantile(reps, 0.975)), 4)]}
        rounds = max(len(e) for e in episodes)
        v, starts = fqe(episodes, p, 46, lambda: lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05,
                                                                     verbose=-1), rounds)
        fq: dict[str, list[float]] = {}
        for w, sv in zip(world_of, starts, strict=True):
            fq.setdefault(w, []).append(float(sv))
        est["fqe"] = {"value": round(v, 4), "ci95": boot(fq, rng), "rounds": rounds}
        true_v = float(np.mean([np.mean(x) for x in truth.values()]))
        out[t] = {"truth": {"value": round(true_v, 4), "ci95": boot(truth, rng)},
                  "ess_full_episode": round(ess(rho), 1), "logged_episodes": len(episodes),
                  **{k: {**e, "error": round(e["value"] - true_v, 4),
                         "covers_truth": e["ci95"][0] <= true_v <= e["ci95"][1]} for k, e in est.items()}}
        print(f"{t:11s} truth {true_v:7.3f} | pdis {est['pdis']['value']:8.3f} wpdis {est['wpdis']['value']:8.3f} "
              f"fqe {est['fqe']['value']:7.3f} | ESS {out[t]['ess_full_episode']}", flush=True)
    doc = {
        "stage": "5.4 off-policy evaluation vs simulator truth",
        "commit": _git("rev-parse", "HEAD"), "dirty": bool(_git("status", "--porcelain", "--", "src", "scripts")),
        "reproduce": f"cd ml && uv run --group train --group forecast python scripts/ope_eval.py --procs {a.procs}",
        "method": __doc__.split("\n\n", 2)[2].strip(),
        "scale": {"worlds": len(ws), "log_runs_per_world": a.log_runs, "truth_runs_per_world": a.truth_runs,
                  "checkpoint": CHECKPOINT, "level": "hard", "gamma": 1.0},
        "targets": out,
        "wall_seconds": round(time.perf_counter() - t0, 1),
    }
    Path(a.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc


if __name__ == "__main__":
    main()
