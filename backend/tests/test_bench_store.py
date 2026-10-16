"""B2 smoke (scripts/bench_store.py) at reduced size against real Postgres. Skipped without DATABASE_URL."""

import os
import sys
from pathlib import Path

import pytest

DSN = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="needs DATABASE_URL (docker compose up -d db)")

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))


def test_store_bench_replays_deterministically_and_about_linearly():
    import bench_store

    # Both sizes finish case1's 18 windows, so the engine work is equal and the growth is per command.
    # (10 vs 50 is not a command-count comparison: the 10-command room covers only a few windows.)
    sizes = (50, 150)
    doc = bench_store.run(DSN, rooms=1, samples=3, warmup=0, sizes=sizes)  # raises on any digest mismatch
    assert doc["s2_outcome"] == ["WIN"]
    assert {"propose", "sign", "ready", "research", "accept_replacement", "tick"} <= set(doc["apply_ms"])
    # Generous bound: the fastest replay may grow at most 2x faster than command count. A per-command
    # cost that grew with room version would give about 9x (3 squared); linear is at most 3x.
    small, large = (doc["replay"][str(n)]["replay_ms"]["min"] for n in sizes)
    assert large / small <= 2 * sizes[1] / sizes[0], doc["replay"]
