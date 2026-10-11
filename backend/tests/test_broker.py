import copy
import json
import os
from dataclasses import FrozenInstanceError
from datetime import date, timedelta
from decimal import localcontext

import pytest
from test_engine import CASE1

from fundforge.broker import Broker
from fundforge.debrief import replay
from fundforge.engine import CommandRejected, Engine, Order
from fundforge.governance import Session
from fundforge.money import D
from fundforge.tape import TapeError, compile_tape, load
from fundforge.terminal import snapshot


def statement_tape():
    raw = copy.deepcopy(load(CASE1).raw)
    raw["broker_statements"] = json.loads((CASE1.parent / "broker_break_example.json").read_text())
    return compile_tape(raw)


def session():
    e = Engine(statement_tape())
    e.advance()
    return Session(e, {"pm": "ana", "mp": "ben"})


def advance(s, day):
    while not s.e.finished() and s.e.ev.day < day:
        for who in ("ana", "ben"):
            s.handle(who, f"ready-{s.version}", {"type": "ready", "version": s.version})


def correction(s, revision=2):
    return {"type": "resolve_statement", "statement_id": "opening-cash", "revision": revision, "version": s.version}


def test_independent_partial_return_weekend_rate_and_fee_rounding():
    b = Broker({"cash": "0", "collateral": "10000", "debt": "1000", "positions": {"X": -100}}, D("0.36"))
    friday = date(2026, 1, 23)
    for n in range(3):  # Friday and each weekend date: $10 stock loan + $0.50 debit
        b.accrue(friday + timedelta(days=n), {"X": D(100)}, D("0.18"))
    b.record(friday + timedelta(days=3), "return", loan_id="L-open-X", qty=25)
    b.accrue(friday + timedelta(days=3), {"X": D(100)}, D("0.18"))
    assert [f.amount for f in b.fees if f.loan_id == "L-open-X"] == [D(10), D(10), D(10), D("7.50")]
    assert b.accrued == D("39.50")
    b.record(friday + timedelta(days=4), "rate", loan_id="L-open-X", rate=D("0.72"))
    b.accrue(friday + timedelta(days=4), {"X": D(100)}, D("0.18"))
    assert b.accrued == D(55)
    with pytest.raises(ValueError, match="duplicate"):
        b.accrue(friday, {"X": D(100)}, D("0.18"))
    with pytest.raises(FrozenInstanceError):
        b.fees[0].amount = D(0)
    # Three independently rounded 1/3-cent days carry exactly one cent.
    tiny = Broker({"cash": "0", "collateral": "1", "debt": "0", "positions": {"X": -1}}, D("1.2"))
    for n in range(3):
        tiny.accrue(friday + timedelta(days=n), {"X": D(1)}, D(0))
    assert [f.amount for f in tiny.fees if f.loan_id == "L-open-X"] == [D("0.00"), D("0.01"), D("0.00")]


@pytest.mark.parametrize("account,amount", [("accrued_interest", D(-100)), ("cash", D(100)), ("debt", D(-100))])
def test_balanced_wrong_posting_passes_internal_invariants_but_fails_independent_controls(account, amount):
    e = Engine(load(CASE1))
    e.advance()
    e._post("balanced but fictitious", (account, amount), ("common_pnl", -amount))
    e.reconcile()
    report = e.control_report()
    assert report["status"] == "break"
    assert any(b["code"] in ("broker_balance", "financing_accrued") for b in report["breaks"])
    before = (e.j.digest(), e.broker.activities, e.broker.fees)
    assert e.control_report() == report
    assert (e.j.digest(), e.broker.activities, e.broker.fees) == before


def test_fee_date_error_is_caught_even_with_same_total_balances():
    e = Engine(load(CASE1))
    while e.ev.day < 13:
        e.advance()
    # Reversal/repost shifts a correct financing charge to the wrong calendar date.
    e._post("reverse wrong date", ("common_pnl", D(-1)), ("accrued_interest", D(1)), date_=date(2026, 1, 20))
    e._post("repost wrong date", ("common_pnl", D(1)), ("accrued_interest", D(-1)), date_=date(2026, 1, 21))
    e.reconcile()
    assert [b["code"] for b in e.control_report()["breaks"]] == ["financing_date", "financing_date"]


def test_real_partial_cover_keeps_fees_until_t_plus_one_return():
    e = Engine(load(CASE1))
    e.advance()
    e.submit_order("partial", "BRIN", "COVER", 500)
    while e.ev.day < 14:
        e.advance()
    lines = [f for f in e.broker.fees if f.loan_id == "L-open-BRIN"]
    assert [(f.date, f.qty) for f in lines] == [("2026-01-20", 12500), ("2026-01-21", 12000)]
    assert e.control_report()["status"] == "checked"
    expected = e.control_report()
    with localcontext() as context:
        context.prec = 6
        assert e.control_report() == expected


def test_solo_operating_partner_reviews_only_published_matching_evidence():
    from fundforge.bot import act, plan

    s = session()
    assert not any(c["type"] == "resolve_statement" for c in plan(s, "mp"))
    advance(s, 13)
    act(s, "mp", "ben", "bot-review")
    assert s.e.control_report()["statement_queue"][0]["status"] == "resolved"


