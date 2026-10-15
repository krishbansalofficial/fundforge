"""Transactional outbox: one atomic write with each command, attributed, audience-scoped, append-only.

Skipped without DATABASE_URL. The ml/ suite separately validates these rows against the frozen
JSON schema (ml/contracts/outbox_event.schema.json).
"""

import os

import psycopg
import pytest

from fundforge.engine import CommandRejected
from fundforge.store import Store

DSN = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="needs DATABASE_URL (docker compose up -d db)")
_opened: list[Store] = []


@pytest.fixture(autouse=True, scope="module")
def _close_pools():
    yield
    for s in _opened:
        s.close()


def _store() -> Store:
    st = Store(DSN)
    _opened.append(st)
    st.init()
    return st


def _play_to_end(st, rid, u):
    k = 0
    while True:
        version, s, _ = st.session(rid)
        if s.e.finished():
            return
        k += 1
        st.apply(rid, u["pm"], f"r{k}a", {"type": "ready", "version": version})
        version, _, _ = st.session(rid)
        st.apply(rid, u["mp"], f"r{k}b", {"type": "ready", "version": version})


def test_every_command_has_events_and_journal_entries_match_the_ledger():
    st = _store()
    r = st.create_room("case1", "Ana", "Ben", variant="base")
    rid = r["room_id"]
    u = {role: st.auth(rid, tok) for role, tok in r["tokens"].items()}
    st.apply(rid, u["mp"], "res", {"type": "research", "topic": "borrow"})
    _play_to_end(st, rid, u)
    events = st.outbox(rid)
    version, _, _ = st.session(rid)
    commands = [e for e in events if e["kind"] == "command"]
    assert [e["seq"] for e in commands] == list(range(1, version + 1))
    assert len({e["event_id"] for e in events}) == len(events)
    with psycopg.connect(DSN) as c:
        stored = c.execute("select entry_id from journal_entries where room_id=%s and command_seq>0"
                           " order by command_seq, entry_id", (rid,)).fetchall()
        heads = dict(c.execute("select seq, chain_hash from commands where room_id=%s", (rid,)).fetchall())
    journal = [e for e in events if e["kind"] == "journal_entry"]
    assert sorted(e["payload"]["id"] for e in journal) == sorted(x[0] for x in stored)
    assert all(e["audience"] == "internal" for e in journal)
    assert all(e["chain_head"] == heads[e["seq"]] for e in events)
    # research evidence belongs to the seat that ordered it; the public share notice is separate
    reveal = [e for e in events if e["kind"] == "notice" and e["payload"]["code"] == "research_reveal"]
    assert reveal and all(e["audience"] == "mp" for e in reveal)
    # exactly one outcome, the only event allowed to name the variant
    outcome = [e for e in events if e["kind"] == "outcome"]
    assert len(outcome) == 1 and outcome[0]["payload"]["variant"] == "base"
    assert all("variant" not in str(e["payload"]) for e in events if e["kind"] != "outcome")
    assert st.verify(rid)["version"] == version  # verify() raises on any mismatch


def test_rejected_and_retried_commands_write_no_extra_events():
    st = _store()
    r = st.create_room("case1", "Ana", "Ben", variant="base")
    rid = r["room_id"]
    u = {role: st.auth(rid, tok) for role, tok in r["tokens"].items()}
    st.apply(rid, u["pm"], "k1", {"type": "say", "text": "hello"})
    n = len(st.outbox(rid))
    st.apply(rid, u["pm"], "k1", {"type": "say", "text": "hello"})  # idempotent retry
    with pytest.raises(CommandRejected):
        st.apply(rid, u["pm"], "k2", {"type": "accept_replacement"})  # wrong role: rolled back
    assert len(st.outbox(rid)) == n


def test_outbox_is_append_only():
    st = _store()
    r = st.create_room("case1", "Ana", "Ben", variant="base")
    rid = r["room_id"]
    u = {role: st.auth(rid, tok) for role, tok in r["tokens"].items()}
    st.apply(rid, u["pm"], "k1", {"type": "say", "text": "hello"})
    with psycopg.connect(DSN) as c, pytest.raises(psycopg.errors.RaiseException):
        c.execute("delete from outbox where room_id=%s", (rid,))


def test_solo_room_bot_commands_get_their_own_events():
    st = _store()
    r = st.create_room("case1", "Ana", "", variant="base", solo_role="pm")
    rid = r["room_id"]
    pm = st.auth(rid, r["tokens"]["pm"])
    v, _, _ = st.session(rid)
    st.apply(rid, pm, "r1", {"type": "ready", "version": v})
    events = st.outbox(rid)
    roles = {e["payload"]["role"] for e in events if e["kind"] == "command"}
    assert roles == {"pm", "mp"}
    v2, _, _ = st.session(rid)
    assert [e["seq"] for e in events if e["kind"] == "command"] == list(range(1, v2 + 1))
