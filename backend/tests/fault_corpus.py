"""B5 fault-injection corpus: seeded, deterministic faults applied to a valid Case1 engine mid-season.

One generator per fault class in docs/BENCHMARKS.md B5. Each fault starts from a golden path (test_golden.PATHS),
is applied at a decision barrier, and is then scored against four layers:

- reconcile: ``Engine.reconcile`` at the injection point, or an ``InvariantError`` with a reconcile code while the
  rest of the season runs (production reconciles after every event);
- controls: ``Engine.control_report`` (shadow, broker, administrator, settlement) at the injection point;
- certificate: ``shadow.certify`` struck at the injection point exactly as the dealing gate strikes it, without
  redemption lines;
- verify: the database-free core of ``Store.verify``: replay the same tape and script with the same code from scratch
  and compare the journal digest. Faults in rules (a patched fee function) or in the tape replay identically.

Injection techniques reuse the existing tests: balanced ``_post`` legs (test_broker, test_certificate), coherent
position plus ``_remark`` (test_shadow), replaced settlement rows (test_settlement_recon), reversed and reposted
dated charges (test_broker), a patched ``mgmt_fee_exact`` (test_administrator) and authored broker statements.
"""

from __future__ import annotations

import contextlib
import copy
import random
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any
from unittest import mock

from test_engine import CASE1
from test_golden import PATHS

from fundforge import engine as engine_module
from fundforge.engine import CommandRejected, Engine, InvariantError
from fundforge.series import mgmt_fee_exact
from fundforge.shadow import certify
from fundforge.tape import Tape, compile_tape, load

CENT = Decimal("0.01")
CLASSES = ("balanced_unsupported_posting", "phantom_or_missing_position", "settlement", "financing", "lp_fee",
           "statement")
# Codes raised by Engine.reconcile; every other InvariantError comes from an independent-control gate.
RECONCILE_CODES = frozenset({"trial_balance", "long_securities", "short_liability", "series_capital",
                             "series_provision", "series_nav", "negative_cash", "credit_limit", "negative_collateral",
                             "borrow_identity", "borrow_returns", "borrow_position"})
PHASES = ("EXEC_A", "EXEC_B")
LAYERS = ("reconcile", "controls", "certificate", "verify")
_TAPE = load(CASE1)


def cents(rng: random.Random, hi: int = 1_000_000) -> Decimal:
    return Decimal(rng.randint(1, hi)).scaleb(-2)


@dataclass
class Fault:
    cls: str
    seed: int
    path: str
    at: tuple[int, str]
    variant: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    inject: Callable[[Engine], None] = lambda e: None
    patch: Callable[[], contextlib.AbstractContextManager[Any]] = contextlib.nullcontext
    tape: Tape = _TAPE


# ---------- driving ----------
def drive(tape: Tape, script: dict, at: tuple[int, str] | None) -> Engine:
    """Run the golden script up to the barrier before event ``at`` (script for ``at`` not yet applied)."""
    e = Engine(tape)
    e.advance()
    while not e.finished():
        nxt = e.next_event()
        if at is not None and (nxt.day, nxt.phase) == at:
            break
        if (nxt.day, nxt.phase) in script:
            script[(nxt.day, nxt.phase)](e)
        e.advance()
    return e


def finish(e: Engine, script: dict) -> str:
    """Continue the season after injection; report how it ended."""
    try:
        while not e.finished():
            nxt = e.next_event()
            if (nxt.day, nxt.phase) in script:
                with contextlib.suppress(CommandRejected):
                    script[(nxt.day, nxt.phase)](e)
            e.advance()
    except InvariantError as exc:
        return f"invariant:{exc.code}"
    if any(i["code"] == "dealing_blocked" for i in e.incident_events):
        return "dealing_blocked"
    return "completed"


def certificate(e: Engine, report: dict[str, Any]) -> dict[str, Any]:
    return certify(e.ev.date.isoformat(), e.ev.day, e._administrator_wealth(), e.administrator.liabilities,
                   {k: (s.units, s.net, s.provision) for k, s in e.administrator.series.items()},
                   e.j.balances("fund"), report["breaks"],
                   [q["id"] for q in report["statement_queue"] if q["status"] == "open"], []).wire()


