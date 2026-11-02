"""LP agents read from, and acting on, a running engine (GAME_SYSTEMS §4; ``lp.py`` holds the rules).

``chapter_facts`` derives chapter-close facts from typed engine state only. Facts the engine cannot
yet produce are stated, not guessed:

- avoidable breaches: the engine refuses mandate-breaching orders before and at execution and
  does not yet type passive (market-driven) breaches, so the count is 0;
- meeting evidence: no LP meeting-with-evidence command exists yet, so it is None.

In generated-market rooms (tape ``lp_agents`` = ``lp.POLICY_VERSION``) the engine also calls
``on_close`` at every business close, after dealing (FUND_ACCOUNTING §7 step 7):

- peaks of each series' net value per unit are tracked at closes;
- at ``lp.REVIEW_DAYS`` closes, ``lp.review`` applies drawdown, response-lag and contact terms;
- at a notice cutoff, ``lp.redemption_request`` creates unit requests from the confidence just
  certified, using the scenario's authored redemption as the LP's external need (the larger of
  the two, never their sum), dealt ``lp.DEALING_LAG`` business days later;
- at a chapter close, ``lp.chapter_close`` with gate deferral and herding.

Confidence values never leave the server during play: the managing partner sees bands
(``view``); exact components are in the finished run's debrief.

Campaign prospect (GAME_SYSTEMS fundraising pipeline, FUND_ACCOUNTING §5): stage only, no money, until
``deal_subscription`` calls ``Engine.admit_series`` at the dealing close. An admitted series is locked through the
campaign and is not one of the three LP agents: it has no confidence state and makes no redemption request.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from typing import TYPE_CHECKING, Any

from .compliance import subscription_breaches
from .lp import (
    DEALING_LAG,
    LAUNCH,
    NOTICE_CUTOFFS,
    POLICY_VERSION,
    REVIEW_DAYS,
    Book,
    ChapterFacts,
    ReviewFacts,
    State,
    allocate_gate,
    band,
    chapter_close,
    drawdown_pp,
    redemption_request,
    review,
)
from .money import CTX, D

if TYPE_CHECKING:
    from .engine import Engine


class Refused(ValueError):
    """A player LP action the rules do not allow now; the engine turns it into CommandRejected."""


def review_days(e: Engine) -> tuple[int, ...]:
    return tuple(e.tape.raw.get("campaign", {}).get("review_days", REVIEW_DAYS))


def chapter_facts(e: Engine, start_nav_per_unit: dict[str, Decimal], start_day: int) -> dict[str, ChapterFacts]:
    """Facts per series still holding units, for the window from ``start_day`` to the engine's current day."""
    dealt = {n["refs"].get("series") for n in e.notices
             if n["code"] == "redemption_dealt" and n["day"] >= start_day}
    unpaid_redemptions = sum(1 for i in e.incident_events
                             if i["code"] == "claim_unpaid" and i["refs"].get("claim") == "redemption"
                             and i["day"] >= start_day)
    # Ordinary chapter reports can reconcile before any redemption is due. A pending
    # dealing certificate is not certification; when dealing did occur in this window,
    # its frozen results also constrain the chapter report, even after controls recover.
    certificates = [c for c in e.certificates if start_day <= c["day"] <= e.ev.day]
    certified = (e.control_report()["status"] == "checked"
                 and all(c["status"] == "certified" for c in certificates))
    deferred = {k for k, v in e.lp.carried.items() if v > 0} if e.lp else set()
    out: dict[str, ChapterFacts] = {}
    with localcontext(CTX):
        for s in e.series:
            if s.units <= 0 or s.series_id not in start_nav_per_unit:
                continue  # a fully redeemed LP is no longer in the fund; an admitted series is not an LP agent
            ret = (s.net / s.units / start_nav_per_unit[s.series_id] - 1) * 100
            out[s.series_id] = ChapterFacts(
                net_return_pp=ret, report_certified=certified,
                overdue_payments=unpaid_redemptions if s.series_id in dealt else 0,
                gate_deferred=s.series_id in deferred, peer_gated=bool(deferred - {s.series_id}))
    return out


