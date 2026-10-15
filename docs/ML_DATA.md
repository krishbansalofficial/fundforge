# ML data platform: point-in-time features (lane L10)

Scope: the offline dataset builder, the live stream feature builder, and the parity and robustness tests between them. Contracts: [ML_CONTRACTS](ML_CONTRACTS.md) sections 3 and 4. Plan: [ML_PLAN](ML_PLAN.md), lane D (days 6-13).

## What is built

| Piece | Path | Role |
|---|---|---|
| Polars features | `ml/src/fundforge_ml/features.py` | `flatten` outbox rows, `point_in_time` cuts (one canonical JSON per decision), `at_end` for whole-room features |
| Live fold | `ml/src/fundforge_ml/stream.py` (unchanged) | Order-independent fold over Kafka or outbox rows, deduplicated by `event_id` |
| Dataset | `ml/src/fundforge_ml/dataset.py` | Plays `FundForgeEnv` episodes through `Session`, writes Parquet partitioned by `split` |
| Build script | `ml/scripts/build_dataset.py` | `uv run python scripts/build_dataset.py --out results/dataset --seeds 40` |
| Tests | `ml/tests/test_features_parity.py`, `test_stream_robustness.py`, `test_dataset.py` | See below |

## Point-in-time rule

A feature row for a decision uses an event only if both hold:
- `seq <= as_of_seq`: the command that produced it was committed before the decision (the room version the decision saw);
- its simulated `(day, phase)` is not after the decision's clock.

Visibility is the stream's: `public` events plus the deciding seat's own; `internal` journal entries and the partner's private events never count. Duplicates by `event_id` count once. Hidden truth is refused in any live event (`ValueError`, as in `stream.fold`).

Features are the stream's exactly: event count, commands by role, notices and incidents by code, watermark `(day, phase)`, the largest margin deficit (numeric Decimal maximum, reported as the event's own string), research topics revealed, and the outcome label. The `features` column is `canonical(snapshot)` (sorted keys, no spaces), so a match is a byte match.

## Parity and robustness results

Run from `ml/` with `uv run pytest`. Counts are for the full ml suite.

- Final-state parity, both seats, both authored variants (`base`, `rally`): Polars equals `stream.features` byte for byte.
- Per-decision parity: every decision of a `passive` and a `random_valid` rally episode equals the stream folded over the prefix `seq <= as_of_seq`.
- Decimal ordering: a margin deficit of `999999.00` and `1000000.50` reports `1000000.50` in both builders (a lexical maximum would be wrong).
- Offset-0 replay: two independent consumers starting from offset 0 reproduce the batch features.
- Duplicate delivery: feeding every row twice, or re-folding one row, changes nothing.
- Consumer restart: a half-consumed state replayed from offset 0 in a different interleaving converges to batch.
- Kafka stopped: a full game finishes with no consumer and with `confluent_kafka` not loaded. This is a Session-level check, not a broker outage test.

The Kafka broker outage, Debezium restart and offset-0 replay from a real topic remain in `ml/scripts/kafka_e2e.py`, which needs the compose stack. It was not run for this lane.

## Dataset

Tables, as in `ml/contracts/dataset.schema.json`: `episodes`, `decisions`, `labels`, plus two derived tables: `features` (one row per decision, point-in-time) and `rejections` (balance-gate refusals with their failure codes).

- Partitioning: `<table>/split=<train|val|test>/`. `split` is `split_of(seed_family)`, where the stored `seed_family` is the SHA-256 of the seed family. Whole families stay on one side.
- No seed is written. `seed_commitment` is the generator's commitment; a test scans every Parquet file for seed text.
- Hidden truth (`variant`, per-day regime) appears only in `labels`. Decision observations are `observe(...)` outputs and carry no hidden key (tested).
- The episode id is SHA-256 of `gen_version|family_hash|episode_seed|policy|rules_version`, where the episode seed is `gen_seed|variant|policy_seed`. This extends the contract wording, which has no variant or policy seed component. It keeps two variants of one seed from colliding.

Build of 40 candidate seeds, both authored variants, two policies (`passive`, `random_valid`), on this machine: 116 episodes, 794 decisions, 1044 labels, 794 feature rows, 22 rejected seed-variant worlds, about 50 s. Splits by episode: 74 train, 20 val, 22 test. These numbers are for the default command above; they are not a model result.

## Limitations

- Policies are a passive play and uniform random over valid actions. There is no learned policy and no ML evaluation here.
- `chain_head` in offline rows is a stand-in hash, since no database is involved. The backend's Store chain is verified by the backend.
- The dataset is written with Polars. There is no PySpark builder; the Polars parity suite is the reference a Spark job would have to match.
- The outbox and Kafka path is tested with rows fed directly, not through Debezium or a broker, in this lane.
- `features` is an extra table outside the contract; the contract version is unchanged (no contract file edited).
