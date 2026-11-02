# Data card: generated worlds and the offline dataset

What the models in [MODEL_CARDS.md](MODEL_CARDS.md) learn from. Numbers in tables link to the result file they come from; `tests/test_cards.py` checks them. Written 28 October 2026 against `main` at `3c1a5ce`.

Note: another change to `backend/src/fundforge/balance.py` and `generator.py` is in progress. This card describes the code at `3c1a5ce`. If the gate or the generator changes, the gate numbers below no longer describe new worlds.

## What the data is

All data is synthetic. Nothing comes from real markets, real funds or real people.

- **A world** is `(gen_seed, variant)`. `fundforge.generator.generate` builds a tape from the authored Case1 skeleton (`fixtures/case1.json`) and a seed; `compile_tape` picks the variant (`base` or `rally`). Code: `src/fundforge_ml/worlds.py`.
- **A seed family** is `<scenario_id>/<GEN_VERSION>/<gen_seed>`. All variants of one seed belong to one family.
- **Episodes** are played through the real `Session`, with the agent's seat driven by a policy and the other seat by `bot:v1`.

## Generator and versions

| Item | Version |
|---|---|
| Generator (marks, base level) | `gen-2026.10.1` (`GEN_VERSION`) |
| Scenario randomiser plus marks (harder levels) | `gen-2026.10.2` (`SCENARIO_VERSION`) |
| Macro prints | `macro-2026.10.2` (`MACRO_VERSION`) |
| ML contracts and dataset schema | `ml-contracts-2026.10.1` |
| Rules at `3c1a5ce` | `case1-rules-2026.10.29` |

The generator also returns a seed commitment (`generator.commitment`), a SHA-256 that identifies the seed without revealing it.

## The balance gate

`fundforge.balance.accept(tape)` plays five fixed policies through the real `Session` on one tape: `passive`, `flatten_d12`, `derisk_floor`, `S1_balanced`, `cover_recall_only`. The policies read only public state, never the tape. A world is accepted only if all of these hold:

| Rejection code | Meaning |
|---|---|
| `flatten_not_refused` | Flattening the book on day 12 was not refused by the mandate |
| `passive_wins` | Doing nothing wins |
| `derisk_floor_does_not_win`, `S1_balanced_does_not_win`, `cover_recall_only_does_not_win` | A line that handles the recall does not win |

`worlds.world(...)` raises `WorldRejected` with these codes. Callers record rejections; they never drop them silently (`docs/ML_CONTRACTS.md` section 4). The dataset writes them to `rejections.parquet`; the training scripts write counts into their result JSON.

