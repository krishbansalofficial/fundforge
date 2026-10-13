"""The backend's outbox rows satisfy the frozen event schema and leak no hidden truth.

Builds rows with the backend's pure ``fundforge.outbox`` from a full solo game (no database),
exactly as Store does per command, then validates every row against
ml/contracts/outbox_event.schema.json.
"""

import hashlib
import json
from pathlib import Path

import jsonschema
from fundforge import bot, outbox
from fundforge.engine import Engine
from fundforge.governance import Session

from fundforge_ml import worlds
from fundforge_ml.contracts import CONTRACT_VERSION, hidden_paths

SCHEMA = json.loads((Path(__file__).parents[1] / "contracts" / "outbox_event.schema.json").read_text("utf-8"))


def _game_rows(variant: str) -> list[dict]:
    e = Engine(worlds.world(None, variant).tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "bot"}, bots=frozenset({"mp"}))
    rows, before, finished_before, k = [], outbox.counts(s), False, 0
    while not s.e.finished():
        k += 1
        start = s.version
        bot.act(s, "mp", "bot", f"b{k}")
        s.handle("ana", f"r{k}", {"type": "ready", "version": s.version})
        bot.act(s, "mp", "bot", f"c{k}")
        for seq in range(start + 1, s.version + 1):
            entry = s.log[seq - 1]
            head = hashlib.sha256(f"{seq}".encode()).hexdigest()
            rows += outbox.rows_for("room-1", "rules-x", s, seq, entry, before, head, finished_before,
                                    last=seq == s.version)
            before = entry["after"]
        finished_before = s.e.finished()
    return rows


def test_contract_versions_agree():
    assert outbox.CONTRACT_VERSION == CONTRACT_VERSION


def test_rows_match_the_schema_and_hide_truth_until_the_outcome():
    for variant in worlds.variant_names():
        rows = _game_rows(variant)
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
