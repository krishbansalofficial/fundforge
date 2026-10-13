"""FundForgeEnv: Gymnasium API, determinism, masks, governance path, and the numeric leak canary."""

import dataclasses

import numpy as np
import pytest
from fundforge.tape import PHASES
from gymnasium.utils.env_checker import check_env

from fundforge_ml import worlds
from fundforge_ml.contracts import hidden_paths
from fundforge_ml.env import FundForgeEnv


def _play(env, seed, options, pick):
    obs, info = env.reset(seed=seed, options=options)
    trace, total = [obs], 0.0
    while True:
        obs, r, term, trunc, info = env.step(pick(env, info))
        trace.append(obs)
        total += r
        if term or trunc:
            return trace, total, info


def first_valid_nonwait(env, info):
    valid = np.flatnonzero(info["action_mask"])
    return int(valid[1]) if len(valid) > 1 else 0


def wait(env, info):
    return 0


@pytest.mark.parametrize("role", ["pm", "mp"])
def test_gymnasium_api(role):
    check_env(FundForgeEnv(role), skip_render_check=True)


@pytest.mark.parametrize("role", ["pm", "mp"])
def test_episode_runs_to_a_scored_finish(role):
    env = FundForgeEnv(role)
    _, total, info = _play(env, 0, {"variant": "base"}, wait)
    assert info["outcome"]["label"] in ("WIN", "SURVIVAL", "DISTRESS")
    assert total != 0.0
    env.s.e.reconcile()  # raises InvariantError if the books do not balance


def test_same_seed_and_actions_give_the_same_journal():
    a = _play(FundForgeEnv("pm"), 7, {"variant": "rally"}, first_valid_nonwait)
    b = _play(FundForgeEnv("pm"), 7, {"variant": "rally"}, first_valid_nonwait)
    assert a[2]["journal_digest"] == b[2]["journal_digest"]
    assert a[1] == b[1]
    assert all(np.array_equal(x, y) for x, y in zip(a[0], b[0], strict=True))


def test_trades_need_the_partners_signature_and_masked_actions_are_mostly_accepted():
    env = FundForgeEnv("pm")
    _obs, info = env.reset(seed=1, options={"variant": "base"})
    sell = env.actions.index(("reduce", ("ALTO", 0.25)))
    assert info["action_mask"][sell]
    _, _, _, _, info = env.step(sell)
    assert info["reject"] is None
    pkgs = env.s.packages.values()
    assert any(p.proposer == "pm" and p.signatures == {"pm", "mp"} for p in pkgs), "bot must countersign"
    assert any(o.sym == "ALTO" and o.side == "SELL" for o in env.s.e.orders)


def test_mask_follows_role():
    pm, mp = FundForgeEnv("pm"), FundForgeEnv("mp")
    _, ipm = pm.reset(seed=0, options={"variant": "base"})
    _, imp = mp.reset(seed=0, options={"variant": "base"})
    accept = pm.actions.index(("accept_replacement", None))
    assert not ipm["action_mask"][accept]
    research_pm = {a for a, ok in zip(pm.actions, ipm["action_mask"], strict=True) if ok and a[0] == "research"}
    research_mp = {a for a, ok in zip(mp.actions, imp["action_mask"], strict=True) if ok and a[0] == "research"}
    assert research_pm and research_mp and not research_pm & research_mp


def test_info_never_carries_hidden_keys_before_the_end():
    env = FundForgeEnv("mp")
    _, info = env.reset(seed=3, options={"variant": "rally"})
    while True:
        assert list(hidden_paths({k: v for k, v in info.items() if k != "action_mask"})) == []
        _obs, _r, term, trunc, info = env.step(first_valid_nonwait(env, info))
        if term or trunc:
            assert info["outcome"]["variant"] == "rally"  # revealed only in the debrief
            return


def _planted_world(variant):
    """The authored world with ALTO doubled from the last public mark on: only the future differs."""
    base = worlds.world(None, variant)
    events = list(base.tape.events)
    i = max(k for k, ev in enumerate(events) if ev.phase == "PUBLIC_MARK")
    ev = events[i]
    # every event carries its own marks, so the change must persist from the planted event onward
    for k in range(i, len(events)):
        events[k] = dataclasses.replace(events[k], marks={**events[k].marks, "ALTO": events[k].marks["ALTO"] * 2})
    return worlds.World(dataclasses.replace(base.tape, events=tuple(events)), None, variant), ev


@pytest.mark.parametrize("variant", ["base", "rally"])
def test_numeric_canary_future_marks_do_not_change_earlier_observations(variant):
    planted, ev = _planted_world(variant)
    clean = FundForgeEnv("pm", world_fn=lambda o, r: worlds.world(None, variant))
    dirty = FundForgeEnv("pm", world_fn=lambda o, r: planted)
    oc, ic = clean.reset(seed=0)
    od, idd = dirty.reset(seed=0)
    compared = 0
    planted_at = (ev.date, PHASES.index(ev.phase))
    while (dirty.s.e.ev.date, PHASES.index(dirty.s.e.ev.phase)) < planted_at and not dirty.s.e.finished():
        assert np.array_equal(oc, od), f"observation differs before the planted event at day {dirty.s.e.ev.day}"
        assert np.array_equal(ic["action_mask"], idd["action_mask"])
        compared += 1
        a = first_valid_nonwait(clean, ic)
        oc, *_, ic = clean.step(a)
        od, *_, idd = dirty.step(a)
    assert compared > 3
    if not np.array_equal(oc, od):  # the step that crossed the planted event may also end the run
        return
    while not dirty.s.e.finished():  # positive control: once the event is processed the mark is visible
        a = first_valid_nonwait(clean, ic)
        oc, *_, ic = clean.step(a)
        od, *_, idd = dirty.step(a)
        if not np.array_equal(oc, od):
            return
    pytest.fail("positive control failed: the planted mark never reached an observation")


def test_generated_world_respects_the_gate_and_family_split():
    w = worlds.world("env-test-1", "base", gate=False)
    assert w.seed_family.endswith("/env-test-1")
    env = FundForgeEnv("pm")
    obs, _ = env.reset(seed=0, options={"gen_seed": "env-test-1", "variant": "base", "gate": False})
    assert obs.shape == env.observation_space.shape
