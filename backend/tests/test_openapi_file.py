"""The committed OpenAPI document (source of the web desk's generated types) matches the running app."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "export_openapi.py"


def test_committed_openapi_document_is_current():
    spec = importlib.util.spec_from_file_location("export_openapi", SCRIPT)
    assert spec and spec.loader
    export = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export)
    assert export.OUT.read_text(encoding="utf-8") == export.document(), (
        "frontend/openapi.json is stale: run `uv run python ../scripts/export_openapi.py` from backend/, "
        "then `npm run types` in frontend/")
