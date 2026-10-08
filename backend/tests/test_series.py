"""FUND_ACCOUNTING §6 isolated arithmetic oracles 1-5, 7 as executable tests."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from fundforge.money import D, allocate
from fundforge.risk import exposures
from fundforge.series import Series, allocate_common, crystallize_annual, redeem, reprovision


def S(sid, units, hwm, gross):
    return reprovision(Series(sid, D(units), D(hwm), D(0)), D(gross))


def test_oracle1_provision_crystallize_and_new_hwm():
    s = S("A", 1000, 100, 110000)
    assert (s.provision, s.net) == (D(2000), D(108000))
    s, fixed = crystallize_annual(s)
    assert fixed == D(2000) and s.hwm == D(108)
    assert reprovision(s, D(104000)).provision == 0
    assert reprovision(s, D(108000)).provision == 0
    later = reprovision(s, D(110000))
    assert (later.provision, later.net) == (D(400), D(109600))


def test_oracle2_loss_reverses_provision():
    s = S("A", 1000, 100, 110000)
    assert reprovision(s, D(105000)).provision == D(1000)


def test_oracle3_entry_fairness():
    old, new = allocate_common([S("old", 1000, 100, 95000), S("new", 950, 100, 95000)], D(19000))
    assert (old.participation, old.provision, old.net) == (D(104500), D(900), D(103600))
    assert (new.participation, new.provision, new.net) == (D(104500), D(1900), D(102600))


def test_oracle4_cohort_allocation_uses_participation_not_net():
    a = Series("A", D(1000), D(100), D(108000), D(2000))
    b = Series("B", D(1000), D(120), D(100000))
    a2, b2 = allocate_common([a, b], D(21000))
    assert (a2.participation, a2.provision, a2.net) == (D(121000), D(4200), D(116800))
    assert (b2.participation, b2.provision, b2.net) == (D(110000), D(0), D(110000))
    assert a2.net + b2.net == D(226800)


def test_oracle5_partial_redemption_keeps_hwm():
    s = S("A", 1000, 100, 110000)
    s2, payable, fee = redeem(s, D(250))
    assert (payable, fee) == (D(27000), D(500))
    assert (s2.units, s2.provision, s2.net, s2.hwm) == (D(750), D(1500), D(81000), D(100))


def test_oracle7_redemption_leverage():
    assert exposures(D(25_000_000), D(27_500_000), D(5_000_000)) == (D("1.3"), D("0.9"))
    assert exposures(D(20_000_000), D(27_500_000), D(5_000_000)) == (D("1.625"), D("1.125"))


@given(st.integers(-10**10, 10**10), st.lists(st.integers(1, 10**9), min_size=1, max_size=8))
def test_allocation_conserves_cents(total_cents, weights):
    total = Decimal(total_cents) / 100
    out = allocate(total, {f"s{i:02}": Decimal(w) for i, w in enumerate(weights)})
    assert sum(out.values()) == total
