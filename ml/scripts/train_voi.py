"""Value of information: how much return does a better belief buy a MaskablePPO policy?

    cd ml && uv run --group train --group forecast python scripts/train_voi.py --seeds 3 --steps 100000

1. Worlds: generated families ``ppo-<n>`` that pass the balance gate for both variants (as in
   train_ppo.py), split by ``split_of``. Rejections are counted.
2. Learned forecaster: ``train_forecast.logreg`` on ``forecast.world_samples`` of the TRAIN families
   of ``forecast-<i>`` worlds only (the train_forecast pipeline).
3. Train MaskablePPO under each belief mode (``belief.MODES``) with the same train families, seeds
   and hyperparameters as train_ppo.py; each run is one process with in-process vector envs.
4. Evaluate every model deterministically on the same test worlds (test family x variant) and
   report ``evals.summary`` per mode and ``evals.compare`` between modes, scores shaped (seeds, worlds).
5. Belief quality on the test worlds' as-of days: Brier of each mode and the learned gap to exact.
Writes results/voi_<role>.json.
"""

import argparse
import json
import platform
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import sb3_contrib
import torch
from fundforge.generator import GEN_VERSION
from sb3_contrib import MaskablePPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
from train_forecast import logreg
from train_ppo import TrainWorlds

from fundforge_ml import evals, forecast, worlds
from fundforge_ml.belief import BELIEF_VERSION, MODES, BeliefWrapper, Forecaster, Logistic
from fundforge_ml.contracts import CONTRACT_VERSION, split_of
from fundforge_ml.encoding import ENCODER_VERSION
from fundforge_ml.env import ACTION_VERSION, REWARD_VERSION, FundForgeEnv

ML = Path(__file__).parents[1]
HPARAMS = {"n_steps": 256, "batch_size": 256, "gamma": 0.99, "learning_rate": 3e-4, "ent_coef": 0.01}
NET = [128, 128]
PAIRS = (("exact", "none"), ("learned", "none"), ("exact", "learned"))


def gate(seed: str) -> tuple[str, list[str] | None]:
    try:
        for v in worlds.variant_names():
            worlds.world(seed, v)
    except worlds.WorldRejected as ex:
        return seed, ex.failures
    return seed, None


def wrapped(role: str, world_fn: Any, mode: str, fc: Forecaster | None, policy: str) -> BeliefWrapper:
    return BeliefWrapper(FundForgeEnv(role, policy_id=policy, world_fn=world_fn), mode,
                         fc if mode == "learned" else None)


def play(env: BeliefWrapper, model: MaskablePPO, tag: str) -> dict[str, Any]:
    obs, _ = env.reset(seed=0, options={"episode_tag": tag})
    total, done, info = 0.0, False, {}
    while not done:
        a, _ = model.predict(obs, deterministic=True, action_masks=env.action_masks())
        obs, r, term, trunc, info = env.step(int(a))
        total += float(r)
        done = term or trunc
    return {"reward": total, "score": float(info["outcome"]["score"]), "label": info["outcome"]["label"]}


def run(role: str, mode: str, seed: int, steps: int, n_envs: int, train: list[str],
        test: list[tuple[str, str]], fc: Forecaster | None) -> dict[str, Any]:
    """Train one (mode, seed) policy and play it on every test world. Runs in a worker process."""
    torch.set_num_threads(1)
    torch.manual_seed(seed)

    def make(rank: int) -> Any:
        def _init() -> BeliefWrapper:
            env = wrapped(role, TrainWorlds(train), mode, fc, "voi-train")
            env.reset(seed=10_000 + rank)
            return env
        return _init

    venv = VecMonitor(DummyVecEnv([make(i) for i in range(n_envs)]))
    model = MaskablePPO("MlpPolicy", venv, **HPARAMS, policy_kwargs={"net_arch": NET}, seed=seed,  # type: ignore[arg-type]
                        verbose=0, device="cpu")
    t = time.perf_counter()
    model.learn(total_timesteps=steps)
    train_s = time.perf_counter() - t
    venv.close()
    model.save(ML / "results" / f"voi_{role}_{mode}_{seed}.zip")  # untracked (.gitignore)
    rows = []
    for s, v in test:
        env = wrapped(role, lambda o, r, s=s, v=v: worlds.world(s, v, gate=False), mode, fc, f"voi-{mode}")
        rows.append(play(env, model, f"{mode}-{seed}"))
    print(f"{mode} seed {seed}: {train_s:.0f}s, mean test reward {np.mean([r['reward'] for r in rows]):.3f}",
          flush=True)
    return {"mode": mode, "seed": seed, "train_seconds": round(train_s, 1), "rows": rows}


