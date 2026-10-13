"""Local frame-time measurement for the Godot client (P3 "60 fps" acceptance).

Opens a solo room on a running API, boots the real game window (office, street, characters, lighting, HUD),
walks a fixed route through every location and records per-frame wall-clock times after a warm-up.
V-Sync is disabled and the frame cap removed so the numbers are the frame's own cost.

    py -3 scripts/measure_frames.py --server http://127.0.0.1:8022 --godot godot --output perf.json

Crisis route (--crisis): pins the case1 "base" variant (server needs FUNDFORGE_TEST_VARIANTS=1), stands at the
trading desk and, while frames are recorded, POSTs joint skip-ready commands so the day-13 borrow recall (broker
courier) and later notices arrive in the running client. The day-12 Tactical redemption notice is already in the
first view, so the tactical LP visitor arrives with the world itself; use --warmup 0 to record those frames.
The report's "events" list gives the worst frame within 3 s after each world effect.
Extra engine flags (e.g. "--rendering-method gl_compatibility") go in --engine-args.

Budget (scripts/budgets.json "frame"): p95 frame time <= 16.7 ms at the recorded resolution on the recorded
adapter. This needs a real GPU and display; CI runners have neither, so CI checks only sizes.
Prints and writes the JSON report; exits 1 when the budget is missed.
"""

import argparse
import json
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
ROUTE = "trading@0,committee@4,risk@8,lp@12,backoffice@16,research@20,street@24,broker@28,trading@34"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8000")
    ap.add_argument("--godot", default="godot", help="editor binary (or an exported build with --exported)")
    ap.add_argument("--exported", action="store_true")
    ap.add_argument("--resolution", default="1600x900")
    ap.add_argument("--warmup", type=float, default=5)
    ap.add_argument("--seconds", type=float, default=40)
    ap.add_argument("--output", default="perf.json")
    ap.add_argument("--crisis", action="store_true", help="pinned base room; skip-ready during the recording")
    ap.add_argument("--skip-at", default="5,9,13,17,21,25,29,33", help="--crisis: seconds after the world appears")
    ap.add_argument("--engine-args", default="", help="extra Godot flags, e.g. '--rendering-method gl_compatibility'")
    a = ap.parse_args()

    http = build_opener(ProxyHandler({}))
    base = a.server.rstrip("/")

    def call(path: str, body: dict | None = None, token: str = "") -> dict:
        headers = {"Content-Type": "application/json"} | ({"Authorization": f"Bearer {token}"} if token else {})
        if body is not None and token:
            headers["Idempotency-Key"] = str(uuid.uuid4())
        req = Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
        with http.open(req, timeout=15) as r:
            return json.load(r)

    room = call("/api/rooms", {"scenario": "case1", "solo_role": "pm"} | ({"variant": "base"} if a.crisis else {}))
    token = room["tokens"]["pm"]
    out = Path(a.output).resolve()
    out.unlink(missing_ok=True)
    engine = [a.godot] if a.exported else [a.godot, "--path", str(ROOT / "game")]
    route = "trading@0" if a.crisis else ROUTE
    cmd = engine + shlex.split(a.engine_args) + ["--disable-vsync", "--max-fps", "0", "--resolution", a.resolution, "--",
                    f"--server={a.server}", f"--join={room['room_id']}:{token}", f"--goto={route}",
                    f"--perf={out}", f"--perf-warmup={a.warmup}", f"--perf-seconds={a.seconds}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    head = []
    if a.crisis:  # time the skips from the moment the office world exists (Godot start-up time varies)
        for line in proc.stdout:
            head.append(line)
            if line.startswith("perf: world up"):
                break
    t0 = time.monotonic()
    for at in ([float(x) for x in a.skip_at.split(",")] if a.crisis else []):
        time.sleep(max(0.0, t0 + at - time.monotonic()))
        if proc.poll() is not None:
            break
        for _ in range(2):  # the solo bot answers a pending ready on the next command, so ask twice
            version = call(f"/api/rooms/{room['room_id']}/view", token=token)["version"]
            res = call(f"/api/rooms/{room['room_id']}/commands", {"type": "ready", "version": version, "skip": True}, token)
            print(f"skip-ready {time.monotonic() - t0:.1f}s after world up: {res}", file=sys.stderr)
            if res.get("advanced"):
                break
    log = "".join(head) + proc.communicate(timeout=a.warmup + a.seconds + 120)[0]
    if not out.exists():
        print(log[-6000:], file=sys.stderr)
        print("no perf report written", file=sys.stderr)
        return 1
    report = json.loads(out.read_text())
    budget = json.loads((ROOT / "scripts" / "budgets.json").read_text())["frame"]["p95_ms_max"]
    report["budget_p95_ms"] = budget
    report["pass"] = report["p95_ms"] <= budget
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
