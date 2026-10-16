# Benchmarks

Written 13 October 2026. This document says what FundForge measures, how, and where each result lives. It follows the CLAUDE.md rule: no number is stated anywhere (README, ENGINEERING, a resume) unless a result file or a CI log in this repository produced it.

## Audit: what was measured before this document

| Claim or tool | State on 13 Oct 2026 |
|---|---|
| Prometheus `command_seconds` and `replay_seconds` histograms, Grafana JSON | Implemented (P2 observability). They observe a running server; no load was ever driven through them and no result was recorded. |
| "Case1 replay about 10 ms" (ROADMAP decisions table) | One informal measurement with no commit, machine or method recorded. Superseded by B1. |
| 60 fps budget on mid hardware (ROADMAP P3 acceptance, WORLD_GAME_PLAN) | Never measured. TERMINAL.md states that no performance benchmark is claimed. |
| Worst frame reduced from 2.1 s to 16.9 ms after tracing a shader compile | No trace, capture, commit or hardware record exists in the repository. Reproduce it under B4 or stop stating it. |
| Load test, Postgres command latency, control detection rate, mutation score | Not measured. |

Conclusion: until B1 below, FundForge had correctness evidence (tests, goldens, verify) but no performance or detection benchmark.

## Suite

Each benchmark has one question, one method, a result location and a status. A **target** is a design goal, not a result; it becomes a result only when a recorded run meets it.

### B1: Engine season and independent controls (implemented)

**Question.** How long does the pure engine take to run a full Case1 season, and how long does the independent control report take? This is the CPU cost inside every room replay, before any Postgres I/O.

**Method.** `scripts/bench_engine.py` runs the four golden paths (S1, S2, F1, F2) with 3 warmups and 50 timed samples each, calls `outcome()` and `control_report()`, and refuses to report if the journal digest differs between samples. Each run writes `bench/results/<date>-B1-<commit>.json` with commit, rules version, Python version and machine.

```bash
cd backend
uv run python ../scripts/bench_engine.py --out ../bench/results
uv run python ../scripts/bench_engine.py --compare ../bench/results/<baseline>.json   # exits 1 on regression
```

**First result** (commit `3cbd8f3`, rules `case1-rules-2026.10.8`, Python 3.13.16, Linux x86_64, Intel Xeon @ 2.80GHz, 2 logical CPUs, shared cloud sandbox). Journal digests equal `backend/tests/golden.json`.

| Path | Season min | Season p50 | Season p95 | `control_report` p50 |
|---|---|---|---|---|
| S1 early reduction | 17.08 ms | 17.48 ms | 20.28 ms | 0.49 ms |
| S2 replacement and cure | 17.77 ms | 18.82 ms | 24.48 ms | 0.51 ms |
| F1 inaction | 17.19 ms | 18.23 ms | 24.53 ms | 0.48 ms |
| F2 replacement without cure | 17.76 ms | 19.87 ms | 29.68 ms | 0.54 ms |

**Noise finding.** On this 2 CPU shared machine the median of the same code moved between about 18 ms and 30 ms across consecutive runs, and a median based gate flagged a false 1.87x regression. The fastest sample stayed within 4% across three repeated comparisons. The regression gate therefore compares the minimum, with a 25% tolerance. A negative check that added 8 ms of sleep per season was flagged on all four paths (1.50x to 1.53x).

**Next.** Wire B1 into CI as an A/B job: check out the PR base and head in the same job on the same runner, run both, and fail on regression. Comparing against a result file from another machine is meaningless.

### B2: Store command latency and replay with Postgres (implemented; local result only, no CI run)

**Question.** What do accepted commands and cold room replays cost end to end, including the row lock, idempotency check, hash chain and journal insert?

