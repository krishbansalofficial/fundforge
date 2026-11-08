"""Stage 1 honest evaluation of MaskablePPO: many seeds, many worlds, val selection.

Run from ml/ (full scale):
  uv run --group train python scripts/eval_ppo.py --seeds 5 --steps 200000 --families 2800

1. Gate: draw families ``ppo-<n>``; each family x variant runs the balance gate in a process pool.
   The base level gates every family; harder levels gate only base-test families. Every rejection
   (gate failure code, or an engine exception on a generated tape) is recorded with its seed.
2. Grid: each config in ``GRID`` is trained once per seed on base train families (one process per run).
3. Select: every run is scored on base val worlds; the config with the best val IQM is chosen.
   Test is never looked at for selection.
4. Test: the chosen config's seeds, ``random`` (several rng seeds), ``rules`` (bot:v1 in the agent's
   seat) and ``wait`` play identical base test worlds in identical column order; reported through
   ``fundforge_ml.evals`` (summary per policy, compare ppo vs each baseline).
5. Difficulty: chosen ppo and random on each harder level's accepted test worlds.

``--train-level hard`` runs steps 1-4 on that level instead of base (the sweep then covers the others).

Writes results/ppo_<role>.json (ppo_<role>_<level>.json for a non-base train level).
Models go to results/*.zip (git-ignored).
"""

import argparse
import dataclasses
import hashlib
import json
import platform
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import Executor, ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import sb3_contrib
import stable_baselines3
import torch
from fundforge.balance import accept
from fundforge.generator import GEN_VERSION, HARD_VERSION, SCENARIO_VERSION, Spec, generate
from fundforge.tape import compile_tape
from sb3_contrib import MaskablePPO
from stable_baselines3.common.vec_env import DummyVecEnv
from train_ppo import make_env, play

from fundforge_ml import evals, worlds
from fundforge_ml.contracts import CONTRACT_VERSION, split_of
from fundforge_ml.encoding import ENCODER_VERSION
from fundforge_ml.env import ACTION_VERSION, REWARD_VERSION, FundForgeEnv

ML = Path(__file__).parents[1]
LEVELS: dict[str, tuple[str, Spec]] = {
    "base": (GEN_VERSION, Spec()),  # exactly what worlds.world builds: the training distribution
    "scenario": (SCENARIO_VERSION, Spec()),  # randomised crisis day/severity, stressed margin, LP, rivals, book
    "hard": (HARD_VERSION, Spec()),  # +20pt stressed margin; the gate also rejects worlds naive play wins
    "harsh": (
        SCENARIO_VERSION,
        Spec(crisis_points=10, margin_points=25, factor_bp=400, idio_bp=250, stress_multiplier=5),
    ),
}
GRID: dict[str, dict[str, float]] = {
    "lr3e-4_ent0.01": {"learning_rate": 3e-4, "ent_coef": 0.01},  # the previous single-seed run
    "lr1e-4_ent0.01": {"learning_rate": 1e-4, "ent_coef": 0.01},
    "lr3e-4_ent0": {"learning_rate": 3e-4, "ent_coef": 0.0},
}
FIXED: dict[str, Any] = {"n_steps": 256, "batch_size": 256, "gamma": 0.99, "net_arch": [128, 128]}


@lru_cache(maxsize=8192)
def build(seed: str, level: str, variant: str) -> worlds.World:
    version, spec = LEVELS[level]
    return worlds.World(compile_tape(generate(seed, version, worlds.skeleton(), spec), variant), seed, variant)


def gate(job: tuple[str, str]) -> tuple[str, str, str, list[str]]:
    """(level, seed, split, failures); no failures means every variant passed the balance gate."""
    level, seed = job
    split, failures = "", []
    for v in worlds.variant_names():
        try:
            w = build(seed, level, v)
            split = split_of(w.seed_family)
            failures += [f"{v}:{f}" for f in accept(w.tape)[1]["failures"]]
        except Exception as ex:  # an engine error on a generated tape is a finding: record it, never skip
            failures.append(f"{v}:error:{type(ex).__name__}")
    return level, seed, split, failures


