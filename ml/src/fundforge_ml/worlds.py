"""Worlds an agent can be dropped into: the authored Case1 tape or a generated one.

A world is ``(gen_seed, variant)``. ``gen_seed=None`` is the authored tape. A generated world is
built by ``fundforge.generator`` from the authored skeleton and, by default, must pass the
balance acceptance gate (``fundforge.balance.accept``) before any agent plays it, exactly like a
room. Rejected seeds raise ``WorldRejected`` with the gate's failure codes, so callers can record
them instead of silently dropping them (ML_CONTRACTS.md section 4).
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fundforge.balance import accept
from fundforge.generator import GEN_VERSION, generate
from fundforge.tape import Tape, compile_tape, variants

FIXTURE = Path(__file__).parents[3] / "fixtures" / "case1.json"


class WorldRejected(ValueError):
    def __init__(self, gen_seed: str, variant: str, failures: list[str]) -> None:
        super().__init__(f"world {gen_seed!r}/{variant} rejected by the balance gate: {failures}")
        self.gen_seed, self.variant, self.failures = gen_seed, variant, failures


@dataclass(frozen=True)
class World:
    tape: Tape
    gen_seed: str | None
    variant: str

    @property
    def seed_family(self) -> str:
        """The unit of train/val/test splitting: all variants of one generated seed stay together."""
        return f"{self.tape.raw['scenario_id']}/authored" if self.gen_seed is None else (
            f"{self.tape.raw['scenario_id']}/{GEN_VERSION}/{self.gen_seed}")


@lru_cache(maxsize=1)
def skeleton() -> dict:  # type: ignore[type-arg]
    return json.loads(FIXTURE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def variant_names() -> list[str]:
    return variants(skeleton())


@lru_cache(maxsize=4096)
def world(gen_seed: str | None, variant: str, gate: bool = True) -> World:
    raw = skeleton() if gen_seed is None else generate(gen_seed, GEN_VERSION, skeleton())
    tape = compile_tape(raw, variant)
    if gen_seed is not None and gate:
        ok, report = accept(tape)
        if not ok:
            raise WorldRejected(gen_seed, variant, list(report["failures"]))
    return World(tape, gen_seed, variant)
