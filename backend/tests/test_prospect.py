"""Campaign prospect LP, through Session.handle only: pipeline, escrow outside the fund, joint admission at dealing."""

import copy
import json
from decimal import Decimal

import pytest

from fundforge import bot, investors, store
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.schemas import SessionView
from fundforge.tape import TapeError, compile_tape

QUAL = {"type": "visit", "location": "lp", "assignment": "prospect_qualification"}
DILIGENCE = {"type": "visit", "location": "lp", "assignment": "prospect_diligence"}
DAY_20 = "2026-01-30"
# Everything the rules say a commitment or escrow must never touch, as this seat reads it.
MONEY = ("fund", "firm", "series", "positions")


def session(tape=None, bots=frozenset()):
    e = Engine(tape or store._tape("campaign-v1"))
    e.advance()
    return Session(e, {"pm": "ana", "mp": "ben"}, bots)


def step(s):
    """One decision barrier forward."""
    k = str(s.version)
    s.handle("ana", "rdy-a" + k, {"type": "ready"})
    s.handle("ben", "rdy-b" + k, {"type": "ready"})


def to_day(s, day):
    while not s.e.finished() and s.e.ev.day < day:
        step(s)


def diligence_done(s):
    """Two scarce assignments, each revealed at the next day's public mark."""
    s.handle("ben", "qual", QUAL)
    to_day(s, 2)
    s.handle("ben", "dil", DILIGENCE)
    to_day(s, 3)


def admit(s, amount):
    d = s.handle("ben", f"prop{amount}", {"type": "propose_admission", "package_id": f"adm{amount}", "amount": amount})
    return s.handle("ana", f"sign{amount}", {"type": "sign", "package_id": f"adm{amount}", "digest": d["digest"]})


def money(s, user="ben"):
    v = s.view(user)
    return {k: v[k] for k in MONEY} | {"margin_call": s.e.margin_call, "journal": s.e.j.digest()}


def stage(s):
    return s.e.prospect.stage


def admission_entry(s):
    return next(x for x in s.e.j.entries if "Admit subscription" in x.memo)


@pytest.fixture(scope="module")
def baseline():
    """The same campaign with the pipeline untouched: money per barrier, closes and the final digest."""
    s = session()
    rows = {}
    while not s.e.finished():
        rows[s.e.cursor] = money(s)
        step(s)
    return rows, s.e.close_values, s.e.j.digest()


def test_full_path_admits_a_new_series_at_100_with_cash_only_at_the_dealing_close(baseline):
    rows, closes, _ = baseline
    s = session()
    diligence_done(s)
    assert stage(s) == "diligence"
    while s.e.ev.day < 20:
        # Assignments, the signed commitment and funded escrow leave every money figure and the journal unchanged,
        # including the day 16 margin call the commitment might have been expected to cure.
        assert money(s) == rows[s.e.cursor]
        step(s)
    assert any(r["margin_call"] for r in rows.values())
    assert stage(s) == "eligible" and s.e.prospect.escrow == Decimal(5000000)
    assert s.view("ben")["prospect"]["escrow"] == "5000000"
    assert any(n["code"] == "prospect_committed" and n["day"] == 15 for n in s.e.notices)
    assert any(n["code"] == "prospect_escrow" and n["day"] == 19 for n in s.e.notices)
    assert admit(s, "5000000")["status"] == "ELECTED"
    step(s)
    # Consent is still not cash.
    assert s.e.ev.day == 20 and "Anchor" not in {x.series_id for x in s.e.series}
    assert money(s) == rows[s.e.cursor]
    to_day(s, 21)

    entry = admission_entry(s)
    assert entry.entity == "fund" and entry.date == DAY_20
    assert {(p.account, p.amount) for p in entry.postings} == {("cash", Decimal(5000000)),
                                                               ("capital:Anchor", Decimal(-5000000))}
    anchor = next(x for x in s.e.series if x.series_id == "Anchor")
    assert (anchor.units, anchor.hwm) == (Decimal(50000), Decimal(100))
    assert s.e.prospect.escrow == 0 and stage(s) == "admitted"
    # Not company revenue: only ordinary weekend management fee on the new series reaches the company, as a receivable.
    assert not any("Admit" in x.memo for x in s.e.j.entries if x.entity == "firm")
    firm, base = s.view("ben")["firm"], rows[s.e.cursor]["firm"]
    assert firm["cash"] == base["cash"]
    assert 0 < Decimal(firm["fee_receivable"]) - Decimal(base["fee_receivable"]) < Decimal(500)
    # No return from entering at 100, against founders near 94: the day 20 value differs only because the new
    # series shares the weekend financing that close_values already includes.
    assert s.e.close_values[:20] == closes[:20]
    assert abs(s.e.close_values[20] - closes[20]) < Decimal("0.01")
    assert s.e.nav() > Decimal(rows[s.e.cursor]["fund"]["nav"]) + Decimal(4900000)
    assert abs(s.e.unit_nav() - closes[20]) < Decimal("0.1")


