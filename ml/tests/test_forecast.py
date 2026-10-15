"""Forecast features: terminal parity, leak canary, Bayes ceiling parity, family split and metrics."""

import random
from decimal import Decimal
from fractions import Fraction

import numpy as np
import pytest
from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.terminal import snapshot

from fundforge_ml import forecast, worlds
from fundforge_ml.contracts import split_of

SEED = "forecast-test-1"


def _all_rows(gen_seed: str) -> list[dict]:
    """Every print the world will ever publish, including future ones and later revisions."""
    raw = worlds.world(gen_seed, "base", gate=False).tape.raw
    return [{"series": o["instrument"], "period_day": o["event_time"], "published_day": o["available_at"],
             "revision": o["revision"], "value": o["value"]} for o in raw["macro"]]


def test_rows_and_posterior_match_the_seat_terminal_in_a_real_session():
    w = worlds.world(SEED, "base", gate=False)
    e = Engine(w.tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    checked, k = 0, 0
    while not s.e.finished():
        for role in ("pm", "mp"):
            term = snapshot(s.e, role)
            rows = forecast.macro_rows(w.tape, s.e.ev.day)
            assert term["macro"] == rows
            if rows:
                _, post = forecast.bayes(rows, s.e.ev.day)
                shown = Decimal(term["regime"]["posterior"]["stressed"])
                assert abs(Decimal(post) - shown) <= Decimal("0.0000005")
                checked += 1
        k += 1
        s.handle("ana", f"a{k}", {"type": "ready"})
        s.handle("ben", f"b{k}", {"type": "ready"})
    assert checked > 0


@pytest.mark.parametrize("gen_seed", [SEED, "forecast-test-2", "forecast-test-3"])
def test_canary_future_prints_never_change_features(gen_seed):
    """Shuffle, rewrite and advance every not-yet-published print: features at the as-of day must not move."""
    full = _all_rows(gen_seed)
    rng = random.Random(gen_seed)
    days = sorted({r["published_day"] for r in full})
    moved = 0
    for as_of in range(days[0], days[-1] + 1):
        honest = forecast.features([r for r in full if r["published_day"] <= as_of], as_of)
        tampered = []
        for r in full:
            if r["published_day"] > as_of:
                # a wild future value, and an extra future revision that would win if it leaked
                tampered.append({**r, "value": "99.9"})
                tampered.append({**r, "revision": r["revision"] + 5, "value": "0.1"})
                moved += 1
            else:
                tampered.append(r)
        rng.shuffle(tampered)
        assert np.array_equal(forecast.features(tampered, as_of), honest), f"future print leaked at day {as_of}"
        if forecast.known(full, as_of):
            assert forecast.bayes(tampered, as_of) == forecast.bayes(full, as_of)
    assert moved > 0
    # positive control: changing an already-published print does change the features
    last = max(days)
    newest = forecast.known(full, last)[-1]
    published = [{**r, "value": "10.0"} if r is newest else r for r in full]
    assert not np.array_equal(forecast.features(published, last), forecast.features(full, last))


def test_samples_carry_labels_only_outside_the_features_and_split_by_family():
    samples = forecast.world_samples(SEED)
    assert samples and {s.seed_family for s in samples} == {worlds.world(SEED, "base", gate=False).seed_family}
    assert {s.split for s in samples} == {split_of(samples[0].seed_family)}
    for s in samples:
        assert s.x.shape == (3 * forecast.WINDOW + 1,) and s.y in (0, 1)
        assert s.period_day < s.as_of
        # the exact filter never gives zero probability to the true regime
        assert (s.bayes > 0) if s.y else (s.bayes < 1)


def test_metrics_on_known_values():
    p, y = np.array([1.0, 0.0, 0.5, 0.5]), np.array([1, 0, 1, 0])
    assert forecast.brier(p, y) == 0.125
    assert forecast.ece(p, y) == 0.0
    assert forecast.ece(np.array([0.9, 0.9]), np.array([0, 0])) == pytest.approx(0.9)
    assert forecast.log_loss(np.array([0.5]), np.array([1])) == pytest.approx(np.log(2))
    s = forecast.score(p, y, p, ["a", "a", "b", "b"])
    assert s["gap_brier"] == 0 and s["mean_abs_to_bayes"] == 0 and s["worlds"] == 2
    # binary Brier is half of research.brier's two-state score
    from fundforge.research import brier as two_state
    assert two_state({"calm": Decimal("0.3"), "stressed": Decimal("0.7")}, "calm") == 2 * Fraction(49, 100)
