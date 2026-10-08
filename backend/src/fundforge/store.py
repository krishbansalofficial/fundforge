"""PostgreSQL authority: an append-only, hash-chained command log per room plus the journal it produced.

State is never stored as mutable rows; it is rebuilt by deterministically replaying the
room's accepted commands against its pinned tape and rules version. Each command runs in
one transaction that locks the room row (serializing the fund), checks the idempotency key,
applies the command to a private copy of the session, and appends the command, its chain
hash, the journal entries and their SQL-checked lines atomically. ``verify`` re-derives
everything from scratch and compares it with what was stored.
"""

import copy
import hashlib
import json
import os
import secrets
import threading
from collections import OrderedDict
from importlib import resources
from pathlib import Path

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from .engine import RULES_VERSION, CommandRejected, Engine
from .governance import CLOCK, Session, canonical
from .tape import load

FIXTURES = Path(os.environ.get("FUNDFORGE_FIXTURES", Path(__file__).resolve().parents[3] / "fixtures"))
SCENARIOS = {"case1": "case1.json"}
CACHE_ROOMS = 256
SECONDS_PER_WINDOW = float(os.environ.get("FUNDFORGE_SECONDS_PER_WINDOW", "8"))


class KeyReused(CommandRejected):
    pass


class RoomIncompatible(RuntimeError):
    """The room was created under rules or a tape this server no longer runs; never silently re-derive it."""


class ReplayDivergence(RuntimeError):
    """Re-deriving the room did not reproduce what was stored."""