def test_series_participates_from_next_period_and_controls_and_certificates_pass():
    s = session()
    diligence_done(s)
    to_day(s, 19)
    admit(s, "5000000")
    to_day(s, 21)
    assert s.e.control_report()["status"] == "checked"
    assert "Anchor" not in {c.series_id for c in s.e.administrator.closes if c.date == DAY_20}
    assert "Anchor" in {c.series_id for c in s.e.administrator.closes if c.date == "2026-01-31"}
    to_day(s, 99)
    e = s.e
    assert e.finished() and e.control_report()["status"] == "checked"
    assert [c["day"] for c in e.certificates] == [20, 30] and all(c["status"] == "certified" for c in e.certificates)
    assert [x["series_id"] for x in e.certificates[0]["strikes"]] == ["Patient", "Seed", "Tactical"]
    assert "Anchor" in [x["series_id"] for x in e.certificates[1]["strikes"]]
    assert "Anchor" not in e.lp.states and "Anchor" not in e.lp.requests  # locked through the campaign
    assert sum(e.j.balances("fund").values()) == 0
    assert SessionView.model_validate(s.view("ana")).prospect.stage == "admitted"
    assert e.outcome()["label"] != "IN_PROGRESS"


def test_replay_gives_the_same_digest():
    s = session()
    diligence_done(s)
    to_day(s, 19)
    admit(s, "3000000")
    to_day(s, 99)
    replay = session()
    for item in s.log:
        replay.handle("ana" if item["role"] == "pm" else "ben", item["key"], item["command"])
    assert replay.e.j.digest() == s.e.j.digest() and replay.e.prospect == s.e.prospect


def test_cap_issues_only_the_consented_amount():
    s = session()
    diligence_done(s)
    to_day(s, 19)
    admit(s, "2000000")
    to_day(s, 21)
    assert next(x for x in s.e.series if x.series_id == "Anchor").units == Decimal(20000)
    assert ("cash", Decimal(2000000)) in {(p.account, p.amount) for p in admission_entry(s).postings}
    assert s.e.prospect.escrow == 0  # the unused $3m returned to the prospect, outside the books


@pytest.mark.parametrize("when", [1, 19])
def test_decline_changes_no_books_at_any_stage(baseline, when):
    s = session()
    if when > 1:
        diligence_done(s)
    to_day(s, when)
    s.handle("ben", "no", {"type": "decline_prospect"})
    assert stage(s) == "declined" and s.e.prospect.escrow == 0
    with pytest.raises(CommandRejected):
        s.handle("ben", "no-again", {"type": "decline_prospect"})
    to_day(s, 99)
    assert s.e.j.digest() == baseline[2]


@pytest.mark.parametrize("qualified", [False, True])
def test_missing_diligence_forfeits_at_the_condition_close(baseline, qualified):
    s = session()
    if qualified:
        s.handle("ben", "qual", QUAL)
    to_day(s, 15)
    assert stage(s) == ("qualified" if qualified else "prospect")
    to_day(s, 16)
    assert stage(s) == "forfeited" and s.e.prospect.reason == "diligence_incomplete" and s.e.prospect.escrow == 0
    to_day(s, 19)
    with pytest.raises(CommandRejected, match="eligible"):
        s.handle("ben", "late", {"type": "propose_admission", "package_id": "late", "amount": "5000000"})
    with pytest.raises(CommandRejected, match="closed"):
        s.handle("ben", "late-dil", DILIGENCE)
    to_day(s, 99)
    assert s.e.j.digest() == baseline[2]


