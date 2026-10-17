"""Clean books from real Session runs, and labelled copies with injected anomalies (docs/ML_ANOMALY.md).

Clean books come from generated worlds played through ``Session`` (the solo bot seat plays the other
partner, as in ``ml/tests/helpers.py``). Every copy is edited in memory only; no live room is touched.

Two kinds of data are kept apart on purpose:

- ``Row``: the exported journal rows (``outbox.rows_for``, ``kind == journal_entry``). Only these are
  model features. Anomalies are injected here, as balanced entries or moved dates, so the journal's own
  double-entry check cannot see them.
- ``Evidence``: independent records from the clean run (confirmations, marks, broker snapshots, broker
  fee lines, administrator closes, settled obligations). Only the deterministic controls read these.
"""

import hashlib
import random
from collections import Counter
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from fundforge import bot, outbox
from fundforge.broker import PHASES
from fundforge.engine import Engine
from fundforge.governance import Session

from . import worlds
from .contracts import split_of

CLOSE = PHASES.index("CLOSE")
KINDS = (
    "wrong_date_fee",
    "balanced_wrong_cash",
    "phantom_position",
    "duplicate_settlement",
    "stale_mark",
    "statement_break",
)
FEE_MEMOS = ("Borrow fee", "Broker debit", "Management fee")
ENTITIES = ("fund", "firm")


@dataclass(frozen=True)
class Row:
    entry_id: str
    entity: str
    sim_date: str  # economic date the entry belongs to
    posted_date: str  # calendar date of the event that posted it (known from then on)
    memo: str
    postings: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class Evidence:
    calendar: tuple[str, ...]
    business_dates: dict[int, str]  # game day -> ISO date of its CLOSE
    marks: dict[int, dict[str, Decimal]]  # CLOSE marks by game day
    symbols: tuple[str, ...]
    opening_positions: dict[str, int]
    fills: tuple[tuple[int, str, int], ...]  # (game day, symbol, signed quantity)
    broker_cash: dict[int, dict[str, Decimal]]  # broker balances at CLOSE by game day
    broker_fees: dict[str, Decimal]  # broker financing charges by ISO date
    admin_fees: dict[tuple[str, str], Decimal]  # (ISO date, series) -> management fee
    settled_memos: dict[str, int]  # "Settle ..." memo -> count of settled obligations


@dataclass(frozen=True)
class Game:
    seed: str
    variant: str
    family: str
    split: str
    rows: tuple[Row, ...]
    evidence: Evidence


def simulate(gen_seed: str, variant: str) -> Game:
    """One clean run through Session. Raises WorldRejected if the balance gate refuses the world."""
    w = worlds.world(gen_seed, variant)
    e = Engine(w.tape)
    e.advance()
    opening = e.j.entries
    s = Session(e, {"pm": "ana", "mp": "bot"}, bots=frozenset({"mp"}))
    out: list[dict[str, Any]] = []
    before, finished_before, k = outbox.counts(s), False, 0
    while not s.e.finished():
        k += 1
        start = s.version
        bot.act(s, "mp", "bot", f"b{k}")
        s.handle("ana", f"r{k}", {"type": "ready", "version": s.version})
        bot.act(s, "mp", "bot", f"c{k}")
        for seq in range(start + 1, s.version + 1):
            entry = s.log[seq - 1]
            head = hashlib.sha256(str(seq).encode()).hexdigest()
            out += outbox.rows_for(
                "anomaly", "rules-anomaly", s, seq, entry, before, head, finished_before, last=seq == s.version
            )
            before = entry["after"]
        finished_before = s.e.finished()
    # The opening entries exist before the first command, so the outbox never emits them; they are
    # part of the exported ledger all the same (the journal at the start of the room).
    rows = tuple(_row(x.canonical()) for x in opening) + tuple(
        _row(x["payload"]) for x in out if x["kind"] == "journal_entry"
    )
    return Game(gen_seed, variant, w.seed_family, split_of(w.seed_family), rows, _evidence(e, rows))


def _row(p: dict[str, Any]) -> Row:
    return Row(
        p["id"],
        p["entity"],
        p["date"],
        p["id"].split("/")[0],
        p["memo"],
        tuple((a, Decimal(v)) for a, v in p["postings"]),
    )


def _evidence(e: Engine, rows: tuple[Row, ...]) -> Evidence:
    business = {o["day"]: o["date"] for o in e.observations if o["phase"] == "CLOSE"}
    marks = {
        o["day"]: {sym: Decimal(m) for sym, m in o["marks"].items()} for o in e.observations if o["phase"] == "CLOSE"
    }
    start = min(business.values())
    end = max([business[max(business)], *(r.sim_date for r in rows)])
    days = (date.fromisoformat(end) - date.fromisoformat(start)).days
    calendar = tuple((date.fromisoformat(start) + timedelta(days=n)).isoformat() for n in range(days + 1))
    broker_cash = {
        day: {k: v for k, v in bal.items() if k in ("cash", "collateral", "debt")}
        for (day, idx), bal in e.broker.snapshots.items()
        if idx == CLOSE
    }
    fees: dict[str, Decimal] = {}
    for f in e.broker.fees:
        fees[f.date] = fees.get(f.date, Decimal(0)) + f.amount
    report = e.control_report()
    settled: Counter[str] = Counter(
        f"Settle {x['kind']} {x['qty']} {x['sym']}" for x in report["settlements"] if x["status"] == "settled"
    )
    return Evidence(
        calendar=calendar,
        business_dates=business,
        marks=marks,
        symbols=tuple(sorted(e.tape.raw["instruments"])),
        opening_positions=dict(e.tape.raw["opening"]["fund"]["positions"]),
        fills=tuple((c.day, c.sym, c.qty if c.side in ("BUY", "COVER") else -c.qty) for c in e.confirmations),
        broker_cash=broker_cash,
        broker_fees=fees,
        admin_fees={(c.date, c.series_id): c.management_fee for c in e.administrator.closes},
        settled_memos=dict(settled),
    )


