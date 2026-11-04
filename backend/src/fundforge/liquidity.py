"""Detached liquidation scenarios using public, frozen assumptions, never future tape.

"cost" and "longs_first" are bounded greedy comparisons. "min_impact" solves each
event's cheapest cure with cure.solve: optimal per event
under frozen assumptions, not a multi-event or forecast optimum.
Only the first event's legs form a draft; normal live governance must approve it.
"""

import copy
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal, localcontext
from typing import Any

from .cure import Leg, economics, solve
from .engine import Engine, Order, Side
from .execution import PRICE, capacity
from .money import CTX, D, cents
from .series import mgmt_fee_exact

STRATEGIES = ("cost", "longs_first", "min_impact")


def _leg(e: Engine, sym: str, volume: int) -> Leg:
    """Public as-of terms for reducing one position in the next hypothetical event."""
    held = e.pos[sym]
    return Leg(sym, "SELL" if held > 0 else "COVER", e.marks[sym],
               e.tape.margin(e.ev.day)["maintenance"]["long" if held > 0 else "short"], volume,
               min(abs(held), capacity(volume, D(e.cfg["participation"]), 0)),
               D(e.cfg["half_spread_bps"]), D(e.cfg["impact_bps"]))


def _quantity(leg: Leg, target: Decimal) -> tuple[int, Decimal, Decimal]:
    """Smallest sufficient single-instrument cure, or its full available capacity."""
    cap = leg.cap
    relief, cost = economics(leg, cap)
    if relief <= 0:
        return 0, relief, cost
    # Supported scenario coefficients keep relief monotone across participation.
    # If the conservative maximum marginal impact exceeds maintenance relief,
    # decline the instrument rather than make a false bisection claim.
    marginal = (leg.half_spread_bps + 3 * leg.impact_bps * (D(cap) / leg.volume) ** 2) / 10000
    if leg.rate <= marginal:
        return 0, D(0), D(0)
    if relief >= target:
        lo, hi = 1, cap
        while lo < hi:
            mid = (lo + hi) // 2
            if economics(leg, mid)[0] >= target:
                hi = mid
            else:
                lo = mid + 1
        cap = lo
        relief, cost = economics(leg, cap)
    return cap, relief, cost


