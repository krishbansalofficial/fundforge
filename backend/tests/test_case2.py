"""Case2 "Profitable, illiquid, and redeeming" (SEASON_SCENARIOS §8, SCENARIO_CONTRACTS Case2), driven by real
two-partner Session commands from the day-39 warm start through day-61 administration.

Two oracles, neither read from engine output:
- ``isolated``: the spec's decision-comparison arithmetic (no day-39/40 accruals). It must reproduce the documented
  numbers exactly (4,195,800 / 18,995,800 / gate 4,999,494.24 / 2,499,747.12 each / 19,997,976.96 ...).
- ``dated``: the same calculator with FUND_ACCOUNTING daily accruals (1.5% ACT/365 management fee on opening
  participation, 2% borrow and 6% debit ACT/360, per-obligation cent residuals, largest-remainder allocation).
  The full run must match it to the cent, because SCENARIO_CONTRACTS says full dated runs include all accruals.

Regenerate the golden digests only with a rules change:  uv run python tests/test_case2.py --write
"""

import json
import os
import sys
from decimal import ROUND_DOWN, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal, localcontext
from pathlib import Path

import pytest

from fundforge import store
from fundforge.engine import RULES_VERSION, Engine
from fundforge.governance import Session
from fundforge.money import CTX

D = Decimal
C = D("0.01")
GOLDEN = Path(__file__).with_name("golden_case2.json")
UNITS = {"Patient": D(80000), "Seed": D(100000), "Tactical": D(70000)}


# ---------- independent calculator (FUND_ACCOUNTING conventions; no engine imports) ----------
def _split(total: Decimal, w: dict[str, Decimal]) -> dict[str, Decimal]:
    s = sum(w.values())
    exact = {k: total * v / s for k, v in w.items()}
    out = {k: v.quantize(C, ROUND_FLOOR) for k, v in exact.items()}
    for k in sorted(exact, key=lambda k: (-(exact[k] - out[k]), k))[:int((total - sum(out.values())) / C)]:
        out[k] += C
    return out


def oracle(cost: Decimal, *, dated: bool, gate: bool) -> dict:
    """Day-40 dealing for $3m dollar targets from Seed and Tactical after a BEAM sale costing ``cost``."""
    with localcontext(CTX):
        cap = {k: u * 100 for k, u in UNITS.items()}  # every series at 100/unit, HWM 120: no provision
        fee_res: dict[str, Decimal] = {}
        fin_exact = [D(12500 * 100) * D("0.02") / 360] * 4 + [D(2500000) * D("0.06") / 360]
        fin_res = [D(0)] * 5
        mgmt = fin = D(0)
        for day_cost in (D(0), cost):  # day 39 close, then day 40 close (the sale executes day 40 EXEC_A)
            day_fin = D(0)
            if dated:
                for i, x in enumerate(fin_exact):
                    t = x + fin_res[i]
                    day_fin += t.quantize(C, ROUND_HALF_EVEN)
                    fin_res[i] = t - t.quantize(C, ROUND_HALF_EVEN)
            fees = {}
            for k in cap:
                t = cap[k] * D("0.015") / 365 + fee_res.get(k, D(0)) if dated else D(0)
                fees[k] = t.quantize(C, ROUND_HALF_EVEN)
                fee_res[k] = t - fees[k]
            pnl = -(day_fin + day_cost)
            share = _split(pnl, cap) if pnl else dict.fromkeys(cap, D(0))
            cap = {k: cap[k] + share[k] - fees[k] for k in cap}
            mgmt, fin = mgmt + sum(fees.values()), fin + day_fin
        nav = sum(cap.values())
        req = {}
        for k in ("Seed", "Tactical"):  # dollar target / struck 6dp value, units 8dp rounded down
            req[k] = (D(3000000) / (cap[k] / UNITS[k]).quantize(D("0.000001"))).quantize(D("1E-8"), ROUND_DOWN)
        wanted = sum(u * cap[k] / UNITS[k] for k, u in req.items())
        f = min(D(1), D("0.2") * nav / wanted) if gate else D(1)
        dealt = {k: (u * f).quantize(D("1E-8"), ROUND_DOWN) for k, u in req.items()}
        pay = {k: (cap[k] * dealt[k] / UNITS[k]).quantize(C, ROUND_HALF_EVEN) for k in dealt}
        return {"nav": nav, "gate_cap": (D("0.2") * nav).quantize(C), "dealt": dealt, "pay": pay,
                "deferred": {k: req[k] - dealt[k] for k in req}, "post": nav - sum(pay.values()),
                "mgmt": mgmt, "fin": fin}


