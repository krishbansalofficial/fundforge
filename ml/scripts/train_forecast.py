"""Train and score regime forecasters against the exact Bayes posterior (docs/ML_FORECAST.md).

    cd ml && uv run --group forecast python scripts/train_forecast.py --worlds 20000

Generates ungated case1 worlds ``forecast-{i}``, splits whole seed families with ``split_of``,
fits logistic regression (numpy IRLS), LightGBM and a small PyTorch MLP on train, early-stops on
val, and scores everything on test. Writes ml/results/forecast.json.
"""

import argparse
import json
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import torch
from fundforge.generator import GEN_VERSION, MACRO_VERSION

from fundforge_ml import forecast
from fundforge_ml.contracts import CONTRACT_VERSION, SPLIT_SALT

OUT = Path(__file__).parents[1] / "results" / "forecast.json"
SEED = 20261015


def logreg(x: np.ndarray, y: np.ndarray, l2: float = 1e-3, iters: int = 50) -> np.ndarray:
    """L2-regularised logistic regression by Newton's method; returns weights with a bias last."""
    a = np.hstack([x, np.ones((len(x), 1))])
    w = np.zeros(a.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-a @ w))
        g = a.T @ (p - y) / len(y) + l2 * w
        h = (a * (p * (1 - p))[:, None]).T @ a / len(y) + l2 * np.eye(len(w))
        step = np.linalg.solve(h, g)
        w -= step
        if np.abs(step).max() < 1e-10:
            break
    return w


def logreg_predict(w: np.ndarray, x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-(np.hstack([x, np.ones((len(x), 1))]) @ w)))  # type: ignore[no-any-return]


def fit_lgbm(xt: np.ndarray, yt: np.ndarray, xv: np.ndarray, yv: np.ndarray) -> lgb.Booster:
    params = {"objective": "binary", "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 50,
              "deterministic": True, "force_row_wise": True, "num_threads": 4, "seed": SEED, "verbose": -1}
    return lgb.train(params, lgb.Dataset(xt, yt), num_boost_round=3000, valid_sets=[lgb.Dataset(xv, yv)],
                     callbacks=[lgb.early_stopping(100, verbose=False)])


def fit_mlp(xt: np.ndarray, yt: np.ndarray, xv: np.ndarray, yv: np.ndarray) -> tuple[torch.nn.Module, int]:
    torch.manual_seed(SEED)
    torch.set_num_threads(1)
    net = torch.nn.Sequential(torch.nn.Linear(xt.shape[1], 64), torch.nn.ReLU(), torch.nn.Linear(64, 64),
                              torch.nn.ReLU(), torch.nn.Linear(64, 1))
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    xt_t, yt_t = torch.tensor(xt, dtype=torch.float32), torch.tensor(yt, dtype=torch.float32)
    xv_t, yv_t = torch.tensor(xv, dtype=torch.float32), torch.tensor(yv, dtype=torch.float32)
    gen = torch.Generator().manual_seed(SEED)
    best, best_state, best_epoch, patience = float("inf"), None, 0, 0
    for epoch in range(200):
        net.train()
        perm = torch.randperm(len(xt_t), generator=gen)
        for start in range(0, len(perm), 512):
            idx = perm[start:start + 512]
            opt.zero_grad()
            loss_fn(net(xt_t[idx]).squeeze(1), yt_t[idx]).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            v = loss_fn(net(xv_t).squeeze(1), yv_t).item()
        if v < best - 1e-5:
            best, best_state, best_epoch, patience = v, {k: t.clone() for k, t in net.state_dict().items()}, epoch, 0
        else:
            patience += 1
            if patience >= 15:
                break
    assert best_state is not None
    net.load_state_dict(best_state)
    return net, best_epoch + 1


