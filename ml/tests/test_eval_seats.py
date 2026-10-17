"""Evaluation harness: two-seat play, baselines and the family bootstrap.

Needs the training group (`uv sync --group train`); skipped otherwise, as in CI.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sb3_contrib")

from sb3_contrib import MaskablePPO

from fundforge_ml import worlds
from fundforge_ml.env import FundForgeEnv

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from eval_seats import evaluate, evaluate_two, family_bootstrap, pairs_of, play_single, play_two


@pytest.fixture(scope="module")
def tiny_model() -> MaskablePPO:
    env = FundForgeEnv("pm", world_fn=lambda o, r: worlds.world(None, "base"))
    return MaskablePPO("MlpPolicy", env, n_steps=64, batch_size=32, seed=0, verbose=0, device="cpu")


def test_two_seat_episode_finishes_on_authored_world(tiny_model: MaskablePPO):
    r = play_two(tiny_model, tiny_model, None, "base", 0)
    assert r["label"] in ("WIN", "SURVIVAL", "DISTRESS")
    assert not r["stuck"]
    assert np.isfinite(r["reward"])


def test_single_seat_policies_are_reproducible(tiny_model: MaskablePPO):
    a = play_single("pm", None, "base", "random", None, 3)
    b = play_single("pm", None, "base", "random", None, 3)
    assert a == b
    assert play_single("mp", None, "base", "wait", None, 0)["label"] in ("WIN", "SURVIVAL", "DISTRESS")


def test_evaluate_counts_random_runs_per_world(tiny_model: MaskablePPO):
    pairs = [(None, "base")]  # type: ignore[list-item]
    rep = evaluate("pm", tiny_model, pairs, ("random", "wait"))
    assert rep["random"]["n_runs"] == 5 and rep["random"]["n_worlds"] == 1
    assert rep["wait"]["n_runs"] == 1


def test_two_seat_report_has_counts(tiny_model: MaskablePPO):
    rep = evaluate_two(tiny_model, tiny_model, [(None, "base")])  # type: ignore[list-item]
    assert rep["n_runs"] == 1 and rep["stuck_runs"] == 0


def test_family_bootstrap_interval_brackets_mean_and_is_seeded():
    per = {"f1": [1.0, 1.2], "f2": [0.0], "f3": [2.0, 2.2, 1.8]}
    ci = family_bootstrap(per)
    means = [np.mean(v) for v in per.values()]
    assert ci["lo"] <= float(np.mean(means)) <= ci["hi"]
    assert family_bootstrap(per) == ci


def test_pairs_of_never_mixes_splits():
    fams = {"train": ["a"], "val": ["b"], "test": ["c"]}
    assert pairs_of("test", fams) == [("c", v) for v in worlds.variant_names()]
