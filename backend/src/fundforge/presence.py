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

The hub is per process. One API process is the deployment target; several would need a shared broker
(for example Redis pub/sub), which is not built until a deployment needs it.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from dataclasses import dataclass, field
from typing import Any

HELLO_SECONDS = 5.0
MAX_FRAME = 1024  # bytes; a move is about 60
MOVES_PER_SECOND = 10.0
BURST = 20
QUEUE = 64  # outbound frames per connection; a slow reader loses presence frames, never the session
MAX_CONNECTIONS_PER_SEAT = 4  # a few tabs or clients, bounded
WORLD = (0.0, 24.0, 0.0, 23.0)  # x min/max, z min/max, matching game/scripts/world_rules.gd WORLD
LOCATIONS = frozenset({"", "trading", "committee", "risk", "research", "backoffice", "lp", "broker", "street"})
UNAUTHORIZED = 4401  # WebSocket close codes in the private 4000-4999 range
TOO_MANY = 4429


class PresenceError(ValueError):
    pass


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
        self.positions.setdefault(conn.room, {})[conn.role] = pos
        for other in self.rooms.get(conn.room, ()):
            if other.role != conn.role:
                other.send({"type": "presence", "role": conn.role, **pos})

    def leave(self, conn: Conn) -> None:
        conns = self.rooms.get(conn.room, set())
        conns.discard(conn)
        if not any(c.role == conn.role for c in conns):
            self.positions.get(conn.room, {}).pop(conn.role, None)
            for other in conns:
                other.send({"type": "left", "role": conn.role})
        if not conns:  # nothing kept for rooms nobody is watching
            self.rooms.pop(conn.room, None)
            self.positions.pop(conn.room, None)

    def nudge(self, room: str, version: int) -> None:
        for conn in self.rooms.get(room, ()):
            conn.send({"type": "version", "version": version})

    def nudge_threadsafe(self, room: str, version: int) -> None:
        """From a worker thread (sync endpoints run in a threadpool): schedule the nudge on the hub's loop."""
        if self.loop is not None and room in self.rooms:
            self.loop.call_soon_threadsafe(self.nudge, room, version)


hub = Hub()
