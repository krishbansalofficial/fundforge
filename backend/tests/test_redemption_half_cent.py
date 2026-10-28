"""Redemption payable is exact pro-rata net capital, rounded once (FUND_ACCOUNTING: cents HALF_EVEN).

Regression: series.redeem rounded units/U to 40 digits before multiplying, so an exact half-cent tie
(5553340.10 x 11500/70000 = 912334.445) rounded up to .45 while the administrator gave .44, and the
day-20 dealing close raised ``administrator_claim`` on scenario-randomiser worlds.
"""

import json
from decimal import Decimal as D
from pathlib import Path

from fundforge import bot
from fundforge.administrator import Administrator
from fundforge.engine import Engine
from fundforge.generator import SCENARIO_VERSION, Spec, generate
from fundforge.governance import Session
from fundforge.series import Series, redeem
from fundforge.tape import compile_tape

SKELETON = json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "case1.json").read_text(encoding="utf-8"))
HARSH = Spec(crisis_points=10, margin_points=25, factor_bp=400, idio_bp=250, stress_multiplier=5)


def test_half_cent_tie_rounds_half_even_in_engine_and_administrator():
    s = Series("Tactical", D(70000), D(100), D("5553340.10"))
    _, payable, fee = redeem(s, D(11500))
    a = Administrator([{"id": "Tactical", "units": "70000", "hwm": "100"}], D("5553340.10"))
    claim = a.preview("2026-01-28", "Tactical", D(11500))
    assert payable == claim.payable == D("912334.44")  # exact 912334.445, HALF_EVEN
    assert fee == claim.crystallized_fee == 0


def test_generated_world_deals_day20_redemption_without_invariant_error():
    # harsh-level world ppo-43/base, passive agent seat with bot:v1 partner: raised at day 20/CLOSE
    e = Engine(compile_tape(generate("ppo-43", SCENARIO_VERSION, SKELETON, HARSH), "base"))
    e.advance()
    s = Session(e, {"pm": "agent", "mp": "bot:mp"}, bots=frozenset({"mp"}))
    k = 0
    while not s.e.finished():
        k += 1
        bot.act(s, "mp", "bot:mp", f"b{k}")
        s.handle("agent", f"r{k}", {"type": "ready", "version": s.version, "skip": True})
        bot.act(s, "mp", "bot:mp", f"c{k}")
    assert any(n.get("code") == "redemption_dealt" for n in s.e.notices)
