from decimal import Decimal

import pytest

from fundforge.asof import AsOfError, AsOfTape, Observation


def obs(sym: str, t: int, avail: int, rev: int, v: str) -> Observation:
    return Observation(sym, t, avail, rev, Decimal(v))


TAPE = AsOfTape((
    obs("GDP", 10, 12, 0, "2.1"),   # first print two events late
    obs("GDP", 10, 20, 1, "1.7"),   # corrected at 20
    obs("GDP", 11, 13, 0, "2.4"),
    obs("CPI", 10, 10, 0, "3.0"),
))


def test_view_holds_only_what_was_published_by_the_clock() -> None:
    assert TAPE.value("GDP", 10, 11) is None  # happened, not yet published
    assert TAPE.value("GDP", 10, 12) == Decimal("2.1")
    assert TAPE.value("GDP", 10, 19) == Decimal("2.1")  # the correction is still in the future
    assert TAPE.value("GDP", 10, 20) == Decimal("1.7")
    assert [(o.event_time, o.revision) for o in TAPE.known(15, "GDP")] == [(10, 0), (11, 0)]
    assert [(o.instrument, o.event_time) for o in TAPE.known(10)] == [("CPI", 10)]


def test_reading_later_never_changes_an_earlier_view() -> None:
    early = TAPE.known(15)
    TAPE.known(99)
    assert TAPE.known(15) == early
    assert all(o.available_at <= 15 for o in early)


@pytest.mark.parametrize("bad", [
    (obs("X", 5, 4, 0, "1"),),                              # published before it happened
    (obs("X", 5, 5, 0, "1"), obs("X", 5, 5, 1, "2")),       # correction not strictly later
    (obs("X", 5, 6, 0, "1"), obs("X", 5, 5, 1, "2")),       # correction earlier than the print
    (obs("X", 5, 5, 0, "1"), obs("X", 5, 7, 2, "2")),       # gap in revisions
    (obs("X", 5, 5, 0, "1"), obs("X", 5, 7, 0, "2")),       # duplicate revision
    (obs("X", 5, 5, 1, "1"),),                              # no first print
])
def test_malformed_revision_chains_are_refused(bad: tuple[Observation, ...]) -> None:
    with pytest.raises(AsOfError):
        AsOfTape(bad)
