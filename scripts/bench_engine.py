"""Engine benchmark B1: time the four golden Case1 paths and the independent control report.

No database, no network. Each sample runs a full Case1 season from the pinned tape
(the same work a room replay does before Postgres I/O), then calls the outcome and
`control_report`. Writes one JSON result with the commit, Python and machine.

    cd backend && uv run python ../scripts/bench_engine.py --repeat 30 --out ../bench/results

Compare a branch with main on the same machine using --compare BASE.json; the run
exits non-zero when a path's fastest sample is slower than BASE by more than --tolerance.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(ROOT / "backend" / "src"))

from test_engine import run  # noqa: E402
from test_golden import PATHS  # noqa: E402

from fundforge.engine import RULES_VERSION  # noqa: E402


def pct(xs: list[float], q: float) -> float:
    ordered = sorted(xs)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


def sample(script: dict) -> tuple[float, float, str]:
    t0 = time.perf_counter()
    engine = run(script)
    digest = engine.outcome()["journal_digest"]
    t1 = time.perf_counter()
    engine.control_report()
    t2 = time.perf_counter()
    return (t1 - t0) * 1000, (t2 - t1) * 1000, digest


def commit() -> str:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "backend/src"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return out.stdout.strip() + ("+dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def machine() -> str:
    cpu = platform.processor() or platform.machine()
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return f"{platform.system()} {platform.machine()}, {cpu}, {os.cpu_count()} logical CPUs"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeat", type=int, default=50)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--compare", type=Path)
    ap.add_argument("--tolerance", type=float, default=0.25)
    args = ap.parse_args()

    results: dict[str, dict] = {}
    for name, script in PATHS.items():
        for _ in range(args.warmup):
            sample(script)
        season, controls, digests = [], [], set()
        for _ in range(args.repeat):
            s, c, d = sample(script)
            season.append(s)
            controls.append(c)
            digests.add(d)
        if len(digests) != 1:
            print(f"{name}: nondeterministic journal digest across samples", file=sys.stderr)
            return 2
        results[name] = {
            "season_ms": {"min": round(min(season), 3), "p50": round(statistics.median(season), 3),
                          "p95": round(pct(season, 0.95), 3), "max": round(max(season), 3)},
            "control_report_ms": {"p50": round(statistics.median(controls), 3),
                                  "p95": round(pct(controls, 0.95), 3)},
            "journal_digest": digests.pop(),
        }

    doc = {
        "benchmark": "B1-engine",
        "commit": commit(),
        "rules_version": RULES_VERSION,
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "machine": machine(),
        "repeat": args.repeat,
        "warmup": args.warmup,
        "paths": results,
    }
    text = json.dumps(doc, indent=2)
    print(text)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        stamp = doc["measured_at"][:10]
        (args.out / f"{stamp}-B1-{doc['commit'].replace('+', '_')}.json").write_text(text + "\n", encoding="utf-8")

    if args.compare:
        base = json.loads(args.compare.read_text(encoding="utf-8"))
        failed = False
        for name, row in results.items():
            # Gate on the minimum: on shared runners the median moves with neighbours' load, while
            # the fastest of N samples tracks the code's own cost much more closely.
            before = base["paths"].get(name, {}).get("season_ms", {}).get("min")
            if before is None:
                continue
            ratio = row["season_ms"]["min"] / before
            flag = "REGRESSION" if ratio > 1 + args.tolerance else "ok"
            failed |= flag == "REGRESSION"
            print(f"{name}: min {before} -> {row['season_ms']['min']} ms ({ratio:.2f}x) {flag}")
        return 1 if failed else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
