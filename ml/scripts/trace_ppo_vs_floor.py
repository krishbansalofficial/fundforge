"""Is hard-world PPO just relearning ``derisk_floor``? Action traces of both on the hard test split.

Run from ml/ (needs the hard checkpoints eval_ppo.py --train-level hard wrote to results/*.zip):
  uv run --group train python scripts/trace_ppo_vs_floor.py

Every hard test world is accepted only if the scripted ``balance.POLICIES["derisk_floor"]`` line wins,
so PPO winning them all could just be that line rediscovered. This replays the published test worlds
(``test_world_order`` in results/ppo_pm_hard.json, the same split and order; checkpoint sha256 checked
against that file) with each trained seed and with derisk_floor, and compares per episode:

- first de-risk: the first reduce order that filled (sell a long / cover a short), keyed by the execution
  window it was proposed for (``clock.next``: day, EXEC_A/EXEC_B). Windows are indexed over the tape's
  execution events (window 0 is the first), so "within +/-1 window" means the same or an adjacent event.
- gross exposure (``view.fund.gross``, end of each day): end of first day, min (and its day), end, and the mean
  absolute difference to derisk_floor's path over common days.
- Jaccard overlap of {(day, "reduce:SYM")} sets, and of the reduced-symbol sets ignoring day.

derisk_floor is played as the gate plays it (two human seats, ``balance.play``'s loop); PPO is played
as eval_ppo.py tests it (agent PM, bot:v1 MP). Writes results/trace_ppo_vs_floor.json.
"""

import argparse
import contextlib
import hashlib
import json
import statistics
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import torch
from eval_ppo import ML, _git, _model, build
from fundforge.balance import POLICIES
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.tape import EXEC_PHASES, Tape
from train_ppo import play

LEVEL, CONFIG = "hard", "lr1e-4_ent0.01"
FLOOR = POLICIES["derisk_floor"]


def windows(tape: Tape) -> dict[tuple[int, str], int]:
    """(day, phase) -> index over the tape's execution events: one decision window each."""
    ex = [(ev.day, ev.phase) for ev in tape.events if ev.phase in EXEC_PHASES]
    return {w: i for i, w in enumerate(ex)}