def project(source: Engine, long_shock: str = "-0.15", short_shock: str = "0.10",
            horizon: int = 5, volume_scale: str = "1", strategy: str = "cost") -> dict[str, Any]:
    """One hypothetical execution event per business day; current terms held fixed."""
    with localcontext(CTX):
        ls, ss, scale = D(long_shock), D(short_shock), D(volume_scale)
        if not (-D("0.9") <= ls <= 1 and -D("0.9") <= ss <= 1
                and D("0.1") <= scale <= 2 and 1 <= horizon <= 10 and strategy in STRATEGIES):
            raise ValueError("invalid liquidity assumptions")
        observed = next((o for o in reversed(source.observations) if o["volume"]), None)
        volumes = {s: int((observed["volume"].get(s, 0) if observed else 0) * scale) for s in source.pos}
        e = copy.deepcopy(source)
        # Freeze terms at the as-of date. No advance(), future event, rate change,
        # rival trade, upcoming recall, dealing date or future capacity is read.
        terms = source.tape.margin(source.ev.day)
        e.tape = replace(e.tape, events=(), raw={**e.tape.raw, "margin_schedule": [
            {"from_day": 0, **{kind: {k: str(v) for k, v in rates.items()} for kind, rates in terms.items()}}]})
        e.orders = []
        e.marks = {s: (mark * (1 + (ls if e.pos[s] > 0 else ss if e.pos[s] < 0 else 0))).quantize(PRICE)
                   for s, mark in e.marks.items()}
        e._remark()
        e._true_up_collateral()
        opening_nav = e.nav()
        total_cost = D(0)
        path: list[dict[str, Any]] = []
        draft: list[dict[str, Any]] = []
        status = "horizon_exhausted"

        def fill(sym: str, q: int) -> None:
            nonlocal total_cost
            side: Side = "SELL" if e.pos[sym] > 0 else "COVER"
            o = Order(f"lab-{step}-{sym}", sym, side, q, forced="hypothetical")
            e._fill(o)
            if o.filled:
                total_cost += abs(D(o.fills[0]["amount"]) - cents(e.marks[sym] * o.filled))
                fills.append({"sym": sym, "side": side, "qty": o.filled, "price": o.fills[0]["price"]})
                if step == 1:
                    draft.append({"sym": sym, "side": side, "qty": o.filled})

        for step in range(1, horizon + 1):
            dt = e.ev.date + timedelta(days=1)
            while dt.weekday() >= 5:
                dt += timedelta(days=1)
            e.ev = replace(e.ev, day=e.ev.day + 1, date=dt, phase="EXEC_A", volume=volumes)
            next_date = dt + timedelta(days=1)
            while next_date.weekday() >= 5:
                next_date += timedelta(days=1)
            for p in list(e.pending):
                if p.settle_day <= e.ev.day and e._settle(p):
                    e.pending.remove(p)
            daily_carry = (sum((ln.qty * e.marks[ln.sym] * ln.rate / 360 for ln in e.loans), D(0))
                           + -e.bal("debt") * D(e.cfg["debit_rate"]) / 360
                           + sum((mgmt_fee_exact(s) for s in e.series if s.units > 0), D(0)))
            cushion = cents(daily_carry * (next_date - dt).days) + D("0.02") * (len(e.loans) + len(e.series) + 1)
            e.event_fills = {}
            fills: list[dict[str, Any]] = []
            remaining = {s for s, q in e.pos.items() if q}
            if strategy == "min_impact" and e.deficit() > 0 and e.nav() > 0:
                plan = solve([_leg(e, sym, volumes[sym]) for sym in sorted(remaining) if volumes[sym]],
                             e.deficit() + cushion)
                for sym, q in sorted(plan.items()):
                    if q:
                        fill(sym, q)
            while strategy != "min_impact" and e.deficit() > 0 and remaining and e.nav() > 0:
                candidates = []
                for sym in sorted(remaining):
                    q, relief, cost = _quantity(_leg(e, sym, volumes[sym]), e.deficit() + cushion)
                    if q:
                        priority = (strategy == "longs_first" and e.pos[sym] < 0, cost / relief)
                        candidates.append((priority, sym, q))
                if not candidates:
                    break
                _, sym, q = min(candidates)
                remaining.remove(sym)
                fill(sym, q)
            e._true_up_collateral()
            e.reconcile()
            funded = e.bal("collateral") >= e._collateral_target()
            settled = not e.pending
            path.append({"event": step, "nav": str(e.nav()), "headroom": str(cents(e.nav() - e.margin())),
                         "cash": str(e.bal("cash")), "debt": str(-e.bal("debt")),
                         "credit_left": str(e.credit_left()), "collateral_funded": funded,
                         "pending_settlements": len(e.pending), "fills": fills})
            if e.nav() <= 0:
                status = "insolvent"
                break
            if e.deficit() == 0 and funded and settled:
                status = "cured"
                break
            if not observed:
                status = "no_observed_capacity"
                break
            if step == horizon:
                break
            # Carry all calendar dates until the following business event. Current
            # rates only; journal and LP allocation follow the existing kernel.
            accrual_date = dt
            while accrual_date < next_date:
                e._accrue_date(accrual_date)
                accrual_date += timedelta(days=1)
        return {"strategy": strategy, "status": status, "events_to_cure": len(path) if status == "cured" else None,
                "insolvent_at_event": len(path) if status == "insolvent" else None,
                "shock_nav": str(opening_nav), "execution_cost": str(cents(total_cost)),
                "path": path, "draft": draft,
                "assumptions": {"long_shock": long_shock, "short_shock": short_shock, "horizon": horizon,
                                "volume_scale": volume_scale,
                                "volume_source_event": observed["event"] if observed else None,
                                "volumes": volumes,
                                "maintenance_rates": {k: str(v) for k, v in terms["maintenance"].items()},
                                "method": "Frozen marks and rates; one event per business day; last observed volume; "
                                "T+1 settlement, collateral, credit and calendar carry "
                                "with one-interval carry cushion. "
                                "Excludes future news, rivals, "
                                "new recalls, investor flows and scheduled invoices. "
                                + ("Per-event minimum-impact cure by marginal-cost bisection; "
                                   "not a multi-event optimum or forecast." if strategy == "min_impact"
                                   else "Greedy comparison, not an optimal forecast.")}}
