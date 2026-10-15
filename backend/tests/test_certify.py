from test_engine import CASE1

from fundforge.engine import Engine
from fundforge.money import D
from fundforge.shadow import certify, payable, strike_nav_per_unit
from fundforge.tape import load


def test_struck_price_and_payable_residual_are_explicit():
    price = strike_nav_per_unit(D("1000.00"), D(3))
    assert price == D("333.333333")
    amount, residual = payable(D(3), price)
    assert amount == D("1000.00")
    assert residual == D("-0.000001")


def test_sub_cent_differences_pass_and_one_cent_plus_breaks():
    units = {"A": D(1000)}
    ok = certify(units, {"A": D("100000.00")}, {"A": D("100000.004")}, [])
    assert ok["status"] == "checked" and not ok["breaks"]
    bad = certify(units, {"A": D("100000.00")}, {"A": D("100000.02")}, [])
    assert bad["status"] == "break"
    assert [b["code"] for b in bad["breaks"]] == ["nav_per_unit"]


def test_dealt_payable_must_equal_units_times_price_within_strike_allowance():
    claims = [("A", D(1000), D("100.000000"), D("100000.00"))]
    assert certify({"A": D(0)}, {"A": D(0)}, {"A": D(0)}, claims)["status"] == "checked"
    wrong = certify({"A": D(0)}, {"A": D(0)}, {"A": D(0)}, [("A", D(1000), D("100.000000"), D("100001.00"))])
    assert [b["code"] for b in wrong["breaks"]] == ["payable"]


def _engine_at_deal_day():
    e = Engine(load(CASE1))
    while e.ev.day < 20:
        e.advance()
    return e


def test_clean_engine_certifies_on_deal_day():
    e = _engine_at_deal_day()
    cert = e.control_report()["certification"]
    assert cert["status"] == "checked" and not cert["breaks"]


def test_balanced_but_economically_wrong_posting_fails_certification_and_blocks_dealing():
    e = _engine_at_deal_day()
    # Balanced journal entry moving LP capital between series: internally consistent, economically wrong.
    e._post("Wrong: transfer LP capital between series", ("capital:Patient", D(5000)), ("capital:Seed", D(-5000)))
    # The engine's own series_capital invariant also rejects this entry; certify must fail independently of it.
    cert = certify(
        {k: s.units for k, s in e.administrator.series.items()},
        {k: -e.j.balances("fund").get(f"capital:{k}", D(0)) for k in e.administrator.series},
        {k: s.net for k, s in e.administrator.series.items()},
        [(c.series_id, c.units, c.price, c.payable) for c in e.administrator.claims])
    assert cert["status"] == "break"
    assert {(b["code"], b["subject"]) for b in cert["breaks"]} == {
        ("nav_per_unit", "Patient"), ("nav_per_unit", "Seed")}
    assert e.control_report()["certification"]["status"] == "break"
    before = (list(e.series), e.j.digest(), list(e.administrator.claims))
    e._deal()  # certification breaks withhold dealing through the existing dealing_blocked path
    assert (list(e.series), e.j.digest(), list(e.administrator.claims)) == before
    assert e.administrator.claims == ()
