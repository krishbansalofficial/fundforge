"""Two-partner command authority over the engine.

* Every command carries an idempotency key: a retry returns the original result,
  and reusing a key for a different command is rejected.
* Small orders are independent PM tickets (<=5% NAV each, <=15% opening-NAV turnover).
  Anything larger is a package: its digest binds contents, policy version and expiry.
  The proposer's signature counts once; it executes only when the *other* partner
  signs the same digest. Edits produce a new digest, so old signatures never carry over.
* Replacement borrow and treasury reserve belong to the managing partner.
* Generated rooms: LP contact belongs to the managing partner. A redemption gate is a package of
  kind ``gate`` whose digest binds the dealing day and the exact pending requests; it is elected only
  when the *other* partner signs, and the requests are revalidated at signing.
* Time advances only when both partners are ready; any state change clears readiness.
  If both vote ``skip``, time keeps advancing through quiet windows until a notice,
  incident, open order or the end (refused while a package awaits a signature).
"""

import copy
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any

from . import investors
from .engine import CommandRejected, Engine
from .generator import MACRO_SERIES, Spec
from .money import CTX, D, cents
from .research import REGIMES, regime_question

Cmd = dict[str, Any]

POLICY_VERSION = "case1-authority-v1"
CLOCK = "clock"  # system actor for logged time ticks
SPEEDS = (1, 2, 4)
ROLE_NAMES = {"pm": "portfolio manager", "mp": "managing partner"}
ROLES = ("pm", "mp")  # portfolio manager, managing (operating/risk) partner
TICKET_NAV_LIMIT = Decimal("0.05")
TURNOVER_LIMIT = Decimal("0.15")


@dataclass
class Package:
    package_id: str
    proposer: str
    orders: tuple
    expires_cursor: int
    digest: str
    signatures: set = field(default_factory=set)
    status: str = "PENDING_APPROVAL"
    kind: str = "orders"  # or "gate": a joint redemption-gate election
    terms: dict = field(default_factory=dict)


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


