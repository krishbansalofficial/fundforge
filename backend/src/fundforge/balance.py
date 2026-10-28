"""Knowledge-free policy grid played through the real Session, and the tape acceptance gate.

A generated tape is accepted only if, in that single world: flattening the book on day 12 is
refused by the mandate (same journal as doing nothing), doing nothing does not win, every
line that handles the recall wins, and no seeded random-valid run (``play_naive``) wins, so the
tier depends on decisions rather than on any trade at all. Cross-world dominance stays a property of a tape *family*
(``tests/test_balance.py``). Plans are fixed in advance and read only public state (announced
margin calls), never the tape.
"""

import contextlib
from decimal import Decimal
from typing import Any

from . import bot
from .engine import CommandRejected, Engine
from .generator import Stream
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


NAIVE_VERSION = "naive-v1"  # draw stream of the seeded random-valid gate policy
NAIVE_SEEDS = 5
FRACTIONS = ((1, 4), (1, 2), (1, 1))  # the ML action space's reduce sizes (ceil of |position| x fraction)
LIVE = ("QUEUED", "PARTIALLY_FILLED")


def play_naive(tape: Tape, rng_seed: int) -> dict[str, Any]:
    """Seeded random-valid investment partner with bot:v1 as managing partner: an untrained agent.

    At each decision point (time skips quiet windows, as in solo play) it draws uniformly from: wait,
    or reduce one held name without a live order by a quarter, half or all of the position. Research
    moves are left out, so it trades at least as often as the ML random baseline.
    """
    e = Engine(tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "bot:mp"}, bots=frozenset({"mp"}))
    rng = Stream(f"{tape.digest}|{rng_seed}", NAIVE_VERSION)
    bot.act(s, "mp", "bot:mp", "n-open")
    k = 0
    while not e.finished():
        k += 1
        live = {x.sym for x in e.orders if x.status in LIVE}
        moves = [None, *((sym, f) for sym, q in sorted(e.pos.items()) if q and sym not in live for f in FRACTIONS)]
        move = moves[rng.integer(0, len(moves) - 1)]
        if move is not None:
            sym, (num, den) = move
            q = e.pos[sym]
            pid = f"n{k}"
            with contextlib.suppress(CommandRejected):  # a mandate refusal is an ordinary outcome
                s.handle("ana", pid, {"type": "propose", "package_id": pid, "orders": [
                    o(f"{pid}-{sym}", sym, "SELL" if q > 0 else "COVER", -(-abs(q) * num // den))]})
        bot.act(s, "mp", "bot:mp", f"n{k}-sign")
        try:
            s.handle("ana", f"r{k}", {"type": "ready", "skip": True})
        except CommandRejected:  # a package the bot refused is still pending: no skip
            s.handle("ana", f"r{k}", {"type": "ready"})
        bot.act(s, "mp", "bot:mp", f"n{k}-ready")
    return e.outcome()


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
    if not failures:  # only a world the designed lines win needs the costlier naive check
        for k in range(NAIVE_SEEDS):
            r = play_naive(tape, k)
            report["policies"][f"naive_{k}"] = {"label": r["label"], "score": r["score"]}
            if r["label"] == "WIN":
                failures.append("naive_play_wins")
                break
    return not failures, report
