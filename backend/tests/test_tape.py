import copy
import json
from datetime import date
from pathlib import Path

import pytest

from fundforge.money import D
from fundforge.tape import TapeError, compile_tape, load

CASE1 = Path(__file__).parents[2] / "fixtures" / "case1.json"


def raw():
    return json.loads(CASE1.read_text(encoding="utf-8"))


def test_case1_materializes_every_event_and_is_reproducible():
    t = load(CASE1)
    assert len(t.events) == 9 * 5 + 1  # days 12-20 x 5 phases + day21 OPEN_ADMIN
    assert t.events[0].date == date(2026, 1, 20) and t.events[-1].date == date(2026, 2, 2)
    assert all(set(e.marks) == set(t.instruments) for e in t.events)
    shock = next(e for e in t.events if (e.day, e.phase) == (16, "PUBLIC_MARK"))
    assert shock.marks["BEAM"] == D(95) and shock.marks["BRIN"] == D(110) and shock.marks["BOND"] == D(100)
    halted = [e for e in t.events if e.day == 20 and e.phase.startswith("EXEC")]
    assert all(e.volume["BEAM"] == 0 for e in halted)
    assert load(CASE1).digest == t.digest


@pytest.mark.parametrize(
    "mutate, msg",
    [
        (lambda r: r["overrides"][0]["marks"].__setitem__("ZZZZ", "1"), "unknown instrument"),
        (lambda r: r["overrides"][0]["marks"].__setitem__("ALTO", 95.0), "decimal strings"),
        (lambda r: r["overrides"][0]["marks"].__setitem__("ALTO", "NaN"), "invalid decimal"),
        (lambda r: r["overrides"][1]["volume"].__setitem__("BEAM", -5), "non-negative"),
        (lambda r: r["overrides"].append({"day": 30, "event": "EXEC_A"}), "no such event"),
        (lambda r: r["overrides"].append(copy.deepcopy(r["overrides"][1])), "duplicate"),
        (lambda r: r["instruments"].append("ALTO"), "duplicate instrument"),
    ],
)
def test_authoring_faults_are_rejected(mutate, msg):
    r = raw()
    mutate(r)
    with pytest.raises(TapeError, match=msg):
        compile_tape(r)
