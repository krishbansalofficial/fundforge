"""Seat-scoped live features folded from outbox events (ML_CONTRACTS.md section 3).

The same ``fold`` runs in batch (over Store.outbox rows) and streaming (over Kafka messages).
Every feature is order-independent (counts, maxima, set unions) and every event is deduplicated
by ``event_id``, so a stream read from offset 0, in any interleaving of topics and with
redeliveries, yields exactly the batch result. A seat's features read only ``public`` events and
that seat's own; ``internal`` and the partner's private events never contribute.
"""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from .contracts import SEATS, hidden_paths

FEATURE_VERSION = "stream-features-v1"
PHASES = ("OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE")
EPOCH = date(1970, 1, 1)


@dataclass
class SeatFeatures:
    room_id: str
    seat: str
    seen: set[str] = field(default_factory=set)
    commands_by_role: Counter[str] = field(default_factory=Counter)
    notices_by_code: Counter[str] = field(default_factory=Counter)
    incidents_by_code: Counter[str] = field(default_factory=Counter)
    watermark: tuple[int, int] = (0, -1)  # (day, phase index) of the latest event seen
    max_margin_deficit: Decimal = Decimal(0)
    research_revealed: set[str] = field(default_factory=set)
    outcome_label: str | None = None

    def snapshot(self) -> dict[str, Any]:
        """A comparable, JSON-friendly view (Decimal as string)."""
        return {"room_id": self.room_id, "seat": self.seat, "events": len(self.seen),
                "commands_by_role": dict(sorted(self.commands_by_role.items())),
                "notices_by_code": dict(sorted(self.notices_by_code.items())),
                "incidents_by_code": dict(sorted(self.incidents_by_code.items())),
                "watermark": list(self.watermark), "max_margin_deficit": str(self.max_margin_deficit),
                "research_revealed": sorted(self.research_revealed), "outcome_label": self.outcome_label,
                "version": FEATURE_VERSION}


def normalize(event: Mapping[str, Any]) -> dict[str, Any]:
    """Accept a Store row or a Debezium outbox-router message (date as days since epoch)."""
    ev = dict(event)
    if isinstance(ev.get("sim_date"), int):
        ev["sim_date"] = (EPOCH + timedelta(days=ev["sim_date"])).isoformat()
    ev["event_id"] = str(ev["event_id"])
    return ev


def fold(state: SeatFeatures, event: Mapping[str, Any]) -> SeatFeatures:
    ev = normalize(event)
    if ev["room_id"] != state.room_id or ev["audience"] not in ("public", state.seat):
        return state
    if ev["event_id"] in state.seen:  # redelivery or duplicate: no effect
        return state
    if ev["kind"] != "outcome" and list(hidden_paths(ev["payload"])):
        raise ValueError(f"hidden truth in a live event {ev['event_id']}")
    state.seen.add(ev["event_id"])
    state.watermark = max(state.watermark, (int(ev["day"]), PHASES.index(ev["phase"])))
    p = ev["payload"]
    if ev["kind"] == "command":
        state.commands_by_role[p["role"]] += 1
    elif ev["kind"] == "notice":
        state.notices_by_code[p["code"]] += 1
        if p["code"] == "margin_call" and "deficit" in p["refs"]:
            state.max_margin_deficit = max(state.max_margin_deficit, Decimal(p["refs"]["deficit"]))
        if p["code"] == "research_reveal":
            state.research_revealed.add(p["refs"]["topic"])
    elif ev["kind"] == "incident":
        state.incidents_by_code[p["code"]] += 1
    elif ev["kind"] == "outcome":
        state.outcome_label = p["label"]
    return state


def features(room_id: str, events: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Batch: both seats' features for one room."""
    states = {seat: SeatFeatures(room_id, seat) for seat in SEATS}
    for ev in events:
        for st in states.values():
            fold(st, ev)
    return {seat: st.snapshot() for seat, st in states.items()}
