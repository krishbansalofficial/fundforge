"""Terminal information boundary, independent stress oracles and economic inertness."""

import os
from decimal import Decimal, localcontext

import pytest
from test_engine import CASE1

from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.tape import load
from fundforge.terminal import HISTORY_LIMIT, snapshot


def fresh(variant="base"):
    e = Engine(load(CASE1, variant))
    e.advance()
    return e


def test_opening_stress_matches_independent_hand_calculation():
    t = snapshot(fresh())
    # Opening longs 27.5m, shorts 5m, NAV 25m. A 10% fall loses
    # 2.75m on longs and gains 0.5m on shorts; maintenance is 35%/40%.
    selloff, squeeze, adverse = t["risk"]["stresses"]
    assert Decimal(selloff["pnl"]) == Decimal("-2250000")
    assert Decimal(selloff["nav"]) == Decimal("22750000")
    assert Decimal(selloff["maintenance_req"]) == Decimal("10462500")
    assert Decimal(squeeze["pnl"]) == Decimal("-1000000")
    assert Decimal(adverse["pnl"]) == Decimal("-4625000")
    assert Decimal(t["risk"]["restricted_collateral"]) == Decimal("5000000")


@pytest.mark.parametrize("variant", ["base", "rally"])
def test_history_contains_only_processed_events_and_replays_identically(variant):
    e, twin = fresh(variant), fresh(variant)
    while True:
        t = snapshot(e)
        assert t == snapshot(twin)
        assert len(t["history"]) == min(e.cursor, HISTORY_LIMIT)
        assert all(x["event"] <= e.cursor for x in t["history"])
        assert t["history"][-1]["marks"] == {s: str(m) for s, m in e.marks.items()}
        assert t["as_of"]["phase"] == e.ev.phase
        if e.finished():
            break
        e.advance()
        twin.advance()


def test_future_tape_and_unreleased_research_do_not_leak():
    e = fresh()
    before = snapshot(e)
    # Mutate unavailable data to sentinel values: the read model must not inspect it.
    e.tape.events[e.cursor].marks["BRIN"] = Decimal("987654321")
    e.tape.raw["research"]["topics"]["borrow"] = "SECRET_FUTURE_RESEARCH"
    e.tape.raw["variant"] = "SECRET_VARIANT"
    assert snapshot(e) == before
    assert "variant" not in before and "tape" not in before
    assert before["as_of"]["day"] == 12
    assert not any(n["code"] == "research_reveal" for n in before["news"])


def test_terminal_is_detached_and_does_not_change_authority_or_journal():
    e = fresh()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    s.handle("ana", "r", {"type": "ready", "version": 0})
    before, digest = s.view("ana"), e.j.digest()
    t = snapshot(e)
    t["history"][0]["marks"]["BRIN"] = "0"
    t["news"][0]["refs"]["tampered"] = True
    t["quotes"].clear()
    assert s.view("ana") == before and e.j.digest() == digest
    assert snapshot(e)["history"][0]["marks"]["BRIN"] != "0"
    assert "tampered" not in e.notices[0]["refs"]
    assert s.ready == {"pm"} and s.version == 1


def test_analytics_use_fixed_context_and_zero_nav_has_no_weight():
    e = fresh()
    expected = snapshot(e)
    with localcontext() as ctx:
        ctx.prec = 8
        assert snapshot(e) == expected
    # Distress display cannot divide by zero. This isolated test bypasses
    # reconciliation to exercise the boundary without changing scenario economics.
    e.nav = lambda: Decimal(0)
    assert all(q["weight"] is None for q in snapshot(e)["quotes"])


def test_borrow_rates_and_current_margin_terms_only():
    e = fresh()
    e.assign_research("borrow")
    while e.ev.day < 14:
        e.advance()
    e.accept_replacement()
    while e.ev.day < 15:
        e.advance()
    q = next(q for q in snapshot(e)["quotes"] if q["sym"] == "BRIN")
    # 11,250 original shares at 2%, 1,250 replacement shares at 40%.
    assert Decimal(q["borrow_rate"]) == Decimal("0.058")
    assert snapshot(e)["risk"]["maintenance_rates"] == {"long": "0.35", "short": "0.40"}
    while e.ev.day < 16:
        e.advance()
    assert snapshot(e)["risk"]["maintenance_rates"] == {"long": "0.70", "short": "0.90"}


def test_history_is_bounded_without_changing_since_start_anchor():
    e = fresh()
    first = e.observations[0]
    e.observations = [dict(first, event=i + 1) for i in range(HISTORY_LIMIT + 10)]
    t = snapshot(e)
    assert t["history_truncated"] and len(t["history"]) == HISTORY_LIMIT
    assert t["history"][0]["event"] == 11


def test_terminal_http_auth_and_consistent_version_without_database():
    from fastapi.testclient import TestClient

    from fundforge.api import app, store

    e = fresh()
    s = Session(e, {"pm": "ana", "mp": "ben"})

    class FakeStore:
        def auth(self, room, token):
            if room != "room" or token not in ("pm-token", "mp-token"):
                raise PermissionError("invalid seat token for this room")
            return "ana" if token == "pm-token" else "ben"

        def session(self, room):
            return 7, s, {}

    # Routes use store() directly; replace its module binding, not dependency overrides.
    import fundforge.api as api

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(api, "store", lambda: FakeStore())
        c = TestClient(app)
        path = "/api/rooms/room/terminal"
        assert c.get(path).status_code == 401
        assert c.get(path, headers={"Authorization": "Bearer forged"}).status_code == 401
        assert c.get("/api/rooms/other/terminal", headers={"Authorization": "Bearer pm-token"}).status_code == 401
        pm = c.get(path, headers={"Authorization": "Bearer pm-token"})
        partner = c.get(path, headers={"Authorization": "Bearer mp-token"})
        assert pm.status_code == 200 and partner.status_code == 200
        pm_data, mp_data = pm.json(), partner.json()
        assert pm_data.pop("role") == "pm" and mp_data.pop("role") == "mp"
        assert pm_data == mp_data
        assert pm.json()["version"] == 7 and pm.json()["as_of"]["event"] == e.cursor
        from fundforge.store import RoomIncompatible

        def incompatible(_self, _room):
            raise RoomIncompatible("room uses different rules")

        mp.setattr(FakeStore, "session", incompatible)
        assert c.get(path, headers={"Authorization": "Bearer pm-token"}).status_code == 409
        assert c.get("/api/rooms/room/view", headers={"Authorization": "Bearer pm-token"}).status_code == 409
        assert c.get("/api/rooms/room/ledger", headers={"Authorization": "Bearer pm-token"}).status_code == 409
    assert api.store is store


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_terminal_survives_postgres_replay_without_logging_reads():
    from fundforge.store import Store

    st = Store(os.environ["DATABASE_URL"])
    try:
        room = st.create_room("case1", "Ana", "Ben", variant="base")
        rid = room["room_id"]
        pm = st.auth(rid, room["tokens"]["pm"])
        mp = st.auth(rid, room["tokens"]["mp"])
        st.apply(rid, pm, "ready-pm", {"type": "ready", "version": 0})
        st.apply(rid, mp, "ready-mp", {"type": "ready", "version": 1})
        version, session, _ = st.session(rid)
        before = snapshot(session.e)
        verification = st.verify(rid)
        st._cache.clear()
        replay_version, replayed, _ = st.session(rid)
        assert replay_version == version == 2
        assert snapshot(replayed.e) == before
        assert st.verify(rid) == verification
    finally:
        st.close()
