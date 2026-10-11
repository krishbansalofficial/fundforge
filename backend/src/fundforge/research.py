"""Research as a skill (ROADMAP P4): hidden discrete states, authored evidence, exact Bayes and Brier scores.

Each research question has a hidden true state drawn from published priors. Evidence cards
carry authored likelihoods P(card | state) as Decimal strings; only their ratios matter.
Posteriors are computed exactly with ``Fraction`` (Decimal division would round) and shown
as 6dp HALF_EVEN Decimals. A card is usable only once its ``available_at`` day has arrived,
so a posterior can never contain future evidence. Thesis tickets are scored with the
multi-state Brier score, reported beside P&L and never inside it.

Pure domain: no engine, journal or I/O imports. Not yet wired into a scenario.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction

SHOWN = Decimal("0.000001")


@dataclass(frozen=True)
class Question:
    question_id: str
    prior: Mapping[str, Decimal]  # published; must sum to exactly 1

    def __post_init__(self) -> None:
        if len(self.prior) < 2 or any(p <= 0 for p in self.prior.values()) or sum(self.prior.values()) != 1:
            raise ValueError(f"{self.question_id}: prior needs >=2 positive states summing to exactly 1")


@dataclass(frozen=True)
class Card:
    card_id: str
    question_id: str
    available_at: int  # first day the card may be seen or used
    likelihood: Mapping[str, Decimal]  # P(this evidence | state), authored


def visible(cards: Iterable[Card], day: int) -> list[Card]:
    """Cards whose evidence exists at ``day``; later cards are invisible, not merely hidden."""
    return [c for c in cards if c.available_at <= day]


def posterior(q: Question, cards: Iterable[Card], day: int) -> dict[str, Fraction]:
    """Exact posterior over ``q``'s states from the cards available by ``day`` (order-independent)."""
    weights = {s: Fraction(p) for s, p in q.prior.items()}
    seen: set[str] = set()
    for c in visible(cards, day):
        if c.question_id != q.question_id:
            continue
        if c.card_id in seen:
            raise ValueError(f"card {c.card_id} counted twice")
        seen.add(c.card_id)
        if set(c.likelihood) != set(q.prior) or any(v < 0 or v > 1 for v in c.likelihood.values()):
            raise ValueError(f"card {c.card_id}: likelihoods must cover every state within [0, 1]")
        weights = {s: w * Fraction(c.likelihood[s]) for s, w in weights.items()}
    total = sum(weights.values(), Fraction(0))
    if total == 0:
        raise ValueError(f"{q.question_id}: evidence is impossible under every state")
    return {s: w / total for s, w in weights.items()}


def shown(p: Mapping[str, Fraction]) -> dict[str, Decimal]:
    """Display values; the exact fractions remain the authority."""
    return {s: (Decimal(v.numerator) / Decimal(v.denominator)).quantize(SHOWN, rounding=ROUND_HALF_EVEN)
            for s, v in p.items()}


def brier(forecast: Mapping[str, Decimal], true_state: str) -> Fraction:
    """Multi-state Brier score: sum of squared errors, 0 (perfect) to 2 (certain and wrong)."""
    if true_state not in forecast or any(p < 0 for p in forecast.values()) or sum(forecast.values()) != 1:
        raise ValueError("forecast must cover the true state with non-negative probabilities summing to 1")
    return sum(((Fraction(p) - (1 if s == true_state else 0)) ** 2 for s, p in forecast.items()), Fraction(0))
