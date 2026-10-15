import json
from collections import Counter
from pathlib import Path

import pytest

from fundforge_ml import contracts
from fundforge_ml.contracts import CONTRACT_VERSION, hidden_paths, split_of

SCHEMAS = Path(__file__).parents[1] / "contracts"


def test_split_is_deterministic_and_close_to_80_10_10():
    families = [f"case1/gen-2026.10.1/{i}" for i in range(20000)]
    first = [split_of(f) for f in families]
    assert first == [split_of(f) for f in families]
    share = {k: v / len(families) for k, v in Counter(first).items()}
    assert abs(share["train"] - 0.8) < 0.02
    assert abs(share["val"] - 0.1) < 0.01
    assert abs(share["test"] - 0.1) < 0.01


def test_split_does_not_depend_on_contract_version(monkeypatch):
    before = [split_of(f"fam{i}") for i in range(200)]
    monkeypatch.setattr(contracts, "CONTRACT_VERSION", "ml-contracts-9999.1.1")
    assert [split_of(f"fam{i}") for i in range(200)] == before


def test_split_rejects_empty_family():
    with pytest.raises(ValueError):
        split_of("")


def test_hidden_paths_finds_nested_keys():
    obj = {"fund": {"nav": "1"}, "rows": [{"ok": 1}, {"meta": {"variant": "rally"}}], "seed": "x"}
    assert sorted(hidden_paths(obj)) == ["$.rows[1].meta.variant", "$.seed"]


def test_schema_files_carry_the_contract_version():
    outbox = json.loads((SCHEMAS / "outbox_event.schema.json").read_text(encoding="utf-8"))
    assert outbox["properties"]["contract_version"]["const"] == CONTRACT_VERSION
    assert outbox["$id"].endswith(CONTRACT_VERSION)
    assert set(outbox["properties"]["audience"]["enum"]) == set(contracts.AUDIENCES)
    assert set(outbox["required"]) == set(outbox["properties"])
    dataset = json.loads((SCHEMAS / "dataset.schema.json").read_text(encoding="utf-8"))
    assert dataset["contract_version"] == CONTRACT_VERSION
    assert set(dataset["tables"]) == {"episodes", "decisions", "labels"}
    assert "obs" in dataset["tables"]["decisions"]["columns"]
    assert "obs" not in dataset["tables"]["labels"]["columns"]
