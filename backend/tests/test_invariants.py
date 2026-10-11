"""Inject real accounting breaks; check failure, rollback and optimized replay.

    pytest itself runs normally. Child Python processes run -O/-OO and use
    explicit exceptions, not assert statements, to validate their checks.
"""

import json
import os
import subprocess
import sys
from decimal import localcontext
from pathlib import Path

import pytest
from test_engine import CASE1

from fundforge.engine import CommandRejected, Engine, InvariantError
from fundforge.governance import Session
from fundforge.money import D
from fundforge.tape import load


def fresh():
    e = Engine(load(CASE1))
    e.advance()
    return e


def corrupt_balance(e, entity):
    # Bypass Journal deliberately to simulate a broken internal balance index.
    e.j._balances[(entity, "cash")] += D(1)


def corrupt_position(e, symbol):
    e.pos[symbol] += 1


CORRUPTIONS = [
    ("fund_index", "trial_balance", lambda e: corrupt_balance(e, "fund")),
    ("firm_index", "trial_balance", lambda e: corrupt_balance(e, "firm")),
    ("long_book", "long_securities", lambda e: corrupt_position(e, "ALTO")),
    ("short_book", "short_liability", lambda e: corrupt_position(e, "BRIN")),
    ("series_capital", "series_capital", lambda e: e._post("Bad capital allocation", ("capital:Seed", D(1)),
                                                         ("common_pnl", D(-1)))),
    ("series_provision", "series_provision", lambda e: e._post("Bad performance provision", ("provision:Seed", D(1)),
                                                             ("common_pnl", D(-1)))),
    ("nav_claims", "series_nav", lambda e: e._post("Unallocated fund capital", ("cash", D(1)),
                                                 ("capital:Ghost", D(-1)))),
    ("fund_cash", "negative_cash", lambda e: e._post("Invalid withdrawal", ("cash", D(-1)),
                                                     ("common_pnl", D(1)))),
    ("firm_cash", "negative_cash", lambda e: e._post("Invalid payroll", ("cash", -(e.bal("cash", "firm") + 1)),
                                                     ("payroll_expense", e.bal("cash", "firm") + 1), entity="firm")),
    ("broker_credit", "credit_limit", lambda e: e._post("Excess borrowing", ("debt", D("-7500000")),
                                                       ("cash", D("7500000")))),
    ("restricted_cash", "negative_collateral", lambda e: e._post("Invalid release", ("collateral", D("-5000001")),
                                                               ("common_pnl", D("5000001")))),
]


@pytest.mark.parametrize("name,code,corrupt", CORRUPTIONS, ids=[x[0] for x in CORRUPTIONS])
def test_breaks_raise_typed_internal_errors(name, code, corrupt):
    e = fresh()
    corrupt(e)
    with pytest.raises(InvariantError) as raised:
        e.reconcile()
    error = raised.value
    assert error.code == code and error.day == 12 and error.phase == "PUBLIC_MARK"
    assert error.detail and "day 12/PUBLIC_MARK" in str(error)
    assert not isinstance(error, CommandRejected | ValueError)


@pytest.mark.parametrize("units", ["0", "-1"])
def test_opening_rejects_nonpositive_units_before_allocation(units):
    tape = load(CASE1)
    for series in tape.raw["opening"]["fund"]["series"]:
        series["units"] = units
    with pytest.raises(InvariantError, match="opening_units"):
        Engine(tape)


def test_valid_reconciliation_is_independent_of_callers_decimal_precision():
    e = fresh()
    before = e.j.digest()
    with localcontext() as ctx:
        ctx.prec = 6
        e.reconcile()
    assert e.j.digest() == before


def bad_execution(original):
    def execute(e):
        original(e)
        corrupt_position(e, "ALTO")
    return execute


