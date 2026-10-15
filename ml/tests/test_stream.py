"""Streaming features equal batch features under any interleaving and redelivery; seats stay isolated."""

import random

import pytest
from helpers import game_rows

from fundforge_ml import stream


@pytest.mark.parametrize("variant", ["base", "rally"])
def test_shuffled_redelivered_stream_equals_batch(variant):
    rows = game_rows(variant)
    batch = stream.features("room-1", rows)
    rng = random.Random(7)
    for _ in range(5):
        noisy = rows + rng.sample(rows, len(rows) // 3)  # redeliveries
        rng.shuffle(noisy)  # topics interleave arbitrarily
        assert stream.features("room-1", noisy) == batch


def test_seats_see_only_public_and_their_own_events():
    rows = game_rows("base")
    f = stream.features("room-1", rows)
    # the bot MP orders the borrow research: its evidence is MP-private until shared
    assert "borrow" in f["mp"]["research_revealed"]
    assert "borrow" not in f["pm"]["research_revealed"]
    visible = {s: {r["event_id"] for r in rows if r["audience"] in ("public", s)} for s in ("pm", "mp")}
    assert f["pm"]["events"] == len(visible["pm"]) and f["mp"]["events"] == len(visible["mp"])
    assert any(r["audience"] == "internal" for r in rows)  # journal entries exist but never count
    assert f["pm"]["outcome_label"] == f["mp"]["outcome_label"] is not None


def test_other_rooms_are_ignored_and_debezium_dates_are_normalized():
    rows = game_rows("base")
    other = [{**r, "room_id": "room-2", "event_id": r["event_id"] + "x"} for r in rows]
    as_debezium = [{**r, "sim_date": (stream.date.fromisoformat(r["sim_date"]) - stream.EPOCH).days} for r in rows]
    assert stream.features("room-1", rows + other) == stream.features("room-1", as_debezium)


def test_hidden_truth_in_a_live_event_is_refused():
    rows = game_rows("base")
    bad = {**next(r for r in rows if r["kind"] == "notice" and r["audience"] == "public")}
    bad["payload"] = {**bad["payload"], "refs": {"variant": "rally"}}
    with pytest.raises(ValueError, match="hidden truth"):
        stream.features("room-1", [bad])
