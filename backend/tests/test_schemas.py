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
        s.handle("ana", "say", {"type": "say", "text": "covering", "ref": "BRIN"})
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


def test_command_union_covers_every_player_command():
    from typing import get_args

    from fundforge.governance import COMMANDS
    from fundforge.schemas import Command

    union = get_args(get_args(Command)[0])
    tags = {get_args(m.model_fields["type"].annotation)[0] for m in union}
    assert tags == set(COMMANDS) - {"tick"}  # the clock's tick is server-only


def test_every_command_logged_in_whole_games_validates():
    from pydantic import TypeAdapter

    from fundforge.schemas import Command

    adapter = TypeAdapter(Command)
    logged = []
    for human in ("pm", "mp"):  # bot and human commands, as Session.handle received them
        bot_role = "mp" if human == "pm" else "pm"
        e = Engine(_tape("case1"))
        e.advance()
        s = Session(e, {human: "me", bot_role: bot.BOT_VERSION}, bots=frozenset({bot_role}))
        for k in range(200):
            if s.e.finished():
                break
            bot.act(s, bot_role, bot.BOT_VERSION, f"b{k}")
            s.handle("me", f"ready{k}", {"type": "ready", "version": s.version})
        logged += [x["command"] for x in s.log]
    for scenario in ("case1", "case1-controls"):
        e = Engine(_tape(scenario))
        e.advance()
        s = Session(e, P)
        k = 0
        while not s.e.finished():
            busy(s, k)
            for user in P.values():
                s.handle(user, f"ready-{k}-{user}", {"type": "ready", "version": s.version})
            k += 1
        logged += [x["command"] for x in s.log]
    assert {c["type"] for c in logged} >= {"propose", "sign", "visit", "share_research", "say", "ready",
                                           "resolve_statement"}
    for c in logged:
        adapter.validate_python(c)


def test_client_command_shapes_validate_and_normalize():
    from pydantic import TypeAdapter

    from fundforge.schemas import Command

    adapter = TypeAdapter(Command)
    godot = [  # Godot parses JSON numbers as floats, so values read back from a view arrive as 1250.0 or 7.0
        {"type": "propose", "package_id": "cure-1", "source_version": 7.0,
         "orders": [{"sym": "BRIN", "side": "COVER", "qty": 1250.0, "order_id": "cure-a"}]},
        {"type": "ticket", "order_id": "pm-1", "sym": "BRIN", "side": "COVER", "qty": 1250},
        {"type": "ready", "version": 3, "skip": True}, {"type": "set_speed", "speed": 2}, {"type": "pause"},
        {"type": "resolve_statement", "statement_id": "opening-cash", "revision": 2.0, "version": 9.0},
        {"type": "visit", "location": "broker", "assignment": "borrow"}, {"type": "share_research", "topic": "borrow"},
        {"type": "sign", "package_id": "p", "digest": "ab12"}, {"type": "set_reserve", "amount": "250000"},
        {"type": "accept_replacement"}, {"type": "cancel", "order_id": "pm-1"},
        {"type": "ticket", "order_id": "w", "sym": "ALTO", "side": "BUY", "qty": 10, "limit": "95.25"},
    ]
    dumped = [adapter.validate_python(c).model_dump(mode="json", exclude_unset=True) for c in godot]
    assert dumped[0]["orders"][0]["qty"] == 1250 and type(dumped[0]["orders"][0]["qty"]) is int
    assert type(dumped[5]["revision"]) is int and "skip" not in dumped[3]  # absent stays absent
    for bad in [{"type": "set_reserve", "amount": "lots"}, {"type": "set_reserve", "amount": 250000},
                {"type": "ticket", "order_id": "x", "sym": "A", "side": "BUY", "qty": 10, "limit": "1e"},
                {"type": "ticket", "order_id": "x", "sym": "A", "side": "LONG", "qty": 10},
                {"type": "ticket", "order_id": "x", "sym": "A", "side": "BUY", "qty": 10.5},
                {"type": "ready", "version": 2, "extra": 1}, {"type": "say", "text": {"a": 1}},
                {"type": "tick", "expected_version": 1}, {"type": "no_such_thing"}, {}]:
        with pytest.raises(ValidationError):
            adapter.validate_python(bad)


def terminal_views(s: Session, seen: list) -> None:
    from fundforge.schemas import TerminalView
    from fundforge.terminal import snapshot

    for role in ("pm", "mp"):
        seen.append(TerminalView.model_validate_json(json.dumps({**snapshot(s.e, role), "version": s.version})))


def debriefs(s: Session) -> list:
    """The baseline replay plus one branch omitting each kind of omittable decision once."""
    from fundforge.debrief import OMITTABLE, replay
    from fundforge.schemas import Debrief

    kinds: dict[str, int] = {}
    for seq, item in enumerate(s.log, 1):
        kinds.setdefault(item["command"]["type"], seq)
    omit = [None, *(seq for kind, seq in kinds.items() if kind in OMITTABLE)]
    return [Debrief.model_validate_json(json.dumps(replay(s, seq))) for seq in omit]


