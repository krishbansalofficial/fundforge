"""Published campaign awards from completed facts; never changes economic state."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class EndingFacts:
    nav: Decimal
    book_certified: bool
    fund_return: Decimal
    cash_benchmark: Decimal
    max_drawdown: Decimal
    seed_confidence: Decimal
    firm_cash: Decimal
    minimum_firm_cash: Decimal
    broker_default: bool = False
    overdue_claims: bool = False
    payroll_unpaid: bool = False
    deferred_units: bool = False
    winddown_complete: bool = False  # every unit redeemed and paid under a declared winddown
    winddown_started: bool = False
    forced_actions: bool = False  # forced margin or recall buy-ins occurred (the published campaign objective)
    broker_shortfalls: bool = False  # collateral or settlement amounts were ever short of the broker's requirement
    confidence_min: Decimal = Decimal(60)
    drawdown_limit: Decimal = Decimal("0.12")


def classify(f: EndingFacts) -> dict[str, Any]:
    """A winddown award requires an actual completed return-of-capital checkpoint.

    Merely flattening positions is not a winddown. The caller must supply verified
    lifecycle facts; an empty book or a pending subscription is never a cash receipt.
    """
    checks = {
        "positive_nav": f.nav > 0,
        "certified_books": f.book_certified,
        "cash_benchmark": f.fund_return >= f.cash_benchmark,
        "drawdown": f.max_drawdown < f.drawdown_limit,
        "seed_confidence": f.seed_confidence >= f.confidence_min,
        "company_runway": f.firm_cash >= f.minimum_firm_cash,
        "claims_current": not f.overdue_claims,
        "no_deferred_units": not f.deferred_units,
        "no_forced_actions": not f.forced_actions,
        "no_broker_shortfalls": not f.broker_shortfalls,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if f.broker_default or f.overdue_claims or (f.nav <= 0 and not f.winddown_complete):
        award = "DEFAULT"
    elif f.payroll_unpaid or f.firm_cash < 0:
        award = "COMPANY_FAILURE"
    elif f.winddown_complete and f.book_certified and not f.deferred_units:
        award = "WINDDOWN"
    elif f.winddown_started:
        award = "SURVIVAL"  # an unfinished winddown is not a responsible completion and cannot renew
    elif not failed:
        award = "RENEWAL"
    else:
        award = "SURVIVAL"
    return {"award": award, "renewal_checks": checks, "renewal_failures": failed}
