"""Relays presence moves, leaves and version nudges between API worker processes via Postgres LISTEN/NOTIFY.

Only started when FUNDFORGE_WORKERS > 1 (B3 showed one process is the limit near 300 view requests/s). Postgres
is already the authority, so this needs no new service. Messages stay ephemeral: a lost NOTIFY costs latency
only, because clients still poll /view. Each payload carries the sending worker's id so a worker ignores its own.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import uuid
from typing import Any

import psycopg

from .presence import Hub

CHANNEL = "fundforge_presence"
WORKER = uuid.uuid4().hex
QUEUE = 10_000  # presence is cosmetic: drop on overflow rather than grow without bound
log = logging.getLogger(__name__)


async def run(dsn: str, hub: Hub, *, worker: str = WORKER, retry_seconds: float = 2.0) -> None:
    """Install ``hub.publish`` and pump NOTIFY both ways until cancelled; reconnects after a database error."""
    out: asyncio.Queue[dict[str, Any]] = asyncio.Queue(QUEUE)

    def publish(event: dict[str, Any]) -> None:  # called on the hub's event loop
        with contextlib.suppress(asyncio.QueueFull):
            out.put_nowait(event)

    hub.publish = publish
    try:
        while True:
            try:
                await _pump(dsn, hub, out, worker)
            except (psycopg.Error, OSError):
                log.exception("presence bridge lost its database connection; retrying")
                await asyncio.sleep(retry_seconds)
    finally:
        hub.publish = None


async def _pump(dsn: str, hub: Hub, out: asyncio.Queue[dict[str, Any]], worker: str) -> None:
    async with await psycopg.AsyncConnection.connect(dsn, autocommit=True) as listen, \
            await psycopg.AsyncConnection.connect(dsn, autocommit=True) as talk:
        await listen.execute(f"LISTEN {CHANNEL}")

        async def send() -> None:
            while True:
                event = await out.get()
                await talk.execute("select pg_notify(%s, %s)", (CHANNEL, json.dumps({"w": worker, **event})))

        sender = asyncio.create_task(send())
        try:
            async for note in listen.notifies():
                try:  # one bad payload must not stop the bridge; apply_remote re-validates the event itself
                    msg = json.loads(note.payload)
                    if isinstance(msg, dict) and msg.pop("w", None) != worker:
                        hub.apply_remote(msg)
                except (ValueError, TypeError):
                    log.warning("presence bridge ignored a malformed notification")
        finally:
            sender.cancel()
