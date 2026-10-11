"""Independent execution/holdings valuation controls, without engine/posting imports.

Cash and liabilities are supplied book balances, not independent bank statements.
Passing these controls is therefore not full administrator NAV certification.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

CONTEXT = Context(prec=40, rounding=ROUND_HALF_EVEN)
CENT, PRICE = Decimal("0.01"), Decimal("0.000001")


@dataclass(frozen=True)
class ExecutionConfirmation:
    event: int
    sym: str
    side: str
    qty: int
    price: Decimal
    amount: Decimal
    reference: Decimal
    volume: int
    same_side: int
    half_spread: Decimal
    impact: Decimal
    day: int = 0  # execution day; the obligation is due on day + 1 (house T+1 rule)


def inspect_book(opening: dict[str, int], confirmations: Iterable[ExecutionConfirmation],
                 positions: dict[str, int], marks: dict[str, Decimal], balances: dict[str, Decimal]) -> dict[str, Any]:
    """Reprice confirmations, rebuild holdings, compare market values and conditional NAV."""
    with localcontext(CONTEXT):
        expected = {sym: opening.get(sym, 0) for sym in marks}
        breaks = []

        def compare(code: str, subject: str, actual: Any, wanted: Any, tolerance: Decimal = Decimal(0)) -> None:
            if abs(actual - wanted) > tolerance:
                breaks.append({"code": code, "subject": subject, "actual": str(actual), "expected": str(wanted)})

        count = 0
        for fill in confirmations:
            count += 1
            if fill.sym not in expected or fill.qty <= 0 or fill.volume <= 0 or fill.side not in (
                    "BUY", "COVER", "SELL", "SHORT"):
                breaks.append({"code": "invalid_confirmation", "subject": fill.sym})
                continue
            q, prior = Decimal(fill.qty), Decimal(fill.same_side)
            # Expanded cubic difference; does not call execution.fill_price/total_cost.
            adverse = fill.reference * (fill.half_spread + fill.impact * (
                3 * prior * prior + 3 * prior * q + q * q) / Decimal(fill.volume) ** 2) / 10000
            sign = 1 if fill.side in ("BUY", "COVER") else -1
            price = (fill.reference + sign * adverse).quantize(PRICE)
            compare("fill_price", fill.sym, fill.price, price)
            compare("fill_amount", fill.sym, fill.amount, (q * price).quantize(CENT))
            held = expected[fill.sym]
            if ((fill.side == "SELL" and fill.qty > max(held, 0))
                    or (fill.side == "COVER" and fill.qty > max(-held, 0))
                    or (fill.side == "BUY" and held < 0) or (fill.side == "SHORT" and held > 0)):
                breaks.append({"code": "position_direction", "subject": fill.sym})
            expected[fill.sym] += sign * fill.qty
        for sym, qty in expected.items():
            compare("position", sym, positions.get(sym, 0), qty)
        longs = sum(((qty * marks[sym]).quantize(CENT) for sym, qty in expected.items() if qty > 0), Decimal(0))
        shorts = sum(((-qty * marks[sym]).quantize(CENT) for sym, qty in expected.items() if qty < 0), Decimal(0))
        compare("long_valuation", "fund", balances.get("long_securities", Decimal(0)), longs, CENT)
        compare("short_valuation", "fund", balances.get("short_liability", Decimal(0)), -shorts, CENT)
        other = sum((value for account, value in balances.items() if not account.startswith("capital:")
                     and account not in ("common_pnl", "long_securities", "short_liability")), Decimal(0))
        conditional_nav = longs - shorts + other
        book_nav = -sum((value for account, value in balances.items()
                         if account.startswith("capital:") or account == "common_pnl"), Decimal(0))
        compare("conditional_nav", "fund", book_nav, conditional_nav, CENT)
        return {"status": "checked" if not breaks else "break", "breaks": breaks,
                "confirmations": count, "expected_positions": expected,
                "conditional_nav": str(conditional_nav), "book_nav": str(book_nav),
                "scope": "Independent fill prices, holdings and quoted values. Cash and liabilities use book balances; "
                "independent bank, loan-fee and LP-claim certification remains pending."}


def inspect_settlements(confirmations: Iterable[ExecutionConfirmation],
                        pending: Iterable[tuple[str, str, str, int, Decimal, int]],
                        receipts: Iterable[tuple[str, str, Decimal]],
                        failures: Iterable[tuple[int, str]], day: int) -> list[dict[str, Any]]:
    """Rebuild one settlement obligation per confirmation (identity X1, X2, ...) and account for each.

    pending: (obligation, kind, sym, qty, amount, due_day); receipts: (obligation, kind, amount);
    failures: dated (day, obligation) attempts. Every obligation must be pending xor settled exactly once,
    with matching economics, and a past-due pending obligation needs dated failed-attempt evidence.
    """
    expected = {f"X{n}": (c.side, c.sym, c.qty, c.amount, c.day + 1)
                for n, c in enumerate(confirmations, start=1)}
    breaks: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    failed = set(failures)
    for oid, kind, sym, qty, amount, due in pending:
        seen[oid] = seen.get(oid, 0) + 1
        if expected.get(oid) != (kind, sym, qty, amount, due):
            breaks.append({"code": "settlement_misallocated", "subject": oid,
                           "actual": f"{kind} {qty} {sym} {amount} due {due}", "expected": str(expected.get(oid))})
        elif due <= day and not any((d, oid) in failed for d in range(due, day + 1)):
            breaks.append({"code": "settlement_unexplained_delay", "subject": oid})
    for oid, kind, amount in receipts:
        seen[oid] = seen.get(oid, 0) + 1
        want = expected.get(oid)
        if want is None or (kind, amount) != (want[0], want[3]):
            breaks.append({"code": "settlement_misallocated", "subject": oid,
                           "actual": f"{kind} {amount}", "expected": str(want)})
    breaks += [{"code": "settlement_missing", "subject": oid} for oid in expected if oid not in seen]
    breaks += [{"code": "settlement_duplicate", "subject": oid} for oid, n in seen.items() if n > 1]
    return breaks
