"""Benchmark B5: control detection on a seeded fault-injection corpus, and false positives on clean seasons.

No database, no network. The corpus lives in backend/tests/fault_corpus.py (one generator per fault class);
this script runs it with more seeds and writes one JSON result with the commit, Python and machine.

    cd backend && uv run python ../scripts/bench_controls.py --seeds 40 --out ../bench/results
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(ROOT / "backend" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from bench_engine import commit, machine  # noqa: E402
from fault_corpus import corpus  # noqa: E402

from fundforge.engine import RULES_VERSION  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40, help="faults per class")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = corpus(args.seeds)
    doc = {
        "benchmark": "B5-control-detection",
        "commit": commit(),
        "rules_version": RULES_VERSION,
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "machine": machine(),
        "seeds_per_class": args.seeds,
        "layers": {
            "reconcile": "Engine.reconcile at injection, or a reconcile InvariantError later in the season",
            "controls": "Engine.control_report breaks or open statement at injection",
            "certificate": "shadow.certify struck at injection (includes control breaks plus shadow_nav)",
            "verify": "database-free Store.verify core: replay tape and script, compare journal digest",
        },
        "not_done": "mutation testing (mutmut) over journal, series, shadow, broker, administrator",
        "summary": result["summary"],
        "faults": result["faults"],
    }
    text = json.dumps(doc, indent=2)
    print(json.dumps(doc["summary"], indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        name = f"{doc['measured_at'][:10]}-B5-{doc['commit'].replace('+', '_')}.json"
        (args.out / name).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out / name}")
    per = result["summary"]["per_class"].values()
    clean_ok = result["summary"]["clean"]["flagged_checkpoints"] == 0
    return 0 if clean_ok and all(r["independent"] == r["n"] for r in per) else 1


if __name__ == "__main__":
    raise SystemExit(main())
