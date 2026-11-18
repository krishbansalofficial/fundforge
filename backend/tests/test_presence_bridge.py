"""Several API workers: a move, leave or nudge on one worker's hub reaches connections on another's."""

import asyncio
import os
import sys

import pytest

from fundforge import presence_bridge
from fundforge.presence import Hub

POS = {"x": 1.0, "z": 2.0, "location": "lounge"}


def drain(conn) -> list[dict]:  # type: ignore[no-untyped-def]
    out = []
    while not conn.queue.empty():
        out.append(conn.queue.get_nowait())
    return out


def test_hubs_relay_moves_leaves_and_nudges_without_echo() -> None:
    a, b = Hub(), Hub()
    sent: list[dict] = []
    a.publish = lambda ev: (sent.append(ev), b.apply_remote(ev))
    b.publish = lambda ev: (sent.append(ev), a.apply_remote(ev))
    pm, mp = a.join("r", "pm"), b.join("r", "mp")
    a.move(pm, POS)
    assert drain(mp) == [{"type": "presence", "role": "pm", **POS}] and drain(pm) == []
    assert b.positions["r"]["pm"] == POS  # a late joiner on b gets it in its welcome
    a.nudge("r", 7)
    assert drain(mp) == [{"type": "version", "version": 7}]
    a.leave(pm)
    assert drain(mp) == [{"type": "left", "role": "pm"}] and "pm" not in b.positions["r"]
    assert len(sent) == 3  # apply_remote never republishes, so nothing loops
    b.apply_remote({"type": "version", "room": "elsewhere", "version": 1})  # nobody watches: no state kept
    assert "elsewhere" not in b.rooms and "elsewhere" not in b.positions


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_bridge_relays_through_postgres_notify() -> None:
    async def scenario() -> None:
        a, b = Hub(), Hub()
        dsn = os.environ["DATABASE_URL"]
        tasks = [asyncio.create_task(presence_bridge.run(dsn, a, worker="a")),
                 asyncio.create_task(presence_bridge.run(dsn, b, worker="b"))]
        try:
            pm, mp = a.join("bridge-room", "pm"), b.join("bridge-room", "mp")
            for _ in range(50):  # both listeners up
                await asyncio.sleep(0.1)
                a.move(pm, POS)
                if not mp.queue.empty():
                    break
            got = await asyncio.wait_for(mp.queue.get(), 5)
            assert got == {"type": "presence", "role": "pm", **POS}
            b.nudge("bridge-room", 3)
            got = None
            while got is None or got.get("type") != "version":  # skip any further presence frames
                got = await asyncio.wait_for(pm.queue.get(), 5)
            assert got == {"type": "version", "version": 3}
        finally:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        assert a.publish is None and b.publish is None  # cancelled bridges uninstall themselves

    if sys.platform == "win32":  # psycopg's async connections need the selector loop on Windows
        asyncio.run(scenario(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(scenario())
