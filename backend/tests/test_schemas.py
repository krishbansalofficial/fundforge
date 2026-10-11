"""Every view a partner can receive matches the published wire contract (fundforge.schemas)."""

import contextlib
import json

import pytest
from pydantic import ValidationError

from fundforge import bot
from fundforge.engine import CommandRejected, Engine
from fundforge.governance import Session
from fundforge.schemas import Fill, RejectedFill, SessionView
from fundforge.store import _tape

P = {"pm": "ana", "mp": "ben"}


def check(s: Session, seen: list[SessionView]) -> None:
    for user in s.partners.values():
        # Validate what clients actually receive: the JSON text, not the Python objects.
        seen.append(SessionView.model_validate_json(json.dumps(s.view(user))))


def play(scenario: str, variant: str = "base", script=None) -> list[SessionView]:
    e = Engine(_tape(scenario, variant))
    e.advance()
    s = Session(e, P)
    seen: list[SessionView] = []
    k = 0
    while not s.e.finished():
        check(s, seen)
        if script:
            script(s, k)
        for user in P.values():
            s.handle(user, f"ready-{k}-{user}", {"type": "ready", "version": s.version})
        k += 1
    check(s, seen)
    return seen


def busy(s: Session, k: int) -> None:
    """Exercise research, sharing, chat, packages with limits, a large purchase and a statement review."""
    if k == 0:
        s.handle("ana", "say", {"type": "say", "text": "covering", "ref": {"sym": "BRIN"}})
        s.handle("ana", "visit-pm", {"type": "visit", "location": "research", "assignment": "demand_survey"})
        s.handle("ben", "visit-mp", {"type": "visit", "location": "broker", "assignment": "borrow"})
        orders = [{"order_id": "cover", "sym": "BRIN", "side": "COVER", "qty": 1250},
                  {"order_id": "alto", "sym": "ALTO", "side": "BUY", "qty": 5000},
                  {"order_id": "low", "sym": "ALTO", "side": "BUY", "qty": 100, "limit": "1"}]
        try:
            package = s.handle("ana", "propose", {"type": "propose", "package_id": "k", "orders": orders})
            s.handle("ben", "sign", {"type": "sign", "package_id": "k", "digest": package["digest"]})
        except CommandRejected:  # an open broker break refuses new risk; reductions stay available
            package = s.handle("ana", "propose-cover", {"type": "propose", "package_id": "c", "orders": orders[:1]})
            s.handle("ben", "sign-cover", {"type": "sign", "package_id": "c", "digest": package["digest"]})
    if s.e.ev.day >= 13 and "s" not in s.packages:  # accepted, then refused at execution: no BRIN borrow left
        try:
            short = [{"order_id": "short", "sym": "BRIN", "side": "SHORT", "qty": 100}]
            package = s.handle("ana", "propose-short", {"type": "propose", "package_id": "s", "orders": short})
            s.handle("ben", "sign-short", {"type": "sign", "package_id": "s", "digest": package["digest"]})
        except CommandRejected:
            pass
    attempts = [("ana", {"type": "share_research", "topic": "demand_survey"}),
                ("ben", {"type": "share_research", "topic": "borrow"})]
    attempts += [("ben", {"type": "resolve_statement", "statement_id": "opening-cash", "revision": revision})
                 for revision in (1, 2)]
    for n, (user, command) in enumerate(attempts):
        if command["type"] == "share_research" and command["topic"] in s.e.shared_research:
            continue
        with contextlib.suppress(CommandRejected):  # possible only once its evidence or revision has arrived
            s.handle(user, f"try-{k}-{n}", {**command, "version": s.version} if "revision" in command else command)


def solo(human_role: str) -> list[SessionView]:
    bot_role = "mp" if human_role == "pm" else "pm"
    e = Engine(_tape("case1"))
    e.advance()
    s = Session(e, {human_role: "me", bot_role: bot.BOT_VERSION}, bots=frozenset({bot_role}))
    seen: list[SessionView] = []
    for k in range(200):
        if s.e.finished():
            break
        bot.act(s, bot_role, bot.BOT_VERSION, f"b{k}")
        check(s, seen)
        s.handle("me", f"ready{k}", {"type": "ready", "version": s.version})
        bot.act(s, bot_role, bot.BOT_VERSION, f"bb{k}")
    check(s, seen)
    return seen


def test_every_view_in_whole_games_matches_the_contract():
    seen = [*play("case1"), *play("case1", "rally"), *play("case1", script=busy),
            *play("case1-controls", script=busy), *play("case1-settlement", script=busy),
            *play("case1-generated", "seed:schema-check"), *solo("pm"), *solo("mp")]
    # The paths above must reach the optional branches, or the contract is untested there.
    fills = [f for v in seen for o in v.orders for f in o.fills]
    assert any(isinstance(f, Fill) for f in fills) and any(isinstance(f, RejectedFill) for f in fills)
    assert {v.outcome.label for v in seen if v.outcome} >= {"WIN", "DISTRESS"}
    assert any(v.fund.margin_call for v in seen) and any(v.research.evidence for v in seen)
    assert any(v.bots for v in seen) and any(v.chat and v.chat[0].ref for v in seen)
    assert any(p.limit for v in seen for p in (o for pkg in v.packages for o in pkg.orders))
    assert any(v.attention.partners for v in seen) and any(v.incident_events for v in seen)


def test_contract_rejects_an_undeclared_field():
    e = Engine(_tape("case1"))
    e.advance()
    view = Session(e, P).view("ana")
    SessionView.model_validate_json(json.dumps(view))
    with pytest.raises(ValidationError):
        SessionView.model_validate_json(json.dumps({**view, "hidden_tape": {}}))
    with pytest.raises(ValidationError):
        SessionView.model_validate_json(json.dumps({**view, "fund": {**view["fund"], "nav": 1}}))
