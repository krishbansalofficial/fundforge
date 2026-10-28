"""Smoke tests for the Stage 1 evaluation helpers in scripts/eval_ppo.py (needs the train group)."""

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sb3_contrib")
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import eval_ppo


def _rows(reward, labels):
    r = np.asarray(reward, dtype=float)
    return {"reward": r, "score": r * 100, "label": np.asarray(labels, dtype=object)}


def test_report_pairs_worlds_and_counts_random_non_wins():
    rows = {
        "ppo": _rows([[3, 2, 1], [3, 2, 2]], [["WIN"] * 3] * 2),
        "random": _rows([[1, 2, 0], [1, 1, 0]], [["WIN", "WIN", "SURVIVAL"], ["WIN", "SURVIVAL", "SURVIVAL"]]),
        "wait": _rows([[0, 0, 0]], [["SURVIVAL"] * 3]),
    }
    r = eval_ppo.report(rows)
    assert set(r["compare"]) == {"ppo_vs_random", "ppo_vs_wait"}
    assert r["compare"]["ppo_vs_wait"]["x_better_worlds"] == 3
    assert r["policies"]["random"]["labels"] == {"WIN": 3, "SURVIVAL": 3}
    assert r["policies"]["ppo"]["runs"] == 2 and r["policies"]["ppo"]["worlds"] == 3
    nw = r["random_not_win"]
    assert nw["n_worlds"] == 3
    assert nw["share_worlds_any_run"] == pytest.approx(2 / 3)
    assert nw["share_worlds_all_runs"] == pytest.approx(1 / 3)
    assert nw["share_episodes"] == pytest.approx(3 / 6)


def test_gate_and_play_block_on_one_world():
    level, seed, split, failures = eval_ppo.gate(("base", "ppo-0"))
    assert (level, seed) == ("base", "ppo-0") and split in ("train", "val", "test")
    assert all(":" in f for f in failures)  # failures are recorded per variant, never dropped
    ws = [("ppo-1", "base")]
    with ThreadPoolExecutor(2) as pool:
        out = eval_ppo.play_block(
            pool, "pm", "base", ws, {"random": ("random", [(None, 0), (None, 1)]), "wait": ("wait", [(None, 0)])}
        )
    assert out["random"]["reward"].shape == (2, 1) and out["wait"]["label"][0, 0] in ("WIN", "SURVIVAL", "DISTRESS")
