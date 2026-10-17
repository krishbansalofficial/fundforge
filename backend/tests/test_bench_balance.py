"""B6 script: Wilson arithmetic against hand-worked cases, verdict logic, and a small real run."""

import importlib.util
from decimal import Decimal
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "bench_balance.py"
spec = importlib.util.spec_from_file_location("bench_balance", SCRIPT)
assert spec and spec.loader
b6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b6)


def test_wilson_matches_hand_worked_cases():
    # k=5, n=10, z=1.96: p=0.5, z^2=3.8416, centre 0.5+0.19208=0.69208,
    # half 1.96*sqrt(0.025+0.009604)=0.3646021..., denominator 1.38416
    # -> (0.69208-0.3646021)/1.38416=0.236589..., (0.69208+0.3646021)/1.38416=0.763410...
    assert b6.wilson(5, 10) == (Decimal("0.2365"), Decimal("0.7635"))
    # k=0: lower 0, upper (z^2/n)/(1+z^2/n) = 3.8416/13.8416 = 0.27754...
    assert b6.wilson(0, 10) == (Decimal("0.0000"), Decimal("0.2776"))
    # k=n: lower n/(n+z^2) = 10/13.8416 = 0.72246..., upper 1
    assert b6.wilson(10, 10) == (Decimal("0.7224"), Decimal("1.0000"))


def _table(wins):
    return {p: b6.rates(["WIN"] * w + ["SURVIVAL"] * (20 - w)) for p, w in wins.items()}


def test_verdict_flags_a_dominant_degenerate_policy():
    designed = {p: 2 for p in b6.DESIGNED}
    bad = b6.verdict(_table({**designed, "passive": 20, "flatten_d12": 0}))
    assert bad["pass"] is False and bad["dominant_degenerate"] == ["passive"]
    # overlapping intervals are not dominance
    close = b6.verdict(_table({**designed, "passive": 5, "flatten_d12": 0}))
    assert close["pass"] is True and close["dominant_degenerate"] == []


def test_score_balance_shares_margins_ties_and_verdict():
    lines = ("a", "b", "c")
    # a best on 18, b on 1, one three-way tie; a beats the next best by 10 bps
    scores = [{"a": "10", "b": "0", "c": "-5"}] * 18 + [{"a": "0", "b": "3", "c": "1"}, {"a": "1", "b": "1", "c": "1"}]
    sb = b6.score_balance(scores, lines)
    a = sb["lines"]["a"]
    assert (a["k"], a["n"], a["share"], sb["ties"]) == (18, 20, "0.9000", 1)
    assert a["wilson95"] == [str(x) for x in b6.wilson(18, 20)] and Decimal(a["wilson95"][0]) > Decimal("0.5")
    assert Decimal(a["margin_bps"]["median"]) == 10 and Decimal(a["margin_bps"]["min"]) == -3
    assert Decimal(sb["lines"]["b"]["margin_bps"]["max"]) == 2 and sb["lines"]["c"]["k"] == 0
    assert sb["pass"] is False and sb["dominant"] == ["a"]
    # an even split passes
    a1, b1, c1 = ({"a": "1", "b": "0", "c": "0"}, {"a": "0", "b": "1", "c": "0"}, {"a": "0", "b": "0", "c": "1"})
    even = [a1] * 8 + [b1] * 6 + [c1] * 6
    assert b6.score_balance(even, lines)["pass"] is True
    # a majority whose interval still reaches below 0.5 is not a failure: 12/20 -> lower bound ~0.39
    assert b6.score_balance([a1] * 12 + even[8:16], lines)["pass"] is True
    assert b6.quantile([Decimal(x) for x in (4, 1, 3, 2)], Decimal("0.5")) == Decimal("2.5")


def test_run_over_a_few_seeds_is_consistent_with_the_gate():
    result = b6.run(4)
    rows = result["seeds"]
    assert len(rows) == 4 and result["ungated"]["n"] == 4
    for r in rows:
        assert r["labels"]["flatten_d12"] == r["labels"]["passive"]
        if r["accepted"]:
            assert all(r["labels"][p] == "WIN" for p in b6.DESIGNED)
    acc = result["accepted"]
    if acc:
        assert acc["n"] == sum(r["accepted"] for r in rows) and acc["verdict"]["pass"]
        assert sum(t["k"] for t in acc["score_balance"]["lines"].values()) + acc["score_balance"]["ties"] == acc["n"]
    for r in rows:  # replayed outcomes agree with the gate's scores
        assert all(r["outcomes"][p]["excess_bps"] == r["scores"][p] or r["labels"][p] != "WIN" for p in b6.DESIGNED)