def ratio(x: Decimal, nav: Decimal) -> Decimal:
    with localcontext(CTX):
        return (x / nav * 100).quantize(D("0.0001"))


def test_isolated_oracle_reproduces_the_documented_checkpoints():
    a = oracle(D(4200), dated=False, gate=False)
    assert a["nav"] == D("24995800.00") and a["post"] == D("18995800.00")
    assert a["pay"] == {"Seed": D("3000000.00"), "Tactical": D("3000000.00")}
    assert (ratio(D(26300000), a["post"]), ratio(D(16300000), a["post"])) == (D("138.4517"), D("85.8084"))
    assert D(2100000) + D("4195800") - sum(a["pay"].values()) - 100000 == D("195800.00")
    b = oracle(D("2528.80"), dated=False, gate=True)
    assert b["nav"] == D("24997471.20") and b["gate_cap"] == D("4999494.24")
    assert b["pay"] == {"Seed": D("2499747.12"), "Tactical": D("2499747.12")}
    assert all(D(3000000) - p == D("500252.88") for p in b["pay"].values())
    assert b["post"] == D("19997976.96")
    assert (ratio(D(27300000), b["post"]), ratio(D(17300000), b["post"])) == (D("136.5138"), D("86.5088"))
    assert D(2100000) + D("3197471.20") - sum(b["pay"].values()) - 100000 == D("197976.96")
    n = oracle(D(0), dated=False, gate=False)
    assert n["post"] == D("19000000.00")
    assert (ratio(D(30500000), n["post"]), ratio(D(20500000), n["post"])) == (D("160.5263"), D("107.8947"))


# ---------- driving the game ----------
class Run:
    def __init__(self) -> None:
        e = Engine(store._tape("case2"))
        e.advance()
        self.s = Session(e, {"pm": "ana", "mp": "ben"})
        self.n = 0
        self.views: list[tuple[int, str, dict, dict]] = []

    @property
    def e(self) -> Engine:
        return self.s.e

    def cmd(self, role: str, command: dict) -> dict:
        self.n += 1
        return self.s.handle("ana" if role == "pm" else "ben", f"{role}-{self.n}", command)

    def joint(self, proposer: str, command: dict) -> dict:
        r = self.cmd(proposer, command)
        return self.cmd("mp" if proposer == "pm" else "pm", {"type": "sign", "package_id": command["package_id"],
                                                             "digest": r["digest"]})

    def sell(self, pid: str, qty: int) -> None:
        res = self.joint("pm", {"type": "propose", "package_id": pid,
                                "orders": [{"order_id": pid, "sym": "BEAM", "side": "SELL", "qty": qty}]})
        assert res["status"] == "AUTHORIZED_QUEUED"

    def step(self) -> None:
        self.views.append((self.e.ev.day, self.e.ev.phase, self.s.view("ana"), self.s.view("ben")))
        self.cmd("pm", {"type": "ready"})
        self.cmd("mp", {"type": "ready"})

    def to(self, day: int, phase: str = "EXEC_A") -> None:
        """Advance to the decision barrier before (day, phase)."""
        while (lambda n: (n.day, n.phase))(self.e.next_event()) != (day, phase):
            self.step()

    def finish(self) -> None:
        while not self.e.finished():
            self.step()


