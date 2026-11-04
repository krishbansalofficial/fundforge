"""Minimum-impact margin cure for one execution event.

Each leg reduces one position. With cumulative event cost C(q) = a*q + b*q**3
(half-spread plus cubic impact, FUND_ACCOUNTING §8) and maintenance relief
R(q) = r*q - C(q), the problem

    minimise sum C_i(q_i)  subject to  sum R_i(q_i) >= target,  0 <= q_i <= cap_i

is convex. Its KKT condition is C_i'(q_i) = mu * r_i with one shared mu in
[0, 1]; mu = 1 is the point of maximum relief. Total relief is monotone in mu,
so mu is found by bisection in Decimal, then whole-share quantities are
floored and re-checked with the engine's exact rounded fill economics.
Pure arithmetic over caller-supplied public assumptions: no engine, tape or I/O.
"""

from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal, localcontext

from .execution import fill_price
from .money import CTX, cents

ITERATIONS = 80  # halves [0, 1] to below 1e-24; deterministic, no tolerance test


@dataclass(frozen=True)
class Leg:
    sym: str
    side: str  # SELL reduces a long, COVER reduces a short
    mark: Decimal
    rate: Decimal  # maintenance margin rate on this side
    volume: int
    cap: int  # whole shares available this event (participation and position bound)
    half_spread_bps: Decimal
    impact_bps: Decimal


def economics(leg: Leg, q: int) -> tuple[Decimal, Decimal]:
    """(margin relief, execution cost) of one q-share fill, rounded as the engine posts it."""
    if q == 0:
        return Decimal(0), Decimal(0)
    with localcontext(CTX):
        price = fill_price(leg.mark, leg.side, 0, q, leg.volume, leg.half_spread_bps, leg.impact_bps)
        cost = abs(cents(price * q) - cents(leg.mark * q))
        return cents(leg.rate * leg.mark * q) - cost, cost


def _quantity_at(leg: Leg, mu: Decimal) -> int:
    """Whole shares where marginal cost reaches mu times marginal margin released."""
    if leg.cap <= 0 or leg.volume <= 0:
        return 0
    with localcontext(CTX):
        a = leg.mark * leg.half_spread_bps / 10_000
        b = leg.mark * leg.impact_bps / (10_000 * Decimal(leg.volume) ** 2)
        room = mu * leg.rate * leg.mark - a
        if room <= 0:
            return 0
        if b == 0:
            return leg.cap
        q = (room / (3 * b)).sqrt().to_integral_value(rounding=ROUND_FLOOR)
        return min(leg.cap, int(q))


def allocate(legs: list[Leg], mu: Decimal) -> dict[str, int]:
    return {leg.sym: _quantity_at(leg, mu) for leg in legs}


def relief(legs: list[Leg], plan: dict[str, int]) -> Decimal:
    return sum((economics(leg, plan[leg.sym])[0] for leg in legs), Decimal(0))


def cost(legs: list[Leg], plan: dict[str, int]) -> Decimal:
    return sum((economics(leg, plan[leg.sym])[1] for leg in legs), Decimal(0))


def solve(legs: list[Leg], target: Decimal) -> dict[str, int]:
    """Cheapest whole-share reductions releasing ``target`` margin, else the maximum-relief plan.

    The caller decides what an uncurable event means; the returned plan is never
    larger than the maximum-relief point, so it never sells into negative relief.
    """
    if target <= 0:
        return {leg.sym: 0 for leg in legs}
    with localcontext(CTX):
        lo, hi = Decimal(0), Decimal(1)
        if relief(legs, allocate(legs, hi)) < target:
            return allocate(legs, hi)
        for _ in range(ITERATIONS):
            mid = (lo + hi) / 2
            if relief(legs, allocate(legs, mid)) >= target:
                hi = mid
            else:
                lo = mid
        plan = allocate(legs, hi)
        # Flooring can overshoot by up to one share per leg; give back any share
        # whose removal still leaves the target met, costliest marginal share first.
        for leg in sorted(legs, key=lambda g: -_last_share_ratio(g, plan[g.sym])):
            low, high = 0, plan[leg.sym]
            while low < high:
                mid_q = (low + high) // 2
                if relief(legs, {**plan, leg.sym: mid_q}) >= target:
                    high = mid_q
                else:
                    low = mid_q + 1
            plan[leg.sym] = low
        return _improve(legs, plan, target)


def _improve(legs: list[Leg], plan: dict[str, int], target: Decimal) -> dict[str, int]:
    """Local search over single decrements and one-for-one swaps that keep the target met.

    ponytail: first-improvement pairwise search, O(legs^2) per pass; the integer
    rounding of the continuous optimum is the only thing it corrects. Add a
    proper integer solver only if books grow beyond a handful of instruments.
    """
    cost_now = cost(legs, plan)
    improved = True
    while improved:
        improved = False
        for i in legs:
            for d in range(1, plan[i.sym] + 1):
                base = {**plan, i.sym: plan[i.sym] - d}
                # Pure decrement, then decrement plus the smallest feasible top-up of each other leg.
                options = [base] if relief(legs, base) >= target else []
                for j in legs:
                    if j is i or base[j.sym] >= j.cap:
                        continue
                    lo, hi = 1, j.cap - base[j.sym]
                    if relief(legs, {**base, j.sym: base[j.sym] + hi}) < target:
                        continue
                    while lo < hi:
                        mid = (lo + hi) // 2
                        if relief(legs, {**base, j.sym: base[j.sym] + mid}) >= target:
                            hi = mid
                        else:
                            lo = mid + 1
                    options.append({**base, j.sym: base[j.sym] + lo})
                for trial in options:
                    trial_cost = cost(legs, trial)
                    if trial_cost < cost_now:
                        plan, cost_now, improved = trial, trial_cost, True
                        break
                if improved:
                    break
            if improved:
                break
    return plan


def _last_share_ratio(leg: Leg, q: int) -> Decimal:
    if q == 0:
        return Decimal(0)
    r1, c1 = economics(leg, q)
    r0, c0 = economics(leg, q - 1)
    dr = r1 - r0
    return (c1 - c0) / dr if dr > 0 else Decimal(10**9)
