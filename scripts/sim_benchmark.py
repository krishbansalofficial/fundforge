"""Measure how fast the real engine plays whole Case1 runs, and where the time goes.

Run from backend/:  uv run python ../scripts/sim_benchmark.py [--runs 20]

Plays the knowledge-free policy grid through the real Session (balance.play), so the number
includes governance, compliance, rollback snapshots and reconciliation, exactly what an RL
environment would pay per episode. Prints per-episode time and the share of time spent in
copy.deepcopy (Session.handle's rollback snapshot).
"""

import argparse
import cProfile
import os
import pstats
import time
from pathlib import Path

from fundforge import balance
from fundforge.balance import POLICIES
from fundforge.tape import load

FIXTURE = Path(__file__).parents[1] / "fixtures" / "case1.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=20)
    args = ap.parse_args()
    print(f"cores visible: {os.cpu_count()}")
    for variant in ("base", "rally"):
        tape = load(FIXTURE, variant)
        for name in ("passive", "S1_balanced"):
            balance.play(tape, POLICIES[name])  # warm up
            t = time.perf_counter()
            for _ in range(args.runs):
                balance.play(tape, POLICIES[name])
            per = (time.perf_counter() - t) / args.runs
            print(f"{variant:6s} {name:12s} {per * 1000:7.1f} ms/episode {1 / per:6.1f} episodes/s/core")
    tape = load(FIXTURE, "base")
    prof = cProfile.Profile()
    prof.enable()
    for _ in range(10):
        balance.play(tape, POLICIES["S1_balanced"])
    prof.disable()
    stats = pstats.Stats(prof).stats  # type: ignore[attr-defined]
    total = sum(v[2] for v in stats.values())  # tottime
    deep = next(v[3] for k, v in stats.items() if k[2] == "deepcopy" and k[0].endswith("copy.py"))  # cumtime
    print(f"deepcopy share of profiled time: {deep / total:.0%}")


if __name__ == "__main__":
    main()
