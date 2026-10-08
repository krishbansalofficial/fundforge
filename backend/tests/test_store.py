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
    _opened.append(st)
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


_opened: list[Store] = []


def fresh(st):
    """Separate Store instance per thread => separate connections and no shared replay cache."""
    _opened.append(Store(st.dsn))
    return _opened[-1]


@pytest.fixture(autouse=True, scope="module")
def _close_pools():
    yield
    for s in _opened:
        s.close()


def test_concurrent_duplicate_signatures_authorize_once(room):
    st, rid, u = room
    pkg = st.apply(rid, u["pm"], "p", {"type": "propose", "package_id": "p1",
                                       "orders": [{"order_id": "o1", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
    sign = {"type": "sign", "package_id": "p1", "digest": pkg["digest"]}
    out = race([lambda i=i: fresh(st).apply(rid, u["mp"], f"s{i}", sign) for i in range(4)])
    assert [o[0] for o in out].count("ok") == 1
    assert all(isinstance(o[1], CommandRejected) for o in out if o[0] == "err")
    _, s, _ = fresh(st).session(rid)
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
    _, s, _ = fresh(st).session(rid)
    assert n == len(s.e.j.entries)


def play_some(st, rid, u):
    pkg = st.apply(rid, u["pm"], "p", {"type": "propose", "package_id": "p1",
                                       "orders": [{"order_id": "o1", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
    st.apply(rid, u["mp"], "s", {"type": "sign", "package_id": "p1", "digest": pkg["digest"]})
    for i in range(4):
        st.apply(rid, u["pm"], f"r{i}a", {"type": "ready"})
        st.apply(rid, u["mp"], f"r{i}b", {"type": "ready"})


def test_verify_rederives_room_and_sql_trial_balance(room):
    st, rid, u = room
    play_some(st, rid, u)
    rep = fresh(st).verify(rid)
    assert rep["version"] == 10 and rep["entries"] > 0


def test_verify_detects_a_tampered_command(room):
    from fundforge.store import ReplayDivergence
    st, rid, u = room
    play_some(st, rid, u)
    with psycopg.connect(DSN) as c:  # an attacker with DB access bypasses the append-only trigger
        c.execute("alter table commands disable trigger commands_append_only")
        c.execute("""update commands set command = jsonb_set(command, '{orders,0,qty}', '19000')
                     where room_id=%s and seq=1""", (rid,))
        c.execute("alter table commands enable trigger commands_append_only")
    with pytest.raises(ReplayDivergence):
        fresh(st).verify(rid)


def test_database_refuses_unbalanced_entry_at_commit(room):
    st, rid, _ = room
    with pytest.raises(psycopg.errors.RaiseException, match="unbalanced"):
        with psycopg.connect(DSN) as c:
            c.execute("insert into journal_entries values (%s,'bad','fund','2026-01-20','x','[]',0)", (rid,))
            c.execute("insert into journal_lines values (%s,'bad',0,'fund','cash',10.00)", (rid,))
            c.execute("insert into journal_lines values (%s,'bad',1,'fund','capital',-9.99)", (rid,))
            c.commit()


def test_truncate_is_refused(room):
    with pytest.raises(psycopg.errors.RaiseException):
        with psycopg.connect(DSN) as c:
            c.execute("truncate journal_lines")


def test_room_from_other_rules_version_is_refused(room):
    from fundforge.store import RoomIncompatible
    st, rid, _ = room
    with psycopg.connect(DSN) as c:
        c.execute("update rooms set rules_version='case1-rules-1999.01.0' where id=%s", (rid,))
    with pytest.raises(RoomIncompatible):
        fresh(st).session(rid)


def test_shared_store_reads_never_see_rejected_command_effects(room):
    st, rid, u = room  # one Store => one cache shared by readers and writers, like production
    pkg = st.apply(rid, u["pm"], "p", {"type": "propose", "package_id": "p1",
                                       "orders": [{"order_id": "a", "sym": "BEAM", "side": "SELL", "qty": 20000},
                                                  {"order_id": "b", "sym": "ZZZZ", "side": "SELL", "qty": 1}]})
    bad = {"type": "sign", "package_id": "p1", "digest": pkg["digest"]}
    out = race([lambda i=i: st.apply(rid, u["mp"], f"bad{i}", bad) for i in range(3)]
               + [lambda: st.session(rid) for _ in range(3)])
    assert all(o[0] == "err" for o in out[:3])
    _, s, _ = st.session(rid)
    assert s.e.orders == [] and s.packages["p1"].status == "PENDING_APPROVAL"
    assert fresh(st).verify(rid)["version"] == 1


def test_clock_ticks_are_logged_idempotent_and_verifiable(room):
    st, rid, u = room
    st.apply(rid, u["pm"], "go", {"type": "set_speed", "speed": 4})
    with psycopg.connect(DSN) as c:
        c.execute("update rooms set next_tick_at = now() where id=%s", (rid,))
    v = fresh(st).session(rid)[0]
    # two schedulers fire for the same due window: exactly one tick is logged
    out = race([lambda: fresh(st).tick(rid, v), lambda: fresh(st).tick(rid, v)])
    assert out[0][1] == out[1][1]  # second is an idempotent replay of the first
    with psycopg.connect(DSN) as c:
        n = c.execute("select count(*) from commands where room_id=%s and user_id='clock'", (rid,)).fetchone()[0]
    assert n == 1
    assert fresh(st).verify(rid)["version"] == v + 1