def mlp_predict(net: torch.nn.Module, x: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        return torch.sigmoid(net(torch.tensor(x, dtype=torch.float32)).squeeze(1)).double().numpy()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=20000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    t0 = time.time()
    seeds = [f"forecast-{i}" for i in range(args.worlds)]
    with ProcessPoolExecutor(args.workers) as pool:
        samples = [s for batch in pool.map(forecast.world_samples, seeds, chunksize=100) for s in batch]
    gen_s = time.time() - t0

    def part(name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], np.ndarray]:
        rows = [s for s in samples if s.split == name]
        return (np.stack([s.x for s in rows]), np.array([s.y for s in rows], dtype=float),
                np.array([s.bayes for s in rows]), np.array([s.prior for s in rows]),
                [s.seed_family for s in rows], np.array([s.as_of for s in rows]))

    xt, yt, *_ = part("train")
    xv, yv, *_ = part("val")
    xs, ys, bs, ps, fs, days = part("test")
    families = {n: len({s.seed_family for s in samples if s.split == n}) for n in ("train", "val", "test")}
    assert not ({s.seed_family for s in samples if s.split == "train"}
                & {s.seed_family for s in samples if s.split == "test"})

    t1 = time.time()
    w = logreg(xt, yt)
    booster = fit_lgbm(xt, yt, xv, yv)
    net, epochs = fit_mlp(xt, yt, xv, yv)
    fit_s = time.time() - t1
    preds = {
        "bayes_exact_filter": bs,
        "chain_prior_only": ps,
        "logistic_regression": logreg_predict(w, xs),
        "lightgbm": booster.predict(xs, num_iteration=booster.best_iteration),
        "torch_mlp": mlp_predict(net, xs),
    }
    models = {name: forecast.score(np.asarray(p, dtype=float), ys, bs, fs) for name, p in preds.items()}
    by_day = {int(d): {name: forecast.brier(np.asarray(p)[days == d], ys[days == d]) for name, p in preds.items()}
              | {"n": int((days == d).sum())} for d in sorted(set(days.tolist()))}
    result: dict[str, Any] = {
        "task": "P(stressed) for the latest published Street activity period, from published prints only",
        "reproduce": f"cd ml && uv run --group forecast python scripts/train_forecast.py --worlds {args.worlds}",
        "versions": {"feature": forecast.FEATURE_VERSION, "generator": GEN_VERSION, "macro": MACRO_VERSION,
                     "contracts": CONTRACT_VERSION, "python": sys.version.split()[0], "numpy": np.__version__,
                     "lightgbm": lgb.__version__, "torch": torch.__version__, "platform": platform.platform()},
        "data": {"worlds": args.worlds, "seed_pattern": "forecast-{i}, i in [0, worlds)", "variant": "base",
                 "balance_gate": "not applied (the filter is exact for the ungated generator distribution)",
                 "split": f"contracts.split_of(seed_family), salt {SPLIT_SALT!r}; whole families held out",
                 "families": families, "samples": {"train": len(yt), "val": len(yv), "test": len(ys)},
                 "test_stressed_rate": float(ys.mean())},
        "metrics_note": "Binary Brier on P(stressed) (research.brier's two-state score is 2x). ECE over 10 "
                        "equal-width bins. gap_* = model minus exact Bayes filter on the same test rows; "
                        "gap_brier_se_by_world is the standard error of per-world mean gaps.",
        "training": {"seed": SEED, "lightgbm_best_iteration": booster.best_iteration, "mlp_epochs": epochs,
                     "logreg": "numpy Newton/IRLS, l2 1e-3"},
        "test": models,
        "test_brier_by_as_of_day": by_day,
        "seconds": {"generate": round(gen_s, 1), "fit": round(fit_s, 1)},
    }
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                        encoding="utf-8")
    for name, m in models.items():
        print(f"{name:22s} n={m['n']} brier={m['brier']:.5f} logloss={m['log_loss']:.5f} ece={m['ece']:.4f} "
              f"gap={m['gap_brier']:+.5f}+/-{m['gap_brier_se_by_world']:.5f} |p-bayes|={m['mean_abs_to_bayes']:.4f}")


if __name__ == "__main__":
    main()
