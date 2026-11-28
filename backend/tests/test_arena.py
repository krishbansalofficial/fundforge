"""Arena: magic-link accounts, game history, verified results, leaderboard, public replay and the weekly digest."""

import datetime as dt
import os
import random

import psycopg
import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
DSN = os.environ.get("DATABASE_URL", "")


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient

    from fundforge import arena
    from fundforge.api import app

    monkeypatch.setenv("FUNDFORGE_CLOCK", "0")
    mail: list[tuple[str, str, str]] = []
    monkeypatch.setattr(arena, "send_mail", lambda to, subject, body: mail.append((to, subject, body)))
    with TestClient(app) as c:
        c.mail = mail  # type: ignore[attr-defined]
        yield c


def sign_in(c, email):
    assert c.post("/api/auth/request", json={"email": email}).status_code == 202
    to, _, body = c.mail[-1]
    assert to == email.lower()
    token = body.split("#token=")[1].split()[0]
    s = c.post("/api/auth/verify", json={"token": token})
    assert s.status_code == 200
    again = c.post("/api/auth/verify", json={"token": token})
    assert again.status_code == 401  # single use
    return s.json()["session"]


def finish_solo(c, session=""):
    from fundforge.api import store

    r = c.post("/api/rooms", json={"solo_role": "pm"}, headers={"X-Session": session}).json()
    st, rid = store(), r["room_id"]
    uid = st.auth(rid, r["tokens"]["pm"])
    st.apply(rid, uid, "say-1", {"type": "say", "text": "private note"})  # never in a public replay
    for _ in range(300):
        version, s, _ = st.session(rid)
        if s.e.finished():
            break
        st.apply(rid, uid, f"r-{version}", {"type": "ready", "version": version})
    return rid, r["tokens"]["pm"]


def test_magic_link_account_profile_and_rename(client):
    c = client
    email = f"Player{random.randrange(10**9)}@Example.com"
    assert c.post("/api/auth/request", json={"email": "not-an-email"}).status_code == 422
    assert c.get("/api/me").status_code == 401
    session = sign_in(c, email)
    me = c.get("/api/me", headers={"X-Session": session}).json()
    assert me["email"] == email.lower() and me["display_name"].startswith("Player-") and me["games"] == []
    assert c.patch("/api/me", json={"display_name": "<script>"}, headers={"X-Session": session}).status_code == 422
    assert c.patch("/api/me", json={"display_name": "Desk Ana"}, headers={"X-Session": session}).json()[
        "display_name"] == "Desk Ana"
    assert sign_in(c, email) != session  # second sign-in, same account, new session
    c.post("/api/auth/signout", headers={"X-Session": session})
    assert c.get("/api/me", headers={"X-Session": session}).status_code == 401


def test_finished_room_is_verified_ranked_and_replayable(client):
    c = client
    session = sign_in(c, f"ranker{random.randrange(10**9)}@example.com")
    c.patch("/api/me", json={"display_name": "Ranker"}, headers={"X-Session": session})

    open_room = c.post("/api/rooms", json={"solo_role": "pm"}).json()
    unfinished = c.post(f"/api/rooms/{open_room['room_id']}/result",
                        headers={"Authorization": f"Bearer {open_room['tokens']['pm']}"})
    assert unfinished.status_code == 409

    rid, tok = finish_solo(c, session)
    assert c.post(f"/api/rooms/{rid}/result").status_code == 401  # only a seat may submit
    res = c.post(f"/api/rooms/{rid}/result", headers={"Authorization": f"Bearer {tok}"}).json()
    assert res["solo"] is True and res["players"] == {"pm": "Ranker", "mp": "Bot"}
    assert c.post(f"/api/rooms/{rid}/result", headers={"Authorization": f"Bearer {tok}"}).json() == res  # once

    board = c.get("/api/leaderboard?scenario=case1&limit=100").json()
    assert any(r["room_id"] == rid and r["score"] == res["score"] for r in board)
    assert [r["rank"] for r in board] == list(range(1, len(board) + 1))

    public = c.get(f"/api/results/{rid}").json()
    types = {t["type"] for t in public["timeline"]}
    assert "ready" in types and "say" not in types
    assert c.post(f"/api/results/{rid}/verify").json() == {
        "ok": True, "journal_digest": res["journal_digest"], "matches_recorded": True, "error": None}

    games = c.get("/api/me", headers={"X-Session": session}).json()["games"]
    assert games[0]["room_id"] == rid and games[0]["label"] == res["label"]


def test_tampered_room_is_never_ranked(client):
    c = client
    rid, tok = finish_solo(c)
    with psycopg.connect(DSN) as conn:  # someone with database access rewrites a command
        conn.execute("alter table commands disable trigger commands_append_only")
        conn.execute("update commands set command = jsonb_set(command, '{version}', '0') where room_id=%s and seq=1",
                     (rid,))
        conn.execute("alter table commands enable trigger commands_append_only")
    from fundforge.api import store
    store()._cache.clear()
    r = c.post(f"/api/rooms/{rid}/result", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 409 and "did not verify" in r.json()["message"]
    assert c.get(f"/api/results/{rid}").status_code == 404


def test_weekly_digest_sends_once_per_week(client):
    from fundforge import arena
    from fundforge.api import store

    c = client
    email = f"digest{random.randrange(10**9)}@example.com"
    session = sign_in(c, email)
    c.post("/api/rooms", json={"solo_role": "pm"}, headers={"X-Session": session})
    day = dt.date(3000 + random.randrange(5000), 6, 1)  # a week no other run has used
    c.mail.clear()
    first = arena.digest(store(), day)
    assert first["sent"] >= 1 and any(to == email and "1 game(s)" in body for to, _, body in c.mail)
    assert arena.digest(store(), day)["sent"] == 0
