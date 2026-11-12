"""Which ending labels do scripted policies reach on gate-accepted generated worlds?

    cd backend && uv run python ../scripts/scan_generated_endings.py [N] [out.json]

Two populations, each filtered by the real gate (``balance.accept``):
  gen   ``store._tape(case1-generated, "seed:{i}-0")`` for i = 1..N-1 (what a generated room runs, GEN_VERSION)
  hard  ``compile_tape(generate("hard-{i}", HARD_VERSION, case1))`` for i = 0..N-1
Policies, all through the real Session: ``balance.POLICIES`` passive and derisk_floor, ``balance.play_naive``
seeds 0..4 (counted per episode), and three deliberately bad lines that add risk and never cure (BAD).
A measurement over fixed seed lists, not a probability claim. At most 4 processes.
"""

import contextlib
import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
from typing import Any

from fundforge import balance, store
from fundforge.engine import CommandRejected, Engine, InvariantError
from fundforge.generator import HARD_VERSION, generate
from fundforge.governance import Session
from fundforge.tape import Tape, compile_tape

SKELETON = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "case1.json").read_text(encoding="utf-8"))
# orders proposed at every EXEC_A (a mandate refusal is skipped); nothing is ever cured or covered
BAD = {
    "lever_long_daily": [("BEAM", "BUY", 25000)],
    "short_more_daily": [("DART", "SHORT", 5000), ("FENN", "SHORT", 5000), ("HELI", "SHORT", 5000)],
    "lever_both_daily": [("BEAM", "BUY", 25000), ("DART", "SHORT", 5000)],
}


def play_daily(tape: Tape, legs: list[tuple[str, str, int]]) -> dict[str, Any]:
    e = Engine(tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    k = 0
    while not s.e.finished():
        k += 1
        nxt = s.e.next_event()
        if nxt is not None and nxt.phase == "EXEC_A":
            with contextlib.suppress(CommandRejected):
                orders = [balance.o(f"d{k}{sym}", sym, side, q) for sym, side, q in legs]
                d = s.handle("ana", f"p{k}", {"type": "propose", "package_id": f"p{k}", "orders": orders})
                s.handle("ben", f"s{k}", {"type": "sign", "package_id": f"p{k}", "digest": d["digest"]})
        s.handle("ana", f"ra{k}", {"type": "ready"})
        s.handle("ben", f"rb{k}", {"type": "ready"})
    return s.e.outcome()


def tape_of(pop: str, i: int) -> Tape:
    if pop == "gen":
        return store._tape(store.GENERATED, f"seed:{i}-0")
    return compile_tape(generate(f"hard-{i}", HARD_VERSION, SKELETON))


def scan(job: tuple[str, int]) -> dict[str, Any]:
    pop, i = job
    try:
        tape = tape_of(pop, i)
        ok, _ = balance.accept(tape)
    except InvariantError as err:
        return {"pop": pop, "i": i, "accepted": False, "error": str(err)}
    if not ok:
        return {"pop": pop, "i": i, "accepted": False}
    labels: dict[str, str] = {}

    def label(fn: Any, *args: Any) -> str:
        try:
            return str(fn(tape, *args)["label"])
        except InvariantError as err:  # the engine refused the line outright: reported, never a label
            return f"INVARIANT:{str(err).split(' at day')[0]}"

    for name in ("passive", "derisk_floor"):
        labels[name] = label(balance.play, balance.POLICIES[name])
    for k in range(balance.NAIVE_SEEDS):
        labels[f"naive_{k}"] = label(balance.play_naive, k)
    for name, legs in BAD.items():
        labels[name] = label(play_daily, legs)
    return {"pop": pop, "i": i, "accepted": True, "labels": labels}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    jobs = [("gen", i) for i in range(1, n)] + [("hard", i) for i in range(n)]
    with Pool(4) as pool:
        rows = pool.map(scan, jobs, chunksize=4)
    for pop in ("gen", "hard"):
        drawn = [r for r in rows if r["pop"] == pop]
        acc = [r for r in drawn if r["accepted"]]
        print(f"{pop}: accepted {len(acc)}/{len(drawn)}")
        table: dict[str, Counter[str]] = {}
        for r in acc:
            for name, lab in r["labels"].items():
                table.setdefault("naive" if name.startswith("naive_") else name, Counter())[lab] += 1
        for name, c in table.items():
            print(f"  {name:18s} {dict(sorted(c.items()))}")
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(rows, indent=1), encoding="utf-8")
