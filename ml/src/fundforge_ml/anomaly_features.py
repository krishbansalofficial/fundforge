"""Per entity and calendar date features, read from journal rows only, as of that date.

A row is visible on date ``d`` only if it was posted on or before ``d``. Nothing else (evidence, the
tape, later postings, labels) reaches this module, so a feature cannot leak the future.
"""

from collections import Counter, defaultdict
from datetime import date

import numpy as np

from .anomaly_data import ENTITIES, FEE_MEMOS, Row

FEATURE_NAMES = (
    "dated_entries",
    "postings",
    "gross",
    "fee_entries",
    "fee_gross",
    "settle_entries",
    "trade_entries",
    "mark_gross",
    "cash_net",
    "pnl_gross",
    "duplicate_memo_entries",
    "advance_entries",
    "posted_today",
    "weekday",
    "business_day",
)
# Counts and amounts are log-scaled; the calendar columns stay as they are.
CATEGORICAL = frozenset({"weekday", "business_day"})


def _floats(r: Row) -> list[tuple[str, float]]:
    return [(a, float(v)) for a, v in r.postings]


def featurize(rows: tuple[Row, ...], calendar: tuple[str, ...]) -> tuple[np.ndarray, list[tuple[str, str]]]:
    by_sim: dict[tuple[str, str], list[Row]] = defaultdict(list)
    for r in rows:
        by_sim[(r.entity, r.sim_date)].append(r)
    posted = Counter(r.posted_date for r in rows)
    out: list[list[float]] = []
    keys: list[tuple[str, str]] = []
    for entity in ENTITIES:
        for d in calendar:
            vis = [r for r in by_sim.get((entity, d), ()) if r.posted_date <= d]
            memos = Counter(r.memo for r in vis)
            amounts = [(a, abs(v)) for r in vis for a, v in _floats(r)]
            fee = [r for r in vis if r.memo.startswith(FEE_MEMOS)]
            cash_net = sum((v for r in vis for a, v in _floats(r) if a == "cash"), 0.0)
            wd = date.fromisoformat(d).weekday()
            out.append(
                [
                    float(len(vis)),
                    float(sum(len(_floats(r)) for r in vis)),
                    float(sum(v for _, v in amounts)),
                    float(len(fee)),
                    float(sum(abs(v) for r in fee for _, v in _floats(r))),
                    float(sum(1 for r in vis if r.memo.startswith("Settle "))),
                    float(sum(1 for r in vis if r.memo.split(" ", 1)[0] in ("BUY", "SELL", "SHORT", "COVER"))),
                    float(sum(v for r in vis if r.memo.startswith("Mark positions") for _, v in _floats(r))),
                    float(cash_net),
                    float(sum(v for a, v in amounts if a == "common_pnl")),
                    float(sum(c for c in memos.values() if c > 1)),
                    float(sum(1 for r in vis if r.posted_date < d)),
                    float(posted.get(d, 0)),
                    float(wd),
                    float(wd < 5),
                ]
            )
            keys.append((entity, d))
    return np.array(out, dtype=float), keys


def transform(x: np.ndarray) -> np.ndarray:
    """Sign-preserving log scale for counts and amounts; calendar columns unchanged."""
    y = np.sign(x) * np.log1p(np.abs(x))
    for k, name in enumerate(FEATURE_NAMES):
        if name in CATEGORICAL:
            y[:, k] = x[:, k]
    return y
