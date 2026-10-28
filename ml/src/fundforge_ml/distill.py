"""VIPER-style policy distillation into a decision tree (Bastani et al. 2018, arXiv:1805.08328).

DAgger with weighted samples: roll out the current student, label every visited state with the
teacher's masked action, weight each state by how much the choice matters there, aggregate with
all earlier data and refit a ``DecisionTreeClassifier``. The first iteration rolls out the teacher.

Weight proxy. VIPER weights a state by ``V(s) - min_a Q(s, a)``, which needs a Q-function. PPO has
none: it has masked action logits and a state value V(s). We use the gap between the largest and
smallest masked log-probability over the valid actions. If the policy were the softmax of its
advantages at temperature tau (``pi(a|s) ~ exp(A(s, a) / tau)``), this gap would be
``(max_a A - min_a A) / tau``: VIPER's quantity, up to the unknown tau, with V(s) cancelling. PPO
with a small entropy bonus is only loosely like that, so treat the weight as a heuristic. A state
with a single valid action gets weight 0 (there is no choice to imitate). Samples are weighted in
the fit instead of resampled in proportion to weight: the same objective in expectation.

The student always respects the action mask: it plays the most probable *valid* action. Only
numpy and scikit-learn are used here; the PPO adapter lives in ``scripts/distill_viper.py``.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from .encoding import PHASES, Layout

Obs = npt.NDArray[np.float32]
Masks = npt.NDArray[np.bool_]
Teacher = Callable[[Obs, Masks], tuple[npt.NDArray[np.int64], npt.NDArray[np.float64]]]
"""(observations (N, D), masks (N, A)) -> (teacher's masked actions (N,), sample weights (N,))."""
Policy = Callable[[Obs, Masks], int]
"""(one observation (D,), one mask (A,)) -> action."""


def masked_argmax(scores: npt.ArrayLike, masks: Masks) -> npt.NDArray[np.int64]:
    """Row-wise argmax over valid actions only (lowest index on ties)."""
    s = np.where(masks, np.asarray(scores, dtype=np.float64), -np.inf)
    if not masks.any(axis=1).all():
        raise ValueError("every state needs at least one valid action")
    return s.argmax(axis=1).astype(np.int64)


def logit_gap(logits: npt.ArrayLike, masks: Masks) -> npt.NDArray[np.float64]:
    """Max minus min masked log-probability per row: the advantage-gap proxy described above."""
    lg = np.asarray(logits, dtype=np.float64)
    hi = np.where(masks, lg, -np.inf).max(axis=1)
    lo = np.where(masks, lg, np.inf).min(axis=1)
    return np.asarray(hi - lo, dtype=np.float64)


def feature_names(layout: Layout) -> list[str]:
    """Names for ``encoding.encode``'s vector, in its order."""
    names = ["role_pm", "role_mp", "day_frac"] + [f"phase_{p}" for p in PHASES]
    names += ["nav_ret", "cash/nav", "collateral/nav", "debt/nav", "credit_left/nav", "reserve/nav",
              "long_mv/nav", "short_mv/nav", "gross", "net", "maint_req/nav", "initial_req/nav",
              "margin_call/nav", "margin_call_flag"]
    for s in layout.instruments:
        names += [f"{s}.mv/nav", f"{s}.mark_ret", f"{s}.borrowed_frac", f"{s}.live_order"]
    names += ["recall_open", "recall_offer_visible", "recall_replacement_accepted", "recall_resolved"]
    for t in layout.topics:
        names += [f"research.{t}.mine", f"research.{t}.used", f"research.{t}.shared", f"research.{t}.seen"]
    names += ["firm_cash_ret", "payroll_payable/firm_cash", "pending_packages", "live_orders", "notices",
              "incidents"]
    if len(names) != layout.size:
        raise AssertionError(f"{len(names)} feature names for a layout of size {layout.size}")
    return names


def action_names(actions: Sequence[tuple[str, Any]]) -> list[str]:
    def one(kind: str, arg: Any) -> str:
        if arg is None:
            return kind
        return f"{kind}:{arg[0]}:{arg[1]}" if isinstance(arg, tuple) else f"{kind}:{arg}"
    return [one(k, a) for k, a in actions]


class Student:
    """A fitted tree that plays only valid actions."""

    def __init__(self, tree: Any, n_actions: int) -> None:
        self.tree, self.n_actions = tree, n_actions

    def probs(self, obs: Obs) -> npt.NDArray[np.float64]:
        p = np.zeros((len(obs), self.n_actions))
        p[:, self.tree.classes_] = self.tree.predict_proba(obs)
        return p

    def act_batch(self, obs: Obs, masks: Masks) -> npt.NDArray[np.int64]:
        return masked_argmax(self.probs(obs), masks)

    def __call__(self, obs: Obs, mask: Masks) -> int:
        return int(self.act_batch(obs[None], mask[None])[0])

    def size(self) -> dict[str, int]:
        return {"depth": int(self.tree.get_depth()), "leaves": int(self.tree.get_n_leaves()),
                "nodes": int(self.tree.tree_.node_count)}

    def rules(self, features: list[str], actions: list[str]) -> str:
        from sklearn.tree import export_text  # type: ignore[import-untyped,import-not-found,unused-ignore]

        text: str = export_text(self.tree, feature_names=features,
                                class_names=[actions[c] for c in self.tree.classes_], max_depth=64)
        return text


def fit_student(obs: Obs, labels: npt.ArrayLike, weights: npt.ArrayLike, n_actions: int, *, depth: int,
                seed: int = 0) -> Student:
    from sklearn.tree import DecisionTreeClassifier  # type: ignore[import-untyped,import-not-found,unused-ignore]

    w = np.asarray(weights, dtype=np.float64)
    if not (w > 0).any():  # every visited state had one valid action: any tree imitates the teacher
        w = np.ones_like(w)
    tree = DecisionTreeClassifier(max_depth=depth, random_state=seed)
    tree.fit(obs, np.asarray(labels), sample_weight=w)
    return Student(tree, n_actions)


@dataclass
class Episode:
    obs: Obs
    masks: Masks
    taken: npt.NDArray[np.int64]
    labels: npt.NDArray[np.int64]
    weights: npt.NDArray[np.float64]
    reward: float
    outcome: dict[str, Any]

    @property
    def agreement(self) -> float:
        return float((self.taken == self.labels).mean())


def rollout(env: Any, policy: Policy, teacher: Teacher, options: dict[str, Any], seed: int = 0) -> Episode:
    """Play one episode with ``policy`` and label every visited state with the teacher."""
    obs, _ = env.reset(seed=seed, options=options)
    xs: list[Obs] = []
    ms: list[Masks] = []
    taken: list[int] = []
    total, done, info = 0.0, False, {}
    while not done:
        m = env.action_masks()
        a = policy(obs, m)
        xs.append(obs)
        ms.append(m)
        taken.append(a)
        obs, r, term, trunc, info = env.step(a)
        total += float(r)
        done = term or trunc
    x, mk = np.stack(xs), np.stack(ms)
    labels, weights = teacher(x, mk)
    return Episode(x, mk, np.asarray(taken, dtype=np.int64), labels, weights, total, dict(info.get("outcome", {})))


def teacher_policy(teacher: Teacher) -> Policy:
    return lambda obs, mask: int(teacher(obs[None], mask[None])[0][0])


def viper(env: Any, worlds: Sequence[dict[str, Any]], teacher: Teacher, *, depth: int, iterations: int,
          seed: int = 0) -> tuple[list[Student], int]:
    """Students from every iteration (pick one on validation worlds) and the final dataset size.

    Each iteration plays every world in ``worlds`` once (env.reset options), so a deterministic
    policy on a deterministic world adds the states it actually reaches.
    """
    n_actions = int(env.action_space.n)
    xs: list[Obs] = []
    ys: list[npt.NDArray[np.int64]] = []
    ws: list[npt.NDArray[np.float64]] = []
    policy, students = teacher_policy(teacher), []
    for _ in range(iterations):
        for opts in worlds:
            ep = rollout(env, policy, teacher, opts)
            xs.append(ep.obs)
            ys.append(ep.labels)
            ws.append(ep.weights)
        student = fit_student(np.concatenate(xs), np.concatenate(ys), np.concatenate(ws), n_actions,
                              depth=depth, seed=seed)
        students.append(student)
        policy = student
    return students, int(sum(len(x) for x in xs))
