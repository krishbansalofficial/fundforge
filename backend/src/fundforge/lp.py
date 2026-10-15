"""Deterministic LP confidence and redemption requests (GAME_SYSTEMS §4).

Confidence is an internal Decimal 0-100 balance state, recomputed at each chapter close
from typed facts. Every component is returned with the policy version so the debrief can
show exactly why an LP moved. These are frozen house balance rules, not a model of real
investors; no LLM or free text awards any part of it.

Pure domain: no engine, journal or I/O imports. Not yet wired into a scenario.
"""

from dataclasses import dataclass, replace
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, localcontext

from .money import CTX

POLICY_VERSION = "lp-confidence-2026.10.1"
UNITS = Decimal("0.00000001")  # series units carry 8dp
ZERO, HUNDRED = Decimal(0), Decimal(100)
PERF_CAP = Decimal(6)
BREACH_COST = Decimal(6)
REPORT_BONUS, REPORT_MISSING = Decimal(1), Decimal(5)
MEETING_CAP = Decimal(3)
OVERDUE_COST = Decimal(15)
NOTICE_CUTOFFS = (15, 35, 55)


@dataclass(frozen=True)
class Profile:
    lp_id: str
    initial: Decimal
    target_pp: Decimal  # chapter net return target in percentage points
    gate_penalty: Decimal
    first_eligible_cutoff: int  # first notice cutoff at which this LP may request anything (lock-up)


# GAME_SYSTEMS §4 launch roster. Seed has no day-20 redemption (first notice day 35); Patient's first
# dealing is day 60, so its first notice is the day-55 cutoff.
LAUNCH = {
    "seed": Profile("seed", Decimal(72), Decimal("0.35"), Decimal(10), 35),
    "patient": Profile("patient", Decimal(80), Decimal("0.20"), Decimal(8), 55),
    "tactical": Profile("tactical", Decimal(65), Decimal("0.60"), Decimal(15), 15),
}


@dataclass(frozen=True)
class State:
    confidence: Decimal
    concern_ceiling: Decimal | None = None  # confidence immediately before the open documented concern
    used_evidence: frozenset[str] = frozenset()  # meeting evidence/commitment identities already credited


@dataclass(frozen=True)
class ChapterFacts:
    """Typed chapter-close facts; the engine derives them from the books, never from prose."""

    net_return_pp: Decimal  # this LP's chapter net return, percentage points
    avoidable_breaches: int = 0  # avoidable active breaches or passive breaches uncured after the opportunity
    report_certified: bool = True  # False when the report is missing or did not reconcile
    meeting_evidence: str | None = None  # identity of new verified information / fulfilled commitment
    gate_deferred: bool = False  # a gate actually deferred this LP's eligible units this window
    overdue_payments: int = 0  # contracted payment incidents newly overdue this chapter


def band(c: Decimal) -> str:
    """Half-open public bands; fractional values fall in exactly one."""
    if not ZERO <= c <= HUNDRED:
        raise ValueError(f"confidence {c} outside 0-100")
    if c >= 70:
        return "strong"
    if c >= 55:
        return "stable"
    if c >= 40:
        return "concerned"
    return "withdrawal_risk"


def chapter_close(p: Profile, s: State, f: ChapterFacts) -> tuple[State, dict[str, str]]:
    """Apply one chapter close; returns the new state and every component for audit."""
    if f.avoidable_breaches < 0 or f.overdue_payments < 0:
        raise ValueError("incident counts cannot be negative")
    with localcontext(CTX):
        perf = max(-PERF_CAP, min(PERF_CAP, 2 * (f.net_return_pp - p.target_pp)))
        breach = -BREACH_COST * f.avoidable_breaches
        report = REPORT_BONUS if f.report_certified else -REPORT_MISSING
        gate = -p.gate_penalty if f.gate_deferred else ZERO
        overdue = -OVERDUE_COST * f.overdue_payments
        before_meeting = s.confidence + perf + breach + report + gate + overdue
        meeting, used = ZERO, s.used_evidence
        if (f.meeting_evidence is not None and s.concern_ceiling is not None
                and f.meeting_evidence not in s.used_evidence):
            meeting = max(ZERO, min(MEETING_CAP, s.concern_ceiling - before_meeting))
            if meeting:
                used = used | {f.meeting_evidence}
        unclamped = before_meeting + meeting
        new = max(ZERO, min(HUNDRED, unclamped))
    ceiling = s.concern_ceiling
    if new < s.confidence and ceiling is None:
        ceiling = s.confidence  # a fall documents a concern; recovery may never exceed where it started
    elif ceiling is not None and new >= ceiling:
        ceiling = None
    components = {"policy_version": POLICY_VERSION, "start": str(s.confidence), "performance": str(perf),
                  "breaches": str(breach), "report": str(report), "meeting": str(meeting), "gate": str(gate),
                  "overdue": str(overdue), "clamp": str(new - unclamped), "end": str(new), "band": band(new)}
    return replace(s, confidence=new, concern_ceiling=ceiling, used_evidence=used), components


