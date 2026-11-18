"""Stage 5.3: split conformal prediction sets for the regime forecaster.

Run from ml/:  uv run --group forecast python scripts/conformal_forecast.py --worlds 20000

Same worlds, features, split and LightGBM fit as train_forecast.py (val is used for early stopping, so it is not
reused here). The held-out TEST families are split in half by a family hash: one half calibrates, the other is
scored. For alpha in {0.05, 0.10, 0.20}, standard and class-conditional (Mondrian) calibration, report empirical
coverage, per-class coverage, set sizes, coverage by as-of day, and a 95% family-bootstrap interval for coverage.
The exact Bayes filter is conformalised the same way, as the reference for how small sets can be.
Caveat: samples of one world are dependent; exchangeability holds across families, not rows.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from train_forecast import fit_lgbm

from fundforge_ml import conformal as C
from fundforge_ml import forecast

ML = Path(__file__).parents[1]
ALPHAS = (0.05, 0.10, 0.20)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ML, capture_output=True, text=True, check=False).stdout.strip()


def half(family: str) -> str:
    return "calibrate" if hashlib.sha256(f"conformal-v1:{family}".encode()).digest()[0] < 128 else "score"


def boot_coverage(covered: np.ndarray, fam: np.ndarray, rng: np.random.Generator, n: int = 1000) -> list[float]:
    uniq, inv = np.unique(fam, return_inverse=True)
    hits, count = np.bincount(inv, covered), np.bincount(inv)
    draws = rng.integers(0, len(uniq), (n, len(uniq)))
    cov = hits[draws].sum(axis=1) / count[draws].sum(axis=1)
    return [round(float(np.quantile(cov, 0.025)), 4), round(float(np.quantile(cov, 0.975)), 4)]


def main() -> dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=20000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", type=Path, default=ML / "results" / "conformal_forecast.json")
    a = ap.parse_args()
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as pool:
        samples = [s for b in pool.map(forecast.world_samples, [f"forecast-{i}" for i in range(a.worlds)],
                                       chunksize=100) for s in b]

    def part(rows: list[Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        return (np.stack([s.x for s in rows]), np.array([s.y for s in rows], dtype=int),
                np.array([s.bayes for s in rows]), np.array([s.seed_family for s in rows]),
                np.array([s.as_of for s in rows]))

    xt, yt, *_ = part([s for s in samples if s.split == "train"])
    xv, yv, *_ = part([s for s in samples if s.split == "val"])
    test = [s for s in samples if s.split == "test"]
    booster = fit_lgbm(xt, yt.astype(float), xv, yv.astype(float))
    xs, ys, bs, fs, days = part(test)
    preds = {"lightgbm": booster.predict(xs, num_iteration=booster.best_iteration), "bayes_exact_filter": bs}
    is_cal = np.array([half(f) == "calibrate" for f in fs])
    rng = np.random.default_rng(20261118)
    out: dict[str, Any] = {}
    for name, p in preds.items():
        out[name] = {}
        for alpha in ALPHAS:
            for mondrian in (False, True):
                q = C.calibrate(p[is_cal], ys[is_cal], alpha, mondrian)
                s = C.sets(p[~is_cal], q)
                y, f, d = ys[~is_cal], fs[~is_cal], days[~is_cal]
                covered = s[np.arange(len(y)), y]
                out[name][f"alpha_{alpha}_{'mondrian' if mondrian else 'marginal'}"] = {
                    "target": 1 - alpha, "qhat": q, **{k: round(v, 4) for k, v in C.evaluate(s, y).items()},
                    "coverage_ci95_by_family": boot_coverage(covered.astype(float), f, rng),
                    "coverage_by_as_of_day": {int(k): round(float(covered[d == k].mean()), 4)
                                              for k in sorted(set(d.tolist()))},
                }
    doc = {
        "stage": "5.3 conformal regime forecast",
        "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain", "--", "src", "scripts")),
        "reproduce": f"cd ml && uv run --group forecast python scripts/conformal_forecast.py --worlds {a.worlds}",
        "method": "split conformal, score 1 - p(true class), qhat = k-th smallest calibration score with "
                  "k = ceil((n+1)(1-alpha)); Mondrian = per-class calibration; "
                  "Angelopoulos and Bates, arXiv 2107.07511",
        "data": {"worlds": a.worlds, "calibration_rows": int(is_cal.sum()), "scored_rows": int((~is_cal).sum()),
                 "calibration_families": len(set(fs[is_cal].tolist())),
                 "scored_families": len(set(fs[~is_cal].tolist())),
                 "split": "test families halved by sha256('conformal-v1:' + family); val kept for early stopping",
                 "lightgbm_best_iteration": booster.best_iteration},
        "caveat": "rows of one world are dependent; the guarantee is over exchangeable families, so read the "
                  "family-bootstrap interval, not a row-count binomial",
        "results": out,
        "python": sys.version.split()[0],
        "seconds": round(time.time() - t0, 1),
    }
    a.out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    for name in out:
        for k, v in out[name].items():
            print(f"{name:20s} {k:22s} cov {v['coverage']:.4f} {v['coverage_ci95_by_family']} "
                  f"size {v['mean_size']:.3f} both {v['share_both']:.3f} empty {v['share_empty']:.3f}")
    return doc


if __name__ == "__main__":
    main()
