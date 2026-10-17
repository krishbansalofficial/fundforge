"""Anomaly detection on the books (docs/ML_ANOMALY.md). Advises the deterministic controls; never replaces them.

Pipeline: generated worlds -> clean journal rows from real Session runs -> labelled copies with injected
anomalies (``anomaly_data``) -> features from the rows only (``anomaly_features``) -> Isolation Forest and a
small autoencoder fitted on clean training rows only -> thresholds chosen on validation -> precision,
recall and PR-AUC on held-out seed families, compared with the deterministic controls (``anomaly_controls``).
"""

import hashlib
import platform
import random
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any

import numpy as np
import sklearn
import torch
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, precision_recall_curve
from torch import nn

from . import worlds
from .anomaly_controls import CONTROLS, replay
from .anomaly_data import KINDS, inject, simulate
from .anomaly_features import FEATURE_NAMES, featurize, transform

Metrics = dict[str, Any]


@dataclass
class Corpus:
    X: np.ndarray  # (rows, features), transformed
    y: np.ndarray  # 1 on a footprint (entity, date) of an injected anomaly
    kind: np.ndarray  # "clean" or the anomaly kind of the copy
    split: np.ndarray
    flags: np.ndarray  # (rows, controls) boolean: the deterministic control flagged this row


def build(seeds: list[str], per_kind: int) -> tuple[Corpus, dict[str, Any]]:
    variants = worlds.variant_names()
    accounting: dict[str, Any] = {
        "requested_families": len(seeds),
        "accepted_families": 0,
        "rejected": {},
        "injections_applied": Counter(),
        "injections_not_applicable": Counter(),
        "copies": 0,
    }
    xs, ys, kinds, splits, flags = [], [], [], [], []
    t0 = time.perf_counter()
    for seed in seeds:
        variant = variants[int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % len(variants)]
        try:
            game = simulate(seed, variant)
        except worlds.WorldRejected as ex:
            accounting["rejected"][seed] = ex.failures
            continue
        accounting["accepted_families"] += 1
        plan: list[tuple[str, str, Any]] = [("clean", f"{seed}/clean", (game.rows, frozenset()))]
        for kind in KINDS:
            for k in range(per_kind):
                res = inject(game, kind, random.Random(f"{seed}|{kind}|{k}"), str(k))
                if res is None:
                    accounting["injections_not_applicable"][kind] += 1
                else:
                    accounting["injections_applied"][kind] += 1
                    plan.append((kind, f"{seed}/{kind}/{k}", res))
        for kind, _copy_id, (rows, footprint) in plan:
            X, keys = featurize(rows, game.evidence.calendar)
            fl = replay(rows, game.evidence)
            per_control = {c: {(f.entity, f.date) for f in fl if f.control == c} for c in CONTROLS}
            xs.append(transform(X))
            ys.append(np.array([k in footprint for k in keys], dtype=int))
            kinds.append(np.array([kind] * len(keys)))
            splits.append(np.array([game.split] * len(keys)))
            flags.append(np.array([[k in per_control[c] for c in CONTROLS] for k in keys], dtype=bool))
            accounting["copies"] += 1
    accounting["injections_applied"] = dict(accounting["injections_applied"])
    accounting["injections_not_applicable"] = dict(accounting["injections_not_applicable"])
    accounting["build_seconds"] = round(time.perf_counter() - t0, 1)
    corpus = Corpus(np.vstack(xs), np.concatenate(ys), np.concatenate(kinds), np.concatenate(splits), np.vstack(flags))
    return corpus, accounting


