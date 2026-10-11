"""HTTP API. Players poll /view; every mutation goes through POST /commands with an Idempotency-Key."""

import asyncio
import contextlib
import logging
import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from .debrief import replay
from .engine import CommandRejected
from .liquidity import project
from .store import KeyReused, ReplayDivergence, RoomIncompatible, Store
from .terminal import snapshot

log = logging.getLogger("fundforge.clock")


async def clock_loop() -> None:
    """Wall-clock scheduler: logs a tick for every running room whose window is due."""
    while True:
        try:
            for room, version in await asyncio.to_thread(store().due_rooms):
                await asyncio.to_thread(store().tick, room, version)
        except Exception:  # keep the clock alive; a failed tick is retried next loop
            log.exception("clock loop error")
        await asyncio.sleep(0.25)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(clock_loop()) if os.environ.get("FUNDFORGE_CLOCK", "1") == "1" else None
    try:
        yield
    finally:
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        if store.cache_info().currsize:
            await asyncio.to_thread(store().close)
            store.cache_clear()


app = FastAPI(title="FundForge", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Idempotency-Key", "Content-Type"])


CODES = {401: "unauthorized", 404: "not_found", 405: "method_not_allowed", 409: "conflict", 422: "rejected"}


class ApiError(HTTPException):
    """An HTTP error with a stable machine-readable code; clients branch on ``code``, never on wording."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(status, message)
        self.code = code


def _envelope(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    # ``detail`` mirrors ``message`` for clients written before the envelope.
    return JSONResponse(status_code=status, content={"code": code, "message": message, "detail": message},
                        headers=headers)


@app.exception_handler(StarletteHTTPException)
async def http_error(_request: Request, error: StarletteHTTPException) -> JSONResponse:
    code = getattr(error, "code", None) or CODES.get(error.status_code, "error")
    return _envelope(error.status_code, code, str(error.detail), getattr(error, "headers", None))


@app.exception_handler(RoomIncompatible)
async def incompatible_room(_request: Request, error: RoomIncompatible) -> JSONResponse:
    return _envelope(409, "room_incompatible", str(error))


@lru_cache
def store() -> Store:
    s = Store(os.environ.get("DATABASE_URL", "postgresql://fundforge:fundforge@localhost:5432/fundforge"))
    try:
        s.init()
    except Exception:
        s.close()
        raise
    return s


class NewRoom(BaseModel):
    scenario: str = "case1"
    pm_name: str = Field("", max_length=40)
    mp_name: str = Field("", max_length=40)
    solo_role: str | None = Field(None, pattern="^(pm|mp)$")  # play alone; the bot takes the other seat


def seat(room_id: str, authorization: str = Header("")) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return store().auth(room_id, token)
    except PermissionError as e:
        raise HTTPException(401, str(e)) from e


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/rooms", status_code=201)
def create_room(body: NewRoom) -> dict[str, Any]:
    try:
        return store().create_room(body.scenario, body.pm_name, body.mp_name, solo_role=body.solo_role)
    except CommandRejected as e:
        raise HTTPException(422, str(e)) from e


# A room can only become incompatible (new rules/tape) across a server restart; a fresh epoch per
# process makes the first poll after a restart take the full path, which checks compatibility.
EPOCH = secrets.token_hex(4)


def _etag(version: int, running: bool) -> str:
    # Everything in a view is fixed by the room version and clock state; ``next_tick_in`` is measured
    # from when the client received the full view, so a 304 keeps that view and its arrival time.
    return f'"{EPOCH}-v{version}-{int(running)}"'


@app.get("/api/rooms/{room_id}/view", response_model=None)
def view(room_id: str, user: str = Depends(seat),
         if_none_match: str | None = Header(None)) -> dict[str, Any] | Response:
    headers = {"Cache-Control": "private, no-cache"}
    info = store().clock_info(room_id)
    if if_none_match is not None and if_none_match == _etag(info["version"], info["running"]):
        return Response(status_code=304, headers={**headers, "ETag": if_none_match})
    version, s, names = store().session(room_id)
    info = store().clock_info(room_id)
    realtime = {k: v for k, v in info.items() if k != "version"}
    body = {"names": names, **s.view(user), "version": version, "realtime": realtime}
    return JSONResponse(body, headers={**headers, "ETag": _etag(version, info["running"])})


@app.get("/api/rooms/{room_id}/ledger")
def ledger(room_id: str, entity: str = "fund", after: int | None = Query(None, ge=0),
           user: str = Depends(seat)) -> dict[str, Any]:
    """The newest 1,000 entries, or with ``after`` the entries following that many (the previous ``next``)."""
    if entity not in ("fund", "firm"):
        raise HTTPException(422, "entity must be fund or firm")
    _, s, _ = store().session(room_id)
    entries = [x.canonical() for x in s.e.j.entries if x.entity == entity]
    page = entries[-1000:] if after is None else entries[after:after + 1000]
    start = len(entries) - len(page) if after is None else min(after, len(entries))
    return {"entity": entity, "entries": page, "next": start + len(page), "digest": s.e.j.digest()}


@app.get("/api/rooms/{room_id}/terminal")
def terminal(room_id: str, user: str = Depends(seat)) -> dict[str, Any]:
    """Authenticated read-only analytics at one consistent room version."""
    try:
        version, s, _ = store().session(room_id)
    except RoomIncompatible as e:
        raise HTTPException(409, str(e)) from e
    role = s.role_of(user)
    return {**snapshot(s.e, role), "version": version}


class DebriefRequest(BaseModel):
    version: int = Field(ge=0)
    omit_seq: int | None = Field(None, ge=1)


@app.post("/api/rooms/{room_id}/debrief")
def debrief(room_id: str, body: DebriefRequest, user: str = Depends(seat)) -> dict[str, Any]:
    try:
        version, s, _ = store().session(room_id)
        s.role_of(user)
        if body.version != version:
            raise HTTPException(409, "room changed; refresh before replaying")
        return replay(s, body.omit_seq)
    except RoomIncompatible as e:
        raise HTTPException(409, str(e)) from e
    except CommandRejected as e:
        raise HTTPException(422, str(e)) from e


class LiquidityRequest(BaseModel):
    version: int = Field(ge=0)
    long_shock: str = Field("-0.15", pattern=r"^-?\d{1,2}(\.\d{1,6})?$", max_length=12)
    short_shock: str = Field("0.10", pattern=r"^-?\d{1,2}(\.\d{1,6})?$", max_length=12)
    volume_scale: str = Field("1", pattern=r"^\d(\.\d{1,6})?$", max_length=9)
    horizon: int = Field(5, ge=1, le=10)


@app.post("/api/rooms/{room_id}/liquidity")
def liquidity(room_id: str, body: LiquidityRequest, user: str = Depends(seat)) -> dict[str, Any]:
    try:
        version, s, _ = store().session(room_id)
        s.role_of(user)
        if body.version != version:
            raise HTTPException(409, "room changed; refresh before running the liquidity lab")
        return {"version": version, "as_of": {"day": s.e.ev.day, "phase": s.e.ev.phase},
                "comparisons": [project(s.e, body.long_shock, body.short_shock, body.horizon,
                                        body.volume_scale, strategy) for strategy in ("cost", "longs_first")]}
    except RoomIncompatible as e:
        raise HTTPException(409, str(e)) from e
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@app.post("/api/rooms/{room_id}/commands")
def command(room_id: str, body: dict[str, Any], user: str = Depends(seat),
            idempotency_key: str = Header(..., max_length=100)) -> dict[str, Any]:
    if not isinstance(body.get("type"), str):
        raise ApiError(422, "invalid_command", "command type required")
    try:
        return store().apply(room_id, user, idempotency_key, body)
    except RoomIncompatible as e:
        raise ApiError(409, "room_incompatible", str(e)) from e
    except KeyReused as e:
        raise ApiError(409, "key_reused", str(e)) from e
    except CommandRejected as e:
        raise ApiError(422, "rejected", str(e) or "command rejected") from e
    except (KeyError, TypeError, ValueError) as e:
        raise ApiError(422, "invalid_command", str(e) or "invalid command") from e


@app.get("/api/rooms/{room_id}/verify")
def verify(room_id: str, user: str = Depends(seat)) -> dict[str, Any]:
    """Re-derive the whole room from tape + command log and compare with every stored row."""
    try:
        return {"ok": True, **store().verify(room_id)}
    except (ReplayDivergence, RoomIncompatible) as e:
        return {"ok": False, "error": str(e)}
