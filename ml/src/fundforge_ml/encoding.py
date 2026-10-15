"""Observation encoder: a partner's as-of view -> a fixed-length float vector.

Pure function of the view returned by ``contracts.observe`` plus public, fixed scenario facts
(instrument list, research topics, calendar), all of which a player sees from the opening.
It never reads the engine or the tape's future events. Money is read from decimal strings and
converted to float only here, for the model.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

ENCODER_VERSION = "obs-v1"
PHASES = ("OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE")
LIVE = ("QUEUED", "PARTIALLY_FILLED")


@dataclass(frozen=True)
class Layout:
    """Public facts that fix the vector's shape for one scenario."""

    instruments: tuple[str, ...]
    topics: tuple[str, ...]
    start_day: int
    end_day: int

    @property
    def size(self) -> int:
        return 2 + 1 + len(PHASES) + 14 + 4 * len(self.instruments) + 4 + 4 * len(self.topics) + 2 + 4


def _f(x: Any) -> float:
    return 0.0 if x is None else float(x)


def encode(view: Mapping[str, Any], layout: Layout, opening: Mapping[str, Any]) -> npt.NDArray[np.float32]:
    """``opening`` is the same seat's first observation of the run (opening NAV, marks, firm cash)."""
    out: list[float] = []
    role = view["role"]
    out += [1.0 if role == "pm" else 0.0, 1.0 if role == "mp" else 0.0]

    clock = view["clock"]
    span = max(1, layout.end_day - layout.start_day)
    out.append((clock["day"] - layout.start_day) / span)
    out += [1.0 if clock["phase"] == p else 0.0 for p in PHASES]

    f = view["fund"]
    nav = _f(f["nav"])
    open_nav = _f(opening["fund"]["nav"]) or 1.0
    per = nav if nav > 0 else open_nav
    margin_call = _f(f["margin_call"])
    out += [
        nav / open_nav - 1.0,
        _f(f["cash"]) / per, _f(f["collateral"]) / per, _f(f["debt"]) / per, _f(f["credit_left"]) / per,
        _f(f["reserve"]) / per, _f(f["long_mv"]) / per, _f(f["short_mv"]) / per,
        _f(f["gross"]), _f(f["net"]),
        _f(f["maintenance_req"]) / per, _f(f["initial_req"]) / per,
        margin_call / per, 1.0 if margin_call > 0 else 0.0,
    ]

    pos = {p["sym"]: p for p in view["positions"]}
    marks = view["marks"]
    open_marks = opening["marks"]
    live = {o["sym"] for o in view["orders"] if o["status"] in LIVE}
    for sym in layout.instruments:
        p = pos.get(sym)
        qty = p["qty"] if p else 0
        out += [
            _f(p["mv"]) / per if p else 0.0,
            _f(marks.get(sym)) / (_f(open_marks.get(sym)) or 1.0) - 1.0,
            (p["borrowed"] / abs(qty)) if p and qty else 0.0,
            1.0 if sym in live else 0.0,
        ]

    r = view["recall"]
    out += [1.0 if r["open"] else 0.0, 1.0 if r["offer_visible"] else 0.0,
            1.0 if r["replacement_accepted"] else 0.0, 1.0 if r["resolved_by"] else 0.0]

    research = view["research"]
    used = {u["topic"] for u in research["used"]}
    shared = set(research["shared"])
    seen = {n["refs"].get("topic") for n in research["evidence"]}
    mine = set(research["topics"])
    for t in layout.topics:
        out += [1.0 if t in mine else 0.0, 1.0 if t in used else 0.0,
                1.0 if t in shared else 0.0, 1.0 if t in seen else 0.0]

    firm = view["firm"]
    open_firm = _f(opening["firm"]["cash"]) or 1.0
    out += [_f(firm["cash"]) / open_firm - 1.0, _f(firm["payroll_payable"]) / open_firm]

    out += [
        sum(1 for p in view["packages"] if p["status"] == "PENDING_APPROVAL") / 4.0,
        sum(1 for o in view["orders"] if o["status"] in LIVE) / 8.0,
        len(view["notices"]) / 20.0,
        len(view["incident_events"]) / 10.0,
    ]
    vec = np.asarray(out, dtype=np.float32)
    if vec.shape != (layout.size,):
        raise AssertionError(f"encoder produced {vec.shape}, layout says {layout.size}")
    return vec


def layout_for(raw: Mapping[str, Any], topics: Sequence[str]) -> Layout:
    cal = raw["calendar"]
    return Layout(tuple(raw["instruments"]), tuple(topics), int(cal["start_day"]), int(cal["end_day"]))
