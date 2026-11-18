"""Live partner presence: ephemeral avatar positions and "the room changed" nudges over a WebSocket.

Nothing here is economic state. Positions are cosmetic, never logged, never replayed and never read by
the engine. Research assignments stay ``visit`` commands, checked by the rules, and signing never needs
proximity. A nudge only tells a client to poll ``/view`` now, and polling remains the fallback, so a
lost nudge or a dropped socket changes nothing but latency. Imports are limited to the standard library.

Protocol (JSON text frames):
  client -> {"type": "hello", "token": SEAT_TOKEN}             first frame, within HELLO_SECONDS
  server -> {"type": "welcome", "role": R, "version": N, "partners": {ROLE: POSITION}}
  client -> {"type": "move", "x": X, "z": Z, "location": LOC}  at most MOVES_PER_SECOND, bursts of BURST
  server -> {"type": "presence", "role": R, "x": X, "z": Z, "location": LOC}   to the other connections
  server -> {"type": "left", "role": R}                         that seat's last connection closed
  server -> {"type": "version", "version": N}                   after a command or clock tick changed the room
  server -> {"type": "error", "message": TEXT}                  a malformed frame; the socket stays open

The hub is per process. With several API worker processes, ``presence_bridge`` relays each local move, leave
and nudge through Postgres LISTEN/NOTIFY to the other workers' hubs (``publish`` / ``apply_remote``); with one
process ``publish`` stays None and nothing leaves the process.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

HELLO_SECONDS = 5.0
MAX_FRAME = 1024  # bytes; a move is about 60
MOVES_PER_SECOND = 10.0
BURST = 20
QUEUE = 64  # outbound frames per connection; a slow reader loses presence frames, never the session
MAX_CONNECTIONS_PER_SEAT = 4  # a few tabs or clients, bounded; per worker process, so at most 4 x FUNDFORGE_WORKERS
ROLES = ("pm", "mp")
WORLD = (0.0, 24.0, 0.0, 23.0)  # x min/max, z min/max, matching game/scripts/world_rules.gd WORLD
LOCATIONS = frozenset({"", "trading", "committee", "risk", "research", "backoffice", "lp", "broker", "street"})
UNAUTHORIZED = 4401  # WebSocket close codes in the private 4000-4999 range
TOO_MANY = 4429


class PresenceError(ValueError):
    pass


def parse_remote(event: Any) -> dict[str, Any] | None:
    """A relayed worker event re-validated like a client frame, or None if it is malformed."""
    if not isinstance(event, dict) or not isinstance(event.get("room"), str) or not 0 < len(event["room"]) <= 64:
        return None
    kind = event.get("type")
    try:
        if kind == "presence" and event.get("role") in ROLES and isinstance(event.get("pos"), dict):
            return {"type": kind, "room": event["room"], "role": event["role"],
                    "pos": parse_move(json.dumps({**event["pos"], "type": "move"}))}
        if kind == "left" and event.get("role") in ROLES:
            return {"type": kind, "room": event["room"], "role": event["role"]}
        version = event.get("version")
        if kind == "version" and isinstance(version, int) and not isinstance(version, bool) and version >= 0:
            return {"type": kind, "room": event["room"], "version": version}
    except PresenceError:
        return None
    return None


def parse_move(text: str) -> dict[str, Any]:
    """A validated move frame, or PresenceError. Coordinates are rounded to centimetres."""
    if len(text.encode()) > MAX_FRAME:
        raise PresenceError("frame too large")
    try:
        msg = json.loads(text)
    except json.JSONDecodeError as e:
        raise PresenceError("frames must be JSON") from e
    if not isinstance(msg, dict) or msg.get("type") != "move":
        raise PresenceError("expected a move frame")
    x: Any = msg.get("x")
    z: Any = msg.get("z")
    loc: Any = msg.get("location", "")
    for v in (x, z):
        if isinstance(v, bool) or not isinstance(v, int | float) or not math.isfinite(v):
            raise PresenceError("x and z must be finite numbers")
    if not (WORLD[0] <= x <= WORLD[1] and WORLD[2] <= z <= WORLD[3]):
        raise PresenceError("position is outside the world")
    if loc not in LOCATIONS:
        raise PresenceError("unknown location")
    return {"x": round(float(x), 2), "z": round(float(z), 2), "location": loc}


@dataclass
class Bucket:
    """Token bucket: ``rate`` per second, up to ``burst`` at once."""
    rate: float = MOVES_PER_SECOND
    burst: float = BURST
    tokens: float = BURST
    at: float = field(default_factory=time.monotonic)

    def take(self, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        self.tokens = min(self.burst, self.tokens + (now - self.at) * self.rate)
        self.at = now
        if self.tokens < 1:
            return False
        self.tokens -= 1
        return True


@dataclass(eq=False)
class Conn:
    room: str
    role: str
    queue: asyncio.Queue[dict[str, Any]] = field(default_factory=lambda: asyncio.Queue(QUEUE))
    bucket: Bucket = field(default_factory=Bucket)
    dropped: int = 0

    def send(self, msg: dict[str, Any]) -> None:
        try:
            self.queue.put_nowait(msg)
        except asyncio.QueueFull:
            self.dropped += 1


class Hub:
    """Connections and last positions per room, on one event loop."""

    def __init__(self) -> None:
        self.rooms: dict[str, set[Conn]] = {}
        self.positions: dict[str, dict[str, dict[str, Any]]] = {}
        self.loop: asyncio.AbstractEventLoop | None = None
        self.publish: Callable[[dict[str, Any]], None] | None = None  # set by presence_bridge with workers > 1

    def join(self, room: str, role: str) -> Conn:
        conns = self.rooms.setdefault(room, set())
        if sum(c.role == role for c in conns) >= MAX_CONNECTIONS_PER_SEAT:
            raise PresenceError("too many connections for this seat")
        conn = Conn(room, role)
        conns.add(conn)
        return conn

    def partners(self, conn: Conn) -> dict[str, dict[str, Any]]:
        return {r: p for r, p in self.positions.get(conn.room, {}).items() if r != conn.role}

    def move(self, conn: Conn, pos: dict[str, Any]) -> None:
        self._moved(conn.room, conn.role, pos)
        if self.publish:
            self.publish({"type": "presence", "room": conn.room, "role": conn.role, "pos": pos})

    def _moved(self, room: str, role: str, pos: dict[str, Any]) -> None:
        self.positions.setdefault(room, {})[role] = pos
        for other in self.rooms.get(room, ()):
            if other.role != role:
                other.send({**pos, "type": "presence", "role": role})  # protocol keys last: never overridden

    def leave(self, conn: Conn) -> None:
        conns = self.rooms.get(conn.room, set())
        conns.discard(conn)
        if not any(c.role == conn.role for c in conns):
            self._left(conn.room, conn.role)
            if self.publish:
                self.publish({"type": "left", "room": conn.room, "role": conn.role})
        if not conns:  # nothing kept for rooms nobody is watching
            self.rooms.pop(conn.room, None)
            self.positions.pop(conn.room, None)

    def _left(self, room: str, role: str) -> None:
        self.positions.get(room, {}).pop(role, None)
        for other in self.rooms.get(room, ()):
            if other.role != role:
                other.send({"type": "left", "role": role})

    def nudge(self, room: str, version: int) -> None:
        self._nudged(room, version)
        if self.publish:
            self.publish({"type": "version", "room": room, "version": version})

    def _nudged(self, room: str, version: int) -> None:
        for conn in self.rooms.get(room, ()):
            conn.send({"type": "version", "version": version})

    def apply_remote(self, event: Any) -> None:
        """Another worker's move, leave or nudge: deliver to this process's connections, never republish.

        Remote events are re-validated like client frames; anything malformed is ignored. A remote "left" is
        advisory: a seat that still has a connection on this worker keeps its position here.
        """
        ev = parse_remote(event)
        if ev is None or ev["room"] not in self.rooms:  # invalid, or nobody here watches it: keep no state
            return
        room = ev["room"]
        if ev["type"] == "presence":
            self._moved(room, ev["role"], ev["pos"])
        elif ev["type"] == "left":
            if not any(c.role == ev["role"] for c in self.rooms[room]):
                self._left(room, ev["role"])
        else:
            self._nudged(room, ev["version"])

    def nudge_threadsafe(self, room: str, version: int) -> None:
        """From a worker thread (sync endpoints run in a threadpool): schedule the nudge on the hub's loop."""
        if self.loop is not None and (room in self.rooms or self.publish):
            self.loop.call_soon_threadsafe(self.nudge, room, version)


hub = Hub()
