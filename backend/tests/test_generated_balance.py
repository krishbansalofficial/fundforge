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