class LevelWorlds:
    """Picklable train sampler for a non-base level: gated train families, random variant."""

    def __init__(self, seeds: list[str], level: str) -> None:
        self.seeds, self.level = seeds, level

    def __call__(self, options: dict[str, Any], rng: np.random.Generator) -> worlds.World:
        names = worlds.variant_names()
        seed = self.seeds[int(rng.integers(len(self.seeds)))]
        return build(seed, self.level, names[int(rng.integers(len(names)))])


def _level_env(role: str, seeds: list[str], level: str, rank: int):  # type: ignore[no-untyped-def]
    if level == "base":  # keep the published base result byte-reproducible
        return make_env(role, seeds, rank)

    def _init() -> FundForgeEnv:
        env = FundForgeEnv(role, policy_id="ppo-train", world_fn=LevelWorlds(seeds, level))
        env.reset(seed=10_000 + rank)
        return env

    return _init


def train(job: tuple[str, int, str, list[str], int, int, str, str]) -> dict[str, Any]:
    cfg, seed, role, train_seeds, steps, n_envs, out, level = job
    torch.set_num_threads(1)
    venv = DummyVecEnv([_level_env(role, train_seeds, level, 1000 * seed + i) for i in range(n_envs)])
    model = MaskablePPO(
        "MlpPolicy",
        venv,
        n_steps=FIXED["n_steps"],
        batch_size=FIXED["batch_size"],
        gamma=FIXED["gamma"],
        policy_kwargs={"net_arch": FIXED["net_arch"]},
        seed=seed,
        verbose=0,
        device="cpu",
        **GRID[cfg],
    )
    t = time.perf_counter()
    model.learn(total_timesteps=steps)
    path = Path(out) / f"ppo_{role}{_suffix(level)}_{cfg}_s{seed}.zip"
    model.save(path)
    return {
        "config": cfg,
        "seed": seed,
        "path": str(path),
        "seconds": round(time.perf_counter() - t, 1),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


@lru_cache(maxsize=64)
def _model(path: str) -> MaskablePPO:
    return MaskablePPO.load(path, device="cpu")


def episode(job: tuple[Any, ...]) -> tuple[Any, dict[str, Any]]:
    key, role, seed, level, variant, kind, model_path, rng_seed = job
    torch.set_num_threads(1)
    model = _model(model_path) if model_path else None
    return key, play(role, build(seed, level, variant), kind, model, rng_seed)


Runs = dict[str, tuple[str, list[tuple[str | None, int]]]]  # name -> (policy kind, [(model path, rng seed)])


def play_block(pool: Executor, role: str, level: str, ws: list[tuple[str, str]], runs: Runs) -> dict[str, Any]:
    """Every run of every policy on the same worlds; returns name -> (runs, worlds) reward/score/label arrays."""
    jobs = [
        ((name, i, j), role, s, level, v, kind, path, rng)
        for name, (kind, rs) in runs.items()
        for i, (path, rng) in enumerate(rs)
        for j, (s, v) in enumerate(ws)
    ]
    out = {
        name: {
            "reward": np.zeros((len(rs), len(ws))),
            "score": np.zeros((len(rs), len(ws))),
            "label": np.empty((len(rs), len(ws)), dtype=object),
        }
        for name, (_, rs) in runs.items()
    }
    for (name, i, j), r in pool.map(episode, jobs, chunksize=8):
        out[name]["reward"][i, j], out[name]["score"][i, j], out[name]["label"][i, j] = (
            r["reward"],
            r["score"],
            r["label"],
        )
    return out


def report(rows: dict[str, Any], ref: str = "ppo") -> dict[str, Any]:
    """evals.summary per policy, evals.compare(ref, X) for every other X, labels, score bps, random's non-wins."""
    out: dict[str, Any] = {"policies": {}, "compare": {}}
    for name, m in rows.items():
        out["policies"][name] = {
            **evals.summary(m["reward"]),
            "per_run_mean_reward": m["reward"].mean(axis=1).round(4).tolist(),
            "mean_score_bps": round(float(m["score"].mean()), 1),
            "labels": dict(Counter(m["label"].ravel().tolist())),
        }
        if name != ref and ref in rows:
            out["compare"][f"{ref}_vs_{name}"] = evals.compare(rows[ref]["reward"], m["reward"])
    if "random" in rows:
        lost = rows["random"]["label"] != "WIN"  # (runs, worlds)
        out["random_not_win"] = {
            "n_worlds": lost.shape[1],
            "share_worlds_any_run": float(lost.any(axis=0).mean()),
            "share_worlds_all_runs": float(lost.all(axis=0).mean()),
            "share_episodes": float(lost.mean()),
        }
    return out


def _git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ML, capture_output=True, text=True, check=False).stdout.strip()


