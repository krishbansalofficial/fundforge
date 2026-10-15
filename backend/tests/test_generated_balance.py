"""The acceptance gate: generated tapes enter play only if the single-world balance checks pass."""

import json
from pathlib import Path

from fundforge.balance import accept
from fundforge.generator import GEN_VERSION, generate
from fundforge.tape import compile_tape, load

F = Path(__file__).parents[2] / "fixtures" / "case1.json"
SKELETON = json.loads(F.read_text(encoding="utf-8"))


def test_authored_worlds_pass_the_gate():
    for variant in ("base", "rally"):
        ok, report = accept(load(F, variant))
        assert ok, (variant, report)


def test_an_unwinnable_crash_is_rejected():
    def crash(o):
        if "marks" not in o:
            return o
        return {**o, "marks": {s: ("60" if v == "95" else "140" if v == "110" else v) for s, v in o["marks"].items()}}
    ok, report = accept(compile_tape({**SKELETON, "overrides": [crash(o) for o in SKELETON["overrides"]]}))
    assert not ok and any(f.endswith("_does_not_win") for f in report["failures"]), report


def test_gate_is_deterministic_for_a_generated_seed():
    tape = compile_tape(generate("gate-1", GEN_VERSION, SKELETON))
    assert accept(tape) == accept(compile_tape(generate("gate-1", GEN_VERSION, SKELETON)))


def test_room_seed_draw_retries_until_accepted_and_gives_up_bounded(monkeypatch):
    import pytest

    from fundforge import store
    from fundforge.engine import CommandRejected

    calls = []

    def gate(answers):
        def fake(tape):
            calls.append(tape.raw["variant"])
            ok = answers.pop(0)
            return ok, {"failures": [] if ok else ["passive_wins"], "policies": {}}
        return fake

    monkeypatch.setattr(store.balance, "accept", gate([False, False, True]))
    variant, record = store._draw_variant(store.GENERATED)
    assert variant == calls[-1] and variant.endswith("-2") and len(calls) == 3
    assert [a["accepted"] for a in record["attempts"]] == [False, False, True]
    assert record["attempts"][0] == {"accepted": False, "failures": ["passive_wins"]}
    assert "seed" not in json.dumps(record) and variant[5:] not in json.dumps(record)
    monkeypatch.setattr(store.balance, "accept", gate([False] * store.GENERATION_ATTEMPTS))
    with pytest.raises(CommandRejected, match="balanced market"):
        store._draw_variant(store.GENERATED)
    with pytest.raises(CommandRejected, match="seed variant"):
        store._tape(store.GENERATED, "base")
    authored, authored_gate = store._draw_variant("case1")
    assert authored in {"base", "rally"} and authored_gate == {}


def test_explicit_generated_seed_must_pass_the_same_gate(monkeypatch):
    """create_room(variant=...) cannot bypass the gate for generated rooms."""
    import pytest

    from fundforge import store
    from fundforge.engine import CommandRejected

    monkeypatch.setattr(store, "_gate_seed", lambda scenario, variant: (False, {"failures": ["passive_wins"]}))
    with pytest.raises(CommandRejected, match="balance gate"):
        store._room_variant(store.GENERATED, "seed:explicit-1")
    monkeypatch.setattr(store, "_gate_seed", lambda scenario, variant: (True, {"failures": [], "policies": {}}))
    variant, record = store._room_variant(store.GENERATED, "seed:explicit-1")
    assert variant == "seed:explicit-1" and record["rule"] == store.GATE_RULE
    assert store._room_variant("case1", "rally") == ("rally", {})


def test_acceptance_rate_is_pinned_over_a_fixed_seed_set():
    """Pins the measured default-spec acceptance (scripts/generator_acceptance.py, N=10, bench-0..9).

    If a generator or balance change moves these counts, re-measure with the script, update the pin
    and record the numbers in docs/PROGRESS.md. Do not change the pin to make a regression pass.
    """
    from collections import Counter

    from fundforge.generator import Spec

    accepted, failures = 0, Counter()
    for i in range(10):
        ok, report = accept(compile_tape(generate(f"bench-{i}", GEN_VERSION, SKELETON, Spec())))
        accepted += ok
        failures.update(report["failures"])
    assert accepted == 3, (accepted, failures)
    assert failures == Counter({"cover_recall_only_does_not_win": 7}), failures