def layers(e: Engine) -> dict[str, Any]:
    try:
        e.reconcile()
        reconcile = ""
    except InvariantError as exc:
        reconcile = exc.code
    report = e.control_report()
    cert = certificate(e, report)
    codes = sorted({b["code"] for b in report["breaks"]}
                   | {"statement_open" for q in report["statement_queue"] if q["status"] == "open"})
    return {"reconcile_code": reconcile, "control_codes": codes, "certificate_reasons": cert["reasons"],
            "nav_difference": cert["difference"]}


# ---------- generators: one per fault class ----------
def balanced_unsupported_posting(f: Fault, rng: random.Random) -> None:
    # (account, sign): + is an asset debit booked as income, - a liability credit booked as expense.
    account, sign = rng.choice([("cash", 1), ("collateral", 1), ("debt", -1), ("accrued_interest", -1),
                                ("accrued_expense", -1), ("mgmt_fee_payable", -1), ("long_securities", 1)])
    amount = sign * cents(rng)
    f.variant, f.params = account, {"amount": str(amount)}
    f.inject = lambda e: e._post("B5 balanced unsupported", (account, amount), ("common_pnl", -amount))


def phantom_or_missing_position(f: Fault, rng: random.Random) -> None:
    f.variant = rng.choice(["add_long", "remove_long", "add_short", "drop_confirmation"])
    pick, qty, index = rng.random(), rng.randint(1, 5000), rng.random()

    def inject(e: Engine) -> None:
        if f.variant == "drop_confirmation" and e.confirmations:
            i = int(index * len(e.confirmations))
            f.params = {"confirmation": f"X{i + 1}"}
            del e.confirmations[i]
            return
        variant = f.variant = "add_long" if f.variant == "drop_confirmation" else f.variant  # no fill yet
        held = sorted(s for s, q in e.pos.items() if (q < 0 if variant == "add_short" else q > 0))
        sym = held[int(pick * len(held))]
        q = min(qty, e.pos[sym]) if variant == "remove_long" else qty
        f.params = {"sym": sym, "qty": q}
        e.pos[sym] += -q if variant in ("remove_long", "add_short") else q
        e._remark()  # position and balanced journal agree with the fabricated holding

    f.inject = inject


def settlement(f: Fault, rng: random.Random) -> None:
    f.variant = rng.choice(["duplicate_receipt", "drop_receipt", "misamount_receipt", "misdate_receipt",
                            "duplicate_pending", "misallocate_pending", "drop_pending"])
    pick, delta = rng.random(), cents(rng, 100_000)

    def inject(e: Engine) -> None:
        variant = f.variant
        if variant.endswith("_pending") and not e.pending:
            variant = f.variant = variant.replace("pending", "receipt").replace("misallocate", "misamount")
        f.params = {}
        if variant.endswith("_pending"):
            i = int(pick * len(e.pending))
            p = e.pending[i]
            if variant == "duplicate_pending":
                e.pending.append(replace(p))
            elif variant == "drop_pending":
                del e.pending[i]
            else:
                e.pending[i] = replace(p, amount=p.amount + delta)
            f.params["obligation"] = p.obligation
            return
        acts = list(e.broker.activities)
        receipts = [i for i, a in enumerate(acts) if a.obligation]
        i = receipts[int(pick * len(receipts))]
        a = acts[i]
        f.params["obligation"] = a.obligation
        if variant == "duplicate_receipt":
            acts.append(replace(a, sequence=len(acts) + 1))
        elif variant == "drop_receipt":
            del acts[i]
        elif variant == "misamount_receipt":
            acts[i] = replace(a, amount=a.amount + delta)
        else:  # dated on the execution day, before its T+1 due day
            executed = e.confirmations[int(a.obligation[1:]) - 1].day
            acts[i] = replace(a, date=next(o["date"] for o in e.observations if o["day"] == executed))
        e.broker.activities = tuple(acts)

    f.inject = inject


