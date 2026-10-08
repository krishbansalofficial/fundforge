"""Case1 scripted paths run day 12 -> day 21 with invariants reconciled after every event."""

from pathlib import Path

import pytest

from fundforge.engine import CommandRejected, Engine
from fundforge.money import D
from fundforge.tape import load

CASE1 = Path(__file__).parents[2] / "fixtures" / "case1.json"


def run(script):
    """script: {(day, phase): callable(engine)} applied at the barrier before that execution event."""
    e = Engine(load(CASE1))
    e.advance()
    while not e.finished():
        nxt = e.next_event()
        if (nxt.day, nxt.phase) in script:
            script[(nxt.day, nxt.phase)](e)
        e.advance()
    return e


def s1(e_):  # early joint reduction: cover the recalled BRIN and pre-fund the redemption
    e_.submit_order("s1-cover", "BRIN", "COVER", 1250)
    e_.submit_order("s1-sell", "BEAM", "SELL", 20000)
    e_.set_reserve(D("1250000"))


S1 = {(14, "EXEC_A"): s1}


def s2_research(e_):
    e_.assign_research("borrow")


def s2_accept(e_):
    e_.accept_replacement()


def s2_cure(e_):
    e_.submit_order("s2-beam", "BEAM", "SELL", 2106)
    e_.submit_order("s2-alto", "ALTO", "SELL", 3000)


S2 = {(12, "EXEC_A"): s2_research, (14, "EXEC_A"): s2_accept, (16, "EXEC_A"): s2_cure,
      (18, "EXEC_A"): lambda e_: e_.submit_order("s2-beam2", "BEAM", "SELL", 20000)}


def test_s1_early_reduction_wins():
    e = run(S1)
    out = e.outcome()
    assert out["label"] == "WIN", out
    assert out["recall_resolved_by"] == "voluntary cover"
    fills = {o.order_id: o.fills[0] for o in e.orders}
    assert fills["s1-sell"]["amount"] == "1998840.00" and fills["s1-cover"]["amount"] == "125062.54"
    assert D(out["redemption_paid"]) > 0


def test_s2_replacement_borrow_and_cure_wins():
    e = run(S2)
    out = e.outcome()
    assert out["label"] == "WIN", out
    assert out["recall_resolved_by"] == "replacement borrow"
    assert any(l.rate == D("0.40") for l in e.loans)


def test_f1_inaction_triggers_forced_buy_in_but_stays_solvent():
    out = run({}).outcome()
    assert out["label"] == "SURVIVAL", out
    assert out["recall_resolved_by"] == "forced buy-in"
    assert D(out["redemption_paid"]) > 0  # investors still paid; forced actions are reported honestly


def test_f2_keeping_full_brin_short_without_cure_forces_margin_liquidation():
    out = run({(12, "EXEC_A"): s2_research, (14, "EXEC_A"): s2_accept}).outcome()
    assert out["label"] == "SURVIVAL", out
    assert out["recall_resolved_by"] == "replacement borrow"
    assert any("forced margin" in f for f in out["forced"])


def test_replay_is_deterministic():
    assert run(S1).outcome()["journal_digest"] == run(S1).outcome()["journal_digest"]


def test_fund_cash_never_pays_firm_payroll():
    e = run({})
    firm = e.j.balances("firm")
    # days 12-20 accrue 9 x $4,000; both $20,000 weekly bills (days 15, 20) are paid from firm cash only
    assert firm["payroll_expense"] == D("36000") and "payroll_payable" not in firm
    cross = [x for x in e.j.entries if x.entity == "firm" and "opening" not in x.memo and any(p.account == "cash" and p.amount > 0 for p in x.postings)]
    assert cross and all("fee" in x.memo for x in cross)


def test_late_replacement_is_rejected_and_barrier_rules_hold():
    e = Engine(load(CASE1))
    e.advance()
    e.assign_research("borrow")
    with pytest.raises(CommandRejected):
        e.accept_replacement()  # not yet revealed at day 12
    while (e.next_event().day, e.next_event().phase) != (15, "EXEC_A"):
        e.advance()
    with pytest.raises(CommandRejected, match="cutoff"):
        e.accept_replacement()


def test_player_cannot_short_brin_after_recall():
    e = Engine(load(CASE1))
    while (e.next_event().day, e.next_event().phase) != (13, "EXEC_A"):
        e.advance()
    o = e.submit_order("x", "BRIN", "SHORT", 100)
    e.advance()
    assert o.status == "REJECTED"
