"""Regime forecasting scored against known ground truth.

Question (the terminal's live research question): was the hidden regime stressed on the latest
period whose Street activity print is published? A model sees only the published prints, in the
exact row format the seat-facing terminal serves (``fundforge.terminal.snapshot(...)["macro"]``):
``series, period_day, published_day, revision, value``. ``features`` drops every row whose
``published_day`` is after the as-of day and keeps the latest revision per period, so future prints
or revisions cannot change a feature (tests/test_forecast.py). The hidden regime is read
from the generator output only as the label.

The ceiling is ``fundforge.research.regime_filter``: the exact forward filter over the same prints,
i.e. the Bayes-optimal posterior under the generator. Learned models are scored by how close they
get to it. Prints are the filter's whole information set; generated marks also carry regime
information (stressed shocks are wider), and are deliberately not used, so the filter stays the ceiling.

This module needs numpy only; models live in ``scripts/train_forecast.py``.
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import numpy as np
from fundforge.asof import Observation
from fundforge.generator import MACRO_SERIES, Spec
from fundforge.research import regime_filter
from fundforge.tape import Tape

from . import worlds
from .contracts import split_of

FEATURE_VERSION = "forecast-features-2026.10.1"
WINDOW = 8  # print slots, newest first; a generated case1 world has at most 8 generated days
SPEC = Spec()  # rooms and the terminal use the default spec, and so does worlds.world
Row = Mapping[str, Any]


def macro_rows(tape: Tape, day: int) -> list[dict[str, Any]]:
    """The terminal's ``macro`` rows at ``day`` (same expression as ``terminal.snapshot``; parity is tested)."""
    return [{"series": o.instrument, "period_day": o.event_time, "published_day": o.available_at,
             "revision": o.revision, "value": str(o.value)} for o in tape.macro.known(day)]


def known(rows: Iterable[Row], as_of: int) -> list[Row]:
    """Latest published revision per Street activity period at ``as_of``, oldest period first."""
    best: dict[int, Row] = {}
    for r in rows:
        if r["series"] != MACRO_SERIES or r["published_day"] > as_of:
            continue
        p = r["period_day"]
        if p not in best or r["revision"] > best[p]["revision"]:
            best[p] = r
    return [best[p] for p in sorted(best)]


def features(rows: Iterable[Row], as_of: int) -> np.ndarray:
    """Fixed-length vector: per slot (newest first) scaled deviation, revised flag, present flag; then count."""
    k = known(rows, as_of)
    x = np.zeros(3 * WINDOW + 1)
    for i, r in enumerate(reversed(k[-WINDOW:])):
        tenths = Decimal(r["value"]) * 10
        x[3 * i] = (float(tenths) - SPEC.macro_level) / SPEC.macro_regime  # calm near +1, stressed near -1
        x[3 * i + 1] = 1.0 if r["revision"] else 0.0
        x[3 * i + 2] = 1.0
    x[-1] = len(k)
    return x


def bayes(rows: Iterable[Row], as_of: int) -> tuple[float, float]:
    """(chain prior, exact posterior) P(stressed) for the latest published period, from ``regime_filter``."""
    obs = [Observation(r["series"], r["period_day"], r["published_day"], r["revision"], Decimal(r["value"]))
           for r in known(rows, as_of)]
    prior, post = regime_filter(obs, SPEC)[-1]
    return float(prior["stressed"]), float(post["stressed"])


@dataclass(frozen=True)
class Sample:
    seed_family: str
    split: str
    as_of: int
    period_day: int
    x: np.ndarray
    y: int  # 1 if the hidden regime was stressed: label only, never a feature
    prior: float
    bayes: float


def world_samples(gen_seed: str) -> list[Sample]:
    """One sample per as-of day with at least one published print. Uses ungated generation (see docs)."""
    w = worlds.world.__wrapped__(gen_seed, "base", gate=False)
    regime = {d: r for d, r in w.tape.raw["generator"]["regimes"]}  # hidden truth: labels only
    days = sorted({ev.day for ev in w.tape.events})
    split = split_of(w.seed_family)
    out = []
    for day in days:
        rows = macro_rows(w.tape, day)
        k = known(rows, day)
        if not k:
            continue
        prior, post = bayes(rows, day)
        period = k[-1]["period_day"]
        out.append(Sample(w.seed_family, split, day, period, features(rows, day),
                          int(regime[period] == "stressed"), prior, post))
    return out


# ---------- metrics (binary, on P(stressed); research.brier's two-state score is exactly twice this) ----------

EPS = 1e-6


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def log_loss(p: np.ndarray, y: np.ndarray) -> float:
    q = np.clip(p, EPS, 1 - EPS)
    return float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q)))


def reliability(p: np.ndarray, y: np.ndarray, bins: int = 10) -> list[dict[str, float | int | None]]:
    """Equal-width bins on [0, 1]; the last bin includes 1. Empty bins report None."""
    idx = np.minimum((p * bins).astype(int), bins - 1)
    out: list[dict[str, float | int | None]] = []
    for b in range(bins):
        m = idx == b
        n = int(m.sum())
        out.append({"lo": b / bins, "hi": (b + 1) / bins, "n": n,
                    "mean_p": float(p[m].mean()) if n else None,
                    "frac_stressed": float(y[m].mean()) if n else None})
    return out


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error: bin-weighted |mean forecast - observed frequency|."""
    return sum(n / len(p) * abs(float(b["mean_p"] or 0) - float(b["frac_stressed"] or 0))
               for b in reliability(p, y, bins) if (n := int(b["n"] or 0)))


def score(p: np.ndarray, y: np.ndarray, bayes_p: np.ndarray, family: Sequence[str]) -> dict[str, Any]:
    """Metrics plus the gap to the Bayes posterior; the Brier-gap SE treats whole worlds as the unit."""
    diff = (p - y) ** 2 - (bayes_p - y) ** 2
    fams = np.asarray(family)
    per_world = np.array([diff[fams == f].mean() for f in dict.fromkeys(family)])
    return {"n": len(p), "worlds": len(per_world), "brier": brier(p, y), "log_loss": log_loss(p, y),
            "ece": ece(p, y), "gap_brier": float(diff.mean()),
            "gap_brier_se_by_world": float(per_world.std(ddof=1) / math.sqrt(len(per_world))),
            "gap_log_loss": log_loss(p, y) - log_loss(bayes_p, y),
            "mean_abs_to_bayes": float(np.mean(np.abs(p - bayes_p))),
            "reliability": reliability(p, y)}
