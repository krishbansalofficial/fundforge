"""PostgreSQL authority: an append-only command log per room plus the journal it produced.

State is never stored as mutable rows; it is rebuilt by deterministically replaying the
room's accepted commands against its versioned tape. Each command runs in one
transaction that locks the room row (serializing the fund), checks the idempotency key,
applies the command, and appends the command + new journal entries atomically.
"""

import hashlib
import json
import os
import secrets
import threading
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from .engine import CommandRejected, Engine
from .governance import Session
from .tape import load

FIXTURES = Path(os.environ.get("FUNDFORGE_FIXTURES", Path(__file__).resolve().parents[3] / "fixtures"))
SCENARIOS = {"case1": "case1.json"}

SCHEMA = """
create table if not exists rooms (
  id text primary key,
  scenario text not null,
  tape_digest text not null,
  partners jsonb not null,
  names jsonb not null,
  version int not null default 0,
  created_at timestamptz not null default now()
);
create table if not exists seats (
  token_hash text primary key,
  room_id text not null references rooms(id),
  user_id text not null,
  role text not null
);
create table if not exists commands (
  room_id text not null references rooms(id),
  seq int not null,
  idem_key text not null,
  user_id text not null,
  command jsonb not null,
  result jsonb not null,
  created_at timestamptz not null default now(),
  primary key (room_id, seq),
  unique (room_id, idem_key)
);
create table if not exists journal_entries (
  room_id text not null references rooms(id),
  entry_id text not null,
  entity text not null,
  date date not null,
  memo text not null,
  postings jsonb not null,
  command_seq int not null,
  primary key (room_id, entry_id)
);
create or replace function forbid_change() returns trigger language plpgsql as $$
begin raise exception 'append-only table %', tg_table_name; end $$;
drop trigger if exists commands_append_only on commands;
create trigger commands_append_only before update or delete on commands
  for each row execute function forbid_change();
drop trigger if exists journal_append_only on journal_entries;
create trigger journal_append_only before update or delete on journal_entries
  for each row execute function forbid_change();
"""


class KeyReused(CommandRejected):
    pass


def _h(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _tape(scenario: str):
    if scenario not in SCENARIOS:
        raise CommandRejected(f"unknown scenario {scenario!r}")
    return load(FIXTURES / SCENARIOS[scenario])


class Store:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._cache: dict[str, tuple[int, Session]] = {}  # ponytail: per-process replay cache; DB stays authoritative
        self._lock = threading.Lock()

    def connect(self):
        return psycopg.connect(self.dsn)

    def init(self):
        with self.connect() as c:
            c.execute(SCHEMA)

    def create_room(self, scenario: str, pm_name: str, mp_name: str) -> dict:
        tape = _tape(scenario)
        room = secrets.token_hex(6)
        seats = {r: (secrets.token_hex(8), secrets.token_urlsafe(24)) for r in ("pm", "mp")}
        partners = {r: uid for r, (uid, _) in seats.items()}
        names = {"pm": pm_name.strip()[:40] or "Portfolio manager", "mp": mp_name.strip()[:40] or "Managing partner"}
        with self.connect() as c, c.transaction():
            c.execute("insert into rooms (id, scenario, tape_digest, partners, names) values (%s,%s,%s,%s,%s)",
                      (room, scenario, tape.digest, Jsonb(partners), Jsonb(names)))
            self._append_journal(c, room, self._fresh(tape, partners).e.j.entries, 0)
            for r, (uid, tok) in seats.items():
                c.execute("insert into seats values (%s,%s,%s,%s)", (_h(tok), room, uid, r))
        return {"room_id": room, "tokens": {r: tok for r, (_, tok) in seats.items()}, "names": names}

    def auth(self, room: str, token: str) -> str:
        with self.connect() as c:
            row = c.execute("select user_id from seats where token_hash=%s and room_id=%s", (_h(token), room)).fetchone()
        if not row:
            raise PermissionError("invalid seat token for this room")
        return row[0]

    def names(self, room: str) -> dict:
        with self.connect() as c:
            return c.execute("select names from rooms where id=%s", (room,)).fetchone()[0]

    @staticmethod
    def _fresh(tape, partners) -> Session:
        e = Engine(tape)
        e.advance()
        return Session(e, partners)

    def _replay(self, c, room: str, version: int, scenario: str, partners: dict) -> Session:
        with self._lock:
            hit = self._cache.get(room)
        if hit and hit[0] == version:
            return hit[1]
        s = self._fresh(_tape(scenario), partners)
        for uid, key, cmd in c.execute(
                "select user_id, idem_key, command from commands where room_id=%s order by seq", (room,)):
            s.handle(uid, key, cmd)
        return s

    def session(self, room: str) -> tuple[int, Session]:
        with self.connect() as c:
            row = c.execute("select version, scenario, partners from rooms where id=%s", (room,)).fetchone()
            if not row:
                raise KeyError(room)
            s = self._replay(c, room, *row)
        with self._lock:
            self._cache[room] = (row[0], s)
        return row[0], s

    def apply(self, room: str, user: str, key: str, command: dict) -> dict:
        try:
            with self.connect() as c, c.transaction():
                version, scenario, partners = c.execute(
                    "select version, scenario, partners from rooms where id=%s for update", (room,)).fetchone()
                prior = c.execute("select user_id, command, result from commands where room_id=%s and idem_key=%s",
                                  (room, key)).fetchone()
                if prior:
                    if (prior[0], prior[1]) != (user, json.loads(json.dumps(command))):
                        raise KeyReused(f"idempotency key {key!r} reused for a different command")
                    return prior[2]
                s = self._replay(c, room, version, scenario, partners)
                with self._lock:
                    self._cache.pop(room, None)  # the session is about to mutate
                n = len(s.e.j.entries)
                result = s.handle(user, key, command)
                seq = version + 1
                c.execute("insert into commands (room_id, seq, idem_key, user_id, command, result) values (%s,%s,%s,%s,%s,%s)",
                          (room, seq, key, user, Jsonb(command), Jsonb(result)))
                self._append_journal(c, room, s.e.j.entries[n:], seq)
                c.execute("update rooms set version=%s where id=%s", (seq, room))
            with self._lock:
                self._cache[room] = (seq, s)
            return result
        except Exception:
            with self._lock:
                self._cache.pop(room, None)
            raise

    @staticmethod
    def _append_journal(c, room, entries, seq):
        with c.cursor() as cur:
            cur.executemany(
                "insert into journal_entries values (%s,%s,%s,%s,%s,%s,%s)",
                [(room, x.entry_id, x.entity, x.date, x.memo, Jsonb(x.canonical()["postings"]), seq) for x in entries])