def test_invariant_failure_rolls_back_session_and_preserves_readiness(monkeypatch):
    s = Session(fresh(), {"pm": "ana", "mp": "ben"})
    s.handle("ana", "pm-ready", {"type": "ready", "version": 0})
    before, digest, history = s.view("ana"), s.e.j.digest(), list(s.e.observations)
    monkeypatch.setattr(Engine, "_exec_a", bad_execution(Engine._exec_a))
    with pytest.raises(InvariantError, match="long_securities"):
        s.handle("ben", "mp-ready", {"type": "ready", "version": 1})
    assert s.view("ana") == before and s.e.j.digest() == digest and s.e.observations == history
    assert s.version == 1 and set(s.ready) == {"pm"} and "mp-ready" not in s.results
    s.e.reconcile()


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_invariant_failure_does_not_commit_or_poison_postgres_cache(monkeypatch):
    from fundforge.store import Store

    st = Store(os.environ["DATABASE_URL"])
    try:
        room = st.create_room("case1", "Ana", "Ben", variant="base")
        rid = room["room_id"]
        pm, mp = [st.auth(rid, room["tokens"][role]) for role in ("pm", "mp")]
        st.apply(rid, pm, "pm-ready", {"type": "ready", "version": 0})
        version, s, _ = st.session(rid)
        before, verified = s.view(pm), st.verify(rid)
        monkeypatch.setattr(Engine, "_exec_a", bad_execution(Engine._exec_a))
        with pytest.raises(InvariantError):
            st.apply(rid, mp, "mp-ready", {"type": "ready", "version": 1})
        after_version, after, _ = st.session(rid)
        assert after_version == version == 1 and after.view(pm) == before
        assert st.verify(rid) == verified
        with st.pool.connection() as c:
            assert c.execute("select count(*) from commands where room_id=%s and idem_key=%s",
                             (rid, "mp-ready")).fetchone()[0] == 0
    finally:
        st.close()


PROBE = """
import json
import sys
from fundforge.engine import Engine, InvariantError
from fundforge.tape import load
from test_invariants import CASE1, CORRUPTIONS, fresh
if not sys.flags.optimize:
    raise RuntimeError('probe did not run under optimized Python')
failures = []
for name, code, corrupt in CORRUPTIONS:
    e = fresh()
    corrupt(e)
    try:
        e.reconcile()
    except InvariantError as error:
        if error.code != code:
            raise RuntimeError('unexpected invariant code: ' + error.code)
        failures.append(name)
    else:
        raise RuntimeError('optimized Python accepted the broken state: ' + name)
tape = load(CASE1)
for series in tape.raw['opening']['fund']['series']:
    series['units'] = '0'
try:
    Engine(tape)
except InvariantError as error:
    if error.code != 'opening_units':
        raise RuntimeError('unexpected opening error: ' + error.code)
    failures.append('opening_units')
else:
    raise RuntimeError('optimized Python accepted zero units')
print(json.dumps(failures))
"""


def optimized(flag, code):
    # sys.path explicitly resolves test helpers in a fresh child; no shell quoting.
    script = "import sys; sys.path.insert(0, sys.argv[1]);\n" + code
    result = subprocess.run([sys.executable, flag, "-c", script, str(Path(__file__).parent)],
                            capture_output=True, text=True, timeout=30, check=False)
    if result.returncode:
        pytest.fail(f"{flag} probe failed:\n{result.stderr}")
    return json.loads(result.stdout)


@pytest.mark.parametrize("flag", ["-O", "-OO"])
def test_optimized_python_refuses_every_accounting_break(flag):
    assert optimized(flag, PROBE) == [x[0] for x in CORRUPTIONS] + ["opening_units"]


@pytest.mark.parametrize("flag", ["-O", "-OO"])
def test_optimized_valid_paths_match_committed_journal_goldens(flag):
    golden = json.loads(Path(__file__).with_name("golden.json").read_text(encoding="utf-8"))
    code = "import json; from test_golden import compute; print(json.dumps(compute()))"
    assert optimized(flag, code) == golden
