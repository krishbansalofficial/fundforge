"""Deterministic LP confidence and redemption requests (GAME_SYSTEMS §4).

Confidence is an internal Decimal 0-100 balance state, recomputed at each chapter close
from typed facts. Every component is returned with the policy version so the debrief can
show exactly why an LP moved. These are frozen house balance rules, not a model of real
investors; no LLM or free text awards any part of it.

Generated-market rooms (``case1-generated``) add house preference terms between chapter closes
(``review``: drawdown, response lag, partner contact) and herding after a gate; authored scenarios
never run them. The engine adapter is ``investors.py``.

Pure domain: no engine, journal or I/O imports.
"""

from dataclasses import dataclass, field, replace
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal, localcontext

from .money import CTX

POLICY_VERSION = "lp-confidence-2026.10.2"
UNITS = Decimal("0.00000001")  # series units carry 8dp
ZERO, HUNDRED = Decimal(0), Decimal(100)
PERF_CAP = Decimal(6)
BREACH_COST = Decimal(6)
REPORT_BONUS, REPORT_MISSING = Decimal(1), Decimal(5)
MEETING_CAP = Decimal(3)
OVERDUE_COST = Decimal(15)
NOTICE_CUTOFFS = (15, 35, 55)
DEALING_LAG = 5  # business days from a notice cutoff to its dealing close (15 -> 20)
REVIEW_DAYS = (13, 15)  # generated rooms: interim reviews at these certified closes, before the day-15 cutoff
DRAWDOWN_CAP = Decimal(8)
PP = Decimal("0.01")


@dataclass(frozen=True)
class Profile:
    lp_id: str
    initial: Decimal
    target_pp: Decimal  # chapter net return target in percentage points
    gate_penalty: Decimal
    first_eligible_cutoff: int  # first notice cutoff at which this LP may request anything (lock-up)
    # House preference terms for interim reviews (balance hypotheses, not investor-behaviour claims):
    drawdown_cost: Decimal = ZERO  # per percentage point below the LP's peak net value per unit
    lag_cost: Decimal = ZERO  # per material alert still unresolved at the review
    contact_bonus: Decimal = ZERO  # partner contact offsets at most this much of the review's losses


