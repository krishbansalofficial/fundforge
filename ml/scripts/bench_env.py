"""Benchmark M1: FundForgeEnv throughput, single process and SB3 SubprocVecEnv, plus a cProfile breakdown.

Run from ml/:  uv run --group train python scripts/bench_env.py [--seeds 12] [--reps 5]

1. Gates generated seed families (``base-<n>``) for every variant; only accepted worlds are played.
   Workers rebuild the same deterministic worlds with ``gate=False`` (the parent already gated them).
2. Single process, each seat: a random policy over masked-valid actions plays ``--episodes`` whole
   episodes per repetition, after one untimed warm-up repetition. Determinism: one episode is
   played twice with the same seeds and must give the same journal digest.
3. Vectorised (pm seat): SubprocVecEnv at 1, 2, 4 and os.cpu_count() workers; each repetition is
   ``--vec-steps`` vector steps after an untimed warm-up. Episodes/s counts only completed episodes.
4. cProfile of one single-process repetition (pm): the top 10 functions by cumulative time, and
   the share of the root call's time spent in ``governance.snapshot`` (the rollback snapshot) and ``restore``.

Writes results/bench_env.json. Numbers hold for this machine, these seeds and this commit only.
"""

import argparse
import cProfile
import functools
import importlib.metadata as md
import json
import os
import platform
import pstats
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from fundforge.engine import RULES_VERSION

from fundforge_ml import worlds
from fundforge_ml.env import FundForgeEnv

OUT = Path(__file__).parents[1] / "results" / "bench_env.json"
Pair = tuple[str, str]  # (gen_seed, variant)


def accepted_worlds(n: int) -> tuple[list[Pair], dict[str, list[str]]]:
    ok: list[Pair] = []
    rejected: dict[str, list[str]] = {}
    for i in range(n):
        seed = f"base-{i}"
        try:
            for v in worlds.variant_names():
                worlds.world(seed, v)  # raises if the gate rejects it
            ok += [(seed, v) for v in worlds.variant_names()]
        except worlds.WorldRejected as ex:
            rejected[seed] = ex.failures
    return ok, rejected


class CycleWorlds:
    """Picks one of the pre-gated worlds per reset; picklable for SubprocVecEnv workers."""

    def __init__(self, pairs: list[Pair]) -> None:
        self.pairs = pairs

    def __call__(self, options: dict[str, Any], rng: np.random.Generator) -> worlds.World:
        seed, variant = self.pairs[int(rng.integers(len(self.pairs)))]
        return worlds.world(seed, variant, False)


def make_env(role: str, pairs: list[Pair]) -> FundForgeEnv:
    return FundForgeEnv(role, policy_id="random", world_fn=CycleWorlds(pairs))


def stats(xs: list[float]) -> dict[str, Any]:
    return {"median": round(statistics.median(xs), 2), "min": round(min(xs), 2), "max": round(max(xs), 2),
            "samples": [round(x, 2) for x in xs]}


def play(env: FundForgeEnv, episodes: int, rng: np.random.Generator, seed0: int) -> tuple[int, str]:
    """Plays whole episodes with a random masked-valid policy; returns (steps, last journal digest)."""
    steps, digest = 0, ""
    for k in range(episodes):
        _, info = env.reset(seed=seed0 + k)
        done = False
        while not done:
            a = int(rng.choice(np.flatnonzero(info["action_mask"])))
            _, _, term, trunc, info = env.step(a)
            steps += 1
            done = term or trunc
        digest = info.get("journal_digest", "")
    return steps, digest


def single(role: str, pairs: list[Pair], episodes: int, reps: int) -> dict[str, Any]:
    env = make_env(role, pairs)
    play(env, episodes, np.random.default_rng(0), 0)  # warm-up: world caches, imports
    d1 = play(env, 1, np.random.default_rng(7), 7)[1]
    d2 = play(env, 1, np.random.default_rng(7), 7)[1]
    sps, eps, spe = [], [], []
    for r in range(reps):
        t = time.perf_counter()
        n = play(env, episodes, np.random.default_rng(100 + r), 1000 * (r + 1))[0]
        dt = time.perf_counter() - t
        sps.append(n / dt)
        eps.append(episodes / dt)
        spe.append(n / episodes)
    return {"role": role, "episodes_per_rep": episodes, "deterministic": d1 == d2 and bool(d1),
            "steps_per_s": stats(sps), "episodes_per_s": stats(eps), "steps_per_episode": stats(spe)}


def vectorised(workers: int, pairs: list[Pair], vec_steps: int, reps: int, warmup: int) -> dict[str, Any]:
    from stable_baselines3.common.vec_env import SubprocVecEnv

    venv = SubprocVecEnv([functools.partial(make_env, "pm", pairs) for _ in range(workers)])
    try:
        venv.seed(0)
        venv.reset()
        masks = [i["action_mask"] for i in venv.reset_infos]
        rng = np.random.default_rng(0)

        def run(n: int) -> int:
            done_eps = 0
            for _ in range(n):
                acts = np.array([int(rng.choice(np.flatnonzero(m))) for m in masks])
                _, _, dones, infos = venv.step(acts)
                for i, d in enumerate(dones):
                    masks[i] = venv.reset_infos[i]["action_mask"] if d else infos[i]["action_mask"]
                done_eps += int(dones.sum())
            return done_eps

        run(warmup)
        sps, eps = [], []
        for _ in range(reps):
            t = time.perf_counter()
            n_eps = run(vec_steps)
            dt = time.perf_counter() - t
            sps.append(workers * vec_steps / dt)
            eps.append(n_eps / dt)
    finally:
        venv.close()
    return {"workers": workers, "vec_steps_per_rep": vec_steps, "steps_per_s": stats(sps),
            "episodes_per_s": stats(eps)}