def test_consent_never_given_lapses_at_the_dealing_close(baseline):
    s = session()
    diligence_done(s)
    to_day(s, 21)
    assert stage(s) == "forfeited" and s.e.prospect.reason == "no_consent" and s.e.prospect.escrow == 0
    to_day(s, 99)
    assert s.e.j.digest() == baseline[2]


def statement_tape(available_day):
    """An authored broker statement that disagrees with the books: an open control break from that day."""
    raw = copy.deepcopy(store._tape("campaign-v1").raw)
    at = {"day": available_day, "phase": "OPEN_ADMIN"}
    raw["broker_statements"] = [{"id": "bad", "revision": 1, "source": "Synthetic prime broker", "account": "cash",
                                 "as_of": at, "available_at": at, "balance": "123.45"}]
    return compile_tape(raw)


def test_uncertified_report_forfeits_the_commitment():
    s = session(statement_tape(12))
    diligence_done(s)
    to_day(s, 16)
    assert stage(s) == "forfeited" and s.e.prospect.reason == "report_not_certified"
    assert not s.e.prospect.signed


def test_broken_certificate_blocks_admission_and_keeps_the_cash_out():
    s = session(statement_tape(18))
    diligence_done(s)
    to_day(s, 19)
    assert stage(s) == "eligible"
    admit(s, "5000000")
    to_day(s, 21)
    assert stage(s) == "forfeited" and s.e.prospect.reason == "dealing_blocked"
    assert "Anchor" not in {x.series_id for x in s.e.series}
    assert not any("Admit subscription" in x.memo for x in s.e.j.entries)
    assert any(i["code"] == "dealing_blocked" for i in s.e.incident_events)


def test_capacity_refuses_an_amount_that_breaks_the_mandate_floor_but_allows_a_cap():
    probe = session()
    to_day(probe, 19)
    gross, nav = probe.e.long_mv() + probe.e.short_mv(), probe.e.nav()
    raw = copy.deepcopy(store._tape("campaign-v1").raw)
    # A floor between the book's ratio with $1m and with $5m of new capital.
    floor = (gross / (nav + 1000000) + gross / (nav + 5000000)) / 2
    raw["mandate"]["gross_min"] = str(floor.quantize(Decimal("0.01")))
    s = session(compile_tape(raw))
    diligence_done(s)
    to_day(s, 19)
    with pytest.raises(CommandRejected, match="capacity"):
        s.handle("ben", "big", {"type": "propose_admission", "package_id": "big", "amount": "5000000"})
    assert admit(s, "1000000")["status"] == "ELECTED"


def test_winddown_forfeits_the_prospect():
    s = session()
    diligence_done(s)
    to_day(s, 19)
    d = s.handle("ana", "w", {"type": "propose_winddown", "package_id": "w"})
    s.handle("ben", "ws", {"type": "sign", "package_id": "w", "digest": d["digest"]})
    assert stage(s) == "forfeited" and s.e.prospect.reason == "winddown"


