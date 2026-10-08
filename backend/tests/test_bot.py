"""Solo play: a deterministic bot partner acting only through ordinary, logged commands."""

from pathlib import Path

from fundforge import bot
from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.tape import load

TAPE = Path(__file__).parents[2] / "fixtures" / "case1.json"
HUMAN = {"pm": "me", "mp": "me"}


def solo(human_role: str, variant="base", human=None):
    bot_role = "mp" if human_role == "pm" else "pm"
    e = Engine(load(TAPE, variant))
    e.advance()
    partners = {human_role: "me", bot_role: bot.BOT_VERSION}
    s = Session(e, partners, bots=frozenset({bot_role}))
    k = 0
    while not s.e.finished() and k < 200:
        k += 1
        bot.act(s, bot_role, bot.BOT_VERSION, f"b{k}")
        if human:
            human(s, k)
        s.handle("me", f"ready{k}", {"type": "ready", "version": s.version})
        bot.act(s, bot_role, bot.BOT_VERSION, f"bb{k}")
    return s


def replay(s: Session, human_role: str) -> str:
    bot_role = "mp" if human_role == "pm" else "pm"
    e = Engine(s.e.tape)
    e.advance()
    r = Session(e, {human_role: "me", bot_role: bot.BOT_VERSION}, bots=frozenset({bot_role}))
    for x in s.log:
        r.handle("me" if x["role"] == human_role else bot.BOT_VERSION, x["key"], x["command"])
    return r.e.j.digest()


def test_bot_operating_partner_secures_borrow_so_recall_is_never_forced():
    s = solo("pm")
    out = s.e.outcome()
    assert out["recall_resolved_by"] == "replacement borrow"
    assert any(m["ref"] == "accept:replacement" for m in s.chat)
    assert replay(s, "pm") == s.e.j.digest()  # bot actions are logged commands


def test_bot_portfolio_manager_covers_recall_and_cures_margin():
    s = solo("mp")
    out = s.e.outcome()
    assert out["recall_resolved_by"] == "voluntary cover"
    assert out["label"] in ("WIN", "SURVIVAL") and not out["unpaid"]
    assert replay(s, "mp") == s.e.j.digest()


def test_bot_refuses_to_countersign_a_mandate_breach_and_says_why():
    def flatten_once(s, k):
        if k == 1:
            s.handle("me", "flat", {"type": "propose", "package_id": "flat", "orders": [
                {"order_id": "x", "sym": "BEAM", "side": "SELL", "qty": 100000},
                {"order_id": "y", "sym": "ALTO", "side": "SELL", "qty": 30000},
                {"order_id": "z", "sym": "COVE", "side": "SELL", "qty": 30000},
                {"order_id": "w", "sym": "ELAN", "side": "SELL", "qty": 30000}]})
            bot.act(s, "mp", bot.BOT_VERSION, "flat")
    s = solo("pm", human=flatten_once)
    note = next(m for m in s.chat if m["ref"] == "pkg:flat")
    assert "won't countersign" in note["text"] and "mandate" in note["text"]
    assert s.packages["flat"].signatures == {"pm"}


def test_bot_countersigns_a_sound_package():
    def reduce_once(s, k):
        if k == 1:
            s.handle("me", "red", {"type": "propose", "package_id": "red", "orders": [
                {"order_id": "x", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
            bot.act(s, "mp", bot.BOT_VERSION, "red")
    s = solo("pm", human=reduce_once)
    assert s.packages["red"].signatures == {"pm", "mp"}
