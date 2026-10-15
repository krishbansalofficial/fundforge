"""LP preference layer: components, herding after a gate, statements (ROADMAP P4 "LP agents")."""

import copy
import dataclasses
from decimal import Decimal as D

import pytest

from fundforge import lp
from fundforge.lp import PREFERENCE_VERSION, PREFERENCES, PreferenceFacts, confidence, series_statements, statements

TACTICAL = PREFERENCES["tactical"]
SEED = PREFERENCES["seed"]


def facts(**kw):
    base = dict(start=D(60), drawdown_pp=D("10.5"), response_lag_days=6, partner_contacts=2,
                gate_event=True, peer_request_share=D("0.5"))
    base.update(kw)
    return PreferenceFacts(**base)


def test_components_match_the_hand_worked_tactical_example():
    # Tactical: drawdown tolerance 8 at 0.3/pp -> (10.5-8)*0.3 = -0.75; lag tolerance 2 at 1.5/day
    # -> (6-2)*1.5 = -6.00; 2 contacts at 0.5 -> +1.00; gate with peer share 0.5 at 10 -> -5.00.
    # End = 60 - 0.75 - 6.00 + 1.00 - 5.00 = 49.25, which is the concerned band.
    c = confidence(TACTICAL, facts())
    assert (c.drawdown, c.response_lag, c.contact, c.herding) == (D("-0.75"), D("-6.00"), D("1.00"), D("-5.00"))
    assert c.end == D("49.25") and c.band == "concerned" and c.policy_version == PREFERENCE_VERSION


def test_herding_is_absent_before_the_gate_and_present_after_it():
    before = confidence(TACTICAL, facts(gate_event=False, peer_request_share=D(1)))
    assert before.herding == 0 and "herding" not in statements(before)
    after = confidence(TACTICAL, facts(gate_event=True, peer_request_share=D(1)))
    assert after.herding == D("-10.00") and "herding" in statements(after)
    none_asked = confidence(TACTICAL, facts(gate_event=True, peer_request_share=D(0)))
    assert none_asked.herding == 0


def test_terms_are_zero_when_within_tolerance_and_penalties_are_floored():
    calm = confidence(SEED, facts(start=D(72), drawdown_pp=D(2), response_lag_days=None, partner_contacts=0,
                                  gate_event=False))
    assert (calm.drawdown, calm.response_lag, calm.contact, calm.herding) == (0, 0, 0, 0)
    assert calm.end == D(72)
    crash = confidence(SEED, facts(start=D(80), drawdown_pp=D(500), response_lag_days=900))
    assert crash.drawdown == D(-10) and crash.response_lag == D(-10)
    assert crash.end == D(80) + D(-10) + D(-10) + crash.contact + crash.herding


def test_rounding_is_half_up_to_the_cent():
    # Seed drawdown weight is 1.0, tolerance 5: excess 1.005 must round half-up to 1.01, not 1.00.
    c = confidence(SEED, facts(start=D(50), drawdown_pp=D("6.005"), response_lag_days=None, partner_contacts=0,
                               gate_event=False))
    assert c.drawdown == D("-1.01")


def test_end_is_clamped_to_zero_to_hundred():
    assert confidence(SEED, facts(start=D(100), drawdown_pp=D(0), response_lag_days=None, partner_contacts=2,
                                  gate_event=False)).end == D(100)


def test_statements_are_derived_from_components_and_deterministic_across_runs():
    f = {"seed": facts(start=D(72), gate_event=True, peer_request_share=D("0.4")),
         "tactical": facts(),
         "patient": facts(start=D(80), drawdown_pp=D(0), response_lag_days=None, partner_contacts=0,
                          gate_event=False)}
    p = {k: PREFERENCES[k] for k in f}
    first = series_statements({k: confidence(p[k], f[k]) for k in f})
    second = series_statements({k: confidence(p[k], f[k]) for k in reversed(list(f))})
    assert first == second and list(first) == ["patient", "seed", "tactical"]
    assert first["tactical"] == ("band:concerned", "slow_response", "herding")
    assert first["patient"] == ("band:strong", "no_partner_contact")
    assert statements(confidence(TACTICAL, facts())) == statements(confidence(TACTICAL, facts()))


def test_confidence_does_not_mutate_inputs():
    f = facts()
    policy_before = copy.deepcopy(TACTICAL)
    facts_before = copy.deepcopy(f)
    confidence(TACTICAL, f)
    assert f == facts_before and policy_before == TACTICAL
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.start = D(1)  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        TACTICAL.herd_weight = D(0)  # type: ignore[misc]


@pytest.mark.parametrize("bad", [
    dict(start=D(101)), dict(start=D(-1)), dict(drawdown_pp=D(-1)), dict(partner_contacts=-1),
    dict(response_lag_days=-1), dict(peer_request_share=D("1.01")),
])
def test_invalid_facts_are_rejected(bad):
    with pytest.raises(ValueError):
        confidence(TACTICAL, facts(**bad))


def test_unknown_or_forged_policy_is_rejected():
    forged = dataclasses.replace(TACTICAL, herd_weight=D(0))
    with pytest.raises(ValueError):
        confidence(forged, facts())


def test_preference_layer_does_not_touch_the_section_4_rule():
    # chapter_close is the GAME_SYSTEMS §4 path; the preference layer must leave it as it was.
    s, comp = lp.chapter_close(lp.LAUNCH["tactical"], lp.State(D(65)), lp.ChapterFacts(D("-0.5"), avoidable_breaches=1))
    assert s.confidence == D("57.8") and comp["policy_version"] == lp.POLICY_VERSION
