"""Exact Bayes posteriors from authored evidence cards and Brier scoring of thesis tickets."""

from decimal import Decimal as D
from fractions import Fraction as F
from itertools import permutations

import pytest

from fundforge.research import Card, Question, brier, posterior, shown

Q = Question("brin-refi", {"refinances": D("0.6"), "distressed": D("0.4")})
SUPPLIER = Card("c1", "brin-refi", 3, {"refinances": D("0.8"), "distressed": D("0.3")})
WORKING_CAPITAL = Card("c2", "brin-refi", 7, {"refinances": D("0.2"), "distressed": D("0.7")})
LATE = Card("c3", "brin-refi", 12, {"refinances": D("0"), "distressed": D("1")})
OTHER = Card("x1", "other", 1, {"a": D("1"), "b": D("0")})


def test_posterior_is_exact_bayes():
    p = posterior(Q, [SUPPLIER], 5)
    # 0.6*0.8 / (0.6*0.8 + 0.4*0.3) = 0.48 / 0.60 = 4/5 exactly
    assert p == {"refinances": F(4, 5), "distressed": F(1, 5)}
    p = posterior(Q, [SUPPLIER, WORKING_CAPITAL], 7)
    # 0.096 / (0.096 + 0.084) = 8/15
    assert p == {"refinances": F(8, 15), "distressed": F(7, 15)}
    assert shown(p) == {"refinances": D("0.533333"), "distressed": D("0.466667")}
    assert sum(p.values()) == 1


def test_order_independent_and_other_questions_ignored():
    cards = [SUPPLIER, WORKING_CAPITAL, OTHER]
    first = posterior(Q, cards, 9)
    assert all(posterior(Q, list(o), 9) == first for o in permutations(cards))


def test_future_evidence_is_never_used():
    assert posterior(Q, [SUPPLIER, WORKING_CAPITAL, LATE], 2) == {"refinances": F(3, 5), "distressed": F(2, 5)}
    assert posterior(Q, [SUPPLIER, WORKING_CAPITAL, LATE], 11) == posterior(Q, [SUPPLIER, WORKING_CAPITAL], 11)
    assert posterior(Q, [SUPPLIER, WORKING_CAPITAL, LATE], 12)["distressed"] == 1  # zero likelihood eliminates


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        Question("bad", {"a": D("0.5"), "b": D("0.49")})
    with pytest.raises(ValueError):
        posterior(Q, [SUPPLIER, SUPPLIER], 5)
    with pytest.raises(ValueError):
        posterior(Q, [Card("c9", "brin-refi", 0, {"refinances": D("0.5")})], 5)
    with pytest.raises(ValueError):
        posterior(Q, [LATE, Card("c8", "brin-refi", 0, {"refinances": D("1"), "distressed": D("0")})], 12)


def test_brier_score():
    assert brier({"refinances": D(1), "distressed": D(0)}, "refinances") == 0
    assert brier({"refinances": D(1), "distressed": D(0)}, "distressed") == 2
    assert brier({"refinances": D("0.5"), "distressed": D("0.5")}, "distressed") == F(1, 2)
    assert brier({"a": D("0.7"), "b": D("0.2"), "c": D("0.1")}, "b") == F(49 + 64 + 1, 100)
    with pytest.raises(ValueError):
        brier({"a": D("0.7"), "b": D("0.2")}, "a")


def test_brier_does_not_mutate_its_forecast():
    forecast = {"refinances": D("0.6"), "distressed": D("0.4")}
    before = dict(forecast)
    brier(forecast, "refinances")
    assert forecast == before


def test_brier_cannot_reach_pnl_or_outcomes():
    # Brier is reported beside P&L, never inside it: no other fundforge module may import research,
    # and research itself imports nothing from fundforge (no engine, journal or ledger).
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "fundforge"
    importers = []
    for path in sorted(src.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        names += [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        if path.name == "research.py":
            assert not [m for m in names if m.startswith("fundforge")]
        elif "fundforge.research" in names:
            importers.append(path.name)
    assert importers == []
