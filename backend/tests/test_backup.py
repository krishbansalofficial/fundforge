"""Backups count only if a restore re-derives every room to the same digest. Needs DATABASE_URL and pg_dump.

Each test uses its own source database so rooms that other tests deliberately corrupt stay out of it.
With FUNDFORGE_REQUIRE_PG_DUMP=1 (CI) a missing or older-than-server pg_dump fails instead of skipping.
"""

import json
import os
import re
import secrets
import shutil
import subprocess

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from fundforge import backup
from fundforge.store import Store

DSN = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="needs DATABASE_URL (docker compose up -d db)")


def _client_problem() -> str | None:
    pg_dump = shutil.which("pg_dump", path=os.environ.get("PG_BIN") or None)
    if not pg_dump or not shutil.which("pg_restore", path=os.environ.get("PG_BIN") or None):
        return "pg_dump/pg_restore not installed"
    m = re.search(r"(\d+)", subprocess.run([pg_dump, "--version"], capture_output=True, text=True).stdout)
    with psycopg.connect(DSN) as c:
        server = int(c.execute("show server_version_num").fetchone()[0]) // 10000
    if not m or int(m.group(1)) < server:
        return f"pg_dump {m.group(1) if m else '?'} is older than server {server}"
    return None


@pytest.fixture
def source():
    problem = _client_problem()
    if problem:
        if os.environ.get("FUNDFORGE_REQUIRE_PG_DUMP") == "1":
            pytest.fail(problem)
        pytest.skip(problem)
    name = f"fundforge_backup_src_{secrets.token_hex(4)}"
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(sql.SQL("create database {}").format(sql.Identifier(name)))
    dsn = make_conninfo(DSN, dbname=name)
    st = Store(dsn)
    st.init()
    yield st, dsn
    st.close()
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(sql.SQL("drop database if exists {} with (force)").format(sql.Identifier(name)))


def _played_room(st: Store) -> str:
    r = st.create_room("case1", "Ana", "Ben")
    u = {role: st.auth(r["room_id"], tok) for role, tok in r["tokens"].items()}
    pkg = st.apply(r["room_id"], u["pm"], "p", {"type": "propose", "package_id": "p1",
                                                 "orders": [{"order_id": "o1", "sym": "BEAM", "side": "SELL",
                                                             "qty": 20000}]})
    st.apply(r["room_id"], u["mp"], "s", {"type": "sign", "package_id": "p1", "digest": pkg["digest"]})
    for i in range(3):
        st.apply(r["room_id"], u["pm"], f"r{i}pm", {"type": "ready"})
        st.apply(r["room_id"], u["mp"], f"r{i}mp", {"type": "ready"})
    return r["room_id"]


def _scratch_dbs() -> set[str]:
    with psycopg.connect(DSN) as c:
        return {r[0] for r in c.execute("select datname from pg_database where datname like 'fundforge_restore_%'")}


def test_restored_backup_reproduces_every_room(source, tmp_path):
    st, dsn = source
    played, fresh = _played_room(st), st.create_room("case1", "Cy", "Di")["room_id"]
    expected = {rid: st.verify(rid) for rid in (played, fresh)}
    before = _scratch_dbs()

    archive = tmp_path / "fundforge.dump"
    manifest = backup.dump(dsn, archive)
    assert set(manifest["rooms"]) == {played, fresh} and manifest["rooms"][played]["version"] == 8
    report = backup.check(DSN, archive)

    for rid, want in expected.items():
        got = report["rooms"][rid]
        assert got["status"] == "verified"
        assert (got["version"], got["chain_head"]) == (want["version"], want["chain_head"])
    assert report["rooms"][played]["journal_digest"] == expected[played]["journal_digest"]
    assert _scratch_dbs() == before  # the scratch database is dropped


def test_restore_keeps_append_only_triggers(source, tmp_path):
    st, dsn = source
    rid = _played_room(st)
    archive = tmp_path / "fundforge.dump"
    backup.dump(dsn, archive)
    report = backup.check(DSN, archive, keep=True)
    try:
        with pytest.raises(psycopg.errors.RaiseException), \
                psycopg.connect(make_conninfo(DSN, dbname=report["database"])) as c:
            c.execute("delete from commands where room_id=%s", (rid,))
    finally:
        with psycopg.connect(DSN, autocommit=True) as c:
            c.execute(sql.SQL("drop database {} with (force)").format(sql.Identifier(report["database"])))


def test_backup_of_tampered_room_fails_the_check(source, tmp_path):
    st, dsn = source
    rid = _played_room(st)
    with psycopg.connect(dsn) as c:  # someone with DB access bypasses the append-only trigger
        c.execute("alter table commands disable trigger commands_append_only")
        c.execute("""update commands set command = jsonb_set(command, '{orders,0,qty}', '19000')
                     where room_id=%s and seq=1""", (rid,))
        c.execute("alter table commands enable trigger commands_append_only")
    archive = tmp_path / "fundforge.dump"
    backup.dump(dsn, archive)
    with pytest.raises(backup.BackupError, match=rid):
        backup.check(DSN, archive)


def test_manifest_mismatch_and_old_rules_rooms(source, tmp_path):
    st, dsn = source
    rid, old = _played_room(st), st.create_room("case1", "Cy", "Di")["room_id"]
    with psycopg.connect(dsn) as c:
        c.execute("update rooms set rules_version='case1-rules-1999.01.0' where id=%s", (old,))
    archive = tmp_path / "fundforge.dump"
    manifest = backup.dump(dsn, archive)
    report = backup.check(DSN, archive)
    assert report["rooms"][old]["status"] == "incompatible"  # heads compared, never claimed verified
    assert report["rooms"][rid]["status"] == "verified"

    manifest["rooms"][rid]["chain_head"] = "f" * 64  # an archive that does not match its manifest
    backup.manifest_path(archive).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(backup.BackupError, match="differ from manifest"):
        backup.check(DSN, archive)
