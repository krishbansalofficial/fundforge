"""Logical backups of the authoritative database and a restore-and-verify check.

``dump`` holds one repeatable-read snapshot, records each room's stored version, journal
digest and chain head in a manifest, and runs ``pg_dump --snapshot`` against that same
snapshot, so the archive and the manifest describe exactly the same commands.

``check`` restores an archive into a fresh scratch database and accepts it only if every
manifest room is present with the same stored head, and every room pinned to this
server's rules re-derives through ``Store.verify`` to that same digest and chain head.
Rooms pinned to older rules cannot be replayed by this runtime; their stored heads are
still compared and they are reported as ``incompatible``, never as verified.

    python -m fundforge.backup dump  BACKUP.dump   # also writes BACKUP.dump.manifest.json
    python -m fundforge.backup check BACKUP.dump   # needs CREATEDB; drops the scratch DB

``DATABASE_URL`` names the source (dump) or the server to restore into (check).
"""

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from .engine import RULES_VERSION
from .store import GENESIS, ReplayDivergence, RoomIncompatible, Store

FORMAT = 1


class BackupError(RuntimeError):
    pass


def _tool(name: str) -> str:
    path = shutil.which(name, path=os.environ.get("PG_BIN") or None)
    if not path:
        raise BackupError(f"{name} not found (install the PostgreSQL client or set PG_BIN)")
    return path


def _run(args: list[str]) -> None:
    done = subprocess.run(args, capture_output=True, text=True)
    if done.returncode != 0:
        raise BackupError(f"{Path(args[0]).name} failed: {done.stderr.strip()}")


def _heads(c: psycopg.Connection[tuple[Any, ...]]) -> dict[str, dict[str, Any]]:
    """Each room's stored head: version, rules, and the digest/chain of its last command."""
    rows = c.execute("select r.id, r.version, r.rules_version, c.journal_digest_after, c.chain_hash"
                     " from rooms r left join commands c on c.room_id=r.id and c.seq=r.version"
                     " order by r.id").fetchall()
    return {rid: {"version": v, "rules_version": rules, "journal_digest": digest, "chain_head": link or GENESIS}
            for rid, v, rules, digest, link in rows}


def manifest_path(archive: Path) -> Path:
    return archive.with_name(archive.name + ".manifest.json")


def dump(dsn: str, archive: Path) -> dict[str, Any]:
    pg_dump = _tool("pg_dump")
    with psycopg.connect(dsn) as c:
        c.execute("begin isolation level repeatable read read only")
        snap = c.execute("select pg_export_snapshot()").fetchone()
        if snap is None:
            raise BackupError("could not export a snapshot")
        heads = _heads(c)
        _run([pg_dump, "--format=custom", "--no-owner", "--no-acl", f"--snapshot={snap[0]}",
              f"--file={archive}", f"--dbname={dsn}"])
        c.execute("commit")
    manifest = {"format": FORMAT, "rules_version": RULES_VERSION, "rooms": heads}
    manifest_path(archive).write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    return manifest


def check(dsn: str, archive: Path, keep: bool = False) -> dict[str, Any]:
    manifest = json.loads(manifest_path(archive).read_text(encoding="utf-8"))
    if manifest.get("format") != FORMAT:
        raise BackupError(f"unknown manifest format {manifest.get('format')!r}")
    scratch = f"fundforge_restore_{secrets.token_hex(4)}"
    target = make_conninfo(dsn, dbname=scratch)
    with psycopg.connect(dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("create database {}").format(sql.Identifier(scratch)))
    try:
        _run([_tool("pg_restore"), "--no-owner", "--no-acl", "--exit-on-error", f"--dbname={target}", str(archive)])
        with psycopg.connect(target) as c:
            restored = _heads(c)
        if restored != manifest["rooms"]:
            missing = sorted(set(manifest["rooms"]) ^ set(restored))
            changed = sorted(r for r in set(restored) & set(manifest["rooms"]) if restored[r] != manifest["rooms"][r])
            raise BackupError(f"restored heads differ from manifest: rooms missing/extra {missing}, changed {changed}")
        report: dict[str, Any] = {"database": scratch, "rooms": {}}
        st = Store(target)
        try:
            for rid, head in restored.items():
                try:
                    v = st.verify(rid)
                except RoomIncompatible as exc:
                    report["rooms"][rid] = {"status": "incompatible", "reason": str(exc)}
                    continue
                except ReplayDivergence as exc:
                    raise BackupError(f"room {rid}: {exc}") from exc
                got = {"version": v["version"], "chain_head": v["chain_head"],
                       "journal_digest": v["journal_digest"] if v["version"] else head["journal_digest"]}
                want = {k: head[k] for k in got}
                if got != want:
                    raise BackupError(f"room {rid}: replayed {got} != manifest {want}")
                report["rooms"][rid] = {"status": "verified"} | got
        finally:
            st.close()
        return report
    finally:
        if not keep:
            with psycopg.connect(dsn, autocommit=True) as admin:
                admin.execute(sql.SQL("drop database if exists {} with (force)").format(sql.Identifier(scratch)))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m fundforge.backup", description=__doc__.split("\n\n")[0])
    p.add_argument("action", choices=["dump", "check"])
    p.add_argument("archive", type=Path)
    p.add_argument("--keep", action="store_true", help="check: keep the scratch database")
    a = p.parse_args(argv)
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is required", file=sys.stderr)
        return 2
    try:
        out = dump(dsn, a.archive) if a.action == "dump" else check(dsn, a.archive, a.keep)
    except BackupError as exc:
        print(f"backup {a.action} failed: {exc}", file=sys.stderr)
        return 1
    rooms = out["rooms"]
    if a.action == "dump":
        print(f"dumped {len(rooms)} rooms to {a.archive}")
    else:
        verified = sum(r["status"] == "verified" for r in rooms.values())
        print(f"restored {len(rooms)} rooms: {verified} verified, {len(rooms) - verified} incompatible (heads match)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