# ---------- injections: each returns new rows and the footprint (entity, date) it should be labelled at ----------

Footprint = frozenset[tuple[str, str]]


def inject(game: Game, kind: str, rng: random.Random, tag: str) -> tuple[tuple[Row, ...], Footprint] | None:
    """One anomaly of ``kind`` in a copy of the clean rows, or None if the book has no place for it."""
    rows = list(game.rows)
    ev = game.evidence
    days = sorted(ev.business_dates.items())
    picks = days[2:-2]  # leave the opening and the final days alone
    if kind == "wrong_date_fee":
        return _wrong_date_fee(rows, ev, rng)
    if kind == "duplicate_settlement":
        cands = [i for i, r in enumerate(rows) if r.entity == "fund" and r.memo.startswith("Settle ")]
        if not cands:
            return None
        i = rng.choice(cands)
        r = rows[i]
        rows.insert(i + 1, replace(r, entry_id=f"{r.entry_id}/dup-{tag}"))
        return tuple(rows), frozenset({("fund", r.sim_date)})
    if not picks:
        return None
    day, d = rng.choice(picks)
    if kind == "balanced_wrong_cash":
        amount = Decimal(rng.choice((1, -1)) * rng.randint(1000, 50000))
        row = Row(
            f"{d}/CLOSE/inj-{kind}-{tag}",
            "fund",
            d,
            d,
            "Cash adjustment (unreviewed)",
            (("cash", amount), ("common_pnl", -amount)),
        )
    elif kind == "statement_break":
        cents_off = Decimal(rng.choice((1, -1)) * rng.randint(1, 99)) / 100
        row = Row(
            f"{d}/CLOSE/inj-{kind}-{tag}",
            "fund",
            d,
            d,
            "Bank statement difference (unreconciled)",
            (("cash", cents_off), ("common_pnl", -cents_off)),
        )
    elif kind == "phantom_position":
        sym = rng.choice(ev.symbols)
        qty = rng.randint(100, 500)
        mark = ev.marks[day][sym]
        amount = (Decimal(qty) * mark).quantize(Decimal("0.01"))
        row = Row(
            f"{d}/CLOSE/inj-{kind}-{tag}",
            "fund",
            d,
            d,
            f"BUY {qty} {sym} @ {mark} (phantom)",
            (("long_securities", amount), ("trade_payable", -amount)),
        )
    elif kind == "stale_mark":
        held = [s for s in ev.symbols if _position(ev, day, s) > 0]
        if not held:
            return None
        sym = rng.choice(held)
        earlier = [dd for dd, _ in days if dd < day and day - dd >= 3]
        if not earlier:
            return None
        old = rng.choice(earlier)
        qty = _position(ev, day, sym)
        amount = (Decimal(qty) * (ev.marks[old][sym] - ev.marks[day][sym])).quantize(Decimal("0.01"))
        if amount == 0:
            return None
        row = Row(
            f"{d}/CLOSE/inj-{kind}-{tag}",
            "fund",
            d,
            d,
            "Mark positions to reference (stale)",
            (("long_securities", amount), ("common_pnl", -amount)),
        )
    else:
        raise ValueError(f"unknown anomaly kind {kind!r}")
    return _insert_at_posting(rows, d, row), frozenset({("fund", d)})


def _position(ev: Evidence, day: int, sym: str) -> int:
    qty = ev.opening_positions.get(sym, 0)
    return qty + sum(q for fd, s, q in ev.fills if s == sym and fd <= day)


def _insert_at_posting(rows: list[Row], posted: str, row: Row) -> tuple[Row, ...]:
    pos = 1 + max(i for i, r in enumerate(rows) if r.posted_date <= posted)
    return tuple([*rows[:pos], row, *rows[pos:]])


def _wrong_date_fee(rows: list[Row], ev: Evidence, rng: random.Random) -> tuple[tuple[Row, ...], Footprint] | None:
    """Move a financing or management-fee entry one calendar day, keeping its posting time."""
    cands = [i for i, r in enumerate(rows) if r.entity == "fund" and r.memo.startswith(FEE_MEMOS)]
    if not cands:
        return None
    i = rng.choice(cands)
    r = rows[i]
    new = (date.fromisoformat(r.sim_date) + timedelta(days=1)).isoformat()
    if new > ev.calendar[-1]:
        new = (date.fromisoformat(r.sim_date) - timedelta(days=1)).isoformat()
    if r.memo.startswith("Management fee"):  # the fund and firm legs move together
        group = [j for j, x in enumerate(rows) if x.memo == r.memo and x.sim_date == r.sim_date]
    else:
        group = [i]
    footprint: set[tuple[str, str]] = set()
    for j in group:
        x = rows[j]
        rows[j] = replace(x, sim_date=new, entry_id=f"{x.entry_id}/moved-{new}")
        footprint |= {(x.entity, x.sim_date), (x.entity, new)}
    return tuple(rows), frozenset(footprint)
