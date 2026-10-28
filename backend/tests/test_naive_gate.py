"""HARD_VERSION gate: tier must depend on decisions, so naive (seeded random-valid) play may not win."""

import json
from decimal import Decimal
from pathlib import Path

from fundforge import balance
from fundforge.balance import accept, play_naive
from fundforge.generator import GEN_VERSION, HARD_VERSION, MARGIN_BUFFER, SCENARIO_VERSION, Spec, generate
from fundforge.tape import Tape, compile_tape

F = Path(__file__).parents[2] / "fixtures" / "case1.json"
SKELETON = json.loads(F.read_text(encoding="utf-8"))
HARD_ACCEPTED = "hard-0"  # measured: derisk_floor wins, naive play loses most runs
HARD_NAIVE_WINS = "hard-20"  # measured: derisk_floor wins and so does naive play


def hard(seed: str) -> Tape:
    return compile_tape(generate(seed, HARD_VERSION, SKELETON))


def test_naive_play_is_deterministic_per_world_and_seed():
    tape = hard(HARD_ACCEPTED)
    a, b = play_naive(tape, 0), play_naive(tape, 0)
    assert a["journal_digest"] == b["journal_digest"] and a["label"] == b["label"]
    assert len({play_naive(tape, k)["journal_digest"] for k in range(3)}) > 1  # seeds differ


def test_solvable_hard_world_is_accepted():
    ok, report = accept(hard(HARD_ACCEPTED))
    assert ok, report
    p = report["policies"]
    assert p["derisk_floor"]["label"] == "WIN"
    naive = [v["label"] for k, v in p.items() if k.startswith("naive_")]
    assert sum(x != "WIN" for x in naive) > balance.NAIVE_SEEDS // 2


def test_hard_world_naive_play_wins_is_rejected():
    ok, report = accept(hard(HARD_NAIVE_WINS))
    assert not ok and report["failures"] == ["naive_play_wins"], report


def test_naive_win_majority_rejects_and_minority_accepts(monkeypatch):
    tape = hard(HARD_ACCEPTED)
    labels: list[str] = []
    monkeypatch.setattr(balance, "play_naive", lambda t, k: {"label": labels[k], "score": "0"})
    labels[:] = ["WIN", "WIN", "SURVIVAL", "WIN", "SURVIVAL"]
    assert accept(tape)[1]["failures"] == ["naive_play_wins"]
    labels[:] = ["WIN", "WIN", "SURVIVAL", "SURVIVAL", "SURVIVAL"]
    assert accept(tape)[0]


def test_older_versions_keep_the_old_gate():
    """Rooms (GEN_VERSION) and SCENARIO_VERSION tapes are gated exactly as before: no naive runs."""
    for version in (GEN_VERSION, SCENARIO_VERSION):
        report = accept(compile_tape(generate("gate-1", version, SKELETON)))[1]
        assert not any(k.startswith("naive_") for k in report["policies"])
    authored = accept(compile_tape(SKELETON))[1]
    assert not any(k.startswith("naive_") for k in authored["policies"])


def test_hard_version_raises_the_stressed_margin_by_its_buffer():
    for seed in ("m1", "m2", "m3"):
        shift = Decimal(generate(seed, HARD_VERSION, SKELETON)["generator"]["scenario"]["margin_shift"])
        assert abs(shift * 100 - MARGIN_BUFFER[HARD_VERSION]) <= Spec().margin_points
        explicit = generate(seed, HARD_VERSION, SKELETON, Spec(margin_buffer_points=0))["generator"]["scenario"]
        assert abs(Decimal(explicit["margin_shift"]) * 100) <= Spec().margin_points
    # SCENARIO_VERSION tapes are byte-identical to before the buffer existed (digests recorded on 3c1a5ce)
    golden = {"s1": "6e1dfb35451e6e3a80ebf4021d6d284443fc5ba4abb67750571c297940b7d316",
              "m1": "6168c4754ece98de84d6a203176f3462835a309a292526850cc9d3055e55b717"}
    for seed, digest in golden.items():
        assert compile_tape(generate(seed, SCENARIO_VERSION, SKELETON)).digest == digest
