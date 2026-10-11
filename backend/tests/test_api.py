import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient

    from fundforge.api import app, store

    monkeypatch.setenv("FUNDFORGE_CLOCK", "0")
    with TestClient(app) as client:
        yield client
        pool = store().pool
    assert pool.closed
    assert store.cache_info().currsize == 0


def test_two_seat_flow_over_http(client):
    c = client
    r = c.post("/api/rooms", json={"pm_name": "Ana", "mp_name": "Ben"}).json()
    rid, pm, mp = r["room_id"], r["tokens"]["pm"], r["tokens"]["mp"]
    h = lambda t, k=None: {"Authorization": f"Bearer {t}", **({"Idempotency-Key": k} if k else {})}  # noqa: E731
    assert c.get(f"/api/rooms/{rid}/view").status_code == 401
    assert c.get(f"/api/rooms/{rid}/view", headers=h("forged")).status_code == 401
    v = c.get(f"/api/rooms/{rid}/view", headers=h(pm)).json()
    assert v["role"] == "pm" and v["clock"]["day"] == 12
    bad = c.post(f"/api/rooms/{rid}/commands", headers=h(mp, "k1"),
                 json={"type": "ticket", "order_id": "x", "sym": "ALTO", "side": "SELL", "qty": 1})
    assert bad.status_code == 422 and bad.json()["code"] == "rejected"
    assert bad.json()["message"] == bad.json()["detail"]
    retry = c.post(f"/api/rooms/{rid}/commands", headers=h(mp, "k1"),
                   json={"type": "ticket", "order_id": "x", "sym": "ALTO", "side": "SELL", "qty": 1})
    assert retry.status_code == 422 and retry.json() == bad.json()
    assert c.get(f"/api/rooms/{rid}/view", headers=h("forged")).json()["code"] == "unauthorized"
    assert c.post(f"/api/rooms/{rid}/commands", headers=h(pm, "k0"), json={}).json()["code"] == "invalid_command"
    assert c.post(f"/api/rooms/{rid}/commands", headers=h(pm, "k2"), json={"type": "ready"}).json()["advanced"] is False
    assert c.post(f"/api/rooms/{rid}/commands", headers=h(mp, "k3"), json={"type": "ready"}).json()["advanced"] is True
    reuse = c.post(f"/api/rooms/{rid}/commands", headers=h(mp, "k3"), json={"type": "research", "topic": "borrow"})
    assert reuse.status_code == 409 and reuse.json()["code"] == "key_reused"
    led = c.get(f"/api/rooms/{rid}/ledger?entity=firm", headers=h(mp)).json()
    assert led["entries"][0]["memo"] == "Management company opening book"
    n = led["next"]
    assert n == len(led["entries"])
    assert c.get(f"/api/rooms/{rid}/ledger?entity=firm&after={n}", headers=h(mp)).json()["entries"] == []
    tail = c.get(f"/api/rooms/{rid}/ledger?entity=firm&after=1", headers=h(mp)).json()
    assert tail["entries"] == led["entries"][1:] and tail["next"] == n
    assert c.get(f"/api/rooms/{rid}/ledger?after=-1", headers=h(mp)).status_code == 422
    full = c.get(f"/api/rooms/{rid}/view", headers=h(pm))
    tag = full.headers["etag"]
    assert full.headers["cache-control"] == "private, no-cache"
    same = c.get(f"/api/rooms/{rid}/view", headers={**h(pm), "If-None-Match": tag})
    assert same.status_code == 304 and same.headers["etag"] == tag and not same.content
    c.post(f"/api/rooms/{rid}/commands", headers=h(pm, "k-etag"), json={"type": "ready"})
    moved = c.get(f"/api/rooms/{rid}/view", headers={**h(pm), "If-None-Match": tag})
    assert moved.status_code == 200 and moved.headers["etag"] != tag
    assert moved.json()["version"] > full.json()["version"]
    assert c.get(f"/api/rooms/{rid}/view", headers={"If-None-Match": tag}).status_code == 401  # auth first


def test_broker_challenge_authenticated_correction_flow(client):
    c = client
    r = c.post("/api/rooms", json={"scenario": "case1-controls", "pm_name": "Ana", "mp_name": "Ben"}).json()
    path = f"/api/rooms/{r['room_id']}"
    headers = {role: {"Authorization": f"Bearer {token}"} for role, token in r["tokens"].items()}
    initial = c.get(path + "/terminal", headers=headers["mp"]).json()
    assert initial["risk"]["controls"]["statement_queue"][0]["revision"] == 1
    assert "duplicate $100" not in str(initial)
    for step in range(4):
        role = "pm" if step % 2 == 0 else "mp"
        response = c.post(path + "/commands", headers={**headers[role], "Idempotency-Key": f"next-{step}"},
                          json={"type": "ready"})
        assert response.status_code == 200
    terminal = c.get(path + "/terminal", headers=headers["mp"]).json()
    assert terminal["risk"]["controls"]["statement_queue"][0]["can_resolve"]
    command = {"type": "resolve_statement", "statement_id": "opening-cash", "revision": 2,
               "version": terminal["version"]}
    denied = c.post(path + "/commands", headers={**headers["pm"], "Idempotency-Key": "wrong-role"}, json=command)
    assert denied.status_code == 422
    accepted = c.post(path + "/commands", headers={**headers["mp"], "Idempotency-Key": "review"}, json=command)
    assert accepted.status_code == 200
    reviewed = c.get(path + "/terminal", headers=headers["mp"]).json()
    assert reviewed["risk"]["controls"]["status"] == "checked"
    assert len(reviewed["risk"]["controls"]["statement_queue"][0]["history"]) == 2
    assert c.get(path + "/verify", headers=headers["mp"]).status_code == 200
