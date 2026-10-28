"""Train MaskablePPO on FundForgeEnv and compare it with baselines on held-out worlds.

Run from ml/:  uv run --group train python scripts/train_ppo.py --role pm --steps 200000

1. Worlds: generated seed families ``ppo-<n>`` that pass the balance gate for both variants,
   split by ``split_of`` into train / val / test. Rejections are counted, never hidden.
2. Train: MaskablePPO (sb3-contrib) on train families only, across parallel worker processes.
   MLflow logs parameters, the training curve, final metrics and the model.
3. Evaluate on test families (each family x each variant is one deterministic world):
   ``ppo`` (deterministic, masked), ``rules`` (bot:v1 playing the agent's seat),
   ``random`` (uniform over valid actions, several seeds) and ``wait``.
   Reports mean reward with a 95% normal interval, mean engine score in bps, outcome labels,
   and the paired per-world difference ppo - random. Writes results/ppo_<role>.json.
"""

import argparse
import hashlib
import json
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

import mlflow
import numpy as np
import torch
from fundforge import bot
from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import SubprocVecEnv

from fundforge_ml import worlds
from fundforge_ml.contracts import CONTRACT_VERSION, split_of
from fundforge_ml.encoding import ENCODER_VERSION
from fundforge_ml.env import ACTION_VERSION, REWARD_VERSION, FundForgeEnv

ML = Path(__file__).parents[1]


def gated_families(n: int) -> tuple[dict[str, list[str]], Counter[str]]:
    splits: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    rejected: Counter[str] = Counter()
    for i in range(n):
        seed = f"ppo-{i}"
        try:
            for v in worlds.variant_names():
                worlds.world(seed, v)
        except worlds.WorldRejected as ex:
            rejected.update(ex.failures)
            continue
        splits[split_of(worlds.world(seed, "base").seed_family)].append(seed)
    return splits, rejected


class TrainWorlds:
    """Picklable world sampler for worker processes: train families only, random variant."""

    def __init__(self, seeds: list[str]) -> None:
        self.seeds = seeds

    def __call__(self, options: dict[str, Any], rng: np.random.Generator) -> worlds.World:
        names = worlds.variant_names()
        seed = self.seeds[int(rng.integers(len(self.seeds)))]
        # these seeds already passed the gate in the parent process; workers need not re-run it
        return worlds.world(seed, names[int(rng.integers(len(names)))], gate=False)


def make_env(role: str, seeds: list[str], rank: int):  # type: ignore[no-untyped-def]
    def _init() -> FundForgeEnv:
        env = FundForgeEnv(role, policy_id="ppo-train", world_fn=TrainWorlds(seeds))
        env.reset(seed=10_000 + rank)
        return env
    return _init


class CurveToMlflow(BaseCallback):
    def __init__(self) -> None:
        super().__init__()
        self.rewards: list[float] = []

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            if "episode" in info:
                self.rewards.append(float(info["episode"]["r"]))
        return True

    def _on_rollout_end(self) -> None:
        if self.rewards:
            mlflow.log_metric("train_episode_reward", statistics.fmean(self.rewards[-200:]), step=self.num_timesteps)


