"""Benchmark B6: game balance across generator seeds.

Draws the fixed seed list ``seed:b6-0`` .. ``seed:b6-(N-1)``, builds each exactly as a generated room
does (``store._tape(case1-generated, seed)``) and runs the existing balance grid (``balance.accept``,
which plays every ``balance.POLICIES`` line through the real Session). Rooms only run gate-accepted
seeds, so the primary population is the accepted subset; the ungated draw is reported alongside
because on accepted seeds the gate itself forces every designed line to WIN and passive not to.

Rates carry Wilson 95% intervals computed in Decimal. Verdict: FAIL if any degenerate policy's win
interval lies wholly above the best designed line's. Score balance (stated before measuring): among the
designed lines only, FAIL if any line's best-score share interval lies wholly above SHARE_LIMIT. No
database, no network.

    cd backend && uv run python ../scripts/bench_balance.py --seeds 200 --out ../bench/results
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections import Counter
from datetime import UTC, datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from fundforge import balance, store  # noqa: E402
from fundforge.engine import RULES_VERSION  # noqa: E402
from fundforge.generator import GEN_VERSION  # noqa: E402

DESIGNED = balance.RECALL_LINES
DEGENERATE = ("passive", "flatten_d12")
OUTCOMES = {"win": "WIN", "survival": "SURVIVAL", "distress": "DISTRESS"}
Z = Decimal("1.96")
Q = Decimal("0.0001")
SHARE_LIMIT = Decimal("0.5")  # design choice: no designed line may be the best answer in most worlds
DIAG = ("fund_return_bps", "benchmark_return_bps", "excess_bps", "financing_drag_bps", "impact_drag_bps")


def wilson(k: int, n: int, z: Decimal = Z) -> tuple[Decimal, Decimal]:
    """Wilson score interval for k successes in n, rounded outward to 4 dp (lower floor, upper ceiling)."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError(f"bad counts k={k} n={n}")
    with localcontext() as ctx:
        ctx.prec = 40
        p, z2, nn = Decimal(k) / n, z * z, Decimal(n)
        centre = p + z2 / (2 * nn)
        half = z * (p * (1 - p) / nn + z2 / (4 * nn * nn)).sqrt()
        den = 1 + z2 / nn
        lo, hi = (centre - half) / den, (centre + half) / den
    return max(lo, Decimal(0)).quantize(Q, ROUND_FLOOR), min(hi, Decimal(1)).quantize(Q, ROUND_CEILING)


def rates(labels: list[str]) -> dict[str, dict[str, object]]:
    n, counts = len(labels), Counter(labels)
    out: dict[str, dict[str, object]] = {}
    for key, label in OUTCOMES.items():
        lo, hi = wilson(counts[label], n)
        out[key] = {"k": counts[label], "n": n, "rate": str((Decimal(counts[label]) / n).quantize(Q)),
                    "wilson95": [str(lo), str(hi)]}
    return out


