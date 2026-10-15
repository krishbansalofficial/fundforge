"""The explicit v1 campaign tape, chapter state, dealing and replay (not the v2 design document)."""

import copy
from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from fundforge import investors, store
from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.lp import State
from fundforge.money import CTX
from fundforge.tape import TapeError, compile_tape


def session(variant="base"):
    e = Engine(store._tape("campaign-v1", variant))
    e.advance()
    return Session(e, {"pm": "ana", "mp": "ben"})


def to_day(s, day):
    while not s.e.finished() and s.e.ev.day < day:
        key = str(s.version)
        s.handle("ana", "pm" + key, {"type": "ready"})
        s.handle("ben", "mp" + key, {"type": "ready"})


@pytest.mark.parametrize("variant", ["base", "rally", "lean-company"])
def test_campaign_all_three_chapters_finish_at_ordinary_payment_admin_and_replay(variant):
    s = session(variant)
    assert s.e.nav() > 0 and len(s.e.tape.instruments) == 6
    assert all(sym.startswith("FF-") for sym in s.e.tape.instruments)
    to_day(s, 99)
    e = s.e
    assert e.finished() and (e.ev.day, e.ev.phase) == (31, "OPEN_ADMIN")
    assert len(e.close_values) == 31  # opening plus thirty actual business closes
    assert {int(c["day"]) for c in e.lp.log if c["kind"] == "chapter_close"} == {10, 20, 30}
    assert {int(c["day"]) for c in e.lp.log if c["kind"] == "review"} == {3, 5, 13, 15, 23, 25}
    assert [c["day"] for c in e.certificates] == [20, 30]
    assert all(c["status"] == "certified" for c in e.certificates)
    assert e.control_report()["status"] == "checked"
    assert e.bal("redemption_payable") == 0 and e.paid["redemption"] > 0
    assert sum(e.j.balances("fund").values()) == 0
    assert any(i["code"] == "payroll_unpaid" for i in e.incident_events) == (variant == "lean-company")
    replay = session(variant)
    for item in s.log:
        replay.handle("ana" if item["role"] == "pm" else "ben", item["key"], item["command"])
    assert replay.e.j.digest() == e.j.digest() and replay.e.lp.log == e.lp.log


def test_campaign_chapter_returns_and_drawdown_restart_after_actual_close():
    s = session()
    to_day(s, 11)
    b = s.e.lp
    assert b.start_day == 11
    assert b.start_value == b.peaks
    facts = investors.chapter_facts(s.e, b.start_value, b.start_day)
    # At the next opening only weekend accrual has changed net value; chapter1 performance
    # is absent from chapter2's base and no future dealing certificate is used.
    for series in s.e.series:
        with localcontext(CTX):
            expected = (series.net / series.units / b.start_value[series.series_id] - 1) * 100
        assert facts[series.series_id].net_return_pp == expected
        assert abs(expected) < Decimal("0.1")


def test_campaign_research_budget_is_available_again_in_next_chapter():
    s = session()
    s.handle("ana", "first", {"type": "research", "topic": "demand_survey"})
    to_day(s, 11)
    s.handle("ana", "second", {"type": "research", "topic": "demand_survey"})
    assert [r["assigned_day"] for r in s.e.research_used] == [1, 11]


def test_campaign_gate_carried_units_roll_into_next_cutoff_without_double_counting():
    s = session()
    b = s.e.lp
    b.profiles["Seed"] = replace(b.profiles["Seed"], first_eligible_cutoff=15)
    b.states["Seed"] = State(Decimal(30))
    to_day(s, 16)
    g = s.handle("ana", "propose", {"type": "propose_gate", "package_id": "gate"})
    s.handle("ben", "sign", {"type": "sign", "package_id": "gate", "digest": g["digest"]})
    to_day(s, 21)
    carried = dict(s.e.lp.carried)
    assert carried and any(v > 0 for v in carried.values())
    to_day(s, 26)
    assert all(s.e.lp.requests[k] >= v for k, v in carried.items())
    to_day(s, 99)
    assert s.e.lp.carried == {}  # next dealing is ungated, so prior units were actually dealt
    assert any(i["code"] == "claim_unpaid" for i in s.e.incident_events)
    assert s.e.bal("redemption_payable") < 0  # dealing does not fabricate funding of the large claim


def test_campaign_rejects_missing_chapters_and_past_terminal_cutoffs():
    raw = copy.deepcopy(store._tape("campaign-v1").raw)
    raw["campaign"]["chapters"][1]["start_day"] = 12
    with pytest.raises(TapeError, match="contiguous"):
        compile_tape(raw)
    raw = copy.deepcopy(store._tape("campaign-v1").raw)
    raw["campaign"]["notice_cutoffs"] = [15, 30]
    with pytest.raises(TapeError, match="terminal"):
        compile_tape(raw)
