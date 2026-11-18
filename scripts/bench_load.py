"""Benchmark B3: API load against the production compose stack (docs/BENCHMARKS.md).

Each virtual room has two seats polling GET /view every 0.5 s with If-None-Match, and both seats send a
version-bound `ready` every --window seconds (the command burst at a decision window). Rooms ramp through
--steps (cumulative: earlier rooms keep playing); each step runs --step-seconds after --warmup seconds.

    deploy up with FUNDFORGE_ROOMS_PER_IP raised (see the PROGRESS entry), then from backend/:
    .venv/Scripts/python ../scripts/bench_load.py --base https://localhost --out ../bench/results

Per step: client p50/p95/p99 per endpoint, status counts, 304 ratio, achieved vs target request rate (a
single client process can saturate before the server: the step is flagged `client_saturated` below 90% of
the target), server-side fundforge_command_seconds from /metrics (delta of the histogram over the step),
and container CPU from `docker stats`. Target: p95 GET /view < 100 ms and zero 5xx at 100 rooms; the knee
is the first step that misses it.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import multiprocessing
import os
import platform
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:  # on the host; inside a bare client container (see PROGRESS) the caller passes these via env
    from bench_engine import commit, machine
except ImportError:
    def commit() -> str:
        return os.environ.get("FUNDFORGE_COMMIT", "unknown")

    def machine() -> str:
        return os.environ.get("FUNDFORGE_MACHINE", platform.platform())


def pct(xs: list[float], q: float) -> float:
    ordered = sorted(xs)  # same definition as bench_engine.pct
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]

POLL_S = 0.5
VIEW_P95_MS, TARGET_ROOMS = 100.0, 100


class Stats:
    """Latencies and status counts for one step; one per step in each client process, merged by the parent."""

    def __init__(self) -> None:
        self.lat: dict[str, list[float]] = {"view": [], "command": []}
        self.status: dict[str, dict[str, int]] = {"view": {}, "command": {}}

    def add(self, kind: str, ms: float, status: int | str) -> None:
        self.lat[kind].append(ms)
        self.status[kind][str(status)] = self.status[kind].get(str(status), 0) + 1

    def merge(self, other: Stats) -> None:
        for kind in self.lat:
            self.lat[kind] += other.lat[kind]
            for k, v in other.status[kind].items():
                self.status[kind][k] = self.status[kind].get(k, 0) + v


class Recorder:
    """Counts a request only if it started inside a step's measurement window (wall clock, shared by all procs)."""

    def __init__(self, windows: list[tuple[float, float]]) -> None:
        self.windows, self.steps = windows, [Stats() for _ in windows]

    def add(self, t_start: float, kind: str, ms: float, status: int | str) -> None:
        for (lo, hi), st in zip(self.windows, self.steps, strict=True):
            if lo <= t_start < hi:
                st.add(kind, ms, status)
                return


async def call(c: httpx.AsyncClient, rec: Recorder, kind: str, method: str, url: str, **kw) -> httpx.Response | None:
    wall, t0 = time.time(), time.perf_counter()
    try:
        r = await c.request(method, url, **kw)
    except httpx.HTTPError as e:
        rec.add(wall, kind, (time.perf_counter() - t0) * 1000, type(e).__name__)
        return None
    rec.add(wall, kind, (time.perf_counter() - t0) * 1000, r.status_code)
    return r


async def seat(c: httpx.AsyncClient, rec: Recorder, prefix: str, token: str, role: str, window: float,
               stop: asyncio.Event) -> None:
    auth = {"Authorization": f"Bearer {token}"}
    etag, version, finished, next_ready, n = None, 0, False, time.monotonic() + window, 0
    while not stop.is_set():
        t0 = time.monotonic()
        cond = {"If-None-Match": etag} if etag else {}
        r = await call(c, rec, "view", "GET", f"{prefix}/view", headers={**auth, **cond})
        if r is not None and r.status_code == 200:
            etag, body = r.headers.get("ETag"), r.json()
            version, finished = body["version"], body.get("outcome") is not None
        if not finished and time.monotonic() >= next_ready:
            n += 1
            await call(c, rec, "command", "POST", f"{prefix}/commands", json={"type": "ready", "version": version},
                       headers={**auth, "Idempotency-Key": f"load-{role}-{n}"})
            next_ready = time.monotonic() + window
        await asyncio.sleep(max(0.0, POLL_S - (time.monotonic() - t0)))


