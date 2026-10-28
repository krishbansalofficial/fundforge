"""Smoke test for scripts/bench_env.py: one gated world, tiny counts, output schema only (no speed claims)."""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("stable_baselines3")

from fundforge_ml import worlds

SCRIPT = Path(__file__).parents[1] / "scripts" / "bench_env.py"


def _load():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("bench_env", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_bench_schema():
    bench_env = _load()
    pair = next((f"base-{i}", "base") for i in range(10) if _gated(f"base-{i}"))
    out = bench_env.bench([pair], roles=("pm",), workers=[1], episodes=1, vec_steps=3, reps=2, warmup=1,
                          profile_episodes=1)
    (s,) = out["single_process"]
    assert s["role"] == "pm" and s["deterministic"] is True
    for block in (s, out["vectorised"][0]):
        for key in ("steps_per_s", "episodes_per_s"):
            st = block[key]
            assert len(st["samples"]) == 2 and st["min"] <= st["median"] <= st["max"]
    assert out["vectorised"][0]["steps_per_s"]["min"] > 0
    p = out["profile"]
    assert len(p["top10_cumulative"]) == 10 and 0 <= p["share_snapshot"] <= 1
    assert {"cpu", "logical_cores", "python", "commit", "packages"} <= bench_env.machine().keys()


def _gated(seed: str) -> bool:
    try:
        worlds.world(seed, "base")
        return True
    except worlds.WorldRejected:
        return False
