"""Load an authored scenario and materialize every default into explicit event records.

A missing or malformed record is an authoring fault and raises ``TapeError``;
nothing is guessed. The materialized tape is hashed so a run can cite exactly
which inputs produced it.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from .money import D

PHASES = ("OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE")
EXEC_PHASES = ("EXEC_A", "EXEC_B")


class TapeError(ValueError):
    pass


@dataclass(frozen=True)
class MarketEvent:
    day: int
    date: date
    phase: str
    marks: dict[str, Decimal]
    volume: dict[str, int]
    headline: str | None = None
    headline_code: str | None = None


def business_date(day1: date, n: int) -> date:
    d, seen = day1, 1
    while seen < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            seen += 1
    return d


def _money(v, where):
    if not isinstance(v, str):
        raise TapeError(f"{where}: money/rates must be decimal strings, got {v!r}")
    try:
        d = D(v)
    except Exception as e:
        raise TapeError(f"{where}: invalid decimal {v!r}") from e
    if d < 0:
        raise TapeError(f"{where}: negative value {v!r}")
    return d


@dataclass(frozen=True)
class Tape:
    raw: dict
    events: tuple[MarketEvent, ...]
    digest: str

    @property
    def instruments(self) -> list[str]:
        return self.raw["instruments"]

    def margin(self, day: int) -> dict:
        row = [m for m in self.raw["margin_schedule"] if m["from_day"] <= day][-1]
        return {k: {s: D(v) for s, v in row[k].items()} for k in ("initial", "maintenance")}


def load(path: str | Path) -> Tape:
    return compile_tape(json.loads(Path(path).read_text(encoding="utf-8")))


def compile_tape(raw: dict) -> Tape:
    syms = raw["instruments"]
    if len(set(syms)) != len(syms):
        raise TapeError("duplicate instrument id")
    dflt = raw["defaults"]
    base_mark = _money(dflt["mark"], "defaults.mark")
    base_vol = dflt["volume"]
    cal = raw["calendar"]
    day1 = date.fromisoformat(cal["day1"])
    if day1.weekday() != 0:
        raise TapeError("day1 must be a Monday")

    seen = set()
    by_key = {}
    for i, o in enumerate(raw["overrides"]):
        key = (o["day"], o["event"])
        if o["event"] not in PHASES or not cal["start_day"] <= o["day"] < cal["end_day"]:
            raise TapeError(f"overrides[{i}]: no such event {key}")
        for field in ("marks", "volume"):
            for s, v in o.get(field, {}).items():
                if s not in syms:
                    raise TapeError(f"overrides[{i}]: unknown instrument {s!r}")
                if (key, field, s) in seen:
                    raise TapeError(f"overrides[{i}]: duplicate {field} for {s} at {key}")
                seen.add((key, field, s))
                if field == "volume" and (not isinstance(v, int) or isinstance(v, bool) or v < 0):
                    raise TapeError(f"overrides[{i}]: volume must be a non-negative integer, got {v!r}")
                if field == "marks":
                    _money(v, f"overrides[{i}].marks.{s}")
        by_key[key] = o
    for k, v in dflt.items():
        if k not in ("volume", "extra_borrow_inventory"):
            _money(v, f"defaults.{k}")

    marks = {s: base_mark for s in syms}
    events = []
    for day in range(cal["start_day"], cal["end_day"]):
        dt = business_date(day1, day)
        for phase in PHASES:
            o = by_key.get((day, phase), {})
            marks = {**marks, **{s: D(v) for s, v in o.get("marks", {}).items()}}
            vol = {s: base_vol for s in syms} | o.get("volume", {}) if phase in EXEC_PHASES else {}
            events.append(MarketEvent(day, dt, phase, dict(marks), vol, o.get("headline"), o.get("headline_code")))
    end = cal["end_day"]
    events.append(MarketEvent(end, business_date(day1, end), "OPEN_ADMIN", dict(marks), {}))

    canon = [[e.day, e.date.isoformat(), e.phase, {k: str(v) for k, v in e.marks.items()}, e.volume] for e in events]
    blob = json.dumps({"raw": raw, "events": canon}, sort_keys=True, separators=(",", ":"))
    return Tape(raw, tuple(events), hashlib.sha256(blob.encode()).hexdigest())
