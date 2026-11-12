"""Generated worlds reach every ending label through real Session commands, not only SURVIVAL.

Pinned gate-accepted seeds (measured with scripts/scan_generated_endings.py, 12 Nov 2026): in each, the
de-risk line wins, doing nothing survives (forced recall), and adding long and short risk every day while
never curing ends in DISTRESS (broker collateral shortfalls; NAV stays positive). On all 84 accepted
GEN_VERSION seeds in seed:1-0..seed:199-0 and all 95 accepted HARD_VERSION seeds in hard-0..hard-199 the
same three labels held for these three lines.
"""

import contextlib
import json
from pathlib import Path
from typing import Any

import pytest

from fundforge import balance, store
from fundforge.engine import CommandRejected, Engine
from fundforge.generator import HARD_VERSION, generate
from fundforge.governance import Session
from fundforge.tape import Tape, compile_tape

SKELETON = json.loads((Path(__file__).parents[2] / "fixtures" / "case1.json").read_text(encoding="utf-8"))
LEVER_BOTH = [("BEAM", "BUY", 25000), ("DART", "SHORT", 5000)]  # proposed at every EXEC_A; never cures


def run(tape: Tape, plan: dict[Any, Any], daily: list[tuple[str, str, int]] | None = None) -> Session:
    e = Engine(tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    k = 0
    while not s.e.finished():
        k += 1
        nxt = s.e.next_event()
        assert nxt is not None
        orders = list(plan.get((nxt.day, nxt.phase), []))
        if daily and nxt.phase == "EXEC_A":
            orders += [balance.o(f"d{k}{sym}", sym, side, q) for sym, side, q in daily]
        if orders:
            with contextlib.suppress(CommandRejected):  # a mandate refusal is an ordinary outcome
                d = s.handle("ana", f"p{k}", {"type": "propose", "package_id": f"p{k}", "orders": orders})
                s.handle("ben", f"s{k}", {"type": "sign", "package_id": f"p{k}", "digest": d["digest"]})
        s.handle("ana", f"ra{k}", {"type": "ready"})
        s.handle("ben", f"rb{k}", {"type": "ready"})
    return s


def replayed(s: Session) -> Session:
    e = Engine(s.e.tape)
    e.advance()
    r = Session(e, dict(s.partners))
    for item in s.log:
        r.handle("ana" if item["role"] == "pm" else "ben", item["key"], item["command"])
    return r


def gen(seed: str) -> Tape:
    ok, report = store._gate_seed(store.GENERATED, seed)
    assert ok, report
    return store._tape(store.GENERATED, seed)


def hard(seed: str) -> Tape:
    tape = compile_tape(generate(seed, HARD_VERSION, SKELETON))
    ok, report = balance.accept(tape)
    assert ok, report
    return tape


@pytest.mark.parametrize("tape_of", [lambda: gen("seed:1-0"), lambda: hard("hard-0")], ids=["gen-seed:1-0", "hard-0"])
@pytest.mark.parametrize(("line", "label"),
                         [("derisk_floor", "WIN"), ("passive", "SURVIVAL"), ("lever_both", "DISTRESS")])
def test_generated_world_reaches_label(tape_of, line, label):
    tape = tape_of()
    s = run(tape, {}, LEVER_BOTH) if line == "lever_both" else run(tape, balance.POLICIES[line])
    out = s.e.outcome()
    assert out["label"] == label, out
    if label == "DISTRESS":
        assert any("collateral shortfall" in u for u in out["unpaid"]) and s.e.nav() > 0
    if label == "SURVIVAL":
        assert out["forced"] and not out["unpaid"]
    s.e.reconcile()
    r = replayed(s)
    assert r.e.j.digest() == s.e.j.digest() == out["journal_digest"]
    assert r.e.outcome()["label"] == label
