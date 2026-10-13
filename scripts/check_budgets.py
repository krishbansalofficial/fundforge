"""Size budgets (P3 "bundle-size budget"): fail when a measured size exceeds scripts/budgets.json.

    python scripts/check_budgets.py --export export          # after scripts/export_game.sh
    python scripts/check_budgets.py --next frontend/.next    # after `npm run build`

--export checks the self-contained desktop builds (bytes on disk, .pck embedded).
--next checks each app route's first-load JavaScript: the root main files plus that route's chunks from
.next/app-build-manifest.json, gzip-compressed (level 9) and summed, deduplicated across the two lists.
That approximates Next's "First Load JS" column; it reads manifests instead of parsing build output,
whose format changes between Next versions. A route missing from the budget fails, so new pages get one.
Budgets were set about 20% above the first measurement; frame-time budgets live there too but are
checked locally by scripts/measure_frames.py, not here. Stdlib only.
"""

import argparse
import gzip
import json
import sys
from pathlib import Path

BUDGETS = Path(__file__).with_name("budgets.json")


def export_sizes(root: Path, names) -> dict[str, int]:
    return {n: (root / n).stat().st_size for n in names}


def first_load_js(next_dir: Path) -> dict[str, int]:
    root_files = json.loads((next_dir / "build-manifest.json").read_text())["rootMainFiles"]
    pages = json.loads((next_dir / "app-build-manifest.json").read_text())["pages"]
    return {route: sum(len(gzip.compress((next_dir / f).read_bytes(), 9))
                       for f in dict.fromkeys(root_files + chunks) if f.endswith(".js"))
            for route, chunks in pages.items()}


def over(measured: dict[str, int], limits: dict[str, int]) -> list[str]:
    return [f"{k}: {v:,} bytes > budget {limits[k]:,}" if k in limits else f"{k}: {v:,} bytes has no budget"
            for k, v in measured.items() if k not in limits or v > limits[k]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", type=Path, help="scripts/export_game.sh output directory")
    ap.add_argument("--next", type=Path, help="frontend/.next after a production build")
    a = ap.parse_args()
    budgets = json.loads(BUDGETS.read_text())
    failures = []
    for flag, key, measure in [(a.export, "export_bytes_max", lambda d, b: export_sizes(d, b)),
                               (a.next, "first_load_js_gzip_bytes_max", lambda d, _b: first_load_js(d))]:
        if flag is None:
            continue
        limits = budgets[key]
        measured = measure(flag, limits)
        for k, v in measured.items():
            print(f"{key} {k}: {v:,} (budget {limits.get(k, 0):,})")
        failures += over(measured, limits)
    for f in failures:
        print("OVER BUDGET", f, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    assert over({"a": 5, "b": 3}, {"a": 4, "b": 3}) == ["a: 5 bytes > budget 4"]
    assert over({"c": 1}, {}) == ["c: 1 bytes has no budget"]
    sys.exit(main())