**Measured acceptance** (from the PPO run's gate, families `ppo-0` to `ppo-2999`):

| Quantity | Value | Source |
|---|---|---|
| Base level: families gated; accepted | 3000; 1319 | [ppo_pm.json](results/ppo_pm.json) |
| Base level rejections: `base` variant; `rally` variant (all `cover_recall_only_does_not_win`) | 1637; 108 | [ppo_pm.json](results/ppo_pm.json) |
| Accepted by split: train / val / test | 1046 / 136 / 137 | [ppo_pm.json](results/ppo_pm.json) |
| Scenario level (test families only): gated; accepted | 320; 107 | [ppo_pm.json](results/ppo_pm.json) |
| Harsh level (test families only): gated; accepted | 320; 73 | [ppo_pm.json](results/ppo_pm.json) |

On the scenario and harsh levels, rejections also include `S1_balanced_does_not_win` and `derisk_floor_does_not_win` (counts per code are in the JSON). The M1 benchmark rejected 1 of 4 families it tried (`base-2`, `cover_recall_only_does_not_win`; [bench_env.json](results/bench_env.json)).

The forecast data is **not** gated (`forecast.json` says so), because the Bayes filter is exact for the ungated generator.

## Splits

`contracts.split_of(seed_family)` takes SHA-256 of `fundforge-split-v1|<seed_family>` and buckets it into 80/10/10 train/val/test. The salt is fixed and is not the contract version, so a contract bump does not reshuffle splits. Whole families are held out, so the two variants of a seed never sit on both sides. Tested in `tests/test_contracts.py` and `tests/test_dataset.py::test_split_is_the_family_split_and_is_partitioned`.

Measured family counts per split are in the result files: [forecast.json](results/forecast.json) (train 15950, val 1968, test 2082) and the PPO table above.

**Fixed 28 October 2026.** `dataset.py` used to split on the SHA-256 hash of the family, while the training scripts split on the family string, so one family could land in different splits. It now calls `split_of(family)` like the training scripts and writes only the hash to the file. `test_split_is_the_family_split_and_is_partitioned` checks this against `split_of(World.seed_family)`.

## The offline dataset (`src/fundforge_ml/dataset.py`)

Built with `cd ml && uv run python scripts/build_dataset.py --out results/dataset --seeds 40`. Seeds are `seed-0000` onward; each runs both variants under the policies `passive` and `random_valid`, PM seat. Output is Parquet under `<out>/<table>/split=<split>/`.

No built dataset is committed, and no result file records its size. Row counts and split sizes are **not yet measured** in the repository.

### Schema (`ml/contracts/dataset.schema.json`)

| Table | Key | Columns |
|---|---|---|
| `episodes` | `episode_id` | `episode_id`, `seed_family` (hashed), `split`, `gen_version`, `seed_commitment` (never the seed), `scenario_id`, `rules_version`, `tape_digest`, `policy_id`, `outcome_label`, `score`, `nav`, `journal_digest` |
| `decisions` | `episode_id, seat, step` | `day`, `phase`, `available_day` (equals `day`), `obs` (the `observe(...)` view as JSON, unchanged), `action` (the command, or null for wait), `accepted`, `reject_code`, `reward` |
| `labels` | `episode_id, label` | `label`, `value`, `known_at_day` |

Money and rates are decimal strings. `dataset.py` also writes two tables that are not in the contract: `features` (point-in-time features per decision, from `features.point_in_time` over the episode's outbox rows) and `rejections` (`seed_commitment`, `variant`, `failures`).

### Hidden-truth label policy

- Hidden truth lives only in `labels`: the variant and the generated regime per day (`regime_day_<n>`).
- `labels` is **never a model input**. It is joined only as a target, with an explicit horizon.
- No seed or seed text is written; `seed_family` is hashed and the seed appears only as a commitment.

Tests (`tests/test_dataset.py`): contract columns; family split; unique keys; no seed text written; hidden truth only in labels, and no hidden key in any `obs`; gate rejections recorded; deterministic rebuild. `tests/test_features_parity.py` checks that offline features are byte-identical to the live stream fold and carry no hidden truth.

Gaps against the schema: `known_at_day` is always null in the current code, and the `factor_day_<n>` labels named in the schema are not written.

## Known biases and limitations

- **Synthetic.** One authored skeleton (Case1), one generator, one default `Spec`. Nothing here says anything about real markets.
- **Gate selection effect.** The gate keeps only worlds where minimal recall lines win and doing nothing loses. On these worlds random valid play also wins every test world (MODEL_CARDS card 1). Models trained on gated worlds see a narrow, easy slice of the generator.
- **Gated vs ungated.** Forecasters train on ungated worlds; agents play gated ones. The two distributions differ.
- **Policy bias.** The dataset's decisions come from `passive` and `random_valid` only. The anomaly detectors' clean books come from a random policy on the authored tape (`train_anomaly.py`), not from human or trained play, so "normal" means "what random play produces".
- **Partner bias.** The other seat is always `bot:v1`, so every episode reflects its fixed behaviour.
- **Rules drift.** Several result files were produced on `case1-rules-2026.10.15`, before the 28 October rounding fixes and the `bot:v1` retry fix. Each JSON records the versions it has; some do not record the rules version.
