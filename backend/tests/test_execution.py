from fundforge.execution import capacity, fill_price
from fundforge.money import D, cents

HS, K = D(5), D(2000)


def test_case1_s1_fills_match_scenario_contract():
    sell = fill_price(D(100), "SELL", 0, 20_000, 1_000_000, HS, K)
    assert sell == D("99.942000") and cents(sell * 20_000) == D("1998840.00")
    cover = fill_price(D(100), "COVER", 0, 1_250, 1_000_000, HS, K)
    assert cover == D("100.050031") and cents(cover * 1_250) == D("125062.54")


def test_case1_day18_beam_sale():
    p = fill_price(D(95), "SELL", 0, 20_000, 400_000, HS, K)
    assert p == D("94.905000") and cents(p * 20_000) == D("1898100.00")


def test_splitting_cannot_reduce_impact():
    whole = cents(fill_price(D(100), "SELL", 0, 20_000, 1_000_000, HS, K) * 20_000)
    a = cents(fill_price(D(100), "SELL", 0, 10_000, 1_000_000, HS, K) * 10_000)
    b = cents(fill_price(D(100), "SELL", 10_000, 10_000, 1_000_000, HS, K) * 10_000)
    assert abs((a + b) - whole) <= D("0.02")  # equal up to per-leg price quantization


def test_participation_cap_is_shared_and_halt_is_zero():
    assert capacity(42_120, D("0.05"), 0) == 2_106
    assert capacity(1_000_000, D("0.05"), 49_000) == 1_000
    assert capacity(0, D("0.05"), 0) == 0
