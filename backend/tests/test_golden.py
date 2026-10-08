"""Cross-version replay guard: scripted paths must reproduce committed journal digests.

Changing economic rules requires bumping engine.RULES_VERSION and regenerating
tests/golden.json in the same commit:  uv run python tests/test_golden.py --write
"""

import json
import sys
from pathlib import Path

from fundforge.engine import RULES_VERSION
from test_engine import S1, S2, run, s2_accept, s2_research

GOLDEN = Path(__file__).with_name("golden.json")
PATHS = {
    "S1_early_reduction": S1,
    "S2_replacement_and_cure": S2,
    "F1_inaction": {},
    "F2_replacement_without_cure": {(12, "EXEC_A"): s2_research, (14, "EXEC_A"): s2_accept},
}


def compute() -> dict:
    out = {}
    for name, script in PATHS.items():
        o = run(script).outcome()
        out[name] = {"label": o["label"], "nav": o["nav"], "journal_digest": o["journal_digest"]}
    return {"rules_version": RULES_VERSION, "tape_digest": run({}).tape.digest, "paths": out}


def test_scripted_paths_match_committed_golden_digests():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden["rules_version"] == RULES_VERSION, "rules changed: bump RULES_VERSION and regenerate goldens"
    assert compute() == golden


if __name__ == "__main__" and "--write" in sys.argv:
    GOLDEN.write_text(json.dumps(compute(), indent=2) + "\n", encoding="utf-8")
