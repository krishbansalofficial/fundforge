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

### B2: Store command latency and replay with Postgres (planned)

**Question.** What do accepted commands and cold room replays cost end to end, including the row lock, idempotency check, hash chain and journal insert?

**Method.** A pytest module behind `DATABASE_URL` drives the S2 command script through `Store.apply` against a real Postgres 16, then clears the cache and rebuilds the room. Record per command type p50, p95, p99 and replay time as a function of room version (10, 50, 200 commands, the last built by repeating clock ticks). Also time `Store.verify`.

**Target.** p95 `apply` under 50 ms for every command type on the CI runner; replay linear in command count. Targets are revised after the first recorded run.

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
