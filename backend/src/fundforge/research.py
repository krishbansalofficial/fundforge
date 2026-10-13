"""Research as a skill (ROADMAP P4): hidden discrete states, authored evidence, exact Bayes and Brier scores.

Each research question has a hidden true state drawn from published priors. Evidence cards
carry authored likelihoods P(card | state) as Decimal strings; only their ratios matter.
Posteriors are computed exactly with ``Fraction`` (Decimal division would round) and shown
as 6dp HALF_EVEN Decimals. A card is usable only once its ``available_at`` day has arrived,
so a posterior can never contain future evidence. Thesis tickets are scored with the
multi-state Brier score, reported beside P&L and never inside it.

Generated markets ask one live question: was the hidden regime stressed on the latest period
whose Street activity print is published? ``regime_filter`` answers it with an exact forward
filter (a two-state hidden Markov model) over the published prints; see its docstring.

Pure domain: no engine, journal or I/O imports.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from typing import Any

from .asof import Observation
from .generator import Spec

SHOWN = Decimal("0.000001")
REGIMES = ("calm", "stressed")


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


def question_id(period_day: int) -> str:
    return f"regime:{period_day}"


def _likelihood(value: Decimal, level: int, bound: int) -> Fraction:
    """P(print | state): the generator adds uniform integer noise in [-bound, bound] tenths."""
    tenths = value * 10
    if tenths != tenths.to_integral_value():
        raise ValueError(f"print {value} is not a whole number of tenths")
    return Fraction(1, 2 * bound + 1) if abs(int(tenths) - level) <= bound else Fraction(0)


def regime_filter(prints: Sequence[Observation], spec: Spec) -> list[tuple[dict[str, Fraction], dict[str, Fraction]]]:
    """Exact forward filter over consecutive generated days: ``(published prior, posterior)`` per print.

    The generator starts calm before its first generated day and, at each generated day, flips the
    regime with probability ``p = switch_bp / 10000``, then prints that day's level plus noise.
    So the published prior for the k-th generated day is the chain alone: P(stressed) = (1 - (1-2p)^k) / 2
    (3/20 on the first day by default). The posterior predicts yesterday's belief one step and multiplies
    by the print's likelihood: 1/(2b+1) if the print is within ``b`` tenths of the state's level, else 0,
    with ``b`` the first-print bound, or the revision bound when ``prints`` carries a revision. Callers pass
    each day's latest available revision only, so a revision replaces its first print, never adds to it.
    Prints must be every generated day up to the newest, oldest first: the as-of view guarantees this,
    because every generated day prints with the same lag.
    """
    p = Fraction(spec.switch_bp, 10_000)
    level = {"calm": spec.macro_level + spec.macro_regime, "stressed": spec.macro_level - spec.macro_regime}

    def step(b: dict[str, Fraction]) -> dict[str, Fraction]:
        return {"calm": b["calm"] * (1 - p) + b["stressed"] * p, "stressed": b["stressed"] * (1 - p) + b["calm"] * p}

    belief = chain = {"calm": Fraction(1), "stressed": Fraction(0)}
    out = []
    for o in prints:
        chain = step(chain)
        bound = spec.macro_revised_noise if o.revision else spec.macro_first_noise
        weights = {s: w * _likelihood(o.value, level[s], bound) for s, w in step(belief).items()}
        total = sum(weights.values(), Fraction(0))
        if total == 0:
            raise ValueError(f"print {o.value} for day {o.event_time} is impossible under every regime")
        belief = {s: w / total for s, w in weights.items()}
        out.append((chain, belief))
    return out


def regime_question(known: Sequence[Observation], spec: Spec) -> dict[str, Any] | None:
    """The live research question from the published prints only (``AsOfTape.known``), or None before any."""
    if not known:
        return None
    prior, post = regime_filter(known, spec)[-1]
    day = known[-1].event_time
    return {"question": question_id(day), "period_day": day, "states": list(REGIMES),
            "prior": {s: str(v) for s, v in shown(prior).items()},
            "posterior": {s: str(v) for s, v in shown(post).items()},
            "evidence": len(known),
            "method": "Exact forward filter over every published print (latest revision only); "
                      "prior is the regime chain alone. Shown to 6dp."}
