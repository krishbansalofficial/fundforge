import copy
import json
import os

import pytest
from test_engine import CASE1

from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.tape import load
from fundforge.terminal import snapshot

SECRET = "PRIVATE_BORROW_EVIDENCE_731"


def fresh():
    tape = load(CASE1)
    tape.raw["research"]["topics"]["borrow"] = SECRET
    e = Engine(tape)
    e.advance()
    return Session(e, {"pm": "ana", "mp": "ben"})


def advance(s):
    s.handle("ana", f"pm-{s.version}", {"type": "ready", "version": s.version})
    s.handle("ben", f"mp-{s.version}", {"type": "ready", "version": s.version})


def reveal(s):
    while s.e.ev.day < 13:
        advance(s)


def assign_borrow(s):
    return s.handle("ben", "borrow", {"type": "visit", "location": "broker", "assignment": "borrow"})


def test_independent_role_slots_but_one_assignment_per_window():
    s = fresh()
    assign_borrow(s)
    s.handle("ana", "demand", {"type": "visit", "location": "research", "assignment": "demand_survey"})
    assert all(s.view(u)["attention"]["committed"] for u in ("ana", "ben"))
    before = copy.deepcopy(s.view("ben"))
    with pytest.raises(CommandRejected, match="attention"):
        s.handle("ben", "debt", {"type": "research", "topic": "debt_schedule"})
    assert s.view("ben") == before
    advance(s)
    assert not s.view("ben")["attention"]["committed"]
    s.handle("ben", "debt-next", {"type": "research", "topic": "debt_schedule"})
    s.handle("ana", "crowding", {"type": "research", "topic": "crowding"})
    assert len(s.e.research_used) == 4
    assert len(s.view("ben")["research"]["used"]) == 2
    assert len(s.view("ana")["research"]["used"]) == 2


@pytest.mark.parametrize("user,command,reason", [
    ("ana", {"type": "research", "topic": "borrow"}, "other partner"),
    ("ben", {"type": "visit", "location": "research", "assignment": "borrow"}, "location"),
    ("ben", {"type": "share_research", "topic": "borrow"}, "arrived"),
])
def test_invalid_assignment_or_early_sharing_is_atomic(user, command, reason):
    s = fresh()
    before = s.view(user)
    with pytest.raises(CommandRejected, match=reason):
        s.handle(user, "invalid", command)
    assert s.view(user) == before


def test_private_evidence_does_not_leak_through_view_terminal_or_clock():
    s = fresh()
    assign_borrow(s)
    assert SECRET not in json.dumps(s.view("ben"))  # owner must wait for availability
    # Tick at reveal exercises the shared pause-reason boundary.
    while s.e.ev.day < 13:
        s.handle("ana", f"speed-{s.version}", {"type": "set_speed", "speed": 1})
        result = s.handle("clock", f"tick-{s.version}", {"type": "tick", "expected_version": s.version})
        assert SECRET not in json.dumps(result)
    assert SECRET in json.dumps(s.view("ben"))
    assert SECRET in json.dumps(snapshot(s.e, "mp"))
    assert SECRET not in json.dumps(s.view("ana"))
    assert SECRET not in json.dumps(snapshot(s.e, "pm"))
    assert SECRET not in json.dumps(snapshot(s.e))  # no role means public only
    assert s.view("ben")["recall"]["offer_visible"]
    assert not s.view("ana")["recall"]["offer_visible"]
    for user in ("ana", "ben"):
        assert any(n["code"] == "recall" for n in s.view(user)["notices"])