def open_book(e: Engine) -> Book:
    if e.tape.raw["lp_agents"] != POLICY_VERSION:
        raise ValueError(f"tape asks for LP policy {e.tape.raw['lp_agents']!r}; this server runs {POLICY_VERSION}")
    with localcontext(CTX):
        value = {s.series_id: s.net / s.units for s in e.series}
    return Book(profiles={s.series_id: LAUNCH[s.series_id.lower()] for s in e.series},
                states={s.series_id: State(LAUNCH[s.series_id.lower()].initial) for s in e.series},
                peaks=dict(value), start_value=value, start_day=e.ev.day)


def _record(e: Engine, b: Book, kind: str, sid: str, before: State, comp: dict[str, str]) -> None:
    b.log.append({"day": str(e.ev.day), "kind": kind, "lp": sid, **comp})
    if band(before.confidence) != comp["band"]:
        e._notice(f"{sid} LP relationship is now {comp['band'].replace('_', ' ')}.", code="lp_band",
                  owner="mp", series=sid, band=comp["band"])  # the managing partner holds the LP inbox


def on_close(e: Engine) -> None:
    b = e.lp
    if b is None:
        return
    day = e.ev.day
    live = [s for s in e.series if s.units > 0 and s.series_id in b.states]
    with localcontext(CTX):
        for s in live:
            b.peaks[s.series_id] = max(b.peaks[s.series_id], s.net / s.units)
        if day in review_days(e):
            alerts = int(e.margin_call is not None) + int(e.recall_open > 0 and not e.replacement_accepted)
            for s in live:
                sid, before = s.series_id, b.states[s.series_id]
                facts = ReviewFacts(drawdown_pp(b.peaks[sid], s.net / s.units), alerts, sid in b.contacts)
                b.states[sid], comp = review(b.profiles[sid], before, facts)
                _record(e, b, "review", sid, before, {**comp, "drawdown_pp": str(facts.drawdown_pp),
                                                      "open_alerts": str(alerts)})
            b.contacts.clear()
    cutoffs = tuple(e.tape.raw.get("campaign", {}).get("notice_cutoffs", NOTICE_CUTOFFS))
    if day in cutoffs and e.winddown is None:  # a declared winddown redeems every unit: no new requests
        deal = day + DEALING_LAG
        external: dict[str, Decimal] = {}
        for r in e.tape.raw["redemptions"]:
            if r["deal_day"] == deal:
                external[r["series"]] = external.get(r["series"], Decimal(0)) + D(r["units"])
        for s in live:
            sid = s.series_id
            units = redemption_request(b.profiles[sid], b.states[sid].confidence, s.units, day,
                                       external.get(sid, Decimal(0)), notice_cutoffs=cutoffs)
            if e.tape.raw.get("campaign"):
                units = min(s.units, units + b.carried.get(sid, Decimal(0)))
            if units > 0:
                b.requests[sid] = b.requests.get(sid, Decimal(0)) + units
                e._notice(f"{sid} gave formal notice to redeem {units:,} units at the day {deal} dealing close.",
                          code="redemption_notice", series=sid, units=str(units), deal_day=deal)
        b.deal_day = deal
    if day % 10 == 0:  # chapter close: after dealing, with this window's gate deferrals
        for sid, f in chapter_facts(e, b.start_value, b.start_day).items():
            before = b.states[sid]
            b.states[sid], comp = chapter_close(b.profiles[sid], before, f)
            _record(e, b, "chapter_close", sid, before, comp)
        if e.tape.raw.get("campaign"):
            # Returns and drawdown belong to this chapter, not the cumulative campaign.
            # Start the next window after this close; carried units remain invested.
            with localcontext(CTX):
                b.start_value = {s.series_id: s.net / s.units for s in live if s.units > 0}
            b.peaks = dict(b.start_value)
            b.start_day = day + 1


def dealing(e: Engine) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """(dealt, carried) units for today's dealing close; pure, so a blocked dealing changes nothing."""
    b = e.lp
    if b is None or b.deal_day != e.ev.day or not b.requests:
        return {}, {}
    with localcontext(CTX):
        price = {s.series_id: s.net / s.units for s in e.series if s.series_id in b.requests}
    return allocate_gate(e.nav(), dict(b.requests), price, gated=b.gate_day == e.ev.day)