def redemption_request(p: Profile, confidence: Decimal, held_units: Decimal, cutoff_day: int,
                       external_units: Decimal = ZERO) -> Decimal:
    """Units requested at a notice cutoff: the larger of the confidence request and any external need."""
    if cutoff_day not in NOTICE_CUTOFFS:
        raise ValueError(f"day {cutoff_day} is not a notice cutoff")
    if held_units < 0 or external_units < 0:
        raise ValueError("units cannot be negative")
    if cutoff_day < p.first_eligible_cutoff:
        return ZERO  # locked LPs wait for their first eligible cutoff
    fraction = Decimal("0.5") if confidence < 40 else Decimal("0.25") if confidence < 55 else ZERO
    with localcontext(CTX):
        by_confidence = (held_units * fraction).quantize(UNITS, rounding=ROUND_DOWN)
    return min(held_units, max(by_confidence, external_units))


GATE_FRACTION = Decimal("0.20")


def allocate_gate(nav: Decimal, requests: dict[str, Decimal], unit_price: dict[str, Decimal],
                  gated: bool) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """Split each LP's requested units (new plus carried) into dealt and carried-forward units.

    ``nav`` is the fund's pre-flow, post-fee NAV at the window. With a gate elected, the dealt
    value is at most 20% of it, allocated by one common pro-rata fraction of each request's value,
    so no LP is preferred. Units round down to 8dp, so rounding can only leave value undealt.
    Without a gate, or when requests fit under the cap, everything is dealt.
    """
    if nav <= 0:
        raise ValueError("gate needs a positive NAV")
    if any(u < 0 for u in requests.values()) or any(unit_price[k] <= 0 for k in requests):
        raise ValueError("requests must be non-negative with positive unit prices")
    with localcontext(CTX):
        wanted = sum((u * unit_price[k] for k, u in requests.items()), ZERO)
        cap = GATE_FRACTION * nav
        fraction = min(Decimal(1), cap / wanted) if gated and wanted > 0 else Decimal(1)
        dealt = {k: (u * fraction).quantize(UNITS, rounding=ROUND_DOWN) for k, u in requests.items()}
    return dealt, {k: requests[k] - dealt[k] for k in requests}


# ---------------------------------------------------------------------------
# Preference layer (ROADMAP P4 "LP agents"). Additive to the GAME_SYSTEMS §4 rules above; it does
# not change chapter_close, and it is not yet wired into any scenario. Every weight, tolerance and
# threshold below is a DESIGN CHOICE for playtesting, not a measured investor behaviour and not
# authored in the fixtures. Changing any of them requires a new PREFERENCE_VERSION.
# ---------------------------------------------------------------------------

PREFERENCE_VERSION = "lp-preference-2026.10.1-design"
CENT = Decimal("0.01")
TERM_FLOOR = Decimal(-10)  # design choice: no single term can cost more than 10 points in one chapter
CONCERN_TERM = Decimal(-2)  # design choice: a term at or below -2 is named as a statement


@dataclass(frozen=True)
class PreferencePolicy:
    """Per-LP preference weights (design choices, see module note above)."""

    lp_id: str
    drawdown_tolerance_pp: Decimal  # drawdown below this costs nothing
    drawdown_weight: Decimal  # points per percentage point of drawdown beyond tolerance
    lag_tolerance_days: int  # reply lag at or below this costs nothing
    lag_weight: Decimal  # points per day of reply lag beyond tolerance
    contact_weight: Decimal  # points per verified partner contact
    contact_cap: int  # contacts beyond this earn nothing more
    herd_weight: Decimal  # points lost per unit of peer gate-request share, after a gate event


# Design-choice roster. Seed values partner access; Patient values low drawdown and patience;
# Tactical values fast response to a deteriorating thesis.
PREFERENCES: dict[str, PreferencePolicy] = {
    "seed": PreferencePolicy("seed", Decimal(5), Decimal("1.0"), 3, Decimal("0.5"), Decimal("2.0"), 2, Decimal(6)),
    "patient": PreferencePolicy("patient", Decimal(3), Decimal("1.5"), 10, Decimal("0.2"), Decimal("0.5"), 2,
                                Decimal(4)),
    "tactical": PreferencePolicy("tactical", Decimal(8), Decimal("0.3"), 2, Decimal("1.5"), Decimal("0.5"), 3,
                                 Decimal(10)),
}


