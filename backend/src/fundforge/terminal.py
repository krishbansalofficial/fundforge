"""Read-only, as-of research terminal. No tape lookahead, writes, or execution authority.

Prices are processed-event marks, NOT exchange ticks or OHLC bars. Volume is the
authored capacity for that observed event, NOT realized exchange trading volume.
Stress is a static mark-to-market exercise at current maintenance rates.
"""

import copy
from decimal import Decimal, localcontext
from typing import Any

from .engine import Engine, Loan
from .execution import BUY_SIDES
from .generator import MACRO_SERIES, Spec
from .money import CTX, D, cents
from .research import regime_question

TERMINAL_VERSION = "forge-terminal-v1"
HISTORY_LIMIT = 512
STRESSES = (
    ("broad_selloff", "Broad sell-off", "-0.10", "-0.10"),
    ("short_squeeze", "Short squeeze", "0", "0.20"),
    ("flight_to_cash", "Longs -15%, shorts +10%", "-0.15", "0.10"),
)


def stress(e: Engine, long_shock: str, short_shock: str) -> dict[str, str | bool | None]:
    """Current holdings shocked by side; no trades, fees, collateral releases or future events.

    All inputs here are fixed presets, not player commands. Keep calculations in
    the domain's context; client floats only format the resulting Decimal strings.
    """
    with localcontext(CTX):
        lm, sm = e.long_mv(), e.short_mv()
        sl, ss = D(long_shock), D(short_shock)
        pnl = lm * sl - sm * ss
        nav = e.nav() + pnl
        req = e.margin(long_mv=lm * (1 + sl), short_mv=sm * (1 + ss))
        return {
            "long_shock": long_shock, "short_shock": short_shock,
            "pnl": str(cents(pnl)), "nav": str(cents(nav)), "maintenance_req": str(cents(req)),
            "headroom": str(cents(nav - req)), "margin_breach": nav < req,
            "gross": str(((lm * (1 + sl) + sm * (1 + ss)) / nav).quantize(D("0.0001")))
                     if nav > 0 else None,
        }


def trading_pnl(e: Engine) -> dict[str, Any]:
    """Per-security trading P&L since the fund opened, at observed marks: value now - value at the opening
    reference marks - cash paid for buys/covers + cash received for sells/shorts (fill amounts, incl. impact).
    Excludes borrow fees, financing, fund expenses and fees. A security whose position does not reconcile with
    opening + fills reports pnl None instead of a number."""
    with localcontext(CTX):
        opening: dict[str, int] = e.tape.raw["opening"]["fund"]["positions"]
        ref = e.tape.events[0].marks
        rows, total = [], Decimal(0)
        for sym in sorted(e.marks):
            bought = sold = 0
            paid = received = Decimal(0)
            for o in e.orders:
                if o.sym != sym:
                    continue
                for f in o.fills:
                    if "qty" not in f:  # a rejection record, not a fill
                        continue
                    if o.side in BUY_SIDES:
                        bought, paid = bought + f["qty"], paid + D(f["amount"])
                    else:
                        sold, received = sold + f["qty"], received + D(f["amount"])
            q0, qty, mark = opening.get(sym, 0), e.pos[sym], e.marks[sym]
            ok = q0 + bought - sold == qty
            pnl = cents(qty * mark - q0 * D(ref[sym]) - paid + received) if ok else None
            if pnl is not None:
                total += pnl
            rows.append({"sym": sym, "opening_qty": q0, "reference_mark": str(ref[sym]), "bought": bought, "sold": sold,
                         "paid": str(paid), "received": str(received), "qty": qty, "mark": str(mark),
                         "pnl": None if pnl is None else str(pnl)})
        return {"rows": rows, "total": str(cents(total)),
                "method": "Value now - value at opening reference marks - buys + sells (fill amounts). "
                          "Excludes borrow fees, financing, fund expenses and fees."}


