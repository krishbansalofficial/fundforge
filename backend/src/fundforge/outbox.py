"""Transactional outbox rows.

Pure: builds the events one accepted command produced, from the session after it ran. Store
writes them in the same PostgreSQL transaction as the command and journal rows, so an event
exists exactly when its command does. Debezium relays the table to Kafka; Kafka is downstream
only and nothing in the game reads it back.

Each event's ``audience`` is fixed when it is emitted and never widened downstream:
commands, incidents and the outcome are ``public`` (both partners see them in the view);
journal entries are ``internal``; a notice is ``public`` unless it has an owner, in which case
it belongs to that seat (sharing research emits its own public notice).
"""

import uuid
from collections.abc import Mapping
from typing import Any

from .governance import Session

CONTRACT_VERSION = "ml-contracts-2026.10.1"  # must equal the ML lane contract version (checked by ml/tests)
NAMESPACE = uuid.UUID("6f3c1e2a-5b7d-4c8e-9a1f-0d2e3c4b5a69")


def event_id(room: str, seq: int, kind: str, idx: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{room}|{seq}|{kind}|{idx}"))


def rows_for(room: str, rules_version: str, s: Session, seq: int, log_entry: Mapping[str, Any],
             before: Mapping[str, Any], chain_head: str, finished_before: bool, last: bool) -> list[dict[str, Any]]:
    """Events for the command logged at ``seq``. ``before`` is the previous command's ``after`` counts."""
    e = s.e
    after = log_entry["after"]
    base = {"contract_version": CONTRACT_VERSION, "room_id": room, "seq": seq, "rules_version": rules_version,
            "tape_digest": e.tape.digest, "chain_head": chain_head}
    out: list[dict[str, Any]] = []

    def add(kind: str, audience: str, day: int, phase: str, sim_date: str, payload: dict[str, Any]) -> None:
        idx = len(out)
        out.append({**base, "event_id": event_id(room, seq, kind, idx), "idx": idx, "kind": kind,
                    "audience": audience, "day": day, "phase": phase, "sim_date": sim_date, "payload": payload})

    cmd = log_entry["command"]
    add("command", "public", log_entry["day"], log_entry["phase"], after["date"],
        {"role": log_entry["role"], "type": cmd["type"], "command": cmd})
    for x in e.j.entries[before["journal"]:after["journal"]]:
        add("journal_entry", "internal", log_entry["day"], log_entry["phase"], x.date, x.canonical())
    for n in e.notices[before["notices"]:after["notices"]]:
        add("notice", n["refs"].get("owner") or "public", n["day"], n["phase"], n["date"],
            {"code": n["code"], "kind": n["kind"], "refs": n["refs"], "text": n["text"]})
    for i in e.incident_events[before["incidents"]:after["incidents"]]:
        add("incident", "public", i["day"], i["phase"], after["date"],
            {"code": i["code"], "refs": i["refs"], "amounts": i["amounts"], "text": i["text"]})
    if last and e.finished() and not finished_before:
        add("outcome", "public", e.ev.day, e.ev.phase, e.ev.date.isoformat(), e.outcome())
    return out


def counts(s: Session) -> dict[str, Any]:
    """Current sizes, for the state a new command starts from (the room's opening entries and notices
    exist before the first command and are derivable from the pinned tape, so they emit no events)."""
    return {"journal": len(s.e.j.entries), "notices": len(s.e.notices), "incidents": len(s.e.incident_events)}
