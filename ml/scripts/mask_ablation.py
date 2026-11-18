"""Stage 5.6: what does action masking buy? MaskablePPO vs plain PPO that is charged for invalid picks.

Run from ml/:  uv run --group train python scripts/mask_ablation.py --procs 8

Both arms: base level, the same gated train families as ppo_pm.json (re-gated here: the gate is deterministic),
config lr1e-4_ent0.01 with eval_ppo's FIXED params, 4 envs, --steps per run, seeds 0..--seeds-1. The no-mask arm
wraps the env in masking.InvalidActionPenalty (an invalid pick waits and costs PENALTY). Test: the published base
test split (ppo_pm.json test_world_order), deterministic policies. Reports evals summaries, the paired
masked - penalty comparison, invalid-pick rates and whether the masked arm reproduces the published checkpoints'
sha256. Writes results/mask_ablation.json.
"""

import argparse
import hashlib
import json
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import torch
from eval_ppo import FIXED, GRID, ML, _git, build, gate
from sb3_contrib import MaskablePPO
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from train_ppo import make_env

from fundforge_ml import evals, worlds
from fundforge_ml.env import FundForgeEnv
from fundforge_ml.masking import PENALTY, InvalidActionPenalty

CONFIG = "lr1e-4_ent0.01"


def _penalised(role: str, seeds: list[str], rank: int):  # type: ignore[no-untyped-def]
    inner = make_env(role, seeds, rank)
    return lambda: InvalidActionPenalty(inner())


def train(job: tuple[str, int, list[str], int, str]) -> dict[str, Any]:
    arm, seed, train_seeds, steps, out = job
    torch.set_num_threads(1)
    factory = make_env if arm == "masked" else _penalised
    venv = DummyVecEnv([factory("pm", train_seeds, 1000 * seed + i) for i in range(4)])
    cls = MaskablePPO if arm == "masked" else PPO
    model = cls("MlpPolicy", venv, n_steps=FIXED["n_steps"], batch_size=FIXED["batch_size"], gamma=FIXED["gamma"],
                policy_kwargs={"net_arch": FIXED["net_arch"]}, seed=seed, verbose=0, device="cpu", **GRID[CONFIG])
    t = time.perf_counter()
    model.learn(total_timesteps=steps)
    path = Path(out) / f"mask_ablation_{arm}_s{seed}.zip"
    model.save(path)
    return {"arm": arm, "seed": seed, "path": str(path), "seconds": round(time.perf_counter() - t, 1),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def evaluate(job: tuple[str, str, str, str]) -> tuple[tuple[str, str, str, str], dict[str, Any]]:
    arm, path, seed, variant = job
    torch.set_num_threads(1)
    model = (MaskablePPO if arm == "masked" else PPO).load(path, device="cpu")
    w = build(seed, "base", variant)
    env = FundForgeEnv("pm", policy_id=f"ablation-{arm}", world_fn=lambda o, r: w)
    obs, info = env.reset(seed=0, options={"episode_tag": f"{arm}-{Path(path).stem}"})
    total, invalid, steps, done = 0.0, 0, 0, False
    while not done:
        mask = env.action_masks()
        if arm == "masked":
            a, _ = model.predict(obs, deterministic=True, action_masks=mask)
        else:
            a, _ = model.predict(obs, deterministic=True)
        invalid += not bool(mask[int(a)])
        obs, r, term, trunc, info = env.step(int(a))
        total, steps, done = total + r, steps + 1, term or trunc
    return job, {"reward": total, "label": info["outcome"]["label"], "invalid": invalid, "steps": steps}


def main() -> dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--steps", type=int, default=200_000)
    ap.add_argument("--families", type=int, default=2800)
    ap.add_argument("--out", default=str(ML / "results"))
    a = ap.parse_args()
    src = json.loads((ML / "results" / "ppo_pm.json").read_text(encoding="utf-8"))
    published = {r["seed"]: r["sha256"] for r in src["grid"][CONFIG]["runs"]}
    test_ws = [tuple(x.split("/")) for x in src["test_world_order"]]
    t0 = time.perf_counter()
    with ProcessPoolExecutor(a.procs) as pool:
        gated = list(pool.map(gate, [("base", f"ppo-{i}") for i in range(a.families)], chunksize=8))
        train_seeds = [s for _, s, sp, f in gated if sp == "train" and not f]
        runs = list(pool.map(train, [(arm, k, train_seeds, a.steps, a.out) for arm in ("masked", "penalty")
                                     for k in range(a.seeds)]))
        jobs = [(r["arm"], r["path"], s, v) for r in runs for s, v in test_ws]
        played = dict(pool.map(evaluate, jobs, chunksize=8))
    arms: dict[str, Any] = {}
    reward = {}
    for arm in ("masked", "penalty"):
        rs = [r for r in runs if r["arm"] == arm]
        m = np.array([[played[(arm, r["path"], s, v)]["reward"] for s, v in test_ws] for r in rs])
        reward[arm] = m
        eps = [played[(arm, r["path"], s, v)] for r in rs for s, v in test_ws]
        arms[arm] = {**evals.summary(m), "labels": dict(Counter(e["label"] for e in eps)),
                     "invalid_pick_rate": round(sum(e["invalid"] for e in eps) / sum(e["steps"] for e in eps), 4),
                     "runs": rs}
    arms["masked"]["reproduces_published_sha256"] = {r["seed"]: r["sha256"] == published.get(r["seed"])
                                                     for r in arms["masked"]["runs"]}
    doc = {
        "stage": "5.6 masking ablation", "commit": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", "src", "scripts")),
        "reproduce": f"cd ml && uv run --group train python scripts/mask_ablation.py --procs {a.procs} "
                     f"--seeds {a.seeds} --steps {a.steps}",
        "scale": {"config": CONFIG, "seeds": a.seeds, "steps": a.steps, "train_families": len(train_seeds),
                  "test_worlds": len(test_ws), "penalty": PENALTY, "variants": worlds.variant_names()},
        "arms": arms,
        "masked_vs_penalty": evals.compare(reward["masked"], reward["penalty"]),
        "wall_seconds": round(time.perf_counter() - t0, 1),
    }
    Path(a.out, "mask_ablation.json").write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("masked_vs_penalty", "wall_seconds")}, default=str))
    return doc


if __name__ == "__main__":
    main()
