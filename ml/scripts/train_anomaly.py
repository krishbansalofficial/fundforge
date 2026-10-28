"""Unsupervised anomaly detection on the books, scored on the labelled B5 fault corpus.

    cd ml && uv run --group anomaly python scripts/train_anomaly.py --seeds 40 --clean-seasons 40

Question: with no knowledge of the control rules, can a model trained only on clean books rediscover which
checkpoints are faulty, and which fault classes does it miss? The rule-based controls are the reference.

Data. The B5 clean seasons are only four deterministic golden paths (eight with a matching statement), too few to
learn "normal" from: in a leave-one-path-out pilot every held-out golden path already looked novel. So clean
training data are seeded *random-policy* seasons on the same Case1 tape: at each execution barrier the policy
submits 0-2 random orders and occasionally assigns borrow research, accepts the replacement or sets a reserve;
rejected commands are skipped. Odd seeds also carry a broker statement that matches the broker record at a
random day (as the B5 "+matching_statement" seasons do). Unfaulted engine state is clean by construction; the
B5 controls are also run on every random checkpoint and their flags are reported (not used to filter).

Models, all fit on train clean rows only: IsolationForest; Mahalanobis distance under a Ledoit-Wolf covariance;
and ``anomaly.max_abs_z`` (largest per-feature |z|).

Split by season seed: random seeds [0, 0.75 n) train; the rest plus all eight B5 golden clean seasons are the
held-out clean set. Faulty checkpoints are ``fault_corpus.make(cls, seed)`` for every class and seed, featurised
right after injection at the barrier the B5 layers score. Fault class/variant are labels only.

Threshold: the flag is ``score > t`` with ``t`` the smallest value leaving at most floor(1% x n) held-out clean
checkpoints flagged.

``backend/tests/fault_corpus.py`` is imported here via sys.path, as scripts/bench_controls.py does; it stays out
of the ``fundforge_ml`` package so the package never depends on backend test code.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import platform
import random
import subprocess
import sys
import time
from collections.abc import Callable
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.covariance import LedoitWolf
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "tests"))

from fault_corpus import _TAPE, CLASSES, PATHS, clean_seasons, drive, layers, make  # noqa: E402
from fundforge.engine import RULES_VERSION, CommandRejected, Engine, InvariantError  # noqa: E402
from fundforge.tape import Tape, compile_tape  # noqa: E402

from fundforge_ml import anomaly  # noqa: E402
from fundforge_ml.evals import bootstrap_ci, mean  # noqa: E402

OUT = ROOT / "ml" / "results" / "anomaly.json"
B5 = ROOT / "bench" / "results" / "2026-10-17-B5-b1dc767.json"
MODEL_SEED = 20261027
BOOT_REPS = 2000
FPR_TARGET = 0.01
SIDES = ("BUY", "SELL", "SHORT", "COVER")


def random_script(seed: int) -> dict[tuple[int, str], Callable[[Engine], None]]:
    """A seeded random policy; every decision is drawn up front so the season is deterministic."""
    rng = random.Random(f"anomaly-clean:{seed}")
    syms = sorted(_TAPE.instruments)
    script: dict[tuple[int, str], Callable[[Engine], None]] = {}
    for ev in _TAPE.events:
        if ev.phase not in ("EXEC_A", "EXEC_B"):
            continue
        acts: list[tuple[Any, ...]] = [("order", f"r{seed}-{ev.day}{ev.phase}-{k}", rng.choice(syms),
                                        rng.choice(SIDES), rng.randint(100, 20_000))
                                       for k in range(rng.choice((0, 0, 1, 1, 2)))]
        if rng.random() < 0.1:
            acts.append(("research",))
        if rng.random() < 0.1:
            acts.append(("accept",))
        if rng.random() < 0.05:
            acts.append(("reserve", Decimal(rng.randint(0, 2_000_000))))

        def apply(e: Engine, acts: list[tuple[Any, ...]] = acts) -> None:
            for a in acts:
                with contextlib.suppress(CommandRejected):
                    if a[0] == "order":
                        e.submit_order(*a[1:])
                    elif a[0] == "research":
                        e.assign_research("borrow")
                    elif a[0] == "accept":
                        e.accept_replacement()
                    else:
                        e.set_reserve(a[1])

        script[(ev.day, ev.phase)] = apply
    return script


def matching_statement_tape(seed: int, script: dict[Any, Any]) -> Tape:
    """Like fault_corpus.statement_tape with delta 0: a broker statement equal to the record, at a random day."""
    rng = random.Random(f"anomaly-statement:{seed}")
    day, account = rng.randint(13, 19), rng.choice(["cash", "collateral", "debt"])
    actual = drive(_TAPE, script, (day, "EXEC_A")).broker.snapshots[(day, 0)][account]
    raw = copy.deepcopy(_TAPE.raw)
    raw["broker_statements"] = [{"id": f"clean-{account}-{day}", "revision": 1, "source": "anomaly clean statement",
                                 "account": account, "as_of": {"day": day, "phase": "OPEN_ADMIN"},
                                 "available_at": {"day": day, "phase": "PUBLIC_MARK"}, "balance": str(actual)}]
    return compile_tape(raw)


def season_rows(season: str, group: str, tape: Tape, script: dict[Any, Any], audit: bool) -> list[dict[str, Any]]:
    """Every decision barrier of an unfaulted season, as fault_corpus.clean_checkpoints walks it."""
    rows = []
    e = Engine(tape)
    e.advance()
    while True:
        done = e.finished()
        at = ["end", ""] if done else [e.next_event().day, e.next_event().phase]
        row = {"season": season, "group": group, "at": at, "x": anomaly.features(anomaly.book_state(e))}
        if audit:
            lay = layers(e)
            row["controls_flag"] = bool(lay["reconcile_code"] or lay["control_codes"] or lay["certificate_reasons"])
        rows.append(row)
        if done:
            return rows
        nxt = e.next_event()
        if (nxt.day, nxt.phase) in script:
            script[(nxt.day, nxt.phase)](e)
        e.advance()


def clean_rows(n_random: int) -> tuple[list[dict[str, Any]], list[int]]:
    rows, failed = [], []
    n_train = int(0.75 * n_random)
    for seed in range(n_random):
        script = random_script(seed)
        tape = matching_statement_tape(seed, script) if seed % 2 else _TAPE
        try:
            rows += season_rows(f"random-{seed}", "train" if seed < n_train else "heldout_random", tape, script,
                                audit=True)
        except InvariantError:
            failed.append(seed)
    for season, (tape, script) in clean_seasons().items():
        rows += season_rows(season, "heldout_golden", tape, script, audit=False)
    return rows, failed


def fault_rows(seeds: int) -> list[dict[str, Any]]:
    rows = []
    for cls in CLASSES:
        for seed in range(seeds):
            f = make(cls, seed)
            with f.patch():
                e = drive(f.tape, PATHS[f.path], f.at)
                f.inject(e)
                x = anomaly.features(anomaly.book_state(e))
            rows.append({"class": cls, "seed": seed, "path": f.path, "at": list(f.at), "variant": f.variant, "x": x})
    return rows


def isolation_forest(train: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    m = IsolationForest(n_estimators=500, random_state=MODEL_SEED).fit(train)
    return lambda x: -m.score_samples(x)


def ledoit_wolf(train: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    """Mahalanobis distance under a shrunk covariance of standardised features (std floored at 1e-6)."""
    mu, sd = train.mean(0), np.maximum(train.std(0), 1e-6)
    m = LedoitWolf().fit((train - mu) / sd)
    return lambda x: m.mahalanobis((x - mu) / sd)


MODELS = {"isolation_forest": isolation_forest, "ledoit_wolf_mahalanobis": ledoit_wolf,
          "max_abs_z": anomaly.max_abs_z}


def pr_auc_ci(pos: np.ndarray, neg: np.ndarray, seed: int) -> dict[str, float]:
    def ap(p: np.ndarray, n: np.ndarray) -> float:
        return float(average_precision_score(np.r_[np.ones(len(p)), np.zeros(len(n))], np.r_[p, n]))

    rng = np.random.default_rng(seed)
    boot = [ap(rng.choice(pos, len(pos)), rng.choice(neg, len(neg))) for _ in range(BOOT_REPS)]
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return {"point": ap(pos, neg), "lo": float(lo), "hi": float(hi)}


def score(model: str, clean: list[dict[str, Any]], faults: list[dict[str, Any]]) -> dict[str, Any]:
    fn = MODELS[model](np.array([r["x"] for r in clean if r["group"] == "train"]))
    held = [r for r in clean if r["group"] != "train"]
    neg = fn(np.array([r["x"] for r in held]))
    allowed = int(FPR_TARGET * len(neg))
    t = float(np.sort(neg)[::-1][allowed])
    out: dict[str, Any] = {
        "threshold": t, "allowed_false_positives": allowed,
        "held_out_clean": {"n": len(neg), "flagged": int((neg > t).sum()), "fpr": float((neg > t).mean())},
        "held_out_clean_by_group": {g: {"n": int(sum(r["group"] == g for r in held)),
                                        "flagged": int(sum(s > t for s, r in zip(neg, held, strict=True)
                                                           if r["group"] == g))}
                                    for g in ("heldout_random", "heldout_golden")},
        "per_class": {}}
    scores = fn(np.array([r["x"] for r in faults]))
    for i, cls in enumerate(CLASSES):
        idx = [k for k, r in enumerate(faults) if r["class"] == cls]
        pos = scores[idx]
        hits = (pos > t).astype(np.float64)
        rows = [faults[k] for k in idx]
        out["per_class"][cls] = {
            "n": len(rows), "detected": int(hits.sum()),
            "recall_at_1pct_fpr": bootstrap_ci(hits, mean, reps=BOOT_REPS, seed=i),
            "pr_auc": pr_auc_ci(pos, neg, seed=i),
            "variants": {v: f"{sum(h for h, r in zip(hits, rows, strict=True) if r['variant'] == v):.0f}/"
                            f"{sum(r['variant'] == v for r in rows)}" for v in sorted({r["variant"] for r in rows})},
        }
    return out


def commit() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "ml", "backend"], capture_output=True, text=True,
                           cwd=ROOT).stdout
    return head.strip() + ("+dirty" if dirty.strip() else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40, help="faults per class (B5 used 40)")
    ap.add_argument("--clean-seasons", type=int, default=40, help="seeded random-policy clean seasons")
    args = ap.parse_args()
    t0 = time.perf_counter()
    (clean, failed), faults = clean_rows(args.clean_seasons), fault_rows(args.seeds)
    b5 = json.loads(B5.read_text(encoding="utf-8"))
    b5_variants = {(r["class"], r["seed"]): r["variant"] for r in b5["faults"]}
    same = all(b5_variants.get((r["class"], r["seed"])) == r["variant"] for r in faults)
    models = {m: score(m, clean, faults) for m in MODELS}
    controls = {cls: {k: b5["summary"]["per_class"][cls][k] for k in ("n", "controls", "certificate", "reconcile",
                                                                       "independent")} for cls in CLASSES}
    audited = [r for r in clean if "controls_flag" in r]
    doc = {
        "experiment": "unsupervised anomaly detection on the books vs B5 rule-based controls",
        "commit": commit(),
        "rules_version": RULES_VERSION,
        "feature_version": anomaly.FEATURE_VERSION,
        "n_features": len(anomaly.FEATURE_NAMES),
        "versions": {"python": platform.python_version(), "numpy": version("numpy"),
                     "scikit-learn": version("scikit-learn")},
        "reproduce": f"cd ml && uv run --group anomaly python scripts/train_anomaly.py --seeds {args.seeds} "
                     f"--clean-seasons {args.clean_seasons}",
        "seeds": {"fault_corpus": f"fault_corpus.make(cls, seed) for seed in range({args.seeds})",
                  "clean_random_policy": f"random.Random('anomaly-clean:<seed>') for seed in "
                                         f"range({args.clean_seasons}); train = seed < "
                                         f"{int(0.75 * args.clean_seasons)}",
                  "isolation_forest_random_state": MODEL_SEED,
                  "bootstrap": f"{BOOT_REPS} reps, numpy default_rng(class index)"},
        "split": "by clean season seed; held-out clean = held-out random seasons + the 8 B5 golden clean seasons",
        "sizes": {"clean_checkpoints_by_group": {g: sum(r["group"] == g for r in clean)
                                                 for g in ("train", "heldout_random", "heldout_golden")},
                  "random_seasons_failed_invariant": failed,
                  "faults_per_class": args.seeds, "faults": len(faults)},
        "random_clean_controls_audit": {"checkpoints": len(audited),
                                        "flagged_by_controls": sum(r["controls_flag"] for r in audited)},
        "threshold_rule": f"score > t; t leaves at most floor({FPR_TARGET} x n) held-out clean checkpoints flagged",
        "controls_reference": {"file": str(B5.relative_to(ROOT)).replace("\\", "/"), "commit": b5["commit"],
                               "same_faults": same, "clean": b5["summary"]["clean"], "per_class": controls},
        "models": models,
        "wall_seconds": round(time.perf_counter() - t0, 1),
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print("sizes", doc["sizes"], "controls audit", doc["random_clean_controls_audit"])
    for m, res in models.items():
        print(m, "clean", res["held_out_clean"], res["held_out_clean_by_group"])
        for cls, r in res["per_class"].items():
            print(f"  {cls:30s} recall {r['detected']}/{r['n']}  PR-AUC {r['pr_auc']['point']:.3f}  "
                  f"controls {controls[cls]['controls']}/{controls[cls]['n']}")
    print(f"same faults as B5: {same}; wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
