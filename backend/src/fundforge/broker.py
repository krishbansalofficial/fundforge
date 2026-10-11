"""Synthetic broker evidence, independently reduced without journal/engine imports.

Activity confirms instructed settlements/cash movements, not an external bank.
Fee arithmetic uses its own loan balances and rounding residuals. Authored
statements are separate dated evidence; corrections never replace originals.
"""

from dataclasses import asdict, dataclass, replace
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

CTX = Context(prec=40, rounding=ROUND_HALF_EVEN)
ZERO, CENT = Decimal(0), Decimal("0.01")
PHASES = ("OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE")


def coordinate(value: dict[str, Any]) -> tuple[int, int]:
    return value["day"], PHASES.index(value["phase"])


def validate_statements(records: list[dict[str, Any]], start: int, end: int) -> None:
    seen: dict[tuple[str, int], dict[str, Any]] = {}
    for r in records:
        try:
            key = (r["id"], r["revision"])
            prior = seen.get((r["id"], r["revision"] - 1))
            amount = Decimal(r["balance"])
            if (not isinstance(r["id"], str) or not r["id"] or type(r["revision"]) is not int
                    or key in seen or not isinstance(r["balance"], str) or not amount.is_finite()
                    or amount < 0 or amount != amount.quantize(CENT)
                    or r["account"] not in ("cash", "collateral", "debt")
                    or not isinstance(r["source"], str) or not r["source"].strip()
                    or not start <= r["as_of"]["day"] <= r["available_at"]["day"] <= end
                    or coordinate(r["as_of"]) > coordinate(r["available_at"])
                    or any(type(r[k]["day"]) is not int or (r[k]["day"] == end
                           and r[k]["phase"] != "OPEN_ADMIN") for k in ("as_of", "available_at"))):
                raise ValueError("invalid statement record")
            if r["revision"] == 1:
                if r.get("supersedes") is not None:
                    raise ValueError("original statement cannot supersede another revision")
            elif (prior is None or r.get("supersedes") != prior["revision"]
                  or not isinstance(r.get("reason"), str) or not r["reason"].strip()
                  or any(r[k] != prior[k] for k in ("source", "account", "as_of"))
                  or coordinate(r["available_at"]) <= coordinate(prior["available_at"])):
                raise ValueError("correction must link its previous revision, source and as-of time")
            seen[key] = r
        except (KeyError, TypeError, ArithmeticError) as exc:
            raise ValueError("malformed broker statement") from exc


@dataclass(frozen=True)
class Activity:
    sequence: int
    date: str
    kind: str
    amount: Decimal = ZERO
    frozen: Decimal = ZERO
    loan_id: str = ""
    sym: str = ""
    obligation: str = ""  # settlement identity of the execution this receipt settles
    qty: int = 0
    rate: Decimal = ZERO
    claim: str = ""


@dataclass(frozen=True)
class Borrow:
    sym: str
    qty: int
    rate: Decimal


@dataclass(frozen=True)
class Fee:
    date: str
    loan_id: str
    qty: int
    basis: Decimal
    rate: Decimal
    amount: Decimal


@dataclass(frozen=True)
class Statement:
    id: str
    revision: int
    source: str
    account: str
    as_of: tuple[int, int]
    available_at: tuple[int, int]
    balance: Decimal
    expected: Decimal
    received_date: str
    supersedes: int | None
    reason: str


@dataclass(frozen=True)
class Resolution:
    statement_id: str
    revision: int
    date: str
    actor: str


