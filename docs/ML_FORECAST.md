# Regime forecasting (ML lane L6)

Scope: learn P(stressed) for the latest published Street activity period, scored against the hidden regime. Code: `ml/src/fundforge_ml/forecast.py`, `ml/scripts/train_forecast.py`, tests `ml/tests/test_forecast.py`. Results: `ml/results/forecast.json`. Plan: [ML_PLAN](ML_PLAN.md), forecasting row of days 4–5. Contracts: [ML_CONTRACTS](ML_CONTRACTS.md) sections 1 and 4.

## What the model sees

Only the published prints, in the row format the seat terminal serves (`fundforge.terminal.snapshot(...)["macro"]`). `forecast.features(rows, as_of)` keeps every row with `published_day <= as_of`, takes the latest revision per period, and returns a fixed 25-element vector: for the 8 newest periods, a scaled deviation from the regime midpoint, a revised flag and a present flag, plus the count of known periods. The hidden regime is only the label. Generated marks are not features, because the exact filter (the ceiling) does not use them.

The ceiling is `fundforge.research.regime_filter` run on the same prints. It is the Bayes-optimal posterior under the generator, so the question is how close each learned model gets to it.

## Protocol

- Worlds: `forecast-{i}` for i in [0, 20000), ungated generator output, authored `base` variant. Balance gate not applied, because the filter is exact for the ungated generator distribution.
- Split: `contracts.split_of(seed_family)`, whole families held out (train 15,950 families, val 1,968, test 2,082). The script asserts no family appears in both train and test.
- Samples: one per as-of day with at least one published print. Train 143,550, val 17,712, test 18,738. Test stressed rate 0.366.
- Training: logistic regression by Newton/IRLS (l2 1e-3); LightGBM, early stopping on val (best iteration 150); small PyTorch MLP (64-64, Adam 1e-3, batch 512, early stopping on val, 34 epochs). No hyperparameter search was run.
- Metrics on test: binary Brier on P(stressed) (research's two-state score is exactly 2x), log loss, ECE over 10 equal-width bins, and gap to the exact filter. Gap SE is computed over the 2,082 test worlds as the unit.

## Results (test, 18,738 samples, 2,082 families)

| Model | Brier | Log loss | ECE | Gap to Bayes (Brier) | SE (by world) | Gap (log loss) | Mean abs diff to Bayes |
|---|---|---|---|---|---|---|---|
| Bayes exact filter (ceiling) | 0.05722 | 0.18052 | 0.0034 | 0 | 0 | 0 | 0 |
| Chain prior only (no prints) | 0.22279 | 0.63531 | 0.0034 | +0.16557 | 0.00205 | +0.45479 | 0.3604 |
| Logistic regression | 0.07499 | 0.23873 | 0.0123 | +0.01777 | 0.00096 | +0.05820 | 0.0761 |
| LightGBM | 0.05765 | 0.18189 | 0.0044 | +0.00043 | 0.00013 | +0.00137 | 0.0071 |
| PyTorch MLP | 0.06014 | 0.18843 | 0.0062 | +0.00292 | 0.00034 | +0.00791 | 0.0191 |

Reproduce: `cd ml && uv run --group forecast python scripts/train_forecast.py --worlds 20000`. Runtime about 35 s (generation 14.7 s, fitting 20.7 s) on a 32-core Windows machine; CPU only.

## Checks

- Leak canary (`test_canary_future_prints_never_change_features`): for every as-of day in three worlds, every future print gets a wild value and an extra future revision, the list is shuffled, and the features and the filter's posterior must not change. A positive control confirms that changing a published print does change the features.
- Terminal parity (`test_rows_and_posterior_match_the_seat_terminal_in_a_real_session`): in a real `Session`, the forecast rows equal the terminal's `macro` rows for both seats at every step, and the filter's posterior matches the terminal's shown posterior to 6dp.
- Metric and split tests on known values and a family-disjointness assertion in the training script.
- Existing `ml/tests/test_canary.py` and boundary tests still pass.

## Limitations

- The filter is the ceiling only under the generator's model. Calibration on real market data is not evaluated.
- Learned models see the same prints the filter sees, so the gap measures how well they learn the filter, not whether they can beat it. Adding generated marks as features is an open experiment.
- Only the `base` variant is used and only one training seed per model. The gaps are small but come from a single run.
- ECE of the exact filter is 0.0034, not 0, because binning is finite-sample noise on a perfectly calibrated forecaster.
- The canary covers the feature builder only, not a Kafka feature builder or the terminal's future thesis scoring.
- The 80/10/10 split and the early-stopping rules were fixed before the final run. A 1,000-world smoke run used the same pipeline; no settings were changed in response to test results.

## Dependencies added

`ml/pyproject.toml`: new optional group `forecast` with `lightgbm>=4.5` and `torch>=2.6`. `ml/uv.lock` regenerated. The feature and metric code needs numpy only.
