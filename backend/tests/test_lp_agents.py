"""LP agents in generated-market rooms: interim reviews, generated requests, gate elections, replay, leaks."""

import json
from dataclasses import replace
from decimal import Decimal as D

import pytest

from fundforge import bot, debrief, investors, store
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.lp import LAUNCH, ReviewFacts, State, band, drawdown_pp, redemption_request, review
from fundforge.money import cents
from fundforge.schemas import SessionView
from fundforge.tape import compile_tape

PM, MP = "ana", "ben"
DRAWDOWN_SEED = "seed:lp-1"  # passive play: Tactical falls to concerned by the day-15 cutoff


def room(variant: str = DRAWDOWN_SEED, tape=None) -> Session:
    e = Engine(tape or store._tape(store.GENERATED, variant))
    e.advance()
    return Session(e, {"pm": PM, "mp": MP})


def step(s: Session, k: int) -> None:
    s.handle(PM, f"ra{k}", {"type": "ready"})
    s.handle(MP, f"rb{k}", {"type": "ready"})


def play_to(s: Session, day: int, start: int = 0) -> int:
    k = start
    while not s.e.finished() and s.e.ev.day < day:
        k += 1
        step(s, k)
    return k


def test_changed_gate_terms_refuse_old_signature_and_allow_fresh_proposal():
    s = room()
    play_to(s, 16)
    old = s.handle(MP, "stale-propose", {"type": "propose_gate", "package_id": "stale-gate"})
    original = dict(s.packages["stale-gate"].terms["requests"])
    # Fault injection: a revised request within the same decision window. Production calendar
    # changes may also expire packages; this isolates the terms check from cursor expiry.
    assert s.e.lp is not None
    s.e.lp.requests["Tactical"] += D(1)
    digest = s.e.j.digest()
    with pytest.raises(CommandRejected, match="redemption requests changed"):
        s.handle(PM, "stale-sign", {"type": "sign", "package_id": "stale-gate", "digest": old["digest"]})
    assert s.packages["stale-gate"].terms["requests"] == original
    assert s.packages["stale-gate"].signatures == {"mp"}
    assert s.e.lp.gate_day is None and s.e.j.digest() == digest
    fresh = s.handle(MP, "fresh-propose", {"type": "propose_gate", "package_id": "fresh-gate"})
    assert fresh["digest"] != old["digest"]
    result = s.handle(PM, "fresh-sign", {"type": "sign", "package_id": "fresh-gate", "digest": fresh["digest"]})
    assert result["status"] == "ELECTED" and s.e.lp.gate_day == 20
    assert s.e.j.digest() == digest


def test_hand_derived_tactical_path_over_two_reviews():
    t = LAUNCH["tactical"]
    assert drawdown_pp(D("100"), D("98.5")) == D("1.50") and drawdown_pp(D("100"), D("101")) == 0
    # Review 1: 1.50 pp below peak x 2 = -3; one open alert x 3 = -3; no contact. 65 -> 59.
    s1, c1 = review(t, State(D(65)), ReviewFacts(D("1.50"), open_alerts=1))
    assert (c1["drawdown"], c1["response_lag"], c1["contact"]) == ("-3.00", "-3", "0")
    assert s1.confidence == D(59) and s1.concern_ceiling == D(65) and band(s1.confidence) == "stable"
    # Review 2: 5.00 pp x 2 = -10 capped at -8; no alerts; contact offsets at most 1. 59 -> 52.
    s2, c2 = review(t, s1, ReviewFacts(D("5.00"), contacted=True))
    assert (c2["drawdown"], c2["response_lag"], c2["contact"]) == ("-8", "0", "1")
    assert s2.confidence == D(52) and c2["band"] == "concerned" and s2.concern_ceiling == D(65)
    # Day-15 cutoff: 25% of 70,000 held units beats the 10,000-unit external need (larger, not the sum).
    assert redemption_request(t, s2.confidence, D(70000), 15, D(10000)) == D(17500)
    # Contact never inflates confidence when nothing went wrong.
    s3, c3 = review(t, State(D(65)), ReviewFacts(D(0), contacted=True))
    assert c3["contact"] == "0" and s3.confidence == D(65)


