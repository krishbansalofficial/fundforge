"""Campaign pacing: skip-ready reaches the same journal as stepping every barrier, in a bounded number of rounds.

Case1's eight-round bound does not transfer: the campaign announces notices, planned committees and
incidents at more barriers (about one every two business days), and each one stops a skip. The bounds
below are the measured rounds plus a small margin, so a regression that makes the campaign chattier fails.
"""

import pytest

from fundforge import store
from fundforge.engine import Engine
from fundforge.governance import Session


def run(variant: str, skip: bool) -> tuple[str, int, str]:
    e = Engine(store._tape("campaign-v1", variant))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    rounds = 0
    while not s.e.finished():
        rounds += 1
        body = {"type": "ready", "skip": True} if skip else {"type": "ready"}
        s.handle("ana", f"a{rounds}", dict(body))
        s.handle("ben", f"b{rounds}", dict(body))
    return s.e.j.digest(), rounds, s.e.outcome()["label"]


@pytest.mark.parametrize(("variant", "max_skip_rounds"), [("base", 16), ("rally", 16), ("lean-company", 16),
                                                          ("tight-credit", 30)])
def test_skip_ready_matches_stepping_in_bounded_rounds(variant, max_skip_rounds):
    stepped_digest, stepped_rounds, stepped_label = run(variant, skip=False)
    skipped_digest, skipped_rounds, skipped_label = run(variant, skip=True)
    assert skipped_digest == stepped_digest
    assert skipped_label == stepped_label
    assert stepped_rounds == 60  # one ready pair per barrier: 30 business days, two execution barriers each
    assert skipped_rounds <= max_skip_rounds


def gate_accepted_seeds(count: int) -> list[str]:
    """The first ``count`` generated seeds that pass the real balance gate, so the room path is exercised."""
    seeds = []
    for i in range(1, 200):
        seed = f"seed:{i}-0"
        ok, _ = store._gate_seed(store.GENERATED, seed)
        if ok:
            seeds.append(seed)
            if len(seeds) == count:
                break
    return seeds


@pytest.mark.parametrize("seed", gate_accepted_seeds(12))
def test_skip_ready_matches_stepping_on_generated_seeds(seed):
    """Generated markets: the first 12 gate-accepted seeds; skip takes 5-8 rounds against 18 stepped (bound 10).

    Every seed measured ends in SURVIVAL, so this covers the digest equivalence; outcome variety is
    pinned in test_generated_endings.py.
    Gate-rejected seeds are excluded: a room never runs on one (store._room_variant).
    """
    stepped_digest, stepped_rounds, _ = run_generated(seed, skip=False)
    skipped_digest, skipped_rounds, _ = run_generated(seed, skip=True)
    assert skipped_digest == stepped_digest
    assert stepped_rounds == 18
    assert skipped_rounds <= 10


def run_generated(seed: str, skip: bool) -> tuple[str, int, str]:
    e = Engine(store._tape(store.GENERATED, seed))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    rounds = 0
    while not s.e.finished():
        rounds += 1
        body = {"type": "ready", "skip": True} if skip else {"type": "ready"}
        s.handle("ana", f"a{rounds}", dict(body))
        s.handle("ben", f"b{rounds}", dict(body))
    return s.e.j.digest(), rounds, s.e.outcome()["label"]