def test_a_rejected_step_changes_nothing():
    s = session()

    def state():
        return (s.version, s.e.j.digest(), copy.deepcopy(s.e.prospect),
                json.dumps([s.view("ana"), s.view("ben")], sort_keys=True, default=str))

    def refused(user, command):
        before = state()
        with pytest.raises(CommandRejected):
            s.handle(user, f"bad{s.version}-{command['type']}-{command.get('amount')}", command)
        assert state() == before

    refused("ben", DILIGENCE)  # not yet qualified
    refused("ana", QUAL)  # the managing partner's assignment
    refused("ben", {"type": "visit", "location": "risk", "assignment": "prospect_qualification"})
    refused("ben", {"type": "propose_admission", "package_id": "early", "amount": "5000000"})  # nothing in escrow
    refused("ana", {"type": "decline_prospect"})
    s.handle("ben", "qual", QUAL)
    refused("ben", DILIGENCE)  # not yet revealed, and attention is spent this window
    to_day(s, 2)
    refused("ben", QUAL)  # no second reveal
    s.handle("ben", "dil", DILIGENCE)
    to_day(s, 19)
    for amount in ("6000000", "2500000", "0", "-1000000", "abc"):
        refused("ben", {"type": "propose_admission", "package_id": "x", "amount": amount})
    d = s.handle("ben", "p", {"type": "propose_admission", "package_id": "p", "amount": "5000000"})
    refused("ben", {"type": "sign", "package_id": "p", "digest": d["digest"]})  # no self-approval
    refused("ana", {"type": "sign", "package_id": "p", "digest": "0" * 64})  # edited contents
    s.handle("ana", "s", {"type": "sign", "package_id": "p", "digest": d["digest"]})
    refused("ben", {"type": "propose_admission", "package_id": "again", "amount": "1000000"})


def test_no_prospect_private_information_in_the_wrong_seat_or_before_it_is_available():
    s = session()

    def sees(user, *needles):
        blob = json.dumps(s.view(user), default=str)
        return [n for n in needles if n in blob]

    private = ("Anchor", "5,000,000", "diligence complete")
    assert sees("ben", *private) == [] and sees("ana", *private) == []
    assert s.view("ana")["prospect"]["max_amount"] is None
    assert any(n["code"] == "prospect_open" for n in s.view("ana")["notices"])  # the introduction itself is public
    assert "prospect_qualification" not in s.view("ana")["research"]["assignments"]

    s.handle("ben", "qual", QUAL)
    assert sees("ben", *private) == []  # assigned, not yet revealed
    to_day(s, 2)
    assert sees("ben", "Anchor") == ["Anchor"] and s.view("ben")["prospect"]["max_amount"] == "5000000"
    assert s.view("ben")["prospect"]["stage"] == "qualified"
    assert sees("ana", *private) == [] and s.view("ana")["prospect"]["stage"] == "prospect"

    s.handle("ben", "share", {"type": "share_research", "topic": "prospect_qualification"})
    assert sees("ana", "Anchor") == ["Anchor"]  # the owner chose to share the evidence
    s.handle("ben", "dil", DILIGENCE)
    to_day(s, 3)
    assert sees("ben", "diligence complete") == ["diligence complete"]
    assert sees("ana", "diligence complete") == []  # still private: only qualification was shared
    to_day(s, 16)
    assert s.view("ana")["prospect"]["stage"] == "committed"  # the signed commitment is a fund matter


def test_pm_learns_terms_only_at_the_signed_commitment_when_nothing_was_shared():
    s = session()
    diligence_done(s)
    to_day(s, 15)
    assert s.view("ana")["prospect"]["max_amount"] is None
    to_day(s, 16)
    assert s.view("ana")["prospect"]["max_amount"] == "5000000"


def test_solo_bot_refuses_to_consent_to_admission():
    s = session(bots=frozenset({"pm"}))
    diligence_done(s)
    to_day(s, 19)
    s.handle("ben", "p", {"type": "propose_admission", "package_id": "p", "amount": "5000000"})
    bot.act(s, "pm", "ana", "bot")
    assert s.packages["p"].status == "PENDING_APPROVAL" and s.e.prospect.authorized is None
    assert any(m.get("ref") == "pkg:p" and "human partner" in m["text"] for m in s.chat)


def test_other_scenarios_have_no_prospect():
    s = Session(Engine(store._tape("case1")), {"pm": "ana", "mp": "ben"})
    assert "prospect" not in s.view("ana")
    with pytest.raises(CommandRejected, match="no prospective LP"):
        s.handle("ben", "x", {"type": "decline_prospect"})
    assert investors.admission_due(s.e) is False


def test_tape_rejects_a_malformed_prospect():
    raw = copy.deepcopy(store._tape("campaign-v1").raw)
    raw["prospect"]["dealing_day"] = 21
    with pytest.raises(TapeError, match="prospect"):
        compile_tape(raw)
