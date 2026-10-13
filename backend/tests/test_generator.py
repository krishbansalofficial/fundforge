"""Seeded generator: deterministic, Decimal-only, authored crisis inputs untouched, valid tapes."""

import json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path

import pytest

from fundforge.generator import GEN_VERSION, Spec, Stream, commitment, generate
from fundforge.tape import compile_tape

SKELETON = json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "case1.json").read_text(encoding="utf-8"))


def test_same_seed_same_tape_and_different_seed_or_version_differs():
    a = compile_tape(generate("s1", GEN_VERSION, SKELETON))
    assert compile_tape(generate("s1", GEN_VERSION, SKELETON)).digest == a.digest
    assert compile_tape(generate("s2", GEN_VERSION, SKELETON)).digest != a.digest
    assert compile_tape(generate("s1", "gen-other", SKELETON)).digest != a.digest


def test_authored_overrides_survive_and_unauthored_days_move():
    raw = generate("s1", GEN_VERSION, SKELETON)
    assert raw["overrides"][:len(SKELETON["overrides"])] == SKELETON["overrides"]
    tape = compile_tape(raw)
    by = {(e.day, e.phase): e for e in tape.events}
    for o in SKELETON["overrides"]:
        for s, v in o.get("marks", {}).items():
            assert by[(o["day"], o["event"])].marks[s] == D(v)  # the day-16 shock is a fixed hidden input
    authored_days = {(o["day"], o["event"]) for o in SKELETON["overrides"] if "marks" in o}
    moved = [e for e in tape.events if e.phase == "PUBLIC_MARK" and (e.day, e.phase) not in authored_days]
    assert moved and all(any(m != D(SKELETON["defaults"]["mark"]) for m in e.marks.values()) for e in moved[:1])
    assert raw["generator"] == {**raw["generator"], "version": GEN_VERSION, "seed_commitment": commitment("s1")}
    assert "s1" not in json.dumps(raw)  # only the commitment, never the seed


def test_marks_are_exact_decimal_steps_with_bond_beta_zero():
    spec = Spec(factor_bp=200, idio_bp=0, switch_bp=0)
    raw = generate("s3", GEN_VERSION, SKELETON, spec)
    gen = raw["overrides"][len(SKELETON["overrides"]):]
    first = gen[0]["marks"]
    assert first["BOND"] == "100.000000"  # beta 0 and no idiosyncratic noise
    assert len({v for s, v in first.items() if s != "BOND"}) == 1  # one common factor, beta 1
    for g in gen:
        for v in g["marks"].values():
            assert isinstance(v, str) and D(v) > 0 and D(v) == D(v).quantize(D("0.000001"))


def test_stream_is_unbiased_in_range_and_rejects_bad_specs():
    rng = Stream("seed", GEN_VERSION)
    draws = [rng.integer(-2, 2) for _ in range(5000)]
    counts = Counter(draws)
    assert set(counts) == {-2, -1, 0, 1, 2} and all(900 < n < 1100 for n in counts.values())
    with pytest.raises(ValueError):
        rng.integer(3, 2)
    with pytest.raises(ValueError):
        Spec(factor_bp=4000, stress_multiplier=3)  # could wipe out a price in one step
    with pytest.raises(ValueError):
        Spec(switch_bp=10_001)


@pytest.mark.parametrize("seed", ["play-1", "play-2", "play-3"])
def test_generated_tapes_play_through_the_engine_and_replay_exactly(seed):
    from fundforge.engine import Engine

    def play():
        e = Engine(compile_tape(generate(seed, GEN_VERSION, SKELETON)))
        e.advance()
        while not e.finished():
            e.advance()
        return e

    a, b = play(), play()
    assert a.outcome()["journal_digest"] == b.outcome()["journal_digest"]
    assert a.outcome()["label"] in {"WIN", "SURVIVAL", "DISTRESS"}


def test_regime_switching_scales_the_factor_bound():
    calm = generate("r", GEN_VERSION, SKELETON, Spec(switch_bp=0))["generator"]["regimes"]
    flip = generate("r", GEN_VERSION, SKELETON, Spec(switch_bp=10_000))["generator"]["regimes"]
    assert {r for _, r in calm} == {"calm"}
    assert [r for _, r in flip][:4] == ["stressed", "calm", "stressed", "calm"]


def test_activity_index_never_changes_marks_and_revisions_are_closer_to_the_regime():
    plain = generate("m", GEN_VERSION, SKELETON, Spec(macro_revise_bp=0))
    raw = generate("m", GEN_VERSION, SKELETON, Spec(macro_revise_bp=10_000))
    assert raw["overrides"] == plain["overrides"]  # separate stream: prices are untouched
    regime = dict(map(tuple, raw["generator"]["regimes"]))
    for o in raw["macro"]:
        level = D("52.5") if regime[o["event_time"]] == "calm" else D("47.5")
        assert abs(D(o["value"]) - level) <= (D("0.5") if o["revision"] else D("4.0"))
        assert o["available_at"] == o["event_time"] + (3 if o["revision"] else 1)
    assert {o["revision"] for o in raw["macro"]} == {0, 1}
    with pytest.raises(ValueError):
        Spec(macro_lag=0)  # a same-day print would come before that day's mark


def test_terminal_shows_only_published_prints_and_revisions():
    from fundforge.engine import Engine
    from fundforge.terminal import snapshot

    raw = generate("leak", GEN_VERSION, SKELETON)
    e = Engine(compile_tape(raw))
    e.advance()
    revised_seen = False
    while not e.finished():
        shown = {m["period_day"]: m for m in snapshot(e)["macro"]}
        expect: dict[int, dict] = {}
        for o in raw["macro"]:
            prior = expect.get(o["event_time"], {"revision": -1})
            if o["available_at"] <= e.ev.day and o["revision"] >= prior["revision"]:
                expect[o["event_time"]] = o
        assert {d: (m["revision"], m["value"]) for d, m in shown.items()} == \
               {d: (o["revision"], o["value"]) for d, o in expect.items()}
        assert all(m["published_day"] <= e.ev.day for m in shown.values())
        revised_seen |= any(m["revision"] for m in shown.values())
        e.advance()
    assert revised_seen


def test_malformed_macro_is_an_authoring_fault():
    from fundforge.tape import TapeError

    raw = generate("bad", GEN_VERSION, SKELETON)
    first = raw["macro"][0]
    for broken in ({**first, "available_at": first["event_time"] - 1}, {**first, "revision": 2}, {**first, "value": 1}):
        with pytest.raises(TapeError):
            compile_tape({**raw, "macro": [broken]})