def play(branch: str) -> Run:
    r = Run()
    if branch == "2B":  # day-39 committee: the managing partner proposes the gate, the PM's signature elects it
        assert r.joint("mp", {"type": "propose_gate", "package_id": "gate"})["status"] == "ELECTED"
    r.to(40)
    if branch in ("2A", "2B"):
        r.sell("beam40", 42000 if branch == "2A" else 32000)
    r.to(41)
    if branch == "recovery":  # F1 then recovery: cure the passive gross/net breach with a liquid sale
        r.sell("beam41", 25000)
    if branch == "2B":  # S2: the signed next-window plan sells 20,000 BEAM at day 58 EXEC_A, settling day 59
        r.to(58)
        r.sell("beam58", 20000)
    r.finish()
    return r


@pytest.fixture(scope="module")
def runs() -> dict[str, Run]:
    return {b: play(b) for b in ("2A", "2B", "none", "recovery")}


def fill(r: Run, oid: str) -> dict:
    (f,) = next(o for o in r.e.orders if o.order_id == oid).fills
    return f


@pytest.mark.parametrize("branch, qty, price, amount, cost, gate", [
    ("2A", 42000, "99.900000", "4195800.00", "4200.00", False),
    ("2B", 32000, "99.920975", "3197471.20", "2528.80", True),
])
def test_day40_sale_and_dealing_match_the_spec_and_the_dated_oracle(runs, branch, qty, price, amount, cost, gate):
    r = runs[branch]
    f = fill(r, "beam40")
    assert (f["day"], f["phase"], f["qty"], f["price"], f["amount"]) == (40, "EXEC_A", qty, price, amount)
    assert D(qty) * 100 - D(amount) == D(cost)
    want = oracle(D(cost), dated=True, gate=gate)
    cert = next(c for c in r.e.certificates if c["day"] == 40)
    assert cert["status"] == "certified" and D(cert["book_nav"]) == want["nav"]
    lines = {x["series_id"]: x for x in cert["redemptions"]}
    assert {k: D(x["units"]) for k, x in lines.items()} == want["dealt"]
    assert {k: D(x["journal_payable"]) for k, x in lines.items()} == want["pay"]
    assert lines["Seed"]["units"] == lines["Tactical"]["units"]  # equal dollar requests, equal treatment
    if gate:
        assert sum(want["pay"].values()) <= want["gate_cap"] == D("4998805.52")
        gated = {n["refs"]["series"]: D(n["refs"]["units"]) for n in r.e.notices if n["code"] == "redemption_gated"}
        assert gated == want["deferred"] == {"Seed": D("5007.16871368"), "Tactical": D("5007.16871368")}
    else:
        assert not any(n["code"] == "redemption_gated" for n in r.e.notices)
    assert not any(i["code"] == "mandate_breach" for i in r.e.incident_events)


@pytest.mark.parametrize("branch, proceeds", [("2A", "4195800"), ("2B", "3197471.20"), ("none", "0")])
def test_day41_payment_cash_bridges_from_the_spec_with_new_dated_charges(runs, branch, proceeds):
    r = runs[branch]
    want = oracle(D(4200) if branch == "2A" else D("2528.80") if branch == "2B" else D(0),
                  dated=True, gate=branch == "2B")
    # day 39/40 charges invoiced at the day-40 close and paid day 41 with the inherited $100,000 invoice
    assert (want["mgmt"], want["fin"]) == (D("2054.72"), D("1388.89"))
    day41 = next(v for d, p, v, _ in r.views if (d, p) == (41, "PUBLIC_MARK"))["fund"]
    owed = sum(want["pay"].values()) + 100000 + want["mgmt"] + want["fin"]
    if branch == "none":  # no preparation: the credit line pays, so cash is zero and debt rises; not a default
        assert D(day41["cash"]) == 0 and D(day41["debt"]) == D(2500000) + owed - D(2100000)
    else:
        assert D(day41["cash"]) == D(2100000) + D(proceeds) - owed
        assert D(day41["debt"]) == D(2500000)
    assert r.e.paid["redemption"] == sum(want["pay"].values()) + (
        sum(D(x["journal_payable"]) for c in r.e.certificates if c["day"] == 60 for x in c["redemptions"]))


