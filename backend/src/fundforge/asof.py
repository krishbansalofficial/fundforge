"""As-of tape (ROADMAP P4): ``(instrument, event_time, available_at, revision, value)`` observations.

A value describes ``event_time`` but can only be known from ``available_at``. Corrections append a
new revision with a strictly later ``available_at``; nothing is overwritten. A reader at ``clock``
sees, for each event, the highest revision already available, so a correction published later can
never leak into an earlier view. Times are integer event ordinals, like research ``available_at``.

Pure domain: no engine, journal or I/O imports. Not yet wired into a scenario.
"""

from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise


@dataclass(frozen=True)
class Observation:
    instrument: str
    event_time: int
    available_at: int
    revision: int  # 0 is the first print
    value: Decimal


class AsOfError(ValueError):
    pass


@dataclass(frozen=True)
class AsOfTape:
    observations: tuple[Observation, ...]

    def __post_init__(self) -> None:
        chains: dict[tuple[str, int], list[Observation]] = {}
        for o in self.observations:
            if o.available_at < o.event_time:
                raise AsOfError(f"{o.instrument}@{o.event_time} r{o.revision}: available before it happened")
            chains.setdefault((o.instrument, o.event_time), []).append(o)
        for (sym, t), chain in chains.items():
            chain.sort(key=lambda o: o.revision)
            if [o.revision for o in chain] != list(range(len(chain))):
                raise AsOfError(f"{sym}@{t}: revisions must be 0..n with no gaps or duplicates")
            if any(b.available_at <= a.available_at for a, b in pairwise(chain)):
                raise AsOfError(f"{sym}@{t}: each correction must become available strictly later")

    def known(self, clock: int, instrument: str | None = None) -> list[Observation]:
        """The latest available revision of every event visible at ``clock``, oldest event first."""
        best: dict[tuple[str, int], Observation] = {}
        for o in self.observations:
            if o.available_at > clock or (instrument is not None and o.instrument != instrument):
                continue
            key = (o.instrument, o.event_time)
            if key not in best or o.revision > best[key].revision:
                best[key] = o
        return sorted(best.values(), key=lambda o: (o.instrument, o.event_time))

    def value(self, instrument: str, event_time: int, clock: int) -> Decimal | None:
        """What ``clock`` knows about one event, or None if nothing is published yet."""
        hits = [o for o in self.known(clock, instrument) if o.event_time == event_time]
        return hits[0].value if hits else None
