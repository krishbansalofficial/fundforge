"""Train MaskablePPO for one FundForgeEnv seat on train-split worlds only.

Run from ml/ (training venv, see docs/ML_RL.md):
    uv run --group train python scripts/train_ppo.py --role mp --seed 1 --steps 150000 [--hp results/ppo_tune.json]

1. Worlds: generated seed families ``ppo-<n>`` that pass the balance gate for both variants,
   split by ``split_of`` into train / val / test. The split and every rejection are cached in
   ``results/ppo_worlds_<n>.json`` so all scripts use the same worlds.
2. Train: MaskablePPO (sb3-contrib) on train families only, across parallel worker processes,
   with hyperparameters ``DEFAULT_HP`` or the ``best_params`` of a tuning result (``--hp``).
   MLflow (local SQLite store) logs parameters, the training curve and the model.
3. Writes ``results/ppo_<role>_s<seed>.zip`` (gitignored) and ``results/ppo_<role>_s<seed>.json``
   (params, seed, split sizes, model SHA-256, reproduce command). Evaluation lives in
   ``eval_seats.py`` so the test split is read once, after tuning.
"""

import argparse
import hashlib
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import mlflow
import numpy as np
import torch
from fundforge.generator import GEN_VERSION
from sb3_contrib import MaskablePPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor

from fundforge_ml import worlds
from fundforge_ml.contracts import CONTRACT_VERSION, split_of
from fundforge_ml.encoding import ENCODER_VERSION
from fundforge_ml.env import ACTION_VERSION, REWARD_VERSION, FundForgeEnv

ML = Path(__file__).parents[1]
RESULTS = ML / "results"
DEFAULT_HP: dict[str, Any] = {
    "n_steps": 256,
    "batch_size": 256,
    "gamma": 0.99,
    "learning_rate": 3e-4,
    "ent_coef": 0.01,
    "width": 128,
}
VERSIONS = {
    "contract": CONTRACT_VERSION,
    "encoder": ENCODER_VERSION,
    "actions": ACTION_VERSION,
    "reward": REWARD_VERSION,
    "generator": GEN_VERSION,
}


def reproduce() -> str:
    return "uv run --group train python " + " ".join(
        Path(a).as_posix() if i == 0 else a for i, a in enumerate(sys.argv)
    )


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


def load_splits(n: int) -> dict[str, Any]:
    """Gate ``n`` families once and cache the split; later calls read the cache."""
    path = RESULTS / f"ppo_worlds_{n}.json"
    if path.exists():
        cached: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        if cached["generator"] == GEN_VERSION:
            return cached
    t0 = time.perf_counter()
    splits, rejected = gated_families(n)
    data = {
        "families_drawn": n,
        "generator": GEN_VERSION,
        "contract": CONTRACT_VERSION,
        "splits": splits,
        "counts": {k: len(v) for k, v in splits.items()},
        "rejected_reasons": dict(rejected),
        "gate_seconds": round(time.perf_counter() - t0, 1),
    }
    RESULTS.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def split_worlds(seeds: list[str]) -> list[tuple[str, str]]:
    return [(s, v) for s in seeds for v in worlds.variant_names()]


class TrainWorlds:
    """Picklable world sampler for worker processes: train families only, random variant."""

    def __init__(self, seeds: list[str]) -> None:
        self.seeds = seeds

    def __call__(self, options: dict[str, Any], rng: np.random.Generator) -> worlds.World:
        names = worlds.variant_names()
        seed = self.seeds[int(rng.integers(len(self.seeds)))]
        # these seeds already passed the gate in the parent process; workers need not re-run it
        return worlds.world(seed, names[int(rng.integers(len(names)))], gate=False)


def make_env(role: str, seeds: list[str], rank: int, seed: int):  # type: ignore[no-untyped-def]
    def _init() -> FundForgeEnv:
        env = FundForgeEnv(role, policy_id="ppo-train", world_fn=TrainWorlds(seeds))
        env.reset(seed=10_000 * (seed + 1) + rank)
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
        if self.rewards and mlflow.active_run():
            mlflow.log_metric("train_episode_reward", statistics.fmean(self.rewards[-200:]), step=self.num_timesteps)


def train(
    role: str, train_seeds: list[str], steps: int, seed: int, hp: dict[str, Any], workers: int
) -> tuple[MaskablePPO, float]:
    torch.manual_seed(seed)
    venv = VecMonitor(SubprocVecEnv([make_env(role, train_seeds, i, seed) for i in range(workers)]))
    try:
        model = MaskablePPO(
            "MlpPolicy",
            venv,
            n_steps=hp["n_steps"],
            batch_size=hp["batch_size"],
            gamma=hp["gamma"],
            learning_rate=hp["learning_rate"],
            ent_coef=hp["ent_coef"],
            policy_kwargs={"net_arch": [hp["width"], hp["width"]]},
            seed=seed,
            verbose=0,
            device="cpu",
        )
        t0 = time.perf_counter()
        model.learn(total_timesteps=steps, callback=CurveToMlflow())
        return model, time.perf_counter() - t0
    finally:
        venv.close()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def use_mlflow() -> None:
    mlflow.set_tracking_uri(f"sqlite:///{ML / 'mlflow.db'}")  # local, untracked; artifacts under mlruns/
    if mlflow.get_experiment_by_name("fundforge-ppo") is None:
        mlflow.create_experiment("fundforge-ppo", artifact_location=(ML / "mlruns").as_uri())
    mlflow.set_experiment("fundforge-ppo")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="pm", choices=["pm", "mp"])
    ap.add_argument("--steps", type=int, default=150_000)
    ap.add_argument("--families", type=int, default=400)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--hp", type=Path, help="tuning result JSON whose best_params replace DEFAULT_HP")
    args = ap.parse_args()
    hp = dict(DEFAULT_HP)
    if args.hp:
        hp.update(json.loads(args.hp.read_text(encoding="utf-8"))["best_params"])
    split = load_splits(args.families)
    use_mlflow()
    name = f"ppo_{args.role}_s{args.seed}"
    with mlflow.start_run(run_name=name):
        params = {
            "role": args.role,
            "steps": args.steps,
            "seed": args.seed,
            "workers": args.workers,
            "families_drawn": args.families,
            "train_families": len(split["splits"]["train"]),
            "hp_source": args.hp.as_posix() if args.hp else "DEFAULT_HP",
            **hp,
            **VERSIONS,
        }
        mlflow.log_params(params)
        model, train_s = train(args.role, split["splits"]["train"], args.steps, args.seed, hp, args.workers)
        model_path = RESULTS / f"{name}.zip"
        model.save(model_path)
        result = {
            "params": params,
            "train_seconds": round(train_s, 1),
            "steps_per_s": round(args.steps / train_s, 1),
            "model": model_path.name,
            "model_sha256": sha256(model_path),
            "reproduce": reproduce(),
        }
        (RESULTS / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        mlflow.log_metric("train_seconds", train_s)
        mlflow.log_artifact(str(model_path))
        print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
