from dataclasses import replace
from decimal import Decimal as D

import pytest

from fundforge.ending import EndingFacts, classify


def good() -> EndingFacts:
    return EndingFacts(D(100), True, D("0.01"), D("0.005"), D("0.10"), D(60), D(80000), D(80000))


@pytest.mark.parametrize(("changes", "expected"), [
    ({}, "RENEWAL"),
    ({"book_certified": False}, "SURVIVAL"),
    ({"max_drawdown": D("0.12")}, "SURVIVAL"),
    ({"seed_confidence": D("59.999999")}, "SURVIVAL"),
    ({"deferred_units": True}, "SURVIVAL"),
    ({"winddown_complete": True}, "WINDDOWN"),
    ({"winddown_complete": True, "book_certified": False}, "SURVIVAL"),
    ({"payroll_unpaid": True}, "COMPANY_FAILURE"),
    ({"firm_cash": D(-1)}, "COMPANY_FAILURE"),
    ({"nav": D(0)}, "DEFAULT"),
    ({"overdue_claims": True}, "DEFAULT"),
    ({"broker_default": True, "payroll_unpaid": True}, "DEFAULT"),
])
def test_awards_and_inclusive_vs_strict_boundaries(changes, expected):
    assert classify(replace(good(), **changes))["award"] == expected


def test_report_explains_failed_renewal_goals_without_mutation():
    facts = replace(good(), book_certified=False, fund_return=D("0.004"))
    result = classify(facts)
    assert result["renewal_failures"] == ["certified_books", "cash_benchmark"]
    assert facts.fund_return == D("0.004")