def trace_plan(tape: Tape, plan: dict[Any, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """``balance.play`` with a per-step trace (same commands, keys and order; a test checks the journal)."""
    e = Engine(tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    k, trace = 0, []
    while not s.e.finished():
        k += 1
        nxt = s.e.next_event()
        if nxt is None:
            break
        orders = list(plan.get((nxt.day, nxt.phase), []))
        if plan.get("cure"):  # balance's cure branch is not part of derisk_floor
            raise ValueError("trace_plan does not replay cure plans")
        if orders:
            d = s.handle("ana", f"p{k}", {"type": "propose", "package_id": f"p{k}", "orders": orders})
            with contextlib.suppress(CommandRejected):
                s.handle("ben", f"s{k}", {"type": "sign", "package_id": f"p{k}", "digest": d["digest"]})
        s.handle("ana", f"ra{k}", {"type": "ready"})
        s.handle("ben", f"rb{k}", {"type": "ready"})
        v = s.view("ana")
        step = {"window": (nxt.day, nxt.phase), "reject": None, "day": v["clock"]["day"], "gross": v["fund"]["gross"]}
        trace += [{**step, "action": ("reduce", (x["sym"], None)), "order_ids": [x["order_id"]]} for x in orders]
        trace += [] if orders else [{**step, "action": ("wait", None), "order_ids": []}]
    fills = {x["order_id"]: x["filled"] for x in s.view("ana")["orders"]}
    for t in trace:
        t["filled"] = sum(fills.get(i, 0) for i in t["order_ids"])
    return s.e.outcome(), trace


def summarize(trace: list[dict[str, Any]], win: dict[tuple[int, str], int]) -> dict[str, Any]:
    """Per-episode facts from a trace: first de-risk window, (day, type) set, daily gross path."""
    acts = [t for t in trace if t["action"][0] == "reduce" and t["filled"] > 0]
    unfilled = sum(t["action"][0] == "reduce" and t["reject"] is None and not t["filled"] for t in trace)
    first = acts[0]["window"] if acts else None
    daily: dict[int, float] = {}
    for t in trace:
        if t["gross"] is not None:
            daily[t["day"]] = float(t["gross"])
    days = sorted(daily)
    lo = min(days, key=lambda d: daily[d]) if days else None
    return {
        "first_derisk": None if first is None else {"day": first[0], "phase": first[1], "window": win[first]},
        "acts": sorted({(t["window"][0], f"reduce:{t['action'][1][0]}") for t in acts}),
        "other_actions": dict(Counter(t["action"][0] for t in trace if t["action"][0] not in ("wait", "reduce"))),
        "rejected": sum(t["reject"] is not None for t in trace),
        "reduce_accepted_unfilled": unfilled,
        "gross": {"first_day_end": daily[days[0]] if days else None, "min": daily.get(lo), "min_day": lo,
                  "end": daily[days[-1]] if days else None},
        "daily_gross": daily,
    }


def jaccard(a: set[Any], b: set[Any]) -> float:
    return len(a & b) / len(a | b) if a | b else 1.0


def compare(ppo: dict[str, Any], floor: dict[str, Any]) -> dict[str, Any]:
    pa, fa = {tuple(x) for x in ppo["acts"]}, {tuple(x) for x in floor["acts"]}
    common = sorted(set(ppo["daily_gross"]) & set(floor["daily_gross"]))
    pf, ff = ppo["first_derisk"], floor["first_derisk"]
    gap = None if pf is None or ff is None else pf["window"] - ff["window"]
    return {
        "first_derisk_window_gap": gap,
        "timing_match_pm1": gap is not None and abs(gap) <= 1,
        "jaccard_day_type": round(jaccard(pa, fa), 4),
        "jaccard_symbols": round(jaccard({x[1] for x in pa}, {x[1] for x in fa}), 4),
        "gross_mean_abs_diff": round(statistics.fmean(
            abs(ppo["daily_gross"][d] - floor["daily_gross"][d]) for d in common), 4) if common else None,
    }


def floor_job(job: tuple[str, str]) -> tuple[tuple[str, str], dict[str, Any]]:
    seed, variant = job
    tape = build(seed, LEVEL, variant).tape
    out, tr = trace_plan(tape, FLOOR)
    return job, {"label": out["label"], "score": float(out["score"]), **summarize(tr, windows(tape))}


def ppo_job(job: tuple[str, str, int, str]) -> tuple[tuple[str, str, int], dict[str, Any]]:
    seed, variant, k, path = job
    torch.set_num_threads(1)
    w = build(seed, LEVEL, variant)
    tr: list[dict[str, Any]] = []
    out = play("pm", w, "ppo", _model(path), 0, trace=tr)
    return (seed, variant, k), {"label": out["label"], "score": out["score"], **summarize(tr, windows(w.tape))}


def _q(xs: list[float]) -> dict[str, float] | None:
    if not xs:
        return None
    q = statistics.quantiles(xs, n=4) if len(xs) > 1 else [xs[0]] * 3
    return {"mean": round(statistics.fmean(xs), 4), "q1": round(q[0], 4), "median": round(q[1], 4),
            "q3": round(q[2], 4), "min": round(min(xs), 4), "max": round(max(xs), 4)}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    syms = Counter(s for r in rows for s in {a[1] for a in r["ppo"]["acts"]})
    floor_syms = {a[1] for a in rows[0]["floor"]["acts"]} if rows else set()
    return {
        "episodes": n,
        "ppo_labels": dict(Counter(r["ppo"]["label"] for r in rows)),
        "floor_labels": dict(Counter(r["floor"]["label"] for r in rows)),
        "mean_score_bps": {"ppo": round(statistics.fmean(r["ppo"]["score"] for r in rows), 1),
                           "floor": round(statistics.fmean(r["floor"]["score"] for r in rows), 1)},
        "share_ppo_score_above_floor": round(sum(r["ppo"]["score"] > r["floor"]["score"] for r in rows) / n, 4),
        "ppo_no_derisk": sum(r["ppo"]["first_derisk"] is None for r in rows),
        "share_timing_match_pm1": round(sum(r["cmp"]["timing_match_pm1"] for r in rows) / n, 4),
        "share_ppo_first_derisk_at_window0": round(sum(
            (r["ppo"]["first_derisk"] or {}).get("window") == 0 for r in rows) / n, 4),
        "share_same_window": round(sum(r["cmp"]["first_derisk_window_gap"] == 0 for r in rows) / n, 4),
        "window_gap_counts": dict(sorted(Counter(r["cmp"]["first_derisk_window_gap"] for r in rows).items(),
                                         key=lambda kv: (kv[0] is None, kv[0] or 0))),
        "ppo_first_derisk_day_counts": dict(sorted(Counter(
            r["ppo"]["first_derisk"]["day"] for r in rows if r["ppo"]["first_derisk"]).items())),
        "jaccard_day_type": _q([r["cmp"]["jaccard_day_type"] for r in rows]),
        "jaccard_symbols": _q([r["cmp"]["jaccard_symbols"] for r in rows]),
        "gross_mean_abs_diff": _q([r["cmp"]["gross_mean_abs_diff"] for r in rows
                                   if r["cmp"]["gross_mean_abs_diff"] is not None]),
        "ppo_gross_min": _q([r["ppo"]["gross"]["min"] for r in rows if r["ppo"]["gross"]["min"] is not None]),
        "floor_gross_min": _q([r["floor"]["gross"]["min"] for r in rows if r["floor"]["gross"]["min"] is not None]),
        "ppo_reduced_symbol_share": {s: round(c / n, 4) for s, c in syms.most_common()},
        "share_ppo_reduces_all_floor_symbols": round(
            sum(floor_syms <= {a[1] for a in r["ppo"]["acts"]} for r in rows) / n, 4),
        "ppo_other_actions": dict(sum((Counter(r["ppo"]["other_actions"]) for r in rows), Counter())),
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--result", default=str(ML / "results" / "ppo_pm_hard.json"))
    ap.add_argument("--models", default=str(ML / "results"))
    ap.add_argument("--limit", type=int, default=0, help="first N test worlds only (smoke)")
    ap.add_argument("--out", default=str(ML / "results" / "trace_ppo_vs_floor.json"))
    args = ap.parse_args(argv)
    src = json.loads(Path(args.result).read_text(encoding="utf-8"))
    ws = [tuple(x.split("/")) for x in src["test_world_order"]]
    ws = ws[: args.limit] if args.limit else ws
    runs = src["grid"][CONFIG]["runs"]
    paths = [str(Path(args.models) / f"ppo_pm_hard_{CONFIG}_s{r['seed']}.zip") for r in runs]
    for r, p in zip(runs, paths, strict=True):  # the exact models the published 1090/1090 came from
        if hashlib.sha256(Path(p).read_bytes()).hexdigest() != r["sha256"]:
            raise SystemExit(f"{p} does not match the sha256 in {args.result}")
    with ProcessPoolExecutor(args.procs) as pool:
        floor = dict(pool.map(floor_job, ws, chunksize=4))
        ppo = dict(pool.map(ppo_job, [(s, v, k, p) for k, p in enumerate(paths) for s, v in ws], chunksize=8))
    rows = []
    for (s, v, k), p in sorted(ppo.items(), key=lambda kv: (kv[0][2], ws.index(kv[0][:2]))):
        f = floor[(s, v)]
        rows.append({"world": f"{s}/{v}", "train_seed": runs[k]["seed"], "ppo": p, "floor": f, "cmp": compare(p, f)})
    result = {
        "question": "does hard-world PPO reproduce the scripted derisk_floor line the hard gate requires to win?",
        "commit": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", ".")),
        "reproduce": "cd ml && uv run --group train python scripts/trace_ppo_vs_floor.py "
        + " ".join(sys.argv[1:] if argv is None else argv),
        "scale": {
            "models": f"{len(runs)} training seeds x {src['scale']['steps_per_run']} steps, config {CONFIG}, "
            "the published hard checkpoints (sha256 verified)",
            "test_worlds": len(ws),
            "episodes": len(rows),
            "source_result": Path(args.result).name,
            "source_commit": src["commit"],
        },
        "floor_plan": {f"{d}/{ph}": [o_["sym"] + " " + o_["side"] + " " + str(o_["qty"]) for o_ in xs]
                       for (d, ph), xs in FLOOR.items()},
        "definitions": {
            "decision_window": "one execution event (EXEC_A or EXEC_B) of the tape; an action is keyed by the "
            "window it was proposed for (clock.next); window 0 is the episode's first decision window",
            "first_derisk": "first reduce (SELL a long / COVER a short), any size, whose order filled (any qty) "
            "by the end of the episode",
            "timing_match_pm1": "|window(PPO first de-risk) - window(derisk_floor first de-risk)| <= 1",
            "jaccard_day_type": "Jaccard of {(day, 'reduce:SYM')} sets; sizes ignored",
            "gross": "view.fund.gross, last value of each day",
        },
        "overall": aggregate(rows),
        "by_train_seed": {str(r["seed"]): aggregate([x for x in rows if x["train_seed"] == r["seed"]]) for r in runs},
        "episodes": [{**r, "ppo": {k: v for k, v in r["ppo"].items() if k != "daily_gross"},
                      "floor": {k: v for k, v in r["floor"].items() if k != "daily_gross"}} for r in rows],
    }
    head = json.dumps({k: v for k, v in result.items() if k != "episodes"}, indent=1, default=str)
    eps = ",\n".join(json.dumps(e, separators=(",", ":"), default=str) for e in result["episodes"])
    Path(args.out).write_text(f'{head[:-2]},\n "episodes": [\n{eps}\n ]\n}}\n', encoding="utf-8")  # one line each
    print(json.dumps(result["overall"], indent=1, default=str))
    return result


if __name__ == "__main__":
    main()
