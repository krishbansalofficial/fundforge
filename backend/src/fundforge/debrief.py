"""Completed-run causal replay; isolated, deterministic branches, no live writes."""

import copy
import hashlib
from typing import Any

from .engine import RULES_VERSION, CommandRejected, Engine
from .governance import CLOCK, Session, canonical
from .money import D, cents

OMITTABLE = {"ticket", "propose", "cancel", "research", "visit", "share_research", "accept_replacement", "set_reserve",
            "resolve_statement"}


def _state(e: Engine) -> dict[str, Any]:
    return {"day": e.ev.day, "phase": e.ev.phase, "nav": str(e.nav()),
            "headroom": str(cents(e.nav() - e.margin())), "recall_open": e.recall_open,
            "positions": dict(e.pos), "journal_digest": e.j.digest()}


def replay(source: Session, omit_seq: int | None = None) -> dict[str, Any]:
    """Omit one decision, then attempt the original suffix without new approvals.

    Ready/tick/review version tokens are rebound to the branch count; signed content
    digests and all economic commands remain unchanged. Rejections are explicit.
    The branch may end before the original: no new partner decisions are invented.
    """
    if not source.e.finished():
        raise CommandRejected("causal replay unlocks after the run is complete")
    if omit_seq is not None and (not 1 <= omit_seq <= len(source.log)
                                or source.log[omit_seq - 1]["command"]["type"] not in OMITTABLE):
        raise CommandRejected("select an eligible recorded decision to omit")
    e = Engine(source.e.tape)
    e.advance()
    branch = Session(e, dict(source.partners), source.bots)
    timeline = []
    rejected = []
    for seq, item in enumerate(source.log, 1):
        command = copy.deepcopy(item["command"])
        kind = command["type"]
        before = _state(branch.e)
        if seq == omit_seq:
            timeline.append({"seq": seq, "role": item["role"], "type": kind,
                             "status": "omitted", "before": before, "after": before})
            continue
        if omit_seq is not None and kind in ("ready", "tick", "resolve_statement"):
            command["expected_version" if kind == "tick" else "version"] = branch.version
        actor = CLOCK if item["role"] == "system" else branch.partners[item["role"]]
        try:
            branch.handle(actor, item["key"], command)
            status = "accepted"
        except CommandRejected as error:
            if omit_seq is None:
                raise  # baseline must replay exactly, never disguise divergence
            status = "rejected"
            rejected.append({"seq": seq, "type": kind, "reason": str(error)})
        if kind not in ("say", "set_speed"):
            after = _state(branch.e)
            timeline.append({"seq": seq, "role": item["role"], "type": kind, "status": status,
                             "before": before, "after": after,
                             "nav_delta": str(cents(branch.e.nav() - D(before["nav"]))),
                             "can_omit": kind in OMITTABLE})
    source_digest = source.e.j.digest()
    if omit_seq is None and (branch.e.j.digest() != source_digest or branch.version != source.version):
        raise RuntimeError("baseline replay diverged from source")
    identity = [RULES_VERSION, source.e.tape.digest, source_digest, source.log, omit_seq]
    return {"branch_id": hashlib.sha256(canonical(identity).encode()).hexdigest(),
            "source_version": source.version, "rules_version": RULES_VERSION, "tape_digest": source.e.tape.digest,
            "omitted_seq": omit_seq, "finished": branch.e.finished(), "state": _state(branch.e),
            "outcome": branch.e.outcome(), "source_outcome": source.e.outcome(),
            "nav_difference": str(cents(branch.e.nav() - source.e.nav())),
            "timeline": timeline, "rejected": rejected, "incidents": copy.deepcopy(branch.e.incident_events),
            "policy": "Completed-run counterfactual. Omit one decision, retry the original suffix, "
            "rebind ready/tick/review versions, preserve signatures and report rejected commands. "
            "No new decisions or approvals are invented; unfinished branches are not comparable ending scores."}
