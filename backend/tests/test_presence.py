"""Live presence: bounded, authenticated, and never part of the economics."""

import asyncio
import json
import os
import threading

import pytest
from starlette.websockets import WebSocketDisconnect

from fundforge import presence
from fundforge.presence import Bucket, Hub, PresenceError, parse_move


def test_move_frames_are_validated_and_rounded():
    assert parse_move('{"type": "move", "x": 3.14159, "z": 7, "location": "trading"}') == {
        "x": 3.14, "z": 7.0, "location": "trading"}
    assert parse_move('{"type": "move", "x": 0, "z": 23}')["location"] == ""
    for bad in ['nope', '[]', '{"type": "hello"}', '{"type": "move", "x": NaN, "z": 1}',
                '{"type": "move", "x": Infinity, "z": 1}', '{"type": "move", "x": true, "z": 1}',
                '{"type": "move", "x": "1", "z": 1}', '{"type": "move", "x": -0.1, "z": 1}',
                '{"type": "move", "x": 1, "z": 23.5}', '{"type": "move", "x": 1, "z": 1, "location": "vault"}',
                '{"type": "move", "x": 1, "z": 1, "pad": "' + "x" * 2000 + '"}']:
        with pytest.raises(PresenceError):
            parse_move(bad)


def test_bucket_allows_a_burst_then_the_steady_rate():
    b = Bucket(rate=10, burst=3, tokens=3, at=0.0)
    assert [b.take(0.0) for _ in range(4)] == [True, True, True, False]
    assert b.take(0.05) is False and b.take(0.1) is True  # one token per 0.1 s
    assert [b.take(10.0) for _ in range(4)] == [True, True, True, False]  # never more than the burst


def test_hub_relays_to_the_other_seat_and_forgets_empty_rooms():
    async def run():
        hub = Hub()
        pm, mp = hub.join("r", "pm"), hub.join("r", "mp")
        hub.move(pm, {"x": 1.0, "z": 2.0, "location": "risk"})
        assert pm.queue.empty() and mp.queue.get_nowait() == {"type": "presence", "role": "pm", "x": 1.0,
                                                               "z": 2.0, "location": "risk"}
        assert hub.partners(mp) == {"pm": {"x": 1.0, "z": 2.0, "location": "risk"}} and hub.partners(pm) == {}
        second = hub.join("r", "pm")  # a second tab: leaving one keeps the seat present
        hub.leave(pm)
        assert mp.queue.empty() and "pm" in hub.positions["r"]
        hub.leave(second)
        assert mp.queue.get_nowait() == {"type": "left", "role": "pm"} and "pm" not in hub.positions["r"]
        hub.nudge("r", 7)
        assert mp.queue.get_nowait() == {"type": "version", "version": 7}
        hub.leave(mp)
        assert hub.rooms == {} and hub.positions == {}
        for _ in range(presence.MAX_CONNECTIONS_PER_SEAT):
            hub.join("q", "mp")
        with pytest.raises(PresenceError):
            hub.join("q", "mp")
        slow = hub.join("q", "pm")
        for i in range(presence.QUEUE + 5):
            hub.nudge("q", i)
        assert slow.queue.qsize() == presence.QUEUE and slow.dropped == 5  # bounded, never blocking

    asyncio.run(run())


needs_db = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient

    from fundforge.api import app

    monkeypatch.setenv("FUNDFORGE_CLOCK", "0")
    with TestClient(app) as client:
        yield client
    assert presence.hub.rooms == {}  # every socket cleaned up


def room(client):
    r = client.post("/api/rooms", json={"pm_name": "Ana", "mp_name": "Ben"}).json()
    return r["room_id"], r["tokens"]["pm"], r["tokens"]["mp"]


def recv(ws, seconds=5.0):
    """``ws.receive_json()`` that fails instead of hanging when an expected frame never comes."""
    box = {}

    def run():
        try:
            box["value"] = ws.receive_json()
        except BaseException as e:  # re-raised in the test thread
            box["error"] = e

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        pytest.fail(f"no frame within {seconds} s")
    if "error" in box:
        raise box["error"]
    return box["value"]


class Socket:
    """An open presence socket that the ``sockets`` fixture closes even when the test fails midway."""

    def __init__(self, client, rid, token):
        self._cm = client.websocket_connect(f"/api/rooms/{rid}/presence")
        self.ws = self._cm.__enter__()
        self.open = True
        self.ws.send_json({"type": "hello", "token": token})
        self.hello = recv(self.ws)

    def close(self):
        if self.open:
            self.open = False
            self._cm.__exit__(None, None, None)


