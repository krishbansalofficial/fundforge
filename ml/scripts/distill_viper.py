"""Distil a MaskablePPO teacher (PM seat) into small decision trees with VIPER; report what they learned.

Run from ml/:
  uv run --group train --with scikit-learn python scripts/distill_viper.py --steps 600000 --workers 16

1. Worlds: the same gated ``ppo-<n>`` families and ``split_of`` split as ``train_ppo.py``.
2. Teacher: MaskablePPO with train_ppo.py's hyperparameters on train families
   (or ``--teacher path.zip`` to reuse one; the run records its sha256).
3. For each depth: VIPER on train worlds (``fundforge_ml.distill``), the iterate with the best
   mean return on val worlds is kept, then scored on test worlds against the teacher and random.
4. Writes results/viper_pm.json with every depth's tree as text.
"""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
import torch
from sb3_contrib import MaskablePPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor
from train_ppo import gated_families, make_env

from fundforge_ml import distill, evals, worlds
from fundforge_ml.contracts import CONTRACT_VERSION
from fundforge_ml.encoding import ENCODER_VERSION
from fundforge_ml.env import ACTION_VERSION, REWARD_VERSION, FundForgeEnv

ML = Path(__file__).parents[1]
HYPER = {"net": [128, 128], "n_steps": 256, "batch_size": 256, "gamma": 0.99, "learning_rate": 3e-4,
         "ent_coef": 0.01}


