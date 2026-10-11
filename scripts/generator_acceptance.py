"""Measure how often generated Case1 tapes pass the balance gate, per generator Spec.

    cd backend && uv run python ../scripts/generator_acceptance.py [N]

Prints accepted/N and the failure counts for each candidate spec over seeds bench-0..bench-(N-1).
A measurement over a fixed seed list, not a probability claim.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from fundforge.balance import accept
from fundforge.generator import GEN_VERSION, Spec, generate
from fundforge.tape import compile_tape

SKELETON = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "case1.json").read_text(encoding="utf-8"))
SPECS = {
    "default": Spec(),
    "calmer": Spec(factor_bp=100, idio_bp=75, stress_multiplier=2),
    "quiet": Spec(factor_bp=60, idio_bp=50, stress_multiplier=2),
}

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    for name, spec in SPECS.items():
        failures: Counter[str] = Counter()
        accepted = 0
        for i in range(n):
            ok, report = accept(compile_tape(generate(f"bench-{i}", GEN_VERSION, SKELETON, spec)))
            accepted += ok
            failures.update(report["failures"])
        print(f"{name:8s} accepted {accepted}/{n}  failures {dict(failures)}")
