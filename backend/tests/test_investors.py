"""LP chapter facts read from real engine paths, then fed through the LP confidence rules."""

from decimal import Decimal as D
from pathlib import Path

from test_engine import S1, run

from fundforge import store
from fundforge.engine import Engine
from fundforge.investors import chapter_facts
from fundforge.lp import LAUNCH, State, chapter_close
from fundforge.tape import load

CASE1 = Path(__file__).parents[2] / "fixtures" / "case1.json"
START = {s.series_id: s.net / s.units for s in Engine(load(CASE1)).series}


def test_facts_from_a_winning_path():
    e = run(S1)
    facts = chapter_facts(e, START, 12)
    assert set(facts) == {"Seed", "Patient", "Tactical"}
    for s in e.series:
        expected = (s.net / s.units / START[s.series_id] - 1) * 100
        assert facts[s.series_id].net_return_pp == expected
        assert facts[s.series_id].report_certified and facts[s.series_id].overdue_payments == 0
    _, comp = chapter_close(LAUNCH["seed"], State(LAUNCH["seed"].initial), facts["Seed"])
    assert D(comp["report"]) == 1 and D(comp["overdue"]) == 0 and D(comp["performance"]) == -6  # capped loss


def test_unpaid_redemption_counts_only_for_the_redeeming_series():
    e = Engine(store._tape("case1-settlement", "base"))
    e.advance()
    while not e.finished():
        nxt = e.next_event()
        if (nxt.day, nxt.phase) == (12, "EXEC_A"):
            e.submit_order("buy", "ALTO", "BUY", 5000)
        if (nxt.day, nxt.phase) == (13, "EXEC_A"):
            e.submit_order("sell", "COVE", "SELL", 8000)
        e.advance()
    facts = chapter_facts(e, START, 12)
    assert facts["Tactical"].overdue_payments == 1  # day-21 unpaid redemption
    assert facts["Seed"].overdue_payments == facts["Patient"].overdue_payments == 0
    _, comp = chapter_close(LAUNCH["tactical"], State(LAUNCH["tactical"].initial), facts["Tactical"])
    assert D(comp["overdue"]) == -15
