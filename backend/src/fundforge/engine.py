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
from typing import Any, Literal, get_args

from .administrator import Administrator, Capital
from .broker import Borrow, Broker
from .compliance import Breach, Ruleset, evaluate
from .execution import BUY_SIDES, capacity, fill_price, limit_quantity
from .journal import Journal, entry
from .market import Market
from .money import CTX, Accrual, D, allocate, cents
from .series import Series, mgmt_fee_exact, redeem, reprovision
from .shadow import ExecutionConfirmation, certify, inspect_book, inspect_settlements
from .tape import EXEC_PHASES, MarketEvent, Tape

Side = Literal["BUY", "SELL", "SHORT", "COVER"]
Status = Literal["QUEUED", "PARTIALLY_FILLED", "FILLED", "CANCELED", "EXPIRED", "REJECTED"]
SIDES: tuple[Side, ...] = get_args(Side)
OPEN: tuple[Status, ...] = ("QUEUED", "PARTIALLY_FILLED")
Leg = tuple[str, Decimal]
# Bump on ANY change to economic rules; rooms created under another version are refused, never re-derived.
RULES_VERSION = "case1-rules-2026.10.8"


class CommandRejected(ValueError):
    pass


class InvariantError(RuntimeError):
    """An internal accounting break, never a player validation error.

    Codes and simulation coordinates support diagnosis without relying on
    presentation text. This check remains active under both -O and -OO.
    """

    def __init__(self, code: str, detail: str, day: int, phase: str) -> None:
        self.code = code
        self.detail = detail
        self.day = day
        self.phase = phase
        super().__init__(f"{code} at day {day}/{phase}: {detail}")


@dataclass
class Order:
    order_id: str
    sym: str
    side: Side
    qty: int
    limit: Decimal | None = None
    forced: str | None = None  # "recall" | "margin" for engine-generated orders
    filled: int = 0
    status: Status = "QUEUED"
    fills: list[dict[str, Any]] = field(default_factory=list)

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
    loan_id: str | None = None  # identity allocated when a new short executes
    returns: tuple[tuple[str, int], ...] = ()  # reserved at cover execution, retained on failed settlement
    obligation: str = ""  # X{n}: the n-th execution confirmation this settles


