"""Anomaly lane checks: clean books pass the controls, injections are balanced, controls and features behave.

These run on a few generated families so they stay fast. The full metrics come from scripts/train_anomaly.py.
"""

import random
from functools import lru_cache

import numpy as np
import pytest

from fundforge_ml import worlds
from fundforge_ml.anomaly import build
from fundforge_ml.anomaly_controls import CONTROLS, replay
from fundforge_ml.anomaly_data import KINDS, Game, inject, simulate
from fundforge_ml.anomaly_features import featurize

EXPECTED = {
    "wrong_date_fee": {"broker_fee_date", "administrator_fee_date"},
    "balanced_wrong_cash": {"broker_cash"},
    "phantom_position": {"shadow_valuation"},
    "duplicate_settlement": {"settlement_identity", "broker_cash"},
    "stale_mark": {"shadow_valuation"},
    "statement_break": {"broker_cash"},
}


@lru_cache(maxsize=1)
def game() -> Game:
    for i in range(10):
        try:
            return simulate(f"anom-{i}", worlds.variant_names()[0])
        except worlds.WorldRejected:
            continue
    raise AssertionError("no accepted family among anom-0..9")


def test_clean_books_pass_every_control():
    assert replay(game().rows, game().evidence) == ()


@pytest.mark.parametrize("kind", KINDS)
def test_injections_are_balanced_so_double_entry_never_flags_them(kind):
    res = inject(game(), kind, random.Random(f"t|{kind}"), "t")
    if res is None:
        pytest.skip(f"{kind} not applicable to this family")
    rows, footprint = res
    assert footprint
    assert "journal_integrity" not in {f.control for f in replay(rows, game().evidence)}


@pytest.mark.parametrize("kind", KINDS)
def test_each_kind_is_caught_by_the_control_built_for_it(kind):
    res = inject(game(), kind, random.Random(f"t|{kind}"), "t")
    if res is None:
        pytest.skip(f"{kind} not applicable to this family")
    rows, _footprint = res
    flagged = {f.control for f in replay(rows, game().evidence)}
    assert flagged & EXPECTED[kind], (kind, flagged)
    assert flagged <= set(CONTROLS)


def test_injection_is_deterministic_for_the_same_seed():
    a = inject(game(), "phantom_position", random.Random("same"), "x")
    b = inject(game(), "phantom_position", random.Random("same"), "x")
    assert a == b


def test_features_read_only_rows_posted_on_or_before_their_date():
    g = game()
    cutoff = g.evidence.calendar[len(g.evidence.calendar) // 2]
    later = [r for r in g.rows if r.posted_date > cutoff]
    assert later, "need postings after the cutoff to test the as-of rule"
    full, keys = featurize(g.rows, g.evidence.calendar)
    truncated, _ = featurize(tuple(r for r in g.rows if r.posted_date <= cutoff), g.evidence.calendar)
    keep = [k for k, (_, d) in enumerate(keys) if d <= cutoff]
    assert np.array_equal(full[keep], truncated[keep])


def test_build_produces_labelled_rows_for_clean_and_injected_copies():
    corpus, accounting = build([f"anom-{i}" for i in range(4)], 1)
    assert corpus.X.shape[0] == len(corpus.y) == len(corpus.kind) == len(corpus.split) == corpus.flags.shape[0]
    assert corpus.flags.shape[1] == len(CONTROLS)
    assert corpus.y.sum() > 0
    assert set(corpus.kind) <= {"clean", *KINDS}
    clean = corpus.kind == "clean"
    assert not corpus.y[clean].any()
    assert not corpus.flags[clean].any()
    assert accounting["accepted_families"] >= 1