def profile(pairs: list[Pair], episodes: int) -> dict[str, Any]:
    env = make_env("pm", pairs)
    play(env, 2, np.random.default_rng(0), 0)  # warm-up outside the profile
    prof = cProfile.Profile()
    prof.enable()
    play(env, episodes, np.random.default_rng(1), 500)
    prof.disable()
    st = pstats.Stats(prof)
    raw: dict[Any, Any] = st.stats  # type: ignore[attr-defined]
    total = max(v[3] for v in raw.values())  # cumulative time of the root call (play)

    def cum(path_end: str, name: str) -> float:
        return sum(v[3] for k, v in raw.items() if k[2] == name and k[0].replace("\\", "/").endswith(path_end))

    top = sorted(raw.items(), key=lambda kv: kv[1][3], reverse=True)[:10]
    return {
        "role": "pm", "episodes": episodes, "total_s": round(total, 3),
        "top10_cumulative": [
            {"function": f"{Path(k[0]).name}:{k[1]}({k[2]})", "ncalls": v[1], "tottime_s": round(v[2], 3),
             "cumtime_s": round(v[3], 3), "cum_share": round(v[3] / total, 3)} for k, v in top],
        "share_snapshot": round(cum("fundforge/governance.py", "snapshot") / total, 3),
        "share_restore": round(cum("fundforge/governance.py", "restore") / total, 3),
        "share_session_handle": round(cum("fundforge/governance.py", "handle") / total, 3),
    }


def _cmd(*args: str) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=30, check=False).stdout.strip()
    except OSError:
        return ""


def machine() -> dict[str, Any]:
    cpu, physical = platform.processor(), None
    if sys.platform == "win32":
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
            cpu = str(winreg.QueryValueEx(k, "ProcessorNameString")[0]).strip()
        out = _cmd("powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).NumberOfCores")
        physical = sum(int(x) for x in out.split()) if out else None
    elif Path("/proc/cpuinfo").exists():
        info = Path("/proc/cpuinfo").read_text()
        cpu = next((ln.split(":", 1)[1].strip() for ln in info.splitlines() if ln.startswith("model name")), cpu)
        ids = {tuple(ln for ln in blk.splitlines() if ln.startswith(("physical id", "core id")))
               for blk in info.split("\n\n")}
        physical = len(ids - {()}) or None
    pkgs = {}
    for p in ("fundforge", "fundforge-ml", "numpy", "gymnasium", "stable-baselines3", "torch"):
        try:
            pkgs[p] = md.version(p)
        except md.PackageNotFoundError:
            pkgs[p] = None
    root = Path(__file__).parents[2]
    return {"cpu": cpu, "logical_cores": os.cpu_count(), "physical_cores": physical,
            "os": platform.platform(), "python": platform.python_version(), "packages": pkgs,
            "commit": _cmd("git", "-C", str(root), "rev-parse", "HEAD"),
            "dirty": bool(_cmd("git", "-C", str(root), "status", "--porcelain")), "rules_version": RULES_VERSION}


def bench(pairs: list[Pair], *, roles: tuple[str, ...] = ("pm", "mp"), workers: list[int] | None = None,
          episodes: int = 20, vec_steps: int = 200, reps: int = 5, warmup: int = 20,
          profile_episodes: int = 10) -> dict[str, Any]:
    return {
        "single_process": [single(r, pairs, episodes, reps) for r in roles],
        "vectorised": [vectorised(w, pairs, vec_steps, reps, warmup) for w in (workers or [])],
        "profile": profile(pairs, profile_episodes) if profile_episodes else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=12, help="seed families to try through the gate")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--episodes", type=int, default=20, help="episodes per single-process repetition")
    ap.add_argument("--vec-steps", type=int, default=200, help="vector steps per vectorised repetition")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    t0 = time.perf_counter()
    pairs, rejected = accepted_worlds(args.seeds)
    print(f"gate: {len(pairs)} worlds accepted, {len(rejected)} families rejected ({time.perf_counter() - t0:.0f}s)")
    n = os.cpu_count() or 1
    workers = sorted({1, 2, 4, n})
    started = datetime.now(UTC).isoformat(timespec="seconds")
    result = bench(pairs, workers=workers, episodes=args.episodes, vec_steps=args.vec_steps, reps=args.reps)
    doc = {
        "benchmark": "M1 env throughput",
        "scope": "Numbers are for this machine, these seeds and this commit only; not portable to other hardware.",
        "reproduce": f"cd ml && uv run --group train python scripts/bench_env.py --seeds {args.seeds} "
                     f"--reps {args.reps} --episodes {args.episodes} --vec-steps {args.vec_steps}",
        "date": started, "machine": machine(),
        "worlds": {"accepted": [f"{s}/{v}" for s, v in pairs], "rejected": rejected},
        "policy": "uniform random over masked-valid actions (seeded); bot:v1 plays the other seat",
        "method": {"reps": args.reps, "warmup": "one untimed repetition (single) / 20 vector steps (vectorised)",
                   "statistic": "median with min and max over repetitions",
                   "vectorised_seat": "pm", "vectorised_episodes": "completed episodes only"},
        **result,
    }
    args.out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("single_process", "vectorised")}, indent=1))
    print(json.dumps(doc["profile"], indent=1))


if __name__ == "__main__":
    main()