def main(argv: list[str] | None = None) -> dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="pm", choices=["pm", "mp"])
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--steps", type=int, default=200_000)
    ap.add_argument("--families", type=int, default=2800)
    ap.add_argument("--random-runs", type=int, default=5)
    ap.add_argument("--envs", type=int, default=4, help="environments per training run (one process)")
    ap.add_argument("--procs", type=int, default=30)
    ap.add_argument("--grid", default=",".join(GRID))
    ap.add_argument("--levels", default=",".join(LEVELS))
    ap.add_argument("--train-level", default="base", choices=list(LEVELS),
                    help="level that gates, trains, selects and tests; other --levels are the difficulty sweep")
    ap.add_argument("--out", default=str(ML / "results"))
    args = ap.parse_args(argv)
    tl = args.train_level
    grid, levels = args.grid.split(","), [lv for lv in args.levels.split(",") if lv != tl]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    wall: dict[str, float] = {}
    t0 = time.perf_counter()
    seeds = [f"ppo-{i}" for i in range(args.families)]
    gates: dict[str, Any] = {}
    with ProcessPoolExecutor(args.procs) as pool:
        # 1. gate
        base = list(pool.map(gate, [(tl, s) for s in seeds], chunksize=8))
        splits: dict[str, list[str]] = {"train": [], "val": [], "test": []}
        candidates = Counter(sp for _, _, sp, _ in base)
        for _, s, sp, f in base:
            if not f:
                splits[sp].append(s)
        test_candidates = [s for _, s, sp, _ in base if sp == "test"]
        gated = {
            tl: base,
            **{lv: list(pool.map(gate, [(lv, s) for s in test_candidates], chunksize=8)) for lv in levels},
        }
        for lv, rows in gated.items():
            rejected: dict[str, list[str]] = defaultdict(list)
            for _, s, _, f in rows:
                for code in f:
                    rejected[code].append(s)
            accepted = [s for _, s, _, f in rows if not f]
            gates[lv] = {
                "families_gated": len(rows),
                "accepted": len(accepted),
                "acceptance": round(len(accepted) / len(rows), 4) if rows else None,
                "test_families_gated": sum(1 for _, _, sp, _ in rows if sp == "test"),
                "test_accepted": sum(1 for _, s, sp, f in rows if sp == "test" and not f),
                "rejected_counts": {k: len(v) for k, v in sorted(rejected.items())},
                "rejected_seeds": dict(sorted(rejected.items())),
                "accepted_test_seeds": [s for _, s, sp, f in rows if sp == "test" and not f],
            }
        gates[tl]["candidates_by_split"] = dict(candidates)
        gates[tl]["accepted_by_split"] = {k: len(v) for k, v in splits.items()}
        wall["gate"] = round(time.perf_counter() - t0, 1)
        print(
            f"gate {wall['gate']}s: "
            + json.dumps({lv: (g["accepted"], g["families_gated"]) for lv, g in gates.items()}),
            flush=True,
        )

        # 2. grid x seeds, all in parallel
        t = time.perf_counter()
        runs = list(
            pool.map(
                train,
                [
                    (c, k, args.role, splits["train"], args.steps, args.envs, str(out), tl)
                    for c in grid
                    for k in range(args.seeds)
                ],
            )
        )
        wall["train"] = round(time.perf_counter() - t, 1)
        print(f"trained {len(runs)} runs in {wall['train']}s", flush=True)
        paths = {c: [(r["path"], 0) for r in runs if r["config"] == c] for c in grid}

        # 3. select on val
        t = time.perf_counter()
        names = worlds.variant_names()
        val_ws = [(s, v) for s in splits["val"] for v in names]
        val = play_block(pool, args.role, tl, val_ws, {c: ("ppo", paths[c]) for c in grid})
        val_iqm = {c: evals.iqm(val[c]["reward"]) for c in grid}
        chosen = max(grid, key=lambda c: val_iqm[c])
        wall["val"] = round(time.perf_counter() - t, 1)
        print(f"val IQM {val_iqm} -> {chosen}", flush=True)

        # 4. test, chosen config only
        t = time.perf_counter()
        rnd = [(None, k) for k in range(args.random_runs)]
        test_ws = [(s, v) for s in splits["test"] for v in names]
        test = play_block(
            pool,
            args.role,
            tl,
            test_ws,
            {
                "ppo": ("ppo", paths[chosen]),
                "random": ("random", rnd),
                "rules": ("rules", [(None, 0)]),
                "wait": ("wait", [(None, 0)]),
            },
        )
        wall["test"] = round(time.perf_counter() - t, 1)

        # 5. difficulty sweep: same chosen models, harder test worlds
        t = time.perf_counter()
        difficulty: dict[str, Any] = {
            tl: {
                "gate_acceptance_test": _ratio(gates[tl]),
                **_light(report({k: test[k] for k in ("ppo", "random")})),
            }
        }
        for lv in levels:
            ws = [(s, v) for s in gates[lv]["accepted_test_seeds"] for v in names]
            rows = play_block(pool, args.role, lv, ws, {"ppo": ("ppo", paths[chosen]), "random": ("random", rnd)})
            difficulty[lv] = {
                "gate_acceptance_test": _ratio(gates[lv]),
                "n_worlds": len(ws),
                **(_light(report(rows)) if ws else {}),
            }
        wall["difficulty"] = round(time.perf_counter() - t, 1)
    wall["total"] = round(time.perf_counter() - t0, 1)

    result = {
        "stage": "ML_SHOWCASE stage 1: multi-seed, val-selected, evals-reported",
        "train_level": tl,
        "commit": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", ".")),
        "reproduce": "cd ml && uv run --group train python scripts/eval_ppo.py "
        + " ".join(sys.argv[1:] if argv is None else argv),
        "scale": {
            "role": args.role,
            "training_seeds": list(range(args.seeds)),
            "steps_per_run": args.steps,
            "families_drawn": args.families,
            "random_runs": args.random_runs,
            "envs_per_run": args.envs,
            "split_families": {k: len(v) for k, v in splits.items()},
            "split_worlds": {k: len(v) * len(names) for k, v in splits.items()},
            "test_families": len(splits["test"]),
            "test_worlds": len(test_ws),
        },
        "versions": {
            "contract": CONTRACT_VERSION,
            "encoder": ENCODER_VERSION,
            "actions": ACTION_VERSION,
            "reward": REWARD_VERSION,
            "python": platform.python_version(),
            "torch": torch.__version__,
            "sb3": stable_baselines3.__version__,
            "sb3_contrib": sb3_contrib.__version__,
            "numpy": np.__version__,
        },
        "levels": {lv: {"gen_version": v, "spec": dataclasses.asdict(sp)} for lv, (v, sp) in LEVELS.items()},
        "fixed_params": FIXED,
        "grid": {
            c: {
                "params": GRID[c],
                "val_iqm": val_iqm[c],
                "val": report({c: val[c]}, ref="")["policies"][c],
                "runs": [{k: r[k] for k in ("seed", "seconds", "sha256")} for r in runs if r["config"] == c],
            }
            for c in grid
        },
        "selection": {
            "rule": "highest IQM of terminal reward on val worlds over all seeds",
            "chosen": chosen,
            "val_worlds": len(val_ws),
        },
        "test": report(test),
        "difficulty": difficulty,
        "gate": gates,
        "test_world_order": [f"{s}/{v}" for s, v in test_ws],
        "wall_seconds": wall,
    }
    path = out / f"ppo_{args.role}{_suffix(tl)}.json"
    path.write_text(json.dumps(result, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"test": result["test"]["compare"], "difficulty": difficulty}, indent=1, default=str))
    return result


def _suffix(level: str) -> str:
    return "" if level == "base" else f"_{level}"


def _ratio(g: dict[str, Any]) -> float | None:
    return round(g["test_accepted"] / g["test_families_gated"], 4) if g["test_families_gated"] else None


def _light(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "ppo_vs_random": r["compare"].get("ppo_vs_random"),
        "random_not_win": r.get("random_not_win"),
        "labels": {k: v["labels"] for k, v in r["policies"].items()},
        "iqm": {k: v["iqm"] for k, v in r["policies"].items()},
    }


if __name__ == "__main__":
    main()