def test_drawdown_drives_a_generated_redemption_dealt_in_exact_units():
    s = room()
    play_to(s, 99)
    e = s.e
    assert e.finished()
    reviews = [x for x in e.lp.log if x["lp"] == "Tactical" and x["kind"] == "review"]
    assert [x["day"] for x in reviews] == ["13", "15"] and D(reviews[1]["drawdown"]) < 0
    assert reviews[1]["band"] == "concerned"
    notice = next(n for n in e.notices if n["code"] == "redemption_notice" and n["refs"].get("series"))
    assert notice["day"] == 15 and notice["refs"]["units"] == "17500.00000000" and notice["refs"]["deal_day"] == 20
    tactical = next(x for x in e.series if x.series_id == "Tactical")
    assert tactical.units == D(52500)  # 70,000 - 17,500 exactly, not the authored 10,000
    dealt = next(n for n in e.notices if n["code"] == "redemption_dealt")
    post = next(x for x in e.j.entries if x.memo == "Deal redemption 17500.00000000 units Tactical")
    payable = -sum(p.amount for p in post.postings if p.account == "redemption_payable")
    assert dealt["refs"]["payable"] == str(payable) and payable == cents(payable)
    assert sum(e.j.balances("fund").values()) == 0  # reconcile() also ran after every event
    assert e.paid["redemption"] == payable and e.outcome()["lp_deferred"] == {}


def test_case1_is_untouched_by_lp_agents():
    e = Engine(store._tape("case1-controls", "base"))
    assert e.lp is None and "lp_agents" not in e.tape.raw
    s = Session(e, {"pm": PM, "mp": MP})
    e.advance()
    assert s.view(MP)["investors"] is None
    with pytest.raises(CommandRejected, match="generated-market"):
        s.handle(MP, "c", {"type": "contact_lp", "lp": "Tactical"})


def big_requests(s: Session) -> None:
    """Test roster: Seed eligible at day 15 and at withdrawal risk, so requests exceed the 20% gate."""
    s.e.lp.profiles["Seed"] = replace(LAUNCH["seed"], first_eligible_cutoff=15)
    s.e.lp.states["Seed"] = State(D(30))


def test_gate_needs_both_partners_and_defers_pro_rata(monkeypatch):
    s = room()
    big_requests(s)
    k = play_to(s, 16)
    requests = dict(s.e.lp.requests)
    assert requests == {"Seed": D(50000), "Tactical": D("17500.00000000")}
    pm_view = s.view(PM)
    assert pm_view["investors"] is None and not any(n["code"] == "lp_band" for n in pm_view["notices"])
    with pytest.raises(CommandRejected, match="managing partner"):
        s.handle(PM, "c1", {"type": "contact_lp", "lp": "Tactical"})
    g = s.handle(PM, "g1", {"type": "propose_gate", "package_id": "gate-1"})
    with pytest.raises(CommandRejected, match="own proposal"):
        s.handle(PM, "g2", {"type": "sign", "package_id": "gate-1", "digest": g["digest"]})
    with pytest.raises(CommandRejected, match="contents"):
        s.handle(MP, "g3", {"type": "sign", "package_id": "gate-1", "digest": "0" * 64})
    assert s.e.lp.gate_day is None
    # the solo bot never supplies the second consent for a gate
    plan = bot.plan(s, "mp")
    assert plan[0]["type"] == "say" and plan[0]["ref"] == "pkg:gate-1" and all(c["type"] != "sign" for c in plan)
    assert s.handle(MP, "g4", {"type": "sign", "package_id": "gate-1", "digest": g["digest"]})["status"] == "ELECTED"
    mp_view = s.view(MP)
    SessionView.model_validate(mp_view)
    assert mp_view["investors"]["gate_elected"] and mp_view["packages"][0]["kind"] == "gate"
    assert mp_view["packages"][0]["terms"] == {"deal_day": 20, "requests": {k: str(v) for k, v in requests.items()}}
    with pytest.raises(CommandRejected, match="already elected"):
        s.handle(PM, "g5", {"type": "propose_gate", "package_id": "gate-2"})
    before = {x.series_id: x for x in s.e.series}
    navs = {}
    real = investors.allocate_gate

    def spy(nav, req, price, gated):
        navs.update(nav=nav, price=price, gated=gated)
        return real(nav, req, price, gated)
    monkeypatch.setattr(investors, "allocate_gate", spy)
    play_to(s, 99, k)
    assert navs["gated"]
    e = s.e
    carried = e.lp.carried
    dealt = {sid: requests[sid] - carried[sid] for sid in requests}
    for sid in requests:
        assert next(x for x in e.series if x.series_id == sid).units == before[sid].units - dealt[sid]
        assert dealt[sid] == dealt[sid].quantize(D("0.00000001")) and carried[sid] > 0
    value = sum(dealt[k] * navs["price"][k] for k in dealt)
    assert value <= D("0.20") * navs["nav"] < value + D("0.0000001") * sum(navs["price"].values())
    fractions = {k: dealt[k] / requests[k] for k in dealt}
    assert abs(fractions["Seed"] - fractions["Tactical"]) < D("1e-9")
    out = e.outcome()
    assert out["label"] != "WIN" and out["lp_deferred"] == {k: str(v) for k, v in sorted(carried.items())}
    closes = {x["lp"]: x for x in e.lp.log if x["kind"] == "chapter_close"}
    assert closes["Tactical"]["gate"] == "-15" and closes["Seed"]["gate"] == "-10"
    assert closes["Patient"]["gate"] == "0" and closes["Patient"]["herding"] == "-4"  # peers were gated


