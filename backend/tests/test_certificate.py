"""NAV certification gate per dealing close (shadow.certify; FUND_ACCOUNTING §5a)."""

from test_broker import advance, correction, session
from test_engine import CASE1, run

from fundforge.debrief import replay
from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.money import D
from fundforge.schemas import Certificate, Debrief, SessionView, TerminalView
from fundforge.shadow import certify
from fundforge.tape import load
from fundforge.terminal import snapshot


def one_series(book_delta="0", journal="123456.79"):
    # 1,000,000 units, net 1,234,567.89, no provision or claims: NAV/unit 1.23456789 strikes to 1.234568.
    book = {"cash": D("1234567.89") + D(book_delta), "capital:A": D("-1234567.89")}
    return certify("2026-01-26", 20, D("1234567.89"), {"redemption_payable": D(0)},
                   {"A": (D(1000000), D("1234567.89"), D(0))}, book, [], [], [("A", D(100000), D(journal))])


def test_hand_computed_strike_payable_and_residual():
    c = one_series()
    assert c.status == "certified" and c.reasons == () and c.difference == 0
    assert c.strikes[0].nav_per_unit == D("1.234568")
    line = c.redemptions[0]
    # 100,000 x 1.234568 = 123,456.80; journal pro-rata 1,234,567.89 / 10 = 123,456.789 -> 123,456.79.
    assert (line.payable, line.journal_payable, line.residual) == (D("123456.80"), D("123456.79"), D("-0.01"))
    assert line.residual_bound == D("0.06")  # 100,000 x 0.0000005 + 0.01
    assert one_series(journal="123456.86").status == "certified"  # residual 0.06 is inside the inclusive bound
    assert one_series(journal="123456.87").reasons == ("payable_residual",)


def test_one_cent_tolerance_is_inclusive():
    assert one_series("0.01").status == "certified" and one_series("-0.01").status == "certified"
    assert one_series("0.02").reasons == ("shadow_nav",) and one_series("-0.02").reasons == ("shadow_nav",)


def test_breaks_and_open_statements_map_to_typed_reasons():
    c = certify("2026-01-26", 20, D(100), {}, {"A": (D(1), D(100), D(0))}, {"cash": D(100), "capital:A": D(-100)},
                [{"code": "settlement_missing"}, {"code": "lp_capital"}, {"code": "broker_balance"},
                 {"code": "position"}, {"code": "something_new"}], ["opening-cash"], [("Gone", D(1), D(1))])
    assert c.status == "broken"
    assert c.reasons == ("broker_break", "broker_statement", "lp_claim_mismatch", "settlement_break",
                         "shadow_break")


def test_case1_dealing_close_certificate_is_hand_checked():
    e = run({})  # F1 inaction
    [cert] = e.certificates
    Certificate.model_validate(cert)
    assert (cert["date"], cert["day"], cert["status"], cert["reasons"]) == ("2026-01-30", 20, "certified", [])
    assert cert["independent_nav"] == cert["book_nav"] == "23107246.94" and D(cert["difference"]) == 0
    strikes = {s["series_id"]: s["nav_per_unit"] for s in cert["strikes"]}
    # 6470029.14/70000 = 92.42898771..., 9242898.79/100000 = 92.4289879, 7394319.01/80000 = 92.428987625
    assert strikes == {"Patient": "92.428988", "Seed": "92.428988", "Tactical": "92.428988"}
    [line] = cert["redemptions"]
    assert (line["units"], line["payable"], line["journal_payable"], D(line["residual"])) == (
        "10000", "924289.88", "924289.88", 0)
    assert e.administrator.claims[0].payable == D("924289.88")


def phantom_expense(amount):
    """At the day-20 dealing close, post a balanced but unsupported expense accrual before dealing."""
    e = Engine(load(CASE1))
    e.advance()
    deal = e._deal

    def wrong():
        if e.ev.day == 20:
            e._post("Unsupported expense accrual", ("common_pnl", D(amount)), ("accrued_expense", -D(amount)))
            e.reconcile()  # trial balance, positions and series capital all still agree
            e.status_at_deal = e.control_report()["status"]  # type: ignore[attr-defined]
        deal()

    e._deal = wrong  # type: ignore[method-assign]
    units = sum(s.units for s in e.series)
    while not e.certificates and not e.finished():
        e.advance()
    return e, units


