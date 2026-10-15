"""Build the offline dataset (ML_CONTRACTS.md section 4) through the real Session.

Run from ml/:
    uv run python scripts/build_dataset.py --out results/dataset --seeds 40

Seeds are ``seed-0000`` .. ``seed-NNNN``; each runs both authored variants under each policy.
Seeds the balance gate refuses are recorded in ``rejections.parquet``, not dropped. The output
directory is rebuilt from scratch, so a rerun never mixes partitions.
"""

import argparse
import json
import shutil
import time
from pathlib import Path

from fundforge_ml import dataset, worlds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/dataset"))
    ap.add_argument("--seeds", type=int, default=40, help="number of generated seeds to try")
    ap.add_argument("--policies", default=",".join(dataset.POLICIES))
    args = ap.parse_args()
    seeds = [f"seed-{i:04d}" for i in range(args.seeds)]
    started = time.perf_counter()
    tables = dataset.generate(seeds, worlds.variant_names(), args.policies.split(","))
    if args.out.exists():
        shutil.rmtree(args.out)
    sizes = dataset.write(tables, args.out)
    summary = {
        "seeds_tried": args.seeds,
        "variants": worlds.variant_names(),
        "policies": args.policies.split(","),
        "rows": sizes,
        "splits": {s: sum(1 for e in tables.episodes if e["split"] == s) for s in ("train", "val", "test")},
        "seconds": round(time.perf_counter() - started, 1),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