def financing(f: Fault, rng: random.Random) -> None:
    f.variant = rng.choice(["wrong_rate", "day_count_365", "date_shift"])
    pick, bump, amount = rng.random(), Decimal(rng.randint(1, 500)).scaleb(-4), cents(rng, 10_000)

    def inject(e: Engine) -> None:
        if f.variant == "wrong_rate":
            i = int(pick * len(e.loans))
            ln = e.loans[i]
            e.loans[i] = replace(ln, rate=ln.rate + bump)
            f.params = {"loan": ln.loan_id, "rate": str(ln.rate + bump)}
            return
        fees = [x for x in e.j.entries if x.memo.startswith("Borrow fee")]
        fee = fees[int(pick * len(fees))]
        d = date.fromisoformat(fee.date)
        if f.variant == "day_count_365":  # the charge re-struck ACT/365 instead of the house ACT/360
            posted = -sum((p.amount for p in fee.postings if p.account == "accrued_interest"), Decimal(0))
            wrong = (posted * 360 / 365).quantize(CENT, rounding=ROUND_HALF_EVEN)
            f.params = {"date": fee.date, "posted": str(posted), "act365": str(wrong)}
            e._post("B5 day count", ("common_pnl", wrong - posted), ("accrued_interest", posted - wrong), date_=d)
        else:  # same totals, charge moved one calendar date later
            f.params = {"from": fee.date, "amount": str(amount)}
            e._post("B5 reverse", ("common_pnl", -amount), ("accrued_interest", amount), date_=d)
            e._post("B5 repost", ("common_pnl", amount), ("accrued_interest", -amount), date_=d + timedelta(days=1))

    f.inject = inject


def lp_fee(f: Fault, rng: random.Random) -> None:
    f.variant = rng.choice(["fee_rate", "series_misallocation", "provision", "fee_date_shift",
                            "unearned_receivable"])
    pick, amount = rng.random(), cents(rng, 100_000)
    if f.variant == "fee_rate":  # rule fault from the first close: fee function scaled
        factor = rng.choice([Decimal(2), Decimal("1.1"), Decimal("0.5")])
        f.params = {"factor": str(factor)}
        f.patch = lambda: mock.patch.object(engine_module, "mgmt_fee_exact", lambda s: mgmt_fee_exact(s) * factor)
        return

    def inject(e: Engine) -> None:
        live = [i for i, s in enumerate(e.series) if s.units > 0]
        i = live[int(pick * len(live))]
        s = e.series[i]
        f.params = {"series": s.series_id, "amount": str(amount)}
        if f.variant == "series_misallocation":  # coherent: state and journal both move capital
            j = live[(live.index(i) + 1) % len(live)]
            t = e.series[j]
            f.params["to"] = t.series_id
            e.series[i], e.series[j] = replace(s, net=s.net - amount), replace(t, net=t.net + amount)
            e._post("B5 misallocate", (f"capital:{s.series_id}", amount), (f"capital:{t.series_id}", -amount))
        elif f.variant == "provision":  # coherent: provision booked out of net capital
            e.series[i] = replace(s, net=s.net - amount, provision=s.provision + amount)
            e._post("B5 provision", (f"capital:{s.series_id}", amount), (f"provision:{s.series_id}", -amount))
        elif f.variant == "fee_date_shift":
            memo = f"Management fee {s.series_id} 1.5% ACT/365"
            fees = [x for x in e.j.entries if x.entity == "fund" and x.memo == memo]
            fee = fees[int(pick * len(fees))]
            d = date.fromisoformat(fee.date)
            f.params["from"] = fee.date
            cap = f"capital:{s.series_id}"
            e._post("B5 reverse fee", ("mgmt_fee_accrued", amount), (cap, -amount), date_=d)
            e._post("B5 repost fee", ("mgmt_fee_accrued", -amount), (cap, amount), date_=d + timedelta(days=1))
        else:
            e._post("B5 unearned", ("fee_receivable", amount), ("fee_revenue", -amount), entity="firm")

    f.inject = inject


def statement(f: Fault, rng: random.Random) -> None:
    f.variant = rng.choice(["authored_mismatch", "broker_record"])
    account, delta = rng.choice(["cash", "collateral", "debt"]), cents(rng, 100_000)
    if f.variant == "broker_record":
        f.params = {"account": account, "delta": str(delta)}

        def inject(e: Engine) -> None:
            e.broker.balances[account] += delta

        f.inject = inject
        return
    f.tape, f.params = statement_tape(f.path, f.at[0], account, delta)


def statement_tape(path: str, day: int, account: str, delta: Decimal) -> tuple[Tape, dict[str, Any]]:
    """A broker statement as of (day, OPEN_ADMIN), published at PUBLIC_MARK, off the broker record by ``delta``."""
    actual = drive(_TAPE, PATHS[path], (day, "EXEC_A")).broker.snapshots[(day, 0)][account]
    balance = actual + delta
    raw = copy.deepcopy(_TAPE.raw)
    raw["broker_statements"] = [{"id": f"b5-{account}-{day}", "revision": 1, "source": "B5 synthetic statement",
                                 "account": account, "as_of": {"day": day, "phase": "OPEN_ADMIN"},
                                 "available_at": {"day": day, "phase": "PUBLIC_MARK"}, "balance": str(balance)}]
    return compile_tape(raw), {"account": account, "record": str(actual), "statement": str(balance)}