async def client_run(base: str, connections: int, window: float, starts: list[float],
                     windows: list[tuple[float, float]], rooms: list[list[dict]]) -> Recorder:
    """One client process: at starts[i] it begins polling its share of the rooms added at step i (rooms[i])."""
    local = httpx.URL(base).host in ("localhost", "127.0.0.1")  # Caddy's internal CA, as deploy/smoke.sh's curl -k
    limits = httpx.Limits(max_connections=connections, max_keepalive_connections=connections)
    rec, stop, tasks = Recorder(windows), asyncio.Event(), []
    async with httpx.AsyncClient(base_url=base, verify=not local, timeout=10, limits=limits) as c:
        for at, batch in zip(starts, rooms, strict=True):
            await asyncio.sleep(max(0.0, at - time.time()))
            tasks += [asyncio.create_task(seat(c, rec, f"/api/rooms/{room['room_id']}", room["tokens"][role], role,
                                               window, stop))
                      for room in batch for role in ("pm", "mp")]
        await asyncio.sleep(max(0.0, windows[-1][1] - time.time()))
        stop.set()
        await asyncio.gather(*tasks, return_exceptions=True)
    return rec


def client_proc(args: tuple) -> list[Stats]:
    return asyncio.run(client_run(*args)).steps


def histogram(text: str, name: str) -> dict[str, float]:
    """{le: cumulative count} plus _sum/_count, summed over label sets."""
    out: dict[str, float] = {}
    for line in text.splitlines():
        m = re.match(rf'{name}_(bucket|sum|count)(\{{[^}}]*\}})? ([0-9.eE+-]+)$', line)
        if not m:
            continue
        key = re.search(r'le="([^"]+)"', m.group(2) or "").group(1) if m.group(1) == "bucket" else f"_{m.group(1)}"
        out[key] = out.get(key, 0.0) + float(m.group(3))
    return out


def server_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float | None]:
    d = {k: after.get(k, 0.0) - before.get(k, 0.0) for k in after}
    count = d.get("_count", 0.0)
    if count <= 0:
        return {"count": 0, "mean_ms": None, "p95_ms_bucket_upper": None}
    buckets = sorted((float(k), v) for k, v in d.items() if not k.startswith("_") and k != "+Inf")
    p95 = next((le for le, v in buckets if v >= 0.95 * count), None)
    return {"count": int(count), "mean_ms": round(d["_sum"] / count * 1000, 2),
            "p95_ms_bucket_upper": None if p95 is None else round(p95 * 1000, 1)}


def docker_cpu() -> dict[str, str]:
    try:
        out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.CPUPerc}} {{.MemUsage}}"],
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return {}
    return {ln.split(" ", 1)[0]: ln.split(" ", 1)[1] for ln in out.splitlines() if ln.startswith("fundforge")}


def cpu_from_log(path: Path, lo: float, hi: float) -> dict[str, dict]:
    """Host-sampled `<unix seconds> <container> <cpu%>` lines (docker stats is not reachable from the client
    container); mean and max per container over samples taken inside [lo, hi)."""
    per: dict[str, list[float]] = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        parts = ln.split()
        if len(parts) == 3 and lo <= float(parts[0]) < hi:
            per.setdefault(parts[1], []).append(float(parts[2].rstrip("%")))
    return {k: {"mean_cpu_pct": round(sum(v) / len(v), 1), "max_cpu_pct": max(v), "samples": len(v)}
            for k, v in sorted(per.items())}


def summary(st: Stats, seconds: float, rooms: int) -> dict:
    def lat(xs: list[float]) -> dict:
        return {"n": len(xs), **({f"p{q}": round(pct(xs, q / 100), 2) for q in (50, 95, 99)} if xs else {})}
    views = st.status["view"]
    target = rooms * 2 / POLL_S
    achieved = len(st.lat["view"]) / seconds
    five = sum(v for k, v in {**views, **st.status["command"]}.items() if k.startswith("5"))
    errors = sum(v for k, v in {**views, **st.status["command"]}.items() if not k.isdigit())
    return {"rooms": rooms, "seconds": round(seconds, 1), "view_ms": lat(st.lat["view"]),
            "command_ms": lat(st.lat["command"]), "status": st.status,
            "ratio_304": round(views.get("304", 0) / max(1, len(st.lat["view"])), 3),
            "view_rps_target": round(target, 1), "view_rps_achieved": round(achieved, 1),
            "client_saturated": achieved < 0.9 * target, "http_5xx": five, "client_errors": errors}