**Method.** `scripts/bench_store.py` (needs `DATABASE_URL` pointing at a scratch database: it creates rooms, and the append-only triggers keep them) drives the S2 golden path as partner commands (MP borrow research at day 12, MP replacement acceptance at 14, ALTO cure package at 16, BEAM package at 18, both partners `ready` at every barrier; 42 commands, outcome WIN) through `Store.apply` on case1/base, after 2 untimed warmup rooms, and times each call by command type. It then builds clock rooms of 10, 50 and 200 commands, clears the session cache and times `Store.session` (cold replay) and `Store.verify`, 20 samples each after 2 warmups. Case1 has only 18 execution windows, so a clock room is `set_speed`, then a `tick` whenever the clock runs and `set_speed` when it auto-pauses, until the season ends; remaining commands are accepted `pause` commands on the finished season. The run refuses to report if the 10 S2 rooms disagree on the verified journal digest or if any replay or verify of a clock room yields a different digest. The result file records commit, rules version, Python version, Postgres server version, machine and date.

```bash
cd backend
DATABASE_URL=postgresql://.../scratch uv run python ../scripts/bench_store.py --out ../bench/results
```

`backend/tests/test_bench_store.py` (skipped without `DATABASE_URL`) runs a reduced version (1 S2 room, clock rooms of 50 and 150 commands, 3 samples) and asserts the S2 outcome, digest equality (inside `run`) and that the fastest replay of the 150-command room is at most 2x linear growth over the 50-command room (ratio at most 6; a per-command cost growing with room version would give about 9). Both rooms finish all 18 windows, so the comparison isolates per-command cost; 10 versus 50 does not, because the 10-command room covers only a few windows.

**First result, local, not CI** (`bench/results/2026-10-16-B2-45c0e7e.json`; commit `45c0e7e`, rules `case1-rules-2026.10.15`, Python 3.13.12, Windows AMD64 Intel Family 6 Model 183, 32 logical CPUs, Postgres 17.11 in local Docker; the container reports 17, not the 16 named above). Command latency over 10 S2 rooms plus the clock rooms:

| Command | n | p50 | p95 | p99 |
|---|---|---|---|---|
| `research` | 10 | 107.4 ms | 111.6 ms | 111.6 ms |
| `accept_replacement` | 10 | 109.6 ms | 119.2 ms | 119.2 ms |
| `propose` | 20 | 115.5 ms | 125.4 ms | 130.8 ms |
| `sign` | 20 | 119.2 ms | 130.6 ms | 131.0 ms |
| `ready` | 360 | 124.9 ms | 187.2 ms | 195.9 ms |
| `tick` | 44 | 169.4 ms | 198.2 ms | 199.5 ms |
| `set_speed` | 14 | 118.9 ms | 131.9 ms | 134.6 ms |
| `pause` | 202 | 131.2 ms | 145.0 ms | 151.9 ms |

| Room version | Journal entries | Cold replay min / p50 / p95 | `verify` min / p50 / p95 |
|---|---|---|---|
| 10 | 91 | 17.4 / 20.5 / 34.0 ms | 22.5 / 29.8 / 45.4 ms |
| 50 | 246 | 147.6 / 168.9 / 217.3 ms | 169.1 / 198.2 / 225.9 ms |
| 200 | 246 | 678.4 / 744.1 / 852.3 ms | 768.3 / 823.2 / 977.9 ms |

`verify` of a 42-command S2 room: p50 117.2 ms, p95 142.0 ms. On this machine no command type meets the 50 ms p95 target; every type, including a `pause` that writes no journal entry, costs at least about 100 ms. A cProfile of 10 `pause` applies put about 89% of the time in psycopg `executemany` (journal entries, journal lines and outbox; about 33 ms per call even for tiny batches) and 96% in socket waits overall, not in the engine or ordinary queries. That points at the Windows client and Docker networking path, not established as the cause; the CI runner has not been measured. From 50 to 200 commands replay (fastest samples) grows about 4.6x for 4x the commands with the engine work fixed; the extra cost is roughly 3.5 ms per replayed command (each `Session.handle` takes a rollback snapshot).

**Not done.** No CI job runs B2; no negative check yet (a deliberately quadratic replay tripping the linearity assertion); the `executemany` floor is a diagnosis lead, not a fix. Targets are not revised until a CI run exists.

