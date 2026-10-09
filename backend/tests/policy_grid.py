"""Knowledge-free policy grid played through the real Session, used by the balance test."""

from pathlib import Path
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.tape import EXEC_PHASES, load
from test_engine import cure_qty

F = Path(__file__).parents[2] / "fixtures" / "case1.json"
LONGS = {"ALTO": 30000, "COVE": 30000, "ELAN": 30000, "GALA": 30000, "IONA": 30000, "JUNO": 25000, "BEAM": 100000}
SHORTS = {"BRIN": 12500, "DART": 12500, "FENN": 12500, "HELI": 12500}
o = lambda i, s, side, q: {"order_id": i, "sym": s, "side": side, "qty": q}
POLICIES = {
    "passive": {},
    "flatten_d12": {(12, "EXEC_A"): [o(f"f{s}", s, "SELL", q) for s, q in LONGS.items()] + [o(f"c{s}", s, "COVER", q) for s, q in SHORTS.items()]},
    "derisk_floor": {(12, "EXEC_A"): [o("b", "BEAM", "SELL", 50000), o("a", "ALTO", "SELL", 25000), o("c", "COVE", "SELL", 25000)],
                     (14, "EXEC_A"): [o("r", "BRIN", "COVER", 1250)]},
    "S1_balanced": {(14, "EXEC_A"): [o("r", "BRIN", "COVER", 1250), o("b", "BEAM", "SELL", 20000)]},
    # Answers margin calls when they are announced (no foreknowledge): since the endogenous market,
    # Halcyon's day-16 forced covering squeezes BRIN enough to put the minimal line into a margin call.
    "cover_recall_only": {(14, "EXEC_A"): [o("r", "BRIN", "COVER", 1250)], "cure": True},
}

def play(variant, plan):
    e = Engine(load(F, variant)); e.advance(); s = Session(e, {"pm": "ana", "mp": "ben"}); k = 0
    while not s.e.finished():
        k += 1
        nxt = s.e.next_event()
        orders = list(plan.get((nxt.day, nxt.phase), []))
        if plan.get("cure") and s.e.margin_call is not None and nxt.phase in EXEC_PHASES:
            orders.append(o(f"cure{k}", "ALTO", "SELL", cure_qty(s.e, k=2)))
        if orders:
            d = s.handle("ana", f"p{k}", {"type": "propose", "package_id": f"p{k}", "orders": orders})
            try:
                s.handle("ben", f"s{k}", {"type": "sign", "package_id": f"p{k}", "digest": d["digest"]})
            except CommandRejected:
                pass
        s.handle("ana", f"ra{k}", {"type": "ready"}); s.handle("ben", f"rb{k}", {"type": "ready"})
    return s.e.outcome()

if __name__ == "__main__":
    for name, plan in POLICIES.items():
        rows = [play(v, plan) for v in ("base", "rally")]
        mean = sum(float(r["score"]) for r in rows) / 2
        print(f"{name:18s} " + "  ".join(f"{r['variant']}:{r['label']:8s} score {float(r['score']):8.1f}" for r in rows) + f"   mean {mean:8.1f}")