def run(a: argparse.Namespace) -> dict:
    """Rooms for every step are created first (the clock is off, so idle rooms cost nothing); then all client
    processes follow one wall-clock schedule: step i adds its rooms at starts[i] and is measured over
    [starts[i] + warmup, + step_seconds). The parent scrapes /metrics at the window edges and merges the lists."""
    local = httpx.URL(a.base).host in ("localhost", "127.0.0.1")
    rooms: list[dict] = []
    with httpx.Client(base_url=a.base, verify=not local, timeout=10) as c:
        while len(rooms) < max(a.steps):
            r = c.post("/api/rooms", json={"pm_name": f"Load PM {len(rooms)}", "mp_name": f"Load MP {len(rooms)}"})
            r.raise_for_status()
            rooms.append(r.json())
    span = a.warmup + a.step_seconds
    t0 = time.time() + 5 + a.procs  # spawn and import time for the client processes
    starts = [t0 + i * span for i in range(len(a.steps))]
    windows = [(s + a.warmup, s + span) for s in starts]
    bounds = [0, *a.steps]
    share = [[[room for j, room in enumerate(rooms[bounds[i]:bounds[i + 1]]) if j % a.procs == p]
              for i in range(len(a.steps))] for p in range(a.procs)]
    steps_out, server = [], []
    with multiprocessing.get_context("spawn").Pool(a.procs) as pool:
        pending = pool.map_async(client_proc, [(a.base, a.connections, a.window, starts, windows, share[p])
                                               for p in range(a.procs)])
        for lo, hi in windows:
            time.sleep(max(0.0, lo - time.time()))
            m0 = histogram(httpx.get(a.metrics, timeout=10).text, "fundforge_command_seconds")
            time.sleep(max(0.0, (lo + hi) / 2 - time.time()))
            snap = {} if a.cpu_log else docker_cpu()
            time.sleep(max(0.0, hi - time.time()))
            m1 = histogram(httpx.get(a.metrics, timeout=10).text, "fundforge_command_seconds")
            server.append((server_delta(m0, m1), snap))
        per_proc = pending.get()
    for i, ((lo, hi), (srv, snap)) in enumerate(zip(windows, server, strict=True)):
        st = Stats()
        for proc_steps in per_proc:
            st.merge(proc_steps[i])
        s = {**summary(st, hi - lo, a.steps[i]), "server_command_seconds": srv,
             "docker_cpu": cpu_from_log(a.cpu_log, lo, hi) if a.cpu_log else snap}
        steps_out.append(s)
        print(f"{a.steps[i]:4d} rooms: view p95 {s['view_ms'].get('p95')} ms, rps {s['view_rps_achieved']}/"
              f"{s['view_rps_target']}, 304 {s['ratio_304']}, 5xx {s['http_5xx']}, errors {s['client_errors']}"
              f"{' CLIENT SATURATED' if s['client_saturated'] else ''}", flush=True)
    return {"steps": steps_out, "windows_unix": [[round(lo, 1), round(hi, 1)] for lo, hi in windows]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://localhost")
    ap.add_argument("--metrics", default="http://127.0.0.1:9464/metrics")
    ap.add_argument("--steps", type=lambda s: [int(x) for x in s.split(",")], default=[10, 25, 50, 100, 200])
    ap.add_argument("--step-seconds", type=float, default=60)
    ap.add_argument("--warmup", type=float, default=10)
    ap.add_argument("--window", type=float, default=10, help="seconds between each seat's ready commands")
    ap.add_argument("--connections", type=int, default=400)
    ap.add_argument("--procs", type=int, default=1, help="client processes; rooms are split round-robin")
    ap.add_argument("--cpu-log", type=Path, help="host-sampled docker stats lines: <unix s> <container> <cpu%%>")
    ap.add_argument("--tag", default="", help="suffix for the result file name, e.g. caddy-p4")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    res = run(a)
    knee = next((s["rooms"] for s in res["steps"]
                 if (s["view_ms"].get("p95") or 1e9) >= VIEW_P95_MS or s["http_5xx"]), None)
    at_target = next((s for s in res["steps"] if s["rooms"] == TARGET_ROOMS), None)
    try:
        from fundforge.engine import RULES_VERSION
    except ImportError:
        RULES_VERSION = os.environ.get("FUNDFORGE_RULES_VERSION", "unknown")
    doc = {
        "benchmark": "B3-api-load", "commit": commit(), "rules_version": RULES_VERSION,
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"), "machine": machine(),
        "python": sys.version.split()[0],
        "stack": os.environ.get("FUNDFORGE_LOAD_STACK", "deploy/compose.prod.yaml on Docker Desktop (WSL2), client on "
                                "the Windows host, via Caddy TLS"),
        "method": {"poll_s": POLL_S, "ready_every_s": a.window, "step_seconds": a.step_seconds,
                   "warmup_s": a.warmup, "steps": a.steps, "base": a.base,
                   "client": f"{a.procs} Python process(es), httpx async, HTTP/1.1, rooms split round-robin, "
                             "one wall-clock step schedule shared by all processes"},
        "client_procs": a.procs,
        "target": f"p95 GET /view < {VIEW_P95_MS:g} ms and zero 5xx at {TARGET_ROOMS} rooms",
        "target_met": bool(at_target and (at_target["view_ms"].get("p95") or 1e9) < VIEW_P95_MS
                           and not at_target["http_5xx"] and not at_target["client_saturated"]),
        "knee_rooms": knee,
        "limits": ["client and server share one machine, so they compete for CPU",
                   "not the intended production VM size; a laptop under Docker Desktop",
                   "a saturated client under-reports load; such steps are flagged and are not a server limit"],
        **res,
    }
    print(f"knee: {knee}; target met at {TARGET_ROOMS} rooms: {doc['target_met']}")
    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
        suffix = f"-{a.tag}" if a.tag else ""
        path = a.out / f"{doc['measured_at'][:10]}-B3-{doc['commit'].replace('+', '_')}{suffix}.json"
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
