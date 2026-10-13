"""Generated-market regime research: exact forward filter, as-of terminal leak check, thesis tickets, debrief Brier."""

import copy
import json
from decimal import Decimal as D
from fractions import Fraction as F
from pathlib import Path

import pytest

from fundforge.asof import Observation
from fundforge.debrief import replay
from fundforge.engine import CommandRejected, Engine
from fundforge.generator import GEN_VERSION, MACRO_SERIES, Spec, generate
from fundforge.governance import Session
from fundforge.research import regime_filter
from fundforge.tape import compile_tape
from fundforge.terminal import snapshot

SKELETON = json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "case1.json").read_text(encoding="utf-8"))


def prints(*values: tuple[str, int]) -> list[Observation]:
    return [Observation(MACRO_SERIES, day, day + 1 + 2 * rev, rev, D(v)) for day, (v, rev) in enumerate(values, 1)]


def test_forward_filter_matches_a_hand_derived_three_day_example():
    # p = 3/20; calm prints 48.5..56.5, stressed 43.5..51.5 (first print), revisions within 0.5.
    out = regime_filter(prints(("50.0", 0), ("50.0", 0), ("45.0", 0), ("52.5", 1)), Spec())
    stressed = [(prior["stressed"], post["stressed"]) for prior, post in out]
    # Day 1: chain prior 3/20; 50.0 is possible under both regimes, so it is uninformative.
    # Day 2: 3/20*17/20 + 17/20*3/20 = 51/200 for both prior and posterior (still uninformative).
    # Day 3: chain prior (1 - (7/10)^3)/2 = 657/2000; 45.0 is impossible when calm, so stressed is certain.
    # Day 4: a revision at 52.5 is impossible when stressed (|47.5 - 52.5| > 0.5), so calm is certain.
    assert stressed == [(F(3, 20), F(3, 20)), (F(51, 200), F(51, 200)), (F(657, 2000), F(1)),
                        (F(1 - F(7, 10) ** 4, 2), F(0))]
    # Decisively stressed, then an uninformative print: one switch step from certainty, 17/20.
    assert regime_filter(prints(("45.0", 0), ("50.0", 0)), Spec())[-1][1]["stressed"] == F(17, 20)
    with pytest.raises(ValueError):
        regime_filter(prints(("60.0", 0)), Spec())  # impossible under every regime


def test_revision_replaces_its_first_print():
    # 49.0 alone is ambiguous; the revision 47.5 (within 0.5 of stressed) decides it and must not stack.
    assert regime_filter(prints(("49.0", 0)), Spec())[-1][1]["stressed"] == F(3, 20)
    assert regime_filter(prints(("47.5", 1)), Spec())[-1][1]["stressed"] == F(1)


def _engine(raw):
    e = Engine(compile_tape(raw))
    e.advance()
    return e


def test_terminal_regime_ignores_unpublished_prints_and_hidden_regimes():
    raw = generate("leak", GEN_VERSION, SKELETON)
    for cutoff in (4, 9, 15):
        future = copy.deepcopy(raw)
        future["generator"]["regimes"] = [[d, ("calm" if r == "stressed" else "stressed") if d >= cutoff else r]
                                          for d, r in raw["generator"]["regimes"]]
        regime = dict(map(tuple, future["generator"]["regimes"]))
        for o in future["macro"]:  # rewrite every print not yet published at the cutoff, consistent with the flip
            if o["available_at"] > cutoff:
                level = D("52.5") if regime[o["event_time"]] == "calm" else D("47.5")
                o["value"] = str(level + (D("0.5") if o["revision"] else D("4.0")))
        a, b = _engine(raw), _engine(future)
        changed = False
        while a.ev.day <= cutoff and not a.finished():
            sa, sb = snapshot(a), snapshot(b)
            assert sa["regime"] == sb["regime"] and sa["macro"] == sb["macro"]
            a.advance()
            b.advance()
        while not a.finished():
            changed |= snapshot(a)["regime"] != snapshot(b)["regime"]
            a.advance()
            b.advance()
        assert changed  # the mutation is visible once published, so the check above is not vacuous


def test_terminal_regime_is_the_filter_over_known_prints_and_absent_in_authored_markets():
    from test_engine import CASE1

    from fundforge.tape import load

    e = _engine(generate("leak", GEN_VERSION, SKELETON))
    seen = 0
    while not e.finished():
        q = snapshot(e)["regime"]
        known = e.tape.macro.known(e.ev.day, MACRO_SERIES)
        if known:
            post = regime_filter(known, Spec())[-1][1]
            assert q["question"] == f"regime:{known[-1].event_time}"
            assert D(q["posterior"]["stressed"]) == (D(post["stressed"].numerator) / post["stressed"].denominator) \
                .quantize(D("0.000001"))
            seen += 1
        else:
            assert q is None
        e.advance()
    assert seen
    case1 = Engine(load(CASE1))
    case1.advance()
    assert snapshot(case1)["regime"] is None