@pytest.fixture
def sockets(client):
    opened = []

    def connect(rid, token):
        opened.append(Socket(client, rid, token))
        return opened[-1]

    yield connect
    for s in reversed(opened):
        s.close()


@needs_db
def test_partners_see_each_other_move_and_commands_nudge_both(client, sockets):
    rid, pm, mp = room(client)
    sa, sb = sockets(rid, pm), sockets(rid, mp)
    a, b = sa.ws, sb.ws
    assert sa.hello == {"type": "welcome", "role": "pm", "version": 0, "partners": {}}
    assert sb.hello["role"] == "mp"
    a.send_json({"type": "move", "x": 5.5, "z": 4.25, "location": "trading"})
    assert recv(b) == {"type": "presence", "role": "pm", "x": 5.5, "z": 4.25, "location": "trading"}
    a.send_json({"type": "move", "x": 99, "z": 1})  # malformed: reported, socket stays open
    assert recv(a) == {"type": "error", "message": "position is outside the world"}
    late = sockets(rid, mp)  # a late joiner learns where the partner already is
    assert late.hello["partners"] == {"pm": {"x": 5.5, "z": 4.25, "location": "trading"}}
    late.close()
    headers = {"Authorization": f"Bearer {mp}", "Idempotency-Key": "r1"}
    assert client.post(f"/api/rooms/{rid}/commands", headers=headers, json={"type": "ready", "version": 0}).is_success
    assert recv(a) == {"type": "version", "version": 1} == recv(b)
    sa.close()
    assert recv(b) == {"type": "left", "role": "pm"}


@needs_db
def test_presence_traffic_never_changes_the_books(client, sockets):
    rid, pm, mp = room(client)
    auth = {"Authorization": f"Bearer {pm}"}
    before = client.get(f"/api/rooms/{rid}/verify", headers=auth).json()
    a, b = sockets(rid, pm).ws, sockets(rid, mp).ws
    for i in range(200):
        a.send_json({"type": "move", "x": i % 24, "z": (i * 7) % 23, "location": "risk"})
    assert recv(b)["type"] == "presence"  # traffic arrived (the bucket passes a burst and drops the excess)
    after = client.get(f"/api/rooms/{rid}/verify", headers=auth).json()
    assert before["ok"] and after["ok"] and before["version"] == after["version"] == 0
    assert (after["journal_digest"], after["chain_head"]) == (before["journal_digest"], before["chain_head"])


@needs_db
def test_presence_requires_a_seat_token_promptly(client, monkeypatch):
    rid, pm, _ = room(client)
    other, _, _ = room(client)
    for hello in [{"type": "hello", "token": "forged"}, {"type": "hello", "token": pm, "room": other},
                  {"type": "hello"}, {"type": "move", "x": 1, "z": 1}, "not json"]:
        target = other if hello == {"type": "hello", "token": pm, "room": other} else rid
        with client.websocket_connect(f"/api/rooms/{target}/presence") as ws:
            ws.send_text(hello if isinstance(hello, str) else json.dumps(hello))
            with pytest.raises(WebSocketDisconnect) as closed:
                recv(ws)
            assert closed.value.code == presence.UNAUTHORIZED
    monkeypatch.setattr(presence, "HELLO_SECONDS", 0.2)
    with client.websocket_connect(f"/api/rooms/{rid}/presence") as ws, pytest.raises(WebSocketDisconnect) as closed:
        recv(ws)  # said nothing
    assert closed.value.code == presence.UNAUTHORIZED


def test_server_bounds_match_the_game_client():
    """presence.WORLD/LOCATIONS duplicate game/scripts/world_rules.gd; drift would drop real moves."""
    import re
    from pathlib import Path

    gd = (Path(__file__).parents[2] / "game" / "scripts" / "world_rules.gd").read_text(encoding="utf-8")
    x, z, w, h = map(int, re.search(r"const WORLD := Rect2i\((\d+), (\d+), (\d+), (\d+)\)", gd).groups())
    assert (float(x), float(x + w), float(z), float(z + h)) == presence.WORLD
    block = gd[gd.index("const LOCATIONS := {"):gd.index("\n}", gd.index("const LOCATIONS := {"))]
    assert set(re.findall(r'^\t"(\w+)": \{', block, re.M)) | {""} == presence.LOCATIONS
