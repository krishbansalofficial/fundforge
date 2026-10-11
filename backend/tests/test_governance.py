import json
from pathlib import Path

import pytest

from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.tape import load

CASE1 = Path(__file__).parents[2] / "fixtures" / "case1.json"
P = {"pm": "ana", "mp": "ben"}


def session():
    e = Engine(load(CASE1))
    e.advance()
    return Session(e, P)


def test_requires_two_distinct_partners():
    with pytest.raises(ValueError):
        Session(Engine(load(CASE1)), {"pm": "ana", "mp": "ana"})


def test_large_order_needs_other_partners_signature_on_same_digest():
    s = session()
    with pytest.raises(CommandRejected, match="5% of NAV"):
        s.handle("ana", "k1", {"type": "ticket", "order_id": "t1", "sym": "BEAM", "side": "SELL", "qty": 20000})
    pkg = s.handle("ana", "k2", {"type": "propose", "package_id": "p1",
                                 "orders": [{"order_id": "o1", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
    with pytest.raises(CommandRejected, match="own proposal"):
        s.handle("ana", "k3", {"type": "sign", "package_id": "p1", "digest": pkg["digest"]})
    with pytest.raises(CommandRejected, match="does not match"):
        s.handle("ben", "k4", {"type": "sign", "package_id": "p1", "digest": "0" * 64})
    out = s.handle("ben", "k5", {"type": "sign", "package_id": "p1", "digest": pkg["digest"]})
    assert out["status"] == "AUTHORIZED_QUEUED"
    assert [o.order_id for o in s.e.orders] == ["o1"]


def test_idempotent_retry_and_key_reuse():
    s = session()
    cmd = {"type": "ticket", "order_id": "t1", "sym": "ALTO", "side": "SELL", "qty": 1000}
    first = s.handle("ana", "k1", cmd)
    assert s.handle("ana", "k1", cmd) == first  # retry: same result, no second order
    assert len(s.e.orders) == 1
    with pytest.raises(CommandRejected, match="reused"):
        s.handle("ana", "k1", {**cmd, "qty": 2000})


def test_role_boundaries_and_outsiders():
    s = session()
    with pytest.raises(CommandRejected, match="managing partner"):
        s.handle("ana", "k1", {"type": "set_reserve", "amount": "1000000"})
    with pytest.raises(CommandRejected, match="portfolio manager"):
        s.handle("ben", "k2", {"type": "ticket", "order_id": "t", "sym": "ALTO", "side": "SELL", "qty": 10})
    with pytest.raises(CommandRejected, match="not a partner"):
        s.handle("mallory", "k3", {"type": "ready"})


def test_time_advances_only_when_both_ready_and_any_change_resets():
    s = session()
    before = s.e.cursor
    assert s.handle("ana", "r1", {"type": "ready"})["advanced"] is False
    s.handle("ben", "c1", {"type": "set_reserve", "amount": "100"})  # change clears readiness
    assert s.handle("ben", "r2", {"type": "ready"})["advanced"] is False
    assert s.handle("ana", "r3", {"type": "ready"})["advanced"] is True
    assert s.e.cursor > before


def test_unsigned_package_expires_when_time_advances():
    s = session()
    pkg = s.handle("ana", "k", {"type": "propose", "package_id": "p",
                                "orders": [{"order_id": "o", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
    s.handle("ana", "r1", {"type": "ready"})
    s.handle("ben", "r2", {"type": "ready"})
    with pytest.raises(CommandRejected):
        s.handle("ben", "k2", {"type": "sign", "package_id": "p", "digest": pkg["digest"]})


def test_view_never_contains_future_information():
    s = session()
    blob = json.dumps(s.view("ana"))
    assert "squeeze" not in blob and "40%" not in blob and "\"95\"" not in blob
    assert "tape" not in s.view("ben")


def test_decision_history_records_who_did_what_but_not_ready_clicks():
    s = session()
    s.handle("ben", "k1", {"type": "research", "topic": "borrow"})
    s.handle("ana", "k2", {"type": "ready"})
    d = s.view("ana")["decisions"]
    assert d == [{"day": 12, "phase": "PUBLIC_MARK", "role": "mp", "type": "research", "detail": {"topic": "borrow"}}]


def test_rejected_command_leaves_no_partial_state():
    s = session()
    pkg = s.handle("ana", "k1", {"type": "propose", "package_id": "p",
                                 "orders": [{"order_id": "a", "sym": "BEAM", "side": "SELL", "qty": 20000},
                                            {"order_id": "b", "sym": "ZZZZ", "side": "SELL", "qty": 1}]})
    digest = s.e.j.digest()
    with pytest.raises(CommandRejected):
        s.handle("ben", "k2", {"type": "sign", "package_id": "p", "digest": pkg["digest"]})  # 2nd leg invalid
    assert s.e.orders == [] and s.packages["p"].status == "PENDING_APPROVAL" and s.e.j.digest() == digest


def test_unknown_command_is_rejected_not_crash():
    with pytest.raises(CommandRejected, match="unknown command"):
        session().handle("ana", "k", {"type": "launch_missiles"})


def test_ready_bound_to_seen_version():
    s = session()
    seen = s.version
    s.handle("ana", "k1", {"type": "propose", "package_id": "p",
                           "orders": [{"order_id": "a", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
    with pytest.raises(CommandRejected, match="stale"):
        s.handle("ben", "k2", {"type": "ready", "version": seen})
    assert s.handle("ben", "k3", {"type": "ready", "version": s.version})["advanced"] is False


def tick(s):
    return s.handle("clock", f"tick-{s.version}", {"type": "tick", "expected_version": s.version})


def test_clock_runs_only_when_played_and_auto_pauses_on_news():
    s = session()
    with pytest.raises(CommandRejected, match="paused"):
        tick(s)  # starts paused
    s.handle("ana", "go", {"type": "set_speed", "speed": 2})
    paused_at = None
    for _ in range(60):
        tick(s)
        if s.clock["paused"]:
            paused_at = (s.e.ev.day, s.clock["reason"])
            break
    assert paused_at is not None and paused_at[0] == 13  # day-13 recall notice stops the clock
    with pytest.raises(CommandRejected, match="paused"):
        tick(s)


def test_clock_waits_for_signature_and_rejects_stale_or_forged_ticks():
    s = session()
    s.handle("ana", "p", {"type": "propose", "package_id": "p",
                          "orders": [{"order_id": "o", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
    s.handle("ben", "go", {"type": "set_speed", "speed": 1})
    cursor = s.e.cursor
    assert tick(s)["advanced"] is False and s.clock["reason"].startswith("A package")
    assert s.e.cursor == cursor and s.packages["p"].status == "PENDING_APPROVAL"
    with pytest.raises(CommandRejected, match="stale"):
        s.handle("clock", "old", {"type": "tick", "expected_version": 0})
    with pytest.raises(CommandRejected, match="only the clock"):
        s.handle("ana", "x", {"type": "tick", "expected_version": s.version})
    with pytest.raises(CommandRejected, match="can only tick"):
        s.handle("clock", "y", {"type": "set_speed", "speed": 4})


def test_full_game_on_the_clock_matches_replay():
    s = session()
    s.handle("ana", "go", {"type": "set_speed", "speed": 4})
    for _ in range(200):
        if s.e.finished():
            break
        if s.clock["paused"]:
            s.handle("ben", f"resume{s.version}", {"type": "set_speed", "speed": 4})
        tick(s)
    assert s.e.finished() and s.clock["reason"] == "Season complete."
    r = session()
    for x in s.log:  # ticks are ordinary logged commands, so replay is exact
        r.handle({"pm": "ana", "mp": "ben", "system": "clock"}[x["role"]], x["key"], x["command"])
    assert r.e.j.digest() == s.e.j.digest()
