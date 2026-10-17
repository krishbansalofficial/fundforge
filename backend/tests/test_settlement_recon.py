import ast
from pathlib import Path

import pytest
from test_engine import CASE1, run
from test_golden import PATHS

import fundforge.settlement_recon as recon
from fundforge.engine import Engine
from fundforge.money import D
from fundforge.shadow import ExecutionConfirmation
from fundforge.tape import load


def extract(e: Engine):
    """Plain rows the reconstruction consumes; copied from recorded engine state, never recomputed here."""
    pending = [(p.obligation, p.kind, p.sym, p.qty, p.amount, p.frozen, p.settle_day) for p in e.pending]
    receipts = [(a.obligation, a.kind, a.date, a.amount, a.frozen) for a in e.broker.activities if a.obligation]
    dates = {ev.day: ev.date.isoformat() for ev in e.tape.events}
    return dict(
        confirmations=e.confirmations,
        day_dates=dates,
        pending=pending,
        receipts=receipts,
        failures=list(e.settlement_failures),
        day=e.ev.day,
    )


def codes(breaks):
    return [b["code"] for b in breaks]


@pytest.mark.parametrize("script", list(PATHS.values()), ids=list(PATHS))
def test_valid_scenario_paths_reconstruct_without_breaks(script):
    e = run(script)
    assert not e.pending, "scenario should end with every obligation settled"
    assert recon.reconstruct(**extract(e)) == []
    assert e.confirmations, "scenario should exercise at least one execution identity"


@pytest.mark.parametrize("script", [PATHS["S1_early_reduction"], PATHS["S2_replacement_and_cure"]], ids=["S1", "S2"])
def test_valid_paths_cover_every_settlement_side(script):
    sides = {c.side for c in run(script).confirmations}
    assert sides & {"SELL", "COVER", "BUY", "SHORT"}


def settled_game():
    """Engine with one SELL and one BUY executed and settled, returned with its recorded rows."""
    e = Engine(load(CASE1))
    e.advance()
    e.submit_order("sale", "ALTO", "SELL", 100)
    e.submit_order("buy", "COVE", "BUY", 50)
    while not e.finished():
        e.advance()
    rows = extract(e)
    assert rows["confirmations"] and recon.reconstruct(**rows) == []
    return e, rows


def test_mis_dated_receipt_before_due_is_detected():
    _, rows = settled_game()
    oid, kind, _, amount, frozen = rows["receipts"][0]
    early = rows["day_dates"][rows["confirmations"][0].day]  # same day as execution, due is the next day
    rows["receipts"][0] = (oid, kind, early, amount, frozen)
    assert codes(recon.reconstruct(**rows)) == ["receipt_before_due"]


def test_mis_dated_pending_instruction_is_detected():
    e = Engine(load(CASE1))
    e.advance()
    e.submit_order("sale", "ALTO", "SELL", 100)
    e.advance()
    rows = extract(e)
    (oid, kind, sym, qty, amount, frozen, due) = rows["pending"][0]
    rows["pending"][0] = (oid, kind, sym, qty, amount, frozen, due + 1)
    assert codes(recon.reconstruct(**rows)) == ["obligation_misdated"]


def test_mis_amounted_receipt_is_detected_even_when_journal_is_untouched():
    _, rows = settled_game()
    oid, kind, iso, amount, frozen = rows["receipts"][0]
    rows["receipts"][0] = (oid, kind, iso, amount + D("0.01"), frozen)
    breaks = recon.reconstruct(**rows)
    assert codes(breaks) == ["receipt_economics"]
    assert breaks[0]["subject"] == oid


def test_mis_amounted_pending_instruction_is_detected():
    e = Engine(load(CASE1))
    e.advance()
    e.submit_order("sale", "ALTO", "SELL", 100)
    e.advance()
    rows = extract(e)
    assert codes(recon.reconstruct(**rows)) == []
    rows["pending"] = [
        (oid, kind, sym, qty, amount - D("1.00"), frozen, due)
        for oid, kind, sym, qty, amount, frozen, due in rows["pending"]
    ]
    assert codes(recon.reconstruct(**rows)) == ["obligation_economics"]


