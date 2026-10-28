"""Unsupervised anomaly features for the fund's books at a decision barrier (docs/ML_SHOWCASE.md, Later 1).

Two steps, kept apart so the hidden-truth boundary is checkable:

- ``book_state(e)`` copies what the books hold at a barrier into a plain dict with exactly ``BOOK_KEYS``:
  journal entries (entity, date, postings; *no memo*), broker record (balances, activities, statements),
  pending settlement rows, confirmations, loans, positions and LP series. It never reads the tape, its
  future events, fault metadata or any engine control output (reconcile, control_report, certificates).
- ``features(book)`` is a pure function of that dict to a fixed-length float vector (``FEATURE_NAMES``).
  It refuses any dict whose keys are not exactly ``BOOK_KEYS``.

Memos are excluded on purpose: the B5 injectors label their entries "B5 ...", which would leak the answer.
No feature encodes a control rule (no "broker minus journal" differences, no recomputed fees): the model
sees raw balances and counts and must learn their joint clean distribution itself.

Money features are divided by ``scale`` = fund LP capital (sum of series net + provision), so paths with
different sizes stay comparable. Feature groups, in order:

1. ``fund:<acct>`` fund journal balance / scale for each account in ``FUND_ACCOUNTS``; ``capital:*`` and
   ``provision:*`` series accounts are summed; ``fund:other`` is the sum of |balance| of any other account.
2. ``firm:<acct>`` the same for the management company (``FIRM_ACCOUNTS``), also / scale.
3. Journal shape: entry counts per entity, mean postings per entry, largest |posting| / scale, entries dated
   after the barrier date, max (entry date - barrier date) in days, and date inversions (an entry dated before
   the one appended just before it, fund entity).
4. ``pair:<k>`` debit->credit account pairs hashed (crc32, entity-qualified, series suffix stripped) into
   ``PAIR_BUCKETS`` buckets, as a share of all entries: what kinds of entries the books contain.
5. Broker record: cash, collateral, debt / scale; activity count, receipts (activities with an obligation),
   sum of activity amounts and frozen collateral / scale.
6. Settlement and trading state: pending rows, their amount and frozen sums / scale, confirmations, loans,
   loaned quantity, mean loan rate, long and short position counts, gross position quantity.
7. Statements: count and sum of stated balances / scale. The engine's own "expected" balance stored with a
   statement is a control output and is not used.
8. LP series: count of series, total units / 1e6. 9. ``day``: simulated day index of the barrier.
"""

from __future__ import annotations

import zlib
from collections.abc import Callable, Mapping
from datetime import date
from decimal import Decimal
from itertools import pairwise
from typing import Any

import numpy as np
import numpy.typing as npt

FEATURE_VERSION = "anomaly-v1"
BOOK_KEYS = frozenset({"date", "day", "entries", "broker_balances", "activities", "statements", "pending",
                       "confirmations", "loans", "positions", "series"})
FUND_ACCOUNTS = ("cash", "collateral", "debt", "long_securities", "short_liability", "accrued_interest",
                 "accrued_expense", "interest_payable", "mgmt_fee_accrued", "mgmt_fee_payable", "trade_receivable",
                 "trade_payable", "redemption_payable", "common_pnl", "capital", "provision")
FIRM_ACCOUNTS = ("cash", "fee_receivable", "fee_revenue", "payroll_payable", "payroll_expense", "owner_capital")
PAIR_BUCKETS = 1024  # ~36 distinct pairs in clean books; 1024 keeps hash collisions rare
FEATURE_NAMES: tuple[str, ...] = (
    *(f"fund:{a}" for a in FUND_ACCOUNTS), "fund:other",
    *(f"firm:{a}" for a in FIRM_ACCOUNTS), "firm:other",
    "entries:fund", "entries:firm", "postings_per_entry", "max_posting", "entries_after_date", "max_date_lead",
    "date_inversions",
    *(f"pair:{k}" for k in range(PAIR_BUCKETS)),
    "broker:cash", "broker:collateral", "broker:debt", "activities", "receipts", "activity_amount",
    "activity_frozen",
    "pending", "pending_amount", "pending_frozen", "confirmations", "loans", "loan_qty", "loan_rate",
    "longs", "shorts", "gross_qty",
    "statements", "statement_balance",
    "series", "series_units", "day",
)


