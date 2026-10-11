from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from fundforge.journal import Journal, JournalError, entry
from fundforge.money import Accrual, D

cents = st.integers(min_value=1, max_value=10**12).map(lambda c: Decimal(c) / 100)


@given(st.lists(st.tuples(st.sampled_from(["fund", "firm"]), cents), min_size=1, max_size=40))
def test_every_entity_trial_balance_is_zero(moves):
    j = Journal()
    for i, (ent, amt) in enumerate(moves):
        j.post(entry(f"e{i}", ent, "2026-01-20", "m", ("cash", amt), ("capital", -amt)))
    for ent in ("fund", "firm"):
        assert sum(j.balances(ent).values(), Decimal(0)) == 0


@given(st.lists(cents, min_size=1, max_size=20))
def test_replay_is_idempotent_and_hash_stable(amounts):
    es = [entry(f"e{i}", "fund", "2026-01-20", "m", ("cash", a), ("capital", -a)) for i, a in enumerate(amounts)]
    j1, j2 = Journal(), Journal()
    j1.post_many(es)
    j2.post_many(es)
    assert j2.post_many(es) is False  # retried delivery adds nothing
    assert j1.digest() == j2.digest()
    assert j2.balance("fund", "cash") == sum(amounts)


def test_rejects_unbalanced_float_subcent_and_reused_identity():
    with pytest.raises(JournalError):
        entry("x", "fund", "2026-01-20", "m", ("cash", D("1.00")), ("capital", D("-0.99")))
    with pytest.raises(JournalError):
        entry("x", "fund", "2026-01-20", "m", ("cash", D("0.001")), ("capital", D("-0.001")))
    with pytest.raises(TypeError):
        D(0.1)
    with pytest.raises(JournalError):
        entry("x", "bank", "2026-01-20", "m", ("cash", D("1")), ("capital", D("-1")))
    j = Journal()
    j.post(entry("x", "fund", "2026-01-20", "m", ("cash", D("1")), ("capital", D("-1"))))
    with pytest.raises(JournalError):
        j.post(entry("x", "fund", "2026-01-20", "m", ("cash", D("2")), ("capital", D("-2"))))


def test_atomic_batch_rejects_without_partial_post():
    j = Journal()
    good = entry("a", "fund", "2026-01-20", "m", ("cash", D("5")), ("capital", D("-5")))
    j.post(good)
    clash = entry("a", "fund", "2026-01-20", "m", ("cash", D("6")), ("capital", D("-6")))
    other = entry("b", "firm", "2026-01-20", "m", ("cash", D("5")), ("capital", D("-5")))
    with pytest.raises(JournalError):
        j.post_many([other, clash])
    assert j.balance("firm", "cash") == 0


def test_accrual_residual_matches_fund_accounting_oracle_6():
    # FUND_ACCOUNTING §6 oracle 6: $25m x 1.5% / 365 for three constant-base dates -> 3082.19 total.
    daily = D("25000000") * D("0.015") / 365
    acc, posted = Accrual(), []
    for _ in range(3):
        p, acc = acc.post(daily)
        posted.append(p)
    assert posted[0] == D("1027.40")
    assert sum(posted) == D("3082.19")
    # $1m borrow at 2%/360 for three dates -> 166.67 after residual rounding.
    acc, total = Accrual(), Decimal(0)
    for _ in range(3):
        p, acc = acc.post(D("1000000") * D("0.02") / 360)
        total += p
    assert total == D("166.67")
