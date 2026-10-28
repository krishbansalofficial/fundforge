"""Offline dataset (ML_CONTRACTS.md section 4): episodes through the real Session into Parquet.

Each episode is one ``FundForgeEnv`` run on a balance-gated world: the agent's seat is driven by a
simple policy, the other seat by ``bot:v1``. The output tables follow ``ml/contracts/dataset.schema.json``:

- ``episodes``, ``decisions``, ``labels``: the contract columns, plus ``split`` for partitioning.
  Hidden truth (variant, generated regimes) lives only in ``labels``.
- ``features``: the deciding seat's point-in-time features at every decision (``features.point_in_time``
  over the episode's outbox rows, cut at the room version the decision saw). Derived, not in the contract.
- ``rejections``: seeds the balance gate refused, with the gate's failure codes and the seed commitment
  (never the seed itself).

The generator seed never reaches a file: ``seed_family`` and the episode id carry a SHA-256 of the
family, and ``seed_commitment`` is the generator's commitment.
"""

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from fundforge import outbox
from fundforge.engine import RULES_VERSION, Engine
from fundforge.generator import GEN_VERSION, commitment
from fundforge.governance import Session

from . import features, worlds
from .contracts import split_of
from .env import FundForgeEnv

POLICIES = ("passive", "random_valid")
SCHEMA_PATH = Path(__file__).parents[2] / "contracts" / "dataset.schema.json"


@dataclass
class Tables:
    episodes: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    labels: list[dict[str, Any]] = field(default_factory=list)
    cutoffs: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    rejections: list[dict[str, Any]] = field(default_factory=list)


def family_hash(family: str) -> str:
    return hashlib.sha256(family.encode()).hexdigest()


def outbox_rows(room: str, s: Session, opening: dict[str, Any]) -> list[dict[str, Any]]:
    """The rows Store would write for this session's log, rebuilt after the fact.

    The journal, notices and incidents are append-only, so each log entry's ``after`` counts attribute
    every event to its command, exactly as Store does. No database is involved, so ``chain_head`` is a
    stand-in hash (the Store chain is verified by the backend, not by the dataset).
    """
    rows: list[dict[str, Any]] = []
    before = opening
    for seq, entry in enumerate(s.log, start=1):
        head = hashlib.sha256(f"{room}|{seq}".encode()).hexdigest()
        rows += outbox.rows_for(room, RULES_VERSION, s, seq, entry, before, head, False, last=seq == len(s.log))
        before = entry["after"]
    return rows


def play(world: worlds.World, policy: str, role: str = "pm", policy_seed: int = 0) -> Tables:
    """One episode. Model-facing data comes from ``observe`` only; the tape feeds ``labels`` alone."""
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}")
    family = world.seed_family
    fam = family_hash(family)
    seed_text = f"{world.gen_seed or 'authored'}|{world.variant}|{policy_seed}"
    episode_id = hashlib.sha256(f"{GEN_VERSION}|{fam}|{seed_text}|{policy}|{RULES_VERSION}".encode()).hexdigest()
    env = FundForgeEnv(role, policy_id=policy, world_fn=lambda _o, _r: world)
    env.reset(seed=policy_seed, options={"episode_tag": seed_text})
    assert env.s is not None
    probe = Engine(world.tape)  # the opening state before any command, derivable from the pinned tape
    probe.advance()
    opening = outbox.counts(Session(probe, {"pm": "a", "mp": "b"}))
    rng = np.random.default_rng(policy_seed)
    t = Tables()
    step, done = 0, False
    info: dict[str, Any] = {}
    while not done:
        view = env.view
        mask = env.action_masks()
        a = 0 if policy == "passive" else int(rng.choice(np.flatnonzero(mask)))
        cut = {
            "room_id": episode_id,
            "seat": role,
            "step": step,
            "as_of_seq": env.s.version,
            "as_of_day": view["clock"]["day"],
            "as_of_phase": view["clock"]["phase"],
        }
        cmd = env.command_for(a)
        _, reward, term, trunc, info = env.step(a)
        done = term or trunc
        t.cutoffs.append(cut)
        t.decisions.append(
            {
                "episode_id": episode_id,
                "seat": role,
                "step": step,
                "day": view["clock"]["day"],
                "phase": view["clock"]["phase"],
                "available_day": view["clock"]["day"],
                "obs": json.dumps(view, sort_keys=True, default=str),
                "action": None if cmd is None else json.dumps(cmd, sort_keys=True),
                "accepted": info["reject"] is None,
                "reject_code": info["reject"],
                "reward": f"{float(reward):.6f}",
            }
        )
        step += 1
    if "outcome" not in info:
        raise RuntimeError(f"episode {episode_id} ended without an outcome")
    out = info["outcome"]
    t.episodes.append(
        {
            "episode_id": episode_id,
            "seed_family": fam,
            "split": split_of(family),  # the same split training uses; only the hash reaches the file
            "gen_version": GEN_VERSION,
            "seed_commitment": commitment(world.gen_seed or "authored"),
            "scenario_id": world.tape.raw["scenario_id"],
            "rules_version": RULES_VERSION,
            "tape_digest": world.tape.digest,
            "policy_id": policy,
            "outcome_label": out["label"],
            "score": str(out["score"]),
            "nav": str(out["nav"]),
            "journal_digest": out["journal_digest"],
        }
    )
    t.labels.append({"episode_id": episode_id, "label": "variant", "value": world.variant, "known_at_day": None})
    for day, regime in world.tape.raw.get("generator", {}).get("regimes", []):
        t.labels.append({"episode_id": episode_id, "label": f"regime_day_{day}", "value": regime, "known_at_day": None})
    t.events = outbox_rows(episode_id, env.s, opening)
    return t