def test_statement_correction_is_as_of_private_until_published_and_never_erases_evidence():
    s = session()
    before = snapshot(s.e, "mp")
    q = before["risk"]["controls"]["statement_queue"][0]
    assert q["age_calendar_days"] == 0 and len(q["history"]) == 1
    assert not q["can_resolve"] and "duplicate $100" not in json.dumps(before)
    with pytest.raises(CommandRejected, match="published correction"):
        s.handle("ben", "early", correction(s))
    advance(s, 13)
    queue = s.e.control_report()["statement_queue"][0]
    assert queue["age_calendar_days"] == 1 and len(queue["history"]) == 2
    assert queue["status"] == "open" and queue["can_resolve"]
    with pytest.raises(CommandRejected, match="managing partner"):
        s.handle("ana", "wrong-role", correction(s))
    with pytest.raises(CommandRejected, match="latest revision"):
        s.handle("ben", "old-revision", correction(s, 1))
    cmd = correction(s)
    with pytest.raises(CommandRejected, match="stale"):
        s.handle("ben", "stale", {**cmd, "version": -1})
    digest, evidence = s.e.j.digest(), s.e.broker.statements
    answer = s.handle("ben", "review", cmd)
    assert s.handle("ben", "review", cmd) == answer  # no second resolution on retry
    assert s.e.j.digest() == digest and s.e.broker.statements == evidence
    assert len(s.e.broker.resolutions) == 1 and s.e.control_report()["status"] == "checked"
    assert s.e.control_report()["statement_queue"][0]["status"] == "resolved"
    with pytest.raises(FrozenInstanceError):
        s.e.broker.statements[0].balance = D(0)


def test_open_break_blocks_new_risk_and_dealing_but_preserves_reductions_and_deadline_failure():
    s = session()
    with pytest.raises(CommandRejected, match="new risk"):
        s.e.submit_order("new", "ALTO", "BUY", 1)
    queued = Order("previously-authorized", "ALTO", "BUY", 1)
    s.e._fill(queued)
    assert queued.status == "REJECTED"
    s.e.submit_order("reduce", "ALTO", "SELL", 100)
    s.e.cancel_order("reduce")
    s.e.submit_order("cover", "BRIN", "COVER", 1250)
    opening_units = sum(x.units for x in s.e.series)
    advance(s, 21)
    assert s.e.finished() and s.e.control_report()["statement_queue"][0]["status"] == "open"
    assert sum(x.units for x in s.e.series) == opening_units
    assert s.e.bal("redemption_payable") == 0 and s.e.paid.get("interest invoice", D(0)) > 0
    assert next(o.filled for o in s.e.orders if o.order_id == "cover") == 1250
    assert any(i["code"] == "dealing_blocked" for i in s.e.incident_events)
    assert s.e.outcome()["label"] == "DISTRESS"
    assert len(s.e.broker.statements) == 2


def test_resolving_before_close_allows_dealing_and_exact_replay():
    s = session()
    advance(s, 13)
    omitted_seq = s.version + 1
    s.handle("ben", "review", correction(s))
    advance(s, 21)
    assert s.e.paid["redemption"] > 0
    assert replay(s)["finished"]
    branch = replay(s, omitted_seq)
    assert branch["finished"] and any("dealing" in text.lower() for text in branch["outcome"]["unpaid"])
    restored = Session(Engine(s.e.tape), dict(s.partners))
    restored.e.advance()
    for row in s.log:
        restored.handle(s.partners[row["role"]], row["key"], row["command"])
    assert restored.e.control_report() == s.e.control_report()


def test_statement_published_at_dealing_close_is_checked_before_units_burn():
    raw = copy.deepcopy(statement_tape().raw)
    raw["broker_statements"] = raw["broker_statements"][:1]
    raw["broker_statements"][0]["available_at"] = {"day": 20, "phase": "CLOSE"}
    e = Engine(compile_tape(raw))
    while not e.finished():
        e.advance()
    assert e.paid.get("redemption", D(0)) == 0
    assert any(i["code"] == "dealing_blocked" for i in e.incident_events)


@pytest.mark.parametrize("change", [
    {"revision": 3}, {"supersedes": 99}, {"reason": ""}, {"balance": "NaN"}, {"balance": "0.001"},
    {"as_of": {"day": 14, "phase": "OPEN_ADMIN"}}, {"available_at": {"day": 12, "phase": "OPEN_ADMIN"}},
    {"source": "some other source"}, {"account": "unknown"},
])
def test_invalid_authored_corrections_are_rejected(change):
    raw = copy.deepcopy(statement_tape().raw)
    raw["broker_statements"][1].update(change)
    with pytest.raises(TapeError, match="broker_statements"):
        compile_tape(raw)


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_statement_resolution_and_original_evidence_survive_postgres_reload():
    import fundforge.store as storage

    store = storage.Store(os.environ["DATABASE_URL"])
    try:
        room = store.create_room("case1-controls", "Ana", "Ben", variant="base")
        rid = room["room_id"]
        users = {r: store.auth(rid, token) for r, token in room["tokens"].items()}
        _, s, _ = store.session(rid)
        while s.e.ev.day < 13:
            for role in ("pm", "mp"):
                version, s, _ = store.session(rid)
                store.apply(rid, users[role], f"ready-{version}", {"type": "ready", "version": version})
            _, s, _ = store.session(rid)
        store.apply(rid, users["mp"], "review", correction(s))
        _, s, _ = store.session(rid)
        expected = s.e.control_report()
        store._cache.clear()
        _, restored, _ = store.session(rid)
        assert restored.e.control_report() == expected
        assert expected["statement_queue"][0]["status"] == "resolved"
        assert len(restored.e.broker.statements) == 2
        assert store.verify(rid)["version"] == restored.version
    finally:
        store.close()
