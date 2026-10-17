"""Anomaly detection on the books: build the labelled ledger dataset, fit, evaluate, write results JSON.

Run from ml/:
    uv run python scripts/train_anomaly.py --families 200 --per-kind 3

Families are generated worlds (seed ``anom-<n>``) accepted by the balance gate; rejected seeds are listed
with their failure codes. Splits are by seed family (fundforge_ml.contracts.split_of). Models are fitted on
clean train rows only; thresholds on validation; every metric in the output is on test families.
"""

import argparse
import json
import time
from pathlib import Path
from typing import Any

from fundforge_ml.anomaly import run

DEFAULT_OUT = Path(__file__).parents[1] / "results" / "anomaly.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", type=int, default=200)
    ap.add_argument("--per-kind", type=int, default=3)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    t0 = time.perf_counter()
    seeds = [f"anom-{i}" for i in range(args.families)]
    result: dict[str, Any] = run(seeds, args.per_kind)
    result["config"] = {
        "families_requested": args.families,
        "injections_per_kind_per_family": args.per_kind,
        "seed_prefix": "anom",
        "kinds": [
            "wrong_date_fee",
            "balanced_wrong_cash",
            "phantom_position",
            "duplicate_settlement",
            "stale_mark",
            "statement_break",
        ],
    }
    result["reproduce"] = (
        f"cd ml && uv run python scripts/train_anomaly.py --families {args.families} --per-kind {args.per_kind}"
    )
    result["total_seconds"] = round(time.perf_counter() - t0, 1)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.out} in {result['total_seconds']}s")


if __name__ == "__main__":
    main()