def test_no_preparation_creates_a_passive_mandate_breach_and_a_liquid_sale_recovers(runs):
    none, rec = runs["none"], runs["recovery"]
    want = oracle(D(0), dated=True, gate=False)
    breaches = [i for i in none.e.incident_events if i["code"] == "mandate_breach"]
    assert [(i["day"], i["refs"]["breach"]) for i in breaches] == [(40, "gross_max"), (40, "net_max")]
    # full-run post-flow ratios on the dated post-flow NAV; the isolated 160.5263%/107.8947% are tested above
    assert (ratio(D(30500000), want["post"]), ratio(D(20500000), want["post"])) == (D("160.5554"), D("107.9143"))
    assert none.e.outcome()["label"] == "SURVIVAL"  # positive NAV, all paid, but ends outside the mandate
    # new risk stays blocked by the mandate while the reduction is allowed
    assert none.e.compliance_check([("ALTO", "BUY", 1)]) and not none.e.compliance_check([("BEAM", "SELL", 1)])
    f = fill(rec, "beam41")
    assert (f["day"], f["qty"], f["price"]) == (41, 25000, "99.937500")  # 2.5% of 1,000,000: 6.25bps
    assert rec.e.outcome()["label"] == "WIN"


@pytest.mark.parametrize("branch", ["2A", "2B", "recovery"])
def test_success_paths_finish_day61_with_no_deferred_units_and_reconciled_books(runs, branch):
    r = runs[branch]
    e, o = r.e, r.e.outcome()
    assert e.finished() and (e.ev.day, e.ev.phase) == (61, "OPEN_ADMIN")
    assert o["label"] == "WIN" and o["lp_deferred"] == {} and not o["unpaid"] and not o["forced"]
    assert e.control_report()["status"] == "checked"
    assert all(c["status"] == "certified" for c in e.certificates)
    for ent in ("fund", "firm"):
        assert sum(e.j.balances(ent).values()) == 0
    assert e.bal("redemption_payable") == e.bal("mgmt_fee_payable") == e.bal("interest_payable") == 0
    assert e.bal("fee_receivable", "firm") == -e.bal("mgmt_fee_accrued")  # only the weekend accrual remains


def test_gate_defers_units_to_day60_which_deal_and_pay_without_a_second_notice(runs):
    r = runs["2B"]
    s58 = fill(r, "beam58")
    assert (s58["day"], s58["price"], s58["amount"]) == (58, "103.939680", "2078793.60")  # 104 less 5.8bps
    day60 = next(c for c in r.e.certificates if c["day"] == 60)
    assert day60["status"] == "certified"
    assert {x["series_id"]: D(x["units"]) for x in day60["redemptions"]} == {
        "Seed": D("5007.16871368"), "Tactical": D("5007.16871368")}
    assert [c["day"] for c in r.e.certificates] == [40, 60]  # 2A has only the day-40 dealing
    assert [c["day"] for c in runs["2A"].e.certificates] == [40]
    # the gate cost confidence once, in its own window only
    gate_marks = [c for c in r.e.lp.log if c["kind"] == "chapter_close" and c["gate"] != "0"]
    assert [(c["day"], c["lp"], c["gate"]) for c in gate_marks] == [("40", "Seed", "-10"), ("40", "Tactical", "-15")]
    assert not any(n["code"] == "redemption_notice" and n["day"] > 39 for n in r.e.notices)


