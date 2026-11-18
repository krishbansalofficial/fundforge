"""Post-game return attribution against the generator's TRUE market factor vs a public proxy.

Run from ml/ (the PPO checkpoints are gitignored; point --models at a checkout that has them):
  uv run --group train --group attribution python scripts/attribution.py [--models ../../ml/results]

Worlds: the hard test split published in results/ppo_pm_hard.json (``test_world_order``), every one
gate-accepted at HARD_VERSION. Policies: ``passive`` and ``derisk_floor`` (balance.POLICIES, played as the
gate plays them) and the published hard PPO checkpoints (sha256 checked; skipped with a note if absent).

Per episode the fund's daily NAV-per-unit return comes only from public views; after the episode finishes
the generator's true factor is replayed (``fundforge_ml.attribution.true_factors``). Regressions:
- per episode: ret = a + b*F, HAC Newey-West, F = true factor or the public proxy (equal-weight equity marks);
- pooled per policy: ret = a + b_pre*F*pre + b_post*F*post, cluster-robust by world (pre/post = before/after
  the drawn crisis day). Writes results/attribution.json.
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

import numpy as np
import torch
from eval_ppo import ML, _git, _model, build
from fundforge.balance import POLICIES
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session

from fundforge_ml import attribution as A
from fundforge_ml.env import FundForgeEnv

LEVEL, CONFIG = "hard", "lr1e-4_ent0.01"
PLANS = ("passive", "derisk_floor")
MIN_DAYS = 5  # per-episode fit needs at least 3 residual degrees of freedom


def play_plan(seed: str, variant: str, plan: dict[Any, Any]) -> tuple[Engine, list[dict[str, Any]]]:
    """``balance.play``'s loop (two human seats) with a public snapshot after every step."""
    e = Engine(build(seed, LEVEL, variant).tape)
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    snaps, k = [A.snapshot(s.view("ana"))], 0
    while not s.e.finished():
        k += 1
        nxt = s.e.next_event()
        if nxt is None:
            break
        orders = list(plan.get((nxt.day, nxt.phase), []))
        if orders:
            d = s.handle("ana", f"p{k}", {"type": "propose", "package_id": f"p{k}", "orders": orders})
            with contextlib.suppress(CommandRejected):
                s.handle("ben", f"s{k}", {"type": "sign", "package_id": f"p{k}", "digest": d["digest"]})
        s.handle("ana", f"ra{k}", {"type": "ready"})
        s.handle("ben", f"rb{k}", {"type": "ready"})
        snaps.append(A.snapshot(s.view("ana")))
    return s.e, snaps


def play_ppo(seed: str, variant: str, path: str) -> tuple[Engine, list[dict[str, Any]]]:
    """``train_ppo.play`` for policy "ppo" (agent PM, bot:v1 MP), snapshotting the agent's observed view."""
    torch.set_num_threads(1)
    w, model = build(seed, LEVEL, variant), _model(path)
    env = FundForgeEnv("pm", policy_id="ppo", world_fn=lambda o, r: w)
    obs, _ = env.reset(seed=0, options={"episode_tag": "ppo-0"})
    snaps, done = [A.snapshot(env.view)], False
    while not done:
        a, _ = model.predict(obs, deterministic=True, action_masks=env.action_masks())
        obs, _, term, trunc, _ = env.step(int(a))
        snaps.append(A.snapshot(env.view))
        done = term or trunc
    assert env.s is not None
    return env.s.e, snaps


def job(j: tuple[str, str, str, str | None]) -> dict[str, Any]:
    policy, seed, variant, path = j
    e, snaps = play_ppo(seed, variant, path) if path else play_plan(seed, variant, POLICIES[policy])
    outcome = e.outcome()
    truth = A.true_factors(e, seed)  # debrief: after the episode is finished
    crisis = e.tape.raw["generator"]["scenario"]["crisis_day"]
    smp = A.sample(A.daily(snaps), truth, crisis)
    y = [r["ret"] for r in smp]
    return {"policy": policy, "world": f"{seed}/{variant}", "label": outcome["label"], "crisis_day": crisis,
            "sample": smp,
            # an intercept and a slope on fewer than MIN_DAYS points is (near) exact interpolation, not a fit
            "true": A.fit(y, [[r["factor"]] for r in smp], ["beta"]) if len(smp) >= MIN_DAYS else None,
            "proxy": A.fit(y, [[r["proxy"]] for r in smp], ["beta"]) if len(smp) >= MIN_DAYS else None}


