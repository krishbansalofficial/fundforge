import copy
import json
from dataclasses import replace

import pytest
from test_engine import CASE1

from fundforge.engine import Engine
from fundforge.governance import Session
from fundforge.liquidity import _quantity, project
from fundforge.money import D
from fundforge.tape import load


def observed():
    e = Engine(load(CASE1))
    e.advance()
    e.advance()
    return e


def test_projection_preserves_live_engine_and_is_deterministic():
    e = observed()
    before = copy.deepcopy(e.__dict__)
    a = project(e, "-0.60", "0.80")
    assert a == project(e, "-0.60", "0.80")
    assert e.pos == before["pos"] and e.pending == before["pending"]
    assert e.j.digest() == before["j"].digest()
    assert e.series == before["series"] and e.loans == before["loans"]
    assert e.orders == before["orders"] and e.notices == before["notices"]
    assert a["path"] and a["draft"]
    assert all(f["qty"] <= 50000 for step in a["path"] for f in step["fills"])


def test_projection_does_not_read_future_tape_or_future_margin_rates():
    e = observed()
    before = project(e)
    raw = copy.deepcopy(e.tape.raw)
    raw["overrides"] = [{"future_secret": "must not be read"}]
    raw["margin_schedule"].append({"from_day": e.ev.day + 1, "initial": {"long": "99", "short": "99"},
                                   "maintenance": {"long": "99", "short": "99"}})
    e.tape = replace(e.tape, raw=raw, events=())
    assert project(e) == before
    assert "future_secret" not in json.dumps(before)


def test_zero_observed_capacity_is_explicit():
    e = Engine(load(CASE1))
    e.advance()
    a = project(e, "-0.60", "0.80")
    assert a["status"] == "no_observed_capacity"
    assert not a["draft"] and a["events_to_cure"] is None


def test_first_event_nav_loss_equals_independent_sum_of_fill_costs():
    e = observed()
    a = project(e, "-0.60", "0.80", horizon=1)
    cost = sum(abs(D(f["price"]) * f["qty"] - e.marks[f["sym"]] *
                   (D("0.40") if f["side"] == "SELL" else D("1.80")) * f["qty"])
               for f in a["path"][0]["fills"])
    assert abs(D(a["shock_nav"]) - D(a["path"][0]["nav"]) - cost) < D("0.10")
    assert D(a["execution_cost"]) > 0


def test_cure_waits_for_settlement_and_accounts_for_carry_and_capacity():
    e = observed()
    normal = project(e, "-0.60", "0.80", horizon=10)
    thin = project(e, "-0.60", "0.80", horizon=10, volume_scale="0.1")
    assert normal["status"] == thin["status"] == "cured"
    assert normal["events_to_cure"] == 2 and thin["events_to_cure"] == 3
    assert normal["path"][0]["pending_settlements"] > 0
    assert normal["path"][-1]["pending_settlements"] == 0
    assert D(normal["path"][-1]["nav"]) < D(normal["path"][0]["nav"])  # financing/management carry
    assert D(normal["path"][-1]["headroom"]) >= 0
    assert normal["path"][-1]["collateral_funded"]


def test_insolvency_and_funding_shortfall_are_not_reported_as_cures():
    e = observed()
    assert project(e, "-0.9", "1")["status"] == "insolvent"
    e.cfg = {**e.cfg, "credit_limit": str(-e.bal("debt"))}
    a = project(e, "-0.6", "0.8", horizon=1)
    assert a["status"] != "cured"
    assert not a["path"][0]["collateral_funded"]


def test_cure_quantity_matches_small_exhaustive_relief_oracle():
    e = observed()
    e.marks["ALTO"] = D(100)
    e.deficit = lambda: D(1000)
    q, _, _ = _quantity(e, "ALTO", 1000)
    # 35% maintenance, 5bps spread, 2000bps quadratic impact, no previous flow.
    eligible = []
    for n in range(1, 51):
        price = (D(100) * (1 - (D(5) + D(2000) * (D(n) / 1000) ** 2) / 10000)).quantize(D("0.000001"))
        cost = D(100) * n - (price * n).quantize(D("0.01"))
        if D(35) * n - cost >= 1000:
            eligible.append(n)
    assert q == min(eligible) == 29


@pytest.mark.parametrize("kwargs", [{"horizon": 11}, {"long_shock": "-1"}, {"short_shock": "NaN"},
                                   {"volume_scale": "0"}, {"strategy": "magic"}])
def test_invalid_assumptions_rejected(kwargs):
    with pytest.raises(ValueError):
        project(observed(), **kwargs)


def test_authenticated_versioned_api_and_no_commands(monkeypatch):
    from fastapi.testclient import TestClient

    import fundforge.api as api

    s = Session(observed(), {"pm": "ana", "mp": "ben"})

    class Store:
        def auth(self, room, token):
            if token != "seat" or room != "room":
                raise PermissionError("wrong seat")
            return "ana"

        def session(self, _room):
            return s.version, s, {}

    monkeypatch.setattr(api, "store", lambda: Store())
    c = TestClient(api.app)
    url = "/api/rooms/room/liquidity"
    headers = {"Authorization": "Bearer seat"}
    assert c.post(url, json={"version": 0}).status_code == 401
    assert c.post(url, headers=headers, json={"version": 99}).status_code == 409
    assert c.post(url, headers=headers, json={"version": 0, "long_shock": "NaN"}).status_code == 422
    before = (s.e.j.digest(), len(s.log), s.version)
    result = c.post(url, headers=headers, json={"version": 0, "long_shock": "-0.30", "short_shock": "0.50"})
    assert result.status_code == 200
    assert len(result.json()["comparisons"]) == 2
    assert (s.e.j.digest(), len(s.log), s.version) == before


def test_stale_draft_is_rejected_and_fresh_draft_requires_other_partner():
    s = Session(observed(), {"pm": "ana", "mp": "ben"})
    from fundforge.engine import CommandRejected

    command = {"type": "propose", "package_id": "lab", "source_version": 999,
               "orders": [{"order_id": "lab-sale", "sym": "ALTO", "side": "SELL", "qty": 29}]}
    with pytest.raises(CommandRejected, match="stale"):
        s.handle("ana", "stale", command)
    command["source_version"] = s.version
    s.handle("ana", "fresh", command)
    assert not s.e.orders
    assert s.packages["lab"].signatures == {"pm"}