def dealt(e: Engine, carried: dict[str, Decimal]) -> None:
    """Close the window: undealt units stay invested and roll forward (GAME_SYSTEMS §4 gates)."""
    b = e.lp
    assert b is not None
    b.requests = {}
    if e.tape.raw.get("campaign"):
        b.carried = {}  # this window re-presented prior carried units; replace with its residual
    for sid, units in carried.items():
        if units > 0:
            b.carried[sid] = b.carried.get(sid, Decimal(0)) + units
            e._notice(f"Gate: {units:,} {sid} units were not dealt; they stay invested and carry forward.",
                      "alert", code="redemption_gated", series=sid, units=str(units))


def contact(e: Engine, role: str, sid: str) -> None:
    b = e.lp
    if b is None:
        raise Refused("LP contact is available only in generated-market rooms")
    if not e.at_barrier() or e.finished():
        raise Refused("LP contact happens at a decision barrier")
    if sid not in b.states or not any(s.series_id == sid and s.units > 0 for s in e.series):
        raise Refused(f"no LP {sid!r} in the fund")
    if e.attention.get(role, {}).get("window") == e.cursor:
        raise Refused("attention already committed for this decision window")
    if not any(d >= e.ev.day for d in review_days(e)):
        raise Refused("no LP review remains in this window")
    if sid in b.contacts:
        raise Refused(f"{sid} was already contacted before its next review")
    b.contacts.add(sid)
    e.attention[role] = {"window": e.cursor, "location": "lp", "assignment": f"contact:{sid}"}


def gate_terms(e: Engine) -> dict[str, Any]:
    """What a gate election binds to: the dealing day and the exact pending requests."""
    b = e.lp
    if b is None:
        raise Refused("gate elections exist only in generated-market rooms")
    if not e.at_barrier() or e.finished():
        raise Refused("a gate is elected at a decision barrier before the dealing close")
    if b.deal_day is None or not b.requests or e.ev.day > b.deal_day:
        raise Refused("no redemption requests await a dealing close")
    if b.gate_day == b.deal_day:
        raise Refused("a gate is already elected for this dealing close")
    return {"deal_day": b.deal_day, "requests": {k: str(v) for k, v in sorted(b.requests.items())}}


def elect_gate(e: Engine, terms: dict[str, Any]) -> None:
    assert e.lp is not None
    e.lp.gate_day = terms["deal_day"]
    e._notice(f"Both partners elected a gate for the day {terms['deal_day']} dealing close: at most 20% of "
              "pre-flow NAV is dealt, pro rata.", code="gate_elected", deal_day=terms["deal_day"])


def view(e: Engine, role: str) -> dict[str, Any] | None:
    """The managing partner's LP inbox: last certified bands and pending requests, never exact values."""
    b = e.lp
    if b is None or role != "mp":
        return None
    return {"policy": POLICY_VERSION, "deal_day": b.deal_day,
            "gate_elected": b.gate_day is not None and b.gate_day == b.deal_day,
            "lps": [{"id": sid, "band": band(b.states[sid].confidence),
                     "requested_units": str(b.requests[sid]) if sid in b.requests else None,
                     "carried_units": str(b.carried[sid]) if sid in b.carried else None,
                     "first_cutoff": b.profiles[sid].first_eligible_cutoff,
                     "contacted": sid in b.contacts}
                    for sid in sorted(b.states)]}


def debrief(e: Engine) -> dict[str, Any] | None:
    b = e.lp
    if b is None:
        return None
    return {"policy": POLICY_VERSION, "checkpoints": [dict(x) for x in b.log],
            "final": {sid: {"confidence": str(st.confidence), "band": band(st.confidence)}
                      for sid, st in sorted(b.states.items())},
            "carried_units": {k: str(v) for k, v in sorted(b.carried.items())}}



