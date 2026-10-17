"""Small Optuna search over MaskablePPO hyperparameters, scored on the VALIDATION split only.

Run from ml/ (training venv, see docs/ML_RL.md):
    uv run --group train python scripts/tune_ppo.py --role pm --trials 8 --steps 40000

Each trial trains on train-split worlds for ``--steps`` and is scored by the mean deterministic
reward on validation-split worlds (``eval_seats.evaluate`` with the ``ppo`` policy). The test split
is never loaded here: the assertion below keeps it out, and ``eval_seats.py`` reads it once, after
the best parameters are fixed. The best parameters are written to ``results/ppo_tune_<role>.json``
under ``best_params``, which ``train_ppo.py --hp`` accepts.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import optuna

ML = Path(__file__).parents[1]
sys.path.insert(0, str(ML / "scripts"))

from eval_seats import evaluate, pairs_of  # noqa: E402
from train_ppo import DEFAULT_HP, load_splits, train  # noqa: E402

SPLIT = "val"  # never change to test: the test split is reported once, after tuning


def space(trial: optuna.Trial) -> dict[str, Any]:
    n_steps = trial.suggest_categorical("n_steps", [128, 256, 512])
    return {
        "learning_rate": trial.suggest_float("learning_rate", 1e-4, 1e-3, log=True),
        "ent_coef": trial.suggest_float("ent_coef", 1e-3, 3e-2, log=True),
        "n_steps": n_steps,
        "batch_size": trial.suggest_categorical("batch_size", [64, 128, 256]),
        "gamma": trial.suggest_categorical("gamma", [0.98, 0.99, 0.995]),
        "width": trial.suggest_categorical("width", [64, 128]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="pm", choices=["pm", "mp"])
    ap.add_argument("--trials", type=int, default=9, help="includes the enqueued default trial")
    ap.add_argument("--steps", type=int, default=40_000)
    ap.add_argument("--families", type=int, default=400)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    split = load_splits(args.families)
    val_pairs = pairs_of(SPLIT, split["splits"])
    train_seeds = split["splits"]["train"]
    assert val_pairs and all(s not in split["splits"]["test"] for s, _ in val_pairs)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    t0 = time.perf_counter()

    def objective(trial: optuna.Trial) -> float:
        hp = space(trial)
        model, secs = train(args.role, train_seeds, args.steps, args.seed, hp, args.workers)
        val = evaluate(args.role, model, val_pairs, ("ppo",))["ppo"]
        trial.set_user_attr("val_mean_reward", val["mean_reward"])
        trial.set_user_attr("train_seconds", round(secs, 1))
        trial.set_user_attr("val_labels", val["labels"])
        print(f"trial {trial.number}: val {val['mean_reward']:.3f} {hp}", flush=True)
        return float(val["mean_reward"])

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=args.seed))
    study.enqueue_trial(dict(DEFAULT_HP))  # trial 0 is the default setting, the reference point
    study.optimize(objective, n_trials=args.trials)
    best = study.best_trial
    result = {
        "role": args.role,
        "split_used": SPLIT,
        "test_split_touched": False,
        "trials": args.trials,
        "steps_per_trial": args.steps,
        "seed": args.seed,
        "val_worlds": len(val_pairs),
        "val_families": len({s for s, _ in val_pairs}),
        "best_value_val_mean_reward": round(best.value or 0.0, 3),
        "best_params": best.params,
        "trial_table": [{"number": t.number, "val_mean_reward": t.value, "params": t.params} for t in study.trials],
        "mean_val_all_trials": round(statistics.fmean(t.value or 0.0 for t in study.trials), 3),
        "tune_seconds": round(time.perf_counter() - t0, 1),
        "reproduce": "uv run --group train python " + " ".join(sys.argv),
    }
    out = ML / "results" / f"ppo_tune_{args.role}.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("best_value_val_mean_reward", "best_params")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