def verdict(table: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    """Best designed line by win rate; FAIL if any degenerate win interval's lower bound exceeds its upper."""
    best = max(DESIGNED, key=lambda p: Decimal(str(table[p]["win"]["rate"])))
    ceiling = Decimal(str(table[best]["win"]["wilson95"][1]))  # type: ignore[index]
    dominant = [p for p in DEGENERATE if Decimal(str(table[p]["win"]["wilson95"][0])) > ceiling]  # type: ignore[index]
    return {"best_designed": best, "dominant_degenerate": dominant, "pass": not dominant}


def quantile(xs: list[Decimal], f: Decimal) -> Decimal:
    """Linear-interpolated quantile of a non-empty list, in Decimal."""
    xs = sorted(xs)
    pos = (len(xs) - 1) * f
    i = int(pos)
    return xs[i] if i + 1 >= len(xs) else xs[i] + (xs[i + 1] - xs[i]) * (pos - i)


def spread(xs: list[Decimal]) -> dict[str, str]:
    return {k: str(quantile(xs, Decimal(f))) for k, f in
            (("min", 0), ("p25", "0.25"), ("median", "0.5"), ("p75", "0.75"), ("max", 1))}


def score_balance(scores: list[dict[str, str]], lines: tuple[str, ...] = DESIGNED) -> dict[str, object]:
    """Best-score share among `lines` per seed (strict best; ties counted apart) and each line's margin over
    the best other line. FAIL if any share's Wilson lower bound exceeds SHARE_LIMIT."""
    n, best, ties = len(scores), Counter[str](), 0
    margins: dict[str, list[Decimal]] = {p: [] for p in lines}
    for sc in scores:
        v = {p: Decimal(sc[p]) for p in lines}
        winners = [p for p in lines if v[p] == max(v.values())]
        if len(winners) == 1:
            best[winners[0]] += 1
        else:
            ties += 1
        for p in lines:
            margins[p].append(v[p] - max(v[q] for q in lines if q != p))
    out: dict[str, dict[str, object]] = {}
    for p in lines:
        lo, hi = wilson(best[p], n)
        out[p] = {"k": best[p], "n": n, "share": str((Decimal(best[p]) / n).quantize(Q)),
                  "wilson95": [str(lo), str(hi)], "margin_bps": spread(margins[p])}
    dominant = [p for p in lines if Decimal(str(out[p]["wilson95"][0])) > SHARE_LIMIT]  # type: ignore[index]
    return {"lines": out, "ties": ties, "share_limit": str(SHARE_LIMIT), "dominant": dominant, "pass": not dominant}


def diagnose(rows: list[dict[str, object]]) -> dict[str, object]:
    """Per designed line, the spread of each score component, and best-score share split by benchmark sign."""
    comp = {p: {k: spread([Decimal(r["outcomes"][p][k]) for r in rows]) for k in DIAG}  # type: ignore[index]
            for p in DESIGNED}
    split: dict[str, object] = {}
    for name, down in (("benchmark_down", True), ("benchmark_up", False)):
        sub = [r for r in rows
               if (Decimal(r["outcomes"][DESIGNED[0]]["benchmark_return_bps"]) < 0) == down]  # type: ignore[index]
        split[name] = score_balance([r["scores"] for r in sub])["lines"] if sub else None  # type: ignore[misc]
    return {"components": comp, "by_benchmark_sign": split}


def summarise(rows: list[dict[str, object]]) -> dict[str, object]:
    policies = list(balance.POLICIES)
    table = {p: rates([r["labels"][p] for r in rows]) for p in policies}  # type: ignore[index]
    best_score = Counter(max(policies, key=lambda p: Decimal(r["scores"][p])) for r in rows)  # type: ignore[index]
    return {"n": len(rows), "policies": table, "best_score_count": dict(best_score), "verdict": verdict(table),
            "score_balance": score_balance([r["scores"] for r in rows]), "diagnosis": diagnose(rows)}  # type: ignore[misc]


def run(n: int) -> dict[str, object]:
    rows = []
    for i in range(n):
        seed = f"seed:b6-{i}"
        tape = store._tape(store.GENERATED, seed)
        ok, report = balance.accept(tape)
        # the gate report keeps label and score only; replay the designed lines (deterministic) for components
        outcomes = {p: balance.play(tape, balance.POLICIES[p]) for p in DESIGNED}
        rows.append({"seed": seed, "accepted": ok, "failures": report["failures"],
                     "labels": {p: v["label"] for p, v in report["policies"].items()},
                     "scores": {p: v["score"] for p, v in report["policies"].items()},
                     "outcomes": {p: {k: r[k] for k in DIAG} for p, r in outcomes.items()}})
    accepted = [r for r in rows if r["accepted"]]
    return {"accepted": summarise(accepted) if accepted else None, "ungated": summarise(rows), "seeds": rows}


def main() -> int:
    from bench_engine import commit, machine

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200, help="seeds drawn (seed:b6-0 .. seed:b6-N-1)")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = run(args.seeds)
    doc = {
        "benchmark": "B6-game-balance",
        "commit": commit(),
        "rules_version": RULES_VERSION,
        "generator_version": GEN_VERSION,
        "gate_rule": store.GATE_RULE,
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "machine": machine(),
        "seeds_drawn": args.seeds,
        "seed_list": f"seed:b6-0 .. seed:b6-{args.seeds - 1}, built by store._tape('{store.GENERATED}', seed)",
        "designed": list(DESIGNED),
        "degenerate": list(DEGENERATE),
        "interval": "Wilson score, z=1.96, Decimal, rounded outward to 4 dp",
        "caveat": "on accepted seeds the gate requires every designed line to WIN and passive not to, "
                  "and flatten_d12 must replay passive's journal; the accepted verdict holds by construction",
        **result,
    }
    for pop in ("accepted", "ungated"):
        s = result[pop]
        if not s:
            print(f"{pop}: no seeds")
            continue
        print(f"{pop}: n={s['n']} verdict={s['verdict']} best_score={s['best_score_count']}")  # type: ignore[index]
        for p, t in s["policies"].items():  # type: ignore[index]
            print(f"  {p:18s} " + "  ".join(f"{o} {t[o]['k']}/{t[o]['n']} {t[o]['wilson95']}" for o in OUTCOMES))
        sb = s["score_balance"]  # type: ignore[index]
        print(f"  score balance pass={sb['pass']} dominant={sb['dominant']} ties={sb['ties']}")
        for p, t in sb["lines"].items():
            print(f"  {p:18s} best {t['k']}/{t['n']} {t['wilson95']} margin {t['margin_bps']}")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        name = f"{doc['measured_at'][:10]}-B6-{doc['commit'].replace('+', '_')}.json"
        (args.out / name).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {args.out / name}")
    acc = result["accepted"]
    return 0 if acc and acc["verdict"]["pass"] and acc["score_balance"]["pass"] else 1  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
