from dataclasses import replace

import pytest
from test_engine import CASE1

from fundforge.engine import Engine, InvariantError, Loan, Order
from fundforge.money import D
from fundforge.tape import TapeError, compile_tape, load


def engine(day=13, phase="EXEC_A"):
    e = Engine(load(CASE1))
    while (e.ev.day, e.ev.phase) != (day, phase):
        assert not e.finished(), "requested observation is not a decision barrier"
        e.advance()
    return e


def split_loan(e):
    e.broker.record(e.ev.date, "return", loan_id="L-open-BRIN", qty=2000)
    e.broker.record(e.ev.date, "loan", loan_id="L-expensive-BRIN", sym="BRIN", qty=2000, rate=D("0.80"))
    old = next(ln for ln in e.loans if ln.loan_id == "L-open-BRIN")
    old.qty -= 2000
    e.loans.insert(0, Loan("L-expensive-BRIN", "BRIN", 2000, D("0.80")))


def cover(e, qty, name="cover"):
    order = Order(name, "BRIN", "COVER", qty)
    e._fill(order)
    e.reconcile()
    return e.pending[-1]


def test_recalled_loan_precedes_more_expensive_loan_then_cost_priority():
    e = engine()
    split_loan(e)
    p = cover(e, 1500)
    assert p.returns == (("L-open-BRIN", 1250), ("L-expensive-BRIN", 250))
    assert e.recall_open == 0
    assert e.borrowed("BRIN") == 12500  # fees continue until actual T+1 return
    assert e._settle(p)
    e.pending.remove(p)
    assert {ln.loan_id: ln.qty for ln in e.loans if ln.sym == "BRIN"} == {
        "L-open-BRIN": 9250, "L-expensive-BRIN": 1750}
    e.reconcile()


def test_partial_covers_reserve_disjoint_shares_and_return_bound_loans():
    e = engine()
    split_loan(e)
    a = cover(e, 500, "a")
    b = cover(e, 900, "b")
    assert a.returns == (("L-open-BRIN", 500),)
    assert b.returns == (("L-open-BRIN", 750), ("L-expensive-BRIN", 150))
    # Changing rates after execution must not redirect either settlement.
    next(ln for ln in e.loans if ln.loan_id == "L-open-BRIN").rate = D("0.99")
    for p in (b, a):
        assert e._settle(p)
        e.pending.remove(p)
    e.reconcile()
    assert next(ln.qty for ln in e.loans if ln.loan_id == "L-expensive-BRIN") == 1850


def test_failed_cover_retains_reservation_across_replacement_transfer():
    e = engine(14)
    split_loan(e)
    p = cover(e, 500)
    p.amount += D("100000000")  # force settlement financing failure
    loans = [(ln.loan_id, ln.qty) for ln in e.loans]
    assert not e._settle(p)
    assert loans == [(ln.loan_id, ln.qty) for ln in e.loans]
    assert p.returns == (("L-open-BRIN", 500),)
    e._transfer_replacement(e.tape.raw["borrow"]["replacement_offer"])
    assert e.recall_open == 0
    assert next(ln.qty for ln in e.loans if ln.loan_id == "L-replacement-BRIN") == 750
    assert next(ln.qty for ln in e.loans if ln.loan_id == "L-expensive-BRIN") == 2000


def test_replacement_returns_named_old_loan_without_position_or_nav_change():
    e = engine(14)
    split_loan(e)
    before = (e.nav(), dict(e.pos), e.bal("collateral"))
    e._transfer_replacement(e.tape.raw["borrow"]["replacement_offer"])
    assert (e.nav(), e.pos, e.bal("collateral")) == before
    assert next(ln.qty for ln in e.loans if ln.loan_id == "L-open-BRIN") == 9250
    assert next(ln.qty for ln in e.loans if ln.loan_id == "L-expensive-BRIN") == 2000
    e.reconcile()


def test_accepted_but_incomplete_replacement_still_forces_residual():
    e = engine(15, "PUBLIC_MARK")
    e.replacement_accepted = True
    # Simulate an undelivered offer; advance() stops only at decision barriers.
    while e.next_event().day <= 15:
        e.advance()
    # Normal deadline already forced the outstanding recall despite acceptance.
    assert e.recall_resolved_by == "forced buy-in"
    assert any(o.forced == "recall" and o.filled == 1250 for o in e.orders)


def test_overdue_recall_uses_next_available_event_after_halt():
    raw = load(CASE1).raw
    raw["overrides"].append({"day": 15, "event": "EXEC_B", "volume": {"BRIN": 0}})
    e = Engine(compile_tape(raw))
    while e.next_event().day <= 15:
        e.advance()
    assert e.recall_open == 1250
    while (e.ev.day, e.ev.phase) != (16, "EXEC_A"):
        e.advance()
    assert e.recall_open == 0
    assert any(o.forced == "recall" and o.filled == 1250 for o in e.orders)


def test_unsettled_short_can_be_covered_with_same_identity():
    e = engine(12)
    e.event_fills = {}
    e._fill(Order("new", "BRIN", "SHORT", 100))
    short = e.pending[-1]
    # Reserve the more expensive incoming loan after exhausting the original.
    e.loans = [ln for ln in e.loans if ln.sym != "BRIN"]
    e.pos["BRIN"] = -100
    e._remark()
    p = cover(e, 100)
    assert p.returns == ((short.loan_id, 100),)
    for item in (short, p):
        assert e._settle(item)
        e.pending.remove(item)
    e.reconcile()
    assert e.borrowed("BRIN") == 0


def test_rerate_changes_only_named_loan_on_effective_day():
    raw = load(CASE1).raw
    raw["borrow"]["rate_changes"] = [{"day": 14, "loan_id": "L-open-BRIN", "rate": "0.15"}]
    e = Engine(compile_tape(raw))
    while (e.ev.day, e.ev.phase) != (13, "EXEC_A"):
        e.advance()
    assert next(ln.rate for ln in e.loans if ln.sym == "BRIN") == D("0.02")
    split_loan(e)
    while (e.ev.day, e.ev.phase) != (14, "PUBLIC_MARK"):
        e.advance()
    assert next(ln.rate for ln in e.loans if ln.loan_id == "L-open-BRIN") == D("0.15")
    assert next(ln.rate for ln in e.loans if ln.loan_id == "L-expensive-BRIN") == D("0.80")


@pytest.mark.parametrize("field,value", [("old_loan_id", "L-other"), ("new_loan_id", "L-open-BRIN")])
def test_invalid_replacement_identities_rejected(field, value):
    raw = load(CASE1).raw
    raw["borrow"]["replacement_offer"][field] = value
    with pytest.raises(TapeError, match="replacement"):
        compile_tape(raw)


def test_corrupt_borrow_balance_raises_explicit_invariant():
    e = engine()
    e.loans[0] = replace(e.loans[0], qty=e.loans[0].qty + 1)
    with pytest.raises(InvariantError, match="borrow_position"):
        e.reconcile()
