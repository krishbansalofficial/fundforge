"""Real PostgreSQL concurrency: separate connections race on one room. Skipped without DATABASE_URL."""

import os
import threading

import psycopg
import pytest

from fundforge.engine import CommandRejected
from fundforge.store import Store

DSN = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="needs DATABASE_URL (docker compose up -d db)")


@pytest.fixture
def room():
    st = Store(DSN)
    st.init()
    r = st.create_room("case1", "Ana", "Ben")
    seats = {role: st.auth(r["room_id"], tok) for role, tok in r["tokens"].items()}
    return st, r["room_id"], seats


def race(fns):
    out, barrier = [None] * len(fns), threading.Barrier(len(fns))

    def go(i, f):
        barrier.wait()
        try:
            out[i] = ("ok", f())
        except Exception as e:  # noqa: BLE001 - we classify outcomes below
            out[i] = ("err", e)

    ts = [threading.Thread(target=go, args=(i, f)) for i, f in enumerate(fns)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    return out


def fresh(st):
    """Separate Store instance per thread => separate connections and no shared replay cache."""
    return Store(st.dsn)


def test_concurrent_duplicate_signatures_authorize_once(room):
    st, rid, u = room
    pkg = st.apply(rid, u["pm"], "p", {"type": "propose", "package_id": "p1",
                                       "orders": [{"order_id": "o1", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
    sign = {"type": "sign", "package_id": "p1", "digest": pkg["digest"]}
    out = race([lambda i=i: fresh(st).apply(rid, u["mp"], f"s{i}", sign) for i in range(4)])
    assert [o[0] for o in out].count("ok") == 1
    assert all(isinstance(o[1], CommandRejected) for o in out if o[0] == "err")
    _, s = fresh(st).session(rid)
    assert [o.order_id for o in s.e.orders] == ["o1"]


def test_concurrent_retries_of_one_key_create_one_order(room):
    st, rid, u = room
    cmd = {"type": "ticket", "order_id": "t1", "sym": "ALTO", "side": "SELL", "qty": 1000}
    out = race([lambda: fresh(st).apply(rid, u["pm"], "same-key", cmd) for _ in range(5)])
    assert all(o[0] == "ok" and o[1] == out[0][1] for o in out)
    with psycopg.connect(DSN) as c:
        assert c.execute("select count(*) from commands where room_id=%s", (rid,)).fetchone()[0] == 1


def test_concurrent_ready_advances_exactly_once(room):
    st, rid, u = room
    out = race([lambda: fresh(st).apply(rid, u["pm"], "r-pm", {"type": "ready"}),
                lambda: fresh(st).apply(rid, u["mp"], "r-mp", {"type": "ready"})])
    advanced = [o[1]["advanced"] for o in out if o[0] == "ok"]
    assert sorted(advanced) == [False, True]


def test_journal_is_append_only_and_replay_matches_db(room):
    st, rid, u = room
    st.apply(rid, u["pm"], "r1", {"type": "ready"})
    st.apply(rid, u["mp"], "r2", {"type": "ready"})
    with psycopg.connect(DSN) as c:
        with pytest.raises(psycopg.errors.RaiseException):
            c.execute("delete from journal_entries where room_id=%s", (rid,))
    with psycopg.connect(DSN) as c:
        n = c.execute("select count(*) from journal_entries where room_id=%s", (rid,)).fetchone()[0]
    _, s = fresh(st).session(rid)
    assert n == len(s.e.j.entries)
