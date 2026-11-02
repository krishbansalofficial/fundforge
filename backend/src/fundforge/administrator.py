"""Independent Case1 LP/fee arithmetic; no engine, journal or series imports.

Capital inputs are synthetic observed holdings, settlement instructions and
broker balances. This is scoped reconciliation, not external NAV certification.
"""

from dataclasses import asdict, dataclass, replace
from decimal import ROUND_FLOOR, ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

CTX = Context(prec=40, rounding=ROUND_HALF_EVEN)
ZERO, CENT = Decimal(0), Decimal("0.01")


def split(amount: Decimal, weights: dict[str, Decimal]) -> dict[str, Decimal]:
    total = sum(weights.values(), ZERO)
    if total <= 0:
        raise ValueError("administrator requires positive participation")
    exact = {key: amount * weight / total for key, weight in weights.items()}
    rounded = {key: value.quantize(CENT, rounding=ROUND_FLOOR) for key, value in exact.items()}
    residual = int((amount - sum(rounded.values(), ZERO)) / CENT)
    priority = sorted(weights, key=lambda key: (rounded[key] - exact[key], key))
    for key in priority[:residual]:
        rounded[key] += CENT
    return rounded


@dataclass(frozen=True)
class Capital:
    series_id: str
    units: Decimal
    hwm: Decimal
    net: Decimal
    provision: Decimal = ZERO


@dataclass(frozen=True)
class Close:
    date: str
    series_id: str
    opening_participation: Decimal
    common_pnl: Decimal
    management_fee: Decimal
    closing: Capital


@dataclass(frozen=True)
class Claim:
    date: str
    series_id: str
    units: Decimal
    price: Decimal
    payable: Decimal
    crystallized_fee: Decimal
    surviving: Capital


class Administrator:
    def __init__(self, rows: list[dict[str, Any]], opening_nav: Decimal) -> None:
        with localcontext(CTX):
            caps = split(opening_nav, {r["id"]: Decimal(r["units"]) for r in rows})
        self.series = {r["id"]: Capital(r["id"], Decimal(r["units"]), Decimal(r["hwm"]), caps[r["id"]]) for r in rows}
        self.residuals: dict[str, Decimal] = {}
        self.liabilities = {a: ZERO for a in ("mgmt_fee_accrued", "mgmt_fee_payable", "perf_fee_payable",
                                             "redemption_payable")}
        self.revenue = ZERO
        self.closes: tuple[Close, ...] = ()
        self.claims: tuple[Claim, ...] = ()

    def close(self, d: str, wealth_before_admin_claims: Decimal) -> None:
        with localcontext(CTX):
            if any(c.date == d for c in self.closes):
                raise ValueError("duplicate administrator close date")
            active = {key: s for key, s in self.series.items() if s.units > 0}
            weights = {key: s.net + s.provision for key, s in active.items()}
            pnl = wealth_before_admin_claims - sum(self.liabilities.values(), ZERO) - sum(weights.values(), ZERO)
            allocated = split(pnl, weights)
            for key, s in active.items():
                unrounded = weights[key] * Decimal("0.015") / Decimal(365) + self.residuals.get(key, ZERO)
                fee = unrounded.quantize(CENT)
                self.residuals[key] = unrounded - fee
                gross = weights[key] + allocated[key] - fee
                # Algebraic capital-above-HWM form, separate from series.reprovision.
                provision = (max(ZERO, gross - s.hwm * s.units) / Decimal(5)).quantize(CENT)
                closing = replace(s, net=gross - provision, provision=provision)
                self.series[key] = closing
                self.liabilities["mgmt_fee_accrued"] += fee
                self.revenue += fee
                self.closes += (Close(d, key, weights[key], allocated[key], fee, closing),)

    def invoice(self) -> None:
        with localcontext(CTX):
            self.liabilities["mgmt_fee_payable"] += self.liabilities["mgmt_fee_accrued"]
            self.liabilities["mgmt_fee_accrued"] = ZERO

    def pay(self, account: str, amount: Decimal) -> None:
        if account in self.liabilities:
            with localcontext(CTX):
                self.liabilities[account] -= amount

    def preview(self, d: str, key: str, units: Decimal) -> Claim:
        with localcontext(CTX):
            s = self.series[key]
            if not ZERO < units <= s.units:
                raise ValueError("invalid administrator redemption units")
            price = s.net / s.units
            # exact pro-rata (FUND_ACCOUNTING): multiply first, so only the cent quantize rounds a half-cent tie
            payable = (s.net * units / s.units).quantize(CENT)
            fee = (s.provision * units / s.units).quantize(CENT)
            return Claim(d, key, units, price, payable, fee,
                         replace(s, units=s.units - units, net=s.net - payable, provision=s.provision - fee))

    def subscribe(self, key: str, units: Decimal, hwm: Decimal, amount: Decimal) -> None:
        if key in self.series:
            raise ValueError("a subscription creates a new series")
        self.series[key] = Capital(key, units, hwm, amount)

    def deal(self, claim: Claim) -> None:
        if claim != self.preview(claim.date, claim.series_id, claim.units):
            raise ValueError("stale administrator claim")
        with localcontext(CTX):
            self.series[claim.series_id] = claim.surviving
            self.liabilities["redemption_payable"] += claim.payable
            self.liabilities["perf_fee_payable"] += claim.crystallized_fee
            self.revenue += claim.crystallized_fee
            self.claims += (claim,)

    def inspect(self, actual: dict[str, Capital], fund: dict[str, Decimal], firm: dict[str, Decimal],
                posted_fees: dict[tuple[str, str], Decimal]) -> dict[str, Any]:
        with localcontext(CTX):
            breaks = []

            def check(code: str, subject: str, got: Any, wanted: Any) -> None:
                if got != wanted:
                    breaks.append({"code": code, "subject": subject, "actual": str(got), "expected": str(wanted)})

            for key in sorted(actual.keys() | self.series.keys()):
                wanted = self.series.get(key)
                check("lp_series", key, actual.get(key), wanted)
                if wanted:
                    check("lp_capital", key, -fund.get(f"capital:{key}", ZERO), wanted.net)
                    check("lp_provision", key, -fund.get(f"provision:{key}", ZERO), wanted.provision)
            for account, amount in self.liabilities.items():
                check("admin_claim", account, -fund.get(account, ZERO), amount)
            receivable = sum((v for k, v in self.liabilities.items() if k != "redemption_payable"), ZERO)
            check("manager_receivable", "firm", firm.get("fee_receivable", ZERO), receivable)
            check("manager_revenue", "firm", -firm.get("fee_revenue", ZERO), self.revenue)
            expected_fees = {(c.date, c.series_id): c.management_fee for c in self.closes}
            for key in sorted(expected_fees.keys() | posted_fees.keys()):
                check("management_fee_date", "/".join(key), posted_fees.get(key, ZERO), expected_fees.get(key, ZERO))
            return {"status": "break" if breaks else "checked", "breaks": breaks,
                    "close_count": len({c.date for c in self.closes}), "claim_count": len(self.claims),
                    "series": [{k: str(v) for k, v in asdict(s).items()} for s in self.series.values()],
                    "liabilities": {k: str(v) for k, v in self.liabilities.items()},
                    "claims": [{k: str(v) for k, v in asdict(c).items() if k != "surviving"} for c in self.claims]}
