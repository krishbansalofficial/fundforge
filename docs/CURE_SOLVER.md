# Minimum-impact margin cure

Status: implemented in `backend/src/fundforge/cure.py`, used by `liquidity.py`. Oracle tests in `backend/tests/test_cure_oracle.py`.

## Problem

For one execution event, each leg reduces one position by `q_i` whole shares.

- Event cost `C_i(q) = a_i q + b_i q^3`: half-spread plus cubic impact (FUND_ACCOUNTING §8). Rounding is applied exactly as the engine posts fills, via `execution.fill_price` and `money.cents`.
- Maintenance relief `R_i(q) = r_i q - C_i(q)`, where `r_i` is the maintenance rate times mark.

```
minimise   sum_i C_i(q_i)
subject to sum_i R_i(q_i) >= target
           0 <= q_i <= cap_i
```

## Method

1. The problem is convex. Its KKT condition is `C_i'(q_i) = mu * r_i` with one shared multiplier `mu` in `[0, 1]`. `mu = 1` is the maximum-relief point.
2. Total relief is monotone in `mu`, so `mu` is found by 80-step bisection in Decimal (below 1e-24). There is no tolerance test.
3. Each leg's quantity at `mu` is `min(cap, floor(sqrt((mu r - a) / 3b)))`, then whole shares are floored.
4. Flooring can overshoot the target. Each leg gives back shares by binary search while the target still holds, costliest marginal share first.
5. A local search (`_improve`) tries single decrements and one-for-one top-ups, keeping the target met and accepting only lower cost.

If the target is unreachable, `solve` returns the maximum-relief plan. The caller decides what an uncurable event means. A zero target sells nothing.

## Checks

| Oracle | Test | Bound |
|---|---|---|
| CVXPY continuous optimum (dev-only lower bound) | `test_solver_cost_within_tolerance_of_convex_optimum`, 40 books | cost ≤ 1.10 × optimum + one average share per leg + one cent |
| Exhaustive integer enumeration on tiny books | `test_solver_matches_exhaustive_integer_oracle_on_tiny_books`, 60 books | cost ≤ optimum + $0.15 |
| Cost/relief greedy | `test_solver_never_costlier_than_greedy`, 60 books | cost ≤ greedy cost |
| Edge cases | zero and unreachable targets | exact |
| Import boundary | `test_runtime_code_does_not_import_cvxpy` | no `cvxpy` under `src/` |

The tolerances are measured figures, not guarantees. Over 300 random books the median gap to the convex optimum was 0.09% and the worst was 7.5% on small caps. The worst gap to the integer optimum on tiny books was $0.13.

## Limits

- `ponytail:` the local search is first-improvement pairwise, O(legs²) per pass. Rounding is the only thing it corrects. Add a proper integer solver only if books grow beyond a handful of instruments.
- The solver is greedy in the sense that it finds a local optimum of the integer problem. No global-optimum claim is made.
- CVXPY is a test oracle only. It is not economic authority and is not imported at runtime.
- Public assumptions (rates, spreads, impact coefficients) are caller-supplied. The solver never reads undisclosed future tape.