def test_no_future_information_reaches_either_seat_before_its_event(runs):
    for r in runs.values():
        for day, phase, *views in r.views:
            for v in views:
                beam = D(v["marks"]["BEAM"])
                codes = {n["code"] for n in v["notices"]}
                if day < 43:
                    assert beam == 100 and "market_rally" not in codes, (day, phase)
                    assert "104" not in json.dumps(v["notices"])
                if day < 60:
                    assert beam != 103
        assert next(v for d, p, v, _ in r.views if (d, p) == (43, "PUBLIC_MARK"))["marks"]["BEAM"] == "104.000000"


def test_gate_is_joint_and_binds_the_dollar_targets():
    r = Run()
    proposal = r.cmd("mp", {"type": "propose_gate", "package_id": "g"})
    pkg = r.s.packages["g"]
    assert pkg.terms == {"deal_day": 40, "requests": {}, "amounts": {"Seed": "3000000", "Tactical": "3000000"}}
    with pytest.raises(Exception, match="cannot approve their own"):
        r.cmd("mp", {"type": "sign", "package_id": "g", "digest": proposal["digest"]})
    inbox = r.s.view("ben")["investors"]
    assert {x["id"]: x["requested_amount"] for x in inbox["lps"]} == {
        "Patient": None, "Seed": "3000000", "Tactical": "3000000"}
    assert r.s.view("ana")["investors"] is None  # the LP inbox is the managing partner's


def test_inherited_invoice_waits_for_its_due_day_and_noticed_claims_block_the_debt_sweep():
    r = Run()
    e = r.e
    assert (e.nav(), e.bal("cash"), -e.bal("debt")) == (D("25000000.00"), D(2100000), D(2500000))
    assert -e.bal("mgmt_fee_payable") == 70000 and -e.bal("interest_payable") == 30000
    assert e.bal("fee_receivable", "firm") == 70000 and e.bal("cash", "firm") == 180000
    assert e.control_report()["status"] == "checked"
    r.to(40, "EXEC_B")  # day 40 administration has run
    assert not e.paid  # the inherited invoice is due day 41, not at the first administration
    assert (e.bal("cash"), -e.bal("debt")) == (D(2100000), D(2500000))  # the $6m notice blocked the debt sweep


def _replay(r: Run) -> Session:
    fresh = Run().s
    for item in r.s.log:
        fresh.handle("ana" if item["role"] == "pm" else "ben", item["key"], item["command"])
    return fresh


@pytest.mark.parametrize("branch", ["2A", "2B", "none", "recovery"])
def test_replay_reproduces_the_journal(runs, branch):
    r = runs[branch]
    assert _replay(r).e.j.digest() == r.e.j.digest()


def compute(runs: dict[str, Run]) -> dict:
    return {"rules_version": RULES_VERSION, "tape_digest": runs["2A"].e.tape.digest,
            "paths": {b: {"label": r.e.outcome()["label"], "nav": str(r.e.nav()),
                          "journal_digest": r.e.j.digest()} for b, r in runs.items()}}


def test_paths_match_committed_golden_digests(runs):
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden["rules_version"] == RULES_VERSION, "rules changed: bump RULES_VERSION and regenerate goldens"
    assert compute(runs) == golden


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs DATABASE_URL")
def test_postgres_room_replays_the_gate_branch(runs):
    st = store.Store(os.environ["DATABASE_URL"])
    try:
        st.init()
        room = st.create_room("case2", "Ana", "Ben")
        users = {role: st.auth(room["room_id"], tok) for role, tok in room["tokens"].items()}
        for item in runs["2B"].s.log:
            st.apply(room["room_id"], users[item["role"]], item["key"], item["command"])
        assert st.verify(room["room_id"])["journal_digest"] == runs["2B"].e.j.digest()
    finally:
        st.close()


if __name__ == "__main__" and "--write" in sys.argv:
    GOLDEN.write_text(json.dumps(compute({b: play(b) for b in ("2A", "2B", "none", "recovery")}), indent=2) + "\n",
                      encoding="utf-8")
