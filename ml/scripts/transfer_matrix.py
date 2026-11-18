"""Stage 5.1: generalisation matrix. Does PPO trained on one world distribution transfer to the other?

Run from ml/ (needs the published checkpoints eval_ppo.py wrote to results/*.zip):
  uv run --group train python scripts/transfer_matrix.py --procs 4

Rows: train level (base, hard). Columns: test level (base, hard). Each cell plays the 5 published checkpoints of
that training level (sha256 checked against ppo_pm.json / ppo_pm_hard.json) on the published test split of the
test level (``test_world_order``, same worlds and order), next to seeded random-valid play on the same worlds, and
reports evals.summary plus the paired PPO - random comparison. No training. Writes results/transfer_matrix.json.
"""

import argparse
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from eval_ppo import ML, _git, play_block, report

SOURCES = {"base": ("ppo_pm.json", "ppo_pm"), "hard": ("ppo_pm_hard.json", "ppo_pm_hard")}
CONFIG = "lr1e-4_ent0.01"  # base's val-selected config; hard was trained with it fixed


def checkpoints(results: Path, level: str) -> tuple[dict[str, Any], list[str]]:
    name, stem = SOURCES[level]
    src = json.loads((results / name).read_text(encoding="utf-8"))
    runs = src["grid"][CONFIG]["runs"]
    paths = [str(results / f"{stem}_{CONFIG}_s{r['seed']}.zip") for r in runs]
    for r, p in zip(runs, paths, strict=True):
        if hashlib.sha256(Path(p).read_bytes()).hexdigest() != r["sha256"]:
            raise SystemExit(f"{p} does not match the sha256 in {name}")
    return src, paths


def main(argv: list[str] | None = None) -> dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--models", default=str(ML / "results"))
    ap.add_argument("--random-runs", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0, help="first N test worlds per level (smoke)")
    ap.add_argument("--out", default=str(ML / "results" / "transfer_matrix.json"))
    args = ap.parse_args(argv)
    results = Path(args.models)
    srcs = {lv: checkpoints(results, lv) for lv in SOURCES}
    rnd: list[tuple[str | None, int]] = [(None, k) for k in range(args.random_runs)]
    cells: dict[str, Any] = {}
    t0 = time.perf_counter()
    with ProcessPoolExecutor(args.procs) as pool:
        for test_level, (test_src, _) in srcs.items():
            ws = [tuple(x.split("/")) for x in test_src["test_world_order"]]
            ws = ws[: args.limit] if args.limit else ws
            runs = {f"ppo_{tl}": ("ppo", [(p, 0) for p in paths]) for tl, (_, paths) in srcs.items()}
            rows = play_block(pool, "pm", test_level, ws, {**runs, "random": ("random", rnd)})
            for tl in srcs:
                r = report({"ppo": rows[f"ppo_{tl}"], "random": rows["random"]})
                cells[f"train_{tl}/test_{test_level}"] = {
                    "test_worlds": len(ws),
                    "ppo": r["policies"]["ppo"],
                    "random": r["policies"]["random"],
                    "ppo_vs_random": r["compare"]["ppo_vs_random"],
                }
            print(f"test {test_level}: {len(ws)} worlds done", flush=True)
    doc = {
        "stage": "5.1 generalisation matrix",
        "question": "does MaskablePPO (pm seat) trained on base or hard worlds transfer to the other "
                    "level's test split?",
        "commit": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", "src", "scripts")),
        "reproduce": "cd ml && uv run --group train python scripts/transfer_matrix.py --procs " + str(args.procs),
        "scale": {"config": CONFIG, "checkpoints_per_train_level": 5, "random_runs": args.random_runs,
                  "sources": {lv: {"file": SOURCES[lv][0], "commit": s["commit"]} for lv, (s, _) in srcs.items()},
                  "note": "same published checkpoints and test splits as the source results; no training here"},
        "cells": cells,
        "wall_seconds": round(time.perf_counter() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc


if __name__ == "__main__":
    main()
