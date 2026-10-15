"""Session.handle's rollback snapshot: an independent full copy, tape shared by reference."""

import copy
import io
import pickle
from pathlib import Path

import pytest

from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session, canonical, restore, snapshot
from fundforge.tape import load

F = Path(__file__).parents[2] / "fixtures" / "case1.json"


def _mid_game() -> Session:
    e = Engine(load(F, "base"))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    for k in range(6):
        s.handle("ana", f"ra{k}", {"type": "ready"})
        s.handle("ben", f"rb{k}", {"type": "ready"})
    return s


def test_restore_matches_deepcopy_and_shares_only_the_tape():
    s = _mid_game()
    tape = s.e.tape
    state = (s.e, s.packages, s.ready, s.turnover, s.clock, s.chat)
    via_pickle = restore(snapshot(state, tape), tape)
    via_deepcopy = copy.deepcopy(state, {id(tape): tape})
    assert via_pickle[0].tape is tape
    assert via_pickle[0] is not s.e and via_pickle[0].j is not s.e.j
    assert via_pickle[0].j.digest() == via_deepcopy[0].j.digest() == s.e.j.digest()
    assert via_pickle[0].nav() == s.e.nav()
    assert canonical(via_pickle[1:]) == canonical(via_deepcopy[1:])
    via_pickle[0].advance()  # mutating the copy must not touch the live engine
    assert s.e.j.digest() == via_deepcopy[0].j.digest()


def test_rejected_command_rolls_back_to_identical_state():
    s = _mid_game()
    tape = s.e.tape
    before = canonical(s.view("ana")), s.e.j.digest(), s.version
    with pytest.raises(CommandRejected):
        s.handle("ana", "bad", {"type": "ticket", "order_id": "x", "sym": "ALTO", "side": "BUY", "qty": 10**9})
    assert (canonical(s.view("ana")), s.e.j.digest(), s.version) == before
    assert s.e.tape is tape  # restored state still shares the one pinned tape


def test_unknown_persistent_id_is_refused():
    class Bad(pickle.Pickler):
        def persistent_id(self, obj):
            return "other" if obj == "x" else None

    buf = io.BytesIO()
    Bad(buf).dump(["x"])
    with pytest.raises(pickle.UnpicklingError):
        restore(buf.getvalue(), object())