def play(role: str, w: worlds.World, policy: str, model: MaskablePPO | None, rng_seed: int) -> dict[str, Any]:
    env = FundForgeEnv(role, policy_id=policy, world_fn=lambda o, r: w)
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
        elif policy == "rules":  # the hand-written bot:v1 policy playing the agent's seat
            assert env.s is not None
            bot.act(env.s, role, env.user, f"rules-{k}")
            env.view = env.s.view(env.user)
            a = 0
        else:
            a = 0
        obs, r, term, trunc, info = env.step(a)
        total += r
        done = term or trunc
    out = info["outcome"]
    return {"reward": total, "score": float(out["score"]), "label": out["label"]}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rewards = [r["reward"] for r in rows]
    half = 1.96 * statistics.stdev(rewards) / len(rewards) ** 0.5 if len(rewards) > 1 else 0.0
    return {"n": len(rows), "mean_reward": round(statistics.fmean(rewards), 3), "ci95": round(half, 3),
            "mean_score_bps": round(statistics.fmean(r["score"] for r in rows), 1),
            "labels": dict(Counter(r["label"] for r in rows))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="pm", choices=["pm", "mp"])
    ap.add_argument("--steps", type=int, default=200_000)
    ap.add_argument("--families", type=int, default=200)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--random-runs", type=int, default=5)
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    t0 = time.perf_counter()
    splits, rejected = gated_families(args.families)
    print(f"gate {time.perf_counter() - t0:.0f}s: " + ", ".join(f"{k} {len(v)}" for k, v in splits.items())
          + f"; rejected {sum(rejected.values()) and dict(rejected)}", flush=True)

    mlflow.set_tracking_uri(f"sqlite:///{ML / 'mlflow.db'}")  # local, untracked; artifacts under mlruns/
    if mlflow.get_experiment_by_name("fundforge-ppo") is None:
        mlflow.create_experiment("fundforge-ppo", artifact_location=(ML / "mlruns").as_uri())
    mlflow.set_experiment("fundforge-ppo")
    with mlflow.start_run(run_name=f"maskableppo-{args.role}-{args.steps}"):
        params = {"role": args.role, "steps": args.steps, "families_drawn": args.families, "seed": args.seed,
                  "train_families": len(splits["train"]), "test_families": len(splits["test"]),
                  "contract": CONTRACT_VERSION, "encoder": ENCODER_VERSION, "actions": ACTION_VERSION,
                  "reward": REWARD_VERSION, "net": "128x128", "n_steps": 256, "batch_size": 256,
                  "gamma": 0.99, "learning_rate": 3e-4, "ent_coef": 0.01}
        mlflow.log_params(params)
        venv = SubprocVecEnv([make_env(args.role, splits["train"], i) for i in range(args.workers)])
        from stable_baselines3.common.vec_env import VecMonitor
        venv = VecMonitor(venv)
        model = MaskablePPO("MlpPolicy", venv, n_steps=256, batch_size=256, gamma=0.99, learning_rate=3e-4,
                            ent_coef=0.01, policy_kwargs={"net_arch": [128, 128]}, seed=args.seed, verbose=0,
                            device="cpu")
        assert get_action_masks(venv).shape[1] == venv.action_space.n
        t1 = time.perf_counter()
        model.learn(total_timesteps=args.steps, callback=CurveToMlflow())
        train_s = time.perf_counter() - t1
        venv.close()
        out = ML / "results"
        out.mkdir(exist_ok=True)
        model_path = out / f"ppo_{args.role}.zip"
        model.save(model_path)
        sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
        print(f"trained {args.steps} steps in {train_s:.0f}s ({args.steps / train_s:.0f} steps/s)", flush=True)

        test = [(s, v) for s in splits["test"] for v in worlds.variant_names()]
        rows: dict[str, list[dict[str, Any]]] = {p: [] for p in ("ppo", "rules", "random", "wait")}
        paired = []
        for s, v in test:
            w = worlds.world(s, v)
            ppo = play(args.role, w, "ppo", model, 0)
            rows["ppo"].append(ppo)
            rows["rules"].append(play(args.role, w, "rules", None, 0))
            rows["wait"].append(play(args.role, w, "wait", None, 0))
            rnd = [play(args.role, w, "random", None, k) for k in range(args.random_runs)]
            rows["random"] += rnd
            paired.append(ppo["reward"] - statistics.fmean(r["reward"] for r in rnd))
        report = {p: summarize(r) for p, r in rows.items()}
        half = 1.96 * statistics.stdev(paired) / len(paired) ** 0.5 if len(paired) > 1 else 0.0
        report["ppo_minus_random_paired"] = {"n_worlds": len(paired), "mean": round(statistics.fmean(paired), 3),
                                             "ci95": round(half, 3),
                                             "ppo_better_worlds": sum(1 for d in paired if d > 0)}
        result = {"params": params, "rejected": dict(rejected), "train_seconds": round(train_s, 1),
                  "model_sha256": sha, "test_worlds": [f"{s}/{v}" for s, v in test], "report": report}
        (out / f"ppo_{args.role}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        for p, m in report.items():
            for k, val in m.items():
                if isinstance(val, int | float):
                    mlflow.log_metric(f"test_{p}_{k}", val)
        mlflow.log_artifact(str(model_path))
        mlflow.log_artifact(str(out / f"ppo_{args.role}.json"))
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
