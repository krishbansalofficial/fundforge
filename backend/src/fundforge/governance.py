"""Two-partner command authority over the engine.

* Every command carries an idempotency key: a retry returns the original result,
  and reusing a key for a different command is rejected.
* Small orders are independent PM tickets (<=5% NAV each, <=15% opening-NAV turnover).
  Anything larger is a package: its digest binds contents, policy version and expiry.
  The proposer's signature counts once; it executes only when the *other* partner
  signs the same digest. Edits produce a new digest, so old signatures never carry over.
* Replacement borrow and treasury reserve belong to the managing partner.
* Time advances only when both partners are ready; any state change clears readiness.
"""

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal

from .engine import CommandRejected, Engine
from .money import D, cents

POLICY_VERSION = "case1-authority-v1"
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


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


class Session:
    def __init__(self, engine: Engine, partners: dict[str, str]):
        if set(partners) != set(ROLES) or len(set(partners.values())) != 2:
            raise ValueError("exactly two distinct human partners are required")
        self.e = engine
        self.partners = partners  # role -> user id
        self.results: dict[str, tuple[str, object]] = {}
        self.packages: dict[str, Package] = {}
        self.ready: set[str] = set()
        self.turnover = Decimal(0)
        self.opening_nav = engine.nav()
        self.log: list[dict] = []

    def role_of(self, user: str) -> str:
        for r, u in self.partners.items():
            if u == user:
                return r
        raise CommandRejected("not a partner in this fund")

    # ---------- single entry point ----------
    def handle(self, user: str, key: str, command: dict):
        """Apply ``command`` once per idempotency ``key``."""
        fp = hashlib.sha256(canonical([user, command]).encode()).hexdigest()
        if key in self.results:
            prior_fp, result = self.results[key]
            if prior_fp != fp:
                raise CommandRejected(f"idempotency key {key!r} reused for a different command")
            return result
        role = self.role_of(user)
        result = getattr(self, "_cmd_" + command["type"])(role, command)
        self.results[key] = (fp, result)
        self.log.append({"day": self.e.ev.day, "phase": self.e.ev.phase, "role": role, "command": command, "result": result})
        if command["type"] != "ready":
            self.ready.clear()
        return result

    # ---------- commands ----------
    def _cmd_ticket(self, role, c):
        if role != "pm":
            raise CommandRejected("independent tickets belong to the portfolio manager")
        notional = self._notional(c)
        nav = self.e.nav()
        if notional > cents(nav * TICKET_NAV_LIMIT):
            raise CommandRejected(f"ticket ${notional:,.2f} exceeds 5% of NAV; propose a joint package")
        if self.turnover + notional > cents(self.opening_nav * TURNOVER_LIMIT):
            raise CommandRejected("independent turnover limit (15% of opening NAV) reached; propose a joint package")
        o = self.e.submit_order(c["order_id"], c["sym"], c["side"], int(c["qty"]), self._limit(c))
        self.turnover += notional
        return {"order_id": o.order_id, "status": o.status}

    def _cmd_propose(self, role, c):
        orders = tuple(sorted((o["order_id"], o["sym"], o["side"], int(o["qty"]), o.get("limit")) for o in c["orders"]))
        if not orders:
            raise CommandRejected("empty package")
        expires = self.e.cursor + 1  # valid only for the next execution event
        digest = hashlib.sha256(canonical([POLICY_VERSION, c["package_id"], orders, expires]).encode()).hexdigest()
        if c["package_id"] in self.packages:
            raise CommandRejected("package id already used; edits must be proposed as a new package")
        self.packages[c["package_id"]] = Package(c["package_id"], role, orders, expires, digest, {role})
        return {"package_id": c["package_id"], "digest": digest}

    def _cmd_sign(self, role, c):
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
        p.signatures.add(role)
        p.status = "AUTHORIZED_QUEUED"
        for oid, sym, side, qty, limit in p.orders:
            self.e.submit_order(oid, sym, side, qty, D(limit) if limit else None)
        return {"package_id": p.package_id, "status": p.status}

    def _cmd_cancel(self, role, c):
        self.e.cancel_order(c["order_id"])
        return {"order_id": c["order_id"], "status": "CANCELED"}

    def _cmd_research(self, role, c):
        self.e.assign_research(c["topic"])
        return {"topic": c["topic"]}

    def _cmd_accept_replacement(self, role, c):
        if role != "mp":
            raise CommandRejected("replacement borrow is the managing partner's decision")
        self.e.accept_replacement()
        return {"accepted": True}

    def _cmd_set_reserve(self, role, c):
        if role != "mp":
            raise CommandRejected("treasury reserve is the managing partner's decision")
        self.e.set_reserve(D(c["amount"]))
        return {"reserve": c["amount"]}

    def _cmd_ready(self, role, c):
        self.ready.add(role)
        if self.ready == set(ROLES) and not self.e.finished():
            self.ready.clear()
            for p in self.packages.values():
                if p.status == "PENDING_APPROVAL":
                    p.status = "EXPIRED"
            self.e.advance()
            return {"advanced": True, "next": self._next()}
        return {"advanced": False, "waiting_for": sorted(set(ROLES) - self.ready)}

    # ---------- helpers ----------
    def _limit(self, c):
        return D(c["limit"]) if c.get("limit") else None

    def _notional(self, c) -> Decimal:
        if c.get("sym") not in self.e.marks:
            raise CommandRejected(f"unknown instrument {c.get('sym')!r}")
        return cents(int(c["qty"]) * self.e.marks[c["sym"]])

    def _next(self):
        n = self.e.next_event()
        return None if n is None else {"day": n.day, "phase": n.phase, "date": n.date.isoformat()}

    # ---------- as-of player view ----------
    def view(self, user: str) -> dict:
        """Everything a partner may see now. Built only from processed events; the tape stays server-side."""
        role = self.role_of(user)
        e = self.e
        nav = e.nav()
        lm, sm = e.long_mv(), e.short_mv()
        return {
            "role": role,
            "partners": self.partners,
            "clock": {"day": e.ev.day, "date": e.ev.date.isoformat(), "phase": e.ev.phase, "next": self._next(),
                      "finished": e.finished()},
            "ready": sorted(self.ready),
            "fund": {
                "nav": str(nav), "cash": str(e.bal("cash")), "collateral": str(e.bal("collateral")),
                "debt": str(-e.bal("debt")), "credit_left": str(e.credit_left()), "reserve": str(e.reserve),
                "long_mv": str(lm), "short_mv": str(sm),
                "gross": str(((lm + sm) / nav).quantize(D("0.0001"))) if nav > 0 else None,
                "net": str(((lm - sm) / nav).quantize(D("0.0001"))) if nav > 0 else None,
                "maintenance_req": str(e.margin()), "initial_req": str(e.margin("initial")),
                "margin_call": str(e.margin_call) if e.margin_call else None,
            },
            "positions": [{"sym": s, "qty": q, "mark": str(e.marks[s]), "mv": str(q * e.marks[s]),
                           "borrowed": e.borrowed(s)} for s, q in e.pos.items()],
            "marks": {s: str(m) for s, m in e.marks.items()},
            "series": [{"id": s.series_id, "units": str(s.units), "net": str(s.net), "provision": str(s.provision),
                        "hwm": str(s.hwm), "nav_per_unit": str((s.net / s.units).quantize(D("0.0001")))}
                       for s in e.series],
            "firm": {"cash": str(e.bal("cash", "firm")), "fee_receivable": str(e.bal("fee_receivable", "firm")),
                     "payroll_payable": str(-e.bal("payroll_payable", "firm"))},
            "recall": {"open": e.recall_open, "resolved_by": e.recall_resolved_by,
                       "offer_visible": e.offer_visible, "replacement_accepted": e.replacement_accepted},
            "research": {"used": e.research_used, "budget": e.tape.raw["research"]["budget"],
                         "topics": sorted(e.tape.raw["research"]["topics"])},
            "orders": [{"order_id": o.order_id, "sym": o.sym, "side": o.side, "qty": o.qty, "filled": o.filled,
                        "status": o.status, "forced": o.forced, "fills": o.fills} for o in e.orders],
            "packages": [{"package_id": p.package_id, "proposer": p.proposer, "digest": p.digest, "status": p.status,
                          "signatures": sorted(p.signatures),
                          "orders": [dict(zip(("order_id", "sym", "side", "qty", "limit"), o)) for o in p.orders]}
                         for p in self.packages.values()],
            "notices": e.notices,
            "incidents": e.incidents,
            "outcome": e.outcome() if e.finished() else None,
        }

    def ledger(self, entity: str = "fund", limit: int = 200) -> list[dict]:
        return [x.canonical() for x in self.e.j.entries if x.entity == entity][-limit:]
