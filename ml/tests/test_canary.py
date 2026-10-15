"""Future-information canary (DECISIONS.md, 13 Oct 2026).

Plant a unique headline on a late tape event, play the whole Case1 run through the real Session,
and read both partners' observations at every barrier. The sentinel must be absent from every
observation before its event is processed. As a positive control it must appear afterwards, which
proves the scan can see a leak if one existed. No hidden-truth key may appear before the debrief.
"""

import dataclasses
import json
from pathlib import Path

import pytest
from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.tape import PHASES, load

from fundforge_ml.contracts import observe

FIXTURE = Path(__file__).parents[2] / "fixtures" / "case1.json"
SENTINEL = "CANARY-7f3c1e-future-headline"
USERS = {"pm": "ana", "mp": "ben"}


def _planted(variant: str):
    tape = load(FIXTURE, variant)
    events = list(tape.events)
    # the last public mark of the run: as far in the future as possible from the opening
    i = max(k for k, ev in enumerate(events) if ev.phase == "PUBLIC_MARK")
    events[i] = dataclasses.replace(events[i], headline=SENTINEL, headline_code="canary")
    return dataclasses.replace(tape, events=tuple(events)), events[i]


def _order(ev) -> tuple:
    return ev.date, PHASES.index(ev.phase)


@pytest.mark.parametrize("variant", ["base", "rally"])
def test_future_headline_never_reaches_an_observation_early(variant):
    tape, planted = _planted(variant)
    e = Engine(tape)
    e.advance()
    s = Session(e, USERS)
    before = after = 0
    k = 0
    while not s.e.finished():
        processed = _order(s.e.ev) >= _order(planted)
        for user in USERS.values():
            text = json.dumps(observe(s, user), default=str)
            if processed:
                after += SENTINEL in text
            else:
                before += 1
                assert SENTINEL not in text, f"future headline visible at day {s.e.ev.day} {s.e.ev.phase}"
        k += 1
        s.handle("ana", f"ra{k}", {"type": "ready"})
        s.handle("ben", f"rb{k}", {"type": "ready"})
    final = json.dumps(observe(s, "ana"), default=str)
    after += SENTINEL in final
    assert before > 0, "no observation was taken before the planted event"
    assert after > 0, "positive control failed: the sentinel never became visible, so the scan proves nothing"