def _play_with_theses():
    raw = generate("thesis", GEN_VERSION, SKELETON)
    s = Session(_engine(raw), {"pm": "ana", "mp": "ben"})

    def ready():
        s.handle("ana", f"pm-{s.version}", {"type": "ready", "version": s.version})
        s.handle("ben", f"mp-{s.version}", {"type": "ready", "version": s.version})

    while snapshot(s.e)["regime"] is None:
        ready()
    q = snapshot(s.e)["regime"]["question"]
    digest, nav = s.e.j.digest(), s.e.nav()
    bad = [{"type": "thesis", "question": "regime:999", "forecast": {"calm": "0.5", "stressed": "0.5"}},
           {"type": "thesis", "question": q, "forecast": {"calm": "0.6", "stressed": "0.5"}},
           {"type": "thesis", "question": q, "forecast": {"calm": 0.5, "stressed": "0.5"}},
           {"type": "thesis", "question": q, "forecast": {"calm": "-0.5", "stressed": "1.5"}},
           {"type": "thesis", "question": q, "forecast": {"calm": "1"}}]
    for i, c in enumerate(bad):
        with pytest.raises(CommandRejected):
            s.handle("ana", f"bad-{i}", c)
    s.handle("ana", "t1", {"type": "thesis", "question": q, "forecast": {"calm": "0.9", "stressed": "0.1"}})
    s.handle("ana", "t2", {"type": "thesis", "question": q, "forecast": {"calm": "0.2", "stressed": "0.8"}})
    s.handle("ben", "t3", {"type": "thesis", "question": q, "forecast": {"calm": "1", "stressed": "0"}})
    assert (s.e.j.digest(), s.e.nav()) == (digest, nav)  # theses never touch money
    while snapshot(s.e)["regime"]["question"] == q:
        ready()
    with pytest.raises(CommandRejected):  # the live question moved on; the old one is closed
        s.handle("ana", "late", {"type": "thesis", "question": q, "forecast": {"calm": "1", "stressed": "0"}})
    while not s.e.finished():
        ready()
    return raw, s, int(q.split(":")[1])


def test_theses_are_scored_in_the_debrief_beside_pnl():
    raw, s, day = _play_with_theses()
    truth = dict(map(tuple, raw["generator"]["regimes"]))[day]
    expect = {"pm": ({"calm": "0.2", "stressed": "0.8"}), "mp": {"calm": "1", "stressed": "0"}}  # latest per seat

    def score(f):
        hit = {s: F(D(v)) - (1 if s == truth else 0) for s, v in f.items()}
        return sum(x * x for x in hit.values())

    out = replay(s)
    research = out["research"]
    assert [(t["role"], t["true_regime"], t["forecast"]) for t in research["theses"]] == \
           [("mp", truth, expect["mp"]), ("pm", truth, expect["pm"])]
    for t in research["theses"]:
        assert D(t["brier"]) == D(score(expect[t["role"]]).numerator) / score(expect[t["role"]]).denominator
    assert research["seats"]["pm"]["theses"] == 1 and research["seats"]["mp"]["theses"] == 1
    # Beside P&L: the outcome is identical to a run with the thesis commands omitted from the log.
    plain = Session(_engine(raw), {"pm": "ana", "mp": "ben"})
    for item in s.log:
        if item["command"]["type"] != "thesis":
            c = dict(item["command"])
            if c["type"] == "ready":
                c["version"] = plain.version
            plain.handle({"pm": "ana", "mp": "ben"}[item["role"]], item["key"], c)
    assert plain.e.outcome() == s.e.outcome()


def test_thesis_is_refused_in_authored_markets():
    from test_engine import CASE1

    from fundforge.tape import load

    e = Engine(load(CASE1))
    e.advance()
    s = Session(e, {"pm": "ana", "mp": "ben"})
    with pytest.raises(CommandRejected):
        s.handle("ana", "t", {"type": "thesis", "question": "regime:1", "forecast": {"calm": "1", "stressed": "0"}})


def test_thesis_wire_shape_is_strict():
    from pydantic import ValidationError

    from fundforge.schemas import CommandBody

    ok = {"type": "thesis", "question": "regime:3", "forecast": {"calm": "0.25", "stressed": "0.75"}}
    assert CommandBody.model_validate(ok).root.forecast.stressed == "0.75"
    for bad in ({**ok, "forecast": {"calm": 0.25, "stressed": "0.75"}}, {**ok, "extra": 1},
                {**ok, "forecast": {"calm": "0.25", "stressed": "0.75", "other": "0"}}):
        with pytest.raises(ValidationError):
            CommandBody.model_validate(bad)
