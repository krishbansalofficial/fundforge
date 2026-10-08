"""LP series claims: participation, HWM performance provision, redemption (FUND_ACCOUNTING §5-6)."""

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext

from .money import CTX, allocate, cents

PERF_RATE = Decimal("0.20")
MGMT_RATE = Decimal("0.015")  # ACT/365


@dataclass(frozen=True)
class Series:
    series_id: str
    units: Decimal  # 8dp
    hwm: Decimal  # per unit, last annual crystallized post-fee NAV/unit
    net: Decimal  # N: capital net of the reversible provision
    provision: Decimal = Decimal(0)  # F: reversible performance-fee liability

    @property
    def participation(self) -> Decimal:
        """A_s = N_s + F_s: the weight for common P&L (provision is added back exactly once)."""
        return self.net + self.provision


def reprovision(s: Series, gross: Decimal) -> Series:
    """Given participation capital B after P&L/fees, reset F to its target and N = B - F."""
    with localcontext(CTX):
        f = cents(PERF_RATE * max(Decimal(0), gross / s.units - s.hwm) * s.units)
    return replace(s, net=gross - f, provision=f)


def allocate_common(book: list[Series], amount: Decimal) -> list[Series]:
    """Allocate common P&L/expense by opening participation, then re-provision each series."""
    shares = allocate(amount, {s.series_id: s.participation for s in book})
    return [reprovision(s, s.participation + shares[s.series_id]) for s in book]


def mgmt_fee_exact(s: Series) -> Decimal:
    """Unrounded daily management fee on opening participation; caller posts via Accrual."""
    with localcontext(CTX):
        return s.participation * MGMT_RATE / 365


def charge(s: Series, amount: Decimal) -> Series:
    """Series-specific fixed charge (e.g. posted management fee) then re-provision."""
    return reprovision(s, s.participation - amount)


def crystallize_annual(s: Series) -> tuple[Series, Decimal]:
    with localcontext(CTX):
        new_hwm = max(s.hwm, s.net / s.units)
    return replace(s, hwm=new_hwm, provision=Decimal(0)), s.provision


def redeem(s: Series, units: Decimal) -> tuple[Series, Decimal, Decimal]:
    """Deal a redemption: returns (surviving series, redemption payable, crystallized fee).

    Crystallizes only the redeemed fraction of F; surviving HWM is unchanged.
    """
    if not 0 < units <= s.units:
        raise ValueError(f"{s.series_id}: invalid redemption of {units} units")
    with localcontext(CTX):
        frac = units / s.units
        fee = cents(s.provision * frac)
        payable = cents(s.net * frac)
    return replace(s, units=s.units - units, net=s.net - payable, provision=s.provision - fee), payable, fee