def _h(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _tape(scenario: str):
    if scenario not in SCENARIOS:
        raise CommandRejected(f"unknown scenario {scenario!r}")
    return load(FIXTURES / SCENARIOS[scenario])


def chain(prev: str, seq: int, key: str, user: str, command: dict, result, digest_after: str) -> str:
    blob = canonical([prev, seq, key, user, command, result, digest_after])
    return hashlib.sha256(blob.encode()).hexdigest()


GENESIS = "0" * 64


class Store:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = ConnectionPool(dsn, min_size=1, max_size=10, open=True)
        # Cached sessions are only ever read; apply() works on a private deep copy.
        self._cache: OrderedDict[str, tuple[int, Session]] = OrderedDict()
        self._lock = threading.Lock()

    def close(self):
        self.pool.close()

    # ---------- schema ----------
    def init(self):
        with self.pool.connection() as c:
            c.execute("create table if not exists schema_migrations (name text primary key, applied_at timestamptz default now())")
            done = {r[0] for r in c.execute("select name from schema_migrations")}
            for f in sorted(resources.files("fundforge.migrations").iterdir(), key=lambda p: p.name):
                if f.name.endswith(".sql") and f.name not in done:
                    with c.transaction():
                        c.execute("select pg_advisory_xact_lock(4242)")
                        if not c.execute("select 1 from schema_migrations where name=%s", (f.name,)).fetchone():
                            c.execute(f.read_text(encoding="utf-8"))
                            c.execute("insert into schema_migrations (name) values (%s)", (f.name,))

    # ---------- cache ----------
    def _cache_get(self, room: str, version: int) -> Session | None:
        with self._lock:
            hit = self._cache.get(room)
            if hit and hit[0] == version:
                self._cache.move_to_end(room)
                return hit[1]
        return None

    def _cache_put(self, room: str, version: int, s: Session):
        with self._lock:
            hit = self._cache.get(room)
            if hit is None or hit[0] < version:
                self._cache[room] = (version, s)
                self._cache.move_to_end(room)
                while len(self._cache) > CACHE_ROOMS:
                    self._cache.popitem(last=False)

    # ---------- rooms and seats ----------
    def create_room(self, scenario: str, pm_name: str, mp_name: str) -> dict:
        tape = _tape(scenario)
        room = secrets.token_hex(6)
        seats = {r: (secrets.token_hex(8), secrets.token_urlsafe(24)) for r in ("pm", "mp")}
        partners = {r: uid for r, (uid, _) in seats.items()}
        names = {"pm": pm_name.strip()[:40] or "Portfolio manager", "mp": mp_name.strip()[:40] or "Managing partner"}
        with self.pool.connection() as c, c.transaction():
            c.execute("insert into rooms (id, scenario, tape_digest, partners, names, rules_version) values (%s,%s,%s,%s,%s,%s)",
                      (room, scenario, tape.digest, Jsonb(partners), Jsonb(names), RULES_VERSION))
            self._append_journal(c, room, self._fresh(tape, partners).e.j.entries, 0)
            for r, (uid, tok) in seats.items():
                c.execute("insert into seats values (%s,%s,%s,%s)", (_h(tok), room, uid, r))
        return {"room_id": room, "tokens": {r: tok for r, (_, tok) in seats.items()}, "names": names}

    def auth(self, room: str, token: str) -> str:
        with self.pool.connection() as c:
            row = c.execute("select user_id from seats where token_hash=%s and room_id=%s", (_h(token), room)).fetchone()
        if not row:
            raise PermissionError("invalid seat token for this room")
        return row[0]

    # ---------- replay ----------
    @staticmethod
    def _fresh(tape, partners) -> Session:
        e = Engine(tape)
        e.advance()
        return Session(e, partners)

    def _room(self, c, room: str, lock: bool = False):
        row = c.execute("select version, scenario, partners, names, rules_version, tape_digest from rooms where id=%s"
                        + (" for update" if lock else ""), (room,)).fetchone()
        if not row:
            raise KeyError(room)
        version, scenario, partners, names, rules, digest = row
        if rules != RULES_VERSION:
            raise RoomIncompatible(f"room uses rules {rules}; this server runs {RULES_VERSION}")
        tape = _tape(scenario)
        if tape.digest != digest:
            raise RoomIncompatible("room's scenario tape changed since it was created")
        return version, tape, partners, names

    def _replay(self, c, room: str, version: int, tape, partners) -> Session:
        s = self._fresh(tape, partners)
        for uid, key, cmd in c.execute(
                "select user_id, idem_key, command from commands where room_id=%s and seq<=%s order by seq", (room, version)):
            s.handle(uid, key, cmd)
        return s

    def session(self, room: str) -> tuple[int, Session, dict]:
        """A read-only session at a consistent version (callers must not mutate it)."""
        with self.pool.connection() as c, c.transaction():
            c.execute("set transaction isolation level repeatable read")
            version, tape, partners, names = self._room(c, room)
            s = self._cache_get(room, version) or self._replay(c, room, version, tape, partners)
        self._cache_put(room, version, s)
        return version, s, names

    # ---------- commands ----------
    def apply(self, room: str, user: str, key: str, command: dict) -> dict:
        with self.pool.connection() as c, c.transaction():
            version, tape, partners, _ = self._room(c, room, lock=True)
            prior = c.execute("select user_id, command, result from commands where room_id=%s and idem_key=%s",
                              (room, key)).fetchone()
            if prior:
                if (prior[0], prior[1]) != (user, json.loads(json.dumps(command))):
                    raise KeyReused(f"idempotency key {key!r} reused for a different command")
                return prior[2]
            base = self._cache_get(room, version) or self._replay(c, room, version, tape, partners)
            s = copy.deepcopy(base, {id(base.e.tape): base.e.tape})
            n = len(s.e.j.entries)
            result = s.handle(user, key, command)
            result = json.loads(json.dumps(result))  # the exact JSON shape that is stored and replay-compared
            seq = version + 1
            prev = c.execute("select chain_hash from commands where room_id=%s and seq=%s", (room, version)).fetchone()
            digest = s.e.j.digest()
            link = chain(prev[0] if prev and prev[0] else GENESIS, seq, key, user, command, result, digest)
            c.execute("insert into commands (room_id, seq, idem_key, user_id, command, result, journal_digest_after, chain_hash)"
                      " values (%s,%s,%s,%s,%s,%s,%s,%s)",
                      (room, seq, key, user, Jsonb(command), Jsonb(result), digest, link))
            self._append_journal(c, room, s.e.j.entries[n:], seq)
            speed = s.clock["speed"] or 1
            c.execute("update rooms set version=%s, running=%s, speed=%s,"
                      " next_tick_at = now() + make_interval(secs => %s) where id=%s",
                      (seq, s.running(), s.clock["speed"], SECONDS_PER_WINDOW / speed, room))
        self._cache_put(room, seq, s)
        return result

    # ---------- real-time clock ----------
    def due_rooms(self, limit: int = 50) -> list[tuple[str, int]]:
        with self.pool.connection() as c:
            return c.execute("select id, version from rooms where running and next_tick_at <= now()"
                             " order by next_tick_at limit %s", (limit,)).fetchall()

    def tick(self, room: str, version: int) -> dict | None:
        """Log one clock tick; idempotent per version, so duplicate schedulers cannot double-advance."""
        try:
            return self.apply(room, CLOCK, f"tick-{version}", {"type": "tick", "expected_version": version})
        except CommandRejected:
            return None

    def clock_info(self, room: str) -> dict:
        with self.pool.connection() as c:
            row = c.execute("select running, speed, next_tick_at, now() from rooms where id=%s", (room,)).fetchone()
        return {"running": row[0], "speed": row[1], "next_tick_at": row[2].isoformat() if row[2] else None,
                "server_now": row[3].isoformat(), "seconds_per_window": SECONDS_PER_WINDOW}

    @staticmethod
    def _append_journal(c, room, entries, seq):
        with c.cursor() as cur:
            cur.executemany(
                "insert into journal_entries values (%s,%s,%s,%s,%s,%s,%s)",
                [(room, x.entry_id, x.entity, x.date, x.memo, Jsonb(x.canonical()["postings"]), seq) for x in entries])
            cur.executemany(
                "insert into journal_lines (room_id, entry_id, line_no, entity, account, amount) values (%s,%s,%s,%s,%s,%s)",
                [(room, x.entry_id, i, x.entity, p.account, p.amount) for x in entries for i, p in enumerate(x.postings)])

    # ---------- audit ----------
    def verify(self, room: str) -> dict:
        """Re-derive the room from its tape and command log and compare with everything stored."""
        with self.pool.connection() as c, c.transaction():
            c.execute("set transaction isolation level repeatable read")
            version, tape, partners, _ = self._room(c, room)
            s = self._fresh(tape, partners)
            prev = GENESIS
            stored_entries = {r[0]: (r[1], r[2]) for r in c.execute(
                "select entry_id, entity, postings from journal_entries where room_id=%s", (room,))}
            for seq, key, uid, cmd, result, digest, link in c.execute(
                    "select seq, idem_key, user_id, command, result, journal_digest_after, chain_hash"
                    " from commands where room_id=%s and seq<=%s order by seq", (room, version)).fetchall():
                got = json.loads(json.dumps(s.handle(uid, key, cmd)))
                if got != result:
                    raise ReplayDivergence(f"seq {seq}: result {got} != stored {result}")
                if s.e.j.digest() != digest:
                    raise ReplayDivergence(f"seq {seq}: journal digest differs from stored")
                if chain(prev, seq, key, uid, cmd, result, digest) != link:
                    raise ReplayDivergence(f"seq {seq}: chain hash broken")
                prev = link
            replayed = {x.entry_id: (x.entity, x.canonical()["postings"]) for x in s.e.j.entries}
            if replayed != stored_entries:
                raise ReplayDivergence("stored journal entries differ from the replayed journal")
            sql_tb = {(e, a): v for e, a, v in c.execute(
                "select entity, account, balance from trial_balance where room_id=%s and balance <> 0", (room,))}
        py_tb = {(ent, a): v for ent in ("fund", "firm") for a, v in s.e.j.balances(ent).items()}
        if sql_tb != py_tb:
            raise ReplayDivergence("SQL trial balance differs from the engine's balances")
        return {"room": room, "version": version, "journal_digest": s.e.j.digest(), "chain_head": prev,
                "entries": len(replayed), "rules_version": RULES_VERSION, "tape_digest": tape.digest}
