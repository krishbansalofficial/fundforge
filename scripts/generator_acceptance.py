"""Measure how often randomised Case1 worlds pass the balance gate, and record every rejected seed.

    cd backend && uv run python ../scripts/generator_acceptance.py [N] [rejects.json]

Plays seeds ``bench-0`` .. ``bench-(N-1)`` under ``SCENARIO_VERSION`` with the default ``Spec`` and
prints accepted/N, the failure counts, and the split of accepted seeds. Rejected seeds with their
failure codes are written to ``rejects.json`` when a path is given. A measurement over a fixed seed
list, not a probability claim.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from fundforge.balance import accept
from fundforge.engine import InvariantError
from fundforge.generator import SCENARIO_VERSION, Spec, generate, split_of
from fundforge.tape import compile_tape

SKELETON = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "case1.json").read_text(encoding="utf-8"))

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    rejects_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    failures: Counter[str] = Counter()
    rejected: list[dict[str, object]] = []
    accepted = Counter[str]()
    for i in range(n):
        seed = f"bench-{i}"
        try:
            ok, report = accept(compile_tape(generate(seed, SCENARIO_VERSION, SKELETON, Spec())))
        except InvariantError as err:  # the engine itself refused the world: a rejection, with its reason
            ok, report = False, {"failures": [f"engine_invariant:{str(err).split(' at day')[0]}"]}
        if ok:
            accepted[split_of(seed)] += 1
        else:
            failures.update(report["failures"])
            rejected.append({"seed": seed, "split": split_of(seed), "failures": report["failures"]})
    total = sum(accepted.values())
    print(f"{SCENARIO_VERSION} default  accepted {total}/{n} ({100 * total / n:.1f}%)")
    print(f"  accepted by split {dict(accepted)}")
    print(f"  failure codes over rejected seeds {dict(failures)}")
    if rejects_path:
        rejects_path.write_text(json.dumps(rejected, indent=1), encoding="utf-8")
        print(f"  rejected seeds written to {rejects_path}")
