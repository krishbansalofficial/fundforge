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
from typing import Any

from .asof import AsOfError, AsOfTape, Observation
from .broker import validate_statements
from .money import D

Margin = dict[str, dict[str, Decimal]]  # {"initial"|"maintenance": {"long"|"short": rate}}

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


def _money(v: object, where: str) -> Decimal:
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
    raw: dict[str, Any]
    events: tuple[MarketEvent, ...]
    digest: str

    @property
    def instruments(self) -> list[str]:
        return list(self.raw["instruments"])

    @property
    def macro(self) -> AsOfTape:
        """Published indicator prints with revisions; times are scenario days."""
        return macro_tape(self.raw)

    def margin(self, day: int) -> Margin:
        row = [m for m in self.raw["margin_schedule"] if m["from_day"] <= day][-1]
        return {k: {s: D(v) for s, v in row[k].items()} for k in ("initial", "maintenance")}


def macro_tape(raw: dict[str, Any]) -> AsOfTape:
    try:
        return AsOfTape(tuple(Observation(o["instrument"], o["event_time"], o["available_at"], o["revision"],
                                          _money(o["value"], "macro.value")) for o in raw.get("macro", [])))
    except (AsOfError, KeyError, TypeError) as exc:
        raise TapeError(f"macro: {exc}") from exc


def load(path: str | Path, variant: str | None = None) -> Tape:
    return compile_tape(json.loads(Path(path).read_text(encoding="utf-8")), variant)


def variants(raw: dict[str, Any]) -> list[str]:
    return ["base", *sorted(raw.get("variants", {}))]


def compile_tape(raw: dict[str, Any], variant: str | None = None) -> Tape:
    """Materialize the tape. A variant replaces overrides that match its (day, event) keys and appends others;
    players never learn which variant they are in until the debrief."""
    if variant not in (None, "base"):
        if variant not in raw.get("variants", {}):
            raise TapeError(f"unknown variant {variant!r}")
        v = raw["variants"][variant]
        keys = {(o["day"], o["event"]) for o in v["overrides"]}
        raw = {**raw, "overrides": [o for o in raw["overrides"] if (o["day"], o["event"]) not in keys] + v["overrides"],
               "public_notices": raw["public_notices"] + v.get("public_notices", []), "variant": variant}
    syms = raw["instruments"]
    if len(set(syms)) != len(syms):
        raise TapeError("duplicate instrument id")
    dflt = raw["defaults"]
    base_mark = _money(dflt["mark"], "defaults.mark")
    base_vol = dflt["volume"]
    cal = raw["calendar"]
    try:
        validate_statements(raw.get("broker_statements", []), cal["start_day"], cal["end_day"])
    except ValueError as exc:
        raise TapeError(f"broker_statements: {exc}") from exc
    macro_tape(raw)
    research = raw["research"]
    assignments = research.get("assignments", {})
    if (set(assignments) != set(research["topics"])
            or any(a.get("role") not in ("pm", "mp") or a.get("location") not in
                   ("research", "risk", "broker", "backoffice", "lp") for a in assignments.values())
            or type(research.get("budget_per_role")) is not int or research["budget_per_role"] < 1):
        raise TapeError("research requires role/location assignments and a positive per-role budget")
    rc, off = raw["borrow"]["recall"], raw["borrow"]["replacement_offer"]
    opening_loans = {f"L-open-{s}": s for s, q in raw["opening"]["fund"]["positions"].items() if q < 0}
    if rc.get("loan_id") not in opening_loans or opening_loans[rc["loan_id"]] != rc["sym"]:
        raise TapeError("recall must name an opening loan for its instrument")
    if (off.get("old_loan_id") != rc["loan_id"] or off["sym"] != rc["sym"]
            or not isinstance(off.get("new_loan_id"), str) or not off["new_loan_id"]
            or off["new_loan_id"] in opening_loans):
        raise TapeError("replacement must name the recalled loan and a unique new loan")
    known_loans = {*opening_loans, off["new_loan_id"]}
    rate_keys = set()
    for change in raw["borrow"].get("rate_changes", []):
        key = (change["day"], change["loan_id"])
        if (change["loan_id"] not in known_loans or key in rate_keys
                or not cal["start_day"] <= change["day"] < cal["end_day"]):
            raise TapeError("invalid or duplicate loan rate change")
        _money(change["rate"], "borrow.rate_changes.rate")
        rate_keys.add(key)
    day1 = date.fromisoformat(cal["day1"])
    if day1.weekday() != 0:
        raise TapeError("day1 must be a Monday")

    seen: set[tuple[tuple[int, str], str, str]] = set()
    by_key: dict[tuple[int, str], dict[str, Any]] = {}
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
    events: list[MarketEvent] = []
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