# GAME_SYSTEMS §4 launch roster. Seed has no day-20 redemption (first notice day 35); Patient's first
# dealing is day 60, so its first notice is the day-55 cutoff. Preferences: Seed values access to
# partners, Patient lower drawdown, Tactical fast response.
LAUNCH = {
    "seed": Profile("seed", Decimal(72), Decimal("0.35"), Decimal(10), 35, Decimal(1), Decimal(1), Decimal(3)),
    "patient": Profile("patient", Decimal(80), Decimal("0.20"), Decimal(8), 55, Decimal(3), Decimal(1), Decimal(1)),
    "tactical": Profile("tactical", Decimal(65), Decimal("0.60"), Decimal(15), 15, Decimal(2), Decimal(3),
                        Decimal(1)),
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
    peer_gated: bool = False  # a gate deferred another LP's units this window (herding)


@dataclass(frozen=True)
class ReviewFacts:
    """Interim review facts (generated rooms), read from the certified close, never from prose."""

    drawdown_pp: Decimal  # this LP's net value per unit below its peak since the window opened, pp, 2dp
    open_alerts: int = 0  # material alerts (margin call, open recall) still unresolved at the review
    contacted: bool = False  # a partner contacted this LP since the previous review


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


def _moved(s: State, new: Decimal, used: frozenset[str]) -> State:
    ceiling = s.concern_ceiling
    if new < s.confidence and ceiling is None:
        ceiling = s.confidence  # a fall documents a concern; recovery may never exceed where it started
    elif ceiling is not None and new >= ceiling:
        ceiling = None
    return replace(s, confidence=new, concern_ceiling=ceiling, used_evidence=used)


def chapter_close(p: Profile, s: State, f: ChapterFacts) -> tuple[State, dict[str, str]]:
    """Apply one chapter close; returns the new state and every component for audit."""
    if f.avoidable_breaches < 0 or f.overdue_payments < 0:
        raise ValueError("incident counts cannot be negative")
    with localcontext(CTX):
        perf = max(-PERF_CAP, min(PERF_CAP, 2 * (f.net_return_pp - p.target_pp)))
        breach = -BREACH_COST * f.avoidable_breaches
        report = REPORT_BONUS if f.report_certified else -REPORT_MISSING
        gate = -p.gate_penalty if f.gate_deferred else ZERO
        herding = -p.gate_penalty / 2 if f.peer_gated and not f.gate_deferred else ZERO
        overdue = -OVERDUE_COST * f.overdue_payments
        before_meeting = s.confidence + perf + breach + report + gate + herding + overdue
        meeting, used = ZERO, s.used_evidence
        if (f.meeting_evidence is not None and s.concern_ceiling is not None
                and f.meeting_evidence not in s.used_evidence):
            meeting = max(ZERO, min(MEETING_CAP, s.concern_ceiling - before_meeting))
            if meeting:
                used = used | {f.meeting_evidence}
        unclamped = before_meeting + meeting
        new = max(ZERO, min(HUNDRED, unclamped))
    components = {"policy_version": POLICY_VERSION, "start": str(s.confidence), "performance": str(perf),
                  "breaches": str(breach), "report": str(report), "meeting": str(meeting), "gate": str(gate),
                  "herding": str(herding), "overdue": str(overdue), "clamp": str(new - unclamped), "end": str(new),
                  "band": band(new)}
    return _moved(s, new, used), components


def drawdown_pp(peak: Decimal, current: Decimal) -> Decimal:
    """Percentage points below the peak, 2dp HALF_EVEN; zero at or above the peak."""
    if peak <= 0:
        raise ValueError("peak value per unit must be positive")
    with localcontext(CTX):
        return max(ZERO, (1 - current / peak) * 100).quantize(PP, rounding=ROUND_HALF_EVEN)


def review(p: Profile, s: State, f: ReviewFacts) -> tuple[State, dict[str, str]]:
    """Interim review between chapter closes (generated rooms): preference terms only.

    Contact never raises confidence on its own: it offsets at most ``contact_bonus`` of this
    review's drawdown and lag losses, so repeated calls in calm markets earn nothing.
    """
    if f.drawdown_pp < 0 or f.open_alerts < 0:
        raise ValueError("drawdown and alert counts cannot be negative")
    with localcontext(CTX):
        dd = ZERO - min(DRAWDOWN_CAP, p.drawdown_cost * f.drawdown_pp)  # ZERO - x never prints "-0"
        lag = ZERO - p.lag_cost * f.open_alerts
        contact = min(p.contact_bonus, -(dd + lag)) if f.contacted else ZERO
        unclamped = s.confidence + dd + lag + contact
        new = max(ZERO, min(HUNDRED, unclamped))
    components = {"policy_version": POLICY_VERSION, "start": str(s.confidence), "drawdown": str(dd),
                  "response_lag": str(lag), "contact": str(contact), "clamp": str(new - unclamped),
                  "end": str(new), "band": band(new)}
    return _moved(s, new, s.used_evidence), components


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


@dataclass
class Book:
    """LP-agent state an engine carries in generated rooms. Holds only past checkpoints' results."""

    profiles: dict[str, Profile]  # by series id
    states: dict[str, State]
    peaks: dict[str, Decimal]  # highest net value per unit seen at a close since the window opened
    start_value: dict[str, Decimal]  # net value per unit when the window opened (chapter return base)
    start_day: int
    contacts: set[str] = field(default_factory=set)  # contacted since the previous review
    requests: dict[str, Decimal] = field(default_factory=dict)  # pending units for ``deal_day``
    deal_day: int | None = None
    carried: dict[str, Decimal] = field(default_factory=dict)  # gated units rolled past their dealing window
    gate_day: int | None = None  # dealing day both partners elected a gate for
    log: list[dict[str, str]] = field(default_factory=list)  # every checkpoint's components, for the debrief
