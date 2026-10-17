# ML and data platform plan

Started 13 October 2026, at the owner's request. Target: three weeks (15 working days) with four parallel builder lanes and **zero spend**. Contracts: [ML_CONTRACTS](ML_CONTRACTS.md). Decisions: [DECISIONS](DECISIONS.md), 13 October 2026. This plan runs next to [ROADMAP](ROADMAP.md) v4; it does not mark any roadmap phase complete.

## Goal

Turn FundForge's deterministic, verifiable fund simulator into a complete ML project:
- reinforcement-learning agents (one seat, then two seats with private information);
- forecasting scored against known ground truth;
- RL that hunts for exploits as automated game QA;
- anomaly detection on the books;
- a production data platform: Kafka, Spark, Kubernetes, MLflow, Dagster and Ray.

ML advises, generates or plays a disclosed seat. **It never owns the economics.**

## Measured baseline (13 October 2026)

`scripts/sim_benchmark.py`, real Session and policy grid, 4-core cloud container, Python 3.13:

| Run | ms per episode | episodes/s/core |
|---|---|---|
| base, passive | 135–142 | 7.1–7.4 |
| base, S1_balanced | 149–158 | 6.3–6.7 |
| rally, passive | 135–136 | 7.4 |
| rally, S1_balanced | 168–174 | 5.7–5.9 |

- **Update, 13 October 2026, pickle snapshot:** `Session.handle` now pickles its rollback snapshot (the tape is shared by reference) and unpickles it only when a command fails. Same rollback semantics; 298 backend tests pass with PostgreSQL. Measured: **65–76 ms per episode (13–15 episodes/s/core), about 2.2× faster**. Under cProfile the snapshot is still 75% of the remaining time, so a per-command undo log stays the next speed step.
- **Where the time went (before the update):** under cProfile, **93%** of the time is `copy.deepcopy` in `Session.handle`'s rollback snapshot (`governance.py`, the "per-entity undo log if profiling says so" comment). The engine's own work is a small remainder.
- **What it means:** at today's speed, 1M decision steps is roughly 2–3 core-hours, so RL on the real Decimal engine is feasible. Replacing the snapshot is lane A's first task. The speed-up is to be measured, not assumed.
- **The float training twin is optional.** Build it only if the measured speed after that fix misses the training budget. If built, it must pass a parity test against the Decimal engine, and final evaluation always uses the real engine.

## Three risks and their fixes

1. **Too little data variety.** The generator randomises only unauthored public marks; crisis days, the recalled name and the margin shock are fixed, so an agent would memorise the timeline. Fixes:
   - add a versioned **scenario randomiser** (crisis-day jitter, which short is recalled, shock severity, rival and LP parameters, opening-book perturbation), with every world passing the balance gate;
   - evaluate on held-out seed families (`split_of`) and on the held-out v1 campaign;
   - publish the generalisation gap and the gate acceptance rate, and record rejected seeds.
2. **Simulation speed.**
   - Measured above.
   - Order of escalation: undo-log snapshot → vectorised environments across cores → Ray (KubeRay) for more machines → float twin only if still short.
3. **Integrity.** Enforced in code from day 1:
   - `lint-imports` plus a source-scan test keep the engine from importing ML; both catch a planted violation;
   - observations come only from `observe()`, and the future-headline canary passes on both variants;
   - learned bots use the existing disclosed, unranked bot seat;
   - Kafka is downstream only, and the game must work with it stopped.

## Zero-spend infrastructure

| Need | Where | Notes |
|---|---|---|
| Development, training, Spark, Ray | Owner's machine, overnight runs | Spark in `local[*]`; Ray local, or KubeRay on kind. |
| CI | GitHub Actions | kind cluster for Kubernetes tests. Free minutes depend on repo visibility; keep CI training to smoke size. |
| Extra notebooks | Kaggle or Colab free tiers | Optional for experiments; the pipeline must not depend on them. |
| Public hosting | Oracle Cloud Always Free, Ampere ARM | Oracle's page lists 4 OCPU / 24 GB. Several 2026 reports say it was cut to 2 OCPU / 12 GB; check your tenancy's limits. The plan fits 12 GB. ARM capacity is often unavailable in busy regions; retry or pick another home region at sign-up. Keep the account on the free plan and never upgrade it. |
| On the public host | k3s with Postgres (CloudNativePG), game API, Caddy/Traefik TLS, Redis, a single Kafka broker in KRaft mode with a small heap, Debezium, the feature consumer, MLflow (read-only model registry), Prometheus and Grafana | Estimated 5–7 GB, to be measured. Spark, Ray and training never run there. Images built multi-arch (`linux/arm64`) in CI. |
| Domain and TLS | A free subdomain (e.g. DuckDNS) or sslip.io, with Let's Encrypt | No paid domain. |
| Cloud credits | AWS new-account or student credits | Optional burst only, never a dependency. A credit account must stay on its free plan. |