# ---------- campaign prospect: prospect -> qualified -> diligence -> committed -> eligible -> admitted ----------
ISSUE_PRICE = Decimal(100)  # FUND_ACCOUNTING §5: every subscription is a new series at 100, HWM 100
CLOSED = ("admitted", "forfeited", "declined")


@dataclass
class Prospect:
    stage: str = "prospect"
    reason: str | None = None  # why it forfeited
    signed: bool = False  # the LP signed a conditional commitment: not NAV, cash or margin collateral
    escrow: Decimal = Decimal(0)  # simulated escrow, outside the fund; never posted to any journal
    authorized: Decimal | None = None  # amount both partners consented to admit


def _terms(e: Engine) -> dict[str, Any]:
    terms: dict[str, Any] = e.tape.raw["prospect"]
    return terms


def forfeit_prospect(e: Engine, reason: str) -> None:
    p = e.prospect
    if p is None or p.stage in CLOSED:
        return
    p.stage, p.reason, p.escrow, p.authorized = "forfeited", reason, Decimal(0), None
    e._notice("The prospective LP's offer has lapsed; any escrow returns to it and the fund is unchanged.",
              code="prospect_forfeited", reason=reason)


def prospect_assignment_refusal(e: Engine, topic: str) -> str | None:
    """Why this pipeline assignment cannot be made now; None for an allowed or unrelated topic."""
    p = e.prospect
    if p is None:
        return None
    t = _terms(e)
    if topic not in (t["qualification_topic"], t["diligence_topic"]):
        return None
    if p.stage in CLOSED or e.ev.day >= t["condition_day"]:
        return "the prospect's diligence window has closed"
    if any(r["topic"] == topic for r in e.research_used):
        return "this prospect assignment is already done"
    if topic == t["diligence_topic"] and p.stage != "qualified":
        return "the prospect must be qualified before diligence"
    return None


def prospect_reveal(e: Engine, topic: str) -> None:
    p = e.prospect
    if p is None:
        return
    t = _terms(e)
    if topic == t["qualification_topic"] and p.stage == "prospect":
        p.stage = "qualified"
    elif topic == t["diligence_topic"] and p.stage == "qualified":
        p.stage = "diligence"


def prospect_conditions(e: Engine) -> None:
    """Condition-day close: diligence and a certified report earn a signed commitment; anything else forfeits."""
    p = e.prospect
    if p is None or p.stage in CLOSED or e.ev.day != _terms(e)["condition_day"]:
        return
    if p.stage != "diligence":
        forfeit_prospect(e, "diligence_incomplete")
    elif e.control_report()["status"] != "checked":
        forfeit_prospect(e, "report_not_certified")
    else:
        p.stage, p.signed = "committed", True
        t = _terms(e)
        e._notice(f"{t['series_id']} signed a conditional commitment of up to ${D(t['max_amount']):,.0f} for the day "
                  f"{t['dealing_day']} dealing close. It is not NAV, cash or margin collateral.",
                  code="prospect_committed", series=t["series_id"])


def prospect_funding(e: Engine) -> None:
    p = e.prospect
    if p is None or p.stage != "committed" or e.ev.day != _terms(e)["funding_day"]:
        return
    t = _terms(e)
    p.stage, p.escrow = "eligible", D(t["max_amount"])
    e._notice(f"{t['series_id']} funded ${p.escrow:,.0f} into escrow outside the fund. Both partners must consent "
              f"to an amount before the day {t['dealing_day']} dealing close, or decline.",
              code="prospect_escrow", series=t["series_id"], escrow=str(p.escrow))


