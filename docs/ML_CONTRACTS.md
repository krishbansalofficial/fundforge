# ML lane contracts (`ml-contracts-2026.10.1`)

Frozen on 13 October 2026, day 1 of [ML_PLAN](ML_PLAN.md). Four parallel lanes build against these. Code: `ml/src/fundforge_ml/contracts.py`; schemas: `ml/contracts/`. Change only with a `CONTRACT_VERSION` bump and every affected lane updated in the same change. Decisions behind them: [DECISIONS](DECISIONS.md), 13 October 2026.

## 1. Observation rule (all lanes)

A model sees exactly what a partner sees.
- `fundforge_ml.contracts.observe(session, user)` is the only sanctioned observation. It returns `Session.view(user)`, the same role-filtered as-of view the API serves. It raises `LeakError` if a hidden-truth key (`variant`, `seed`, `gen_seed`, `tape`, `factors`, `regime`, `true_state`) appears before the run finishes.
- After the run finishes, the debrief `outcome` may reveal the variant, as it does for a human.
- Encoders turn an observation into tensors. They are pure functions of the observation, carry an `ENCODER_VERSION`, and never read `session.e` or the tape.
- `ml/tests/test_canary.py` plants a unique future headline in the tape and requires that it is absent from both partners' observations until its event is processed, and present afterwards (positive control). Every new model-input path (encoder, feature table, Kafka feature builder) adds the same canary.

## 2. Environment API (lane B, consumed by C and D)

| Item | Contract |
|---|---|
| Single seat | `FundForgeEnv(gymnasium.Env)`. `reset(seed, options={"seed_family", "gen_seed", "role": "pm" or "mp", "partner": "bot:v1"})`. The other seat is played by `bot.plan` through ordinary commands. |
| Two seats | `FundForgeParallelEnv` (PettingZoo `ParallelEnv`), agents `("pm", "mp")`, same rules, no bot. |
| Step | One decision point for the seat: zero or one material command (or wait), then `ready` with skip. The real-time clock stays paused; time moves only through `ready`. |
| Actions | A discrete catalogue that maps 1:1 to existing Session commands (`propose`, `sign`, `research`, `visit`, `share_research`, `accept_replacement`, `cancel`, `set_reserve`, `resolve_statement`, wait), plus parameters drawn from the observation. Versioned as `ACTION_VERSION`. |
| Masks | Computed from the observation and the public mandate only. A command the engine still rejects is a normal outcome: state unchanged (all-or-nothing), `info["reject_code"]` set, no special penalty. |
| Reward | Terminal: the engine's `outcome()` score and tier, the numbers a player sees. Optional shaping: change in observed NAV divided by opening NAV. Any change bumps `REWARD_VERSION`. |
| Info | No hidden keys before the terminal step (enforced by `observe`). Terminal `info` carries the outcome, including the revealed variant. |
| Idempotency keys | `"{episode_id}:{seat}:{step}:{n}"`. |
| Determinism | The same tape, seed and action sequence give the same `journal_digest`. Tested. |
| Deployment of a learned policy | `bot:v2` = ONNX policy, single-threaded with a pinned runtime, model SHA-256 in the bot version. One disclosed seat at most, unranked rooms, actions logged as commands; replay never re-runs the model. |

## 3. Outbox events and Kafka (lane D, consumed by B and C)

`ml/contracts/outbox_event.schema.json`. In summary:
- One row per event, written in the **same PostgreSQL transaction** as the accepted command. Debezium relays rows to topics `fundforge.<kind>s`, partitioned by `room_id`, ordered by `(seq, idx)`.
- `event_id` is a UUIDv5 of `room_id|seq|kind|idx`; consumers deduplicate on it.
- `audience` is `public`, `pm`, `mp` or `internal`. A seat-facing feature builder reads `public` plus that seat only. `internal` (journal entries) is for audit and anomaly jobs.
- `sim_date` is simulated availability time, never wall time. Money and rates are decimal strings.
- Kafka is downstream only. Required tests:
  - the game plays and `verify(room)` passes with Kafka stopped;
  - replay from offset 0 equals the batch features;
  - duplicated deliveries change nothing.

## 4. Offline dataset (lanes B and D)

`ml/contracts/dataset.schema.json`. Three tables:

| Table | Key | Purpose |
|---|---|---|
| `episodes` | `episode_id` | One run: generator version, seed commitment (never the seed), policy, outcome, score, journal digest, `split`. |
| `decisions` | `episode_id, seat, step` | `obs` is `observe(...)` unchanged; the action sent; accepted or rejected with code; reward. |
| `labels` | `episode_id, label` | Hidden truth (variant, regime, generator factors) with `known_at_day`. Never a model input; joined only as a target with an explicit horizon. |

Locally the tables are Parquet; on Spark they are Delta Lake tables. On a sample, Spark output must equal Polars output exactly.

**Splits.** `split_of(seed_family)` hashes the family with a fixed salt into 80/10/10 train/val/test. Whole families are held out, and the 30-day v1 campaign is a further held-out scenario. Seeds rejected by the balance gate are recorded with their failure reasons, never silently dropped.

## Lane ownership

| Lane | Owns | Must not edit |
|---|---|---|
| A, game | `backend/src/fundforge/`, `backend/tests/`, `fixtures/`, `game/`, `frontend/` | `ml/`, `deploy/k8s/`, `data/` |
| B, ML | `ml/` (except `ml/contracts/`, which only a contract bump changes) | backend sources; it requests engine changes from lane A |
| C, platform | `deploy/`, `.github/workflows/`, Helm chart, Dagster definitions | engine economics |
| D, data | `data/` (Spark jobs, Kafka consumers), plus the outbox migration and writer in the backend, coordinated with lane A | engine economics |

The outbox writer is the one shared touch point. Lane D proposes it; lane A reviews it, because it runs inside the command transaction.
