"""Seeded market generator (ROADMAP P4): ``generate(seed, gen_version, skeleton, spec) -> raw``.

Randomness is a SHA-256 counter stream: draw ``n`` hashes ``gen_version|seed|n`` and turn them
into integers by rejection sampling (no modulo bias, no floats). Shocks are whole basis points,
so every price step is exact Decimal arithmetic, quantized once to 6dp HALF_EVEN.

The skeleton's authored overrides (crisis marks, volumes, headlines) are fixed hidden inputs and
are never changed. Each unauthored ``PUBLIC_MARK`` gets one market-factor shock (scaled by
the current calm/stressed regime and each instrument's beta) plus an idiosyncratic shock;
later days continue from whatever the last authored or generated mark was. The output records
only a SHA-256 commitment to the seed; the seed stays server-side until the debrief, when
anyone can check it against the commitment and regenerate the tape.

Each generated day also prints a fictional Street activity index: the hidden regime's level plus
noise, published the next day. Some prints get a more accurate revision three days later. It reads
a separate ``MACRO_VERSION`` stream, so adding it never changes the generated marks.

Pure domain: no I/O. Acceptance through the balance runner is a separate step.
"""

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any

from .money import CTX

GEN_VERSION = "gen-2026.10.1"
MACRO_VERSION = "macro-2026.10.2"
MACRO_SERIES = "STREET_ACTIVITY"
TENTH = Decimal("0.1")
PRICE = Decimal("0.000001")
BP = Decimal("0.0001")


class Stream:
    """Deterministic integers from SHA-256(gen_version|seed|counter)."""

    def __init__(self, seed: str, gen_version: str):
        self.prefix = f"{gen_version}|{seed}|".encode()
        self.counter = 0

    def _word(self) -> int:
        digest = hashlib.sha256(self.prefix + str(self.counter).encode()).digest()
        self.counter += 1
        return int.from_bytes(digest[:8], "big")

    def integer(self, lo: int, hi: int) -> int:
        """Uniform on [lo, hi] inclusive; rejects the top partial block so there is no modulo bias."""
        if hi < lo:
            raise ValueError("empty range")
        span = hi - lo + 1
        limit = (1 << 64) - (1 << 64) % span
        while True:
            w = self._word()
            if w < limit:
                return lo + w % span


@dataclass(frozen=True)
class Spec:
    factor_bp: int = 150  # calm market-factor shock bound per public mark
    stress_multiplier: int = 3  # stressed regime scales the factor bound
    idio_bp: int = 100  # idiosyncratic shock bound
    switch_bp: int = 1500  # probability (bp) of switching regime at each public mark
    beta: Mapping[str, Decimal] = field(default_factory=lambda: {"BOND": Decimal(0)})  # default beta is 1
    # Street activity index, in tenths of a point: calm prints near 52.5, stressed near 47.5.
    macro_level: int = 500
    macro_regime: int = 25
    # first print error bound; wider than half the calm/stressed gap, so a print in the overlap is ambiguous
    macro_first_noise: int = 40
    macro_revised_noise: int = 5  # revisions are closer to the hidden level
    macro_revise_bp: int = 3000  # probability (bp) that a print is revised
    macro_lag: int = 1  # days from the period to its first print
    macro_revision_lag: int = 3

    def __post_init__(self) -> None:
        if min(self.factor_bp, self.idio_bp, self.switch_bp, self.stress_multiplier) < 0 or self.switch_bp > 10_000:
            raise ValueError("generator bounds must be non-negative and switch_bp at most 10000")
        if not 0 <= self.macro_revise_bp <= 10_000 or not 1 <= self.macro_lag < self.macro_revision_lag:
            # a same-day print would come before that day's mark
            raise ValueError("macro needs revise_bp in 0..10000 and 1 <= lag < revision lag")
        worst_beta = max([Decimal(1), *(abs(b) for b in self.beta.values())])
        if worst_beta * self.factor_bp * self.stress_multiplier + self.idio_bp >= 10_000:
            raise ValueError("a single step could take a mark to zero")


def commitment(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def generate(seed: str, gen_version: str, skeleton: dict[str, Any], spec: Spec | None = None) -> dict[str, Any]:
    """A new raw tape: the skeleton with generated public marks on every unauthored day."""
    spec = spec or Spec()
    rng = Stream(seed, gen_version)
    syms = list(skeleton["instruments"])
    cal = skeleton["calendar"]
    authored = {(o["day"], o["event"]): o for o in skeleton["overrides"]}
    marks = {s: Decimal(skeleton["defaults"]["mark"]) for s in syms}
    stressed = False
    generated: list[dict[str, Any]] = []
    with localcontext(CTX):
        for day in range(cal["start_day"], cal["end_day"]):
            for event in ("OPEN_ADMIN", "PUBLIC_MARK", "EXEC_A", "EXEC_B", "CLOSE"):
                fixed = authored.get((day, event), {}).get("marks", {})
                marks.update({s: Decimal(v) for s, v in fixed.items()})
                if event != "PUBLIC_MARK" or fixed:
                    continue
                if rng.integer(0, 9_999) < spec.switch_bp:
                    stressed = not stressed
                bound = spec.factor_bp * (spec.stress_multiplier if stressed else 1)
                factor = rng.integer(-bound, bound) * BP
                for s in syms:
                    step = spec.beta.get(s, Decimal(1)) * factor + rng.integer(-spec.idio_bp, spec.idio_bp) * BP
                    marks[s] = (marks[s] * (1 + step)).quantize(PRICE, rounding=ROUND_HALF_EVEN)
                generated.append({"day": day, "event": event, "marks": {s: str(marks[s]) for s in syms},
                                  "regime": "stressed" if stressed else "calm"})
    overrides = [*skeleton["overrides"], *({k: v for k, v in g.items() if k != "regime"} for g in generated)]
    regimes = [[g["day"], g["regime"]] for g in generated]
    return {**skeleton, "overrides": overrides, "macro": macro(seed, regimes, spec),
            "generator": {"version": gen_version, "seed_commitment": commitment(seed), "regimes": regimes}}


def macro(seed: str, regimes: list[list[Any]], spec: Spec) -> list[dict[str, Any]]:
    """As-of observations of the Street activity index for each generated day (``asof.Observation`` fields)."""
    rng = Stream(seed, MACRO_VERSION)
    out: list[dict[str, Any]] = []
    for day, regime in regimes:
        level = spec.macro_level + (spec.macro_regime if regime == "calm" else -spec.macro_regime)
        prints = [level + rng.integer(-spec.macro_first_noise, spec.macro_first_noise)]
        if rng.integer(0, 9_999) < spec.macro_revise_bp:
            prints.append(level + rng.integer(-spec.macro_revised_noise, spec.macro_revised_noise))
        for rev, tenths in enumerate(prints):
            out.append({"instrument": MACRO_SERIES, "event_time": day, "revision": rev,
                        "available_at": day + (spec.macro_revision_lag if rev else spec.macro_lag),
                        "value": str(tenths * TENTH)})
    return out
