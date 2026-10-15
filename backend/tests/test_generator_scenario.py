"""Scenario randomiser (SCENARIO_VERSION): old versions unchanged, draws bounded, texts match the tape."""

import hashlib
import json
from decimal import Decimal as D
from pathlib import Path

import pytest

from fundforge.balance import accept
from fundforge.engine import Engine
from fundforge.generator import GEN_VERSION, SCENARIO_VERSION, Spec, family_of, generate, split_of
from fundforge.tape import compile_tape

SKELETON = json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "case1.json").read_text(encoding="utf-8"))


def test_gen_version_still_reproduces_its_old_tapes():
    # digests recorded on b3a41c9, before the randomiser existed; GEN_VERSION output must not move
    for seed, json_sha, tape_digest in [
        (
            "golden-1",
            "e42aed8ff1c74b95eab059fbe3b4c7da27c0da74b3d38c61ce3c433edf0e9d88",
            "77bb37afc97386f34ded6df2a72b4a11468b960c38dd5fe3a9d2850c54af9fa4",
        ),
        (
            "golden-2",
            "ccc4f87950661bbba120e6baeec0d5204e0eba3b80256dffc16a108bdadcf671",
            "491aebc397186e9573aad381492de0cc933179e31709080d24771ccb881d6bdc",
        ),
    ]:
        raw = generate(seed, GEN_VERSION, SKELETON, Spec())
        assert hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest() == json_sha
        assert compile_tape(raw).digest == tape_digest
        assert "scenario" not in raw["generator"]


def test_scenario_version_is_deterministic_and_sensitive_to_seed():
    a = compile_tape(generate("s1", SCENARIO_VERSION, SKELETON))
    assert compile_tape(generate("s1", SCENARIO_VERSION, SKELETON)).digest == a.digest
    assert compile_tape(generate("s2", SCENARIO_VERSION, SKELETON)).digest != a.digest
    assert (
        compile_tape(generate("s1", SCENARIO_VERSION, SKELETON)).digest
        != compile_tape(generate("s1", GEN_VERSION, SKELETON)).digest
    )


@pytest.mark.parametrize("seed", [f"draw-{i}" for i in range(12)])
def test_draws_are_bounded_and_player_texts_match_the_tape(seed):
    raw = generate(seed, SCENARIO_VERSION, SKELETON)
    sc = raw["generator"]["scenario"]
    d = sc["crisis_day"]
    assert d in (15, 16, 17)
    assert any(o["day"] == d and o.get("headline_code") == "market_shock" for o in raw["overrides"])
    assert [m["from_day"] for m in raw["margin_schedule"]] == [12, d]
    assert D("93") <= D(sc["crisis_long_mark"]) <= D("97") and D("108") <= D(sc["crisis_short_mark"]) <= D("112")
    (units,) = sc["redemption_units"]
    assert units % 500 == 0 and 8000 <= units <= 12000
    notices = {
        n["code"]: n["text"] for n in raw["public_notices"] if n["code"] in ("margin_terms", "redemption_notice")
    }
    assert f"take effect day {d}." in notices["margin_terms"]
    assert f"{units:,}-unit" in notices["redemption_notice"]
    rally = raw["variants"]["rally"]
    assert all(o["day"] == d for o in rally["overrides"]) and f"day {d}" in rally["description"]
    assert all(D(p) > 0 for f in raw["market"]["funds"] for p in f["params"].values())


def test_randomised_worlds_play_through_the_engine_and_replay_exactly():
    def play(seed):
        e = Engine(compile_tape(generate(seed, SCENARIO_VERSION, SKELETON)))
        e.advance()
        while not e.finished():
            e.advance()
        return e.outcome()

    for seed in ("play-a", "play-b"):
        assert play(seed)["journal_digest"] == play(seed)["journal_digest"]


def test_rejected_seeds_carry_their_failure_reasons():
    rejected = []
    for i in range(10):
        ok, report = accept(compile_tape(generate(f"bench-{i}", SCENARIO_VERSION, SKELETON)))
        if not ok:
            rejected.append(report["failures"])
    assert rejected, "expected at least one rejection among ten seeds"
    assert all(
        f.endswith("_does_not_win") or f == "flatten_not_refused" or f == "passive_wins"
        for fails in rejected
        for f in fails
    )


def test_split_is_by_family_and_stable():
    assert family_of("fam#1") == family_of("fam#2") == family_of("fam") == "fam"
    assert split_of("fam#1") == split_of("fam#2") == split_of("fam")
    seeds = [f"seed-{i}" for i in range(400)]
    assert [split_of(s) for s in seeds] == [split_of(s) for s in seeds]
    counts = {k: sum(split_of(s) == k for s in seeds) for k in ("train", "val", "test")}
    assert counts["train"] > counts["val"] and counts["train"] > counts["test"] and counts["test"] > 0
    with pytest.raises(ValueError):
        split_of("#1")


def test_randomiser_bounds_are_validated():
    with pytest.raises(ValueError):
        Spec(rival_pct=100)
    with pytest.raises(ValueError):
        Spec(crisis_days=-1)
