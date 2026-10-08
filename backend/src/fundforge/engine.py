"""Deterministic Case1 session engine: dated phases, execution, settlement, accrual, dealing.

All economics flow through the journal. Positions, loans and series are kept as
state and reconciled against journal balances after every event (``reconcile``),
so a posting bug cannot hide behind a balanced trial balance.

Players act only at decision barriers (before EXEC_A / EXEC_B). Orders accepted at a
barrier execute at the next execution event, never at an already-published mark.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, localcontext

from .execution import BUY_SIDES, capacity, fill_price
from .journal import Journal, entry
from .money import CTX, D, Accrual, allocate, cents
from .series import Series, mgmt_fee_exact, redeem, reprovision
from .tape import EXEC_PHASES, MarketEvent, Tape

SIDES = ("BUY", "SELL", "SHORT", "COVER")
# Bump on ANY change to economic rules; rooms created under another version are refused, never re-derived.
RULES_VERSION = "case1-rules-2026.10.1"


class CommandRejected(ValueError):
    pass


@dataclass
class Order:
    order_id: str
    sym: str
    side: str
    qty: int
    limit: Decimal | None = None
    forced: str | None = None  # "recall" | "margin" for engine-generated orders
    filled: int = 0
    status: str = "QUEUED"
    fills: list = field(default_factory=list)

    @property
    def remaining(self) -> int:
        return self.qty - self.filled


@dataclass
class Loan:
    loan_id: str
    sym: str
    qty: int
    rate: Decimal


@dataclass
class Pending:
    settle_day: int
    kind: str
    sym: str
    qty: int
    amount: Decimal
    frozen: Decimal = Decimal(0)


class Engine:
    def __init__(self, tape: Tape):
        self.tape = tape
        r = tape.raw
        self.cfg = r["defaults"]
        self.start, self.end = r["calendar"]["start_day"], r["calendar"]["end_day"]
        self.j = Journal()
        self.cursor = 0
        self.seq = 0
        self.ev: MarketEvent = tape.events[0]
        self.marks = dict(tape.events[0].marks)
        self.pos: dict[str, int] = {s: 0 for s in tape.instruments}
        self.loans: list[Loan] = []
        self.pending: list[Pending] = []
        self.orders: list[Order] = []
        self.accruals: dict[str, Accrual] = {}
        self.event_fills: dict[tuple[str, str], int] = {}
        self.notices: list[dict] = []
        self.research_used: list[dict] = []
        self.offer_visible = False
        self.replacement_accepted = False
        self.recall_open = 0
        self.recall_resolved_by: str | None = None
        self.margin_call: Decimal | None = None
        self.reserve: Decimal | None = None  # None => default 2% NAV buffer (FUND_ACCOUNTING §4)
        self.incidents: list[str] = []
        self.paid: dict[str, Decimal] = {}
        self._open()

    # ---------- journal helpers ----------
    def _eid(self) -> str:
        self.seq += 1
        return f"{self.ev.date.isoformat()}/{self.ev.phase}/{self.seq:04d}"

    def _post(self, memo: str, *legs, entity: str = "fund", date_: date | None = None):
        legs = [(a, x) for a, x in legs if x != 0]
        if legs:
            self.j.post(entry(self._eid(), entity, (date_ or self.ev.date).isoformat(), memo, *legs))

    def _post_pair(self, memo, fund_legs, firm_legs, date_=None):
        d = (date_ or self.ev.date).isoformat()
        fund_legs = [(a, x) for a, x in fund_legs if x != 0]
        firm_legs = [(a, x) for a, x in firm_legs if x != 0]
        if not fund_legs:
            return
        self.j.post_many([entry(self._eid(), "fund", d, memo, *fund_legs), entry(self._eid(), "firm", d, memo, *firm_legs)])

    def bal(self, account: str, entity: str = "fund") -> Decimal:
        return self.j.balance(entity, account)

    # ---------- opening ----------
    def _open(self):
        o = self.tape.raw["opening"]
        f = o["fund"]
        for s, q in f["positions"].items():
            self.pos[s] = q
            if q < 0:
                self.loans.append(Loan(f"L-open-{s}", s, -q, D(self.cfg["borrow_rate"])))
        long_mv = sum(cents(q * self.marks[s]) for s, q in self.pos.items() if q > 0)
        short_mv = sum(cents(-q * self.marks[s]) for s, q in self.pos.items() if q < 0)
        cash, coll, debt = D(f["cash"]), D(f["collateral"]), D(f["debt"])
        nav = long_mv + coll + cash - short_mv - debt
        total_units = sum(D(x["units"]) for x in f["series"])
        caps = allocate(nav, {x["id"]: D(x["units"]) for x in f["series"]})
        self.series = [Series(x["id"], D(x["units"]), D(x["hwm"]), caps[x["id"]]) for x in f["series"]]
        assert total_units > 0
        self._post(
            "Warm-start opening book (inherited positions at reference marks)",
            ("long_securities", long_mv), ("collateral", coll), ("cash", cash),
            ("short_liability", -short_mv), ("debt", -debt),
            *[(f"capital:{s.series_id}", -s.net) for s in self.series],
        )
        fo = o["firm"]
        fc, pp = D(fo["cash"]), D(fo["payroll_payable"])
        self._post("Management company opening book", ("cash", fc), ("payroll_payable", -pp),
                   ("owner_capital", -(fc - pp)), entity="firm")

    # ---------- derived values ----------
    def long_mv(self):
        return sum((cents(q * self.marks[s]) for s, q in self.pos.items() if q > 0), Decimal(0))

    def short_mv(self):
        return sum((cents(-q * self.marks[s]) for s, q in self.pos.items() if q < 0), Decimal(0))

    def nav(self) -> Decimal:
        """Net NAV after provisions (assets - liabilities), valid intraday."""
        return -sum((v for a, v in self.j.balances("fund").items()
                     if a.startswith("capital:") or a == "common_pnl"), Decimal(0))

    def margin(self, kind="maintenance", long_mv=None, short_mv=None) -> Decimal:
        r = self.tape.margin(self.ev.day)[kind]
        lm = self.long_mv() if long_mv is None else long_mv
        sm = self.short_mv() if short_mv is None else short_mv
        return cents(r["long"] * lm + r["short"] * sm)

    def deficit(self) -> Decimal:
        return max(Decimal(0), self.margin() - self.nav())

    def borrowed(self, sym) -> int:
        return sum(l.qty for l in self.loans if l.sym == sym)

    def credit_left(self) -> Decimal:
        return D(self.cfg["credit_limit"]) + self.bal("debt")  # debt is a credit (negative) balance

    # ---------- cash primitives ----------
    def _raise_cash(self, amount: Decimal, why: str) -> Decimal:
        """Draw credit so unrestricted cash covers ``amount``; returns cash actually available."""
        short = amount - self.bal("cash")
        if short > 0:
            draw = min(short, self.credit_left())
            self._post(f"Draw credit line: {why}", ("cash", draw), ("debt", -draw))
        return min(amount, self.bal("cash"))

    def _repay_debt(self):
        known = -sum((self.bal(a) for a in ("redemption_payable", "mgmt_fee_payable", "perf_fee_payable",
                                            "interest_payable", "trade_payable")), Decimal(0))
        spare = self.bal("cash") - self.buffer() - known
        repay = min(spare, -self.bal("debt"))
        if repay > 0:
            self._post("Repay broker debit above treasury reserve", ("debt", repay), ("cash", -repay))

    def buffer(self) -> Decimal:
        return cents(D("0.02") * self.nav()) if self.reserve is None else self.reserve

    def _remark(self):
        dl = self.long_mv() - self.bal("long_securities")
        ds = -self.short_mv() - self.bal("short_liability")
        self._post("Mark positions to reference", ("long_securities", dl), ("short_liability", ds), ("common_pnl", -dl - ds))

    def _collateral_target(self) -> Decimal:
        """Per symbol: active short value less its own earmarked unsettled proceeds (never negative), plus frozen covers."""
        frozen = sum((p.frozen for p in self.pending if p.kind == "COVER"), Decimal(0))
        need = Decimal(0)
        for s, q in self.pos.items():
            mv = cents(-q * self.marks[s]) if q < 0 else Decimal(0)
            earmarked = sum((p.amount for p in self.pending if p.kind == "SHORT" and p.sym == s), Decimal(0))
            need += max(Decimal(0), mv - earmarked)
        return need + frozen

    def _true_up_collateral(self):
        diff = self._collateral_target() - self.bal("collateral")
        if diff > 0:
            got = self._raise_cash(diff, "short collateral top-up")
            self._post("Top up restricted short collateral", ("collateral", got), ("cash", -got))
            if got < diff:
                self.incidents.append(f"day {self.ev.day}: collateral shortfall {diff - got}")
        elif diff < 0:
            self._post("Release excess restricted collateral", ("cash", -diff), ("collateral", diff))

    # ---------- player-facing commands (authority checked by the governance layer) ----------
    def at_barrier(self) -> bool:
        return self.cursor < len(self.tape.events) and self.tape.events[self.cursor].phase in EXEC_PHASES

    def next_event(self) -> MarketEvent | None:
        return self.tape.events[self.cursor] if self.cursor < len(self.tape.events) else None

    def submit_order(self, order_id: str, sym: str, side: str, qty: int, limit: Decimal | None = None) -> Order:
        if not self.at_barrier():
            raise CommandRejected("orders are accepted only at a decision barrier")
        if sym not in self.pos or side not in SIDES or not isinstance(qty, int) or qty <= 0:
            raise CommandRejected(f"invalid order {side} {qty} {sym}")
        if any(o.order_id == order_id for o in self.orders):
            raise CommandRejected(f"duplicate order id {order_id}")
        o = Order(order_id, sym, side, qty, limit)
        self.orders.append(o)
        return o

    def cancel_order(self, order_id: str):
        o = next((o for o in self.orders if o.order_id == order_id and o.status in ("QUEUED", "PARTIALLY_FILLED")), None)
        if o is None:
            raise CommandRejected(f"no open order {order_id}")
        o.status = "CANCELED"

    def assign_research(self, topic: str):
        rs = self.tape.raw["research"]
        if not self.at_barrier():
            raise CommandRejected("research is assigned at a decision barrier")
        if topic not in rs["topics"] or any(r["topic"] == topic for r in self.research_used):
            raise CommandRejected(f"unknown or repeated research topic {topic!r}")
        if len(self.research_used) >= rs["budget"]:
            raise CommandRejected("research budget exhausted")
        self.research_used.append({"topic": topic, "assigned_day": self.ev.day, "reveal_day": self.ev.day + 1})

    def accept_replacement(self):
        off = self.tape.raw["borrow"]["replacement_offer"]
        nxt = self.next_event()
        if not self.offer_visible:
            raise CommandRejected("no replacement offer is known")
        if self.replacement_accepted:
            raise CommandRejected("replacement already accepted")
        if self.recall_open <= 0:
            raise CommandRejected("there is no open recall to replace")
        if nxt is None or (nxt.day, nxt.phase) > (off["accept_by_day"], off["accept_by_event"]):
            raise CommandRejected("replacement acceptance cutoff has passed")
        self.replacement_accepted = True

    def set_reserve(self, amount: Decimal):
        if amount < 0:
            raise CommandRejected("reserve must be non-negative")
        self.reserve = amount

    # ---------- event loop ----------
    def advance(self) -> list[MarketEvent]:
        """Process events up to the next decision barrier (or the end). Returns processed events."""
        done = []
        while self.cursor < len(self.tape.events):
            e = self.tape.events[self.cursor]
            if e.phase in EXEC_PHASES and done:
                break
            self.ev = e
            self.marks = dict(e.marks)
            getattr(self, "_" + e.phase.lower())()
            self.cursor += 1
            done.append(e)
            self.reconcile()
            if self.cursor < len(self.tape.events) and self.tape.events[self.cursor].phase in EXEC_PHASES:
                break
        return done

    def finished(self) -> bool:
        return self.cursor >= len(self.tape.events)

    def _notice(self, text: str, kind: str = "notice", code: str = "notice", **refs):
        """Typed notice: game logic and the world read ``code``/refs; ``text`` is presentation only."""
        self.notices.append({"code": code, "refs": refs, "day": self.ev.day, "date": self.ev.date.isoformat(), "phase": self.ev.phase,
                             "kind": kind, "text": text})

    def _publish_notices(self):
        for n in self.tape.raw["public_notices"]:
            if (n["day"], n["event"]) == (self.ev.day, self.ev.phase):
                self._notice(n["text"], code=n.get("code", "notice"))
        if self.ev.headline:
            self._notice(self.ev.headline, "market", code=self.ev.headline_code or "market_event")

    def _open_admin(self):
        self._publish_notices()
        day = self.ev.day
        for p in [p for p in self.pending if p.settle_day <= day]:
            if self._settle(p):
                self.pending.remove(p)
        off = self.tape.raw["borrow"]["replacement_offer"]
        if self.replacement_accepted and day == off["transfer_day"]:
            self._transfer_replacement(off)
        self._true_up_collateral()
        self._pay_due()
        self._repay_debt()

    def _public_mark(self):
        self._publish_notices()
        self._remark()
        rc = self.tape.raw["borrow"]["recall"]
        if self.ev.day == rc["announce_day"]:
            self.recall_open = rc["qty"]
        for r in self.research_used:
            if r["reveal_day"] == self.ev.day:
                self._notice(self.tape.raw["research"]["topics"][r["topic"]], "research", code="research_reveal", topic=r["topic"])
                if r["topic"] == "borrow":
                    self.offer_visible = True
        self._true_up_collateral()
        d = self.deficit()
        self.margin_call = d if d > 0 else None
        if d > 0:
            self._notice(f"Margin call: maintenance deficit ${d:,.2f}. Cure at the next execution or face forced liquidation.", "alert",
                         code="margin_call", deficit=str(d))

    def _exec_a(self):
        self._execute()

    def _exec_b(self):
        self._execute()

    def _close(self):
        self._remark()
        self._true_up_collateral()
        for o in self.orders:
            if o.status in ("QUEUED", "PARTIALLY_FILLED"):
                o.status = "EXPIRED"
        firm = self.tape.raw["firm"]
        self._post("Accrue partner payroll", ("payroll_expense", D(firm["payroll_per_business_day"])),
                   ("payroll_payable", -D(firm["payroll_per_business_day"])), entity="firm")
        if self.ev.day % firm["pay_every_n_days"] == 0:
            due = -self.bal("payroll_payable", "firm")
            paid = min(due, self.bal("cash", "firm"))
            self._post("Pay weekly payroll from firm cash", ("payroll_payable", paid), ("cash", -paid), entity="firm")
            if paid < due:
                self.incidents.append(f"day {self.ev.day}: firm payroll unpaid {due - paid}")
        self._accrue_date(self.ev.date)
        if self.ev.day % 20 == 0:
            self._invoice()
        self._deal()
        nxt = self.next_event_after_close()
        d = self.ev.date + timedelta(days=1)
        while nxt and d < nxt:
            self._accrue_date(d)
            d += timedelta(days=1)

    def next_event_after_close(self) -> date | None:
        i = self.cursor + 1
        return self.tape.events[i].date if i < len(self.tape.events) else None

    # ---------- execution ----------
    def _execute(self):
        self._remark()
        rc = self.tape.raw["borrow"]["recall"]
        deadline = (self.ev.day, self.ev.phase) == (rc["deadline_day"], rc["deadline_event"])
        queued = [o for o in self.orders if o.status in ("QUEUED", "PARTIALLY_FILLED")]
        for o in queued:
            self._fill(o)
        if deadline and self.recall_open > 0 and not self.replacement_accepted:
            self._forced("recall", rc["sym"], "COVER", min(self.recall_open, -self.pos[rc["sym"]]))
        if self.margin_call is not None and self.deficit() > 0:
            self._forced_margin()
        self._true_up_collateral()
        d = self.deficit()
        self.margin_call = d if d > 0 else None

    def _forced(self, why, sym, side, qty) -> Order | None:
        if qty <= 0:
            return None
        o = Order(f"forced-{why}-{self.ev.day}-{self.ev.phase}-{sym}", sym, side, qty, forced=why)
        self.orders.append(o)
        self._fill(o)
        if o.filled:
            self.incidents.append(f"day {self.ev.day} {self.ev.phase}: forced {why} {side} {o.filled} {sym}")
        if o.status != "FILLED":
            o.status = "EXPIRED"
        return o

    def _forced_margin(self):
        """Sell longs (largest market value first), then cover shorts, until maintenance is met."""
        r = self.tape.margin(self.ev.day)["maintenance"]
        longs = sorted((s for s, q in self.pos.items() if q > 0), key=lambda s: (-self.pos[s] * self.marks[s], s))
        shorts = sorted((s for s, q in self.pos.items() if q < 0), key=lambda s: (self.pos[s] * self.marks[s], s))
        for side, syms, rate in (("SELL", longs, r["long"]), ("COVER", shorts, r["short"])):
            for s in syms:
                d = self.deficit()
                if d <= 0:
                    return
                with localcontext(CTX):
                    relief = rate * self.marks[s] - self.marks[s] * D("0.002")  # conservative per-share relief
                    need = int(d / relief * D("1.05")) + 1
                self._forced("margin", s, side, min(need, abs(self.pos[s])))

    def _fill(self, o: Order):
        ev, s = self.ev, o.sym
        if o.status not in ("QUEUED", "PARTIALLY_FILLED"):
            return
        # reduce-only checks against current economic position
        held = self.pos[s]
        max_q = {"SELL": max(held, 0), "COVER": max(-held, 0)}.get(o.side, o.remaining)
        if o.side == "BUY" and held < 0 or o.side == "SHORT" and held > 0:
            return self._reject(o, "reverse the position with explicit close/open legs")
        if o.side == "SHORT":
            inv = self._short_inventory(s)
            max_q = min(max_q, inv)
            if inv <= 0:
                return self._reject(o, f"no borrow inventory for {s}")
        done = self.event_fills.get((s, "both"), 0)
        same = self.event_fills.get((s, "BUY" if o.side in BUY_SIDES else "SELL"), 0)
        cap = capacity(ev.volume.get(s, 0), D(self.cfg["participation"]), done)
        q = min(o.remaining, max_q, cap)
        hs, k = D(self.cfg["half_spread_bps"]), D(self.cfg["impact_bps"])
        while q > 0 and o.limit is not None:
            p = fill_price(self.marks[s], o.side, same, q, ev.volume[s], hs, k)
            if (p <= o.limit) if o.side in BUY_SIDES else (p >= o.limit):
                break
            q -= max(1, q // 20)
        if q <= 0:
            return
        price = fill_price(self.marks[s], o.side, same, q, ev.volume[s], hs, k)
        amount = cents(price * q)
        if o.side in ("BUY", "SHORT") and not o.forced:
            if not self._initial_margin_ok(s, o.side, q):
                return self._reject(o, "initial margin would be breached at execution")
        self._book(o, q, price, amount)
        self.event_fills[(s, "both")] = done + q
        self.event_fills[(s, "BUY" if o.side in BUY_SIDES else "SELL")] = same + q
        o.filled += q
        o.fills.append({"day": ev.day, "phase": ev.phase, "qty": q, "price": str(price), "amount": str(amount)})
        o.status = "FILLED" if o.remaining == 0 else "PARTIALLY_FILLED"
        if o.side == "COVER" and s == self.tape.raw["borrow"]["recall"]["sym"] and self.recall_open:
            covered = min(q, self.recall_open)
            self.recall_open -= covered
            if self.recall_open == 0 and self.recall_resolved_by is None:
                self.recall_resolved_by = "forced buy-in" if o.forced else "voluntary cover"

    def _reject(self, o: Order, why: str):
        o.status = "REJECTED"
        o.fills.append({"day": self.ev.day, "phase": self.ev.phase, "rejected": why})

    def _short_inventory(self, s) -> int:
        nn = self.tape.raw["borrow"]["no_new_inventory"]
        if s == nn["sym"] and self.ev.day >= nn["from_day"]:
            return 0
        opening_short = max(0, -self.tape.raw["opening"]["fund"]["positions"].get(s, 0))
        return opening_short + self.cfg["extra_borrow_inventory"] - self.borrowed(s) - sum(
            p.qty for p in self.pending if p.kind == "SHORT" and p.sym == s)

    def _initial_margin_ok(self, s, side, q) -> bool:
        add = cents(q * self.marks[s])
        lm, sm = self.long_mv(), self.short_mv()
        lm, sm = (lm + add, sm) if side == "BUY" else (lm, sm + add)
        return self.margin("initial", lm, sm) <= self.nav()

    def _next_business_day(self) -> int:
        return self.ev.day + 1

    def _book(self, o: Order, q: int, price: Decimal, amount: Decimal):
        s, t1 = o.sym, self._next_business_day()
        memo = f"{o.side} {q} {s} @ {price}" + (f" (forced {o.forced})" if o.forced else "")
        if o.side == "BUY":
            self._post(memo, ("long_securities", amount), ("trade_payable", -amount))
            self.pos[s] += q
        elif o.side == "SELL":
            self._post(memo, ("trade_receivable", amount), ("long_securities", -amount))
            self.pos[s] -= q
        elif o.side == "SHORT":
            self._post(memo, ("short_sale_receivable", amount), ("short_liability", -amount))
            self.pos[s] -= q
        else:
            self._post(memo, ("short_liability", amount), ("trade_payable", -amount))
            self.pos[s] += q
        frozen = cents(q * self.marks[s]) if o.side == "COVER" else Decimal(0)
        self.pending.append(Pending(t1, o.side, s, q, amount, frozen))
        self._remark()

    def _settle(self, p: Pending) -> bool:
        """Settle one obligation; on a cash shortfall record a failed settlement and keep it pending."""
        memo = f"Settle {p.kind} {p.qty} {p.sym}"
        if p.kind == "SELL":
            self._post(memo, ("cash", p.amount), ("trade_receivable", -p.amount))
        elif p.kind == "SHORT":
            self._post(memo, ("collateral", p.amount), ("short_sale_receivable", -p.amount))
            self.loans.append(Loan(f"L-{self.ev.day}-{p.sym}-{self.seq}", p.sym, p.qty, D(self.cfg["borrow_rate"])))
        elif p.kind == "BUY":
            got = self._raise_cash(p.amount, memo)
            if got < p.amount:
                self.incidents.append(f"day {self.ev.day}: failed settlement {memo}, short {p.amount - got}")
                return False
            self._post(memo, ("trade_payable", p.amount), ("cash", -p.amount))
        else:  # COVER: release frozen collateral to pay, return borrowed shares
            extra = p.amount - p.frozen
            if extra > 0 and self._raise_cash(extra, memo) < extra:
                self.incidents.append(f"day {self.ev.day}: failed settlement {memo}; borrow and collateral retained")
                return False
            self._post(memo, ("trade_payable", p.amount), ("collateral", -p.frozen), ("cash", p.frozen - p.amount))
            self._return_shares(p.sym, p.qty)
        return True

    def _return_shares(self, sym, qty):
        for l in sorted((l for l in self.loans if l.sym == sym), key=lambda l: (-l.rate, l.loan_id)):
            take = min(qty, l.qty)
            l.qty -= take
            qty -= take
        self.loans = [l for l in self.loans if l.qty > 0]

    def _transfer_replacement(self, off):
        q = min(off["qty"], self.recall_open)
        if q <= 0:
            self._notice("Replacement borrow not needed: the recall was already covered.", code="replacement_unneeded")
            return
        self._return_shares(off["sym"], q)
        self.loans.append(Loan(f"L-replacement-{off['sym']}", off["sym"], q, D(off["rate"])))
        covered = min(q, self.recall_open)
        self.recall_open -= covered
        if self.recall_open == 0 and self.recall_resolved_by is None:
            self.recall_resolved_by = "replacement borrow"
        self._notice(f"Replacement borrow settled: {q} {off['sym']} at {D(off['rate']) * 100}% replaces recalled shares.", code="replacement_settled", sym=off["sym"], qty=q)

    # ---------- accrual, invoicing, dealing, payment ----------
    def _accrue(self, key: str, exact: Decimal) -> Decimal:
        posted, self.accruals[key] = self.accruals.get(key, Accrual()).post(exact)
        return posted

    def _accrue_date(self, d: date):
        with localcontext(CTX):
            for l in self.loans:
                amt = self._accrue(f"borrow:{l.loan_id}", l.qty * self.marks[l.sym] * l.rate / 360)
                self._post(f"Borrow fee {l.sym} {l.qty} sh @ {l.rate}", ("common_pnl", amt), ("accrued_interest", -amt), date_=d)
            debt = -self.bal("debt")
            amt = self._accrue("debit", debt * D(self.cfg["debit_rate"]) / 360)
            self._post("Broker debit interest", ("common_pnl", amt), ("accrued_interest", -amt), date_=d)
        opening = [s for s in self.series if s.units > 0]
        fees = {s.series_id: self._accrue(f"mgmt:{s.series_id}", mgmt_fee_exact(s)) for s in opening}
        pnl = -self.bal("common_pnl")
        shares = allocate(pnl, {s.series_id: s.participation for s in opening}) if pnl else {}
        if pnl:
            self._post("Allocate common P&L by opening participation", ("common_pnl", pnl),
                       *[(f"capital:{k}", -v) for k, v in shares.items()], date_=d)
        new = []
        for s in opening:
            f = fees[s.series_id]
            if f:
                self._post_pair(f"Management fee {s.series_id} 1.5% ACT/365",
                                [(f"capital:{s.series_id}", f), ("mgmt_fee_accrued", -f)],
                                [("fee_receivable", f), ("fee_revenue", -f)], date_=d)
            n = reprovision(s, s.participation + shares.get(s.series_id, Decimal(0)) - f)
            dF = n.provision - s.provision
            self._post(f"Performance provision change {s.series_id}", (f"capital:{s.series_id}", dF),
                       (f"provision:{s.series_id}", -dF), date_=d)
            new.append(n)
        by_id = {n.series_id: n for n in new}
        self.series = [by_id.get(x.series_id, x) for x in self.series]

    def _invoice(self):
        self._post("Invoice management fees accrued through dealing close",
                   ("mgmt_fee_accrued", -self.bal("mgmt_fee_accrued")), ("mgmt_fee_payable", self.bal("mgmt_fee_accrued")))
        self._post("Invoice borrow/debit interest accrued through dealing close",
                   ("accrued_interest", -self.bal("accrued_interest")), ("interest_payable", self.bal("accrued_interest")))

    def _deal(self):
        for r in self.tape.raw["redemptions"]:
            if r["deal_day"] != self.ev.day:
                continue
            idx = next(i for i, s in enumerate(self.series) if s.series_id == r["series"])
            s, payable, fee = redeem(self.series[idx], D(r["units"]))
            self.series[idx] = s
            self._post(f"Deal redemption {r['units']} units {r['series']}", (f"capital:{r['series']}", payable),
                       ("redemption_payable", -payable))
            if fee:
                self._post_pair(f"Crystallize redeemed performance fee {r['series']}",
                                [(f"provision:{r['series']}", fee), ("perf_fee_payable", -fee)],
                                [("fee_receivable", fee), ("fee_revenue", -fee)])
            self._notice(f"Dealt {r['series']} redemption of {r['units']} units: ${payable:,.2f} payable next business day.", code="redemption_dealt",
                         series=r["series"], payable=str(payable))

    def _pay_due(self):
        """Treasury sweep priority: redemptions, then fixed fees, then interest (collateral already trued up)."""
        for acct, label in (("redemption_payable", "redemption"), ("mgmt_fee_payable", "management fee"),
                            ("perf_fee_payable", "performance fee"), ("interest_payable", "interest invoice")):
            due = -self.bal(acct)
            if due <= 0:
                continue
            got = self._raise_cash(due, label)
            if acct in ("mgmt_fee_payable", "perf_fee_payable"):
                self._post_pair(f"Pay {label} to management company", [(acct, got), ("cash", -got)],
                                [("cash", got), ("fee_receivable", -got)])
            else:
                self._post(f"Pay {label}", (acct, got), ("cash", -got))
            self.paid[label] = self.paid.get(label, Decimal(0)) + got
            if got < due:
                self.incidents.append(f"day {self.ev.day}: unpaid {label} {due - got}")

    # ---------- invariants ----------
    def reconcile(self):
        """Independent cross-checks between state and journal; raises on any break."""
        for ent in ("fund", "firm"):
            assert sum(self.j.balances(ent).values(), Decimal(0)) == 0, f"{ent} trial balance"
        assert self.bal("long_securities") == self.long_mv(), "long securities vs positions"
        assert self.bal("short_liability") == -self.short_mv(), "short liability vs positions"
        for s in self.series:
            assert self.bal(f"capital:{s.series_id}") == -s.net, f"series {s.series_id} net capital"
            assert self.bal(f"provision:{s.series_id}") == -s.provision, f"series {s.series_id} provision"
        if self.bal("common_pnl") == 0:
            assert self.nav() == sum(s.net for s in self.series), "NAV equals sum of series net capital"
        assert self.bal("cash") >= 0 and self.bal("cash", "firm") >= 0, "no negative cash"
        assert -self.bal("debt") <= D(self.cfg["credit_limit"]), "credit limit"
        assert self.bal("collateral") >= 0

    # ---------- outcome ----------
    def outcome(self) -> dict:
        forced = [i for i in self.incidents if "forced" in i]
        unpaid = [i for i in self.incidents if "unpaid" in i or "shortfall" in i or "failed" in i]
        tactical = self.paid.get("redemption", Decimal(0))
        nav = self.nav()
        if not self.finished():
            label = "IN_PROGRESS"
        elif nav <= 0 or unpaid:
            label = "DISTRESS"
        elif forced:
            label = "SURVIVAL"
        else:
            label = "WIN"
        return {"label": label, "nav": str(nav), "redemption_paid": str(tactical), "forced": forced,
                "unpaid": unpaid, "recall_resolved_by": self.recall_resolved_by,
                "journal_digest": self.j.digest(), "tape_digest": self.tape.digest}