def belief_rows(test: list[tuple[str, str]], fc: Forecaster) -> dict[str, Any]:
    """P(stressed) per mode on every as-of day (with a print) of every test world; labels are hidden truth."""
    p: dict[str, list[float]] = {m: [] for m in MODES}
    y, fams = [], []
    for s, v in test:
        w = worlds.world(s, v, gate=False)  # gated in main()
        regime = {d: r for d, r in w.tape.raw["generator"]["regimes"]}  # label only
        for day in sorted({ev.day for ev in w.tape.events}):
            rows = forecast.macro_rows(w.tape, day)
            k = forecast.known(rows, day)
            if not k:
                continue
            p["none"].append(0.0)
            p["exact"].append(forecast.bayes(rows, day)[1])
            p["learned"].append(fc(forecast.features(rows, day)))
            y.append(int(regime[k[-1]["period_day"]] == "stressed"))
            fams.append(f"{w.seed_family}/{v}")
    ya, ex = np.array(y, dtype=float), np.array(p["exact"])
    out = {m: {k: val for k, val in forecast.score(np.array(p[m]), ya, ex, fams).items() if k != "reliability"}
           for m in MODES}
    return {"rows": len(y), "worlds": len(set(fams)), "stressed_rate": float(ya.mean()), "by_mode": out,
            "learned_brier_gap_to_exact": out["learned"]["gap_brier"],
            "learned_brier_gap_se_by_world": out["learned"]["gap_brier_se_by_world"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="pm", choices=["pm", "mp"])
    ap.add_argument("--steps", type=int, default=100_000)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--families", type=int, default=1000)
    ap.add_argument("--forecast-worlds", type=int, default=20000)
    ap.add_argument("--n-envs", type=int, default=4)
    ap.add_argument("--workers", type=int, default=9)
    args = ap.parse_args()
    t0 = time.perf_counter()
    with ProcessPoolExecutor(args.workers) as pool:
        gated = list(pool.map(gate, [f"ppo-{i}" for i in range(args.families)], chunksize=10))
        samples = [s for b in pool.map(forecast.world_samples, [f"forecast-{i}" for i in range(args.forecast_worlds)],
                                       chunksize=100) for s in b if s.split == "train"]
    splits: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    rejected: Counter[str] = Counter()
    for seed, fail in gated:
        if fail is None:
            splits[split_of(worlds.world(seed, "base", gate=False).seed_family)].append(seed)
        else:
            rejected.update(fail)
    test = [(s, v) for s in splits["test"] for v in worlds.variant_names()]
    w = logreg(np.stack([s.x for s in samples]), np.array([s.y for s in samples], dtype=float))
    fc = Logistic(w)
    prep_s = time.perf_counter() - t0
    print(f"prep {prep_s:.0f}s: " + ", ".join(f"{k} {len(v)}" for k, v in splits.items())
          + f"; forecaster on {len(samples)} train rows", flush=True)

    t1 = time.perf_counter()
    with ProcessPoolExecutor(min(args.workers, len(MODES) * args.seeds)) as pool:
        futs = [pool.submit(run, args.role, m, k, args.steps, args.n_envs, splits["train"], test, fc)
                for m in MODES for k in range(args.seeds)]
        runs = [f.result() for f in futs]
    wall_s = time.perf_counter() - t1

    rewards = {m: np.array([[r["reward"] for r in x["rows"]] for x in runs if x["mode"] == m]) for m in MODES}
    scores = {m: np.array([[r["score"] for r in x["rows"]] for x in runs if x["mode"] == m]) for m in MODES}
    report: dict[str, Any] = {
        "summary_reward": {m: evals.summary(rewards[m]) for m in MODES},
        "mean_score_bps": {m: round(float(scores[m].mean()), 1) for m in MODES},
        "labels": {m: dict(Counter(r["label"] for x in runs if x["mode"] == m for r in x["rows"])) for m in MODES},
        "compare_reward": {f"{a}_vs_{b}": evals.compare(rewards[a], rewards[b]) for a, b in PAIRS},
        "belief_quality": belief_rows(test, fc),
    }
    larger = (f"cd ml && uv run --group train --group forecast python scripts/train_voi.py --role {args.role} "
              f"--seeds 10 --steps 500000 --families 3000 --workers 30")
    result = {
        "question": "Return bought by appending P(stressed) (none / learned / exact Bayes) to the PPO observation",
        "reproduce": (f"cd ml && uv run --group train --group forecast python scripts/train_voi.py --role {args.role} "
                      f"--seeds {args.seeds} --steps {args.steps} --families {args.families} "
                      f"--forecast-worlds {args.forecast_worlds} --n-envs {args.n_envs} --workers {args.workers}"),
        "larger_run": larger,
        "scale": {"seeds_per_mode": args.seeds, "steps_per_run": args.steps, "n_envs": args.n_envs,
                  "families_drawn": args.families, "train_families": len(splits["train"]),
                  "test_families": len(splits["test"]), "test_worlds": len(test),
                  "forecaster_train_rows": len(samples), "forecast_worlds_drawn": args.forecast_worlds},
        "params": {"role": args.role, "net": NET, **HPARAMS,
                   "algo": f"sb3-contrib MaskablePPO {sb3_contrib.__version__}",
                   "learned_forecaster": "train_forecast.logreg (numpy IRLS, l2 1e-3) on forecast-<i> TRAIN families"},
        "versions": {"belief": BELIEF_VERSION, "feature": forecast.FEATURE_VERSION, "encoder": ENCODER_VERSION,
                     "actions": ACTION_VERSION, "reward": REWARD_VERSION, "contracts": CONTRACT_VERSION,
                     "generator": GEN_VERSION, "python": sys.version.split()[0], "torch": torch.__version__,
                     "platform": platform.platform()},
        "notes": "Scores are (seeds, worlds); evals.compare pairs on worlds. Reward = engine score / 100 + tier bonus "
                 "(reward-v1). Belief rows: every as-of day with a published print on each test world; gap = "
                 "model minus exact Brier on the same rows.",
        "rejected": dict(rejected),
        "seconds": {"prep": round(prep_s, 1), "train_and_eval_wall": round(wall_s, 1),
                    "train_per_run": {f"{x['mode']}-{x['seed']}": x["train_seconds"] for x in runs}},
        "test_worlds": [f"{s}/{v}" for s, v in test],
        "report": report,
    }
    out = ML / "results" / f"voi_{args.role}.json"
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("summary_reward", "compare_reward")}, indent=2))
    print(json.dumps(report["belief_quality"]["by_mode"], indent=2))


if __name__ == "__main__":
    main()