def generate(
    gen_seeds: Iterable[str], variants: Iterable[str], policies: Iterable[str] = POLICIES, role: str = "pm"
) -> Tables:
    acc = Tables()
    variants = list(variants)
    for gen_seed in gen_seeds:
        for variant in variants:
            try:
                world = worlds.world(gen_seed, variant)
            except worlds.WorldRejected as ex:
                acc.rejections.append(
                    {"seed_commitment": commitment(gen_seed), "variant": variant, "failures": ex.failures}
                )
                continue
            for i, policy in enumerate(policies):
                t = play(world, policy, role, policy_seed=i)
                for name in ("episodes", "decisions", "labels", "cutoffs", "events"):
                    getattr(acc, name).extend(getattr(t, name))
    return acc


def frames(t: Tables) -> dict[str, pl.DataFrame]:
    """Typed DataFrames for every table (contract columns, ``split`` added for partitioning)."""
    spec = json.loads(SCHEMA_PATH.read_text("utf-8"))["tables"]
    episodes = pl.DataFrame(t.episodes, schema={c: pl.String for c in spec["episodes"]["columns"]})
    split = episodes.select("episode_id", "split")
    decisions = pl.DataFrame(
        t.decisions,
        schema={
            "episode_id": pl.String,
            "seat": pl.String,
            "step": pl.Int64,
            "day": pl.Int64,
            "phase": pl.String,
            "available_day": pl.Int64,
            "obs": pl.String,
            "action": pl.String,
            "accepted": pl.Boolean,
            "reject_code": pl.String,
            "reward": pl.String,
        },
    )
    labels = pl.DataFrame(
        t.labels, schema={"episode_id": pl.String, "label": pl.String, "value": pl.String, "known_at_day": pl.Int64}
    )
    cut = pl.DataFrame(t.cutoffs, schema=features.CUTOFF_SCHEMA)
    feats = features.point_in_time(features.flatten(t.events), cut).rename({"room_id": "episode_id"})
    rejections = pl.DataFrame(
        t.rejections, schema={"seed_commitment": pl.String, "variant": pl.String, "failures": pl.List(pl.String)}
    )
    return {
        "episodes": episodes,
        "decisions": decisions.join(split, on="episode_id"),
        "labels": labels.join(split, on="episode_id"),
        "features": feats.join(split, on="episode_id"),
        "rejections": rejections,
    }


def write(t: Tables, out: Path) -> dict[str, int]:
    """Parquet under ``out/<table>/split=<split>/``; ``rejections`` is a single file."""
    sizes = {}
    for name, df in frames(t).items():
        sizes[name] = len(df)
        if name == "rejections":
            out.mkdir(parents=True, exist_ok=True)
            df.write_parquet(out / "rejections.parquet")
        else:
            df.write_parquet(out / name, partition_by="split")
    return sizes


def read(out: Path, table: str) -> pl.DataFrame:
    return pl.read_parquet(out / table / "**" / "*.parquet", hive_partitioning=True)
