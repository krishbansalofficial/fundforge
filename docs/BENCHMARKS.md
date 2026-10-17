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

**Diagnosis of the floor (this machine, not CI).** psycopg 3.3.6 (binary, libpq 18.4) against the same container, 30 calls each, p50: on `localhost` a `select 1` takes 0.74 ms and a single-row `execute` insert 0.77 ms, but `executemany` takes 24.8 ms with 0 rows and 50.0 ms with 1 or 5 rows, an explicit `conn.pipeline()` of 3 inserts 50.1 ms, and one multi-row `insert ... values` of 5 rows 1.29 ms. On `127.0.0.1` every one of these is 0.9 to 1.4 ms. `localhost` resolves to `::1` first, so the stall is libpq pipeline mode (which psycopg's `executemany` uses) over Docker Desktop's IPv6 loopback forwarder: a client and network effect, not per-statement server cost. The store now writes journal entries, journal lines and outbox rows with one plain multi-row `insert ... values` per table (`Store._insert_rows`: chunked under Postgres's 65535 bind-parameter cap, skipped when empty, rows in input order), inside the same transaction, after the same row lock, idempotency check and hash chain, with the deferred balance trigger unchanged. Pointing `DATABASE_URL` at `127.0.0.1` would also remove the stall without a code change.

**Second result, local, not CI** (`bench/results/2026-10-17-B2-55036d9.json`; commit `55036d9`, same machine, Python, Postgres and `localhost` URL as the first result). Every journal digest matches the first result (S2 `d7aaeb27...`, clock rooms `258600ba...` and `67c220ce...`).

| Command | n | p50 before / after | p95 before / after |
|---|---|---|---|
| `research` | 10 | 107.4 / 8.5 ms | 111.6 / 13.3 ms |
| `accept_replacement` | 10 | 109.6 / 9.9 ms | 119.2 / 12.3 ms |
| `propose` | 20 | 115.5 / 13.7 ms | 125.4 / 16.8 ms |
| `sign` | 20 | 119.2 / 14.1 ms | 130.6 / 16.2 ms |
| `ready` | 360 | 124.9 / 14.8 ms | 187.2 / 162.2 ms |
| `tick` | 44 | 169.4 / 19.2 ms | 198.2 / 166.6 ms |
| `set_speed` | 14 | 118.9 / 10.6 ms | 131.9 / 15.5 ms |
| `pause` | 202 | 131.2 / 17.5 ms | 145.0 / 20.1 ms |

Cold replay p50 for 10 / 50 / 200 commands: 13.0 / 99.0 / 445.8 ms (was 20.5 / 168.9 / 744.1); `verify` of the S2 room p50 75.9 ms, p95 82.0 ms. Six of eight command types now meet the 50 ms p95 target on this machine. `ready` and `tick` still have a p95 of about 165 ms while their p50 is under 20 ms; the slow tail is not diagnosed (a likely lead is the commands that cross a barrier and advance the engine, not measured).

**Not done.** No CI job runs B2; no negative check yet (a deliberately quadratic replay tripping the linearity assertion); the `ready`/`tick` p95 tail is not diagnosed. Targets are not revised until a CI run exists.

**Target.** p95 `apply` under 50 ms for every command type on the CI runner; replay linear in command count.

### B3: API load (planned)

**Question.** How many concurrent rooms can one production sized VM serve before p95 latency or errors break the game's 0.5 s polling loop?

**Method.** k6 (or Locust) against `deploy/compose.prod.yaml` on the intended VM size. Each virtual room has two seats polling `GET /view` every 0.5 s with `If-None-Match`, plus a command burst at each decision window. Ramp rooms 10, 25, 50, 100, 200. Record p50 and p95 per endpoint, error rate, 304 ratio, Postgres CPU and the Prometheus `command_seconds` histogram for the same window, so the server side and client side numbers can be cross checked.

**Target.** p95 `GET /view` under 100 ms and zero 5xx at 100 concurrent rooms. Report the knee (first step where the target fails), not only a passing point.

### B4: Game client frame time (implemented; one laptop, integrated target fails)

**Question.** Does the Godot client hold the 60 fps budget, and how bad is the worst hitch?

**Method.** `scripts/bench_frames.py` wraps `scripts/measure_frames.py`. It opens a solo case1 room on a running API and boots the real game window at 1280x720 with V-Sync off and no frame cap. The player then walks the existing `--goto` office-and-street route (trading, committee, risk, LP, back office, research, street, broker, trading) twice, covering about 70 s. `game/scripts/perf.gd` (`--perf`) records the real frame delta (wall clock between frames), `Performance.TIME_PROCESS` and the measured GPU time for every frame. It reports the first 10 s after the office appears separately (`settle_first_10s`, where shader compilation hitches show) and the following 60 s as `steady`: p50, p95, p99, max, frames over 33.3 ms and frames over 100 ms. The adapter is forced with Godot's `--gpu-index` (Forward+ only). The result records the adapter Godot actually used from `RenderingServer.get_video_adapter_name()`, so it never infers the GPU from the index. It also records the Windows driver version for that adapter, the renderer, resolution, power source (`Win32_Battery`), power plan (`powercfg`), CPU load at start and any running pytest or `bench_*` process. It refuses to record on battery. Without `--perf` the game does not create the recorder, so its behaviour is unchanged.

```powershell
# API against a scratch database, e.g. DATABASE_URL=.../fundforge_b4 uv run uvicorn fundforge.api:app --port 8044
py -3 scripts/bench_frames.py --server http://127.0.0.1:8044 --gpu-index 1 --tag igpu --run 1
```

**GPU selection on this machine.** Godot's default Vulkan driver lists only the NVIDIA GPU (`--verbose` shows one device), so `--gpu-index` cannot select the Intel GPU under Vulkan. Under `--rendering-driver d3d12`, Godot lists NVIDIA as #0 and Intel UHD as #1, and the startup log confirms `Using Device #1: Intel - Intel(R) UHD Graphics`. Every run below therefore uses D3D12 Forward+, not the project's Vulkan default. The internal display is attached to the Intel GPU (Windows reports the 2560x1600 mode on it), so discrete GPU frames are copied to it for display.

**Result: one laptop, two GPUs (not two machines).** Commit `f5a0733` (clean), Godot 4.7.2-stable official, Windows 11 (10.0.26300), Intel Core i9-14900HX, D3D12 Forward+, 1280x720 window, V-Sync off, on AC power, Balanced plan. No pytest or bench process was running at any start. CPU load at start was 5.4% and 17.3% for the two integrated runs and 4.3% and 8.1% for the two discrete runs. `igpu-r2` is marked `machine_busy` because its own 5 s sample read 17.3%, above the 15% threshold; a check just before it read 6.9%, and its numbers match r1.

| Run | Adapter (driver) | Window | Frames | p50 | p99 | Max | > 33.3 ms | > 100 ms |
|---|---|---|---|---|---|---|---|---|
| `igpu-r1` | Intel UHD Graphics (32.0.101.6881) | first 10 s | 115 | 78.5 ms | 233.4 ms | 259.6 ms | 115 | 18 |
| | | steady 60 s | 689 | 79.9 ms | 182.2 ms | 205.5 ms | 689 | 189 |
| `igpu-r2` | Intel UHD Graphics (32.0.101.6881) | first 10 s | 115 | 78.9 ms | 231.3 ms | 257.8 ms | 115 | 17 |
| | | steady 60 s | 687 | 80.2 ms | 182.2 ms | 205.6 ms | 687 | 187 |
| `dgpu-r1` | RTX 4070 Laptop GPU (32.0.15.6094) | first 10 s | 1964 | 5.0 ms | 7.1 ms | 25.4 ms | 0 | 0 |
| | | steady 60 s | 12170 | 5.1 ms | 7.5 ms | 10.8 ms | 0 | 0 |
| `dgpu-r2` | RTX 4070 Laptop GPU (32.0.15.6094) | first 10 s | 1974 | 5.0 ms | 7.2 ms | 24.6 ms | 0 | 0 |
| | | steady 60 s | 12217 | 5.1 ms | 7.5 ms | 10.6 ms | 0 | 0 |

Result files: `bench/results/2026-10-16-B4-f5a0733-igpu-r1.json`, `-igpu-r2.json`, `-dgpu-r1.json`, `-dgpu-r2.json`. Each holds the full `perf.gd` report under `raw`, including the five slowest frames and their position on the route.

**Verdict.** The integrated GPU fails the target. Its steady p99 is 182 ms against 16.7 ms, about 11.5 fps on average, and about 187 steady frames exceed 100 ms in each run, so the no-frame-over-100 ms rule also fails. Its measured GPU time averages about 87 ms per frame, so the bottleneck is GPU rendering. `TIME_PROCESS` (p50 about 113 ms) follows the frame time here, so it does not isolate script cost on this adapter. The discrete GPU meets both rules with a wide margin (steady p99 7.5 ms, max 10.8 ms). Its worst first-10 s frame is about 25 ms, so it shows no large shader compilation hitch after the office appears. No quality setting or game code was changed for these runs.

**Not done.** The second machine (a discrete GPU desktop) has not been measured. The project's default Vulkan driver has not been measured on the integrated GPU, because Vulkan does not expose it here. The 2.1 s to 16.9 ms hitch claim in the audit table is still not reproduced. No pipeline cache or warmup before and after capture exists.

**Target.** p99 frame time at or under 16.7 ms at 1280x720 on the integrated GPU laptop; no frame over 100 ms after the first 10 s. A pipeline cache or warmup that removes the first frame hitch is recorded with before and after captures in this document.

### B5: Control detection and mutation score (detection corpus implemented; mutation testing planned)

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

**Implemented.** `backend/tests/fault_corpus.py` holds one seeded generator per class above (`random.Random("B5:<class>:<seed>")`). Each fault picks a golden path and a decision barrier on days 13 to 19 (17 to 19 for settlement, so receipts exist), is injected with the techniques the existing tests already use, and is scored on four layers: `reconcile` (at injection, or a reconcile `InvariantError` later in the season), `controls` (`control_report` breaks or an open statement), `certificate` (`shadow.certify` struck at injection as the dealing gate strikes it, without redemption lines; it includes every control break plus `shadow_nav`) and `verify` (the database-free core of `Store.verify`: replay the same tape and script from scratch and compare the journal digest). False positives are counted at every barrier of eight clean seasons: the four golden paths, and each again with a broker statement that matches the broker record. `backend/tests/test_fault_corpus.py` runs 4 seeds per class and asserts every class is caught by controls or certificate with zero false positives. `scripts/bench_controls.py --seeds 40 --out ../bench/results` writes the result file.

**First result** (`bench/results/2026-10-16-B5-92e0cca.json`, commit `92e0cca`, rules `case1-rules-2026.10.15`, Python 3.13.12, Windows AMD64, 32 logical CPUs). 40 faults per class:

| Fault class | reconcile | controls | certificate | verify |
|---|---|---|---|---|
| Balanced but unsupported posting | 3/40 | 30/40 | 40/40 | 40/40 |
| Phantom or missing position | 4/40 | 40/40 | 40/40 | 32/40 |
| Settlement fault | 0/40 | 40/40 | 40/40 | 0/40 |
| Financing fault | 0/40 | 40/40 | 40/40 | 30/40 |
| LP and fee fault | 0/40 | 40/40 | 40/40 | 31/40 |
| Statement fault | 0/40 | 40/40 | 40/40 | 0/40 |

Clean seasons: 0 of 152 barrier checkpoints flagged across 8 seasons.

**Findings.** (1) In the first result, `control_report` missed a balanced posting to an account no control owned: all 10 `accrued_expense` faults passed it, and only the certificate's `shadow_nav` caught them at a dealing close. Fixed by `shadow.inspect_expense_accrual` (an independent recomputation of the account from authored sources, currently zero). Rerun `bench/results/2026-10-16-B5-8a79b07.json` (commit `8a79b07`, same machine and corpus): `control_report` 40/40 for every class, including balanced postings, with 0 false positives on 152 clean checkpoints. (2) Internal reconciliation caught only faults that break a stored identity (`long_securities` postings, extra shorts without a borrow); everything coherent passed it, which is the gap the independent controls exist for. (3) `verify` replay catches only faults that change the journal; tape faults, rule faults (a scaled fee function replays identically), loan-state, settlement-row and confirmation tampering replay clean. (4) Pending-obligation variants fall back to receipt variants when nothing is pending at the barrier; only 1 of 40 settlement faults touched a pending row, so pending coverage still rests on `test_settlement_recon.py` and `test_shadow.py`.

**Not done.** Mutation testing (mutmut) has not been run; no killed-mutant figures exist.

This corpus is also the task generator for the external `fundforge-rl` research repository (an agent repairs the injected fault and the independent controls grade it). That work stays outside the product: FundForge itself keeps the no LLM decision.

### B6: Game balance across seeds (implemented)

**Question.** Is there still no dominant degenerate strategy once markets are generated rather than authored?

**Method.** `scripts/bench_balance.py` draws the fixed seed list `seed:b6-0` .. `seed:b6-(N-1)`, builds each tape exactly as a generated room does (`store._tape("case1-generated", seed)`, `GEN_VERSION` plus LP agents) and runs the existing grid through `balance.accept`, which plays every `balance.POLICIES` line through the real Session. Designed lines are `balance.RECALL_LINES` (`derisk_floor`, `S1_balanced`, `cover_recall_only`); degenerate lines are `passive` and `flatten_d12`. Win, survival and distress rates carry Wilson 95% intervals (z = 1.96) computed in Decimal and rounded outward to 4 dp. The verdict fails if any degenerate win interval's lower bound exceeds the best designed line's upper bound. Rooms run only gate-accepted seeds, so the accepted subset is the primary population; the ungated draw is reported as well, because on accepted seeds the gate itself requires every designed line to win, passive not to win and `flatten_d12` to replay passive's journal, so the accepted verdict holds by construction. The generator balance gate already lives in `store.py` (`balance-v1`); B6 measures it and does not change it. `backend/tests/test_bench_balance.py` checks the Wilson arithmetic against hand-worked cases, that the verdict flags a synthetic dominant policy, and a 4-seed run.

```bash
cd backend
uv run python ../scripts/bench_balance.py --seeds 400 --out ../bench/results   # exits 1 if the accepted verdict fails
```

**First result** (`bench/results/2026-10-16-B6-148c93d.json`, commit `148c93d` with `backend/src` clean and the script uncommitted, rules `case1-rules-2026.10.15`, generator `gen-2026.10.1`, gate `balance-v1`, Python 3.13.12, Windows AMD64, 32 logical CPUs). 400 seeds drawn, 186 accepted by the gate; every rejection was `cover_recall_only_does_not_win`. 400 is the number drawn so the accepted subset exceeds 150 seeds; the per-seed list with labels and scores is in the result file.

| Policy | Accepted win (n=186) | Accepted survival | Accepted distress | Ungated win (n=400) | Ungated survival |
|---|---|---|---|---|---|
| passive (degenerate) | 0 [0.0000, 0.0203] | 186 [0.9797, 1.0000] | 0 [0.0000, 0.0203] | 0 [0.0000, 0.0096] | 400 [0.9904, 1.0000] |
| flatten_d12 (degenerate) | 0 [0.0000, 0.0203] | 186 [0.9797, 1.0000] | 0 [0.0000, 0.0203] | 0 [0.0000, 0.0096] | 400 [0.9904, 1.0000] |
| derisk_floor | 186 [0.9797, 1.0000] | 0 [0.0000, 0.0203] | 0 [0.0000, 0.0203] | 400 [0.9904, 1.0000] | 0 [0.0000, 0.0096] |
| S1_balanced | 186 [0.9797, 1.0000] | 0 [0.0000, 0.0203] | 0 [0.0000, 0.0203] | 400 [0.9904, 1.0000] | 0 [0.0000, 0.0096] |
| cover_recall_only | 186 [0.9797, 1.0000] | 0 [0.0000, 0.0203] | 0 [0.0000, 0.0203] | 186 [0.4166, 0.5140] | 214 [0.4860, 0.5834] |

No policy reached DISTRESS on any of the 400 seeds.

**Verdict.** Pass on both populations: no degenerate policy wins on any seed, so no degenerate interval lies above `derisk_floor`'s. On the accepted population this is guaranteed by the gate; the ungated draw is the non-trivial evidence, and it agrees.

**Findings.** (1) Outcome labels separate designed from degenerate lines completely, so win rate cannot detect dominance *among* designed lines. By score, `derisk_floor` was the best policy on 164 of 186 accepted seeds (344 of 400 ungated), `cover_recall_only` on 13 and `S1_balanced` on 9; the authored-world property "no policy is best in every world" holds, but `derisk_floor` is the near-dominant choice in generated markets. (2) The gate rejects 214 of 400 seeds, all because the minimal `cover_recall_only` line falls into a forced action; generated markets are harsher than the authored ones on that line.

**Not done (first result).** Only the fixed knowledge-free grid is measured; no human, bot-seat or learned policy is included, and no score-dominance target was set.

#### B6 score balance among designed lines

**Rule (stated before the second run).** Per seed, the designed line with the strictly highest `score` is that seed's best line; ties are counted separately and credit no line. For each designed line the script reports its best-score share with a Wilson 95% interval and the spread (min, p25, median, p75, max) of its margin over the best *other* designed line, in score bps (negative when it is not the best). **Fail if any designed line's best-score share interval lies wholly above 50%** (Wilson lower bound > 0.5, `SHARE_LIMIT` in the script). 50% is a design choice, not a measured figure: with three designed lines, a line that is the right answer in most generated worlds makes the other two lines decoration. The first result's count (164 of 186) was already known when the threshold was chosen; the threshold was not tuned to it, and the engine, scoring rules, policies and gate are unchanged. The script exits 1 if either verdict fails on the accepted population. Diagnosis: the script replays each designed line (deterministic) to record `fund_return_bps`, `benchmark_return_bps`, `excess_bps`, `financing_drag_bps` and `impact_drag_bps`, and splits best-score shares by the sign of the seed's benchmark return. `backend/tests/test_bench_balance.py` checks the share, tie, margin and verdict arithmetic on synthetic scores.

**Second result** (`bench/results/2026-10-17-B6-f3d0104.json`, commit `f3d0104` with `backend/src` clean and the script change uncommitted, same rules, generator, gate, Python and machine as the first result, same seed list `seed:b6-0` .. `seed:b6-399`). The gate accepted the same 186 seeds and the label table is identical to the first result. No ties.

| Designed line | Accepted best-score share (n=186) | Margin over next best, median [p25, p75] (min, max) | Ungated share (n=400) | Ungated median margin |
|---|---|---|---|---|
| derisk_floor | 164 [0.8274, 0.9206] | +169.25 [+91.05, +238.93] (-201.0, +649.7) | 344 [0.8225, 0.8906] | +159.95 |
| S1_balanced | 9 [0.0256, 0.0894] | -171.85 [-238.93, -92.65] (-649.7, +79.1) | 43 [0.0807, 0.1417] | -160.90 |
| cover_recall_only | 13 [0.0412, 0.1159] | -198.75 [-281.08, -126.53] (-767.0, +45.3) | 13 [0.0190, 0.0549] | -352.75 |

**Verdict: FAIL.** `derisk_floor`'s best-score share interval [0.8274, 0.9206] lies wholly above 50% on the accepted population (and [0.8225, 0.8906] ungated). It is the dominant designed line in generated markets; the script exits 1.

**Why `derisk_floor` wins.** On accepted seeds every designed line wins, so no forced-action penalty applies and score equals excess return over the passive opening book; the benchmark is the same for every line on a seed, so the ranking is purely fund return. The generated market falls on 184 of 186 accepted seeds (median benchmark -796.4 bps). `derisk_floor` sells 100,000 long shares (BEAM 50k, ALTO 25k, COVE 25k) on day 12, so it carries the least long exposure into the decline: median fund return -571.7 bps against -767.1 for `S1_balanced` (sells 20k BEAM on day 14) and -797.4 for `cover_recall_only`, giving median excess +199.1, +29.3 and -4.1 bps. The drags do not explain it: median financing drag is 1.7 / 2.7 / 3.7 bps and impact drag 3.3 / 0.5 / 0.2 bps (derisk_floor pays the most impact and still wins by ~170 bps). Of the 22 accepted seeds where `derisk_floor` is not best, 20 have a milder benchmark than the median (16 above -320 bps) and 2 have a rising benchmark. The finding is a market-direction bias in generated tapes interacting with a de-risking line, not a cost or penalty imbalance; a fix belongs to the generator's return distribution or to the designed-line set, and is not attempted here.

**Not done.** No engine, scoring, policy, gate or generator change; no fix for the dominance. The split by benchmark sign has only 2 rising-market accepted seeds, too few to say how the lines rank when markets rise.

## Methodology rules

1. Every result file records commit, dirty state, rules version, Python or Godot version, machine and date.
2. Compare A and B only on the same machine in the same session. Gate on the minimum of N samples; report median and p95 for context.
3. Warm up before sampling, and check determinism (identical digests) inside the benchmark.
4. Report the failure point of a load test, not only a passing load.
5. Every negative claim needs a negative check: a deliberately slowed or broken build must trip the gate.
6. README and ENGINEERING cite a result file by name; nothing else counts as evidence.
