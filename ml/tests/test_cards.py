"""MODEL_CARDS.md and DATA_CARD.md: every results link exists, and every number on a linked line is in that JSON.

Rule checked: on any card line that links ``](results/<name>.json)``, each number outside code spans and link
markup must equal some number in the linked JSON (values, numeric keys, or numbers inside string values) after
rounding the JSON number to the number of decimals shown. Lines without a results link are not checked.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest

ML = Path(__file__).resolve().parents[1]
CARDS = (ML / "MODEL_CARDS.md", ML / "DATA_CARD.md")
if not all(card.exists() for card in CARDS):  # the cards are local-only; a clean checkout has none
    pytest.skip("model and data cards are not in this checkout", allow_module_level=True)
LINK = re.compile(r"\[[^\]]*\]\((results/[^)\s]+\.json)\)")
CODE = re.compile(r"`[^`]*`")
# A number not glued to a word, a version string (2026.10.1) or a percent sign.
NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w%]|\.\d)")


def numbers(obj: Any) -> list[float]:
    """Every number in a JSON document: values, numeric-looking keys and numbers inside strings."""
    if isinstance(obj, bool):
        return []
    if isinstance(obj, int | float):
        return [float(obj)]
    if isinstance(obj, str):
        return [float(m) for m in NUM.findall(obj)]
    if isinstance(obj, dict):
        return [n for k, v in obj.items() for n in numbers(k) + numbers(v)]
    if isinstance(obj, list):
        return [n for v in obj for n in numbers(v)]
    return []


def linked_lines() -> list[tuple[str, int, str, list[str]]]:
    out = []
    for card in CARDS:
        for i, line in enumerate(card.read_text(encoding="utf-8").splitlines(), start=1):
            if links := LINK.findall(line):
                out.append((card.name, i, line, links))
    return out


def test_cards_exist_and_link_results():
    for card in CARDS:
        assert card.exists(), card
    assert len(linked_lines()) >= 20  # the check is not vacuous


@pytest.mark.parametrize("name,lineno,line,links", linked_lines(), ids=lambda x: str(x)[:40])
def test_linked_numbers_appear_in_the_json(name: str, lineno: int, line: str, links: list[str]):
    values: list[float] = []
    for link in links:
        path = ML / link
        assert path.exists(), f"{name}:{lineno} links missing {link}"
        values += numbers(json.loads(path.read_text(encoding="utf-8")))
    text = LINK.sub(" ", CODE.sub(" ", line))
    for token in NUM.findall(text):
        decimals = len(token.split(".")[1]) if "." in token else 0
        shown = float(token)
        tol = 0.5 * 10**-decimals + 1e-12
        assert any(abs(v - shown) <= tol for v in values), f"{name}:{lineno}: {token} not in {links}"