def thesis_room(s: Session, k: int) -> None:
    """Each seat forecasts the terminal's live regime question whenever one is open."""
    from fundforge.terminal import snapshot

    q = snapshot(s.e)["regime"]
    if q and not s.e.finished():
        for n, user in enumerate(P.values()):
            with contextlib.suppress(CommandRejected):
                s.handle(user, f"thesis-{k}-{n}", {"type": "thesis", "question": q["question"],
                                                   "forecast": {"calm": "0.7", "stressed": "0.3"}})


def gate_room(s: Session, k: int) -> None:
    """Managing partner contacts Tactical before the reviews; a gate is proposed and elected after the cutoff."""
    if s.e.ev.day == 12 and k == 0:
        s.handle("ben", "contact", {"type": "contact_lp", "lp": "Tactical"})
    if s.e.ev.day >= 16 and "gate" not in s.packages:
        g = s.handle("ana", "gate", {"type": "propose_gate", "package_id": "gate"})
        s.handle("ben", "gate-sign", {"type": "sign", "package_id": "gate", "digest": g["digest"]})


def contract_play(scenario: str, variant: str = "base", script=None) -> tuple[list, list]:
    e = Engine(_tape(scenario, variant))
    e.advance()
    s = Session(e, P)
    terminals: list = []
    k = 0
    while not s.e.finished():
        terminal_views(s, terminals)
        if script:
            script(s, k)
        for user in P.values():
            s.handle(user, f"ready-{k}-{user}", {"type": "ready", "version": s.version})
        k += 1
    terminal_views(s, terminals)
    return terminals, debriefs(s)


def test_terminal_and_debrief_from_whole_games_match_the_contract():
    games = [contract_play("case1"), contract_play("case1", "rally"), contract_play("case1", script=busy),
             contract_play("case1-controls", script=busy), contract_play("case1-generated", "seed:thesis-contract",
                                                                         thesis_room),
             contract_play("case1-generated", "seed:lp-1", gate_room)]
    terminals = [t for g in games for t in g[0]]
    debriefs_ = [d for g in games for d in g[1]]
    # The games above must reach the optional branches, or the contract is untested there.
    assert any(t.macro for t in terminals) and any(t.regime for t in terminals)
    assert any(t.regime is None for t in terminals) and any(t.finished for t in terminals)
    assert any(t.risk.controls.statement_queue for t in terminals) and any(t.orders for t in terminals)
    assert any(t.risk.controls.settlements for t in terminals) and any(t.news for t in terminals)
    assert {n.visibility for t in terminals for n in t.news} == {"private", "shared"}
    assert any(r.revision for t in terminals for r in t.macro)
    assert any(d.research.theses for d in debriefs_) and any(d.investors for d in debriefs_)
    kinds = {c.kind for d in debriefs_ if d.investors for c in d.investors.checkpoints}
    assert kinds == {"review", "chapter_close"}
    assert any(step.status == "omitted" for d in debriefs_ for step in d.timeline)
    assert any(d.rejected for d in debriefs_)
    finished = [d.source_outcome for d in debriefs_]
    assert any(o.seed_commitment for o in finished) and any(o.seed_commitment is None for o in finished)
    assert {o.scenario for o in finished} == {"case1", "case1-controls", "case1-generated"}


def test_terminal_and_debrief_contracts_reject_undeclared_fields():
    from fundforge.debrief import replay
    from fundforge.schemas import BranchOutcome, Debrief, TerminalView
    from fundforge.terminal import snapshot

    e = Engine(_tape("case1"))
    e.advance()
    s = Session(e, P)
    view = {**snapshot(e, "pm"), "version": 0}
    # a branch that stops early reports the live outcome, labelled IN_PROGRESS, without post-run reveals
    assert BranchOutcome.model_validate_json(json.dumps(e.outcome())).label == "IN_PROGRESS"
    TerminalView.model_validate_json(json.dumps(view))
    with pytest.raises(ValidationError):
        TerminalView.model_validate_json(json.dumps({**view, "tape": {}}))
    with pytest.raises(ValidationError):
        TerminalView.model_validate_json(json.dumps({**view, "risk": {**view["risk"], "nav": 1}}))
    k = 0
    while not s.e.finished():
        for user in P.values():
            s.handle(user, f"r{k}-{user}", {"type": "ready", "version": s.version})
        k += 1
    out = replay(s)
    Debrief.model_validate_json(json.dumps(out))
    with pytest.raises(ValidationError):
        Debrief.model_validate_json(json.dumps({**out, "regimes": []}))
    with pytest.raises(ValidationError):  # exponent notation is not a plain decimal string
        Debrief.model_validate_json(json.dumps({**out, "nav_difference": "1E+2"}))
