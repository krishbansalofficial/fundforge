"""HTTP API. Players poll /view; every mutation goes through POST /commands with an Idempotency-Key."""

import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .engine import CommandRejected
from .store import KeyReused, ReplayDivergence, RoomIncompatible, Store

log = logging.getLogger("fundforge.clock")


async def clock_loop():
    """Wall-clock scheduler: logs a tick for every running room whose window is due."""
    while True:
        try:
            for room, version in await asyncio.to_thread(store().due_rooms):
                await asyncio.to_thread(store().tick, room, version)
        except Exception:  # keep the clock alive; a failed tick is retried next loop
            log.exception("clock loop error")
        await asyncio.sleep(0.25)


@asynccontextmanager
async def lifespan(_app):
    task = asyncio.create_task(clock_loop()) if os.environ.get("FUNDFORGE_CLOCK", "1") == "1" else None
    yield
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="FundForge", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Idempotency-Key", "Content-Type"])


@lru_cache
def store() -> Store:
    s = Store(os.environ.get("DATABASE_URL", "postgresql://fundforge:fundforge@localhost:5432/fundforge"))
    s.init()
    return s


class NewRoom(BaseModel):
    scenario: str = "case1"
    pm_name: str = Field("", max_length=40)
    mp_name: str = Field("", max_length=40)


def seat(room_id: str, authorization: str = Header("")) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return store().auth(room_id, token)
    except PermissionError as e:
        raise HTTPException(401, str(e)) from e


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/rooms", status_code=201)
def create_room(body: NewRoom):
    try:
        return store().create_room(body.scenario, body.pm_name, body.mp_name)
    except CommandRejected as e:
        raise HTTPException(422, str(e)) from e


@app.get("/api/rooms/{room_id}/view")
def view(room_id: str, user: str = Depends(seat)):
    version, s, names = store().session(room_id)
    return {"names": names, **s.view(user), "version": version, "realtime": store().clock_info(room_id)}


@app.get("/api/rooms/{room_id}/ledger")
def ledger(room_id: str, entity: str = "fund", user: str = Depends(seat)):
    if entity not in ("fund", "firm"):
        raise HTTPException(422, "entity must be fund or firm")
    _, s, _ = store().session(room_id)
    return {"entity": entity, "entries": s.ledger(entity, limit=1000), "digest": s.e.j.digest()}


@app.post("/api/rooms/{room_id}/commands")
def command(room_id: str, body: dict, user: str = Depends(seat), idempotency_key: str = Header(..., max_length=100)):
    if not isinstance(body.get("type"), str):
        raise HTTPException(422, "command type required")
    try:
        return store().apply(room_id, user, idempotency_key, body)
    except RoomIncompatible as e:
        raise HTTPException(409, str(e)) from e
    except KeyReused as e:
        raise HTTPException(409, str(e)) from e
    except (CommandRejected, KeyError, TypeError, ValueError) as e:
        raise HTTPException(422, str(e) or "invalid command") from e


@app.get("/api/rooms/{room_id}/verify")
def verify(room_id: str, user: str = Depends(seat)):
    """Re-derive the whole room from tape + command log and compare with every stored row."""
    try:
        return {"ok": True, **store().verify(room_id)}
    except (ReplayDivergence, RoomIncompatible) as e:
        return {"ok": False, "error": str(e)}
