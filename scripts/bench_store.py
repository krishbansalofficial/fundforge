"""Store benchmark B2: accepted-command latency and cold room replay against a real Postgres.

Drives the S2 golden path (research, replacement borrow, cure, second BEAM sale) as Session commands
through ``Store.apply`` on case1/base, recording wall time per command type. Then builds clock rooms
of 10, 50 and 200 commands, clears the session cache and times ``Store.session`` (a cold replay) and
``Store.verify``. Refuses to report if two S2 rooms or repeated replays disagree on the journal digest.

Case1 has only 18 execution windows, so a clock room is: set_speed, then a tick whenever the clock
runs and set_speed whenever it auto-pauses, until the season ends; any remaining commands are logged
``pause`` commands on the finished season. Every row is a real accepted command that replay re-handles.

    cd backend && DATABASE_URL=postgresql://... uv run python ../scripts/bench_store.py --out ../bench/results

Never point it at a database you care about: it creates rooms, and the append-only triggers keep them.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench_engine import commit, machine, pct

from fundforge.balance import cure_qty
from fundforge.engine import RULES_VERSION
from fundforge.governance import CLOCK
from fundforge.store import Store

SIZES = (10, 50, 200)


def _room(st: Store) -> tuple[str, dict[str, str]]:
    r = st.create_room("case1", "Ana", "Ben", variant="base")
    return r["room_id"], {role: st.auth(r["room_id"], tok) for role, tok in r["tokens"].items()}


def _timed(st: Store, lat: dict[str, list[float]] | None, rid: str, user: str, key: str, cmd: dict) -> dict:
    t0 = time.perf_counter()
    out = st.apply(rid, user, key, cmd)
    if lat is not None:
        lat[cmd["type"]].append((time.perf_counter() - t0) * 1000)
    return out


def play_s2(st: Store, lat: dict[str, list[float]] | None) -> tuple[str, str]:
    """The S2 golden path as partner commands, one barrier at a time. Returns (room, outcome label)."""
    rid, u = _room(st)
    k = 0
    while True:
        _, s, _ = st.session(rid)
        nxt = s.e.next_event()
        if s.e.finished() or nxt is None:
            return rid, s.e.outcome()["label"]
        k += 1
        at = (nxt.day, nxt.phase)
        orders = []
        if at == (12, "EXEC_A"):
            _timed(st, lat, rid, u["mp"], f"res{k}", {"type": "research", "topic": "borrow"})
        elif at == (14, "EXEC_A"):
            _timed(st, lat, rid, u["mp"], f"acc{k}", {"type": "accept_replacement"})
        elif at == (16, "EXEC_A"):
            orders = [{"order_id": "s2-alto", "sym": "ALTO", "side": "SELL", "qty": cure_qty(s.e)}]
        elif at == (18, "EXEC_A"):
            orders = [{"order_id": "s2-beam2", "sym": "BEAM", "side": "SELL", "qty": 20000}]
        if orders:
            d = _timed(st, lat, rid, u["pm"], f"p{k}", {"type": "propose", "package_id": f"p{k}", "orders": orders})
            _timed(st, lat, rid, u["mp"], f"s{k}", {"type": "sign", "package_id": f"p{k}", "digest": d["digest"]})
        _timed(st, lat, rid, u["pm"], f"ra{k}", {"type": "ready"})
        _timed(st, lat, rid, u["mp"], f"rb{k}", {"type": "ready"})


def clock_room(st: Store, n: int, lat: dict[str, list[float]] | None) -> str:
    """A room of exactly ``n`` accepted commands (see module docstring)."""
    rid, u = _room(st)
    for v in range(n):
        _, s, _ = st.session(rid)
        if s.running():
            _timed(st, lat, rid, CLOCK, f"tick-{v}", {"type": "tick", "expected_version": v})
        elif not s.e.finished():
            _timed(st, lat, rid, u["pm"], f"go-{v}", {"type": "set_speed", "speed": 1})
        else:
            _timed(st, lat, rid, u["mp"], f"pause-{v}", {"type": "pause"})
    assert st.session(rid)[0] == n
    return rid


def cold_replay(st: Store, rid: str) -> tuple[float, str]:
    st._cache.clear()  # benchmark only: force Store.session to rebuild from the command log
    t0 = time.perf_counter()
    _, s, _ = st.session(rid)
    return (time.perf_counter() - t0) * 1000, s.e.j.digest()


def stats(xs: list[float]) -> dict[str, float]:
    return {"n": len(xs), "min": round(min(xs), 3), "p50": round(statistics.median(xs), 3),
            "p95": round(pct(xs, 0.95), 3), "p99": round(pct(xs, 0.99), 3), "max": round(max(xs), 3)}


def run(dsn: str, rooms: int = 10, samples: int = 20, warmup: int = 2, sizes: tuple[int, ...] = SIZES) -> dict:
    st = Store(dsn)
    try:
        st.init()
        with st.pool.connection() as c:
            server = c.execute("show server_version").fetchone()[0]
        for _ in range(warmup):
            play_s2(st, None)
        lat: dict[str, list[float]] = defaultdict(list)
        s2 = [play_s2(st, lat) for _ in range(rooms)]
        labels = {label for _, label in s2}
        verifies = [st.verify(rid) for rid, _ in s2]
        s2_digests = {v["journal_digest"] for v in verifies}
        if len(s2_digests) != 1:
            raise RuntimeError(f"nondeterministic: S2 rooms produced {len(s2_digests)} journal digests")

        replay: dict[str, dict] = {}
        for n in sizes:
            rid = clock_room(st, n, lat)
            for _ in range(warmup):
                cold_replay(st, rid)
            times, digests = [], set()
            for _ in range(samples):
                t, d = cold_replay(st, rid)
                times.append(t)
                digests.add(d)
            vt: list[float] = []
            for _ in range(samples):
                t0 = time.perf_counter()
                rep = st.verify(rid)
                vt.append((time.perf_counter() - t0) * 1000)
                digests.add(rep["journal_digest"])
            if len(digests) != 1:
                raise RuntimeError(f"nondeterministic: {n}-command room replayed to {len(digests)} digests")
            replay[str(n)] = {"replay_ms": stats(times), "verify_ms": stats(vt), "entries": rep["entries"],
                              "journal_digest": digests.pop()}

        s2_rid = s2[0][0]
        vt = []
        for _ in range(samples):
            t0 = time.perf_counter()
            st.verify(s2_rid)
            vt.append((time.perf_counter() - t0) * 1000)
    finally:
        st.close()

    return {
        "benchmark": "B2-store",
        "commit": commit(),
        "rules_version": RULES_VERSION,
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "machine": machine(),
        "postgres": server,
        "scenario": "case1/base",
        "s2_rooms": rooms,
        "s2_room_version": verifies[0]["version"],
        "s2_outcome": sorted(labels),
        "s2_journal_digest": s2_digests.pop(),
        "s2_verify_ms": stats(vt),
        "warmup": warmup,
        "samples": samples,
        "apply_ms": {t: stats(xs) for t, xs in sorted(lat.items())},
        "replay": replay,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rooms", type=int, default=10, help="timed S2 rooms")
    ap.add_argument("--samples", type=int, default=20, help="cold replays and verifies per room size")
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("set DATABASE_URL to a scratch Postgres database", file=sys.stderr)
        return 2
    try:
        doc = run(dsn, args.rooms, args.samples, args.warmup)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 2
    text = json.dumps(doc, indent=2)
    print(text)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        stamp = doc["measured_at"][:10]
        (args.out / f"{stamp}-B2-{doc['commit'].replace('+', '_')}.json").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
