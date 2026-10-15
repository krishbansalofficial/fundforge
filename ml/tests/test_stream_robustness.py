"""Robustness of the live feature builder (ML_PLAN day 10-13 tests): offset-0 replay, duplicate
delivery, consumer restart, and a game that runs with no consumer at all (Kafka stopped).

Feeds outbox rows directly; no broker, no database. The Kafka end-to-end run is
``scripts/kafka_e2e.py`` and needs the compose stack.
"""

import random
import sys

import pytest
from helpers import game_rows

from fundforge_ml import features, stream


@pytest.mark.parametrize("variant", ["base", "rally"])
def test_offset_zero_replay_reproduces_the_batch_features(variant):
    rows = game_rows(variant)
    batch = features.canonical(stream.features("room-1", rows)["pm"])
    for _ in range(2):  # two independent consumers, both starting at offset 0
        st = stream.SeatFeatures("room-1", "pm")
        for r in rows:
            stream.fold(st, r)
        assert features.canonical(st.snapshot()) == batch


def test_duplicate_delivery_changes_nothing():
    rows = game_rows("base")
    once = stream.features("room-1", rows)
    twice = stream.features("room-1", rows + rows)
    assert once == twice
    st = stream.SeatFeatures("room-1", "mp")
    for r in rows:
        stream.fold(st, r)
        before = st.snapshot()
        stream.fold(st, r)  # the same delivery again must be a no-op
        assert st.snapshot() == before


def test_consumer_restart_from_offset_zero_onto_partial_state_converges():
    """A consumer that crashed half way and restarted from offset 0 keeps its state and ends equal to batch."""
    rows = game_rows("rally")
    rng = random.Random(3)
    cut = len(rows) // 2
    st = stream.SeatFeatures("room-1", "mp")
    for r in rows[:cut]:
        stream.fold(st, r)
    replay = list(rows)
    rng.shuffle(replay)
    for r in replay:  # restart from offset 0, in a different interleaving
        stream.fold(st, r)
    assert st.snapshot() == stream.features("room-1", rows)["mp"]


def test_a_game_runs_and_verifies_with_no_consumer_and_no_kafka_client():
    """The engine, Session and outbox rows never depend on a stream consumer: with none running,
    the game finishes, and no Kafka client library was loaded to make that happen."""
    rows = game_rows("base")
    outcomes = [r for r in rows if r["kind"] == "outcome"]
    assert len(outcomes) == 1
    assert "confluent_kafka" not in sys.modules
    assert all(r["contract_version"] == outcomes[0]["contract_version"] for r in rows)
