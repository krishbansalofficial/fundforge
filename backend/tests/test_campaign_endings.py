"""Every published campaign award is reached through valid commands (Session.handle), never by label alias.

Policies are scripted from public state only: they read the announced margin call and the barrier
they stand at, never the tape. Each partner command goes through the same propose/sign or ready path
a player uses; a rejected command is simply not issued.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass, field

import pytest

from fundforge import bot, store
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session

Policy = Callable[[Session, list[str]], None]


@dataclass
class Plan:
    """Counter-keyed command issuing so every idempotency key is fresh within one run."""

    n: int = 0
    rejected: list[str] = field(default_factory=list)

    def key(self, prefix: str) -> str:
        self.n += 1
        return f"{prefix}{self.n}"


def trade(s: Session, p: Plan, sym: str, side: str, qty: int) -> None:
    """A joint package: the managing and portfolio partners propose and sign the same digest."""
    k = p.key("t")
    try:
        d = s.handle("ana", "p" + k, {"type": "propose", "package_id": "p" + k,
                                      "orders": [{"order_id": "o" + k, "sym": sym, "side": side, "qty": int(qty)}]})
        s.handle("ben", "s" + k, {"type": "sign", "package_id": "p" + k, "digest": d["digest"]})
    except CommandRejected as ex:
        p.rejected.append(f"day {s.e.ev.day} {s.e.ev.phase} {side} {qty} {sym}: {ex}")


def open_orders(s: Session, sym: str) -> bool:
    return any(o.sym == sym and o.status in ("QUEUED", "PARTIALLY_FILLED") for o in s.e.orders)


def cure(s: Session, p: Plan, sym: str) -> None:
    """Sell enough of a long to clear the announced maintenance deficit, with a 15% margin of safety."""
    if s.e.margin_call is None or s.e.pos.get(sym, 0) <= 0:
        return
    rate = s.e.tape.margin(s.e.ev.day)["maintenance"]["long"]
    need = math.ceil(float(s.e.margin_call) / (float(rate) * float(s.e.marks[sym])) * 1.15) + 1
    trade(s, p, sym, "SELL", min(need, s.e.pos[sym]))


def passive(s: Session, p: Plan) -> None:
    return


def cover_and_cure(s: Session, p: Plan) -> None:
    """Route A: cover the recalled borrow voluntarily before the deadline, then cure the day-16 margin call."""
    at = (s.e.ev.day, s.e.ev.phase)
    if at == (13, "EXEC_A") and s.e.pos.get("FF-BRIN", 0) < 0 and not open_orders(s, "FF-BRIN"):
        trade(s, p, "FF-BRIN", "COVER", 1250)
    if at == (16, "EXEC_A"):
        cure(s, p, "FF-ASTER")
        cure(s, p, "FF-COVE")


def replacement_and_cure(s: Session, p: Plan) -> None:
    """Route B: buy the managing partner's research on borrow, accept the replacement loan before its cutoff,
    then cure the day-16 margin call."""
    at = (s.e.ev.day, s.e.ev.phase)
    if at == (1, "EXEC_A"):
        try:
            s.handle("ben", p.key("v"), {"type": "visit", "assignment": "borrow", "location": "broker"})
        except CommandRejected as ex:
            p.rejected.append(f"research: {ex}")
    if at == (14, "EXEC_A"):
        try:
            s.handle("ben", p.key("a"), {"type": "accept_replacement"})
        except CommandRejected as ex:
            p.rejected.append(f"replacement: {ex}")
    if at == (16, "EXEC_A"):
        cure(s, p, "FF-ASTER")
        cure(s, p, "FF-COVE")


def winddown(s: Session, p: Plan) -> None:
    """Route C: propose a joint winddown on day 21, then liquidate every position at each execution barrier."""
    e = s.e
    if (e.ev.day, e.ev.phase) == (21, "EXEC_A") and e.winddown is None:
        k = p.key("w")
        try:
            d = s.handle("ana", "pw" + k, {"type": "propose_winddown", "package_id": "pw" + k})
            s.handle("ben", "sw" + k, {"type": "sign", "package_id": "pw" + k, "digest": d["digest"]})
        except CommandRejected as ex:
            p.rejected.append(f"winddown: {ex}")
    if e.winddown is not None and e.ev.phase in ("EXEC_A", "EXEC_B"):
        for sym, q in list(e.pos.items()):
            if q != 0 and not open_orders(s, sym):
                trade(s, p, sym, "SELL" if q > 0 else "COVER", abs(q))


def play(variant: str, policy: Policy) -> tuple[Session, dict]:
    e = Engine(store._tape("campaign-v1", variant))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    plan = Plan()
    while not s.e.finished():
        policy(s, plan)
        s.handle("ana", plan.key("ra"), {"type": "ready"})
        s.handle("ben", plan.key("rb"), {"type": "ready"})
    return s, s.e.outcome()


@pytest.mark.parametrize(("variant", "policy", "award"), [
    ("base", cover_and_cure, "RENEWAL"),
    ("base", replacement_and_cure, "RENEWAL"),
    ("base", passive, "SURVIVAL"),
    ("base", winddown, "WINDDOWN"),
    ("tight-credit", passive, "DEFAULT"),
    ("lean-company", passive, "COMPANY_FAILURE"),
])
def test_each_award_is_reached_through_valid_commands(variant, policy, award):
    s, o = play(variant, policy)
    assert o["label"] == award
    assert s.e.finished() and s.version > 0


def test_renewal_routes_have_no_forced_actions_and_no_failures():
    for policy in (cover_and_cure, replacement_and_cure):
        _s, o = play("base", policy)
        assert o["forced"] == [] and o["renewal_failures"] == []
        assert o["recall_resolved_by"] in ("voluntary cover", "replacement borrow")


def test_passive_failure_names_the_renewal_terms_it_missed():
    _s, o = play("base", passive)
    assert o["renewal_failures"] == ["no_forced_actions"]
    assert len(o["forced"]) == 2  # the recall buy-in and the day-16 margin sale, both explainable in the debrief


def test_default_is_explained_by_unpaid_claims_and_collateral_shortfalls():
    s, o = play("tight-credit", passive)
    codes = {i["code"] for i in s.e.incident_events}
    assert {"collateral_shortfall", "claim_unpaid"} <= codes
    assert set(o["renewal_failures"]) >= {"claims_current", "no_broker_shortfalls"}


def test_company_failure_is_payroll_not_the_fund():
    s, o = play("lean-company", passive)
    assert [i["code"] for i in s.e.incident_events if i["code"] == "payroll_unpaid"] == ["payroll_unpaid"]
    assert o["nav"] != "0" and float(o["nav"]) > 0  # the fund is still solvent; the management company is not


def test_winddown_redeems_every_unit_and_refuses_new_risk():
    s, o = play("base", winddown)
    assert o["label"] == "WINDDOWN"
    assert all(x.units == 0 for x in s.e.series)
    assert s.e.bal("redemption_payable") == 0 and not s.e.pending
    assert not any(q for q in s.e.pos.values())
    assert [n for n in s.e.notices if n["code"] == "winddown_declared"]


def test_winddown_closes_elective_buying_at_the_next_barrier():
    e = Engine(store._tape("campaign-v1", "base"))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    plan = Plan()
    while e.winddown is None:
        winddown(s, plan)
        s.handle("ana", plan.key("ra"), {"type": "ready"})
        s.handle("ben", plan.key("rb"), {"type": "ready"})
    assert e.at_barrier() and not e.finished()
    with pytest.raises(CommandRejected, match="winddown"):
        s.handle("ana", "buy-ticket", {"type": "ticket", "order_id": "late", "sym": "FF-ASTER", "side": "BUY",
                                       "qty": 100})


def test_winddown_is_a_joint_package_not_a_unilateral_command():
    e = Engine(store._tape("campaign-v1", "base"))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    d = s.handle("ana", "p1", {"type": "propose_winddown", "package_id": "w1"})
    with pytest.raises(CommandRejected, match="own proposal"):
        s.handle("ana", "p2", {"type": "sign", "package_id": "w1", "digest": d["digest"]})
    assert s.e.winddown is None  # a rejected command restores the snapshot, so read the engine through the session
    s.handle("ben", "p3", {"type": "sign", "package_id": "w1", "digest": d["digest"]})
    assert s.e.winddown == 1


def test_solo_bot_never_countersigns_a_winddown():
    e = Engine(store._tape("campaign-v1", "base"))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": bot.BOT_VERSION})
    s.handle("ana", "p1", {"type": "propose_winddown", "package_id": "w1"})
    plan = bot.plan(s, "mp")
    assert plan[0] == {"type": "say", "ref": "pkg:w1", "text": bot.REFUSED["winddown"]}
    assert all(c["type"] != "sign" for c in plan)


def test_winddown_is_refused_outside_campaign_rooms():
    e = Engine(store._tape("case1", "base"))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    with pytest.raises(CommandRejected, match="campaign"):
        s.handle("ana", "p1", {"type": "propose_winddown", "package_id": "w1"})
