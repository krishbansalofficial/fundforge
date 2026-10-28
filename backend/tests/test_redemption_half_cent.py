"""Redemption payable is exact pro-rata net capital, rounded once (FUND_ACCOUNTING: cents HALF_EVEN).

Regression: series.redeem rounded units/U to 40 digits before multiplying, so an exact half-cent tie
(5553340.10 x 11500/70000 = 912334.445) rounded up to .45 while the administrator gave .44, and the
day-20 dealing close raised ``administrator_claim`` on scenario-randomiser worlds.
"""

import json
from decimal import Decimal as D
from pathlib import Path

import pytest

from fundforge import bot
from fundforge.administrator import Administrator, Capital
from fundforge.engine import Engine
from fundforge.generator import SCENARIO_VERSION, Spec, generate
from fundforge.governance import Session
from fundforge.series import Series, redeem, reprovision
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


@pytest.mark.parametrize(("units", "gross", "provision"), [
    ("1332291.87945", "133274699.72", "9102.36"),  # above HWM 45511.775 x 0.2 = 9102.355
    ("4092498.04545", "410091946.02", "168428.30"),
])
def test_reprovision_tie_matches_administrator_close(units, gross, provision):
    # one series opened at `gross`; wealth = gross + that day's fee, so the close's gross is exactly `gross`
    a = Administrator([{"id": "S", "units": units, "hwm": "100"}], D(gross))
    fee = (D(gross) * D("0.015") / D(365)).quantize(D("0.01"))
    a.close("2026-01-02", D(gross) + fee)
    admin = a.series["S"]
    assert admin.net + admin.provision == D(gross)
    s = reprovision(Series("S", D(units), D(100), D(0)), D(gross))
    assert s.provision == admin.provision == D(provision)
    assert s.net == admin.net


def test_redemption_tie_with_provision_crystallizes_half_even_fee():
    # 42004.90 x 11500/70000 = 6900.805 exactly: the fee ties at a half cent (old code gave 6900.81)
    s = Series("T", D(70000), D(100), D("5553340.10"), D("42004.90"))
    surviving, payable, fee = redeem(s, D(11500))
    a = Administrator([{"id": "T", "units": "70000", "hwm": "100"}], D("5595345.00"))
    a.series["T"] = Capital("T", D(70000), D(100), D("5553340.10"), D("42004.90"))
    claim = a.preview("2026-01-28", "T", D(11500))
    assert fee == claim.crystallized_fee == D("6900.80")
    assert payable == claim.payable == D("912334.44")
    assert (surviving.units, surviving.net, surviving.provision) == (
        claim.surviving.units, claim.surviving.net, claim.surviving.provision)


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
        report = s.e.control_report()
        assert report["administrator"]["breaks"] == [], (s.e.cursor, report["administrator"]["breaks"])
        assert not [b for b in report["breaks"] if b["code"].startswith(("lp_", "admin", "manager_"))]
    assert any(n.get("code") == "redemption_dealt" for n in s.e.notices)
    assert not [i for i in s.e.incident_events if i["code"] == "dealing_blocked"]