## Lanes and schedule

Each lane is its own session and worktree. Ownership is in [ML_CONTRACTS](ML_CONTRACTS.md#lane-ownership). Every task starts from a written acceptance test and merges small pull requests to `main` once CI is green.

| Days | A: game | B: ML | C: platform | D: data |
|---|---|---|---|---|
| 1 | **Done in this change:** decisions, CLAUDE.md rules, `ml/` package, contracts, boundary and canary tests, benchmark, CI job | | | |
| 2–3 | Undo-log snapshot replacing deepcopy (stateful Hypothesis test, goldens unchanged, measured speed-up); settlement obligations task | Gymnasium and PettingZoo environments, encoder, determinism and canary tests | kind/k3s, Helm chart, CloudNativePG, multi-arch images | Outbox table, migration and writer (reviewed by A); Strimzi Kafka, Debezium |
| 4–5 | Generator in rooms, scenario randomiser, balance gate | Forecasting: LightGBM, then PyTorch; purged walk-forward CV; Brier score and calibration; gap to the Bayes-optimal posterior | MLflow, DVC, Dagster assets | Spark generation of episodes into Delta tables, split by family |
| 6–9 | 30-day v1 campaign | MaskablePPO, own PPO, MAPPO with a share action; training overnight | Prometheus/Grafana model dashboards, Evidently, ML checks in CI, Argo CD | Spark point-in-time features equal to Polars; Kafka live feature builder with canary |
| 10–11 | As-of tape revisions, exported builds | `bot:v2` (ONNX), exploit-hunter RL with a CI gate, Optuna generator tuning | Redis presence across 2 replicas, Oracle deployment | Live anomaly scoring (Isolation Forest, then autoencoder); offset-0 replay test |
| 12–13 | Trailer, cleanup, playtest fixes | Rule-parameter fitting for LP confidence; Spark evaluation sweeps with confidence intervals | Terminal ML panel (advisory label), load test | "Kafka stopped" test, drift dashboards |
| 14–15 | *All lanes:* retrain on the final campaign with one pipeline command; evaluation report, model and data cards, architecture diagram, README, demo video | | | |

**Cut order if behind:** rule-parameter fitting → Argo CD → anomaly autoencoder (keep Isolation Forest) → v1 campaign scope.

## Acceptance evidence (nothing counts without it)

- `ml` CI job green: `lint-imports`, ruff, mypy strict, pytest including the canary.
- Backend goldens and digests unchanged by every ML-lane change. Engine changes follow the existing rules-version policy.
- Every reported metric comes with its seed split, its sample size and the command that reproduces it. No invented results.
- Kafka: stopped-broker, offset-0 replay and duplicate-delivery tests. Spark: Polars-parity test. Kubernetes: kind deployment smoke in CI. Redis: two-replica presence test.

## Status, 13 October 2026

Lane B day 2 done: `FundForgeEnv` with masks, determinism and numeric canary tests, and measured baselines (see PROGRESS). Random valid play already wins every measured world, so learned policies are judged against that baseline.

## Next task

The cheaper snapshot is done (above). Lanes B, C and D start on their day 2–3 items once the day-1 change is merged. Lane A continues with the settlement-obligations task; the undo log is taken up only if RL training time demands it.

## Revision proposal, 16 October 2026

Audit of `main` at `45c0e7e` against the lane schedule above, then a proposed lean schedule. **The cuts below are a recommendation; the 13 October platform decisions stand until the owner records a change in DECISIONS.**

### Status by lane (calendar day 4 of 15)

| Item | State | Evidence |
|---|---|---|
| Boundary, contracts, canary | Done | `ml/tests/test_boundary.py`, `test_canary.py` |
| Rollback snapshot speed | Done (pickle, about 2.2x); undo log not started | ML_PLAN baseline section |
| Gymnasium env with masks | Done | `ml/src/fundforge_ml/env.py`, `test_env.py` |
| MaskablePPO, PM seat | Done, thin evaluation | `ml/results/ppo_pm.json`: 14 test worlds, 1 seed |
| Forecasting vs exact Bayes filter | Done, strong | `ml/results/forecast.json`: LightGBM Brier gap +0.0004 (SE 0.0001) on 2,082 held out families |
| Outbox, Debezium, Kafka, stopped broker test | Done | `ml/results/kafka_e2e.json` |
| Polars point in time features, Parquet dataset | Done | `test_features_parity.py`, `test_dataset.py` |
| Scenario randomiser and generator gate | Done | `gen-2026.10.2`; gate accepts 84 of 199 scanned seeds |
| PettingZoo, MAPPO, share action | Not started | |
| `bot:v2` ONNX | Not started | |
| Exploit hunter RL, Optuna | Not started | |
| Anomaly detection | Not started | |
| Spark, Helm/kind, Dagster, DVC, Ray, Argo CD, Redis, Evidently, Oracle deploy | Not started | |
| Evaluation report, model and data cards | Not started | |

### Evaluation problems to fix before adding anything

1. **Random valid play wins every test world.** PPO's gain (+2.38 reward paired, 13 of 14 worlds) is a score gain over a baseline that already always wins. The headline needs worlds where tier is at stake: use the randomiser's harder settings and report the share of worlds where random play does not win.
2. **Sample size.** 7 test families (14 worlds) and one training seed. Target at least 100 test families and 5 training seeds, reporting variance across seeds.
3. **Validation split unused.** Hyperparameters must be chosen on validation, never on test.

### Proposed lean schedule

Assumes Claude Code builds and the owner reviews about 3 to 4 hours a day; training runs overnight on the owner's machine.

| Order | Work | Days | Acceptance |
|---|---|---|---|
| 1 | Undo log snapshot plus vectorized environments | 2 | Goldens unchanged; measured episodes per second before and after |
| 2 | PPO evaluation hardening: harder worlds, 5 seeds, at least 100 test families, MP seat, masking ablation, Optuna on validation | 3 | `ppo_pm.json` and `ppo_mp.json` with per seed results and paired intervals |
| 3 | `bot:v2` as frozen ONNX in the disclosed bot seat | 2 | Deterministic replay equals the journal digest; refused exactly like a human on illegal proposals |
| 4 | Exploit hunter: RL rewarded for degenerate wins the balance gate should have rejected; a CI gate fails on any found exploit | 3 | Planted exploit found; current gate passes or the found exploits are recorded and fixed |
| 5 | Anomaly detection on the books: Isolation Forest over journal and control features, trained on clean seasons, scored on the BENCHMARKS B5 fault corpus, compared with the deterministic controls | 3 | Detection rate per fault class for both the model and the controls; false positive rate on clean seasons |
| 6 | Two seats with private information (PettingZoo, MAPPO, share action) | 4 | Stretch; cut first |
| 7 | Evaluation report, model and data cards, architecture diagram, README, demo video | 3 | Every number links to a result file |

Total about 16 working days without step 6, 20 with it.

**Recommended platform cuts.** Spark (the dataset is about 180k rows and Polars already matches it), Ray (one machine already reaches the measured training budget), Dagster, DVC, Argo CD and Kubernetes on the public host. Keep MLflow, the Kafka outbox (built, with a real stopped broker test) and Prometheus. Each cut tool would be a weak interview answer to "why did you need this at this data size", and together they are roughly 15 to 20 lane days.

### Working with Claude Code

* **Two lanes at most, not four.** The 15 October review found worktrees cut from old commits duplicating code already on `main` (shadow certification, LP confidence). Each lane starts from current `main`, merges `main` before every PR, and owns disjoint paths.
* **Acceptance test first.** Every task begins with the failing test or result file it must produce, written in the PR description.
* **Review gate.** Changes touching `backend/src/fundforge` get the `finance-reviewer` agent; changes touching API, views or observations get `security-reviewer`. No merge with goldens changed unless `RULES_VERSION` is bumped in the same commit.
* **Owner explain back.** After each merged step the owner writes, without Claude, a half page in their own words: what the step does, one design choice and its alternative, and how the result could be wrong. Interviewers will probe these.

