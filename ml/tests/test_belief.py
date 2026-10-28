"""Belief wrapper: seat-terminal parity, future-print canary, and one observation shape for all modes."""

import copy
import dataclasses
from decimal import Decimal

import numpy as np
import pytest
from fundforge.terminal import snapshot

from fundforge_ml import forecast, worlds
from fundforge_ml.belief import MODES, BeliefWrapper, Logistic
from fundforge_ml.env import FundForgeEnv

SEED = "forecast-test-1"
# a fixed, untrained forecaster: leans on the newest print's scaled deviation
LEARNED = Logistic(np.r_[-3.0, np.zeros(3 * forecast.WINDOW), -1.0])


def _env(world: worlds.World, mode: str) -> BeliefWrapper:
    return BeliefWrapper(FundForgeEnv("pm", world_fn=lambda o, r: world), mode,
                         LEARNED if mode == "learned" else None)


def _run(world: worlds.World, mode: str) -> list[tuple[int, np.ndarray]]:
    """(as-of day, observation) at every decision point of a wait-only episode."""
    env = _env(world, mode)
    obs, _ = env.reset(seed=0)
    out, done = [], False
    while not done:
        out.append((env.base.view["clock"]["day"], obs))
        obs, _, term, trunc, _ = env.step(0)
        done = term or trunc
    return out


def test_belief_rows_and_exact_posterior_match_the_seat_terminal():
    env = _env(worlds.world(SEED, "base", gate=False), "exact")
    obs, _ = env.reset(seed=0)
    checked = done = 0
    while not done:
        term = snapshot(env.base.s.e, env.base.role)
        assert env.rows() == term["macro"]
        if term["regime"] is None:
            assert obs[-1] == 0.0
        else:
            assert abs(Decimal(float(obs[-1])) - Decimal(term["regime"]["posterior"]["stressed"])) < Decimal("1e-6")
            checked += 1
        obs, _, t, tr, _ = env.step(0)
        done = t or tr
    assert checked > 0


def test_canary_future_macro_print_never_changes_the_belief():
    honest = worlds.world(SEED, "base", gate=False)
    cut = 15  # alter every print published after day 15
    raw = copy.deepcopy(honest.tape.raw)
    calm, stressed = (str(Decimal(forecast.SPEC.macro_level + s * forecast.SPEC.macro_regime) / 10) for s in (1, -1))
    altered = 0
    for o in raw["macro"]:
        if o["available_at"] > cut:
            o["value"] = stressed if Decimal(o["value"]) * 10 > forecast.SPEC.macro_level else calm
            altered += 1
    assert altered
    tampered = worlds.World(dataclasses.replace(honest.tape, raw=raw), honest.gen_seed, honest.variant)
    for mode in ("learned", "exact"):
        a, b = _run(honest, mode), _run(tampered, mode)
        assert [d for d, _ in a] == [d for d, _ in b]
        before = [(x, y) for (d, x), (_, y) in zip(a, b, strict=True) if d <= cut]
        after = [(x, y) for (d, x), (_, y) in zip(a, b, strict=True) if d > cut]
        assert before and all(np.array_equal(x, y) for x, y in before), f"{mode}: future print leaked"
        # positive control: once published, the altered print does move the belief
        assert any(x[-1] != y[-1] for x, y in after), f"{mode}: canary scan cannot see a change"


def test_modes_share_one_shape_and_none_is_constant():
    w = worlds.world(SEED, "base", gate=False)
    runs = {m: _run(w, m) for m in MODES}
    base = FundForgeEnv("pm").observation_space.shape[0]
    for m, run in runs.items():
        assert all(obs.shape == (base + 1,) and obs.dtype == np.float32 for _, obs in run), m
        assert all(np.array_equal(obs[:-1], o2[:-1]) for (_, obs), (_, o2) in zip(run, runs["none"], strict=True))
    assert {float(obs[-1]) for _, obs in runs["none"]} == {0.0}
    assert len({float(obs[-1]) for _, obs in runs["exact"]}) > 1
    with pytest.raises(ValueError):
        BeliefWrapper(FundForgeEnv("pm"), "learned")
    with pytest.raises(ValueError):
        BeliefWrapper(FundForgeEnv("pm"), "exact", LEARNED)
