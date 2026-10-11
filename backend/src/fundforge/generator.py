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

Pure domain: no I/O. Acceptance through the balance runner is a separate step.
"""

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any

from .money import CTX

GEN_VERSION = "gen-2026.10.1"
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

    def __post_init__(self) -> None:
        if min(self.factor_bp, self.idio_bp, self.switch_bp, self.stress_multiplier) < 0 or self.switch_bp > 10_000:
            raise ValueError("generator bounds must be non-negative and switch_bp at most 10000")
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
    return {**skeleton, "overrides": overrides,
            "generator": {"version": gen_version, "seed_commitment": commitment(seed),
                          "regimes": [[g["day"], g["regime"]] for g in generated]}}
