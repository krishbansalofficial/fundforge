"""The engine side never depends on ML (DECISIONS.md, 13 Oct 2026).

`lint-imports` enforces this on the import graph in CI; this source scan also catches dynamic
imports and string references, and runs with plain pytest.
"""

import ast
from pathlib import Path

BACKEND = Path(__file__).parents[2] / "backend" / "src" / "fundforge"


def test_backend_never_imports_fundforge_ml():
    offenders = []
    files = sorted(BACKEND.rglob("*.py"))
    assert files, f"no backend sources under {BACKEND}"
    for f in files:
        text = f.read_text(encoding="utf-8")
        if "fundforge_ml" in text:
            offenders.append(str(f))
            continue
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Import):
                offenders += [f"{f}: {a.name}" for a in node.names if a.name.split(".")[0] == "fundforge_ml"]
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "fundforge_ml":
                offenders.append(f"{f}: {node.module}")
    assert offenders == []