class Session:
    def __init__(self, engine: Engine, partners: dict[str, str], bots: frozenset[str] = frozenset()) -> None:
        if set(partners) != set(ROLES) or len(set(partners.values())) != 2:
            raise ValueError("exactly two distinct human partners are required")
        self.e = engine
        self.partners = partners  # role -> user id
        self.results: dict[str, tuple[str, Cmd]] = {}
        self.packages: dict[str, Package] = {}
        self.ready: dict[str, bool] = {}  # role -> voted to skip quiet windows
        self.turnover = Decimal(0)
        self.opening_nav = engine.nav()
        self.log: list[dict] = []
        self.bots = frozenset(bots)  # roles played by the deterministic partner bot (solo mode)
        self.chat: list[dict] = []
        # Real-time clock: wall time only decides WHEN the server sends a logged `tick`; economics never see it.
        self.clock: dict[str, Any] = {"speed": 0, "paused": True, "reason": "Opening: review the book and press play."}

    def role_of(self, user: str) -> str:
        if user == CLOCK:
            return "system"
        for r, u in self.partners.items():
            if u == user:
                return r
        raise CommandRejected("not a partner in this fund")

    # ---------- single entry point ----------
    def handle(self, user: str, key: str, command: Cmd) -> Cmd:
        """Apply ``command`` once per idempotency ``key``. All-or-nothing: a rejection leaves no trace."""
        fp = hashlib.sha256(canonical([user, command]).encode()).hexdigest()
        if key in self.results:
            prior_fp, result = self.results[key]
            if prior_fp != fp:
                raise CommandRejected(f"idempotency key {key!r} reused for a different command")
            return result
        role = self.role_of(user)
        if role == "system" and command.get("type") != "tick":
            raise CommandRejected("the clock can only tick")
        if role != "system" and command.get("type") == "tick":
            raise CommandRejected("only the clock ticks")
        handler = COMMANDS.get(str(command.get("type")))
        if handler is None:
            raise CommandRejected(f"unknown command type {command.get('type')!r}")
        # ponytail: snapshot by deepcopy (tape shared via memo); per-entity undo log if profiling says so
        saved = copy.deepcopy((self.e, self.packages, self.ready, self.turnover, self.clock, self.chat),
                              {id(self.e.tape): self.e.tape})
        try:
            result = handler(self, role, command)
        except Exception:
            self.e, self.packages, self.ready, self.turnover, self.clock, self.chat = saved
            raise
        self.results[key] = (fp, result)
        self.log.append({"day": self.e.ev.day, "phase": self.e.ev.phase, "role": role, "key": key,
                         "command": command, "result": result})
        if command["type"] != "ready":
            self.ready.clear()
        return result

    @property
    def version(self) -> int:
        """Accepted-command count; equals the persisted room version."""
        return len(self.log)

    # ---------- commands ----------
    def _cmd_ticket(self, role: str, c: Cmd) -> Cmd:
        if role != "pm":
            raise CommandRejected("independent tickets belong to the portfolio manager")
        notional = self._notional(c)
        nav = self.e.nav()
        if notional > cents(nav * TICKET_NAV_LIMIT):
            raise CommandRejected(f"ticket ${notional:,.2f} exceeds 5% of NAV; propose a joint package")
        if self.turnover + notional > cents(self.opening_nav * TURNOVER_LIMIT):
            raise CommandRejected("independent turnover limit (15% of opening NAV) reached; propose a joint package")
        self._mandate([(c["sym"], c["side"], int(c["qty"]))])
        o = self.e.submit_order(c["order_id"], c["sym"], c["side"], int(c["qty"]), self._limit(c))
        self.turnover += notional
        return {"order_id": o.order_id, "status": o.status}

    def _cmd_propose(self, role: str, c: Cmd) -> Cmd:
        if "source_version" in c and c["source_version"] != self.version:
            raise CommandRejected("analysis is stale; refresh and review the draft again")
        orders = tuple(sorted((o["order_id"], o["sym"], o["side"], int(o["qty"]), o.get("limit")) for o in c["orders"]))
        if not orders:
            raise CommandRejected("empty package")
        expires = self.e.cursor + 1  # valid only for the next execution event
        digest = hashlib.sha256(canonical([POLICY_VERSION, self.e.mandate.digest, c["package_id"], orders, expires])
                                .encode()).hexdigest()
        if c["package_id"] in self.packages:
            raise CommandRejected("package id already used; edits must be proposed as a new package")
        self.packages[c["package_id"]] = Package(c["package_id"], role, orders, expires, digest, {role})
        return {"package_id": c["package_id"], "digest": digest}

    def _cmd_sign(self, role: str, c: Cmd) -> Cmd:
        p = self.packages.get(c["package_id"])
        if p is None or p.status != "PENDING_APPROVAL":
            raise CommandRejected("no pending package")
        if c["digest"] != p.digest:
            raise CommandRejected("signature does not match the package contents")
        if role in p.signatures:
            raise CommandRejected("a partner cannot approve their own proposal twice")
        if self.e.cursor > p.expires_cursor or not self.e.at_barrier():
            p.status = "EXPIRED"
            raise CommandRejected("package expired")
        if p.kind == "gate":
            if self._lp(investors.gate_terms) != p.terms:
                raise CommandRejected("redemption requests changed since the gate was proposed")
            p.signatures.add(role)
            p.status = "ELECTED"
            investors.elect_gate(self.e, p.terms)
            return {"package_id": p.package_id, "status": p.status}
        self._mandate([(sym, side, qty) for _, sym, side, qty, _ in p.orders])  # signatures never override limits
        p.signatures.add(role)
        p.status = "AUTHORIZED_QUEUED"
        for oid, sym, side, qty, limit in p.orders:
            self.e.submit_order(oid, sym, side, qty, D(limit) if limit else None)
        return {"package_id": p.package_id, "status": p.status}

    def _cmd_propose_gate(self, role: str, c: Cmd) -> Cmd:
        terms = self._lp(investors.gate_terms)
        if c["package_id"] in self.packages:
            raise CommandRejected("package id already used; edits must be proposed as a new package")
        expires = self.e.cursor + 1
        identity = [POLICY_VERSION, "gate", c["package_id"], terms, expires]
        digest = hashlib.sha256(canonical(identity).encode()).hexdigest()
        self.packages[c["package_id"]] = Package(c["package_id"], role, (), expires, digest, {role}, kind="gate",
                                                 terms=terms)
        return {"package_id": c["package_id"], "digest": digest}

    def _cmd_contact_lp(self, role: str, c: Cmd) -> Cmd:
        if role != "mp":
            raise CommandRejected("LP relationships belong to the managing partner")
        self._lp(investors.contact, role, c["lp"])
        return {"contacted": c["lp"]}

    def _cmd_cancel(self, role: str, c: Cmd) -> Cmd:
        self.e.cancel_order(c["order_id"])
        return {"order_id": c["order_id"], "status": "CANCELED"}

    def _cmd_research(self, role: str, c: Cmd) -> Cmd:
        self.e.assign_research(c["topic"], role)
        return {"topic": c["topic"]}

    def _cmd_visit(self, role: str, c: Cmd) -> Cmd:
        self.e.assign_research(c["assignment"], role, c["location"])
        return {"location": c["location"], "assignment": c["assignment"]}

    def _cmd_share_research(self, role: str, c: Cmd) -> Cmd:
        self.e.share_research(role, c["topic"])
        return {"shared": c["topic"]}

    def _cmd_accept_replacement(self, role: str, c: Cmd) -> Cmd:
        if role != "mp":
            raise CommandRejected("replacement borrow is the managing partner's decision")
        self.e.accept_replacement()
        return {"accepted": True}

    def _cmd_set_reserve(self, role: str, c: Cmd) -> Cmd:
        if role != "mp":
            raise CommandRejected("treasury reserve is the managing partner's decision")
        self.e.set_reserve(D(c["amount"]))
        return {"reserve": c["amount"]}

    def _cmd_resolve_statement(self, role: str, c: Cmd) -> Cmd:
        if role != "mp":
            raise CommandRejected("statement resolution belongs to the managing partner")
        if c.get("version") != self.version or type(c.get("revision")) is not int:
            raise CommandRejected("stale statement review: refresh the current version and revision")
        self.e.resolve_statement(c["statement_id"], c["revision"], role)
        return {"resolved": c["statement_id"], "revision": c["revision"]}

    def _cmd_ready(self, role: str, c: Cmd) -> Cmd:
        if "version" in c and c["version"] != self.version:
            raise CommandRejected("stale: the plan changed since you looked; review it before marking ready")
        skip = c.get("skip") is True
        if skip and any(p.status == "PENDING_APPROVAL" for p in self.packages.values()):
            raise CommandRejected("a package is waiting for a signature: sign or let it expire before skipping ahead")
        self.ready[role] = skip
        if set(self.ready) == set(ROLES) and not self.e.finished():
            skip = all(self.ready.values())  # both partners must vote to skip
            self.ready.clear()
            for p in self.packages.values():
                if p.status == "PENDING_APPROVAL":
                    p.status = "EXPIRED"
            windows = 0
            while True:
                n_notices, n_incidents = len(self.e.notices), len(self.e.incident_events)
                self.e.advance()
                windows += 1
                # Skipping only replays the same advance() calls, so the journal equals stepping each barrier.
                if (not skip or self.e.finished() or self.e.notices[n_notices:]
                        or self.e.incident_events[n_incidents:]
                        or any(o.status in ("QUEUED", "PARTIALLY_FILLED") for o in self.e.orders)):
                    break
            return {"advanced": True, "next": self._next()} | ({"windows": windows} if skip else {})
        return {"advanced": False, "waiting_for": sorted(set(ROLES) - set(self.ready))}

    # ---------- real-time clock ----------
    def _cmd_set_speed(self, role: str, c: Cmd) -> Cmd:
        speed = c.get("speed")
        if speed not in SPEEDS:
            raise CommandRejected(f"speed must be one of {SPEEDS}")
        if self.e.finished():
            raise CommandRejected("the season is over")
        self.clock = {"speed": speed, "paused": False, "reason": None}
        return {"clock": self.clock}

    def _cmd_say(self, role: str, c: Cmd) -> Cmd:
        text = str(c.get("text", "")).strip()
        if not text or len(text) > 240:
            raise CommandRejected("messages must be 1-240 characters")
        self.chat.append({"day": self.e.ev.day, "phase": self.e.ev.phase, "role": role, "text": text,
                          "ref": c.get("ref")})
        return {"said": True}

    def _cmd_thesis(self, role: str, c: Cmd) -> Cmd:
        """Record a forecast for the live regime question. Lives only in the command log: no money, positions
        or journal. The debrief scores each seat's latest thesis per question."""
        if self.e.finished():
            raise CommandRejected("the season is over")
        q = regime_question(self.e.tape.macro.known(self.e.ev.day, MACRO_SERIES), Spec())
        if q is None or c.get("question") != q["question"]:
            raise CommandRejected("a thesis must answer the terminal's current research question")
        f = c.get("forecast")
        if not isinstance(f, dict) or set(f) != set(REGIMES) or not all(type(v) is str for v in f.values()):
            raise CommandRejected("forecast needs a decimal string for each of calm and stressed")
        try:
            probs = {s: Decimal(v) for s, v in f.items()}
        except InvalidOperation as e:
            raise CommandRejected("forecast needs a decimal string for each of calm and stressed") from e
        if not all(v.is_finite() and 0 <= v <= 1 for v in probs.values()) or sum(probs.values()) != 1:
            raise CommandRejected("forecast probabilities must be between 0 and 1 and sum to exactly 1")
        return {"question": q["question"], "forecast": {s: str(v) for s, v in probs.items()}}

    def _cmd_pause(self, role: str, c: Cmd) -> Cmd:
        self.clock = {**self.clock, "paused": True, "reason": f"Paused by the {ROLE_NAMES[role]}."}
        return {"clock": self.clock}

    def _cmd_tick(self, role: str, c: Cmd) -> Cmd:
        """Advance one execution window. Auto-pauses on anything a partner should see before time moves on."""
        if c.get("expected_version") != self.version:
            raise CommandRejected("stale tick")
        if self.clock["paused"] or self.e.finished():
            raise CommandRejected("clock is paused")
        if any(p.status == "PENDING_APPROVAL" for p in self.packages.values()):
            self.clock = {**self.clock, "paused": True, "reason": "A package is waiting for a signature."}
            return {"advanced": False, "clock": self.clock}
        n_notices, n_incidents = len(self.e.notices), len(self.e.incidents)
        self.e.advance()
        new = self.e.notices[n_notices:]
        if self.e.finished():
            self.clock = {"speed": 0, "paused": True, "reason": "Season complete."}
        elif self.e.incidents[n_incidents:] or any(n["kind"] in ("alert", "market", "research") for n in new):
            reason = ("A partner's research has arrived." if new and new[-1]["refs"].get("owner")
                      else new[-1]["text"] if new else self.e.incidents[-1])
            self.clock = {**self.clock, "paused": True, "reason": reason}
        elif new:  # a private notice (e.g. the MP's LP inbox) must not reach the other seat through the clock
            reason = "A partner has new private information." if new[-1]["refs"].get("owner") else new[-1]["text"]
            self.clock = {**self.clock, "paused": True, "reason": reason}
        return {"advanced": True, "next": self._next(), "clock": self.clock}

    def running(self) -> bool:
        return not self.clock["paused"] and not self.e.finished()

    # ---------- helpers ----------
    def _lp(self, fn: Callable[..., Any], *args: Any) -> Any:
        try:
            return fn(self.e, *args)
        except investors.Refused as ex:
            raise CommandRejected(str(ex)) from ex

    def _mandate(self, orders: list[tuple[str, str, int]]) -> None:
        for sym, side, qty in orders:
            if sym not in self.e.marks or side not in ("BUY", "SELL", "SHORT", "COVER") or qty <= 0:
                raise CommandRejected(f"invalid order {side} {qty} {sym}")
        breaches = self.e.compliance_check(orders)
        if breaches:
            raise CommandRejected("mandate: " + "; ".join(b.detail for b in breaches))

    def _limit(self, c: Cmd) -> Decimal | None:
        return D(c["limit"]) if c.get("limit") else None

    def _notional(self, c: Cmd) -> Decimal:
        if c.get("sym") not in self.e.marks:
            raise CommandRejected(f"unknown instrument {c.get('sym')!r}")
        return cents(int(c["qty"]) * self.e.marks[c["sym"]])

    def _next(self) -> dict[str, Any] | None:
        n = self.e.next_event()
        return None if n is None else {"day": n.day, "phase": n.phase, "date": n.date.isoformat()}

    # ---------- as-of player view ----------
    def view(self, user: str) -> dict:
        """Everything a partner may see now. Built only from processed events; the tape stays server-side."""
        role = self.role_of(user)
        e = self.e
        nav = e.nav()
        lm, sm = e.long_mv(), e.short_mv()
        with localcontext(CTX):  # ratios are display values but must not depend on the caller's context
            gross = ((lm + sm) / nav).quantize(D("0.0001")) if nav > 0 else None
            net = ((lm - sm) / nav).quantize(D("0.0001")) if nav > 0 else None
            per_unit = {s.series_id: (s.net / s.units).quantize(D("0.0001")) if s.units else None for s in e.series}
        return {
            "role": role,
            "partners": self.partners,
            "clock": {"day": e.ev.day, "date": e.ev.date.isoformat(), "phase": e.ev.phase, "next": self._next(),
                      "finished": e.finished()},
            "ready": sorted(self.ready),
            "clock_state": self.clock,
            "bots": sorted(self.bots),
            "chat": self.chat[-40:],
            "version": self.version,
            "fund": {
                "nav": str(nav), "cash": str(e.bal("cash")), "collateral": str(e.bal("collateral")),
                "debt": str(-e.bal("debt")), "credit_left": str(e.credit_left()), "reserve": str(e.buffer()),
                "long_mv": str(lm), "short_mv": str(sm),
                "gross": None if gross is None else str(gross),
                "net": None if net is None else str(net),
                "maintenance_req": str(e.margin()), "initial_req": str(e.margin("initial")),
                "margin_call": str(e.margin_call) if e.margin_call else None,
            },
            "positions": [{"sym": s, "qty": q, "mark": str(e.marks[s]), "mv": str(q * e.marks[s]),
                           "borrowed": e.borrowed(s)} for s, q in e.pos.items()],
            "marks": {s: str(m) for s, m in e.marks.items()},
            "series": [{"id": s.series_id, "units": str(s.units), "net": str(s.net), "provision": str(s.provision),
                        "hwm": str(s.hwm), "nav_per_unit": str(per_unit[s.series_id])}
                       for s in e.series],
            "firm": {"cash": str(e.bal("cash", "firm")), "fee_receivable": str(e.bal("fee_receivable", "firm")),
                     "payroll_payable": str(-e.bal("payroll_payable", "firm"))},
            "recall": {"open": e.recall_open, "resolved_by": e.recall_resolved_by,
                       "offer_visible": e.offer_visible and (role == "mp" or "borrow" in e.shared_research),
                       "replacement_accepted": e.replacement_accepted},
            "research": {"used": [dict(r) for r in e.research_used if r.get("owner") in (None, role)],
                         "budget": e.tape.raw["research"]["budget_per_role"],
                         "shared": sorted(e.shared_research),
                         "evidence": copy.deepcopy([n for n in e.visible_notices(role)
                                                    if n["code"] == "research_reveal"]),
                         "topics": sorted(t for t, a in e.tape.raw["research"]["assignments"].items()
                                          if a["role"] == role),
                         "assignments": {t: dict(a) for t, a in e.tape.raw["research"]["assignments"].items()
                                         if a["role"] == role}},
            "attention": {"window": e.cursor, "committed": e.attention.get(role, {}).get("window") == e.cursor,
                          "partners": copy.deepcopy(e.attention)},
            "orders": [{"order_id": o.order_id, "sym": o.sym, "side": o.side, "qty": o.qty, "filled": o.filled,
                        "status": o.status, "forced": o.forced, "fills": o.fills} for o in e.orders],
            "packages": [{"package_id": p.package_id, "proposer": p.proposer, "digest": p.digest, "status": p.status,
                          "signatures": sorted(p.signatures), "kind": p.kind, "terms": copy.deepcopy(p.terms),
                          "orders": [dict(zip(("order_id", "sym", "side", "qty", "limit"), o, strict=True))
                                     for o in p.orders]}
                         for p in self.packages.values()],
            "notices": copy.deepcopy(e.visible_notices(role)),
            "league": e.league(),  # rival returns come from public marks only
            "incidents": e.incidents,
            "incident_events": copy.deepcopy(e.incident_events),
            "decisions": [{"day": x["day"], "phase": x["phase"], "role": x["role"], "type": x["command"]["type"],
                           "detail": {k: v for k, v in x["command"].items() if k != "type"}}
                          for x in self.log if x["command"]["type"] not in ("ready", "tick", "say")],
            "outcome": e.outcome() if e.finished() else None,
            "investors": investors.view(e, role),
            "certification": e.certification()["status"],
        }

    def ledger(self, entity: str = "fund", limit: int = 200) -> list[dict]:
        return [x.canonical() for x in self.e.j.entries if x.entity == entity][-limit:]


COMMANDS: dict[str, Callable[[Session, str, Cmd], Cmd]] = {
    name[len("_cmd_"):]: fn for name, fn in vars(Session).items() if name.startswith("_cmd_")}
