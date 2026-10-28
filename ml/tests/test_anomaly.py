"""Anomaly features: deterministic, fixed length, blind to hidden truth; a gross planted fault stands out."""

from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest
from fundforge.engine import Engine
from fundforge.tape import load

from fundforge_ml import anomaly

CASE1 = Path(__file__).parents[2] / "fixtures" / "case1.json"


class _NoTape:
    def __getattr__(self, name: str) -> None:
        raise AssertionError(f"book_state read the tape ({name})")


def _season() -> tuple[Engine, list[dict]]:
    """Inaction season on Case1: the book state at every barrier; the engine is returned at season end, books[-1]."""
    e = Engine(load(CASE1))
    e.advance()
    books = []
    while not e.finished():
        books.append(anomaly.book_state(e))
        e.advance()
    books.append(anomaly.book_state(e))
    return e, books


def test_features_deterministic_and_fixed_length():
    _, a = _season()
    _, b = _season()
    xa = [anomaly.features(x) for x in a]
    assert all(x.shape == (len(anomaly.FEATURE_NAMES),) for x in xa)
    assert all(np.isfinite(x).all() for x in xa)
    assert all(np.array_equal(x, anomaly.features(y)) for x, y in zip(xa, b, strict=True))
    assert len(set(anomaly.FEATURE_NAMES)) == len(anomaly.FEATURE_NAMES)


def test_no_hidden_truth_reaches_features():
    e, _ = _season()
    e.tape = _NoTape()  # the tape holds future events; book_state must not touch it
    book = anomaly.book_state(e)
    assert set(book) == anomaly.BOOK_KEYS
    assert all(len(entry) == 3 for entry in book["entries"])  # entity, date, postings: no memo
    for leak in ("variant", "params", "class", "tape", "memo", "controls"):
        with pytest.raises(KeyError):
            anomaly.features({**book, leak: "x"})


def _planted() -> tuple[np.ndarray, np.ndarray]:
    e, books = _season()
    clean = np.array([anomaly.features(b) for b in books])
    big = Decimal("20000000.00")
    e._post("planted", ("collateral", big), ("debt", -big))  # balanced, unsupported, gross
    return clean, anomaly.features(anomaly.book_state(e))


def test_planted_gross_fault_scores_above_every_clean_checkpoint():
    clean, faulty = _planted()
    score = anomaly.max_abs_z(clean)
    # A training row's max |z| is at most sqrt(n - 1) (Samuelson's inequality); the planted fault is far beyond it.
    assert score(clean).max() <= np.sqrt(len(clean) - 1) + 1e-9 < score(faulty)[0]


def test_isolation_forest_saturates_outside_the_training_range():
    """Documents a limitation, not a goal: the season-end state is already at the edge of the clean range, so the
    planted $20m fault lands in the same leaves and scores like the clean season end (see ml/results/anomaly.json)."""
    ensemble = pytest.importorskip("sklearn.ensemble")
    clean, faulty = _planted()
    model = ensemble.IsolationForest(n_estimators=200, random_state=0).fit(clean[:-1])
    clean_end, faulty_end = -model.score_samples(np.vstack([clean[-1], faulty]))
    assert abs(faulty_end - clean_end) < 0.02
