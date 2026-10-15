"""Offline Polars features are byte-identical to the live stream fold, with no Kafka involved.

The live builder folds outbox rows one at a time (``stream.fold``); here the same rows, taken
straight from the backend's pure ``outbox.rows_for``, go through both builders. Equality is on
the canonical JSON string, so any difference in a count, a watermark, a Decimal or a list order fails.
"""

import copy
import json

import polars as pl
import pytest
from helpers import game_rows

from fundforge_ml import dataset, features, stream, worlds
from fundforge_ml.contracts import hidden_paths


@pytest.mark.parametrize("variant", worlds.variant_names())
def test_final_features_are_byte_identical_for_both_seats(variant):
    rows = game_rows(variant)
    live = stream.features("room-1", rows)
    ev = features.flatten(rows)
    offline = features.point_in_time(ev, features.at_end(ev, "room-1", ("pm", "mp")))
    assert offline.height == 2
    for r in offline.iter_rows(named=True):
        assert r["features"] == features.canonical(live[r["seat"]]), r["seat"]


@pytest.mark.parametrize("policy", dataset.POLICIES)
def test_features_at_every_decision_match_the_stream_prefix(policy):
    """Each decision's features equal the stream over exactly the events committed before it."""
    t = dataset.play(worlds.world(None, "rally"), policy)
    by_room = [e for e in t.events]
    ev = features.flatten(by_room)
    cut = features.point_in_time(ev, pl.DataFrame(t.cutoffs, schema=features.CUTOFF_SCHEMA))
    assert cut.height == len(t.cutoffs) > 0
    for c, row in zip(t.cutoffs, cut.iter_rows(named=True), strict=True):
        prefix = [e for e in by_room if e["seq"] <= c["as_of_seq"]]
        assert row["features"] == features.canonical(stream.features(c["room_id"], prefix)[c["seat"]]), c


def test_margin_deficit_is_the_numeric_maximum_not_the_lexical_one():
    """'999999.00' sorts above '1000000.50' as text; the feature must still report the Decimal maximum.
    Both amounts exceed the authored game's own largest margin call, so they set the maximum."""
    rows = game_rows("base")
    last = max(rows, key=lambda r: (r["seq"], r["idx"]))
    notice = next(r for r in rows if r["kind"] == "notice")
    extra = []
    for k, amount in enumerate(("999999.00", "1000000.50")):
        n = copy.deepcopy(notice)
        n.update(
            event_id=f"deficit-{k}",
            seq=last["seq"],
            day=last["day"],
            phase=last["phase"],
            audience="public",
            kind="notice",
        )
        n["payload"] = {"code": "margin_call", "kind": "alert", "refs": {"deficit": amount}, "text": "call"}
        extra.append(n)
    rows = rows + extra
    live = stream.features("room-1", rows)["pm"]
    assert live["max_margin_deficit"] == "1000000.50"
    ev = features.flatten(rows)
    offline = features.point_in_time(ev, features.at_end(ev, "room-1", ("pm",)))
    assert offline.item(0, "features") == features.canonical(live)


def test_outbox_rows_for_one_room_flatten_without_loss():
    rows = game_rows("base")
    ev = features.flatten(rows)
    assert ev.height == len(rows)
    assert set(ev["kind"].unique()) >= {"command", "journal_entry", "notice", "outcome"}


def test_hidden_truth_in_a_live_event_is_refused_offline_too():
    rows = game_rows("base")
    bad = {**next(r for r in rows if r["kind"] == "notice" and r["audience"] == "public")}
    bad["payload"] = {**bad["payload"], "refs": {"variant": "rally"}}
    with pytest.raises(ValueError, match="hidden truth"):
        features.flatten([bad])


def test_decision_observations_carry_no_hidden_truth():
    t = dataset.play(worlds.world(None, "base"), "random_valid")
    assert t.decisions
    for d in t.decisions:
        assert list(hidden_paths(json.loads(d["obs"]))) == [], d["step"]
