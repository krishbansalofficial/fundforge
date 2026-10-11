"""HTTP API. Players poll /view; every mutation goes through POST /commands with an Idempotency-Key."""

import asyncio
import contextlib
import logging
import os
import re
import secrets
import threading
import time
import uuid
from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from .debrief import replay
from .engine import CommandRejected
from .liquidity import project
from .observability import REJECTIONS, JsonFormatter, context, request_id
from .schemas import LedgerPage, NewRoomResponse, RoomView
from .store import KeyReused, ReplayDivergence, RoomExpired, RoomIncompatible, Store
from .terminal import snapshot

log = logging.getLogger("fundforge.clock")
access = logging.getLogger("fundforge.http")
REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")


def configure_logging() -> None:
    """JSON lines on stderr for every ``fundforge.*`` logger, unless FUNDFORGE_JSON_LOGS=0."""
    root = logging.getLogger("fundforge")
    if os.environ.get("FUNDFORGE_JSON_LOGS", "1") == "1" and not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)
        root.setLevel(logging.INFO)
        root.propagate = False


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
    configure_logging()
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


MAX_BODY_BYTES = int(os.environ.get("FUNDFORGE_MAX_BODY_BYTES", str(64 * 1024)))
ROOMS_PER_IP = int(os.environ.get("FUNDFORGE_ROOMS_PER_IP", "20"))
ROOM_WINDOW_SECONDS = 3600.0


class BodyLimit:
    """ASGI middleware: refuse request bodies over ``limit`` bytes, declared or streamed (chunked).

    The body is read up to the limit before the app runs (at most ``limit`` bytes are held), then
    replayed; FastAPI would turn an error raised mid-parse into a generic 400.
    """

    def __init__(self, app: Any, limit: int):
        self.app, self.limit = app, limit

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        def too_large() -> JSONResponse:
            return _envelope(413, "body_too_large", f"request body over {self.limit} bytes")

        declared = dict(scope.get("headers", [])).get(b"content-length")
        if declared is not None and (not declared.isdigit() or int(declared) > self.limit):
            await too_large()(scope, receive, send)
            return
        messages, seen = [], 0
        while True:
            message = await receive()
            messages.append(message)
            seen += len(message.get("body", b""))
            if seen > self.limit:
                await too_large()(scope, receive, send)
                return
            if message["type"] != "http.request" or not message.get("more_body"):
                break

        async def replay() -> Any:
            return messages.pop(0) if messages else await receive()

        await self.app(scope, replay, send)


class RateLimit:
    """Sliding one-hour window of room creations per client address (one process, in memory)."""

    def __init__(self, per_window: int, window: float = ROOM_WINDOW_SECONDS):
        self.per_window, self.window = per_window, window
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, client: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            for ip in [ip for ip, q in self._hits.items() if not q or q[-1] <= now - self.window]:
                del self._hits[ip]  # forget idle clients so the table stays bounded by recent traffic
            q = self._hits.setdefault(client, deque())
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.per_window:
                return False
            q.append(now)
            return True


room_creations = RateLimit(ROOMS_PER_IP)

app = FastAPI(title="FundForge", version="0.1.0", lifespan=lifespan)
app.add_middleware(BodyLimit, limit=MAX_BODY_BYTES)


@app.middleware("http")
async def request_log(request: Request, call_next: Any) -> Response:
    """Tag the request (and every log line it causes) with an id, echo it back and log one access line."""
    given = request.headers.get("x-request-id", "")
    token = request_id.set(given if REQUEST_ID.fullmatch(given) else uuid.uuid4().hex)
    start = time.perf_counter()
    status = 500
    try:
        response: Response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id.get()
        return response
    finally:  # path only: seat tokens travel in headers, never in the logged line
        parts = request.url.path.split("/")
        room = parts[3] if len(parts) > 3 and parts[1:3] == ["api", "rooms"] else None
        access.info("request", extra=context(method=request.method, path=request.url.path, status=status,
                                             ms=round((time.perf_counter() - start) * 1000, 2), room=room))
        request_id.reset(token)
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Idempotency-Key", "Content-Type"])


CODES = {401: "unauthorized", 404: "not_found", 405: "method_not_allowed", 409: "conflict", 410: "room_expired",
         413: "body_too_large", 422: "rejected", 429: "rate_limited", 503: "unavailable"}


class ApiError(HTTPException):
    """An HTTP error with a stable machine-readable code; clients branch on ``code``, never on wording."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(status, message)
        self.code = code


def _envelope(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    REJECTIONS.labels(code=code).inc()
    # ``detail`` mirrors ``message`` for clients written before the envelope.
    return JSONResponse(status_code=status, content={"code": code, "message": message, "detail": message},
                        headers=headers)


@app.exception_handler(StarletteHTTPException)
async def http_error(_request: Request, error: StarletteHTTPException) -> JSONResponse:
    code = getattr(error, "code", None) or CODES.get(error.status_code, "error")
    return _envelope(error.status_code, code, str(error.detail), getattr(error, "headers", None))


@app.exception_handler(RoomExpired)
async def expired_room(_request: Request, error: RoomExpired) -> JSONResponse:
    return _envelope(410, "room_expired", str(error))


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


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Prometheus scrape target. Operational counts only; keep it off the public proxy."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/ready")
def ready() -> dict[str, bool]:
    """Readiness: the schema is migrated and the database answers. Deploy healthchecks gate on this."""
    try:
        with store().pool.connection(timeout=5) as c:
            c.execute("select 1 from schema_migrations limit 1")
    except Exception as e:
        raise HTTPException(503, "database not ready") from e
    return {"ok": True}


@app.post("/api/rooms", status_code=201, response_model=NewRoomResponse)
def create_room(body: NewRoom, request: Request) -> dict[str, Any]:
    if not room_creations.allow(request.client.host if request.client else "unknown"):
        raise ApiError(429, "rate_limited", f"at most {room_creations.per_window} new rooms per hour from one address")
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


@app.get("/api/rooms/{room_id}/view", response_model=None,
         responses={200: {"model": RoomView}, 304: {"description": "Unchanged since If-None-Match"}})
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


@app.get("/api/rooms/{room_id}/ledger", response_model=LedgerPage)
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
