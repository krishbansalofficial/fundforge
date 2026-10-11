import os
from dataclasses import FrozenInstanceError, replace

import pytest
from test_engine import CASE1, run
from test_golden import PATHS

from fundforge.engine import Engine, InvariantError, Order
from fundforge.money import D
from fundforge.shadow import ExecutionConfirmation, inspect_book, inspect_settlements
from fundforge.tape import load


@pytest.mark.parametrize("script", list(PATHS.values()), ids=list(PATHS))
def test_all_scenario_paths_pass_independent_controls(script):
    e = run(script)
    report = e.control_report()
    assert report["status"] == "checked" and not report["breaks"]
    assert D(report["conditional_nav"]) == e.nav()


def test_balanced_coherent_phantom_position_is_caught_outside_engine_reconcile():
    e = Engine(load(CASE1))
    e.advance()
    e.pos["ALTO"] += 100
    e._remark()  # both position and balanced journal agree with the fabricated asset
    e.reconcile()  # internal invariants alone cannot establish provenance
    report = e.control_report()
    assert report["status"] == "break"
    assert {b["code"] for b in report["breaks"]} >= {"position", "long_valuation", "conditional_nav"}


def test_failed_independent_controls_block_dealing_before_units_are_burned():
    e = Engine(load(CASE1))
    while e.ev.day < 20:
        e.advance()
    e.pos["ALTO"] += 100
    e._remark()
    e.reconcile()
    before = (list(e.series), e.j.digest(), list(e.notices))
    with pytest.raises(InvariantError, match="administrator_controls"):
        e._deal()
    assert (e.series, e.j.digest(), e.notices) == before


def test_confirmations_are_immutable_and_price_corruption_is_detected():
    e = Engine(load(CASE1))
    e.advance()
    e.submit_order("sale", "ALTO", "SELL", 100)
    e.advance()
    confirmation = e.confirmations[0]
    with pytest.raises(FrozenInstanceError):
        confirmation.qty = 999
    e.confirmations[0] = replace(confirmation, price=confirmation.price + 1)
    assert any(b["code"] == "fill_price" for b in e.control_report()["breaks"])


def test_independent_expanded_cost_and_holdings_example():
    fill = ExecutionConfirmation(1, "X", "SELL", 20000, D("99.942000"), D("1998840.00"),
                                 D(100), 1000000, 0, D(5), D(2000))
    report = inspect_book({"X": 30000}, [fill], {"X": 10000}, {"X": D(100)},
                          {"long_securities": D(1000000), "trade_receivable": D("1998840.00"),
                           "capital:A": D(-3000000), "common_pnl": D(1160)})
    assert report["status"] == "checked"
    assert report["conditional_nav"] == "2998840.00"
    bad = inspect_book({"X": 30000}, [replace(fill, amount=D(1999000))], {"X": 10000}, {"X": D(100)},
                       {"long_securities": D(1000000), "capital:A": D(-1000000)})
    assert any(b["code"] == "fill_amount" for b in bad["breaks"])


def test_direct_execution_path_also_records_confirmation():
    e = Engine(load(CASE1))
    e.advance()
    e.advance()
    order = Order("direct", "ALTO", "SELL", 25)
    e._fill(order)
    assert e.confirmations[-1].qty == order.filled == 25
    assert e.control_report()["status"] == "checked"


def _codes(e):
    return {b["code"] for b in e.control_report()["breaks"]}


def test_settlement_obligations_rebuilt_from_execution_identities():
    e = Engine(load(CASE1))
    e.advance()
    e.submit_order("sale", "ALTO", "SELL", 100)
    e.advance()
    (p,) = e.pending
    assert p.obligation == "X1" and e.control_report()["status"] == "checked"
    e.pending.append(replace(p))  # duplicate obligation, journal untouched
    assert "settlement_duplicate" in _codes(e)
    e.pending[1] = replace(p, sym="BRIN")  # coherent-looking but misallocated
    assert "settlement_misallocated" in _codes(e)
    e.pending.clear()  # silently dropped obligation
    assert "settlement_missing" in _codes(e)
    e.pending.append(p)
    while e.pending:
        e.advance()
    receipt = next(a for a in e.broker.activities if a.obligation == "X1")
    assert receipt.kind == "SELL" and e.control_report()["status"] == "checked"
    e.broker.activities += (replace(receipt, sequence=999),)  # same execution settled twice
    assert "settlement_duplicate" in _codes(e)


def test_past_due_obligation_needs_dated_failed_attempts():
    fill = ExecutionConfirmation(1, "X", "BUY", 10, D("100.000000"), D("1000.00"),
                                 D(100), 1000, 0, D(5), D(2000), day=3)
    pending = [("X1", "BUY", "X", 10, D("1000.00"), 4)]
    assert inspect_settlements([fill], pending, [], [], 3) == []  # not yet due
    assert [b["code"] for b in inspect_settlements([fill], pending, [], [], 4)] == ["settlement_unexplained_delay"]
    assert inspect_settlements([fill], pending, [], [(4, "X1")], 5) == []  # retried after a dated failure
    assert [b["code"] for b in inspect_settlements([fill], [], [("X9", "BUY", D("1000.00"))], [], 5)] == [
        "settlement_misallocated", "settlement_missing"]


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_failed_buy_settlement_retries_with_dated_evidence_through_postgres():
    import fundforge.store as storage

    store = storage.Store(os.environ["DATABASE_URL"])
    try:
        room = store.create_room("case1-settlement", "Ana", "Ben", variant="base")
        rid = room["room_id"]
        users = {r: store.auth(rid, token) for r, token in room["tokens"].items()}

        def trade(name, order, until_day):
            pkg = store.apply(rid, users["pm"], name, {"type": "propose", "package_id": name, "orders": [order]})
            store.apply(rid, users["mp"], f"{name}-sign", {"type": "sign", "package_id": name, "digest": pkg["digest"]})
            while store.session(rid)[1].e.ev.day < until_day:
                for role in ("pm", "mp"):
                    version = store.session(rid)[0]
                    store.apply(rid, users[role], f"ready-{version}", {"type": "ready", "version": version})

        trade("buy", {"order_id": "buy", "sym": "ALTO", "side": "BUY", "qty": 5000}, 13)
        trade("sell", {"order_id": "sell", "sym": "COVE", "side": "SELL", "qty": 8000}, 15)
        _, s, _ = store.session(rid)
        expected = s.e.control_report()
        buy = expected["settlements"][0]
        assert (buy["obligation"], buy["kind"], buy["status"], buy["failed_days"]) == ("X1", "BUY", "settled", [13, 14])
        assert expected["execution_status"] == "checked"
        assert not [b for b in expected["breaks"] if b["code"].startswith("settlement_")]
        store._cache.clear()
        _, restored, _ = store.session(rid)
        assert restored.e.control_report() == expected
        assert store.verify(rid)["version"] == restored.version
    finally:
        store.close()