def _q(xs: list[float], nd: int = 4) -> dict[str, float]:
    q = statistics.quantiles(xs, n=4)
    return {"mean": round(statistics.fmean(xs), nd), "q1": round(q[0], nd), "median": round(q[1], nd),
            "q3": round(q[2], nd), "min": round(min(xs), nd), "max": round(max(xs), nd)}


def pooled(eps: list[dict[str, Any]], key: str, worlds_ix: dict[str, int]) -> dict[str, Any]:
    rows = [(r, worlds_ix[e["world"]]) for e in eps for r in e["sample"]]
    x = [[r[key] * (not r["post"]), r[key] * r["post"]] for r, _ in rows]
    f = A.fit([r["ret"] for r, _ in rows], x, ["beta_pre", "beta_post"], groups=[g for _, g in rows])
    one = A.fit([r["ret"] for r, _ in rows], [[r[key]] for r, _ in rows], ["beta"], groups=[g for _, g in rows])
    return {"pre_post": f, "single": one}


def per_episode(eps: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    eps = [e for e in eps if e[key] is not None]
    if len(eps) < 2:
        return None
    c = [e[key]["coef"] for e in eps]
    return {
        "episodes_fitted": len(eps),
        "alpha_bp_per_day": _q([x["alpha"]["est"] * 1e4 for x in c], 2),
        "beta": _q([x["beta"]["est"] for x in c]),
        "beta_ci95_width": _q([x["beta"]["hi"] - x["beta"]["lo"] for x in c]),
        "share_beta_ci_excludes_0": round(sum(x["beta"]["lo"] > 0 or x["beta"]["hi"] < 0 for x in c) / len(c), 4),
        "share_alpha_ci_excludes_0": round(sum(x["alpha"]["lo"] > 0 or x["alpha"]["hi"] < 0 for x in c) / len(c), 4),
        "r2": _q([e[key]["r2"] for e in eps]),
    }


def summarize(eps: list[dict[str, Any]], worlds_ix: dict[str, int]) -> dict[str, Any]:
    days = [r for e in eps for r in e["sample"]]
    net = {p: [r["net"] for r in days if r["post"] == p] for p in (False, True)}
    gap = [abs(e["true"]["coef"]["beta"]["est"] - e["proxy"]["coef"]["beta"]["est"]) for e in eps if e["true"]]
    return {
        "episodes": len(eps),
        "days": len(days),
        "obs_per_episode": dict(sorted(Counter(len(e["sample"]) for e in eps).items())),
        "labels": dict(sorted(Counter(e["label"] for e in eps).items())),
        "public_net_exposure_mean": {"pre": round(statistics.fmean(net[False]), 4),
                                     "post": round(statistics.fmean(net[True]), 4)},
        "per_episode_true": per_episode(eps, "true"),
        "per_episode_proxy": per_episode(eps, "proxy"),
        "abs_beta_gap_true_vs_proxy": _q(gap) if len(gap) > 1 else None,
        "pooled_true": pooled(eps, "factor", worlds_ix),
        "pooled_proxy": pooled(eps, "proxy", worlds_ix),
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--result", default=str(ML / "results" / "ppo_pm_hard.json"))
    ap.add_argument("--models", default=str(ML / "results"))
    ap.add_argument("--ppo-seeds", type=int, default=5, help="how many published checkpoints to play (0 = none)")
    ap.add_argument("--limit", type=int, default=0, help="first N test worlds only (smoke)")
    ap.add_argument("--out", default=str(ML / "results" / "attribution.json"))
    args = ap.parse_args(argv)
    src = json.loads(Path(args.result).read_text(encoding="utf-8"))
    ws = [tuple(x.split("/")) for x in src["test_world_order"]]
    ws = ws[: args.limit] if args.limit else ws
    runs = src["grid"][CONFIG]["runs"][: args.ppo_seeds]
    paths = [Path(args.models) / f"ppo_pm_hard_{CONFIG}_s{r['seed']}.zip" for r in runs]
    ppo_note = f"{len(runs)} published hard checkpoints, sha256 verified against {Path(args.result).name}"
    if not paths or not all(p.exists() for p in paths):
        ppo_note, runs, paths = f"skipped: checkpoints not found under {args.models}", [], []
    for r, p in zip(runs, paths, strict=True):
        if hashlib.sha256(p.read_bytes()).hexdigest() != r["sha256"]:
            raise SystemExit(f"{p} does not match the sha256 in {args.result}")
    jobs = [(pol, s, v, None) for pol in PLANS for s, v in ws]
    jobs += [(f"ppo_s{r['seed']}", s, v, str(p)) for r, p in zip(runs, paths, strict=True) for s, v in ws]
    with ProcessPoolExecutor(args.procs) as pool:
        eps = list(pool.map(job, jobs, chunksize=4))
    worlds_ix = {f"{s}/{v}": i for i, (s, v) in enumerate(ws)}
    groups = {pol: [e for e in eps if e["policy"] == pol] for pol in PLANS}
    if runs:
        groups["ppo"] = [e for e in eps if e["policy"].startswith("ppo")]
    allf = [(r["factor"], r["proxy"]) for e in eps if e["policy"] == "passive" for r in e["sample"]]
    f, p = np.array(allf).T
    result = {
        "question": "what does OLS attribution against the generator's true hidden market factor say about each "
        "policy's daily returns, and how far is it from the attribution a player could run on public marks?",
        "commit": _git("rev-parse", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", ".")),
        "reproduce": "cd ml && uv run --group train --group attribution python scripts/attribution.py "
        + " ".join(sys.argv[1:] if argv is None else argv),
        "scale": {"level": LEVEL, "test_worlds": len(ws), "source_result": Path(args.result).name,
                  "source_commit": src["commit"], "ppo": ppo_note},
        "method": {
            "fund_return": "daily change in fund NAV / total series units, end of each day, from public views only "
            "(flow-neutral: the LP redemption moves units and NAV together); gross of nothing, so fees, financing, "
            "spreads and impact land in alpha",
            "true_factor": "the generator's market-factor draw for that day's PUBLIC_MARK (exact Decimal replay of "
            "generate's SHA-256 stream, checked mark-for-mark against generate's output); equity beta 1, BOND 0",
            "proxy_factor": "equal-weight mean return of the 11 public equity marks (BOND excluded): what a player "
            "could compute as of each mark",
            "sample": "generated days only: the first day (no public previous close), the authored crisis day and, "
            "in the rally variant, the day after it (the generator stepped from crisis marks the tape replaced) are "
            "excluded. Public marks also move between PUBLIC_MARK and CLOSE (rival flows and impact in the engine's "
            "market model), so even the true factor does not explain public close-to-close moves exactly",
            "per_episode_se": "HAC Newey-West, Bartlett kernel, maxlags = floor(4*(T/100)^(2/9)) "
            f"(= {A.nw_lags(6)} for T=6..7)",
            "pooled_se": "cluster-robust by world (all policies' and seeds' episodes of a world share a cluster id)",
            "per_episode_min_days": f"per-episode fits only with >= {MIN_DAYS} usable days; PPO votes to skip quiet "
            "windows, so its seat has no view on many days and most PPO episodes have too few one-day returns: PPO is "
            "read from the pooled fit",
            "caveat": "6-7 daily observations per episode: per-episode intervals are very wide and HAC with T<10 "
            "is not reliable; read the per-episode numbers as a distribution, and the pooled fits for structure. "
            "Ex-post descriptive attribution; residual return is not proof of skill.",
        },
        "factor_vs_proxy": {"corr": round(float(np.corrcoef(f, p)[0, 1]), 4),
                            "sd_true": round(float(f.std(ddof=1)), 6),
                            "sd_proxy_minus_true": round(float((p - f).std(ddof=1)), 6), "days": len(f)},
        "policies": {k: summarize(v, worlds_ix) for k, v in groups.items()},
        "by_ppo_seed": {pol: summarize([e for e in eps if e["policy"] == pol], worlds_ix)["pooled_true"]
                        for pol in sorted({e["policy"] for e in eps}) if pol.startswith("ppo")},
    }
    Path(args.out).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: {"pooled_true": v["pooled_true"]["pre_post"]["coef"],
                          "pooled_proxy": v["pooled_proxy"]["pre_post"]["coef"]}
                      for k, v in result["policies"].items()}, indent=1))
    return result


if __name__ == "__main__":
    main()
