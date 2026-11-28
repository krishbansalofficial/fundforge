"""Lobby join codes: one short code opens the other seat once, and only the token it returns plays."""

import os

import pytest

from fundforge.store import normalize_code

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient

    from fundforge.api import app

    monkeypatch.setenv("FUNDFORGE_CLOCK", "0")
    with TestClient(app) as client:
        yield client


def h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_code_opens_the_other_seat_once(client):
    r = client.post("/api/rooms", json={"pm_name": "Ana", "mp_name": "Ben"}).json()
    rid, pm, old_mp = r["room_id"], r["tokens"]["pm"], r["tokens"]["mp"]
    assert client.post(f"/api/rooms/{rid}/invite", headers=h("forged")).status_code == 401
    inv = client.post(f"/api/rooms/{rid}/invite", headers=h(pm)).json()
    assert inv["role"] == "mp" and len(inv["code"]) == 6
    assert client.post(f"/api/rooms/{rid}/invite", headers=h(pm)).json() == inv  # same open code, not a new one

    typed = f"{inv['code'][:3].lower()}-{inv['code'][3:]}"  # case and dashes do not matter
    joined = client.post("/api/join", json={"code": typed}).json()
    assert joined["room_id"] == rid and joined["role"] == "mp"
    assert client.get(f"/api/rooms/{rid}/view", headers=h(joined["token"])).json()["role"] == "mp"
    assert client.get(f"/api/rooms/{rid}/view", headers=h(old_mp)).status_code == 401  # rotated

    again = client.post("/api/join", json={"code": inv["code"]})
    assert again.status_code == 404 and again.json()["code"] == "not_found"
    assert client.post(f"/api/rooms/{rid}/invite", headers=h(pm)).json()["code"] != inv["code"]  # fresh after claim


def test_no_code_for_the_bot_seat(client):
    r = client.post("/api/rooms", json={"solo_role": "pm"}).json()
    assert client.post(f"/api/rooms/{r['room_id']}/invite", headers=h(r["tokens"]["pm"])).status_code == 422


def test_unknown_code_is_not_found(client):
    assert client.post("/api/join", json={"code": "ZZZZZZ"}).status_code == 404


def test_normalize_code():
    assert normalize_code(" ab c-23f ") == "ABC23F"


def test_lobby_socket_flow_join_nudge_and_reconnect(client):
    """The joined guest's socket is welcomed, the rotated token is refused, and a reconnect resumes at the
    current version (missed nudges are recovered from the welcome, never replayed)."""
    from starlette.websockets import WebSocketDisconnect

    from fundforge import presence

    r = client.post("/api/rooms", json={"pm_name": "Ana", "mp_name": "Ben"}).json()
    rid, pm, old_mp = r["room_id"], r["tokens"]["pm"], r["tokens"]["mp"]
    code = client.post(f"/api/rooms/{rid}/invite", headers=h(pm)).json()["code"]
    mp = client.post("/api/join", json={"code": code}).json()["token"]

    with client.websocket_connect(f"/api/rooms/{rid}/presence") as ws:
        ws.send_json({"type": "hello", "token": old_mp})
        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_json()
        assert closed.value.code == presence.UNAUTHORIZED

    with client.websocket_connect(f"/api/rooms/{rid}/presence") as host:
        host.send_json({"type": "hello", "token": pm})
        assert host.receive_json()["version"] == 0
        with client.websocket_connect(f"/api/rooms/{rid}/presence") as guest:
            guest.send_json({"type": "hello", "token": mp})
            assert guest.receive_json() == {"type": "welcome", "role": "mp", "version": 0, "partners": {}}
            client.post(f"/api/rooms/{rid}/commands", headers={**h(mp), "Idempotency-Key": "g1"},
                        json={"type": "ready", "version": 0})
            assert host.receive_json() == {"type": "version", "version": 1} == guest.receive_json()
        # guest dropped; the host acts while it is away
        client.post(f"/api/rooms/{rid}/commands", headers={**h(pm), "Idempotency-Key": "h1"},
                    json={"type": "ready", "version": 1})
        assert host.receive_json()["type"] in ("left", "version")
    with client.websocket_connect(f"/api/rooms/{rid}/presence") as back:  # reconnect
        back.send_json({"type": "hello", "token": mp})
        assert back.receive_json()["version"] == client.get(f"/api/rooms/{rid}/view", headers=h(mp)).json()["version"]


def test_sentry_events_carry_no_tokens():
    from fundforge.observability import scrub

    event = {"request": {"url": "/api/join", "headers": {"Authorization": "Bearer s", "X-Session": "x"},
                         "data": {"token": "magic"}, "query_string": "t=1"}}
    assert scrub(event) == {"request": {"url": "/api/join"}}
