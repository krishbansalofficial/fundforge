"""Independent exhaustive oracle for rounded quadratic limit execution."""

from dataclasses import replace
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from itertools import pairwise

import pytest
from test_engine import CASE1

from fundforge.engine import Engine, Order
from fundforge.execution import limit_quantity
from fundforge.money import CTX, D
from fundforge.tape import load

REF, HS, K = D(100), D(5), D(2000)


def oracle_price(side, same, q, volume, ref=REF, hs=HS, k=K):
    # Expand ((same+q)^3 - same^3)/q independently of total_cost/fill_price.
    with localcontext(CTX):
        adverse = ref * (hs + k * Decimal(3 * same * same + 3 * same * q + q * q)
                         / Decimal(volume * volume)) / 10000
        sign = 1 if side in ("BUY", "COVER") else -1
        return (ref + sign * adverse).quantize(D("0.000001"), rounding=ROUND_HALF_EVEN)


@pytest.mark.parametrize("side", ["BUY", "COVER", "SELL", "SHORT"])
@pytest.mark.parametrize("same", [0, 7, 29])
def test_search_matches_exhaustive_rounded_oracle(side, same):
    # Every distinct price, its adjacent microticks, and midpoint limits probe
    # inclusive boundaries and HALF_EVEN plateaus across all small quantities.
    prices = [oracle_price(side, same, q, 1000) for q in range(1, 51)]
    limits = {p + offset for p in prices for offset in (D(0), D("0.000001"), D("-0.000001"))}
    limits.update((a + b) / 2 for a, b in pairwise(prices))
    for limit in limits:
        expected = max([0] + [q for q, p in enumerate(prices, 1)
                             if (p <= limit if side in ("BUY", "COVER") else p >= limit)])
        assert limit_quantity(D(100), side, same, 50, 1000, D(5), D(2000), limit) == expected


@pytest.mark.parametrize("side", ["BUY", "COVER", "SELL", "SHORT"])
def test_old_step_down_underfilled_boundary(side):
    limit = oracle_price(side, 0, 99, 1000)
    assert limit_quantity(D(100), side, 0, 100, 1000, D(5), D(2000), limit) == 99
    # Previously 100 failed, then q -= q//20 skipped straight to 95.
    assert oracle_price(side, 0, 100, 1000) != limit


@pytest.mark.parametrize("side", ["BUY", "COVER", "SELL", "SHORT"])
def test_zero_impact_full_plateau_and_empty_bounds(side):
    price = oracle_price(side, 11, 1, 1000, k=D(0))
    assert limit_quantity(D(100), side, 11, 50, 1000, D(5), D(0), price) == 50
    assert limit_quantity(D(100), side, 11, 0, 1000, D(5), D(0), price) == 0
    assert limit_quantity(D(100), side, 11, 50, 0, D(5), D(0), None) == 0
    assert limit_quantity(D(100), side, 11, 50, 1000, D(5), D(0), None) == 50


@pytest.mark.parametrize("side,sym", [("BUY", "ALTO"), ("SELL", "ALTO"),
                                      ("SHORT", "BRIN"), ("COVER", "BRIN")])
def test_real_engine_limit_fill_and_shared_capacity(side, sym):
    e = Engine(load(CASE1))
    while e.ev.phase != "EXEC_A":
        e.advance()
    # Detached execution event isolates the search from rival flow. Closing
    # sides use the actual opening holdings; opening sides are tiny lawful legs.
    e.ev = replace(e.ev, volume={**e.ev.volume, sym: 1000})
    key = "BUY" if side in ("BUY", "COVER") else "SELL"
    e.event_fills = {(sym, "both"): 10, (sym, key): 7}
    ref = e.marks[sym]
    limit = oracle_price(side, 7, 39, 1000, ref)
    order = Order("boundary", sym, side, 100, limit)
    e._fill(order)
    assert order.filled == 39  # 40 capacity, but only 39 at the limit
    assert order.fills[0]["price"] == str(limit)
    assert order.status == "PARTIALLY_FILLED"
    assert e.event_fills[(sym, "both")] == 49
    assert e.event_fills[(sym, key)] == 46
    e.reconcile()


@pytest.mark.parametrize("side,sym", [("SELL", "ALTO"), ("COVER", "BRIN")])
def test_reduce_only_never_crosses_position(side, sym):
    e = Engine(load(CASE1))
    while e.ev.phase != "EXEC_A":
        e.advance()
    held = abs(e.pos[sym])
    e.event_fills = {}
    order = Order("close", sym, side, held + 100, D(0) if side == "SELL" else D(10000))
    e._fill(order)
    assert order.filled == min(held, int(e.ev.volume[sym] * D(e.cfg["participation"])))
    assert e.pos[sym] >= 0 if side == "SELL" else e.pos[sym] <= 0
    e.reconcile()
