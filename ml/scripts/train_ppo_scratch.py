"""Stage 2: from-scratch PPO (fundforge_ml.ppo) vs SB3 MaskablePPO on the same worlds and seeds.

Run from ml/:  uv run --group train python scripts/train_ppo_scratch.py --procs 10

Same as ppo_pm.json's chosen config (lr1e-4_ent0.01, eval_ppo FIXED params): base train families from the same
deterministic gate (3000 drawn), 4 envs, --steps per run, seeds 0..--seeds-1. Test: the published base test split
(ppo_pm.json test_world_order), deterministic argmax over valid actions. The SB3 arm replays the published
checkpoints (sha256 checked) on those worlds. Acceptance (docs/ML_SHOWCASE.md): scratch is not worse than SB3
within the bootstrap CI. Writes results/ppo_scratch.json; models go to results/ppo_scratch_s<seed>.pt (git-ignored).
"""

import argparse
import dataclasses
import hashlib
import json
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import torch
from eval_ppo import ML, _git, build, episode, gate
from train_ppo import make_env

from fundforge_ml import evals, ppo
from fundforge_ml.env import FundForgeEnv

CONFIG = "lr1e-4_ent0.01"
CFG = ppo.Config(learning_rate=1e-4, ent_coef=0.01)  # the other defaults equal eval_ppo.FIXED and SB3's


def train(job: tuple[int, list[str], int, str]) -> dict[str, Any]:
    seed, train_seeds, steps, out = job
    torch.set_num_threads(1)
    t = time.perf_counter()
    net, history = ppo.train([make_env("pm", train_seeds, 1000 * seed + i) for i in range(4)], steps, CFG, seed)
    path = Path(out) / f"ppo_scratch_s{seed}.pt"
    torch.save(net.state_dict(), path)
    return {"seed": seed, "path": str(path), "seconds": round(time.perf_counter() - t, 1),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "curve": [{k: round(h[k], 4) for k in ("steps", "ep_reward", "approx_kl", "clipfrac", "entropy")}
                      for h in history[:: max(1, len(history) // 20)]]}


def play_scratch(job: tuple[str, str, str]) -> tuple[tuple[str, str, str], dict[str, Any]]:
    path, seed, variant = job
    torch.set_num_threads(1)
    w = build(seed, "base", variant)
    env = FundForgeEnv("pm", policy_id="ppo-scratch", world_fn=lambda o, r: w)
    obs, info = env.reset(seed=0, options={"episode_tag": f"scratch-{Path(path).stem}"})
    net = ppo.ActorCritic(obs.shape[0], int(env.action_space.n), CFG.hidden)
    net.load_state_dict(torch.load(path, weights_only=True))
    total, done = 0.0, False
    while not done:
        obs, r, term, trunc, info = env.step(net.act(obs, env.action_masks()))
        total, done = total + r, term or trunc
    return job, {"reward": total, "label": info["outcome"]["label"]}


def main() -> dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--steps", type=int, default=200_000)
    ap.add_argument("--families", type=int, default=3000)
    ap.add_argument("--out", default=str(ML / "results"))
    ap.add_argument("--test-worlds", type=int, default=0, help="smoke runs: first N test worlds only (0 = all)")
    a = ap.parse_args()
    src = json.loads((ML / "results" / "ppo_pm.json").read_text(encoding="utf-8"))
    published = {r["seed"]: r["sha256"] for r in src["grid"][CONFIG]["runs"]}
    test_ws = [tuple(x.split("/")) for x in src["test_world_order"]][: a.test_worlds or None]
    sb3 = []
    for k in range(a.seeds):
        path = ML / "results" / f"ppo_pm_{CONFIG}_s{k}.zip"
        if hashlib.sha256(path.read_bytes()).hexdigest() != published[k]:
            raise SystemExit(f"{path} does not match ppo_pm.json")
        sb3.append(str(path))
    t0 = time.perf_counter()
    with ProcessPoolExecutor(a.procs) as pool:
        gated = list(pool.map(gate, [("base", f"ppo-{i}") for i in range(a.families)], chunksize=8))
        train_seeds = [s for _, s, sp, f in gated if sp == "train" and not f]
        runs = list(pool.map(train, [(k, train_seeds, a.steps, a.out) for k in range(a.seeds)]))
        scratch = dict(pool.map(play_scratch, [(r["path"], s, v) for r in runs for s, v in test_ws], chunksize=4))
        sb3_jobs = [((p, s, v), "pm", s, "base", v, "ppo", p, 0) for p in sb3 for s, v in test_ws]
        library = dict(pool.map(episode, sb3_jobs, chunksize=4))
    reward = {"scratch": np.array([[scratch[(r["path"], s, v)]["reward"] for s, v in test_ws] for r in runs]),
              "sb3": np.array([[library[(p, s, v)]["reward"] for s, v in test_ws] for p in sb3])}
    labels = {"scratch": Counter(x["label"] for x in scratch.values()),
              "sb3": Counter(x["label"] for x in library.values())}
    cmp = evals.compare(reward["scratch"], reward["sb3"])
    doc = {
        "stage": "2 PPO from scratch vs SB3 MaskablePPO", "commit": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", "src", "scripts")),
        "reproduce": f"cd ml && uv run --group train python scripts/train_ppo_scratch.py --procs {a.procs} "
                     f"--seeds {a.seeds} --steps {a.steps} --families {a.families}"
                     + (f" --test-worlds {a.test_worlds}" if a.test_worlds else ""),
        "scale": {"config": CONFIG, "seeds": a.seeds, "steps": a.steps, "train_families": len(train_seeds),
                  "test_worlds": len(test_ws)},
        "ppo_config": dataclasses.asdict(CFG),
        "arms": {name: {**evals.summary(m), "per_run_mean_reward": m.mean(axis=1).round(4).tolist(),
                        "labels": dict(labels[name])} for name, m in reward.items()},
        "scratch_vs_sb3": cmp,
        "not_worse_than_sb3": cmp["diff"]["hi"] >= 0,  # the acceptance target: 0 is not above the CI
        "runs": runs,
        "wall_seconds": round(time.perf_counter() - t0, 1),
    }
    Path(a.out, "ppo_scratch.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("scratch_vs_sb3", "not_worse_than_sb3", "wall_seconds")}))
    return doc


if __name__ == "__main__":
    main()
