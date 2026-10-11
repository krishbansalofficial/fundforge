"""Deterministic LP confidence and redemption requests (GAME_SYSTEMS §4).

Confidence is an internal Decimal 0-100 balance state, recomputed at each chapter close
from typed facts. Every component is returned with the policy version so the debrief can
show exactly why an LP moved. These are frozen house balance rules, not a model of real
investors; no LLM or free text awards any part of it.

Pure domain: no engine, journal or I/O imports. Not yet wired into a scenario.
"""

from dataclasses import dataclass, replace
from decimal import ROUND_DOWN, Decimal, localcontext

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