GENERATORS: dict[str, Callable[[Fault, random.Random], None]] = {
    "balanced_unsupported_posting": balanced_unsupported_posting,
    "phantom_or_missing_position": phantom_or_missing_position,
    "settlement": settlement,
    "financing": financing,
    "lp_fee": lp_fee,
    "statement": statement,
}


def make(cls: str, seed: int) -> Fault:
    rng = random.Random(f"B5:{cls}:{seed}")
    path = rng.choice(sorted(PATHS))
    # Settlement faults need settled executions: every golden path has receipts from day 17.
    day = rng.randint(17 if cls == "settlement" else 13, 19)
    f = Fault(cls, seed, path, (day, rng.choice(PHASES)))
    GENERATORS[cls](f, rng)
    return f


# ---------- scoring ----------
def evaluate(f: Fault) -> dict[str, Any]:
    script = PATHS[f.path]
    with f.patch():
        e = drive(f.tape, script, f.at)
        f.inject(e)
        row = layers(e)
        diverged = e.j.digest() != drive(f.tape, script, f.at).j.digest()
        outcome = finish(e, script)
    reconcile = bool(row["reconcile_code"]) or (outcome.startswith("invariant:")
                                                and outcome.removeprefix("invariant:") in RECONCILE_CODES)
    return {"class": f.cls, "seed": f.seed, "path": f.path, "at": list(f.at), "variant": f.variant,
            "params": f.params, **row, "propagation": outcome,
            "detected": {"reconcile": reconcile, "controls": bool(row["control_codes"]),
                         "certificate": bool(row["certificate_reasons"]),
                         "verify": diverged}}


def clean_checkpoints(tape: Tape, script: dict) -> Iterator[dict[str, Any]]:
    """Score every decision barrier of an unfaulted season; any flag is a false positive."""
    e = Engine(tape)
    e.advance()
    while not e.finished():
        nxt = e.next_event()
        yield {"at": [nxt.day, nxt.phase], **layers(e)}
        if (nxt.day, nxt.phase) in script:
            script[(nxt.day, nxt.phase)](e)
        e.advance()
    yield {"at": ["end", ""], **layers(e)}


def clean_seasons() -> dict[str, tuple[Tape, dict]]:
    """The four golden paths, and each again with a broker statement that matches the broker record."""
    out = {name: (_TAPE, script) for name, script in PATHS.items()}
    for name, script in PATHS.items():
        out[f"{name}+matching_statement"] = (statement_tape(name, 15, "cash", Decimal(0))[0], script)
    return out


def corpus(seeds: int) -> dict[str, Any]:
    faults = [evaluate(make(cls, seed)) for cls in CLASSES for seed in range(seeds)]
    clean = []
    for name, (tape, script) in clean_seasons().items():
        for point in clean_checkpoints(tape, script):
            flagged = bool(point["reconcile_code"] or point["control_codes"] or point["certificate_reasons"])
            clean.append({"season": name, **point, "flagged": flagged})
    return {"faults": faults, "clean": clean, "summary": summarize(faults, clean)}


def summarize(faults: list[dict[str, Any]], clean: list[dict[str, Any]]) -> dict[str, Any]:
    per_class: dict[str, dict[str, Any]] = {}
    for cls in CLASSES:
        rows = [r for r in faults if r["class"] == cls]
        per_class[cls] = {"n": len(rows), **{layer: sum(r["detected"][layer] for r in rows)
                                             for layer in LAYERS},
                          "independent": sum(r["detected"]["controls"] or r["detected"]["certificate"] for r in rows),
                          "missed_by_controls": sorted({r["variant"] for r in rows if not r["detected"]["controls"]}),
                          "variants": {v: {layer: f"{sum(r['detected'][layer] for r in rows if r['variant'] == v)}/"
                                              f"{sum(r['variant'] == v for r in rows)}" for layer in LAYERS}
                                       for v in sorted({r["variant"] for r in rows})}}
    seasons = sorted({c["season"] for c in clean})
    return {"per_class": per_class,
            "clean": {"seasons": len(seasons), "checkpoints": len(clean),
                      "flagged_checkpoints": sum(c["flagged"] for c in clean),
                      "flagged_seasons": sorted({c["season"] for c in clean if c["flagged"]})}}
