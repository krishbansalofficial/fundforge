"""Quadratic impact execution against a tape event (FUND_ACCOUNTING §8).

C(Q) = ref * Q * [half_spread + k * (Q/V)^2] / 10_000 for cumulative same-side
quantity Q in the event, so splitting an order cannot reset impact.
"""

from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from .money import CTX

PRICE = Decimal("0.000001")
BUY_SIDES = {"BUY", "COVER"}


def total_cost(ref: Decimal, q: int, volume: int, half_spread: Decimal, k: Decimal) -> Decimal:
    if q == 0:
        return Decimal(0)
    with localcontext(CTX):
        frac = Decimal(q) / Decimal(volume)
        return ref * q * (half_spread + k * frac * frac) / 10_000


def fill_price(ref, side, done_same_side, q, volume, half_spread, k) -> Decimal:
    """Per-share executed price for q more shares after ``done_same_side`` already filled this event."""
    with localcontext(CTX):
        inc = total_cost(ref, done_same_side + q, volume, half_spread, k) - total_cost(
            ref, done_same_side, volume, half_spread, k
        )
        sign = 1 if side in BUY_SIDES else -1
        return (ref + sign * inc / q).quantize(PRICE, rounding=ROUND_HALF_EVEN)


def capacity(volume: int, participation: Decimal, done_both_sides: int) -> int:
    """Whole shares still available to the fund in this instrument/event (shared across sides)."""
    return max(0, int(volume * participation) - done_both_sides)
