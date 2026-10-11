"""Knowledge-free policy grid played through the real Session, used by the balance test."""

from pathlib import Path

from fundforge import balance
from fundforge.balance import POLICIES
from fundforge.tape import load

F = Path(__file__).parents[2] / "fixtures" / "case1.json"


def play(variant, plan):
    return balance.play(load(F, variant), plan)


if __name__ == "__main__":
    for name, plan in POLICIES.items():
        rows = [play(v, plan) for v in ("base", "rally")]
        mean = sum(float(r["score"]) for r in rows) / 2
        cells = "  ".join(f"{r['variant']}:{r['label']:8s} score {float(r['score']):8.1f}" for r in rows)
        print(f"{name:18s} {cells}   mean {mean:8.1f}")