def train_autoencoder(x: np.ndarray, seed: int = 0, epochs: int = 40) -> nn.Sequential:
    torch.manual_seed(seed)
    gen = torch.Generator().manual_seed(seed)
    f = x.shape[1]
    model = nn.Sequential(
        nn.Linear(f, 8), nn.ReLU(), nn.Linear(8, 3), nn.ReLU(), nn.Linear(3, 8), nn.ReLU(), nn.Linear(8, f)
    )
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    data = torch.tensor(x, dtype=torch.float32)
    for _ in range(epochs):
        perm = torch.randperm(len(data), generator=gen)
        for i in range(0, len(data), 256):
            batch = data[perm[i : i + 256]]
            loss = ((model(batch) - batch) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    return model


def reconstruction_error(model: nn.Sequential, z: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        t = torch.tensor(z, dtype=torch.float32)
        return np.asarray(((model(t) - t) ** 2).mean(dim=1).numpy(), dtype=float)


def best_threshold(y: np.ndarray, score: np.ndarray) -> float:
    """Validation threshold that maximises F1; falls back to the clean 99th percentile if no positives."""
    if not y.any():
        return float(np.quantile(score[y == 0], 0.99))
    p, r, t = precision_recall_curve(y, score)
    f1 = 2 * p * r / np.maximum(p + r, 1e-12)
    return float(t[np.argmax(f1[:-1])])


def _metrics(y: np.ndarray, score: np.ndarray, ml: np.ndarray, ctrl: np.ndarray) -> Metrics:
    tp_ml, tp_c = int((ml & (y == 1)).sum()), int((ctrl & (y == 1)).sum())
    pos = int(y.sum())
    return {
        "positive_rows": pos,
        "negative_rows": int(len(y) - pos),
        "pr_auc": round(float(average_precision_score(y, score)), 4) if pos else None,
        "ml_precision": _ratio(tp_ml, int(ml.sum())),
        "ml_recall": _ratio(tp_ml, pos),
        "control_precision": _ratio(tp_c, int(ctrl.sum())),
        "control_recall": _ratio(tp_c, pos),
        "ml_flagged_negatives": int((ml & (y == 0)).sum()),
        "control_flagged_negatives": int((ctrl & (y == 0)).sum()),
        "ml_only": int((ml & ~ctrl & (y == 1)).sum()),
        "control_only": int((ctrl & ~ml & (y == 1)).sum()),
        "both": int((ml & ctrl & (y == 1)).sum()),
        "neither": int((~ml & ~ctrl & (y == 1)).sum()),
    }


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 4) if b else None


def _ml_block(c: Corpus, score: np.ndarray, thr: float) -> dict[str, Any]:
    val, test = c.split == "val", c.split == "test"
    ctrl_any = c.flags.any(axis=1)
    ml_pred = score >= thr
    per_kind: dict[str, Any] = {}
    for k in KINDS:
        m = test & ((c.kind == "clean") | (c.kind == k))
        block = _metrics(c.y[m], score[m], ml_pred[m], ctrl_any[m])
        block["control_recall_by_control"] = {
            name: _ratio(int((c.flags[m, i] & (c.y[m] == 1)).sum()), int(c.y[m].sum()))
            for i, name in enumerate(CONTROLS)
        }
        per_kind[k] = block
    overall = _metrics(c.y[test], score[test], ml_pred[test], ctrl_any[test])
    clean_test = test & (c.kind == "clean")
    return {
        "threshold_from_validation": round(thr, 6),
        "validation_positive_rows": int(c.y[val].sum()),
        "per_kind_test": per_kind,
        "all_kinds_test": overall,
        "clean_test_false_positive_rate": _ratio(int(ml_pred[clean_test].sum()), int(clean_test.sum())),
        "clean_test_rows": int(clean_test.sum()),
    }


def evaluate(c: Corpus, seed: int = 0) -> dict[str, Any]:
    train_clean = (c.split == "train") & (c.kind == "clean")
    mu = c.X[train_clean].mean(axis=0)
    sd = c.X[train_clean].std(axis=0)
    sd[sd == 0] = 1.0
    z = np.clip((c.X - mu) / sd, -10, 10)
    val, test = c.split == "val", c.split == "test"
    results: dict[str, Any] = {}
    t0 = time.perf_counter()
    iso = IsolationForest(n_estimators=200, random_state=seed).fit(z[train_clean])
    s_if = -iso.score_samples(z)
    results["isolation_forest"] = _ml_block(c, s_if, best_threshold(c.y[val], s_if[val]))
    fit_if = round(time.perf_counter() - t0, 2)
    t1 = time.perf_counter()
    ae = train_autoencoder(z[train_clean], seed)
    s_ae = reconstruction_error(ae, z)
    results["autoencoder"] = _ml_block(c, s_ae, best_threshold(c.y[val], s_ae[val]))
    fit_ae = round(time.perf_counter() - t1, 2)
    ctrl_any = c.flags.any(axis=1)
    clean_test = test & (c.kind == "clean")
    results["controls"] = {
        "clean_train_rows_flagged": int(ctrl_any[train_clean].sum()),
        "clean_test_rows_flagged": int(ctrl_any[clean_test].sum()),
        "clean_test_rows": int(clean_test.sum()),
    }
    results["fit_seconds"] = {"isolation_forest": fit_if, "autoencoder": fit_ae}
    results["feature_columns"] = list(FEATURE_NAMES)
    results["train_clean_rows"] = int(train_clean.sum())
    return results


def run(seeds: list[str], per_kind: int) -> dict[str, Any]:
    corpus, accounting = build(seeds, per_kind)
    splits = {s: int(((corpus.split == s) & (corpus.kind == "clean")).sum()) for s in ("train", "val", "test")}
    models = evaluate(corpus)
    return {
        "splits_clean_rows": splits,
        "copies": accounting["copies"],
        "rows": len(corpus.y),
        "dataset": accounting,
        "rows_per_split_kind": {
            s: {k: int(((corpus.split == s) & (corpus.kind == k)).sum()) for k in ("clean", *KINDS)}
            for s in ("train", "val", "test")
        },
        "positive_rows_per_split_kind": {
            s: {k: int(corpus.y[(corpus.split == s) & (corpus.kind == k)].sum()) for k in KINDS}
            for s in ("train", "val", "test")
        },
        "models": models,
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "torch": torch.__version__,
        },
    }
