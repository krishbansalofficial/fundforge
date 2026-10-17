"""The deterministic controls the books already have, replayed over a (possibly corrupted) copy of the rows.

Each control compares independent evidence with the journal rebuilt from the rows. The comparison
rules mirror the backend (``engine.control_report``, ``shadow.inspect_book``, ``broker.discrepancies``,
``administrator.inspect``, ``engine.reconcile``). They are reimplemented over exported rows so that a
copied ledger can be checked without a live room; the double-entry check uses the backend's ``Journal``.

A control flags a (entity, date) pair. Persistent breaks (a wrong balance stays wrong) are flagged at
every date they fail, which is how the engine reports them.
"""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from fundforge.journal import Journal, JournalError, entry
from fundforge.money import CENT, cents

from .anomaly_data import Evidence, Row

CONTROLS = (
    "journal_integrity",
    "shadow_valuation",
    "broker_cash",
    "broker_fee_date",
    "administrator_fee_date",
    "settlement_identity",
)


@dataclass(frozen=True)
class Flag:
    control: str
    entity: str
    date: str


def replay(rows: tuple[Row, ...], ev: Evidence) -> tuple[Flag, ...]:
    flags: list[Flag] = []
    j = Journal()
    i = 0

    def post_until(limit: str | None) -> None:
        nonlocal i
        while i < len(rows) and (limit is None or rows[i].posted_date <= limit):
            r = rows[i]
            i += 1
            try:
                j.post(entry(r.entry_id, r.entity, r.sim_date, r.memo, *r.postings))
            except JournalError:
                flags.append(Flag("journal_integrity", r.entity, r.sim_date))

    for day in sorted(ev.business_dates):
        d = ev.business_dates[day]
        post_until(d)
        flags += _shadow(j, ev, day, d)
        flags += _broker_cash(j, ev, day, d)
    post_until(None)
    flags += _fees(rows, ev)
    flags += _settlements(rows, ev)
    return _alerts(flags)


STATE_CONTROLS = ("shadow_valuation", "broker_cash")


def _alerts(flags: list[Flag]) -> tuple[Flag, ...]:
    """A balance that stays wrong would be re-flagged every day. Treat the first break per entity as the
    alert (the incident), so later persistence is not counted as new detections. Flags are in date order."""
    seen: set[tuple[str, str]] = set()
    out = []
    for f in flags:
        if f.control in STATE_CONTROLS:
            if (f.control, f.entity) in seen:
                continue
            seen.add((f.control, f.entity))
        out.append(f)
    return tuple(out)


def _shadow(j: Journal, ev: Evidence, day: int, d: str) -> list[Flag]:
    """Holdings from confirmations at observed marks must equal the journal's securities balances."""
    qty = dict(ev.opening_positions)
    for fill_day, sym, signed in ev.fills:
        if fill_day <= day:
            qty[sym] = qty.get(sym, 0) + signed
    marks = ev.marks[day]
    long_v = sum((cents(Decimal(q) * marks[s]) for s, q in qty.items() if q > 0), Decimal(0))
    short_v = sum((cents(Decimal(-q) * marks[s]) for s, q in qty.items() if q < 0), Decimal(0))
    tol = CENT * len(ev.symbols)
    if (
        abs(j.balance("fund", "long_securities") - long_v) > tol
        or abs(j.balance("fund", "short_liability") + short_v) > tol
    ):
        return [Flag("shadow_valuation", "fund", d)]
    return []


def _broker_cash(j: Journal, ev: Evidence, day: int, d: str) -> list[Flag]:
    """Journal cash, collateral and debt must equal the broker's balances at the same close (exact)."""
    b = ev.broker_cash[day]
    if (
        j.balance("fund", "cash") != b["cash"]
        or j.balance("fund", "collateral") != b["collateral"]
        or -j.balance("fund", "debt") != b["debt"]
    ):
        return [Flag("broker_cash", "fund", d)]
    return []


def _fees(rows: tuple[Row, ...], ev: Evidence) -> list[Flag]:
    charges: dict[str, Decimal] = {}
    admin: dict[tuple[str, str], Decimal] = {}
    for r in rows:
        if r.entity != "fund":
            continue
        accounts = {a for a, _ in r.postings}
        if "common_pnl" in accounts:
            c = -sum((v for a, v in r.postings if a == "accrued_interest"), Decimal(0))
            if c:
                charges[r.sim_date] = charges.get(r.sim_date, Decimal(0)) + c
        if "mgmt_fee_accrued" in accounts:
            for a, v in r.postings:
                if a.startswith("capital:"):
                    key = (r.sim_date, a.removeprefix("capital:"))
                    admin[key] = admin.get(key, Decimal(0)) + v
    flags = [
        Flag("broker_fee_date", "fund", d)
        for d in sorted(set(charges) | set(ev.broker_fees))
        if charges.get(d, Decimal(0)) != ev.broker_fees.get(d, Decimal(0))
    ]
    flags += [
        Flag("administrator_fee_date", "fund", key[0])
        for key in sorted(set(admin) | set(ev.admin_fees))
        if admin.get(key, Decimal(0)) != ev.admin_fees.get(key, Decimal(0))
    ]
    # The firm leg of each management fee (fee_receivable, memo "Management fee ...") must match the same date.
    firm: dict[str, Decimal] = {}
    for r in rows:
        if r.entity == "firm" and r.memo.startswith("Management fee"):
            for a, v in r.postings:
                if a == "fee_receivable":
                    firm[r.sim_date] = firm.get(r.sim_date, Decimal(0)) + v
    expected_firm: dict[str, Decimal] = {}
    for (d, _series), amount in ev.admin_fees.items():
        expected_firm[d] = expected_firm.get(d, Decimal(0)) + amount
    flags += [
        Flag("administrator_fee_date", "firm", d)
        for d in sorted(set(firm) | set(expected_firm))
        if firm.get(d, Decimal(0)) != expected_firm.get(d, Decimal(0))
    ]
    return flags


def _settlements(rows: tuple[Row, ...], ev: Evidence) -> list[Flag]:
    """A settlement memo may appear no more often than the clean run settled obligations with it."""
    seen: Counter[str] = Counter()
    flags = []
    for r in rows:
        if r.entity == "fund" and r.memo.startswith("Settle "):
            seen[r.memo] += 1
            if seen[r.memo] > ev.settled_memos.get(r.memo, 0):
                flags.append(Flag("settlement_identity", "fund", r.sim_date))
    return flags