def test_only_owner_can_share_available_evidence_and_replay_preserves_it():
    s = fresh()
    assign_borrow(s)
    reveal(s)
    with pytest.raises(CommandRejected, match="owner"):
        s.handle("ana", "steal", {"type": "share_research", "topic": "borrow"})
    s.handle("ben", "share", {"type": "share_research", "topic": "borrow"})
    assert SECRET in json.dumps(s.view("ana"))
    assert SECRET in json.dumps(snapshot(s.e, "pm"))
    assert s.view("ana")["recall"]["offer_visible"]
    restored = fresh()
    for row in s.log:
        restored.handle(restored.partners[row["role"]], row["key"], row["command"])
    assert restored.view("ana") == s.view("ana")
    assert restored.view("ben") == s.view("ben")
    with pytest.raises(CommandRejected, match="already shared"):
        s.handle("ben", "again", {"type": "share_research", "topic": "borrow"})


def test_per_role_budget_does_not_borrow_other_partners_capacity():
    s = fresh()
    s.e.tape.raw["research"]["budget_per_role"] = 1
    assign_borrow(s)
    advance(s)
    with pytest.raises(CommandRejected, match="budget"):
        s.handle("ben", "debt", {"type": "research", "topic": "debt_schedule"})
    s.handle("ana", "demand", {"type": "research", "topic": "demand_survey"})


def test_attention_does_not_block_mandatory_trading_or_signatures():
    s = fresh()
    s.handle("ana", "demand", {"type": "research", "topic": "demand_survey"})
    assign_borrow(s)
    s.handle("ana", "ticket", {"type": "ticket", "order_id": "x", "side": "SELL", "sym": "ALTO", "qty": 10})
    p = s.handle("ana", "pkg", {"type": "propose", "package_id": "p", "orders": [
        {"order_id": "y", "side": "SELL", "sym": "ALTO", "qty": 10}]})
    s.handle("ben", "sign", {"type": "sign", "package_id": "p", "digest": p["digest"]})
    assert len(s.e.orders) == 2


def test_http_terminal_cannot_spoof_role_or_read_private_partner_evidence(monkeypatch):
    from fastapi.testclient import TestClient

    import fundforge.api as api

    s = fresh()
    assign_borrow(s)
    reveal(s)

    class Store:
        def auth(self, room, token):
            if room != "room" or token not in ("ana", "ben"):
                raise PermissionError("invalid seat")
            return token

        def session(self, _room):
            return s.version, s, {}

        def clock_info(self, _room):
            return {"running": False, "version": 0}

    monkeypatch.setattr(api, "store", lambda: Store())
    c = TestClient(api.app)
    for suffix in ("terminal?role=mp", "view?role=mp"):
        assert SECRET not in c.get(f"/api/rooms/room/{suffix}", headers={"Authorization": "Bearer ana"}).text
        assert SECRET in c.get(f"/api/rooms/room/{suffix}", headers={"Authorization": "Bearer ben"}).text


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_private_evidence_and_attention_survive_postgres_replay():
    from fundforge.store import Store

    store = Store(os.environ["DATABASE_URL"])
    try:
        room = store.create_room("case1", "Ana", "Ben", variant="base")
        rid = room["room_id"]
        users = {role: store.auth(rid, token) for role, token in room["tokens"].items()}
        store.apply(rid, users["mp"], "borrow", {"type": "visit", "location": "broker", "assignment": "borrow"})
        _, s, _ = store.session(rid)
        while s.e.ev.day < 13:
            for role in ("pm", "mp"):
                version, s, _ = store.session(rid)
                store.apply(rid, users[role], f"ready-{version}", {"type": "ready", "version": version})
            _, s, _ = store.session(rid)
        text = s.e.tape.raw["research"]["topics"]["borrow"]
        assert text not in json.dumps(s.view(users["pm"]))
        assert text in json.dumps(s.view(users["mp"]))
        store._cache.clear()
        _, restored, _ = store.session(rid)
        assert restored.view(users["mp"]) == s.view(users["mp"])
        assert restored.view(users["pm"]) == s.view(users["pm"])
        store.apply(rid, users["mp"], "share", {"type": "share_research", "topic": "borrow"})
        store._cache.clear()
        _, shared, _ = store.session(rid)
        assert text in json.dumps(shared.view(users["pm"]))
        assert store.verify(rid)["version"] == shared.version
    finally:
        store.close()
