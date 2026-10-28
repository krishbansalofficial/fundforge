"""VIPER distillation: masked student, weight proxy, feature names, and a tiny end-to-end loop."""

import numpy as np
import pytest

pytest.importorskip("sklearn")

from fundforge_ml import distill
from fundforge_ml.env import FundForgeEnv


def test_masked_argmax_and_gap_ignore_invalid_actions():
    logits = np.array([[5.0, 1.0, -3.0], [0.0, 9.0, 2.0]])
    masks = np.array([[False, True, True], [True, False, False]])
    assert distill.masked_argmax(logits, masks).tolist() == [1, 0]
    assert distill.logit_gap(logits, masks).tolist() == [4.0, 0.0]


def last_valid_teacher(obs, masks):
    """Synthetic teacher: the highest-index valid action, weight 1."""
    return np.array([np.flatnonzero(m)[-1] for m in masks], dtype=np.int64), np.ones(len(masks))


def test_viper_student_respects_masks_and_names_features():
    env = FundForgeEnv("pm")
    assert len(distill.feature_names(env.layout)) == env.layout.size
    worlds = [{"gen_seed": None, "variant": v} for v in ("base", "rally")]
    students, n = distill.viper(env, worlds, last_valid_teacher, depth=3, iterations=2)
    assert len(students) == 2 and n > 0
    st = students[-1]
    for o in worlds:
        ep = distill.rollout(env, st, last_valid_teacher, o)
        assert ep.masks[np.arange(len(ep.taken)), ep.taken].all(), "student played a masked action"
    rules = st.rules(distill.feature_names(env.layout), distill.action_names(env.actions))
    assert "class:" in rules
    # an all-invalid-but-one mask forces the student's hand even where the tree disagrees
    only = np.zeros(env.action_space.n, dtype=bool)
    only[0] = True
    assert st(ep.obs[0], only) == 0