def test_dropped_and_duplicated_obligations_are_detected():
    _, rows = settled_game()
    dropped = replace_list(rows, "receipts", rows["receipts"][1:])
    assert codes(recon.reconstruct(**dropped)) == ["obligation_missing"]
    doubled = replace_list(rows, "receipts", rows["receipts"] + rows["receipts"][:1])
    assert codes(recon.reconstruct(**doubled)) == ["obligation_duplicate"]


def test_unknown_identity_is_detected():
    _, rows = settled_game()
    rows["receipts"][0] = ("X99", *rows["receipts"][0][1:])
    assert "obligation_unknown" in codes(recon.reconstruct(**rows))


def test_failed_attempts_must_sit_inside_the_due_to_settlement_window():
    e = Engine(load(CASE1))
    e.advance()
    e.submit_order("sale", "ALTO", "SELL", 100)
    e.advance()
    rows = extract(e)
    due = rows["pending"][0][-1]
    rows["failures"] = [(due - 1, "X1")]  # attempt dated before the obligation was due
    rows["pending"] = []
    rows["receipts"] = []
    breaks = codes(recon.reconstruct(**rows))
    assert "failure_outside_window" in breaks and "obligation_missing" in breaks


def test_past_due_without_dated_failure_is_unexplained_then_explained():
    e = Engine(load(CASE1))
    e.advance()
    e.submit_order("sale", "ALTO", "SELL", 100)
    e.advance()
    rows = extract(e)
    due = rows["pending"][0][-1]
    rows["day"] = due
    assert codes(recon.reconstruct(**rows)) == ["obligation_unexplained_delay"]
    rows["failures"] = [(due, "X1")]
    assert recon.reconstruct(**rows) == []


def test_receipt_dated_after_the_current_day_is_detected():
    _, rows = settled_game()
    rows["day"] = min(c.day for c in rows["confirmations"])  # pretend the book is read before settlement
    rows["pending"], rows["failures"] = [], []
    assert "receipt_future" in codes(recon.reconstruct(**rows))


def test_hand_worked_cover_and_short_economics():
    cover = ExecutionConfirmation(
        1, "ALTO", "COVER", 1000, D("50.123456"), D("50123.46"), D("50.000000"), 100000, 0, D(5), D(2000), day=4
    )
    short = ExecutionConfirmation(
        2, "COVE", "SHORT", 300, D("20.000000"), D("6000.00"), D("20.000000"), 100000, 0, D(5), D(2000), day=4
    )
    ob = recon.expected_obligations([cover, short])
    assert ob["X1"].frozen == D("50000.00") and ob["X1"].due_day == 5
    assert ob["X1"].cash == D("50000.00") - D("50123.46") and ob["X1"].collateral == -D("50000.00")
    assert ob["X2"].collateral == D("6000.00") and ob["X2"].cash == 0
    assert recon.expected_cash_receipts([cover, short]) == {5: {"cash": D("-123.46"), "collateral": D("-44000.00")}}


def test_reconstruction_module_has_no_engine_or_posting_imports():
    source = Path(recon.__file__).read_text(encoding="utf-8")
    imported = {node.module for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom) and node.module}
    assert not {m for m in imported if m.lstrip(".") in ("engine", "broker", "journal", "store", "ml")}
    assert "from .money import CENT, CTX, cents" in source


def replace_list(rows, key, value):
    out = dict(rows)
    out[key] = value
    return out


def test_engine_control_report_flags_a_receipt_dated_before_its_due_day():
    """The dated checks are wired into control_report and block certification as a settlement break."""
    import dataclasses

    from fundforge.shadow import REASONS

    e = run(PATHS["S1_early_reduction"])
    assert not [b for b in e.control_report()["breaks"] if b["code"] in recon.RECON_ONLY_CODES]
    acts = list(e.broker.activities)
    i = next(i for i, a in enumerate(acts) if a.obligation)
    oid = acts[i].obligation
    due = e.confirmations[int(oid[1:]) - 1].day + 1
    early = next(ev.date.isoformat() for ev in e.tape.events if ev.day == due - 1)
    acts[i] = dataclasses.replace(acts[i], date=early)
    e.broker.activities = type(e.broker.activities)(acts)
    breaks = e.control_report()["breaks"]
    assert {"code": "receipt_before_due", "subject": oid, "actual": str(due - 1), "expected": str(due)} in breaks
    assert REASONS["receipt_before_due"] == "settlement_break"


