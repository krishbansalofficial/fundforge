# Scenario randomiser (`gen-2026.10.2`)

Status: implemented in `backend/src/fundforge/generator.py` (`SCENARIO_VERSION`). Not yet wired into
`store.py` or `ml/`; see "Wiring" below.

## Why

The authored Case1 fixture fixes the crisis day, the crisis marks, the recalled short, the margin
terms, the LP redemption and the opening book. An agent can memorise that timeline. This version
draws those parameters from the seed so a policy has to read the public state rather than recall it.

## What is randomised

All draws come from a separate SHA-256 counter stream, `gen_version/scenario|seed|n`, so they never
shift the marks stream. Bounds are `Spec` fields.

| Parameter | Draw | Default bound |
|---|---|---|
| Crisis day (marks, volumes, variant overrides, stressed margin) | +/- days | `crisis_days=1` (days 15-17) |
| Crisis long and short marks | +/- points | `crisis_points=2` (long 93-97, short 108-112) |
| Stressed margin coefficients (both pairs) | common shift | `margin_points=5` (points, i.e. +/-0.05) |
| Scheduled LP redemption | scaled, 500-unit steps | `redemption_pct=20` (8,000-12,000 units) |
| Rival parameters (`size`, `pain`, `deleverage`) | scaled | `rival_pct=20` |
| Opening book (each position) | scaled, 100-share steps | `book_pct=5`; debt absorbs the value change so opening NAV is unchanged |

Authored crisis inputs are moved, not replaced. Public notices (`margin_terms`,
`redemption_notice`) and the rally variant's description are rewritten to match the drawn values,
so every player-facing text still describes the tape. The draws are recorded under
`raw["generator"]["scenario"]`.

## Not randomised (limitations)

- **Which short is recalled.** Stays BRIN. `balance.accept` hardcodes BRIN in its policy grid
  (`RECALL_LINES`, `o("r", "BRIN", ...)`). Relabelling the recall would reject nearly every seed.
  Making it a draw needs `balance.py` to read the recalled name from the tape: the owner of that
  file should make that change first.
- The three fixed balance-grid plans were written for the authored book, so they are the main
  source of rejections (see below).

## Versions and reproduction

- `GEN_VERSION = "gen-2026.10.1"` is unchanged. Its output is byte-identical to b3a41c9: the golden
  tests in `backend/tests/test_generator_scenario.py` pin the JSON and tape digests of two seeds.
- `SCENARIO_VERSION = "gen-2026.10.2"` runs `randomise` first, then the same marks generator.
- A new `gen_version` is required for any change to a draw, bound or order.

## Balance gate acceptance

`balance.accept` is the existing gate and is unchanged. Measured with
`cd backend && uv run python ../scripts/generator_acceptance.py [N] [rejects.json]` on seeds
`bench-0..bench-(N-1)`, default `Spec`:

- 60 seeds: 19 accepted (31.7%). Rejections: `derisk_floor_does_not_win` 33,
  `S1_balanced_does_not_win` 39, `cover_recall_only_does_not_win` 37 (counts across policies).
- 500 seeds: see the measured figure in `docs/PROGRESS.md` once recorded.

One-at-a-time ablation over 30 seeds (accepted / 30; baseline about 11): `book_pct=0` gives 22;
`crisis_days=0` 11; `crisis_points=0` 10; `margin_points=0` 13; `rival_pct=0` 12; `redemption_pct=0` 12.
The opening-book perturbation is the largest driver, because the fixed plans size their sales and
covers to the authored positions. Ranges were not narrowed to raise the rate: that would make the
randomiser weaker, and the grid is the thing to fix.

Rejected seeds are recorded with their failure codes by the acceptance script (JSON when a path is
given). Acceptance is a measurement over a fixed seed list, not a probability guarantee.

## Seed families and splits

- `split_of(seed) -> "train" | "val" | "test"` (in `fundforge.generator`) hashes the seed's family
  with the same salt and function as `fundforge_ml.contracts.split_of`, so a family string gets the
  same split in both places.
- Family is the part of a seed before `#` (`family_of`). Seeds `fam#1` and `fam#2` share a split;
  a seed without `#` is its own family. 80/10/10 by bucket.

## Wiring (for the owners of `store.py` and `ml/`)

- `store.py` (lane L1 owns it; not edited here): to offer randomised rooms, the tape call
  `generate(seed, GEN_VERSION, raw, ...)` changes to `SCENARIO_VERSION` in `_tape`, and
  `_draw_variant`'s retry logic already handles rejections. Expect about 1 in 3 seeds to pass; with
  `GENERATION_ATTEMPTS = 12` roughly 0.8% of draws would exhaust the retries.
- `ml/src/fundforge_ml/worlds.py` builds worlds with `GEN_VERSION`. Switching it to
  `SCENARIO_VERSION` is a one-line change there; the family key in `World.seed_family` already includes
  `GEN_VERSION` and would need the new version too.

## Tests

`backend/tests/test_generator_scenario.py` covers: old-version goldens, determinism and seed
sensitivity, bounded draws with matching player texts over 12 seeds, engine replay of randomised
tapes, reasons on rejected seeds, split grouping, and spec validation.