**Target.** p95 `apply` under 50 ms for every command type on the CI runner; replay linear in command count.

### B3: API load (planned)

**Question.** How many concurrent rooms can one production sized VM serve before p95 latency or errors break the game's 0.5 s polling loop?

**Method.** k6 (or Locust) against `deploy/compose.prod.yaml` on the intended VM size. Each virtual room has two seats polling `GET /view` every 0.5 s with `If-None-Match`, plus a command burst at each decision window. Ramp rooms 10, 25, 50, 100, 200. Record p50 and p95 per endpoint, error rate, 304 ratio, Postgres CPU and the Prometheus `command_seconds` histogram for the same window, so the server side and client side numbers can be cross checked.

**Target.** p95 `GET /view` under 100 ms and zero 5xx at 100 concurrent rooms. Report the knee (first step where the target fails), not only a passing point.

### B4: Game client frame time (planned)

**Question.** Does the Godot client hold the 60 fps budget, and how bad is the worst hitch?

**Method.** A scripted camera route through the office and street (reuse `--goto` timed routes) records per frame `Performance.TIME_PROCESS` and real frame delta for 60 s after a 10 s settle, plus the first 10 s separately so shader compilation hitches are visible. Output p50, p99 and max frame time and the count of frames over 33.3 ms. Must run on real GPUs, not headless CI: record GPU, driver, OS, resolution and renderer. Minimum two machines: an integrated GPU laptop and a discrete GPU desktop.

**Target.** p99 frame time at or under 16.7 ms at 1280x720 on the integrated GPU laptop; no frame over 100 ms after the first 10 s. A pipeline cache or warmup that removes the first frame hitch is recorded with before and after captures in this document.

### B5: Control detection and mutation score (planned)

**Question.** How much of the integrity story is real? When the books are wrong, which layer catches it?

**Method.** A fault injection corpus with one generator per fault class, each seeded and deterministic:

| Fault class | Example |
|---|---|
| Balanced but unsupported posting | A journal entry that balances but has no execution, broker or LP source |
| Phantom or missing position | A coherent position with no confirmation |
| Settlement fault | Duplicate, missing or misallocated obligation |
| Financing fault | Wrong loan fee day count, rate or date |
| LP and fee fault | Wrong series allocation, fee date or provision reversal |
| Statement fault | Broker cash statement differing from activity |

For every injected fault record whether internal reconciliation, the independent controls (`shadow`, `broker`, `administrator`) and `verify` detect it. Report detection rate per class per layer, plus false positive rate on clean seasons. Separately run mutation testing (mutmut) over `journal.py`, `series.py`, `shadow.py`, `broker.py` and `administrator.py` and report the killed mutant percentage per module, listing survivors.

**Target.** 100% detection by the independent controls for every authored class, 0 false positives on clean seasons. The interesting result is the gap between internal reconciliation and independent controls, so report both.

This corpus is also the task generator for the external `fundforge-rl` research repository (an agent repairs the injected fault and the independent controls grade it). That work stays outside the product: FundForge itself keeps the no LLM decision.

### B6: Game balance across seeds (planned)

**Question.** Is there still no dominant degenerate strategy once markets are generated rather than authored?

**Method.** Run the `policy_grid.py` policies over a fixed list of generator seeds and report win, survival and distress rates per policy with Wilson 95% intervals. This also implements the open generator balance gate.

**Target.** No degenerate policy's win rate interval lies above the best designed line's.

## Methodology rules

1. Every result file records commit, dirty state, rules version, Python or Godot version, machine and date.
2. Compare A and B only on the same machine in the same session. Gate on the minimum of N samples; report median and p95 for context.
3. Warm up before sampling, and check determinism (identical digests) inside the benchmark.
4. Report the failure point of a load test, not only a passing load.
5. Every negative claim needs a negative check: a deliberately slowed or broken build must trip the gate.
6. README and ENGINEERING cite a result file by name; nothing else counts as evidence.
