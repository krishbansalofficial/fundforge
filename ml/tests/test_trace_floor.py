"""scripts/trace_ppo_vs_floor.py: its derisk_floor replay is the gate's line, and the overlap metrics are right."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("sb3_contrib")
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import trace_ppo_vs_floor as t
from fundforge.balance import play


def test_trace_plan_replays_balance_play_exactly():
    tape = t.build("ppo-12", "hard", "base").tape
    out, tr = t.trace_plan(tape, t.FLOOR)
    assert out["journal_digest"] == play(tape, t.FLOOR)["journal_digest"]
    s = t.summarize(tr, t.windows(tape))
    assert s["first_derisk"]["day"] == 12 and s["first_derisk"]["phase"] == "EXEC_A"
    assert {d for d, _ in s["acts"]} <= {12, 14}


def test_compare_timing_and_jaccard():
    def ep(window, acts):
        return {"first_derisk": window and {"window": window}, "acts": acts, "daily_gross": {12: 1.0, 13: 0.5}}

    floor = ep(3, [(12, "reduce:A"), (12, "reduce:B")])
    c = t.compare(ep(4, [(12, "reduce:A"), (13, "reduce:B")]), floor)
    assert c["first_derisk_window_gap"] == 1 and c["timing_match_pm1"]
    assert c["jaccard_day_type"] == pytest.approx(1 / 3, abs=1e-4) and c["jaccard_symbols"] == 1.0
    assert c["gross_mean_abs_diff"] == 0.0
    assert not t.compare(ep(None, []), floor)["timing_match_pm1"]  # never de-risking is not a match
