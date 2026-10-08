"""Fixed-precision money helpers (FUND_ACCOUNTING §1).

Cash posts in cents with HALF_EVEN rounding. Accruals keep their sub-cent
remainder per obligation so repeated daily postings never drift.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext

CENT = Decimal("0.01")
CTX = Context(prec=40, rounding=ROUND_HALF_EVEN)


def D(value: str | int | Decimal) -> Decimal:
    """Parse money/rates from str/int only; floats are rejected at the boundary."""
    if isinstance(value, float) or isinstance(value, bool):
        raise TypeError(f"binary float/bool not allowed for money: {value!r}")
    d = Decimal(value)
    if not d.is_finite():
        raise ValueError(f"non-finite decimal: {value!r}")
    return d + 0  # normalises -0 to 0


def cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class Accrual:
    """Carries the unposted fraction of an obligation between postings."""

    residual: Decimal = Decimal(0)

    def post(self, exact: Decimal) -> tuple[Decimal, "Accrual"]:
        with localcontext(CTX):
            total = self.residual + exact
            posted = cents(total)
            return posted, Accrual(total - posted)
