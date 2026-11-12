"""B1 A/B regression gate: run scripts/bench_engine.py from two checkouts on the same machine.

    python scripts/bench_ab.py --base ../base --head .     # exits 1 on regression

Rule (stated here so the gate is reviewable):
  * Rounds are interleaved, alternating order (base,head / head,base / ...) so drift in machine
    load hits both sides equally.
  * Each run reports the fastest season sample per golden path (bench_engine's --repeat samples).
    On shared runners the minimum tracks the code's own cost; medians moved 18-30 ms between runs
    of identical code (docs/BENCHMARKS.md B1 noise finding).
  * Per path, the statistic is the MEDIAN across rounds of those per-run minima, so one lucky or
    unlucky run cannot decide the gate.
  * Fail when head / base > THRESHOLD (1.25, same tolerance as bench_engine --compare) on any path.

Both sides run with the same interpreter (--python, default this one), so a dependency change
between base and head is measured with head's environment. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

THRESHOLD = 1.25
RUN_TIMEOUT_S = 600


def run_once(tree: Path, python: str, repeat: int) -> dict[str, float]:
    out = subprocess.run([python, str(tree / "scripts" / "bench_engine.py"), "--repeat", str(repeat)],
                         cwd=tree / "backend", stdout=subprocess.PIPE, text=True, check=True,
                         timeout=RUN_TIMEOUT_S).stdout  # a hang raises TimeoutExpired: the gate fails closed
    doc = json.loads(out)
    return {name: row["season_ms"]["min"] for name, row in doc["paths"].items()}


def verdict(base: dict[str, list[float]], head: dict[str, list[float]], threshold: float) -> tuple[bool, list[str]]:
    missing = sorted(set(base) - set(head))
    failed = not head or bool(missing)  # fail closed: a removed or renamed path is a reviewed change, not a pass
    lines = [f"{name}: in base, missing from head" for name in missing] or ([] if head else ["head reported no paths"])
    for name in head:
        if name not in base:
            lines.append(f"{name}: new path, no base")
            continue
        b, h = statistics.median(base[name]), statistics.median(head[name])
        ratio = h / b
        bad = ratio > threshold
        failed |= bad
        lines.append(f"{name}: base {b:.3f} ms, head {h:.3f} ms, {ratio:.3f}x {'REGRESSION' if bad else 'ok'}")
    return failed, lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--head", type=Path, required=True)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--repeat", type=int, default=20)
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    if not (a.base / "scripts" / "bench_engine.py").exists():
        print("base has no scripts/bench_engine.py; nothing to compare")
        return 0
    sides: dict[str, dict[str, list[float]]] = {"base": {}, "head": {}}
    for r in range(a.rounds):
        order = [("base", a.base), ("head", a.head)][:: 1 if r % 2 == 0 else -1]
        for side, tree in order:
            for name, ms in run_once(tree.resolve(), a.python, a.repeat).items():
                sides[side].setdefault(name, []).append(ms)
    print(json.dumps(sides, indent=2))
    failed, lines = verdict(sides["base"], sides["head"], a.threshold)
    print(f"rule: median over {a.rounds} interleaved rounds of per-run min (repeat {a.repeat}); "
          f"fail if head/base > {a.threshold}")
    print("\n".join(lines))
    return 1 if failed else 0


if __name__ == "__main__":
    assert verdict({"p": [10, 10, 99]}, {"p": [12, 12, 1]}, 1.25)[0] is False
    assert verdict({"p": [10, 10, 10]}, {"p": [13, 13, 13]}, 1.25)[0] is True
    assert verdict({"p": [10], "q": [10]}, {"p": [10]}, 1.25)[0] is True
    assert verdict({"p": [10]}, {}, 1.25)[0] is True
    assert verdict({"p": [10]}, {"p": [10], "new": [5]}, 1.25)[0] is False
    sys.exit(main())
