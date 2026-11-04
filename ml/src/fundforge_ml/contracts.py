"""Frozen cross-lane contracts.

Every lane (game, ML, platform, data) builds against these names. Change them only with a
``CONTRACT_VERSION`` bump and the affected lanes updated in the same change.

The observation rule is the important one: a model sees exactly what a partner sees. ``observe``
is the only sanctioned way to build an observation, and it is ``Session.view(user)`` plus a
check that no hidden-truth key is present before the debrief.
"""

import hashlib
from collections.abc import Iterator, Mapping
from typing import Any, Literal

from fundforge.governance import Session

CONTRACT_VERSION = "ml-contracts-2026.10.1"

SEATS: tuple[str, str] = ("pm", "mp")

Split = Literal["train", "val", "test"]
# Fixed salt, deliberately not CONTRACT_VERSION: bumping the contract must not reshuffle splits.
SPLIT_SALT = "fundforge-split-v1"

# Keys that carry hidden truth. They may appear in label tables and, after the run finishes,
# in the debrief outcome; never in an observation, feature row or live feature event before that.
HIDDEN_KEYS = frozenset({"variant", "seed", "gen_seed", "tape", "factors", "regime", "true_state"})

# Outbox audiences (ml/contracts/outbox_event.schema.json). Consumers building model inputs
# for a seat may read only "public" and that seat's events; "internal" is for audit/anomaly jobs.
AUDIENCES = ("public", "pm", "mp", "internal")


class LeakError(AssertionError):
    """A hidden-truth key reached something a model can read."""


def split_of(seed_family: str) -> Split:
    """Deterministic 80/10/10 split by seed family, so whole families of worlds are held out."""
    if not seed_family:
        raise ValueError("seed_family must be non-empty")
    bucket = int.from_bytes(hashlib.sha256(f"{SPLIT_SALT}|{seed_family}".encode()).digest()[:8], "big") % 10
    return "test" if bucket == 9 else "val" if bucket == 8 else "train"


def hidden_paths(obj: Any, path: str = "$") -> Iterator[str]:
    """Paths of every mapping key in ``obj`` that names hidden truth."""
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            here = f"{path}.{k}"
            if k in HIDDEN_KEYS:
                yield here
            yield from hidden_paths(v, here)
    elif isinstance(obj, list | tuple):
        for i, v in enumerate(obj):
            yield from hidden_paths(v, f"{path}[{i}]")


def observe(session: Session, user: str) -> dict[str, Any]:
    """The only sanctioned observation: the partner's as-of view.

    Before the run finishes, the view must contain no hidden-truth key. After it finishes the
    debrief ``outcome`` may reveal the variant, exactly as it does for a human player.
    """
    view = session.view(user)
    if not view["clock"]["finished"]:
        leaks = list(hidden_paths(view))
        if leaks:
            raise LeakError(f"hidden keys in a live observation: {leaks}")
    return view
