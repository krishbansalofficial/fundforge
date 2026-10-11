from dataclasses import FrozenInstanceError, replace
from decimal import localcontext

import pytest
from test_engine import CASE1, run
from test_golden import PATHS

from fundforge.administrator import Administrator, Capital
from fundforge.engine import Engine, InvariantError
from fundforge.money import D
from fundforge.tape import load


@pytest.mark.parametrize("script", list(PATHS.values()), ids=list(PATHS))
def test_complete_paths_match_independent_lp_fees_and_claims(script):
    e = run(script)
    report = e.control_report()["administrator"]
    assert report["status"] == "checked" and report["close_count"] == 13
    assert report["claim_count"] == 1
    assert report["liabilities"]["redemption_payable"] == "0.00"
    with localcontext() as ctx:
        ctx.prec = 6
        assert e.control_report()["administrator"] == report


def test_independent_cohort_participation_and_partial_redemption_oracle():
    a = Administrator([{"id": "A", "units": "1000", "hwm": "100"},
                       {"id": "B", "units": "1000", "hwm": "120"}], D(210000))
    a.series = {"A": Capital("A", D(1000), D(100), D(108000), D(2000)),
                "B": Capital("B", D(1000), D(120), D(100000))}
    a.close("2026-01-23", D(231000))
    assert [(c.common_pnl, c.management_fee) for c in a.closes] == [(D(11000), D("4.52")), (D(10000), D("4.11"))]
    assert a.series["A"].net == D("116796.38")
    assert a.series["A"].provision == D("4199.10")
    assert a.series["B"].net == D("109995.89")
    claim = a.preview("2026-01-23", "A", D(250))
    assert claim.payable == D("29199.10") and claim.crystallized_fee == D("1049.78")
    assert claim.surviving.hwm == D(100) and claim.surviving.units == D(750)
    a.deal(claim)
    a.invoice()
    a.pay("redemption_payable", claim.payable)
    assert a.liabilities["redemption_payable"] == 0
    assert a.liabilities["mgmt_fee_payable"] == D("8.63")
    with pytest.raises(FrozenInstanceError):
        a.closes[0].management_fee = D(0)
    with pytest.raises(ValueError, match="stale"):
        a.deal(claim)


def test_weekends_compound_fee_base_and_residual_without_recharging_payment():
    a = Administrator([{"id": "A", "units": "250000", "hwm": "100"}], D(25000000))
    for day in (23, 24, 25):
        a.close(f"2026-01-{day}", D(25000000))
    assert [c.management_fee for c in a.closes] == [D("1027.40"), D("1027.35"), D("1027.32")]
    assert a.series["A"].net == D("24996917.93")
    a.invoice()
    a.pay("mgmt_fee_payable", D("3082.07"))
    a.close("2026-01-26", D("24996917.93"))
    assert a.closes[-1].common_pnl == 0
    assert a.closes[-1].management_fee == D("1027.27")
    with pytest.raises(ValueError, match="duplicate"):
        a.close("2026-01-26", D(0))


def test_loss_reverses_only_surviving_provision_and_full_close_preserves_identity():
    a = Administrator([{"id": "A", "units": "1000", "hwm": "100"}], D(110000))
    a.series["A"] = Capital("A", D(1000), D(100), D(108000), D(2000))
    claim = a.preview("2026-01-23", "A", D(250))
    assert (claim.payable, claim.crystallized_fee) == (D(27000), D(500))
    a.deal(claim)
    a.close("2026-01-24", D(100000))  # 27,500 fixed claims remain outside participation
    assert a.series["A"].provision == 0 and a.liabilities["perf_fee_payable"] == D(500)
    assert a.series["A"].hwm == D(100)
    a.deal(a.preview("2026-01-24", "A", D(750)))
    assert a.series["A"].units == 0 and a.series["A"].net == 0


def test_balanced_double_management_fee_is_caught_without_using_posted_pnl(monkeypatch):
    import fundforge.engine as module

    normal = module.mgmt_fee_exact
    monkeypatch.setattr(module, "mgmt_fee_exact", lambda s: normal(s) * 2)
    e = Engine(load(CASE1))
    while e.ev.day < 13:
        e.advance()
    e.reconcile()  # both entities, capital and provisions agree internally
    report = e.control_report()["administrator"]
    assert report["status"] == "break"
    assert {b["code"] for b in report["breaks"]} >= {"lp_series", "admin_claim", "management_fee_date"}
    while e.ev.day < 20:
        e.advance()
    units = [s.units for s in e.series]
    e._deal()
    assert [s.units for s in e.series] == units and not e.administrator.claims
    assert e.incident_events[-1]["code"] == "dealing_blocked"


def test_unearned_manager_receivable_is_detected_in_other_entity():
    e = Engine(load(CASE1))
    e.advance()
    e._post("unearned income", ("fee_receivable", D(100)), ("fee_revenue", D(-100)), entity="firm")
    e.reconcile()
    assert {b["code"] for b in e.control_report()["administrator"]["breaks"]} == {
        "manager_receivable", "manager_revenue"}


@pytest.mark.parametrize("corruption", ["payable", "fee", "hwm", "units"])
def test_bad_redemption_candidate_is_blocked_before_mutating_units_claims_or_journal(monkeypatch, corruption):
    import fundforge.engine as module

    e = Engine(load(CASE1))
    while e.ev.day < 20:
        e.advance()
    normal = module.redeem

    def wrong(s, units):
        surviving, payable, fee = normal(s, units)
        if corruption == "payable":
            payable += D(1)
            surviving = replace(surviving, net=surviving.net - 1)
        elif corruption == "fee":
            fee += D(1)
            surviving = replace(surviving, provision=surviving.provision - 1)
        else:
            surviving = replace(surviving, **{corruption: getattr(surviving, corruption) + 1})
        return surviving, payable, fee

    monkeypatch.setattr(module, "redeem", wrong)
    before = (list(e.series), e.j.digest(), e.administrator.claims, dict(e.administrator.series))
    with pytest.raises(InvariantError, match="administrator_claim"):
        e._deal()
    assert (e.series, e.j.digest(), e.administrator.claims, e.administrator.series) == before


def test_dated_fee_reclassification_detected_even_when_ending_capital_matches():
    e = Engine(load(CASE1))
    while e.ev.day < 13:
        e.advance()
    from datetime import date

    for d, amount in ((date(2026, 1, 20), D(-1)), (date(2026, 1, 21), D(1))):
        e._post_pair("date-only corruption", [("capital:Seed", amount), ("mgmt_fee_accrued", -amount)],
                     [("fee_receivable", amount), ("fee_revenue", -amount)], date_=d)
    e.reconcile()
    assert [b["code"] for b in e.control_report()["administrator"]["breaks"]] == [
        "management_fee_date", "management_fee_date"]
