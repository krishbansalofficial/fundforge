"""Endogenous market: rival funds' flow moves prices deterministically, from public information only."""

from decimal import Decimal

from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.market import CAP, Market
from fundforge.tape import load
from test_engine import CASE1


def play(variant="base", script=None, each=None):
    e = Engine(load(CASE1, variant))
    e.advance()
    while not e.finished():
        nxt = e.next_event()
        if script and (nxt.day, nxt.phase) in script:
            script[(nxt.day, nxt.phase)](e)
        e.advance()
        if each:
            each(e)
    return e


def deleveraged(e, rival="Halcyon Partners"):
    return [n for n in e.notices if n["code"] == "rival_deleveraging" and n["refs"]["rival"] == rival]


def test_two_identical_runs_are_identical():
    a, b = play(), play()
    assert a.outcome()["journal_digest"] == b.outcome()["journal_digest"]
    assert a.league() == b.league()


def test_crowded_short_unwinds_after_the_selloff_and_squeezes_brin_only_in_base():
    base = play("base")
    hits = deleveraged(base)
    assert hits and all(n["day"] >= 16 for n in hits)
    halcyon = lambda e: next(r for r in e.market.rivals if r.rival_id == "halcyon")
    assert halcyon(base).pos["BRIN"] > -40000  # forced covering
    assert base.marks["BRIN"] > base.ev.marks["BRIN"]  # effective mark still above the tape: the squeeze
    rally = play("rally")
    assert not deleveraged(rally)
    # BRIN's price alone does not separate the worlds (Vantage buys the rally-world dip), the forced cover does
    assert halcyon(rally).pos["BRIN"] == -40000


def test_crowding_report_is_revealed_only_after_it_is_assigned():
    crowding = lambda e: [n for n in e.notices if n["refs"].get("topic") == "crowding"]
    seen = []
    e = play(script={(12, "EXEC_A"): lambda e_: e_.assign_research("crowding")},
             each=lambda e_: seen.append((e_.ev.day, len(crowding(e_)))))
    (n,) = crowding(e)
    assert "Halcyon Partners" in n["text"] and n["day"] == 13
    assert all(k == 0 for d, k in seen if d < 13)
    assert not crowding(play())  # never assigned, never shown


def test_impact_is_capped_and_decays_toward_one_without_flow():
    lo, hi = 1 - CAP, 1 + CAP

    def capped(e):
        assert all(lo <= m <= hi for m in e.market.mult.values()), e.market.mult

    for v in ("base", "rally"):
        play(v, each=capped)
    m = Market({"impact": "0.5"}, ["X", "Y"])
    m.push({"X": 10**9, "Y": -10**9}, {"X": 1, "Y": 1})
    assert (m.mult["X"], m.mult["Y"]) == (hi, lo)
    prev = dict(m.mult)
    for _ in range(20):
        m.decay()
        assert all(abs(m.mult[s] - 1) < abs(prev[s] - 1) for s in m.mult)
        prev = dict(m.mult)
    assert all(abs(x - 1) < Decimal("0.001") for x in m.mult.values())


def test_league_includes_us_and_outcome_has_a_rank():
    e = play()
    league = e.league()
    assert "you" in [r["id"] for r in league]
    out = e.outcome()
    assert out["funds"] == len(league) and 1 <= out["rank"] <= out["funds"]


def test_player_view_exposes_the_league():
    e = Engine(load(CASE1))
    e.advance()
    view = Session(e, {"pm": "ana", "mp": "ben"}).view("ana")
    assert len(view["league"]) == 6 and any(r["id"] == "you" for r in view["league"])