def snapshot(e: Engine, role: str | None = None) -> dict[str, Any]:
    """Projection from observed state only; private research is filtered by seat role.

    Never expose raw tape, unrevealed research, variant, future coefficients, rival
    holdings or a forecast of future event capacity. Returned data is detached.
    """
    with localcontext(CTX):
        nav = e.nav()
        samples = e.observations[-HISTORY_LIMIT:]
        latest = samples[-1] if samples else None
        prev = e.observations[-2] if len(e.observations) > 1 else latest
        first = e.observations[0] if e.observations else None
        rates: dict[str, list[Loan]] = {ln.sym: [] for ln in e.loans}
        for ln in e.loans:
            rates[ln.sym].append(ln)
        quotes = []
        for sym in sorted(e.marks):
            mark, qty = e.marks[sym], e.pos[sym]
            before = D(prev["marks"][sym]) if prev else mark
            opening = D(first["marks"][sym]) if first else mark
            loans = rates.get(sym, [])
            borrowed = sum(ln.qty for ln in loans)
            borrow_rate = sum((ln.qty * ln.rate for ln in loans), Decimal(0)) / borrowed if borrowed else None
            quotes.append({
                "sym": sym, "mark": str(mark), "qty": qty, "mv": str(cents(qty * mark)),
                "change_bps": str(((mark / before - 1) * 10000).quantize(D("0.1"))) if before else None,
                "since_start_bps": str(((mark / opening - 1) * 10000).quantize(D("0.1"))) if opening else None,
                "weight": str((qty * mark / nav).quantize(D("0.0001"))) if nav > 0 else None,
                "borrowed": borrowed, "borrow_rate": str(borrow_rate) if borrow_rate is not None else None,
                "observed_event_volume": latest["volume"].get(sym, 0) if latest else None,
            })
        return {
            "schema": TERMINAL_VERSION,
            "finished": e.finished(),
            "role": role,
            "as_of": {"event": e.cursor, "day": e.ev.day, "date": e.ev.date.isoformat(), "phase": e.ev.phase},
            "source": "synthetic processed-event marks",
            "quotes": quotes,
            "history": [{"event": x["event"], "day": x["day"], "date": x["date"], "phase": x["phase"],
                         "marks": dict(x["marks"])} for x in samples],
            "history_truncated": len(e.observations) > HISTORY_LIMIT,
            "risk": {
                "controls": e.control_report(),
                "certification": e.certification(),
                "nav": str(nav), "long_mv": str(e.long_mv()), "short_mv": str(e.short_mv()),
                "maintenance_req": str(e.margin()), "headroom": str(cents(nav - e.margin())),
                "cash": str(e.bal("cash")), "restricted_collateral": str(e.bal("collateral")),
                "debt": str(-e.bal("debt")), "credit_left": str(e.credit_left()),
                "maintenance_rates": {k: str(v) for k, v in e.tape.margin(e.ev.day)["maintenance"].items()},
                "stress_method": "Static side shocks at current maintenance rates; excludes trading and financing.",
                "stresses": [{"id": sid, "label": label, **stress(e, ls, ss)} for sid, label, ls, ss in STRESSES],
            },
            "news": [{**copy.deepcopy(n), "visibility": "private" if n["refs"].get("owner")
                      and n["refs"].get("topic") not in e.shared_research else "shared"}
                     for n in e.visible_notices(role)[-100:]],
            "incidents": copy.deepcopy(e.incident_events[-100:]),
            "orders": [{"order_id": o.order_id, "sym": o.sym, "side": o.side, "qty": o.qty,
                        "filled": o.filled, "remaining": o.remaining, "status": o.status,
                        "forced": o.forced, "fills": [dict(f) for f in o.fills]} for o in e.orders[-100:]],
            "league": [dict(r) for r in e.league()],
            "pnl": trading_pnl(e),
            # Indicator prints published by today; a later revision stays hidden until its own day.
            "macro": [{"series": o.instrument, "period_day": o.event_time, "published_day": o.available_at,
                       "revision": o.revision, "value": str(o.value)} for o in e.tape.macro.known(e.ev.day)],
            # Generated markets only: the live regime question from the same published prints (rooms use Spec()).
            "regime": regime_question(e.tape.macro.known(e.ev.day, MACRO_SERIES), Spec()),
        }