def ppo_teacher(model: MaskablePPO) -> distill.Teacher:
    """Masked deterministic action and the log-probability gap (distill.py's weight proxy)."""
    def teacher(obs: np.ndarray, masks: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        with torch.no_grad():
            t, _ = model.policy.obs_to_tensor(obs)
            logits = model.policy.get_distribution(t, action_masks=masks).distribution.logits.cpu().numpy()
        return distill.masked_argmax(logits, masks), distill.logit_gap(logits, masks)
    return teacher


def opts(pairs: list[tuple[str, str]]) -> list[dict[str, Any]]:
    return [{"gen_seed": s, "variant": v, "gate": False, "episode_tag": f"{s}/{v}"} for s, v in pairs]


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ML, capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=600_000)
    ap.add_argument("--families", type=int, default=400)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--depths", default="2,4,6,8")
    ap.add_argument("--iterations", type=int, default=10)
    ap.add_argument("--random-runs", type=int, default=5)
    ap.add_argument("--teacher", type=Path, default=None, help="reuse a saved MaskablePPO .zip")
    args = ap.parse_args()
    depths = [int(d) for d in args.depths.split(",")]
    torch.manual_seed(args.seed)
    t0 = time.perf_counter()
    splits, rejected = gated_families(args.families)
    print(f"gate {time.perf_counter() - t0:.0f}s: " + ", ".join(f"{k} {len(v)}" for k, v in splits.items()),
          flush=True)
    names = worlds.variant_names()
    split_worlds = {k: [(s, v) for s in seeds for v in names] for k, seeds in splits.items()}

    out = ML / "results"
    train_s = None
    if args.teacher is None:
        venv = VecMonitor(SubprocVecEnv([make_env("pm", splits["train"], i) for i in range(args.workers)]))
        model = MaskablePPO("MlpPolicy", venv, n_steps=HYPER["n_steps"], batch_size=HYPER["batch_size"],
                            gamma=HYPER["gamma"], learning_rate=HYPER["learning_rate"], ent_coef=HYPER["ent_coef"],
                            policy_kwargs={"net_arch": HYPER["net"]}, seed=args.seed, verbose=0, device="cpu")
        t1 = time.perf_counter()
        model.learn(total_timesteps=args.steps)
        train_s = round(time.perf_counter() - t1, 1)
        venv.close()
        teacher_path = out / "viper_teacher_pm.zip"
        model.save(teacher_path)
        print(f"teacher trained {args.steps} steps in {train_s}s", flush=True)
    else:
        teacher_path = args.teacher
        model = MaskablePPO.load(teacher_path, device="cpu")
    teacher = ppo_teacher(model)
    env = FundForgeEnv("pm", policy_id="viper")
    feats = distill.feature_names(env.layout)
    acts = distill.action_names(env.actions)

    test, val = opts(split_worlds["test"]), opts(split_worlds["val"])
    teacher_eps = [distill.rollout(env, distill.teacher_policy(teacher), teacher, o) for o in test]
    teacher_r = np.array([e.reward for e in teacher_eps])
    t_obs = np.concatenate([e.obs for e in teacher_eps])
    t_masks = np.concatenate([e.masks for e in teacher_eps])
    t_labels = np.concatenate([e.labels for e in teacher_eps])
    random_r = np.empty((args.random_runs, len(test)))
    for k in range(args.random_runs):
        rng = np.random.default_rng(k)
        for j, o in enumerate(test):
            random_r[k, j] = distill.rollout(
                env, lambda ob, m, rng=rng: int(rng.choice(np.flatnonzero(m))), teacher, o).reward
    val_teacher = float(np.mean([distill.rollout(env, distill.teacher_policy(teacher), teacher, o).reward
                                 for o in val]))

    per_depth: dict[str, Any] = {}
    for d in depths:
        t2 = time.perf_counter()
        students, n_samples = distill.viper(env, opts(split_worlds["train"]), teacher, depth=d,
                                            iterations=args.iterations, seed=args.seed)
        val_r = [float(np.mean([distill.rollout(env, st, teacher, o).reward for o in val])) for st in students]
        best = int(np.argmax(val_r))
        st = students[best]
        eps = [distill.rollout(env, st, teacher, o) for o in test]
        sr = np.array([e.reward for e in eps])
        per_depth[str(d)] = {
            "dataset_states": n_samples, "picked_iteration": best + 1, "val_mean_reward_by_iteration": val_r,
            "tree": st.size(),
            "fidelity_on_student_states": float(np.mean(np.concatenate([e.taken == e.labels for e in eps]))),
            "fidelity_on_teacher_states": float(np.mean(st.act_batch(t_obs, t_masks) == t_labels)),
            "test_states_student": int(sum(len(e.taken) for e in eps)),
            "summary": evals.summary(sr[None]),
            "vs_teacher": evals.compare(sr[None], teacher_r[None]),
            "vs_random": evals.compare(sr[None], random_r),
            "mean_score_bps": float(np.mean([float(e.outcome["score"]) for e in eps])),
            "labels": dict(Counter(e.outcome["label"] for e in eps)),
            "rules": st.rules(feats, acts),
            "seconds": round(time.perf_counter() - t2, 1),
        }
        m = per_depth[str(d)]
        print(f"depth {d}: leaves {m['tree']['leaves']}, fidelity {m['fidelity_on_student_states']:.3f}, "
              f"return {m['summary']['mean']['point']:.3f} (teacher {teacher_r.mean():.3f})", flush=True)

    small = [d for d in depths if d <= 4] or depths
    pick = max(small, key=lambda d: (per_depth[str(d)]["val_mean_reward_by_iteration"][
        per_depth[str(d)]["picked_iteration"] - 1], -d))
    print(f"\nexported tree: depth {pick}\n{per_depth[str(pick)]['rules']}")
    result = {
        "commit": git("rev-parse", "HEAD"), "worktree_dirty": bool(git("status", "--porcelain")),
        "reproduce": "cd ml && uv run --group train --with scikit-learn python scripts/distill_viper.py "
                     + " ".join(sys.argv[1:]),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
                     "sklearn": sklearn.__version__, "sb3_contrib": __import__("sb3_contrib").__version__,
                     "contract": CONTRACT_VERSION, "encoder": ENCODER_VERSION, "actions": ACTION_VERSION,
                     "reward": REWARD_VERSION},
        "seeds": {"torch_and_ppo": args.seed, "tree_random_state": args.seed,
                  "random_baseline": list(range(args.random_runs)),
                  "world_families": f"ppo-0..ppo-{args.families - 1}"},
        "scale": {"teacher_steps": args.steps if args.teacher is None else "loaded", "workers": args.workers,
                  "teacher_train_seconds": train_s, "teacher_hyperparameters": HYPER,
                  "viper_iterations": args.iterations, "families_drawn": args.families,
                  "families": {k: len(v) for k, v in splits.items()}, "rejected": dict(rejected),
                  "worlds": {k: len(v) for k, v in split_worlds.items()}},
        "teacher_sha256": hashlib.sha256(Path(teacher_path).read_bytes()).hexdigest(),
        "weight_proxy": "max minus min masked log-probability of the teacher over valid actions (see distill.py)",
        "selection": "per depth: VIPER iterate with best mean val reward; exported tree: depth <= 4 with best "
                     "val reward (ties to the shallower)",
        "test_worlds": [f"{s}/{v}" for s, v in split_worlds["test"]],
        "teacher": {"summary": evals.summary(teacher_r[None]), "val_mean_reward": val_teacher,
                    "test_states": len(t_labels),
                    "mean_score_bps": float(np.mean([float(e.outcome["score"]) for e in teacher_eps])),
                    "labels": dict(Counter(e.outcome["label"] for e in teacher_eps))},
        "random": {"summary": evals.summary(random_r)},
        "depths": per_depth,
        "exported_depth": pick,
        "exported_rules": per_depth[str(pick)]["rules"],
    }
    (out / "viper_pm.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out / 'viper_pm.json'} in {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
