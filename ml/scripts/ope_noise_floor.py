"""Stage 5.4 sanity check: how much does random-valid play's mean return move between independent seed sets?

Run from ml/:  uv run --group train --group forecast python scripts/ope_noise_floor.py --procs 4

The OPE truth and logged data use different seed sets of the same random policy; if those sets disagree by more
than their standard errors, estimator errors smaller than that spread are noise, not bias. Same worlds as
ope_eval.py (hard test split), 10 episodes per world per set. Writes results/ope_noise_floor.json.
"""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from eval_ppo import ML, _git
from ope_eval import episode

SETS = (10_000, 20_000, 30_000)  # 10_000: ope_eval's logged data; 20_000: its truth runs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    src = json.loads((ML / "results" / "ppo_pm_hard.json").read_text(encoding="utf-8"))
    ws = [tuple(x.split("/")) for x in src["test_world_order"]]
    sets = {}
    with ProcessPoolExecutor(a.procs) as pool:
        for base in SETS:
            jobs = [(s, v, "random", base + k) for s, v in ws for k in range(10)]
            r = np.array([sum(st.reward for st in e) for _, e in pool.map(episode, jobs, chunksize=8)])
            per_world = r.reshape(len(ws), 10).mean(axis=1)
            sets[str(base)] = {"mean": round(float(r.mean()), 4),
                               "se_by_world": round(float(per_world.std(ddof=1) / np.sqrt(len(ws))), 4),
                               "episodes": len(r), "max_return": round(float(r.max()), 3),
                               "min_return": round(float(r.min()), 3)}
            print(base, sets[str(base)], flush=True)
    means = [v["mean"] for v in sets.values()]
    doc = {"stage": "5.4 OPE noise floor", "commit": _git("rev-parse", "HEAD"),
           "dirty": bool(_git("status", "--porcelain", "--", "src", "scripts")),
           "reproduce": f"cd ml && uv run --group train --group forecast python scripts/ope_noise_floor.py "
                        f"--procs {a.procs}",
           "worlds": len(ws), "seed_sets": sets, "spread": round(max(means) - min(means), 4)}
    (ML / "results" / "ope_noise_floor.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