def admission_terms(e: Engine, amount: Any) -> dict[str, Any]:
    """What a joint admission consent binds to; recomputed at signing, so a changed fact invalidates it."""
    p = e.prospect
    if p is None:
        raise Refused("no prospective LP in this scenario")
    if not e.at_barrier() or e.finished():
        raise Refused("admission is proposed at a decision barrier")
    if p.stage != "eligible":
        raise Refused("no funded, eligible subscription awaits admission")
    if p.authorized is not None:
        raise Refused("both partners already consented to this admission")
    try:
        value = D(amount)
    except (TypeError, ValueError, InvalidOperation) as ex:
        raise Refused("subscription amount must be a decimal string") from ex
    t = _terms(e)
    with localcontext(CTX):
        if not 0 < value <= p.escrow or value % D(t["cap_step"]) != 0:
            raise Refused(f"amount must be a positive multiple of ${D(t['cap_step']):,.0f}, at most the "
                          f"${p.escrow:,.0f} in escrow")
        breaches = subscription_breaches(e.pos, e.marks, e.nav(), value, e._mandate_rules())
    if breaches:
        raise Refused("capacity: " + "; ".join(b.detail for b in breaches))
    return {"series": t["series_id"], "amount": f"{value:f}", "deal_day": t["dealing_day"],
            "issue_price": str(ISSUE_PRICE), "hwm": str(ISSUE_PRICE)}


def authorize_admission(e: Engine, terms: dict[str, Any]) -> None:
    assert e.prospect is not None
    e.prospect.authorized = D(terms["amount"])
    e.administrator.consent(terms["series"], e.prospect.authorized)
    e._notice(f"Both partners consented to admit ${e.prospect.authorized:,.0f} at the day {terms['deal_day']} dealing "
              "close, subject to certification and post-flow checks.", code="prospect_consent",
              series=terms["series"], amount=terms["amount"])


def decline_prospect(e: Engine) -> None:
    p = e.prospect
    if p is None:
        raise Refused("no prospective LP in this scenario")
    if not e.at_barrier() or e.finished():
        raise Refused("a prospect is declined at a decision barrier")
    if p.stage in CLOSED:
        raise Refused("the prospect's pipeline is already closed")
    if p.authorized is not None:
        raise Refused("both partners consented to this admission; it can no longer be declined")
    p.stage, p.escrow, p.authorized = "declined", Decimal(0), None
    e._notice("The fund declined the prospective LP; any escrow returns to it and the fund is unchanged.",
              code="prospect_declined")


def admission_due(e: Engine) -> bool:
    """A consented admission tonight needs a certificate even when no redemption is due."""
    p = e.prospect
    return p is not None and p.authorized is not None and e.ev.day == _terms(e)["dealing_day"]


def deal_subscription(e: Engine, *, certified: bool) -> None:
    """Dealing close: admit a funded, consented subscription after redemptions, or lapse it. Unused escrow returns."""
    p = e.prospect
    if p is None or p.stage in CLOSED or e.ev.day != _terms(e)["dealing_day"]:
        return
    if p.authorized is None:
        return forfeit_prospect(e, "no_consent")
    if not certified:
        return forfeit_prospect(e, "dealing_blocked")
    amount = p.authorized
    e._require(amount <= p.escrow, "subscription_escrow", "admission exceeds the funded escrow")
    if subscription_breaches(e.pos, e.marks, e.nav(), amount, e._mandate_rules()):
        return forfeit_prospect(e, "capacity")
    sid = _terms(e)["series_id"]
    with localcontext(CTX):
        units = amount / ISSUE_PRICE
    e.admit_series(sid, amount, units, ISSUE_PRICE)
    p.stage, p.escrow = "admitted", Decimal(0)
    e._notice(f"Admitted {sid}: ${amount:,.0f} received, {units:,} units issued at 100 with a high-water mark of 100.",
              code="prospect_admitted", series=sid, amount=str(amount), units=str(units))


def prospect_view(e: Engine, role: str) -> dict[str, Any]:
    """Terms reach a seat only once it holds the revealed evidence or the LP has signed; escrow is outside the fund."""
    p = e.prospect
    assert p is not None
    t = _terms(e)
    known = p.signed or any(n["code"] == "research_reveal" and n["refs"].get("topic") == t["qualification_topic"]
                            for n in e.visible_notices(role))
    stage = p.stage if known or p.stage in ("forfeited", "declined") else "prospect"
    return {"stage": stage, "reason": p.reason, "escrow": str(p.escrow),
            "authorized": None if p.authorized is None else str(p.authorized),
            "series_id": t["series_id"] if known else None, "max_amount": t["max_amount"] if known else None,
            "cap_step": t["cap_step"] if known else None, "dealing_day": t["dealing_day"] if known else None}
