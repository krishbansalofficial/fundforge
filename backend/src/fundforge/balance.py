"""Knowledge-free policy grid played through the real Session, and the tape acceptance gate.

A generated tape is accepted only if, in that single world: flattening the book on day 12 is
refused by the mandate (same journal as doing nothing), doing nothing does not win, and every
line that handles the recall wins. Cross-world dominance stays a property of a tape *family*
(``tests/test_balance.py``). Plans are fixed in advance and read only public state (announced
margin calls), never the tape.
"""

import contextlib
from decimal import Decimal
from typing import Any

from .engine import CommandRejected, Engine
from .governance import Session
from .tape import EXEC_PHASES, Tape

LONGS = {"ALTO": 30000, "COVE": 30000, "ELAN": 30000, "GALA": 30000, "IONA": 30000, "JUNO": 25000, "BEAM": 100000}
SHORTS = {"BRIN": 12500, "DART": 12500, "FENN": 12500, "HELI": 12500}
RECALL_LINES = ("derisk_floor", "S1_balanced", "cover_recall_only")


def o(i: str, s: str, side: str, q: int) -> dict[str, Any]:
    return {"order_id": i, "sym": s, "side": side, "qty": q}


POLICIES: dict[str, dict[Any, Any]] = {
    "passive": {},
    "flatten_d12": {(12, "EXEC_A"): [o(f"f{s}", s, "SELL", q) for s, q in LONGS.items()]
                    + [o(f"c{s}", s, "COVER", q) for s, q in SHORTS.items()]},
    "derisk_floor": {(12, "EXEC_A"): [o("b", "BEAM", "SELL", 50000), o("a", "ALTO", "SELL", 25000),
                                      o("c", "COVE", "SELL", 25000)],
                     (14, "EXEC_A"): [o("r", "BRIN", "COVER", 1250)]},
    "S1_balanced": {(14, "EXEC_A"): [o("r", "BRIN", "COVER", 1250), o("b", "BEAM", "SELL", 20000)]},
    # Answers margin calls when they are announced (no foreknowledge): since the endogenous market,
    # Halcyon's day-16 forced covering squeezes BRIN enough to put the minimal line into a margin call.
    "cover_recall_only": {(14, "EXEC_A"): [o("r", "BRIN", "COVER", 1250)], "cure": True},
}


def cure_qty(e: Engine, sym: str = "ALTO", k: int = 5) -> int:
    """Shares of a long to sell so maintenance relief is k x the announced deficit.

    Rival funds trade first at each execution event (market.py): in the base world Halcyon's
    forced unwind squeezes BRIN and knocks BEAM before our cure fills, roughly quadrupling the
    day-16 deficit, so a cure sized to the notice alone is forced out. ALTO is not crowded.
    """
    nxt = e.next_event()
    if e.margin_call is None or nxt is None:
        raise ValueError("no announced margin call to cure")
    rate: Decimal = e.tape.margin(nxt.day)["maintenance"]["long"]
    return int(e.margin_call * k / (rate * e.marks[sym])) + 1


def play(tape: Tape, plan: dict[Any, Any]) -> dict[str, Any]:
    e = Engine(tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    k = 0
    while not s.e.finished():
        k += 1
        nxt = s.e.next_event()
        if nxt is None:
            break
        orders = list(plan.get((nxt.day, nxt.phase), []))
        if plan.get("cure") and s.e.margin_call is not None and nxt.phase in EXEC_PHASES:
            orders.append(o(f"cure{k}", "ALTO", "SELL", cure_qty(s.e, k=2)))
        if orders:
            d = s.handle("ana", f"p{k}", {"type": "propose", "package_id": f"p{k}", "orders": orders})
            with contextlib.suppress(CommandRejected):
                s.handle("ben", f"s{k}", {"type": "sign", "package_id": f"p{k}", "digest": d["digest"]})
        s.handle("ana", f"ra{k}", {"type": "ready"})
        s.handle("ben", f"rb{k}", {"type": "ready"})
    return s.e.outcome()


def accept(tape: Tape) -> tuple[bool, dict[str, Any]]:
    """Play the grid on one tape; returns (accepted, per-policy label/score and failed checks)."""
    results = {name: play(tape, plan) for name, plan in POLICIES.items()}
    failures = []
    if results["flatten_d12"]["journal_digest"] != results["passive"]["journal_digest"]:
        failures.append("flatten_not_refused")
    if results["passive"]["label"] == "WIN":
        failures.append("passive_wins")
    failures += [f"{name}_does_not_win" for name in RECALL_LINES if results[name]["label"] != "WIN"]
    report = {"policies": {n: {"label": r["label"], "score": r["score"]} for n, r in results.items()},
              "failures": failures}
    return not failures, report
