import copy
import os

import pytest
from test_engine import CASE1

from fundforge.debrief import replay
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.tape import load


def completed(package=False, clock=False):
    e = Engine(load(CASE1))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    while s.e.ev.day < 13:
        s.handle("ana", f"pm-{s.version}", {"type": "ready", "version": s.version})
        s.handle("ben", f"mp-{s.version}", {"type": "ready", "version": s.version})
    order = {"order_id": "cover", "sym": "BRIN", "side": "COVER", "qty": 1250}
    if package:
        s.handle("ana", "propose", {"type": "propose", "package_id": "p", "orders": [order]})
        s.handle("ben", "sign", {"type": "sign", "package_id": "p", "digest": s.packages["p"].digest})
    else:
        s.handle("ana", "cover", {"type": "ticket", **order})
    while not s.e.finished():
        if clock:
            s.handle("ana", f"speed-{s.version}", {"type": "set_speed", "speed": 1})
            s.handle("clock", f"tick-{s.version}", {"type": "tick", "expected_version": s.version})
        else:
            s.handle("ana", f"pm-{s.version}", {"type": "ready", "version": s.version})
            s.handle("ben", f"mp-{s.version}", {"type": "ready", "version": s.version})
    return s


def decision_seq(s):
    return next(i for i, row in enumerate(s.log, 1) if row["command"]["type"] in ("ticket", "propose"))


def test_baseline_replay_is_exact_and_detached():
    s = completed()
    log, digest = copy.deepcopy(s.log), s.e.j.digest()
    result = replay(s)
    assert result["state"]["journal_digest"] == digest
    assert result["outcome"] == s.e.outcome()
    assert result["nav_difference"] == "0.00"
    assert replay(s) == result
    assert s.log == log and s.e.j.digest() == digest


def test_omitted_cover_has_its_own_branch_and_forced_recall_consequence():
    s = completed()
    baseline = replay(s)
    seq = decision_seq(s)
    branch = replay(s, seq)
    assert branch["branch_id"] != baseline["branch_id"]
    assert branch["finished"]
    assert branch == replay(s, seq)
    assert any(i["code"] == "forced_recall" for i in branch["incidents"])
    assert not any(i["code"] == "forced_recall" for i in baseline["incidents"])
    assert branch["state"]["journal_digest"] != baseline["state"]["journal_digest"]
    assert next(row for row in branch["timeline"] if row["seq"] == seq)["status"] == "omitted"


def test_omitted_package_does_not_reuse_partner_signature():
    s = completed(package=True)
    branch = replay(s, decision_seq(s))
    assert any(row["type"] == "sign" and "no pending package" in row["reason"] for row in branch["rejected"])
    assert any(i["code"] == "forced_recall" for i in branch["incidents"])


def test_unfinished_session_cannot_see_counterfactual_future():
    e = Engine(load(CASE1))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    with pytest.raises(CommandRejected, match="complete"):
        replay(s)


def test_clock_tokens_rebase_without_inventing_approvals():
    s = completed(clock=True)
    assert replay(s)["outcome"] == s.e.outcome()
    branch = replay(s, decision_seq(s))
    assert branch["finished"]
    assert not branch["rejected"]
    assert any(i["code"] == "forced_recall" for i in branch["incidents"])


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_analysis_survives_database_reload_without_writing_commands():
    from fundforge.liquidity import project
    from fundforge.store import Store

    store = Store(os.environ["DATABASE_URL"])
    try:
        room = store.create_room("case1", "Ana", "Ben", variant="base")
        rid = room["room_id"]
        users = {role: store.auth(rid, token) for role, token in room["tokens"].items()}
        for item in completed().log:
            store.apply(rid, users[item["role"]], item["key"], item["command"])
        version, s, _ = store.session(rid)
        evidence = store.verify(rid)
        a, b = replay(s, decision_seq(s)), project(s.e)
        assert store.verify(rid) == evidence
        store._cache.clear()
        restored_version, restored, _ = store.session(rid)
        assert restored_version == version
        assert restored.e.control_report()["administrator"] == s.e.control_report()["administrator"]
        assert restored.e.administrator.closes == s.e.administrator.closes
        assert restored.e.administrator.claims == s.e.administrator.claims
        assert replay(restored, decision_seq(restored)) == a
        assert project(restored.e) == b
        assert store.verify(rid) == evidence
    finally:
        store.close()


@pytest.mark.parametrize("seq", [0, 2, 999999])
def test_only_eligible_decisions_may_be_omitted(seq):
    with pytest.raises(CommandRejected, match="eligible"):
        replay(completed(), seq)


def test_incident_wording_cannot_change_outcome_or_score():
    s = completed()
    expected = s.e.outcome()
    for event in s.e.incident_events:
        event["text"] = "Neutral translated message"
    s.e.incidents = ["forced unpaid failed" for _ in s.e.incidents]
    changed = s.e.outcome()
    assert changed["label"] == expected["label"]
    assert changed["score"] == expected["score"]
    assert len(changed["forced"]) == len(expected["forced"])
    assert len(changed["unpaid"]) == len(expected["unpaid"])


def test_replay_http_requires_auth_version_and_completed_game(monkeypatch):
    from fastapi.testclient import TestClient

    import fundforge.api as api

    s = completed()

    class Store:
        def auth(self, room, token):
            if room != "room" or token != "seat":
                raise PermissionError("wrong seat")
            return "ana"

        def session(self, _room):
            return s.version, s, {}

    monkeypatch.setattr(api, "store", lambda: Store())
    c = TestClient(api.app)
    path, headers = "/api/rooms/room/debrief", {"Authorization": "Bearer seat"}
    assert c.post(path, json={"version": s.version}).status_code == 401
    assert c.post(path, headers=headers, json={"version": 0}).status_code == 409
    seq = decision_seq(s)
    response = c.post(path, headers=headers, json={"version": s.version, "omit_seq": seq})
    assert response.status_code == 200 and response.json()["omitted_seq"] == seq
    assert response.json() == replay(s, seq) and "investors" not in response.json()  # exact shape, no nulls added