class Broker:
    def __init__(self, opening: dict[str, Any], rate: Decimal) -> None:
        self.balances = {a: Decimal(opening[a]) for a in ("cash", "collateral", "debt")}
        self.loans = {f"L-open-{s}": Borrow(s, -q, rate) for s, q in opening["positions"].items() if q < 0}
        self.activities: tuple[Activity, ...] = ()
        self.fees: tuple[Fee, ...] = ()
        self.residuals: dict[str, Decimal] = {}
        self.accrued = ZERO
        self.invoiced = ZERO
        self.snapshots: dict[tuple[int, int], dict[str, Decimal]] = {}
        self.statements: tuple[Statement, ...] = ()
        self.resolutions: tuple[Resolution, ...] = ()

    def record(self, d: date, kind: str, **values: Any) -> None:
        a = Activity(len(self.activities) + 1, d.isoformat(), kind, **values)
        with localcontext(CTX):
            b = self.balances
            if kind == "draw":
                b["cash"] += a.amount
                b["debt"] += a.amount
            elif kind == "repay":
                b["cash"] -= a.amount
                b["debt"] -= a.amount
            elif kind == "collateral":
                b["cash"] -= a.amount
                b["collateral"] += a.amount
            elif kind == "SELL":
                b["cash"] += a.amount
            elif kind == "SHORT":
                b["collateral"] += a.amount
            elif kind in ("BUY", "payment"):
                b["cash"] -= a.amount
                if a.claim == "interest_payable":
                    self.invoiced -= a.amount
            elif kind == "COVER":
                b["cash"] += a.frozen - a.amount
                b["collateral"] -= a.frozen
            elif kind == "loan":
                if a.loan_id in self.loans:
                    raise ValueError("duplicate broker loan")
                self.loans[a.loan_id] = Borrow(a.sym, a.qty, a.rate)
            elif kind == "return":
                old = self.loans[a.loan_id]
                if not 0 < a.qty <= old.qty:
                    raise ValueError("invalid broker loan return")
                if a.qty == old.qty:
                    del self.loans[a.loan_id]
                else:
                    self.loans[a.loan_id] = replace(old, qty=old.qty - a.qty)
            elif kind == "rate":
                self.loans[a.loan_id] = replace(self.loans[a.loan_id], rate=a.rate)
            elif kind == "invoice":
                self.invoiced += self.accrued
                self.accrued = ZERO
            else:
                raise ValueError(f"unknown broker activity {kind}")
        self.activities += (a,)

    def accrue(self, d: date, marks: dict[str, Decimal], debit_rate: Decimal) -> None:
        if any(f.date == d.isoformat() for f in self.fees):
            raise ValueError("duplicate broker accrual date")
        with localcontext(CTX):
            bases = [(key, loan.qty, loan.qty * marks[loan.sym], loan.rate)
                     for key, loan in sorted(self.loans.items())]
            bases.append(("debit", 0, self.balances["debt"], debit_rate))
            for key, qty, basis, rate in bases:
                unrounded = basis * rate / Decimal(360) + self.residuals.get(key, ZERO)
                amount = unrounded.quantize(CENT)
                self.residuals[key] = unrounded - amount
                self.accrued += amount
                self.fees += (Fee(d.isoformat(), key, qty, basis, rate, amount),)

    def discrepancies(self, balances: dict[str, Decimal], loans: dict[str, Borrow],
                      posted_fees: dict[str, Decimal]) -> list[dict[str, str]]:
        with localcontext(CTX):
            return self._discrepancies(balances, loans, posted_fees)

    def _discrepancies(self, balances: dict[str, Decimal], loans: dict[str, Borrow],
                       posted_fees: dict[str, Decimal]) -> list[dict[str, str]]:
        issues = []

        def check(code: str, subject: str, actual: Any, expected: Any) -> None:
            if actual != expected:  # cents already rounded; no unexplained one-cent plug
                issues.append({"code": code, "subject": subject, "actual": str(actual), "expected": str(expected)})

        for account, value in self.balances.items():
            check("broker_balance", account, balances.get(account, ZERO) * (-1 if account == "debt" else 1), value)
        check("financing_accrued", "fund", -balances.get("accrued_interest", ZERO), self.accrued)
        check("financing_invoiced", "fund", -balances.get("interest_payable", ZERO), self.invoiced)
        for key in sorted(loans.keys() | self.loans.keys()):
            check("settled_loan", key, loans.get(key), self.loans.get(key))
        daily: dict[str, Decimal] = {}
        with localcontext(CTX):
            for fee in self.fees:
                daily[fee.date] = daily.get(fee.date, ZERO) + fee.amount
            for d in sorted(daily.keys() | posted_fees.keys()):
                check("financing_date", d, posted_fees.get(d, ZERO), daily.get(d, ZERO))
        return issues

    def observe(self, day: int, phase: str, d: date, authored: list[dict[str, Any]]) -> list[str]:
        now = day, PHASES.index(phase)
        self.snapshots[now] = dict(self.balances)
        received = {(s.id, s.revision) for s in self.statements}
        arrivals = []
        for r in authored:
            if coordinate(r["available_at"]) != now or (r["id"], r["revision"]) in received:
                continue
            expected = self.snapshots[coordinate(r["as_of"])][r["account"]]
            s = Statement(r["id"], r["revision"], r["source"], r["account"], coordinate(r["as_of"]), now,
                          Decimal(r["balance"]), expected, d.isoformat(), r.get("supersedes"), r.get("reason", ""))
            self.statements += (s,)
            if s.balance != s.expected or s.revision > 1:
                arrivals.append(s.id)
        return arrivals

    def queue(self, today: date) -> list[dict[str, Any]]:
        rows = []
        for sid in sorted({s.id for s in self.statements}):
            history = [s for s in self.statements if s.id == sid]
            wrong = [s for s in history if s.balance != s.expected]
            if not wrong:
                continue
            latest, first = history[-1], wrong[0]
            resolved = next((r for r in reversed(self.resolutions) if r.statement_id == sid
                             and r.revision == latest.revision), None)
            rows.append({"id": sid, "owner": "mp", "status": "resolved" if resolved else "open",
                         "age_calendar_days": ((date.fromisoformat(resolved.date) if resolved else today)
                                               - date.fromisoformat(first.received_date)).days,
                         "revision": latest.revision, "account": latest.account,
                         "actual": str(latest.balance), "expected": str(latest.expected),
                         "can_resolve": resolved is None and latest.balance == latest.expected,
                         "resolution": asdict(resolved) if resolved else None,
                         "resolution_history": [asdict(r) for r in self.resolutions if r.statement_id == sid],
                         "history": [{**asdict(s), "balance": str(s.balance), "expected": str(s.expected),
                                      "as_of": {"day": s.as_of[0], "phase": PHASES[s.as_of[1]]},
                                      "available_at": {"day": s.available_at[0], "phase": PHASES[s.available_at[1]]}}
                                     for s in history]})
        return rows

    def resolve(self, sid: str, revision: int, today: date, actor: str) -> None:
        row = next((r for r in self.queue(today) if r["id"] == sid), None)
        if row is None or row["revision"] != revision or not row["can_resolve"]:
            raise ValueError("a matching, published correction is required; review the latest revision")
        self.resolutions += (Resolution(sid, revision, today.isoformat(), actor),)
