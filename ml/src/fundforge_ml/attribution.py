"""Debrief-time return attribution against the generator's true hidden market factor.

Two inputs, kept apart on purpose:

- ``snapshot(view)`` reads one public as-of view (``Session.view`` / ``contracts.observe``): fund NAV,
  total series units and public marks. ``daily(snaps)`` turns the last snapshot of each day into the
  fund's daily NAV-per-unit return (flow-neutral: redemptions change units and NAV together) and an
  observable market proxy: the equal-weight mean return of the public equity marks (BOND excluded).
- ``true_factors(engine, gen_seed, spec)`` is hidden truth. ``generate`` does not return its factor
  draws, so this replays its SHA-256 draw sequence with the generator's own ``Stream`` and checks the
  replayed marks equal ``generate``'s output exactly before returning anything. It refuses to run
  until the episode is finished: it is a debrief tool, never an input to play.

``fit`` is OLS (statsmodels) of daily fund returns on one factor with Newey-West (HAC) errors.
These are descriptive ex-post regressions on a handful of days; residual return is not proof of skill.
"""

import math
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any

from fundforge.engine import Engine
from fundforge.generator import BP, PRICE, RANDOMISED, Spec, Stream, generate, randomise
from fundforge.money import CTX

from . import worlds

NON_EQUITY = frozenset({"BOND"})  # the proxy is an equity index; the player can see BOND is not one


def snapshot(view: dict[str, Any]) -> dict[str, Any]:
    """Public fields only, from one as-of view."""
    units = sum(Decimal(s["units"]) for s in view["series"])
    return {
        "day": view["clock"]["day"],
        "nav": Decimal(view["fund"]["nav"]),
        "units": units,
        "opening_nav_per_unit": sum(Decimal(s["net"]) for s in view["series"]) / units,
        "net": float(view["fund"]["net"]),
        "marks": {k: Decimal(v) for k, v in view["marks"].items()},
    }