def barriers(e: Engine, script=None):
    """Yield the engine at every decision barrier of a season and once at the end."""
    e.advance()
    while not e.finished():
        yield e
        nxt = e.next_event()
        if script and (nxt.day, nxt.phase) in script:
            script[(nxt.day, nxt.phase)](e)
        e.advance()
    yield e


def test_frozen_collateral_is_its_own_code_not_economics():
    cover = ExecutionConfirmation(
        1, "ALTO", "COVER", 1000, D("50.123456"), D("50123.46"), D("50.000000"), 100000, 0, D(5), D(2000), day=4
    )
    rows = dict(confirmations=[cover], day_dates={5: "2026-01-06"}, failures=[], day=5,
                pending=[], receipts=[("X1", "COVER", "2026-01-06", D("50123.46"), D("50000.01"))])
    assert recon.reconstruct(**rows) == [
        {"code": "settlement_collateral", "subject": "X1", "actual": "50000.01", "expected": "50000.00"}]
    rows.update(receipts=[], failures=[(5, "X1")],
                pending=[("X1", "COVER", "ALTO", 1000, D("50123.46"), D("49999.99"), 5)])
    assert codes(recon.reconstruct(**rows)) == ["settlement_collateral"]


def test_control_report_flags_wrong_frozen_on_a_cover_receipt():
    import dataclasses

    from fundforge.shadow import REASONS

    e = run(PATHS["S1_early_reduction"])
    acts = list(e.broker.activities)
    i = next(i for i, a in enumerate(acts) if a.obligation and a.kind == "COVER")
    acts[i] = dataclasses.replace(acts[i], frozen=acts[i].frozen + D("0.01"))
    e.broker.activities = type(e.broker.activities)(acts)
    breaks = e.control_report()["breaks"]
    assert [(b["code"], b["subject"]) for b in breaks] == [("settlement_collateral", acts[i].obligation)]
    assert REASONS["settlement_collateral"] == "settlement_break"


def test_control_report_flags_wrong_frozen_on_a_pending_cover_mid_game():
    import dataclasses

    covers: list[int] = []
    for e in barriers(Engine(load(CASE1)), PATHS["S1_early_reduction"]):
        covers = [k for k, p in enumerate(e.pending) if p.kind == "COVER"]
        if covers:
            break
    assert covers, "S1 should hold a pending cover at some barrier"
    p = e.pending[covers[0]]
    e.pending[covers[0]] = dataclasses.replace(p, frozen=p.frozen - D("1.00"))
    breaks = e.control_report()["breaks"]
    assert [(b["code"], b["subject"]) for b in breaks] == [("settlement_collateral", p.obligation)]


def _valid_seasons():
    from test_campaign_pacing import gate_accepted_seeds

    from fundforge import store

    out = [(name, lambda: load(CASE1), script) for name, script in PATHS.items()]
    out += [(f"campaign-v1:{v}", lambda v=v: store._tape("campaign-v1", v), None)
            for v in ("base", "rally", "lean-company", "tight-credit")]
    out += [(seed, lambda seed=seed: store._tape(store.GENERATED, seed), None) for seed in gate_accepted_seeds(2)]
    return out


VALID_SEASONS = _valid_seasons()


@pytest.mark.parametrize(("name", "tape", "script"), VALID_SEASONS, ids=[s[0] for s in VALID_SEASONS])
def test_valid_seasons_raise_no_break_at_any_barrier(name, tape, script):
    for e in barriers(Engine(tape()), script):
        assert e.control_report()["breaks"] == [], (name, e.ev.day)
