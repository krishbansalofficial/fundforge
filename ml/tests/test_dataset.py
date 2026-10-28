"""The offline dataset matches its contract, is split by family, and leaks neither seeds nor hidden truth."""

import json
from pathlib import Path

import polars as pl
import pytest

from fundforge_ml import dataset, worlds
from fundforge_ml.contracts import hidden_paths, split_of

SCHEMA = json.loads((Path(__file__).parents[1] / "contracts" / "dataset.schema.json").read_text("utf-8"))
SEEDS = [f"seed-{i:04d}" for i in range(6)]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dataset")
    tables = dataset.generate(SEEDS, worlds.variant_names(), dataset.POLICIES)
    sizes = dataset.write(tables, out)
    return tables, out, sizes


def test_tables_have_the_contract_columns(built):
    _, out, _ = built
    for name, spec in SCHEMA["tables"].items():
        assert set(spec["columns"]) <= set(dataset.read(out, name).columns), name
    assert set(dataset.read(out, "episodes").columns) == set(SCHEMA["tables"]["episodes"]["columns"])


def test_split_is_the_family_split_and_is_partitioned(built):
    tables, out, _ = built
    eps = dataset.read(out, "episodes")
    assert eps.height == len(tables.episodes) > 0
    # the split must equal the one training scripts use, split_of(World.seed_family), not a split of its hash
    fams = [worlds.world(s, v, gate=False).seed_family for s in [None, *SEEDS] for v in worlds.variant_names()]
    expected = {dataset.family_hash(f): split_of(f) for f in fams}
    for row in eps.iter_rows(named=True):
        assert row["split"] == expected[row["seed_family"]]
    assert {p.name for p in (out / "episodes").iterdir() if p.is_dir()} <= {"split=train", "split=val", "split=test"}


def test_keys_are_unique(built):
    _, out, _ = built
    d = dataset.read(out, "decisions")
    assert d.select(["episode_id", "seat", "step"]).is_unique().all()
    assert dataset.read(out, "episodes")["episode_id"].is_unique().all()


def test_no_seed_or_seed_text_is_written(built):
    tables, out, _ = built
    seeds_written = [p for p in out.rglob("*.parquet") if any(s.encode() in p.read_bytes() for s in SEEDS)]
    assert seeds_written == []
    assert all(e["seed_commitment"] and len(e["seed_commitment"]) == 64 for e in tables.episodes)


def test_hidden_truth_is_only_in_labels(built):
    _, out, _ = built
    feats = dataset.read(out, "features")
    assert not {"variant", "regime"} & set(feats.columns)
    labels = dataset.read(out, "labels")
    assert set(labels["label"].unique()) >= {"variant"}
    for v in dataset.read(out, "decisions")["obs"].to_list():
        assert list(hidden_paths(json.loads(v))) == []
    assert dataset.read(out, "features").height == dataset.read(out, "decisions").height


def test_gate_rejections_are_recorded_not_dropped(built):
    tables, out, _ = built
    rej = pl.read_parquet(out / "rejections.parquet")
    assert rej.height == len(tables.rejections)
    assert set(rej.columns) == {"seed_commitment", "variant", "failures"}


def test_rebuild_is_deterministic(built):
    tables, _, _ = built
    again = dataset.generate(SEEDS, worlds.variant_names(), dataset.POLICIES)
    assert [e["journal_digest"] for e in again.episodes] == [e["journal_digest"] for e in tables.episodes]
    assert [e["episode_id"] for e in again.episodes] == [e["episode_id"] for e in tables.episodes]