@dataclass(frozen=True)
class PreferenceFacts:
    """Facts visible to the LP at a chapter close. Only typed, player-visible or authored events belong here."""

    start: Decimal  # confidence before this chapter, 0-100
    drawdown_pp: Decimal  # this LP's chapter maximum drawdown, positive percentage points
    response_lag_days: int | None  # days from the LP's letter to the partner reply; None when no letter
    partner_contacts: int  # verified partner meetings or calls with this LP this chapter
    gate_event: bool  # an authored gate election/notice is in the facts
    peer_request_share: Decimal  # share of other LPs with visible gate-window requests, 0-1


@dataclass(frozen=True)
class PreferenceComponents:
    policy_version: str
    start: Decimal
    drawdown: Decimal
    response_lag: Decimal
    contact: Decimal
    herding: Decimal
    end: Decimal
    band: str


def _term(x: Decimal) -> Decimal:
    """Floor at TERM_FLOOR, then round half-up to 0.01. Applied to each term inside CTX."""
    return max(TERM_FLOOR, x).quantize(CENT, rounding=ROUND_HALF_UP)


def confidence(policy: PreferencePolicy, facts: PreferenceFacts) -> PreferenceComponents:
    """Named Decimal components for one LP at one chapter close. Pure: neither argument is mutated.

    Rounding: each term is computed in CTX precision, floored at -10 for penalties, then rounded
    half-up to 0.01 (``_term``). ``end`` is ``start`` plus the four rounded terms, clamped to 0-100
    and rounded half-up to 0.01. Herding is exactly zero unless ``facts.gate_event`` is true, so a
    peer's request can only weigh on this LP after a visible gate. A missing reply letter costs nothing.
    """
    if PREFERENCES.get(policy.lp_id) != policy:
        raise ValueError("policy must be one of the versioned PREFERENCES")
    band(facts.start)  # raises outside 0-100
    if facts.drawdown_pp < 0 or facts.partner_contacts < 0:
        raise ValueError("drawdown and contacts cannot be negative")
    if facts.response_lag_days is not None and facts.response_lag_days < 0:
        raise ValueError("response lag cannot be negative")
    if not ZERO <= facts.peer_request_share <= 1:
        raise ValueError("peer request share must be within 0-1")
    with localcontext(CTX):
        dd = _term(-policy.drawdown_weight * max(ZERO, facts.drawdown_pp - policy.drawdown_tolerance_pp))
        if facts.response_lag_days is None:
            lag = ZERO
        else:
            late = max(0, facts.response_lag_days - policy.lag_tolerance_days)
            lag = _term(-policy.lag_weight * late)
        contact = _term(policy.contact_weight * min(facts.partner_contacts, policy.contact_cap))
        herd = _term(-policy.herd_weight * facts.peer_request_share) if facts.gate_event else ZERO
        raw = facts.start + dd + lag + contact + herd
        end = max(ZERO, min(HUNDRED, raw)).quantize(CENT, rounding=ROUND_HALF_UP)
    return PreferenceComponents(PREFERENCE_VERSION, facts.start, dd, lag, contact, herd, end, band(end))


# Statement codes are fixed tokens; the UI maps them to the sentences below.
STATEMENT_TEXT: dict[str, str] = {
    "drawdown_concern": "Drawdown is beyond this LP's tolerance.",
    "slow_response": "Replies are running behind this LP's expectation.",
    "no_partner_contact": "No partner contact reached this LP this chapter.",
    "herding": "Other LPs' gate requests are weighing on this LP.",
}


def statements(c: PreferenceComponents) -> tuple[str, ...]:
    """Deterministic statement codes for one series, derived only from its components."""
    out = [f"band:{c.band}"]
    if c.drawdown <= CONCERN_TERM:
        out.append("drawdown_concern")
    if c.response_lag <= CONCERN_TERM:
        out.append("slow_response")
    if c.contact == ZERO:
        out.append("no_partner_contact")
    if c.herding < ZERO:
        out.append("herding")
    return tuple(out)


def series_statements(results: dict[str, PreferenceComponents]) -> dict[str, tuple[str, ...]]:
    """Statements for each series, keyed in sorted order so the output is stable."""
    return {k: statements(results[k]) for k in sorted(results)}
