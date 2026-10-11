"""Write the API's OpenAPI document to frontend/openapi.json, the source of frontend/app/api-types.ts.

    cd backend && uv run python ../scripts/export_openapi.py && cd ../frontend && npm run types

`backend/tests/test_openapi_file.py` fails while the committed JSON differs from the app, and the
frontend CI job fails while the generated types differ from the JSON.
"""

import json
from pathlib import Path

from fundforge.api import app

OUT = Path(__file__).resolve().parents[1] / "frontend" / "openapi.json"


def document() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    OUT.write_text(document(), encoding="utf-8")
    print(f"wrote {OUT}")
