"""The backend's outbox rows satisfy the frozen event schema and leak no hidden truth.

Builds rows with the backend's pure ``fundforge.outbox`` from a full solo game (no database),
exactly as Store does per command, then validates every row against
ml/contracts/outbox_event.schema.json.
"""

import json
from pathlib import Path

import jsonschema
from fundforge import outbox
from helpers import game_rows

from fundforge_ml import worlds
from fundforge_ml.contracts import CONTRACT_VERSION, hidden_paths

SCHEMA = json.loads((Path(__file__).parents[1] / "contracts" / "outbox_event.schema.json").read_text("utf-8"))


def test_contract_versions_agree():
    assert outbox.CONTRACT_VERSION == CONTRACT_VERSION


def test_rows_match_the_schema_and_hide_truth_until_the_outcome():
    for variant in worlds.variant_names():
        rows = game_rows(variant)
        kinds = {r["kind"] for r in rows}
        assert {"command", "journal_entry", "notice", "outcome"} <= kinds
        validator = jsonschema.Draft202012Validator(SCHEMA)
        for r in rows:
            errors = sorted(validator.iter_errors(r), key=str)
            assert not errors, (r["kind"], [e.message for e in errors[:3]])
            if r["kind"] != "outcome":
                assert list(hidden_paths(r["payload"])) == [], r
        assert len({r["event_id"] for r in rows}) == len(rows)
        assert sum(r["kind"] == "outcome" for r in rows) == 1
