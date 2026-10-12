import os

import pytest

from fundforge.schemas import RoomView

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
    RoomView.model_validate(v)  # the published contract, including names and realtime
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


def test_abuse_limits_body_size_room_rate_and_ttl(client, monkeypatch):
    import fundforge.api as api

    c = client
    huge = {"type": "ready", "pad": "x" * api.MAX_BODY_BYTES}
    big = c.post("/api/rooms/any/commands", json=huge)
    assert big.status_code == 413 and big.json()["code"] == "body_too_large"

    def chunks():  # no Content-Length: the streamed byte count still trips the cap
        yield b'{"pad": "'
        for _ in range(api.MAX_BODY_BYTES // 1024 + 1):
            yield b"x" * 1024
        yield b'"}'
    streamed = c.post("/api/rooms", content=chunks(), headers={"Content-Type": "application/json"})
    assert streamed.status_code == 413

    monkeypatch.setattr(api, "room_creations", api.RateLimit(2))
    made = [c.post("/api/rooms", json={"pm_name": "A", "mp_name": "B"}) for _ in range(3)]
    assert [r.status_code for r in made] == [201, 201, 429] and made[2].json()["code"] == "rate_limited"

    rid, pm = made[0].json()["room_id"], made[0].json()["tokens"]["pm"]
    h = {"Authorization": f"Bearer {pm}", "Idempotency-Key": "late"}
    monkeypatch.setattr(api.store(), "ttl_hours", 0)
    gone = c.post(f"/api/rooms/{rid}/commands", headers=h, json={"type": "ready"})
    assert gone.status_code == 410 and gone.json()["code"] == "room_expired"
    assert c.get(f"/api/rooms/{rid}/view", headers=h).status_code == 200  # still readable
    assert c.get(f"/api/rooms/{rid}/verify", headers=h).json()["ok"] is True
    assert rid not in {r for r, _ in api.store().due_rooms(limit=10_000)}


def test_rate_limit_window_slides_and_forgets_idle_clients():
    from fundforge.api import RateLimit

    rl = RateLimit(2, window=10)
    assert rl.allow("a", 0) and rl.allow("a", 1) and not rl.allow("a", 2)
    assert rl.allow("b", 2)  # per address
    assert rl.allow("a", 10.5)  # the first hit left the window
    assert not rl.allow("a", 10.6)
    rl.allow("c", 100)
    assert set(rl._hits) == {"c"}


def test_metrics_and_json_request_logs(client, caplog):
    import json
    import logging

    from fundforge.observability import JsonFormatter

    c = client
    r = c.post("/api/rooms", json={"pm_name": "A", "mp_name": "B"}).json()
    rid, pm = r["room_id"], r["tokens"]["pm"]
    h = {"Authorization": f"Bearer {pm}", "X-Request-ID": "trace-123"}
    with caplog.at_level(logging.INFO, logger="fundforge"):
        ok = c.post(f"/api/rooms/{rid}/commands", headers={**h, "Idempotency-Key": "m1"}, json={"type": "ready"})
        c.post(f"/api/rooms/{rid}/commands", headers={**h, "Idempotency-Key": "m2"}, json={"type": "no_such_thing"})
    assert ok.headers["x-request-id"] == "trace-123"
    assert c.get("/api/health", headers={"X-Request-ID": "bad id!"}).headers["x-request-id"] != "bad id!"
    fmt = JsonFormatter()
    lines = [json.loads(fmt.format(rec)) for rec in caplog.records]
    applied = [x for x in lines if x["msg"] == "command applied"]
    assert applied == [{**applied[0], "room": rid, "seq": 1, "command": "ready", "request_id": "trace-123"}]
    hits = [x for x in lines if x["msg"] == "request" and x["room"] == rid]
    assert [x["status"] for x in hits] == [200, 422] and all(x["request_id"] == "trace-123" for x in hits)
    assert pm not in json.dumps(lines)  # seat tokens never reach the logs

    text = c.get("/metrics").text
    assert 'fundforge_command_seconds_count{type="ready"}' in text
    assert "no_such_thing" not in text  # client-chosen types never become labels: refused before the store
    assert 'fundforge_rejections_total{code="invalid_command"}' in text
    assert "fundforge_replay_seconds_count" in text


def test_ready_requires_a_migrated_reachable_database(client, monkeypatch):
    from fundforge import api

    assert client.get("/api/ready").json() == {"ok": True}

    def down(*_args, **_kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(api.store().pool, "connection", down)
    r = client.get("/api/ready")
    assert r.status_code == 503 and r.json()["code"] == "unavailable"
    assert client.get("/api/health").json() == {"ok": True}  # liveness does not touch the database


def test_openapi_publishes_the_view_ledger_and_room_contracts(client):
    spec = client.get("/openapi.json").json()
    paths, schemas = spec["paths"], spec["components"]["schemas"]
    ref = lambda path, method="get", status="200": (  # noqa: E731
        paths[path][method]["responses"][status]["content"]["application/json"]["schema"]["$ref"])
    assert ref("/api/rooms/{room_id}/view").endswith("/RoomView")
    assert ref("/api/rooms/{room_id}/ledger").endswith("/LedgerPage")
    assert ref("/api/rooms", "post", "201").endswith("/NewRoomResponse")
    assert schemas["RoomView"]["additionalProperties"] is False and "realtime" in schemas["RoomView"]["required"]


def test_malformed_commands_are_refused_before_the_engine(client):
    c = client
    r = c.post("/api/rooms", json={"pm_name": "Ana", "mp_name": "Ben"}).json()
    rid, pm, mp = r["room_id"], r["tokens"]["pm"], r["tokens"]["mp"]
    h = lambda t, k: {"Authorization": f"Bearer {t}", "Idempotency-Key": k}  # noqa: E731
    path = f"/api/rooms/{rid}/commands"
    # Each of these used to be a 500, or (the "1e" limit) an accepted package bound to an unusable price.
    for token, cmd in [(mp, {"type": "set_reserve", "amount": "lots"}),
                       (pm, {"type": "ticket", "order_id": "x", "sym": "ALTO", "side": "BUY", "qty": 10,
                             "limit": "abc"}),
                       (pm, {"type": "propose", "package_id": "p", "orders": [
                           {"order_id": "o", "sym": "ALTO", "side": "BUY", "qty": 10, "limit": "1e"}]}),
                       (pm, {"type": "say", "text": {"a": 1}}), (pm, {"type": "tick", "expected_version": 0}),
                       (pm, {"type": "no_such_thing"})]:
        res = c.post(path, headers=h(token, "bad-" + cmd["type"]), json=cmd)
        assert res.status_code == 422 and res.json()["code"] == "invalid_command", (cmd, res.json())
        assert isinstance(res.json()["message"], str) and isinstance(res.json()["detail"], str)
    messages = {cmd: c.post(path, headers=h(pm, "msg-" + cmd), json=body).json()["message"] for cmd, body in [
        ("ticket", {"type": "ticket", "order_id": "x", "sym": "ALTO", "side": "BUY", "qty": 10, "limit": "9.5.1"}),
        ("propose", {"type": "propose", "package_id": "p", "orders": [
            {"order_id": "o", "sym": "ALTO", "side": "BUY", "qty": 10, "limit": "1e"}]}),
        ("tick", {"type": "tick", "expected_version": 0}), ("none", {"qty": 1})]}
    decimal = 'must be a plain decimal number sent as a string, such as "95.25"'
    assert messages == {"ticket": f"limit: {decimal}", "propose": f"orders.0.limit: {decimal}",
                        "tick": "unknown command type 'tick'", "none": "command type required"}
    assert c.post(path, headers={"Idempotency-Key": "k"}, json={"type": "no_such_thing"}).status_code == 401
    assert c.get(f"/api/rooms/{rid}/view", headers={"Authorization": f"Bearer {pm}"}).json()["version"] == 0
    # A Godot client's whole floats are the same command as a web client's integers.
    cover = {"order_id": "c", "sym": "BRIN", "side": "COVER", "qty": 1250.0}
    p = c.post(path, headers=h(pm, "godot"), json={"type": "propose", "package_id": "g", "orders": [cover]}).json()
    again = {**cover, "qty": 1250}
    assert c.post(path, headers=h(pm, "godot"), json={"type": "propose", "package_id": "g",
                                                       "orders": [again]}).json() == p  # same key, same command
    assert c.get(f"/api/rooms/{rid}/ledger?after=-1", headers=h(pm, "x")).json()["code"] == "invalid_request"
