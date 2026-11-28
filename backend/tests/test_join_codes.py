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
