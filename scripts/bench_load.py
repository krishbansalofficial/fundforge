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
    def __init__(self) -> None:
        self.lat: dict[str, list[float]] = {"view": [], "command": []}
        self.status: dict[str, dict[str, int]] = {"view": {}, "command": {}}
        self.errors: dict[str, int] = {}
        self.on = False

    def add(self, kind: str, ms: float, status: int | str) -> None:
        if self.on:
            self.lat[kind].append(ms)
            self.status[kind][str(status)] = self.status[kind].get(str(status), 0) + 1


async def call(c: httpx.AsyncClient, st: Stats, kind: str, method: str, url: str, **kw) -> httpx.Response | None:
    t0 = time.perf_counter()
    try:
        r = await c.request(method, url, **kw)
    except httpx.HTTPError as e:
        st.add(kind, (time.perf_counter() - t0) * 1000, type(e).__name__)
        return None
    st.add(kind, (time.perf_counter() - t0) * 1000, r.status_code)
    return r


async def seat(c: httpx.AsyncClient, st: Stats, prefix: str, token: str, role: str, window: float,
               stop: asyncio.Event) -> None:
    auth = {"Authorization": f"Bearer {token}"}
    etag, version, finished, next_ready, n = None, 0, False, time.monotonic() + window, 0
    while not stop.is_set():
        t0 = time.monotonic()
        cond = {"If-None-Match": etag} if etag else {}
        r = await call(c, st, "view", "GET", f"{prefix}/view", headers={**auth, **cond})
        if r is not None and r.status_code == 200:
            etag, body = r.headers.get("ETag"), r.json()
            version, finished = body["version"], body.get("outcome") is not None
        if not finished and time.monotonic() >= next_ready:
            n += 1
            await call(c, st, "command", "POST", f"{prefix}/commands", json={"type": "ready", "version": version},
                       headers={**auth, "Idempotency-Key": f"load-{role}-{n}"})
            next_ready = time.monotonic() + window
        await asyncio.sleep(max(0.0, POLL_S - (time.monotonic() - t0)))


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
    return {ln.split(" ", 1)[0]: ln.split(" ", 1)[1] for ln in out.splitlines() if ln.startswith("fundforge-")}


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


async def run(a: argparse.Namespace) -> dict:
    # Caddy's internal CA on localhost only (as deploy/smoke.sh's curl -k); anything else keeps verification.
    local = httpx.URL(a.base).host in ("localhost", "127.0.0.1")
    limits = httpx.Limits(max_connections=a.connections, max_keepalive_connections=a.connections)
    steps_out, stop = [], asyncio.Event()
    async with httpx.AsyncClient(base_url=a.base, verify=not local, timeout=10, limits=limits) as c:
        tasks: list[asyncio.Task] = []
        rooms = 0
        for target in a.steps:
            while rooms < target:
                r = await c.post("/api/rooms", json={"pm_name": f"Load PM {rooms}", "mp_name": f"Load MP {rooms}"})
                r.raise_for_status()
                room = r.json()
                prefix = f"/api/rooms/{room['room_id']}"
                tasks += [asyncio.create_task(seat(c, st_ref[0], prefix, room["tokens"][role], role, a.window, stop))
                          for role in ("pm", "mp")]
                rooms += 1
            await asyncio.sleep(a.warmup)
            st_ref[0].__init__()  # reset counters in place: seats hold this object
            m0 = histogram(httpx.get(a.metrics, timeout=10).text, "fundforge_command_seconds")
            st_ref[0].on, t0 = True, time.perf_counter()
            await asyncio.sleep(a.step_seconds / 2)
            cpu = docker_cpu()
            await asyncio.sleep(a.step_seconds / 2)
            st_ref[0].on, seconds = False, time.perf_counter() - t0
            m1 = histogram(httpx.get(a.metrics, timeout=10).text, "fundforge_command_seconds")
            s = {**summary(st_ref[0], seconds, rooms), "server_command_seconds": server_delta(m0, m1),
                 "docker_cpu": cpu}
            steps_out.append(s)
            print(f"{rooms:4d} rooms: view p95 {s['view_ms'].get('p95')} ms, rps {s['view_rps_achieved']}/"
                  f"{s['view_rps_target']}, 304 {s['ratio_304']}, 5xx {s['http_5xx']}, errors {s['client_errors']}"
                  f"{' CLIENT SATURATED' if s['client_saturated'] else ''}", flush=True)
        stop.set()
        await asyncio.gather(*tasks, return_exceptions=True)
    return {"steps": steps_out}


st_ref = [Stats()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://localhost")
    ap.add_argument("--metrics", default="http://127.0.0.1:9464/metrics")
    ap.add_argument("--steps", type=lambda s: [int(x) for x in s.split(",")], default=[10, 25, 50, 100, 200])
    ap.add_argument("--step-seconds", type=float, default=60)
    ap.add_argument("--warmup", type=float, default=10)
    ap.add_argument("--window", type=float, default=10, help="seconds between each seat's ready commands")
    ap.add_argument("--connections", type=int, default=400)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    res = asyncio.run(run(a))
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
                   "warmup_s": a.warmup, "steps": a.steps, "client": "one Python process, httpx async, HTTP/1.1"},
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
        path = a.out / f"{doc['measured_at'][:10]}-B3-{doc['commit'].replace('+', '_')}.json"
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