def test_commands_replay_to_identical_journal_and_lp_state():
    s = room()
    k = play_to(s, 13)
    s.handle(MP, "contact", {"type": "contact_lp", "lp": "Tactical"})
    with pytest.raises(CommandRejected, match="attention"):
        s.handle(MP, "contact2", {"type": "contact_lp", "lp": "Seed"})
    k = play_to(s, 16, k)
    g = s.handle(MP, "gate", {"type": "propose_gate", "package_id": "g"})
    s.handle(PM, "sign", {"type": "sign", "package_id": "g", "digest": g["digest"]})
    play_to(s, 99, k)
    assert s.e.lp.gate_day == 20 and s.e.lp.carried == {}  # elected, but requests fit under 20%: no deferral
    assert all(x["gate"] == "0" and x["herding"] == "0" for x in s.e.lp.log if x["kind"] == "chapter_close")
    contact = next(x for x in s.e.lp.log if x["lp"] == "Tactical" and x["day"] == "13")
    assert D(contact["contact"]) > 0
    again = room()
    for item in s.log:
        again.handle(PM if item["role"] == "pm" else MP, item["key"], item["command"])
    assert again.e.j.digest() == s.e.j.digest() and again.e.lp.log == s.e.lp.log
    result = debrief.replay(s)
    assert result["outcome"]["journal_digest"] == s.e.j.digest()
    assert result["investors"]["checkpoints"] == s.e.lp.log


def crashed_after(variant: str, day: int) -> object:
    raw = json.loads(json.dumps(store._tape(store.GENERATED, variant).raw))
    for o in raw["overrides"]:
        if o["day"] >= day and o["event"] == "PUBLIC_MARK" and "marks" in o:
            o["marks"] = {k: str((D(v) * D("0.8")).quantize(D("0.000001"))) for k, v in o["marks"].items()}
    return compile_tape(raw)


def test_views_never_show_a_future_checkpoint():
    # seed lp-0 ends the day-15 review stable; a 20% fall from day 15 makes it concerned
    a, b = room("seed:lp-0"), room(tape=crashed_after("seed:lp-0", 15))
    k = 0
    while not a.e.finished() and a.e.ev.day <= 15:
        for s in (a, b):
            view = s.view(MP)
            assert '"confidence"' not in json.dumps(view) and s.view(PM)["investors"] is None
            assert all(int(x["day"]) <= s.e.ev.day for x in s.e.lp.log)
        assert a.view(MP)["investors"] == b.view(MP)["investors"], a.e.ev
        k += 1
        for s in (a, b):
            step(s, k)
    # the crash after day 15 changes the day-15 review only once that close has been processed
    assert a.e.ev.day == 16 and a.view(MP)["investors"] != b.view(MP)["investors"]
