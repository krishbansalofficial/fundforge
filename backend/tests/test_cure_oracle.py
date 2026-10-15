"""Oracle tests for the minimum-impact cure solver (docs/CURE_SOLVER.md).

CVXPY is a dev-only oracle: runtime code under src/ never imports it.
Three oracles: (1) CVXPY continuous optimum as a lower bound, (2) exhaustive
integer enumeration on tiny books, (3) a cost/relief greedy that the solver must
never exceed when the greedy meets the target.
"""

import itertools
import random
from decimal import Decimal

import cvxpy as cp
import pytest

from fundforge.cure import Leg, allocate, economics, relief, solve

D = Decimal


def random_book(rng: random.Random, n: int, max_cap: int) -> list[Leg]:
    legs = []
    for i in range(n):
        volume = rng.randint(500, 5000)
        legs.append(Leg(
            sym=f"S{i}", side=rng.choice(["SELL", "COVER"]),
            mark=D(str(round(rng.uniform(5, 200), 2))),
            rate=D(str(round(rng.uniform(0.05, 0.6), 3))),
            volume=volume, cap=rng.randint(1, max_cap),
            half_spread_bps=D(str(round(rng.uniform(0, 40), 2))),
            impact_bps=D(str(round(rng.uniform(0, 4000), 1))),
        ))
    return legs


def max_relief(legs: list[Leg]) -> Decimal:
    return sum((economics(leg, leg.cap)[0] if relief_positive(leg) else D(0) for leg in legs), D(0))


def relief_positive(leg: Leg) -> bool:
    return economics(leg, leg.cap)[0] > 0


def cvx_optimum(legs: list[Leg], target: Decimal) -> float:
    """Continuous lower bound: min sum a q + b q^3 s.t. sum (r m q - a q - b q^3) >= target."""
    # x_i = q_i / cap_i in [0, 1] keeps the cubic terms well scaled for the solver.
    x = cp.Variable(len(legs), nonneg=True)
    cost_terms, rel_terms = [], []
    for i, leg in enumerate(legs):
        k = float(leg.cap)
        a = float(leg.mark * leg.half_spread_bps / 10_000) * k
        b = float(leg.mark * leg.impact_bps / (10_000 * D(leg.volume) ** 2)) * k**3
        r = float(leg.rate * leg.mark) * k
        cost_terms.append(a * x[i] + b * cp.power(x[i], 3))
        rel_terms.append(r * x[i] - a * x[i] - b * cp.power(x[i], 3))
    prob = cp.Problem(cp.Minimize(sum(cost_terms)),
                      [x <= 1, sum(rel_terms) >= float(target)])
    prob.solve(solver=cp.CLARABEL)
    assert prob.status == cp.OPTIMAL, prob.status
    return float(prob.value)


def plan_cost(legs: list[Leg], plan: dict[str, int]) -> Decimal:
    return sum((economics(leg, plan[leg.sym])[1] for leg in legs), D(0))


def feasible(legs: list[Leg], plan: dict[str, int], target: Decimal) -> bool:
    return relief(legs, plan) >= target


def greedy(legs: list[Leg], target: Decimal) -> dict[str, int] | None:
    """Cost-per-relief greedy in the style of liquidity.project; None when target unmet."""
    plan = {leg.sym: 0 for leg in legs}
    while relief(legs, plan) < target:
        best = None
        for leg in legs:
            cur = plan[leg.sym]
            if cur >= leg.cap:
                continue
            base_r, base_c = economics(leg, cur)
            need = target - relief(legs, plan) + base_r
            lo, hi = cur + 1, leg.cap
            while lo < hi:
                mid = (lo + hi) // 2
                if economics(leg, mid)[0] >= need:
                    hi = mid
                else:
                    lo = mid + 1
            r, c = economics(leg, lo)
            dr = r - base_r
            if dr <= 0:
                continue
            key = (c - base_c) / dr
            if best is None or key < best[0]:
                best = (key, leg.sym, lo)
        if best is None:
            return None
        plan[best[1]] = best[2]
    return plan


def exhaustive(legs: list[Leg], target: Decimal) -> Decimal | None:
    best = None
    for combo in itertools.product(*[range(leg.cap + 1) for leg in legs]):
        plan = {leg.sym: q for leg, q in zip(legs, combo, strict=True)}
        if feasible(legs, plan, target):
            c = plan_cost(legs, plan)
            if best is None or c < best:
                best = c
    return best


@pytest.mark.parametrize("seed", range(40))
def test_solver_cost_within_tolerance_of_convex_optimum(seed):
    rng = random.Random(seed)
    legs = random_book(rng, rng.randint(2, 5), 400)
    target = max_relief(legs) * D(str(round(rng.uniform(0.05, 0.9), 3)))
    if target <= 0:
        pytest.skip("no positive relief in this book")
    plan = solve(legs, target)
    assert feasible(legs, plan, target)
    cost = float(plan_cost(legs, plan))
    opt = cvx_optimum(legs, target)
    # Stated tolerance: integer shares and cent rounding may add cost. Measured over
    # 300 books: median relative gap 0.09%, worst 7.5% (small caps). Bound: 10% plus
    # one average share's cost per leg and a cent of rounding.
    slack = sum(float(economics(leg, plan[leg.sym])[1]) / max(plan[leg.sym], 1) + 0.01
                for leg in legs) + 0.01
    assert opt - 1e-6 <= cost <= opt * 1.10 + slack, (cost, opt)


@pytest.mark.parametrize("seed", range(60))
def test_solver_matches_exhaustive_integer_oracle_on_tiny_books(seed):
    rng = random.Random(1000 + seed)
    legs = random_book(rng, rng.randint(1, 3), 6)
    target = max_relief(legs) * D(str(round(rng.uniform(0.05, 1.0), 3)))
    if target <= 0:
        pytest.skip("no positive relief in this book")
    best = exhaustive(legs, target)
    if best is None:
        pytest.skip("target not reachable with integer shares")
    plan = solve(legs, target)
    assert feasible(legs, plan, target)
    # Stated tolerance: $0.15 absolute. Measured over 300 tiny books: worst gap $0.13;
    # the local search cannot always reach a three-leg integer mix (docs/CURE_SOLVER.md).
    assert plan_cost(legs, plan) <= best + D("0.15"), (plan, best)


@pytest.mark.parametrize("seed", range(60))
def test_solver_never_costlier_than_greedy(seed):
    rng = random.Random(2000 + seed)
    legs = random_book(rng, rng.randint(2, 6), 400)
    target = max_relief(legs) * D(str(round(rng.uniform(0.05, 0.9), 3)))
    if target <= 0:
        pytest.skip("no positive relief in this book")
    g = greedy(legs, target)
    if g is None:
        pytest.skip("greedy cannot reach target")
    plan = solve(legs, target)
    assert feasible(legs, plan, target)
    assert plan_cost(legs, plan) <= plan_cost(legs, g), (plan, g)


def test_zero_target_sells_nothing_and_unreachable_target_returns_max_relief_plan():
    legs = random_book(random.Random(7), 3, 50)
    assert all(q == 0 for q in solve(legs, D(0)).values())
    assert solve(legs, D("1e12")) == allocate(legs, D(1))


def test_runtime_code_does_not_import_cvxpy():
    import pathlib

    src = pathlib.Path(__file__).parents[1] / "src" / "fundforge"
    assert not any("cvxpy" in p.read_text(encoding="utf-8") for p in src.rglob("*.py"))
