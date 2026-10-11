"""Chapter-close facts for LP confidence (``lp.chapter_close``) read from a finished engine window.

Only typed engine state is used: series units/net, typed notices and incidents, and the
control report. Facts the engine cannot yet produce are stated, not guessed:

- avoidable breaches: the engine refuses mandate-breaching orders before and at execution and
  does not yet type passive (market-driven) breaches, so the count is 0;
- gate deferral: no gate election exists in the engine yet, so it is False;
- meeting evidence: no LP meeting command exists yet, so it is None.
"""

from decimal import Decimal, localcontext

from .engine import Engine
from .lp import ChapterFacts
from .money import CTX


def chapter_facts(e: Engine, start_nav_per_unit: dict[str, Decimal], start_day: int) -> dict[str, ChapterFacts]:
    """Facts per series still holding units, for the window from ``start_day`` to the engine's current day."""
    dealt = {n["refs"].get("series") for n in e.notices
             if n["code"] == "redemption_dealt" and n["day"] >= start_day}
    unpaid_redemptions = sum(1 for i in e.incident_events
                             if i["code"] == "claim_unpaid" and i["refs"].get("claim") == "redemption"
                             and i["day"] >= start_day)
    certified = e.control_report()["status"] == "checked"
    out: dict[str, ChapterFacts] = {}
    with localcontext(CTX):
        for s in e.series:
            if s.units <= 0:
                continue  # a fully redeemed LP is no longer in the fund
            ret = (s.net / s.units / start_nav_per_unit[s.series_id] - 1) * 100
            out[s.series_id] = ChapterFacts(
                net_return_pp=ret, report_certified=certified,
                overdue_payments=unpaid_redemptions if s.series_id in dealt else 0)
    return out
