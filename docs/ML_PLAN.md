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
