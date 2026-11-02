"""Pre-trade and at-execution mandate checks (GAME_SYSTEMS §2, compliance review).

A ruleset is versioned Decimal data from the scenario. An order is refused when the book it
would produce breaks a limit *and* the order makes that limit worse, so risk-reducing trades
stay allowed while the fund is already outside a band (passive breaches are remediated, not
frozen). A second partner's signature never overrides a hard limit.
"""

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any

from .money import CTX, D


@dataclass(frozen=True)
class Ruleset:
    version: str
    gross_min: Decimal
    gross_max: Decimal
    net_min: Decimal
    net_max: Decimal
    issuer_max: Decimal
    issuer_exempt: frozenset[str]
    restricted: frozenset[str]

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "Ruleset":
        return cls(raw["version"], D(raw["gross_min"]), D(raw["gross_max"]), D(raw["net_min"]), D(raw["net_max"]),
                   D(raw["issuer_max"]), frozenset(raw.get("issuer_exempt", [])), frozenset(raw.get("restricted", [])))

    @property
    def digest(self) -> str:
        blob = json.dumps({k: sorted(v) if isinstance(v, frozenset) else str(v) for k, v in vars(self).items()},
                          sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()


@dataclass(frozen=True)
class Breach:
    code: str
    detail: str


def _measures(pos: dict[str, int], marks: dict[str, Decimal], nav: Decimal, rs: Ruleset) -> dict[str, Decimal]:
    with localcontext(CTX):
        long_mv = sum((q * marks[s] for s, q in pos.items() if q > 0), Decimal(0))
        short_mv = sum((-q * marks[s] for s, q in pos.items() if q < 0), Decimal(0))
        out = {"gross": (long_mv + short_mv) / nav, "net": (long_mv - short_mv) / nav}
        for s, q in pos.items():
            if s not in rs.issuer_exempt:
                out[f"issuer:{s}"] = abs(q) * marks[s] / nav
        return out


def evaluate(pos: dict[str, int], marks: dict[str, Decimal], nav: Decimal,
             orders: list[tuple[str, str, int]], rs: Ruleset) -> list[Breach]:
    """Breaches caused or worsened by applying ``orders`` (sym, side, qty) to ``pos`` at ``marks``."""
    if nav <= 0:
        return [Breach("nav_nonpositive", "NAV is not positive; only risk-reducing remediation is allowed")]
    after = dict(pos)
    breaches = []
    for sym, side, qty in orders:
        if sym in rs.restricted and side in ("BUY", "SHORT"):
            breaches.append(Breach("restricted", f"{sym} is on the restricted list"))
        after[sym] = after.get(sym, 0) + (qty if side in ("BUY", "COVER") else -qty)
    pre, post = _measures(pos, marks, nav, rs), _measures(after, marks, nav, rs)
    for key, lo, hi in (("gross", rs.gross_min, rs.gross_max), ("net", rs.net_min, rs.net_max)):
        x = post[key]
        if x > hi and x > pre[key]:
            breaches.append(Breach(f"{key}_max", f"{key} exposure {x:.1%} would exceed the {hi:.0%} mandate cap"))
        if x < lo and x < pre[key]:
            breaches.append(Breach(f"{key}_min", f"{key} exposure {x:.1%} would fall below the {lo:.0%} mandate floor"))
    for key, val in post.items():
        if key.startswith("issuer:") and val > rs.issuer_max and val > pre.get(key, Decimal(0)):
            cap = rs.issuer_max
            breaches.append(Breach("issuer_max", f"{key[7:]} would be {val:.1%} of NAV, above the {cap:.0%} cap"))
    return breaches


def subscription_breaches(pos: dict[str, int], marks: dict[str, Decimal], nav: Decimal, added: Decimal,
                          rs: Ruleset) -> list[Breach]:
    """Capacity: new capital shrinks exposure ratios on the same book, so it can only worsen the mandate floors."""
    if nav <= 0:
        return [Breach("nav_nonpositive", "NAV is not positive")]
    pre, post = _measures(pos, marks, nav, rs), _measures(pos, marks, nav + added, rs)
    return [Breach(f"{key}_min", f"{key} exposure {post[key]:.1%} would fall below the {lo:.0%} mandate floor")
            for key, lo in (("gross", rs.gross_min), ("net", rs.net_min)) if post[key] < lo and post[key] < pre[key]]