def test_balanced_but_economically_wrong_posting_fails_certification_and_blocks_dealing():
    e, units = phantom_expense("100.00")
    assert e.status_at_deal == "break"  # the expense-accrual control flags it before dealing
    [cert] = e.certificates
    assert cert["status"] == "broken" and cert["reasons"] == ["shadow_break", "shadow_nav"]
    assert cert["difference"] == "-100.00"
    assert sum(s.units for s in e.series) == units and not e.administrator.claims
    assert e.bal("redemption_payable") == 0
    incident = e.incident_events[-1]
    assert incident["code"] == "dealing_blocked" and incident["refs"]["reasons"] == "shadow_break,shadow_nav"
    assert incident["amounts"] == {"nav_difference": "-100.00"}


def test_unsupported_expense_accrual_is_flagged_between_dealing_closes():
    e = Engine(load(CASE1))
    e.advance()
    while e.ev.day < 10:
        e.advance()
    assert not e.certificates and not [b for b in e.control_report()["breaks"] if b["code"] == "expense_accrual"]
    e._post("Unsupported expense accrual", ("common_pnl", D("250.00")), ("accrued_expense", D("-250.00")))
    e.reconcile()  # balanced: trial balance, positions and series capital still agree
    report = e.control_report()
    assert report["status"] == "break" and not e.certificates
    assert [b for b in report["breaks"] if b["code"] == "expense_accrual"] == [
        {"code": "expense_accrual", "subject": "accrued_expense", "actual": "-250.00", "expected": "0.00"}]
    assert e.bal("accrued_expense") == D("-250.00")  # reported, never repaired


def test_golden_paths_carry_no_expense_accrual_break_at_any_barrier():
    from test_golden import PATHS
    for name, script in PATHS.items():
        e = Engine(load(CASE1))
        e.advance()
        while not e.finished():
            nxt = e.next_event()
            if e.at_barrier():
                assert not [b for b in e.control_report()["breaks"] if b["code"] == "expense_accrual"], name
            if (nxt.day, nxt.phase) in script:
                script[(nxt.day, nxt.phase)](e)
            e.advance()
        assert not [b for b in e.control_report()["breaks"] if b["code"] == "expense_accrual"], name


def test_one_cent_engine_boundary():
    e, units = phantom_expense("0.01")
    assert e.certificates[-1]["status"] == "certified" and sum(s.units for s in e.series) < units
    e, units = phantom_expense("0.02")
    assert e.certificates[-1]["reasons"] == ["shadow_break", "shadow_nav"] and sum(s.units for s in e.series) == units


def test_open_broker_statement_break_blocks_certification_and_dealing():
    s = session()  # case1-controls overlay; review omitted
    advance(s, 21)
    [cert] = s.e.certificates
    assert cert["status"] == "broken" and cert["reasons"] == ["broker_statement"]
    assert D(cert["difference"]) == 0  # the books are right; the broker's statement is not yet resolved
    assert s.e.bal("redemption_payable") == 0 and not s.e.administrator.claims
    assert s.e.incident_events[-1]["refs"]["reasons"] == "broker_statement"
    view = s.view("ben")
    assert view["certification"] == "broken"
    SessionView.model_validate(view)


def test_resolved_statement_certifies_and_replays_identically():
    s = session()
    advance(s, 13)
    s.handle("ben", "review", correction(s))
    assert snapshot(s.e)["risk"]["certification"] == {"status": "pending", "certificates": []}  # never future
    advance(s, 20)
    assert s.e.certificates == []  # day-20 barrier: the dealing close has not been processed yet
    advance(s, 21)
    assert [c["status"] for c in s.e.certificates] == ["certified"]
    term = {**snapshot(s.e, "mp"), "version": s.version}
    TerminalView.model_validate(term)
    assert term["risk"]["certification"]["certificates"] == s.e.certificates
    restored = Session(Engine(s.e.tape), dict(s.partners))
    restored.e.advance()
    for row in s.log:
        restored.handle(s.partners[row["role"]], row["key"], row["command"])
    assert restored.e.certificates == s.e.certificates
    debrief = replay(s)
    assert debrief["certificates"] == s.e.certificates
    Debrief.model_validate(debrief)
