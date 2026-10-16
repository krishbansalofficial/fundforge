"""Independent dated settlement reconstruction from execution identities.

Rebuilds every settlement obligation (X1, X2, ...) from the execution confirmations alone: side, symbol,
quantity, cents amount, frozen cover collateral at the reference mark, and the house T+1 due day. It then
compares that expectation with the engine's recorded pending instructions, settled receipts and dated failed
attempts. Breaks are reported with typed codes and are never repaired.

It does not import the engine or its posting code. Only the stdlib, the execution confirmation record and the
cents rounding helper from ``money`` are used. The inputs are plain rows extracted from the engine by the caller.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from .money import CENT, CTX, cents
from .shadow import ExecutionConfirmation

ZERO = Decimal(0)
# Codes only this module can raise; the engine reports these beside shadow.inspect_settlements.
DATED_SETTLEMENT_CODES = frozenset({"receipt_before_due", "receipt_future", "receipt_unknown_date",
                                    "failure_outside_window"})


@dataclass(frozen=True)
class Obligation:
    """A settlement obligation rebuilt from one execution identity."""

    oid: str
    kind: str
    sym: str
    qty: int
    amount: Decimal
    frozen: Decimal  # cover collateral frozen at the reference mark; zero for other sides
    due_day: int  # execution day + 1 (house T+1 rule)
    cash: Decimal  # expected cash effect on settlement; positive is an inflow
    collateral: Decimal  # expected change in restricted collateral on settlement


def expected_obligations(confirmations: Iterable[ExecutionConfirmation]) -> dict[str, Obligation]:
    """One expected obligation per confirmation, numbered in execution order."""
    out: dict[str, Obligation] = {}
    with localcontext(CTX):
        for n, c in enumerate(confirmations, start=1):
            if c.side not in ("BUY", "SELL", "SHORT", "COVER") or c.qty <= 0:
                raise ValueError(f"unsupported confirmation side {c.side!r} for X{n}")
            amount = cents(Decimal(c.qty) * c.price)
            frozen = cents(Decimal(c.qty) * c.reference) if c.side == "COVER" else ZERO
            cash, collateral = {
                "BUY": (-amount, ZERO),
                "SELL": (amount, ZERO),
                "SHORT": (ZERO, amount),
                "COVER": (frozen - amount, -frozen),
            }[c.side]
            out[f"X{n}"] = Obligation(f"X{n}", c.side, c.sym, c.qty, amount, frozen, c.day + 1, cash, collateral)
    return out


def reconstruct(
    confirmations: Iterable[ExecutionConfirmation],
    *,
    day_dates: Mapping[int, str],
    pending: Iterable[tuple[str, str, str, int, Decimal, Decimal, int]],
    receipts: Iterable[tuple[str, str, str, Decimal, Decimal]],
    failures: Iterable[tuple[int, str]],
    day: int,
) -> list[dict[str, str | int]]:
    """Compare recorded settlement state with the reconstruction.

    day_dates: ISO calendar date for each engine day (used to date receipts back to engine days).
    pending: (oid, kind, sym, qty, amount, frozen, due_day) for each open instruction.
    receipts: (oid, kind, iso_date, amount, frozen) for each settled receipt.
    failures: dated failed attempts (day, oid). day: the current engine day; nothing later is known.
    """
    expected = expected_obligations(confirmations)
    by_date = {iso: d for d, iso in day_dates.items()}
    breaks: list[dict[str, str | int]] = []
    seen: dict[str, list[str]] = {}
    settled_day: dict[str, int] = {}

    def brk(code: str, oid: str, **detail: str | int) -> None:
        breaks.append({"code": code, "subject": oid, **detail})

    for oid, kind, sym, qty, amount, frozen, due in pending:
        seen.setdefault(oid, []).append("pending")
        want = expected.get(oid)
        if want is None:
            brk("obligation_unknown", oid, detail="pending instruction has no execution identity")
            continue
        if (kind, sym, qty, amount, frozen) != (want.kind, want.sym, want.qty, want.amount, want.frozen):
            brk(
                "obligation_economics",
                oid,
                actual=f"{kind} {qty} {sym} {amount} {frozen}",
                expected=f"{want.kind} {want.qty} {want.sym} {want.amount} {want.frozen}",
            )
        if due != want.due_day:
            brk("obligation_misdated", oid, actual=due, expected=want.due_day)
        if want.due_day <= day and not any(d >= want.due_day and o == oid for d, o in failures):
            brk("obligation_unexplained_delay", oid, expected=want.due_day)

    for oid, kind, iso, amount, frozen in receipts:
        seen.setdefault(oid, []).append("receipt")
        want = expected.get(oid)
        if want is None:
            brk("obligation_unknown", oid, detail="receipt has no execution identity")
            continue
        if (kind, amount, frozen) != (want.kind, want.amount, want.frozen):
            brk(
                "receipt_economics",
                oid,
                actual=f"{kind} {amount} {frozen}",
                expected=f"{want.kind} {want.amount} {want.frozen}",
            )
        d = by_date.get(iso)
        if d is None:
            brk("receipt_unknown_date", oid, actual=iso)
            continue
        settled_day[oid] = d
        if d < want.due_day:
            brk("receipt_before_due", oid, actual=d, expected=want.due_day)
        if d > day:
            brk("receipt_future", oid, actual=d, expected=day)

    for oid in expected:
        if oid not in seen:
            brk("obligation_missing", oid)
    for oid, sources in seen.items():
        if len(sources) > 1:
            brk("obligation_duplicate", oid, detail="+".join(sources))

    for d, oid in failures:
        want = expected.get(oid)
        settled = settled_day.get(oid)
        if want is None or d < want.due_day or d > day or (settled is not None and d >= settled):
            brk("failure_outside_window", oid, actual=d, expected=want.due_day if want else -1)
    return breaks


def expected_cash_receipts(confirmations: Iterable[ExecutionConfirmation]) -> dict[int, dict[str, Decimal]]:
    """Expected cash and collateral movement per due day, summed over obligations (for dated reporting)."""
    out: dict[int, dict[str, Decimal]] = {}
    with localcontext(CTX):
        for ob in expected_obligations(confirmations).values():
            row = out.setdefault(ob.due_day, {"cash": ZERO, "collateral": ZERO})
            row["cash"] += ob.cash
            row["collateral"] += ob.collateral
    return {d: {k: v.quantize(CENT, rounding=ROUND_HALF_EVEN) for k, v in row.items()}
            for d, row in sorted(out.items())}