class Engine:
    def __init__(self, tape: Tape) -> None:
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
        self.confirmations: list[ExecutionConfirmation] = []
        self.settlement_failures: list[tuple[int, str]] = []  # dated failed attempts (day, obligation)
        self.broker = Broker(r["opening"]["fund"], D(self.cfg["borrow_rate"]))
        self.accruals: dict[str, Accrual] = {}
        self.event_fills: dict[tuple[str, str], int] = {}
        self.notices: list[dict[str, Any]] = []
        # Observations only: populated AFTER an event is processed, never from future tape rows.
        # Rebuilt with the command log; not part of the economic journal or rules version.
        self.observations: list[dict[str, Any]] = []
        self.research_used: list[dict[str, Any]] = []
        self.attention: dict[str, dict[str, Any]] = {}
        self.shared_research: set[str] = set()
        self.offer_visible = False
        self.replacement_accepted = False
        self.recall_open = 0
        self.recall_resolved_by: str | None = None
        self.margin_call: Decimal | None = None
        self.reserve: Decimal | None = None  # None => default 2% NAV buffer (FUND_ACCOUNTING §4)
        self.incidents: list[str] = []
        self.incident_events: list[dict[str, Any]] = []
        self.paid: dict[str, Decimal] = {}
        self.mandate = Ruleset.from_raw(tape.raw["mandate"])
        self._opening_marks = dict(self.marks)
        self.market = Market(tape.raw.get("market"), tape.instruments)
        self.market.init_navs(self.marks)
        self._prev_exec_marks = dict(self.marks)
        self._open()
        self.administrator = Administrator(r["opening"]["fund"]["series"], self._administrator_wealth())

    # ---------- journal helpers ----------
    def _eid(self) -> str:
        self.seq += 1
        return f"{self.ev.date.isoformat()}/{self.ev.phase}/{self.seq:04d}"

    def _post(self, memo: str, *legs: Leg, entity: str = "fund", date_: date | None = None) -> None:
        live = [(a, x) for a, x in legs if x != 0]
        if live:
            self.j.post(entry(self._eid(), entity, (date_ or self.ev.date).isoformat(), memo, *live))

    def _post_pair(self, memo: str, fund_legs: list[Leg], firm_legs: list[Leg], date_: date | None = None) -> None:
        d = (date_ or self.ev.date).isoformat()
        fund_legs = [(a, x) for a, x in fund_legs if x != 0]
        firm_legs = [(a, x) for a, x in firm_legs if x != 0]
        if not fund_legs:
            return
        self.j.post_many([entry(self._eid(), "fund", d, memo, *fund_legs),
                          entry(self._eid(), "firm", d, memo, *firm_legs)])

    def bal(self, account: str, entity: str = "fund") -> Decimal:
        return self.j.balance(entity, account)

    # ---------- opening ----------
    def _open(self) -> None:
        o = self.tape.raw["opening"]
        f = o["fund"]
        for s, q in f["positions"].items():
            self.pos[s] = q
            if q < 0:
                self.loans.append(Loan(f"L-open-{s}", s, -q, D(self.cfg["borrow_rate"])))
        long_mv, short_mv = self.long_mv(), self.short_mv()
        cash, coll, debt = D(f["cash"]), D(f["collateral"]), D(f["debt"])
        nav = long_mv + coll + cash - short_mv - debt
        total_units = sum(D(x["units"]) for x in f["series"])
        self._require(total_units > 0, "opening_units", "opening series must have positive total units")
        caps = allocate(nav, {x["id"]: D(x["units"]) for x in f["series"]})
        self.series = [Series(x["id"], D(x["units"]), D(x["hwm"]), caps[x["id"]]) for x in f["series"]]
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
    def long_mv(self) -> Decimal:
        return sum((cents(q * self.marks[s]) for s, q in self.pos.items() if q > 0), Decimal(0))

    def short_mv(self) -> Decimal:
        return sum((cents(-q * self.marks[s]) for s, q in self.pos.items() if q < 0), Decimal(0))

    def nav(self) -> Decimal:
        """Net NAV after provisions (assets - liabilities), valid intraday."""
        return -sum((v for a, v in self.j.balances("fund").items()
                     if a.startswith("capital:") or a == "common_pnl"), Decimal(0))

    def margin(self, kind: str = "maintenance", long_mv: Decimal | None = None,
               short_mv: Decimal | None = None) -> Decimal:
        r = self.tape.margin(self.ev.day)[kind]
        lm = self.long_mv() if long_mv is None else long_mv
        sm = self.short_mv() if short_mv is None else short_mv
        return cents(r["long"] * lm + r["short"] * sm)

    def deficit(self) -> Decimal:
        return max(Decimal(0), self.margin() - self.nav())

    def borrowed(self, sym: str) -> int:
        return sum(ln.qty for ln in self.loans if ln.sym == sym)

    def credit_left(self) -> Decimal:
        return D(self.cfg["credit_limit"]) + self.bal("debt")  # debt is a credit (negative) balance

    # ---------- cash primitives ----------
    def _raise_cash(self, amount: Decimal, why: str) -> Decimal:
        """Draw credit so unrestricted cash covers ``amount``; returns cash actually available."""
        short = amount - self.bal("cash")
        if short > 0:
            draw = min(short, self.credit_left())
            self.broker.record(self.ev.date, "draw", amount=draw)
            self._post(f"Draw credit line: {why}", ("cash", draw), ("debt", -draw))
        return min(amount, self.bal("cash"))

    def _repay_debt(self) -> None:
        known = -sum((self.bal(a) for a in ("redemption_payable", "mgmt_fee_payable", "perf_fee_payable",
                                            "interest_payable", "trade_payable")), Decimal(0))
        spare = self.bal("cash") - self.buffer() - known
        repay = min(spare, -self.bal("debt"))
        if repay > 0:
            self.broker.record(self.ev.date, "repay", amount=repay)
            self._post("Repay broker debit above treasury reserve", ("debt", repay), ("cash", -repay))

    def buffer(self) -> Decimal:
        return cents(D("0.02") * self.nav()) if self.reserve is None else self.reserve

    def _remark(self) -> None:
        dl = self.long_mv() - self.bal("long_securities")
        ds = -self.short_mv() - self.bal("short_liability")
        self._post("Mark positions to reference", ("long_securities", dl), ("short_liability", ds),
                   ("common_pnl", -dl - ds))

    def _collateral_target(self) -> Decimal:
        """Per symbol: active short value less its own earmarked unsettled proceeds (never negative),
        plus frozen covers."""
        frozen = sum((p.frozen for p in self.pending if p.kind == "COVER"), Decimal(0))
        need = Decimal(0)
        for s, q in self.pos.items():
            mv = cents(-q * self.marks[s]) if q < 0 else Decimal(0)
            earmarked = sum((p.amount for p in self.pending if p.kind == "SHORT" and p.sym == s), Decimal(0))
            need += max(Decimal(0), mv - earmarked)
        return need + frozen

    def _true_up_collateral(self) -> None:
        diff = self._collateral_target() - self.bal("collateral")
        if diff > 0:
            got = self._raise_cash(diff, "short collateral top-up")
            self.broker.record(self.ev.date, "collateral", amount=got)
            self._post("Top up restricted short collateral", ("collateral", got), ("cash", -got))
            if got < diff:
                self._incident("collateral_shortfall", f"day {self.ev.day}: collateral shortfall {diff - got}",
                               amounts={"shortfall": str(diff - got)})
        elif diff < 0:
            self.broker.record(self.ev.date, "collateral", amount=diff)
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
        if side in ("BUY", "SHORT") and self.control_report()["status"] != "checked":
            raise CommandRejected("unresolved controls block new risk; reductions and cancels remain available")
        o = Order(order_id, sym, side, qty, limit)  # `side in SIDES` above narrows str to Side
        self.orders.append(o)
        return o

    def cancel_order(self, order_id: str) -> None:
        o = next((o for o in self.orders if o.order_id == order_id and o.status in OPEN), None)
        if o is None:
            raise CommandRejected(f"no open order {order_id}")
        o.status = "CANCELED"

    def assign_research(self, topic: str, role: str | None = None, location: str | None = None) -> None:
        rs = self.tape.raw["research"]
        if not self.at_barrier():
            raise CommandRejected("research is assigned at a decision barrier")
        if topic not in rs["topics"] or any(r["topic"] == topic for r in self.research_used):
            raise CommandRejected(f"unknown or repeated research topic {topic!r}")
        if role is not None:
            assignment = rs["assignments"][topic]
            if assignment["role"] != role:
                raise CommandRejected("assignment belongs to the other partner's role")
            if location is not None and assignment["location"] != location:
                raise CommandRejected("assignment is not available at this location")
            if self.attention.get(role, {}).get("window") == self.cursor:
                raise CommandRejected("attention already committed for this decision window")
        used = sum(r.get("owner") == role for r in self.research_used)
        if used >= rs["budget_per_role" if role else "budget"]:
            raise CommandRejected("research budget exhausted")
        if role:
            self.attention[role] = {"window": self.cursor, "location": rs["assignments"][topic]["location"],
                                    "assignment": topic}
        self.research_used.append({"topic": topic, "assigned_day": self.ev.day, "reveal_day": self.ev.day + 1,
                                   "owner": role})

    def visible_notices(self, role: str | None = None) -> list[dict[str, Any]]:
        return [n for n in self.notices if not n["refs"].get("owner")
                or n["refs"]["owner"] == role or n["refs"].get("topic") in self.shared_research]

    def share_research(self, role: str, topic: str) -> None:
        evidence = next((n for n in self.notices if n["code"] == "research_reveal"
                         and n["refs"].get("topic") == topic and n["refs"].get("owner") == role), None)
        if evidence is None:
            raise CommandRejected("only the owner can share evidence after it has arrived")
        if topic in self.shared_research:
            raise CommandRejected("evidence already shared")
        self.shared_research.add(topic)
        self._notice(f"{role.upper()} shared {topic.replace('_', ' ')} research with the partnership.",
                     code="research_shared", topic=topic)

    def accept_replacement(self) -> None:
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

    def compliance_check(self, new_orders: list[tuple[str, str, int]]) -> list[Breach]:
        """Mandate check for new orders on top of every still-open voluntary order, at current marks."""
        queued = [(o.sym, str(o.side), o.remaining) for o in self.orders if o.status in OPEN and not o.forced]
        return evaluate(self.pos, self.marks, self.nav(), queued + new_orders, self.mandate)

    def set_reserve(self, amount: Decimal) -> None:
        if amount < 0:
            raise CommandRejected("reserve must be non-negative")
        self.reserve = amount

    # ---------- event loop ----------
    def advance(self) -> list[MarketEvent]:
        """Process events up to the next decision barrier (or the end). Returns processed events."""
        done: list[MarketEvent] = []
        while self.cursor < len(self.tape.events):
            e = self.tape.events[self.cursor]
            if e.phase in EXEC_PHASES and done:
                break
            self.ev = e
            self.market.decay()
            self.marks = self.market.effective(e.marks)
            self._remark()  # prices can move at any event (news or impact decay); books always follow
            getattr(self, "_" + e.phase.lower())()
            self._observe_broker()
            self.cursor += 1
            done.append(e)
            self.reconcile()
            self.observations.append({
                "event": self.cursor, "day": e.day, "date": e.date.isoformat(), "phase": e.phase,
                "marks": {s: str(m) for s, m in self.marks.items()}, "volume": dict(e.volume),
            })
            if self.cursor < len(self.tape.events) and self.tape.events[self.cursor].phase in EXEC_PHASES:
                break
        return done

    def finished(self) -> bool:
        return self.cursor >= len(self.tape.events)

    def _notice(self, text: str, kind: str = "notice", code: str = "notice", **refs: Any) -> None:
        """Typed notice: game logic and the world read ``code``/refs; ``text`` is presentation only."""
        self.notices.append({"code": code, "refs": refs, "day": self.ev.day, "date": self.ev.date.isoformat(),
                             "phase": self.ev.phase, "kind": kind, "text": text})

    def _incident(self, code: str, text: str, *, amounts: dict[str, str] | None = None, **refs: Any) -> None:
        self.incident_events.append({"code": code, "day": self.ev.day, "phase": self.ev.phase,
                                     "refs": refs, "amounts": amounts or {}, "text": text})
        self.incidents.append(text)  # presentation compatibility for existing clients

    def _publish_notices(self) -> None:
        for n in self.tape.raw["public_notices"]:
            if (n["day"], n["event"]) == (self.ev.day, self.ev.phase):
                self._notice(n["text"], code=n.get("code", "notice"))
        if self.ev.headline:
            self._notice(self.ev.headline, "market", code=self.ev.headline_code or "market_event")

    def _open_admin(self) -> None:
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

    def _public_mark(self) -> None:
        self._publish_notices()
        self._remark()
        rc = self.tape.raw["borrow"]["recall"]
        if self.ev.day == rc["announce_day"]:
            self.recall_open = min(rc["qty"], self._loan_available(rc["loan_id"]))
            if not self.recall_open:
                self.recall_resolved_by = "prior cover"
        for change in self.tape.raw["borrow"].get("rate_changes", []):
            if self.ev.day == change["day"]:
                for loan in self.loans:
                    if loan.loan_id == change["loan_id"]:
                        self.broker.record(self.ev.date, "rate", loan_id=loan.loan_id, rate=D(change["rate"]))
                        loan.rate = D(change["rate"])
                        self._notice("Borrow rate changed.", code="borrow_rerate", loan_id=loan.loan_id,
                                     sym=loan.sym, rate=str(loan.rate))
        for r in self.research_used:
            if r["reveal_day"] == self.ev.day:
                text = (self.market.crowding_report(self.marks, self.pos) if r["topic"] == "crowding"
                        else self.tape.raw["research"]["topics"][r["topic"]])
                self._notice(text, "research", code="research_reveal", topic=r["topic"], owner=r.get("owner"))
                if r["topic"] == "borrow":
                    self.offer_visible = True
        self._true_up_collateral()
        d = self.deficit()
        self.margin_call = d if d > 0 else None
        if d > 0:
            self._notice(f"Margin call: maintenance deficit ${d:,.2f}. Cure at the next execution or face forced "
                         "liquidation.", "alert", code="margin_call", deficit=str(d))

    def _exec_a(self) -> None:
        self._execute()

    def _exec_b(self) -> None:
        self._execute()

    def _close(self) -> None:
        self._remark()
        self._true_up_collateral()
        for o in self.orders:
            if o.status in OPEN:
                o.status = "EXPIRED"
        firm = self.tape.raw["firm"]
        self._post("Accrue partner payroll", ("payroll_expense", D(firm["payroll_per_business_day"])),
                   ("payroll_payable", -D(firm["payroll_per_business_day"])), entity="firm")
        if self.ev.day % firm["pay_every_n_days"] == 0:
            due = -self.bal("payroll_payable", "firm")
            paid = min(due, self.bal("cash", "firm"))
            self._post("Pay weekly payroll from firm cash", ("payroll_payable", paid), ("cash", -paid), entity="firm")
            if paid < due:
                self._incident("payroll_unpaid", f"day {self.ev.day}: firm payroll unpaid {due - paid}",
                               amounts={"shortfall": str(due - paid)})
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
    def _execute(self) -> None:
        self.event_fills = {}  # participation capacity is per execution event (FUND_ACCOUNTING §8)
        self._remark()
        # rival funds trade first on public marks; their flow moves prices before our orders fill
        flow, news = self.market.trade(self.marks, self._prev_exec_marks, self.ev.volume, self.tape.margin(self.ev.day))
        self.market.push(flow, self.ev.volume)
        self.marks = self.market.effective(self.ev.marks)
        self._remark()
        for n in news:
            self._notice(n["text"], "market", code=n["code"], rival=n["rival"])
        rc = self.tape.raw["borrow"]["recall"]
        deadline = (self.ev.day, self.ev.phase) >= (rc["deadline_day"], rc["deadline_event"])
        queued = [o for o in self.orders if o.status in OPEN]
        for o in queued:
            self._fill(o)
        if deadline and self.recall_open > 0:
            self._forced("recall", rc["sym"], "COVER", min(self.recall_open, -self.pos[rc["sym"]]))
        if self.margin_call is not None and self.deficit() > 0:
            self._forced_margin()
        # our own net flow leaves a permanent footprint on later prices
        ours = {s: self.event_fills.get((s, "BUY"), 0) - self.event_fills.get((s, "SELL"), 0) for s in self.pos}
        self.market.push({s: q for s, q in ours.items() if q}, self.ev.volume)
        self._prev_exec_marks = dict(self.marks)
        self._true_up_collateral()
        d = self.deficit()
        self.margin_call = d if d > 0 else None

    def _forced(self, why: str, sym: str, side: Side, qty: int) -> Order | None:
        if qty <= 0:
            return None
        o = Order(f"forced-{why}-{self.ev.day}-{self.ev.phase}-{sym}", sym, side, qty, forced=why)
        self.orders.append(o)
        self._fill(o)
        if o.filled:
            self._incident(f"forced_{why}", f"day {self.ev.day} {self.ev.phase}: forced {why} {side} {o.filled} {sym}",
                           order_id=o.order_id, sym=sym, side=side, qty=o.filled)
        if o.status != "FILLED":
            o.status = "EXPIRED"
        return o

    def _forced_margin(self) -> None:
        """Sell longs (largest market value first), then cover shorts, until maintenance is met."""
        r = self.tape.margin(self.ev.day)["maintenance"]
        longs = sorted((s for s, q in self.pos.items() if q > 0), key=lambda s: (-self.pos[s] * self.marks[s], s))
        shorts = sorted((s for s, q in self.pos.items() if q < 0), key=lambda s: (self.pos[s] * self.marks[s], s))
        legs: tuple[tuple[Side, list[str], Decimal], ...] = (("SELL", longs, r["long"]), ("COVER", shorts, r["short"]))
        for side, syms, rate in legs:
            for s in syms:
                d = self.deficit()
                if d <= 0:
                    return
                with localcontext(CTX):
                    relief = rate * self.marks[s] - self.marks[s] * D("0.002")  # conservative per-share relief
                    need = int(d / relief * D("1.05")) + 1
                self._forced("margin", s, side, min(need, abs(self.pos[s])))

    def _fill(self, o: Order) -> None:
        ev, s = self.ev, o.sym
        if o.status not in OPEN:
            return
        if o.side in ("BUY", "SHORT") and self.control_report()["status"] != "checked":
            return self._reject(o, "unresolved controls block new risk at execution")
        # reduce-only checks against current economic position
        held = self.pos[s]
        max_q = {"SELL": max(held, 0), "COVER": max(-held, 0)}.get(o.side, o.remaining)
        if (o.side == "BUY" and held < 0) or (o.side == "SHORT" and held > 0):
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
        q = limit_quantity(self.marks[s], o.side, same, q, ev.volume.get(s, 0), hs, k, o.limit)
        if q <= 0:
            return
        price = fill_price(self.marks[s], o.side, same, q, ev.volume[s], hs, k)
        amount = cents(price * q)
        if o.side in ("BUY", "SHORT") and not o.forced and not self._initial_margin_ok(s, o.side, q):
            return self._reject(o, "initial margin would be breached at execution")
        if not o.forced:  # revalidate the mandate at execution with live marks and NAV
            breaches = evaluate(self.pos, self.marks, self.nav(), [(s, o.side, q)], self.mandate)
            if breaches:
                return self._reject(o, f"mandate: {breaches[0].detail}")
        self._book(o, q, price, amount)
        self.confirmations.append(ExecutionConfirmation(self.cursor, s, o.side, q, price, amount,
                                                       self.marks[s], ev.volume[s], same, hs, k, ev.day))
        self.pending[-1].obligation = f"X{len(self.confirmations)}"
        self.event_fills[(s, "both")] = done + q
        self.event_fills[(s, "BUY" if o.side in BUY_SIDES else "SELL")] = same + q
        o.filled += q
        o.fills.append({"day": ev.day, "phase": ev.phase, "qty": q, "price": str(price), "amount": str(amount)})
        o.status = "FILLED" if o.remaining == 0 else "PARTIALLY_FILLED"
        if o.side == "COVER" and self.recall_open:
            recalled_id = self.tape.raw["borrow"]["recall"]["loan_id"]
            covered = min(sum(qty for loan_id, qty in self.pending[-1].returns if loan_id == recalled_id),
                          self.recall_open)
            self.recall_open -= covered
            if self.recall_open == 0 and self.recall_resolved_by is None:
                self.recall_resolved_by = "forced buy-in" if o.forced else "voluntary cover"

    def _reject(self, o: Order, why: str) -> None:
        o.status = "REJECTED"
        o.fills.append({"day": self.ev.day, "phase": self.ev.phase, "rejected": why})

    def _short_inventory(self, s: str) -> int:
        nn = self.tape.raw["borrow"]["no_new_inventory"]
        if s == nn["sym"] and self.ev.day >= nn["from_day"]:
            return 0
        opening_short: int = max(0, -self.tape.raw["opening"]["fund"]["positions"].get(s, 0))
        extra: int = self.cfg["extra_borrow_inventory"]
        return opening_short + extra - self.borrowed(s) - sum(
            p.qty for p in self.pending if p.kind == "SHORT" and p.sym == s)

    def _initial_margin_ok(self, s: str, side: Side, q: int) -> bool:
        add = cents(q * self.marks[s])
        lm, sm = self.long_mv(), self.short_mv()
        lm, sm = (lm + add, sm) if side == "BUY" else (lm, sm + add)
        return self.margin("initial", lm, sm) <= self.nav()

    def _next_business_day(self) -> int:
        return self.ev.day + 1

    def _book(self, o: Order, q: int, price: Decimal, amount: Decimal) -> None:
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
        loan_id = f"L-trade-{o.order_id}-{o.filled}" if o.side == "SHORT" else None
        returns = self._reserve_returns(s, q) if o.side == "COVER" else ()
        self.pending.append(Pending(t1, o.side, s, q, amount, frozen, loan_id, returns))
        self._remark()

    def _settle(self, p: Pending) -> bool:
        """Settle one obligation; on a cash shortfall record a failed settlement and keep it pending."""
        memo = f"Settle {p.kind} {p.qty} {p.sym}"
        if p.kind == "SELL":
            self._post(memo, ("cash", p.amount), ("trade_receivable", -p.amount))
        elif p.kind == "SHORT":
            self._post(memo, ("collateral", p.amount), ("short_sale_receivable", -p.amount))
            self._require(p.loan_id is not None, "borrow_identity", "short settlement has no loan identity")
            self.loans.append(Loan(str(p.loan_id), p.sym, p.qty, D(self.cfg["borrow_rate"])))
            self.broker.record(self.ev.date, "loan", loan_id=str(p.loan_id), sym=p.sym,
                               qty=p.qty, rate=D(self.cfg["borrow_rate"]))
        elif p.kind == "BUY":
            got = self._raise_cash(p.amount, memo)
            if got < p.amount:
                self._incident("settlement_failed", f"day {self.ev.day}: failed settlement {memo}, "
                               f"short {p.amount - got}",
                               amounts={"shortfall": str(p.amount - got)}, sym=p.sym, kind=p.kind)
                self.settlement_failures.append((self.ev.day, p.obligation))
                return False
            self._post(memo, ("trade_payable", p.amount), ("cash", -p.amount))
        else:  # COVER: release frozen collateral to pay, return borrowed shares
            self._require(sum(q for _, q in p.returns) == p.qty, "borrow_returns", "cover allocation mismatch")
            for loan_id, qty in p.returns:
                self._require(any(ln.loan_id == loan_id and ln.qty >= qty for ln in self.loans),
                              "borrow_returns", "reserved loan unavailable at settlement")
            extra = p.amount - p.frozen
            if extra > 0 and self._raise_cash(extra, memo) < extra:
                self._incident("settlement_failed", f"day {self.ev.day}: failed settlement {memo}; "
                               "borrow and collateral retained", sym=p.sym, kind=p.kind,
                               loan_returns=list(p.returns))
                self.settlement_failures.append((self.ev.day, p.obligation))
                return False
            self._post(memo, ("trade_payable", p.amount), ("collateral", -p.frozen), ("cash", p.frozen - p.amount))
            for loan_id, qty in p.returns:
                self._return_loan(loan_id, qty)
        self.broker.record(self.ev.date, p.kind, amount=p.amount, frozen=p.frozen, obligation=p.obligation)
        return True

    def _loan_available(self, loan_id: str) -> int:
        settled = sum(ln.qty for ln in self.loans if ln.loan_id == loan_id)
        incoming = sum(p.qty for p in self.pending if p.kind == "SHORT" and p.loan_id == loan_id)
        reserved = sum(q for p in self.pending for lid, q in p.returns if lid == loan_id)
        return settled + incoming - reserved

    def _reserve_returns(self, sym: str, qty: int) -> tuple[tuple[str, int], ...]:
        """Recall first, then highest rate/identity; include already executed unsettled shorts."""
        candidates = [ln for ln in self.loans if ln.sym == sym]
        candidates += [Loan(str(p.loan_id), sym, p.qty, D(self.cfg["borrow_rate"]))
                       for p in self.pending if p.kind == "SHORT" and p.sym == sym]
        recalled = self.tape.raw["borrow"]["recall"]["loan_id"]
        out = []
        recall_take = min(qty, self.recall_open, self._loan_available(recalled)) if any(
            ln.loan_id == recalled for ln in candidates) else 0
        if recall_take:
            out.append((recalled, recall_take))
            qty -= recall_take
        for ln in sorted(candidates, key=lambda ln: (-ln.rate, ln.loan_id)):
            take = min(qty, self._loan_available(ln.loan_id) - (recall_take if ln.loan_id == recalled else 0))
            if take > 0:
                out.append((ln.loan_id, take))
                qty -= take
        self._require(qty == 0, "borrow_returns", "cover exceeds unreserved borrowed shares")
        return tuple(out)

    def _return_loan(self, loan_id: str, qty: int) -> None:
        loan = next((ln for ln in self.loans if ln.loan_id == loan_id), None)
        self._require(loan is not None and loan.qty >= qty, "borrow_returns", "loan return exceeds balance")
        if loan is not None:
            self.broker.record(self.ev.date, "return", loan_id=loan_id, qty=qty)
            loan.qty -= qty
        self.loans = [ln for ln in self.loans if ln.qty > 0]

    def _transfer_replacement(self, off: dict[str, Any]) -> None:
        q = min(off["qty"], self.recall_open, self._loan_available(off["old_loan_id"]))
        if q <= 0:
            self._notice("Replacement borrow not needed: the recall was already covered.", code="replacement_unneeded")
            return
        self._return_loan(off["old_loan_id"], q)
        self.loans.append(Loan(off["new_loan_id"], off["sym"], q, D(off["rate"])))
        self.broker.record(self.ev.date, "loan", loan_id=off["new_loan_id"], sym=off["sym"],
                           qty=q, rate=D(off["rate"]))
        covered = min(q, self.recall_open)
        self.recall_open -= covered
        if self.recall_open == 0 and self.recall_resolved_by is None:
            self.recall_resolved_by = "replacement borrow"
        self._notice(f"Replacement borrow settled: {q} {off['sym']} at {D(off['rate']) * 100}% replaces recalled "
                     "shares.", code="replacement_settled", sym=off["sym"], qty=q)

    # ---------- accrual, invoicing, dealing, payment ----------
    def _accrue(self, key: str, exact: Decimal) -> Decimal:
        posted, self.accruals[key] = self.accruals.get(key, Accrual()).post(exact)
        return posted

    def _accrue_date(self, d: date) -> None:
        self.broker.accrue(d, self.marks, D(self.cfg["debit_rate"]))
        self.administrator.close(d.isoformat(), self._administrator_wealth())
        with localcontext(CTX):
            for ln in self.loans:
                amt = self._accrue(f"borrow:{ln.loan_id}", ln.qty * self.marks[ln.sym] * ln.rate / 360)
                self._post(f"Borrow fee {ln.sym} {ln.qty} sh @ {ln.rate}", ("common_pnl", amt),
                           ("accrued_interest", -amt), date_=d)
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

    def _invoice(self) -> None:
        self.administrator.invoice()
        self.broker.record(self.ev.date, "invoice")
        fee, interest = self.bal("mgmt_fee_accrued"), self.bal("accrued_interest")
        self._post("Invoice management fees accrued through dealing close",
                   ("mgmt_fee_accrued", -fee), ("mgmt_fee_payable", fee))
        self._post("Invoice borrow/debit interest accrued through dealing close",
                   ("accrued_interest", -interest), ("interest_payable", interest))

    def _deal(self) -> None:
        self._observe_broker()  # close statements are available before the dealing gate
        if any(r["deal_day"] == self.ev.day for r in self.tape.raw["redemptions"]):
            report = self.control_report()
            self._require(report["execution_status"] == "checked", "administrator_controls",
                          "independent execution/valuation break blocks dealing")
            if report["status"] != "checked":
                self._incident("dealing_blocked", "Redemption dealing blocked by unresolved broker controls.")
                self._notice("Dealing withheld: resolve broker controls before the dealing close.", "alert",
                             code="dealing_blocked")
                return
        for r in self.tape.raw["redemptions"]:
            if r["deal_day"] != self.ev.day:
                continue
            idx = next(i for i, s in enumerate(self.series) if s.series_id == r["series"])
            s, payable, fee = redeem(self.series[idx], D(r["units"]))
            claim = self.administrator.preview(self.ev.date.isoformat(), r["series"], D(r["units"]))
            self._require((payable, fee, s.units, s.hwm, s.net, s.provision) == (
                claim.payable, claim.crystallized_fee, claim.surviving.units, claim.surviving.hwm,
                claim.surviving.net, claim.surviving.provision), "administrator_claim",
                "independent redemption calculation differs; no units or claims changed")
            self.administrator.deal(claim)
            self.series[idx] = s
            self._post(f"Deal redemption {r['units']} units {r['series']}", (f"capital:{r['series']}", payable),
                       ("redemption_payable", -payable))
            if fee:
                self._post_pair(f"Crystallize redeemed performance fee {r['series']}",
                                [(f"provision:{r['series']}", fee), ("perf_fee_payable", -fee)],
                                [("fee_receivable", fee), ("fee_revenue", -fee)])
            self._notice(f"Dealt {r['series']} redemption of {r['units']} units: ${payable:,.2f} payable next "
                         "business day.", code="redemption_dealt", series=r["series"], payable=str(payable))

    def _pay_due(self) -> None:
        """Treasury sweep priority: redemptions, then fixed fees, then interest (collateral already trued up)."""
        for acct, label in (("redemption_payable", "redemption"), ("mgmt_fee_payable", "management fee"),
                            ("perf_fee_payable", "performance fee"), ("interest_payable", "interest invoice")):
            due = -self.bal(acct)
            if due <= 0:
                continue
            got = self._raise_cash(due, label)
            self.administrator.pay(acct, got)
            self.broker.record(self.ev.date, "payment", amount=got, claim=acct)
            if acct in ("mgmt_fee_payable", "perf_fee_payable"):
                self._post_pair(f"Pay {label} to management company", [(acct, got), ("cash", -got)],
                                [("cash", got), ("fee_receivable", -got)])
            else:
                self._post(f"Pay {label}", (acct, got), ("cash", -got))
            self.paid[label] = self.paid.get(label, Decimal(0)) + got
            if got < due:
                self._incident("claim_unpaid", f"day {self.ev.day}: unpaid {label} {due - got}",
                               amounts={"shortfall": str(due - got)}, claim=label)

    # ---------- invariants ----------
    def _administrator_wealth(self) -> Decimal:
        """Capital before administrator claims; never read journal P&L or series capital."""
        with localcontext(CTX):
            holdings = dict(self.tape.raw["opening"]["fund"]["positions"])
            for fill in self.confirmations:
                holdings[fill.sym] = holdings.get(fill.sym, 0) + (
                    fill.qty if fill.side in ("BUY", "COVER") else -fill.qty)
            securities = sum((cents(q * self.marks[s]) for s, q in holdings.items()), Decimal(0))
            unsettled = sum((p.amount if p.kind in ("SELL", "SHORT") else -p.amount for p in self.pending), Decimal(0))
            b = self.broker.balances
            return (securities + b["cash"] + b["collateral"] - b["debt"] + unsettled
                    - self.broker.accrued - self.broker.invoiced)

    def _observe_broker(self) -> None:
        for statement_id in self.broker.observe(self.ev.day, self.ev.phase, self.ev.date,
                                                self.tape.raw.get("broker_statements", [])):
            self._notice("Broker statement requires review in Terminal RISK.", "alert",
                         code="broker_statement", statement_id=statement_id)

    def control_report(self) -> dict[str, Any]:
        report = inspect_book(self.tape.raw["opening"]["fund"]["positions"], self.confirmations,
                              self.pos, self.marks, self.j.balances("fund"))
        report["execution_status"] = report["status"]
        posted: dict[str, Decimal] = {}
        with localcontext(CTX):
            for item in self.j.entries:
                if item.entity == "fund" and any(p.account == "common_pnl" for p in item.postings):
                    charge = -sum((p.amount for p in item.postings if p.account == "accrued_interest"), Decimal(0))
                    if charge:
                        posted[item.date] = posted.get(item.date, Decimal(0)) + charge
        report["breaks"] += self.broker.discrepancies(self.j.balances("fund"),
                                                    {ln.loan_id: Borrow(ln.sym, ln.qty, ln.rate) for ln in self.loans},
                                                    posted)
        management: dict[tuple[str, str], Decimal] = {}
        with localcontext(CTX):
            for item in self.j.entries:
                if item.entity != "fund" or not any(p.account == "mgmt_fee_accrued" for p in item.postings):
                    continue
                for p in item.postings:
                    if p.account.startswith("capital:"):
                        key = (item.date, p.account.removeprefix("capital:"))
                        management[key] = management.get(key, Decimal(0)) + p.amount
        admin = self.administrator.inspect(
            {s.series_id: Capital(s.series_id, s.units, s.hwm, s.net, s.provision) for s in self.series},
            self.j.balances("fund"), self.j.balances("firm"), management)
        report["administrator"] = admin
        report["breaks"] += admin["breaks"]
        fund_balances = self.j.balances("fund")
        with localcontext(CTX):  # sign flips and claim inputs must not inherit a caller's precision
            certification = certify(
                {k: s.units for k, s in self.administrator.series.items()},
                {k: -fund_balances.get(f"capital:{k}", Decimal(0)) for k in self.administrator.series},
                {k: s.net for k, s in self.administrator.series.items()},
                [(c.series_id, c.units, c.price, c.payable) for c in self.administrator.claims])
        report["certification"] = certification
        report["breaks"] += certification["breaks"]
        report["breaks"] += inspect_settlements(
            self.confirmations,
            [(p.obligation, p.kind, p.sym, p.qty, p.amount, p.settle_day) for p in self.pending],
            [(a.obligation, a.kind, a.amount) for a in self.broker.activities if a.obligation],
            self.settlement_failures, self.ev.day)
        open_ids = {p.obligation for p in self.pending}
        report["settlements"] = [
            {"obligation": f"X{n}", "kind": c.side, "sym": c.sym, "qty": c.qty, "amount": str(c.amount),
             "due_day": c.day + 1, "status": "pending" if f"X{n}" in open_ids else "settled",
             "failed_days": [d for d, oid in self.settlement_failures if oid == f"X{n}"]}
            for n, c in enumerate(self.confirmations, start=1)]
        queue = self.broker.queue(self.ev.date)
        report["statement_queue"] = queue
        report["broker"] = {"activity_count": len(self.broker.activities), "fee_line_count": len(self.broker.fees),
                            "statement_count": len(self.broker.statements),
                            "balances": {k: str(v) for k, v in self.broker.balances.items()},
                            "financing_accrued": str(self.broker.accrued),
                            "financing_invoiced": str(self.broker.invoiced)}
        report["status"] = "break" if report["breaks"] or any(q["status"] == "open" for q in queue) else "checked"
        report["scope"] = ("Independent fill, holdings, broker cash activity and dated loan/debit fee checks. "
                           "Synthetic broker confirmations share instructed movements and observed marks; "
                           "independent LP participation, management fees, provisions and redemption claims; "
                           "settlement obligations rebuilt from execution identities. "
                           "Shared marks, settlement instructions and payment confirmations remain inputs; "
                           "this is not external NAV certification.")
        return report

    def resolve_statement(self, statement_id: str, revision: int, actor: str) -> None:
        if not self.at_barrier():
            raise CommandRejected("statement review requires a decision barrier")
        if self.control_report()["breaks"]:
            raise CommandRejected("current book discrepancies require repair before statement resolution")
        try:
            self.broker.resolve(statement_id, revision, self.ev.date, actor)
        except ValueError as exc:
            raise CommandRejected(str(exc)) from exc
        self._notice("Broker correction reviewed; original statement retained.", code="broker_resolved",
                     statement_id=statement_id, revision=revision)

    def _require(self, condition: bool, code: str, detail: str) -> None:
        if not condition:
            raise InvariantError(code, detail, self.ev.day, self.ev.phase)

    def reconcile(self) -> None:
        """Cross-check economic state and books; optimization cannot disable these guards.

        An exception aborts the transition. Session.handle restores its snapshot,
        and Store.apply rolls back the transaction without publishing the copy.
        A direct Engine caller must discard a failed transition, not continue it.
        """
        with localcontext(CTX):
            for ent in ("fund", "firm"):
                self._require(sum(self.j.balances(ent).values(), Decimal(0)) == 0,
                              "trial_balance", f"{ent} trial balance")
            self._require(self.bal("long_securities") == self.long_mv(),
                          "long_securities", "long securities vs positions")
            self._require(self.bal("short_liability") == -self.short_mv(),
                          "short_liability", "short liability vs positions")
            for s in self.series:
                self._require(self.bal(f"capital:{s.series_id}") == -s.net,
                              "series_capital", f"series {s.series_id} net capital")
                self._require(self.bal(f"provision:{s.series_id}") == -s.provision,
                              "series_provision", f"series {s.series_id} provision")
            if self.bal("common_pnl") == 0:
                self._require(self.nav() == sum(s.net for s in self.series),
                              "series_nav", "NAV equals sum of series net capital")
            for ent in ("fund", "firm"):
                self._require(self.bal("cash", ent) >= 0, "negative_cash", f"{ent} cash cannot be negative")
            self._require(-self.bal("debt") <= D(self.cfg["credit_limit"]), "credit_limit", "credit limit")
            self._require(self.bal("collateral") >= 0,
                          "negative_collateral", "restricted collateral cannot be negative")
            ids = [ln.loan_id for ln in self.loans] + [p.loan_id for p in self.pending if p.kind == "SHORT"]
            self._require(len(ids) == len(set(ids)), "borrow_identity", "duplicate loan identity")
            for loan_id in ids:
                self._require(loan_id is not None and self._loan_available(str(loan_id)) >= 0,
                              "borrow_returns", "loan over-reserved")
            for p in self.pending:
                if p.kind == "COVER":
                    self._require(sum(q for _, q in p.returns) == p.qty and all(
                        lid in ids and q > 0 for lid, q in p.returns), "borrow_returns", "invalid cover allocation")
            for sym, qty in self.pos.items():
                pending_short = sum(p.qty for p in self.pending if p.sym == sym and p.kind == "SHORT")
                pending_cover = sum(p.qty for p in self.pending if p.sym == sym and p.kind == "COVER")
                self._require(self.borrowed(sym) + pending_short - pending_cover == max(0, -qty),
                              "borrow_position", f"{sym} loans do not reconcile to economic short")

    def league(self) -> list[dict[str, str]]:
        """Public league table: every fund's return since the warm start, ours included."""
        with localcontext(CTX):
            units = sum((x.units for x in self.series), Decimal(0))
            unit_nav = sum((x.net for x in self.series), Decimal(0)) / units if units else Decimal(0)
            ours = {"id": "you", "name": "Your fund", "style": "long/short", "status": "active",
                    "return_bps": str(((unit_nav / 100 - 1) * 10000).quantize(Decimal("0.1"))), "nav": str(self.nav())}
        return sorted([*self.market.league(self.marks), ours], key=lambda x: (-Decimal(x["return_bps"]), x["id"]))

    # ---------- outcome ----------
    FORCED_PENALTY_BPS = Decimal(150)

    def score(self, n_forced: int) -> dict[str, Any]:
        """Excess unit return over a passive buy-and-hold of the opening book (no costs), minus forced-action
        penalties. Flows don't distort it: redemptions leave at NAV per unit."""
        with localcontext(CTX):
            open_pos = self.tape.raw["opening"]["fund"]["positions"]
            open_nav = sum((D(x["units"]) for x in self.tape.raw["opening"]["fund"]["series"]), Decimal(0)) * 100
            moves = (q * (self.marks[s] - self._opening_marks[s]) for s, q in open_pos.items())
            bench = sum(moves, Decimal(0)) / open_nav
            units = sum((x.units for x in self.series), Decimal(0))
            unit_nav = sum((x.net for x in self.series), Decimal(0)) / units if units else Decimal(0)
            fund = unit_nav / 100 - 1
            excess = ((fund - bench) * 10000).quantize(Decimal("0.1"))
            return {"fund_return_bps": str((fund * 10000).quantize(Decimal("0.1"))),
                    "benchmark_return_bps": str((bench * 10000).quantize(Decimal("0.1"))),
                    "excess_bps": str(excess), "score": str(excess - self.FORCED_PENALTY_BPS * n_forced)}

    def outcome(self) -> dict[str, Any]:
        forced = [i["text"] for i in self.incident_events if i["code"] in ("forced_recall", "forced_margin")]
        unpaid = [i["text"] for i in self.incident_events if i["code"] in (
            "payroll_unpaid", "claim_unpaid", "collateral_shortfall", "settlement_failed", "dealing_blocked")]
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
        score = self.score(len(forced))
        league = self.league()
        score["rank"] = 1 + sorted((-Decimal(x["return_bps"]), x["id"]) for x in league).index(
            next((-Decimal(x["return_bps"]), x["id"]) for x in league if x["id"] == "you"))
        score["funds"] = len(league)
        return {"label": label, "nav": str(nav), **score, "redemption_paid": str(tactical), "forced": forced,
                "unpaid": unpaid, "recall_resolved_by": self.recall_resolved_by,
                "variant": self.tape.raw.get("variant", "base"),
                "journal_digest": self.j.digest(), "tape_digest": self.tape.digest}
