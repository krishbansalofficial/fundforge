"""Ending-card facts in the outcome: scenario, max drawdown, and post-run generator reveals (never before the end)."""

import hashlib
import json
from decimal import ROUND_HALF_EVEN
from decimal import Decimal as D
from fractions import Fraction

import pytest

from fundforge import store
from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.terminal import snapshot

P = {"pm": "ana", "mp": "ben"}
REVEALS = ("seed_commitment", "stressed_days", "generated_days")


def engine(scenario: str, variant: str = "base") -> Engine:
    e = Engine(store._tape(scenario, variant))
    e.advance()
    return e


def finish(e: Engine) -> Engine:
    while not e.finished():
        e.advance()
    return e


@pytest.mark.parametrize(("values", "expected"), [
    (["100", "110", "99", "105", "88"], "0.200000"),  # peak 110, trough 88; the 99 dip (0.1) is smaller
    (["100", "101", "102"], "0.000000"),  # never below the running peak
    (["3", "2"], "0.333333"),  # 1/3 at 6dp
    (["3", "1"], "0.666667"),  # 2/3 rounds up
    (["8", "7.9999995"], "0.000000"),  # 0.0000000625 rounds to zero at 6dp
    (["1", "0.9999975"], "0.000002"),  # exactly 0.0000025: HALF_EVEN keeps the even digit
])
def test_max_drawdown_is_peak_to_trough_on_closes(values, expected):
    e = engine("case1")
    e.close_values = [D(v) for v in values]
    assert e.max_drawdown() == expected


def test_close_values_are_fund_nav_per_unit_after_every_business_close(monkeypatch):
    seen = []
    original = Engine._close

    def spy(self):
        original(self)
        seen.append(Fraction(sum(s.net for s in self.series)) / Fraction(sum(s.units for s in self.series)))
    monkeypatch.setattr(Engine, "_close", spy)
    e = finish(engine("case1"))
    closes = sum(1 for ev in e.tape.events if ev.phase == "CLOSE")
    assert len(e.close_values) == closes + 1 and len(seen) == closes
    assert all(abs(Fraction(v) - x) < Fraction(1, 10**20) for v, x in zip(e.close_values[1:], seen, strict=True))
    assert e.close_values[0] == D(100)  # warm start: every series opens at 100 per unit
    worst, peak = Fraction(0), Fraction(100)
    for v in seen:
        peak = max(peak, v)
        worst = max(worst, 1 - v / peak)
    exact = (D(worst.numerator) / D(worst.denominator)).quantize(D("0.000001"), rounding=ROUND_HALF_EVEN)
    assert e.outcome()["max_drawdown"] == str(exact) and exact > 0


@pytest.mark.parametrize("scenario", ["case1", "case1-controls", "case1-settlement"])
def test_authored_outcomes_name_the_scenario_and_reveal_nothing_generated(scenario):
    out = finish(engine(scenario)).outcome()
    assert out["scenario"] == scenario and not set(REVEALS) & set(out)


def test_generated_outcome_reveals_commitment_and_stressed_days_after_the_run():
    e = finish(engine(store.GENERATED, "seed:facts"))
    regimes = e.tape.raw["generator"]["regimes"]
    out = e.outcome()
    assert out["scenario"] == store.GENERATED and out["variant"] == "seed:facts"
    assert out["seed_commitment"] == hashlib.sha256(b"facts").hexdigest()
    assert out["stressed_days"] == sum(1 for _, r in regimes if r == "stressed")
    assert out["generated_days"] == len(regimes) > 0


def test_generator_reveals_never_reach_a_pre_finish_view_terminal_or_outcome():
    e = engine(store.GENERATED, "seed:leak-facts")
    s = Session(e, P)
    secret = e.tape.raw["generator"]["seed_commitment"]
    k = 0
    while not s.e.finished():
        assert not set(REVEALS) & set(s.e.outcome())  # the outcome the balance gate and branches read
        for role, user in P.items():
            text = json.dumps([s.view(user), snapshot(s.e, role)])
            assert secret not in text and not any(name in text for name in REVEALS)
        for user in P.values():
            s.handle(user, f"r{k}-{user}", {"type": "ready", "version": s.version})
        k += 1
    final = s.view("ana")["outcome"]
    assert final["seed_commitment"] == secret and final["stressed_days"] >= 0
