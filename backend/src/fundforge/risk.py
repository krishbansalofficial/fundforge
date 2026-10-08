"""Exposure and margin ratios (FUND_ACCOUNTING §4)."""

from decimal import Decimal

INITIAL = {"long": Decimal("0.50"), "short": Decimal("0.60")}
MAINTENANCE = {"long": Decimal("0.35"), "short": Decimal("0.40")}


def exposures(nav: Decimal, long_mv: Decimal, short_mv: Decimal) -> tuple[Decimal, Decimal]:
    """(gross, net) exposure as fractions of NAV; short_mv is a positive magnitude."""
    if nav <= 0:
        raise ValueError("non-positive NAV: exposure undefined, fund in distress")
    return (long_mv + short_mv) / nav, (long_mv - short_mv) / nav


def margin_requirement(long_mv: Decimal, short_mv: Decimal, rates: dict[str, Decimal]) -> Decimal:
    return rates["long"] * long_mv + rates["short"] * short_mv
