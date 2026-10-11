"""LP confidence components, bands, concern recovery and notice requests (GAME_SYSTEMS §4)."""

from decimal import Decimal as D

import pytest

from fundforge.lp import LAUNCH, POLICY_VERSION, ChapterFacts, State, band, chapter_close, redemption_request

SEED, PATIENT, TACTICAL = LAUNCH["seed"], LAUNCH["patient"], LAUNCH["tactical"]


@pytest.mark.parametrize(("c", "expected"), [
    (D(100), "strong"), (D(70), "strong"), (D("69.999"), "stable"), (D(55), "stable"),
    (D("54.99"), "concerned"), (D(40), "concerned"), (D("39.9999"), "withdrawal_risk"), (D(0), "withdrawal_risk")])
def test_bands_are_half_open_without_gaps(c, expected):
    assert band(c) == expected


def test_band_rejects_out_of_range():
    with pytest.raises(ValueError):
        band(D("100.01"))


def test_components_follow_the_rulebook():
    # Tactical misses its 0.60pp target by 1.1pp: 2 x -1.1 = -2.2; one avoidable breach -6; certified +1.
    s, comp = chapter_close(TACTICAL, State(D(65)), ChapterFacts(D("-0.5"), avoidable_breaches=1))
    assert D(comp["performance"]) == D("-2.2") and D(comp["breaches"]) == D("-6") and D(comp["report"]) == D("1")
    assert s.confidence == D("57.8") and comp["band"] == "stable" and comp["policy_version"] == POLICY_VERSION
    assert s.concern_ceiling == D(65)


def test_performance_is_capped_and_confidence_clamped():
    up, comp = chapter_close(PATIENT, State(D(99)), ChapterFacts(D(50)))
    assert D(comp["performance"]) == D("6") and up.confidence == D(100) and D(comp["clamp"]) == D("-6")
    down, comp = chapter_close(SEED, State(D(10)), ChapterFacts(D(-50), report_certified=False,
                                                                gate_deferred=True, overdue_payments=1))
    assert D(comp["performance"]) == D("-6") and D(comp["report"]) == D("-5") and D(comp["gate"]) == D("-10")
    assert D(comp["overdue"]) == D("-15") and down.confidence == D(0) and D(comp["clamp"]) == D("26")


def test_meeting_recovers_only_after_a_concern_up_to_its_ceiling_once_per_evidence():
    flat = ChapterFacts(D("0.35"), report_certified=True)  # Seed on target: perf 0, report +1
    # No documented concern yet: a meeting does nothing.
    s, comp = chapter_close(SEED, State(D(72)), ChapterFacts(D("0.35"), meeting_evidence="ev1"))
    assert D(comp["meeting"]) == D("0") and s.used_evidence == frozenset()
    # A missing report opens a concern at 72 -> 67.
    s, _ = chapter_close(SEED, State(D(72)), ChapterFacts(D("0.35"), report_certified=False))
    assert s.confidence == D(67) and s.concern_ceiling == D(72)
    # New verified evidence recovers at most 3 on top of the chapter's other components.
    s, comp = chapter_close(SEED, s, ChapterFacts(D("0.35"), meeting_evidence="ev1"))
    assert D(comp["meeting"]) == D("3") and s.confidence == D(71) and s.concern_ceiling == D(72)
    # Repeating the same evidence is meeting spam: nothing.
    s, comp = chapter_close(SEED, s, ChapterFacts(D("0.35"), report_certified=False, meeting_evidence="ev1"))
    assert D(comp["meeting"]) == D("0") and s.confidence == D(66)
    # Recovery never exceeds the confidence immediately before the concern; reaching it closes the concern.
    s, comp = chapter_close(SEED, s, ChapterFacts(D("2.35"), meeting_evidence="ev2"))
    assert D(comp["performance"]) == D("4") and D(comp["meeting"]) == D("1") and s.confidence == D(72)
    assert s.concern_ceiling is None
    s2, _ = chapter_close(SEED, s, flat)
    assert s2.concern_ceiling is None


def test_notice_requests_by_band_lock_and_external_need():
    held = D("10000.12345678")
    assert redemption_request(TACTICAL, D("39.99"), held, 15) == D("5000.06172839")  # 50%, rounded down
    assert redemption_request(TACTICAL, D(40), held, 15) == D("2500.03086419")  # 25%
    assert redemption_request(TACTICAL, D(55), held, 15) == 0
    # Tactical's contractual 10,000-unit need: the larger of need and confidence request, not their sum.
    assert redemption_request(TACTICAL, D(45), held, 15, external_units=D(10000)) == D(10000)
    assert redemption_request(TACTICAL, D(45), D(8000), 15, external_units=D(10000)) == D(8000)  # capped by units
    # Seed has no day-20 redemption; Patient's first eligible notice is day 55.
    assert redemption_request(SEED, D(10), held, 15) == 0
    assert redemption_request(SEED, D(10), held, 35) == D("5000.06172839")
    assert redemption_request(PATIENT, D(10), held, 35) == 0
    assert redemption_request(PATIENT, D(10), held, 55) == D("5000.06172839")
    with pytest.raises(ValueError):
        redemption_request(SEED, D(10), held, 20)


def test_negative_incident_counts_are_rejected():
    with pytest.raises(ValueError):
        chapter_close(SEED, State(D(72)), ChapterFacts(D(0), avoidable_breaches=-1))


def test_gate_allocates_one_pro_rata_fraction_and_carries_the_rest():
    from fundforge.lp import allocate_gate
    price = {"seed": D("1.10"), "tactical": D("0.95")}
    req = {"seed": D(1_000_000), "tactical": D(3_000_000)}  # $1.1m + $2.85m = $3.95m wanted
    dealt, carried = allocate_gate(D(10_000_000), req, price, gated=True)  # cap $2m
    frac = D(2_000_000) / D(3_950_000)
    for k in req:
        assert dealt[k] == (req[k] * frac).quantize(D("0.00000001"), rounding="ROUND_DOWN")
        assert dealt[k] + carried[k] == req[k] and carried[k] > 0
    assert sum(dealt[k] * price[k] for k in req) <= D(2_000_000)
    assert D(2_000_000) - sum(dealt[k] * price[k] for k in req) < D("0.0000001")
    # Same fraction for every LP: nobody is preferred.
    assert abs(dealt["seed"] / req["seed"] - dealt["tactical"] / req["tactical"]) < D("1e-14")


def test_no_gate_or_small_requests_deal_everything():
    from fundforge.lp import allocate_gate
    price = {"a": D(1)}
    assert allocate_gate(D(100), {"a": D(50)}, price, gated=False) == ({"a": D(50)}, {"a": D(0)})
    assert allocate_gate(D(100), {"a": D(20)}, price, gated=True) == ({"a": D(20)}, {"a": D(0)})
    assert allocate_gate(D(100), {"a": D(0)}, price, gated=True) == ({"a": D(0)}, {"a": D(0)})
    with pytest.raises(ValueError):
        allocate_gate(D(0), {"a": D(1)}, price, gated=True)