def book_state(e: Any) -> dict[str, Any]:
    """Copy the book state of an ``Engine`` at its current barrier. Reads no tape, control or fault data."""
    return {
        "date": e.ev.date.isoformat(),
        "day": e.ev.day,
        "entries": [(x.entity, x.date, [(p.account, p.amount) for p in x.postings]) for x in e.j.entries],
        "broker_balances": dict(e.broker.balances),
        "activities": [(a.date, a.kind, a.amount, a.frozen, bool(a.obligation)) for a in e.broker.activities],
        "statements": [(s.account, s.balance) for s in e.broker.statements],
        "pending": [(p.kind, p.amount, p.frozen) for p in e.pending],
        "confirmations": len(e.confirmations),
        "loans": [(ln.qty, ln.rate) for ln in e.loans],
        "positions": dict(e.pos),
        "series": [(s.units, s.net, s.provision) for s in e.series],
    }


def _base(account: str) -> str:
    return account.split(":", 1)[0]


def _bucket(key: str) -> int:
    return zlib.crc32(key.encode()) % PAIR_BUCKETS


def features(book: Mapping[str, Any]) -> npt.NDArray[np.float64]:
    if set(book) != BOOK_KEYS:
        raise KeyError(f"book keys must be exactly BOOK_KEYS; extra {sorted(set(book) - BOOK_KEYS)}, "
                       f"missing {sorted(BOOK_KEYS - set(book))}")
    scale = sum((n + f for _, n, f in book["series"]), Decimal(0)) or Decimal(1)
    entries = book["entries"]
    bal: dict[tuple[str, str], Decimal] = {}
    pairs = [0.0] * PAIR_BUCKETS
    for entity, _, legs in entries:
        for acct, amt in legs:
            k = (entity, _base(acct))
            bal[k] = bal.get(k, Decimal(0)) + amt
        debits = [_base(a) for a, x in legs if x > 0]
        credits = [_base(a) for a, x in legs if x < 0]
        for d in debits:
            for c in credits:
                pairs[_bucket(f"{entity}|{d}>{c}")] += 1

    def ratio(x: Decimal) -> float:
        return float(x / scale)

    def group(entity: str, accounts: tuple[str, ...]) -> list[float]:
        known = [ratio(bal.get((entity, a), Decimal(0))) for a in accounts]
        other = sum((abs(v) for (ent, a), v in bal.items() if ent == entity and a not in accounts), Decimal(0))
        return [*known, ratio(other)]

    today = date.fromisoformat(book["date"])
    fund_dates = [date.fromisoformat(d) for ent, d, _ in entries if ent == "fund"]
    all_dates = [date.fromisoformat(d) for _, d, _ in entries]
    n = max(len(entries), 1)
    legs_all = [x for _, _, legs in entries for _, x in legs]
    acts, pend, loans, stmts = book["activities"], book["pending"], book["loans"], book["statements"]
    pos = book["positions"].values()
    bb = book["broker_balances"]
    row = [
        *group("fund", FUND_ACCOUNTS), *group("firm", FIRM_ACCOUNTS),
        float(sum(ent == "fund" for ent, _, _ in entries)), float(sum(ent == "firm" for ent, _, _ in entries)),
        len(legs_all) / n, ratio(max((abs(x) for x in legs_all), default=Decimal(0))),
        float(sum(d > today for d in all_dates)), float(max(((d - today).days for d in all_dates), default=0)),
        float(sum(b < a for a, b in pairwise(fund_dates))),
        *(p / n for p in pairs),
        ratio(bb["cash"]), ratio(bb["collateral"]), ratio(bb["debt"]),
        float(len(acts)), float(sum(a[4] for a in acts)),
        ratio(sum((a[2] for a in acts), Decimal(0))), ratio(sum((a[3] for a in acts), Decimal(0))),
        float(len(pend)), ratio(sum((p[1] for p in pend), Decimal(0))), ratio(sum((p[2] for p in pend), Decimal(0))),
        float(book["confirmations"]), float(len(loans)), float(sum(q for q, _ in loans)),
        float(sum((r for _, r in loans), Decimal(0)) / len(loans)) if loans else 0.0,
        float(sum(q > 0 for q in pos)), float(sum(q < 0 for q in pos)), float(sum(abs(q) for q in pos)),
        float(len(stmts)), ratio(sum((s[1] for s in stmts), Decimal(0))),
        float(len(book["series"])), float(sum((u for u, _, _ in book["series"]), Decimal(0)) / Decimal(10**6)),
        float(book["day"]),
    ]
    assert len(row) == len(FEATURE_NAMES)
    return np.asarray(row, dtype=np.float64)


def max_abs_z(train: npt.NDArray[np.float64]) -> Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]]:
    """Baseline scorer: the largest per-feature |z| against clean training rows (std floored at 1e-6).

    A feature constant in training (an account pair never seen) gets the floor, so any change in it scores huge.
    """
    mu, sd = train.mean(0), np.maximum(train.std(0), 1e-6)
    return lambda x: np.abs((np.atleast_2d(x) - mu) / sd).max(-1)