def daily(snaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """End-of-day rows: day, fund return, observable proxy return, net exposure, marks."""
    last: dict[int, dict[str, Any]] = {}
    for s in snaps:
        last[s["day"]] = s
    first = snaps[0]
    prev_npu = first["opening_nav_per_unit"]  # series are struck at the opening until the first close
    prev_marks: dict[str, Decimal] | None = None
    rows = []
    for d in sorted(last):
        s = last[d]
        npu = s["nav"] / s["units"]
        proxy = None
        if prev_marks is not None:
            eq = [s["marks"][k] / prev_marks[k] - 1 for k in s["marks"] if k not in NON_EQUITY]
            proxy = float(sum(eq) / len(eq))
        rows.append({"day": d, "ret": float(npu / prev_npu - 1), "proxy": proxy, "net": s["net"],
                     "marks": s["marks"]})
        prev_npu, prev_marks = npu, s["marks"]
    return rows


def true_factors(e: Engine, gen_seed: str, spec: Spec | None = None) -> dict[int, dict[str, Any]]:
    """{day: {factor, regime, pre_marks}} for every generated PUBLIC_MARK; authored days are absent.

    Debrief only: raises unless the episode is finished. Replays ``generate``'s draw order with its
    ``Stream`` and checks every replayed mark against ``generate``'s own output.
    """
    if not e.finished():
        raise RuntimeError("true factors are hidden until the episode is finished")
    spec = spec or Spec()
    version = e.tape.raw["generator"]["version"]
    sk = worlds.skeleton()
    raw = generate(gen_seed, version, sk, spec)  # the public function: the reference output
    if version in RANDOMISED:
        sk, _ = randomise(gen_seed, version, sk, spec)
    rng, syms, cal = Stream(gen_seed, version), list(sk["instruments"]), sk["calendar"]
    authored = {(o["day"], o["event"]): o for o in sk["overrides"]}
    marks = {s: Decimal(sk["defaults"]["mark"]) for s in syms}
    stressed = False
    out: dict[int, dict[str, Any]] = {}
    with localcontext(CTX):
        for day in range(cal["start_day"], cal["end_day"]):
            for event in ("OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE"):
                fixed = authored.get((day, event), {}).get("marks", {})
                marks.update({s: Decimal(v) for s, v in fixed.items()})
                if event != "PUBLIC_MARK" or fixed:
                    continue
                pre = dict(marks)
                if rng.integer(0, 9_999) < spec.switch_bp:
                    stressed = not stressed
                bound = spec.factor_bp * (spec.stress_multiplier if stressed else 1)
                factor = rng.integer(-bound, bound) * BP
                for s in syms:
                    step = spec.beta.get(s, Decimal(1)) * factor + rng.integer(-spec.idio_bp, spec.idio_bp) * BP
                    marks[s] = (marks[s] * (1 + step)).quantize(PRICE, rounding=ROUND_HALF_EVEN)
                out[day] = {"factor": float(factor), "regime": "stressed" if stressed else "calm",
                            "pre_marks": pre, "marks": {s: str(marks[s]) for s in syms}}
    generated = raw["overrides"][len(sk["overrides"]):]
    if [(g["day"], g["marks"]) for g in generated] != [(d, v["marks"]) for d, v in out.items()]:
        raise RuntimeError(f"factor replay does not reproduce generate({gen_seed!r}, {version!r})")
    if [[d, v["regime"]] for d, v in out.items()] != raw["generator"]["regimes"]:
        raise RuntimeError("factor replay regimes differ from the generator's record")
    # A variant (e.g. rally) replaces authored crisis marks after generation, so the next generated mark
    # steps from marks the played tape never printed: that day's return is not factor-driven.
    tape_marks = {o["day"]: o["marks"] for o in e.tape.raw["overrides"] if o["event"] == "PUBLIC_MARK" and "marks" in o}
    for d, v in out.items():
        prev = [p for p in tape_marks if p < d]
        v["continuous"] = not prev or all(Decimal(x) == v["pre_marks"][s] for s, x in tape_marks[max(prev)].items())
    return out


def sample(rows: list[dict[str, Any]], truth: dict[int, dict[str, Any]], crisis_day: int) -> list[dict[str, Any]]:
    """Days usable for attribution: the generator drew a factor from the marks the tape printed, and there is a
    public previous close (so the proxy exists; this drops the first day). ``post`` = after the crisis day."""
    return [{"day": r["day"], "ret": r["ret"], "factor": t["factor"], "proxy": r["proxy"],
             "regime": t["regime"], "post": r["day"] > crisis_day, "net": r["net"]}
            for r in rows if (t := truth.get(r["day"])) is not None and t["continuous"] and r["proxy"] is not None]


def nw_lags(n: int) -> int:
    """Newey-West (1994) plug-in rule: floor(4 (T/100)^(2/9))."""
    return math.floor(4 * math.pow(n / 100, 2 / 9))


def fit(y: list[float], x: list[list[float]], names: list[str], *, groups: list[int] | None = None) -> dict[str, Any]:
    """OLS with an intercept. HAC (Bartlett kernel, ``nw_lags``) by default; cluster-robust when ``groups`` is given."""
    import numpy as np
    import statsmodels.api as sm  # type: ignore[import-untyped,import-not-found,unused-ignore]

    X = sm.add_constant(np.asarray(x, dtype=float), has_constant="add")
    n = len(y)
    if groups is None:
        res = sm.OLS(np.asarray(y, dtype=float), X).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags(n)})
        se = f"HAC Newey-West, Bartlett, maxlags={nw_lags(n)}"
    else:
        res = sm.OLS(np.asarray(y, dtype=float), X).fit(cov_type="cluster", cov_kwds={"groups": np.asarray(groups)})
        se = f"cluster-robust by world ({len(set(groups))} clusters)"
    ci = res.conf_int(0.05)
    coef = {k: {"est": float(res.params[i]), "lo": float(ci[i][0]), "hi": float(ci[i][1]), "se": float(res.bse[i])}
            for i, k in enumerate(["alpha", *names])}
    return {"n": n, "se": se, "coef": coef, "r2": float(res.rsquared), "resid_sd": float(np.sqrt(res.mse_resid))}
