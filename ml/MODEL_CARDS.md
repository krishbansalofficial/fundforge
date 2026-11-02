# Model cards

One card per model in `ml/`. Every number in an evaluation table is copied from a file in `ml/results/` and links to it. `tests/test_cards.py` checks that each linked file exists and that each number on a linked line appears in that file. Where there is no result file, the card says "not yet measured".

Written 28 October 2026 against `main` at `3c1a5ce`. The data the models train on is described in [DATA_CARD.md](DATA_CARD.md).

## Rules that apply to every model

- **Models never own fills, balances, NAV, fees, risk, approvals, scores or rankings.** The engine (`backend/src/fundforge`) computes all of those with versioned rules. A model can only advise, or send ordinary commands through `Session.handle`, where the engine checks them like any player's command.
- The engine never imports `fundforge_ml`. Checked by `lint-imports` (contract in `ml/pyproject.toml`) and by `tests/test_boundary.py`.
- A model sees what a partner sees. `contracts.observe(session, user)` returns `Session.view(user)` and raises `LeakError` if a hidden-truth key (`variant`, `seed`, `gen_seed`, `tape`, `factors`, `regime`, `true_state`) appears before the run finishes. See `docs/ML_CONTRACTS.md` section 1.
- Splits are by seed family: `contracts.split_of(seed_family)` hashes the family with the fixed salt `fundforge-split-v1` into 80/10/10 train/val/test. All variants of one generated seed stay in the same split. Tested in `tests/test_contracts.py`.
- No model here is deployed. There is no `bot:v2`; the only bot in the game is the rule-based `bot:v1`.

---

## 1. MaskablePPO policy (PM seat)

**What it is.** A reinforcement-learning policy for one seat of `FundForgeEnv` (`src/fundforge_ml/env.py`). The other seat is played by `bot:v1` through normal commands. Algorithm: `sb3_contrib.MaskablePPO`, MLP 128×128, CPU.

**Intended use.** Research: measure whether a learned policy plays the game better than random valid play, wait, and the `bot:v1` rules.

**Out of scope.** Ranked play, any hidden seat, any claim about real markets. It does not own fills, balances, NAV, fees, risk, approvals or rankings. It cannot approve its own trades: every reduce action is a joint package that the partner must countersign.

**Inputs.** `obs-v1`: a 96-float vector from `encoding.encode`, a pure function of `observe(...)` plus public scenario facts (instruments, research topics, calendar). The action mask comes from the observation and the public mandate only. Actions (`actions-v1`): wait; reduce a position by 25%, 50% or 100%; research a topic; share it; accept replacement borrow.

**Leak guarantees and the tests that enforce them.**

| Guarantee | Test |
|---|---|
| A planted future headline is absent from both partners' observations until its event runs, and present after (positive control) | `tests/test_canary.py` |
| Doubling ALTO's future marks changes no earlier observation or mask, and does change later ones | `tests/test_env.py::test_numeric_canary_future_marks_do_not_change_earlier_observations` |
| `info` carries no hidden key before the last step | `tests/test_env.py::test_info_never_carries_hidden_keys_before_the_end` |
| Masks follow the seat's role | `tests/test_env.py::test_mask_follows_role` |
| Generated worlds pass the gate and keep their family split | `tests/test_env.py::test_generated_world_respects_the_gate_and_family_split` |

**Training data and split.** Generated worlds `ppo-<n>` that pass the balance gate for both variants (`base`, `rally`), split with `split_of`. Hyperparameters are chosen on val worlds only (highest IQM of terminal reward). Test worlds are never used for selection.

**Reward** (`reward-v1`). Zero until the run ends, then the engine's own score in percent plus a tier bonus. The model does not compute the score; it reads the engine's `outcome()`.

**Evaluation.** Full run: 5 training seeds × 200,000 steps each, on 274 held-out test worlds.

| Quantity | Value | Source |
|---|---|---|
| Training seeds and steps | seeds 0, 1, 2, 3, 4; 200000 steps each | [ppo_pm.json](results/ppo_pm.json) |
| Split (families) | train 1046, val 136, test 137 | [ppo_pm.json](results/ppo_pm.json) |
| Split (worlds = family × variant) | train 2092, val 272, test 274 | [ppo_pm.json](results/ppo_pm.json) |
| Chosen config on val | learning rate 0.0001, entropy coefficient 0.01, val IQM 8.150 | [ppo_pm.json](results/ppo_pm.json) |
| PPO test reward, IQM [95% bootstrap CI] | 8.12 [7.74, 8.48] | [ppo_pm.json](results/ppo_pm.json) |
| Random valid play, IQM | 6.10 [5.87, 6.45] | [ppo_pm.json](results/ppo_pm.json) |
| PPO − random, paired by world | 1.960 [1.725, 2.198]; PPO ahead on 224 of 274 worlds | [ppo_pm.json](results/ppo_pm.json) |
| P(PPO > random) | 0.819 | [ppo_pm.json](results/ppo_pm.json) |
| PPO − `bot:v1` rules in the PM seat | 10.57 [10.45, 10.69]; PPO ahead on 274 of 274 worlds | [ppo_pm.json](results/ppo_pm.json) |
| Mean engine score | PPO 316.6 bps; random 120.6 bps; rules -240.8 bps; wait -245.4 bps | [ppo_pm.json](results/ppo_pm.json) |
| Outcomes | PPO WIN 1370 of 1370 episodes; random WIN 1370 of 1370 | [ppo_pm.json](results/ppo_pm.json) |
| Harder level "scenario": PPO − random | 0.897 [0.645, 1.138] on 214 worlds | [ppo_pm.json](results/ppo_pm.json) |
| Harder level "harsh": PPO − random | 0.496 [-0.233, 1.187] on 146 worlds | [ppo_pm.json](results/ppo_pm.json) |

Statistics come from `src/fundforge_ml/evals.py`: IQM, a percentile bootstrap that resamples runs and worlds, a world-paired difference, and P(X > Y) after Agarwal et al. 2021.

**Known failure modes and limitations.**
- Random valid play wins every test world at every level tried. So PPO's gain is in score, not in tier. The likely reasons (`docs/PROGRESS.md`, 27 October): the bot partner handles the recall, almost any single reduce action avoids the day-16 margin call, and the gate keeps only worlds where minimal recall lines win.
- PPO was trained on base worlds. Its lead shrinks on the two harder levels: the scenario-level interval excludes zero, the harsh-level interval does not.
- These levels exclude `hard` (`HARD_VERSION`), the only level where random play loses. It has not been evaluated yet.
- The run was made on commit `9049303` from a clean tree, after the rules changes of 28 October (`case1-rules-2026.10.28`, `case1-rules-2026.10.29`) and the `bot:v1` retry fix. The JSON does not record its rules version.
- Only the PM seat has been trained.
- An earlier 1-seed, 200k-step result is in git history (commit `f1d5b26`). It is superseded and not quoted here.

**Reproduce.** `cd ml && uv run --group train python scripts/eval_ppo.py --seeds 5 --steps 200000 --families 3000 --procs 8`

**Versions.** Contract `ml-contracts-2026.10.1`; encoder `obs-v1`; actions `actions-v1`; reward `reward-v1`; generator `gen-2026.10.1` (base) and `gen-2026.10.2` (harder levels); sb3 and sb3-contrib `2.9.0`; torch `2.14.1+cpu`; commit `9049303`. Each trained model's SHA-256 is in the JSON; the model files are not committed.

---

## 2. Regime forecasters vs the exact Bayes filter

**What it is.** Three models that output P(stressed) for the latest published Street activity period: logistic regression (numpy Newton/IRLS, L2 1e-3), LightGBM, and a PyTorch MLP (64-64). They are compared with `fundforge.research.regime_filter`, the exact forward filter over the same prints. That filter is the Bayes-optimal posterior under the generator, so it is the ceiling. Code: `src/fundforge_ml/forecast.py`, `scripts/train_forecast.py`.

**Intended use.** Show how close a learned model gets to a known optimum. Supply the `learned` belief for the value-of-information experiment (card 5).

**Out of scope.** Real macro data. Use as the game's research answer; the game shows the exact filter. It does not own fills, balances, NAV, fees, risk, approvals or rankings.

**Inputs.** Only published macro prints, in the row format the seat terminal serves (`series, period_day, published_day, revision, value`). `forecast.features` drops every row published after the as-of day and keeps the latest revision per period. Feature version `forecast-features-2026.10.1`. Generated marks also carry regime information but are deliberately not used, so the filter stays the ceiling.

**Leak guarantees and the tests that enforce them.**

| Guarantee | Test |
|---|---|
| Rows and posterior equal the seat terminal's in a real session | `tests/test_forecast.py::test_rows_and_posterior_match_the_seat_terminal_in_a_real_session` |
| Rewriting, adding or shuffling not-yet-published prints changes no feature and no Bayes posterior; changing a published print does (positive control) | `tests/test_forecast.py::test_canary_future_prints_never_change_features` |
| The hidden regime is a label only, and samples split by family | `tests/test_forecast.py::test_samples_carry_labels_only_outside_the_features_and_split_by_family` |

**Training data and split.** Ungated generated worlds `forecast-<i>`, base variant, split with `split_of`. LightGBM and the MLP early-stop on val. All scores below are on test families.

**Evaluation.** 1 training seed. Test set: 2,082 families, one sample per as-of day with a print. Brier is binary Brier on P(stressed). "Gap" is model minus exact filter on the same test rows. SE is the standard error of per-world mean gaps, so it measures spread across worlds, not across training seeds.

| Quantity | Value | Source |
|---|---|---|
| Worlds generated; families train / val / test | 20000; 15950 / 1968 / 2082 | [forecast.json](results/forecast.json) |
| Test rows; stressed rate | 18738; 0.366 | [forecast.json](results/forecast.json) |
| Training seed; LightGBM best iteration; MLP epochs | 20261015; 150; 34 | [forecast.json](results/forecast.json) |
| Exact Bayes filter: Brier, log loss, ECE | 0.0572, 0.1805, 0.0034 | [forecast.json](results/forecast.json) |
| Chain prior only: Brier, gap (SE) | 0.2228, 0.1656 (0.0021) | [forecast.json](results/forecast.json) |
| Logistic regression: Brier, ECE, gap (SE) | 0.0750, 0.0123, 0.0178 (0.00096) | [forecast.json](results/forecast.json) |
| LightGBM: Brier, ECE, gap (SE) | 0.0577, 0.0044, 0.00043 (0.00013) | [forecast.json](results/forecast.json) |
| MLP: Brier, ECE, gap (SE) | 0.0601, 0.0062, 0.0029 (0.00034) | [forecast.json](results/forecast.json) |

**Known failure modes and limitations.**
- One training seed. Variance across training seeds is not measured.
- Worlds are not passed through the balance gate (the JSON says so). The filter is exact for the ungated generator, but the games agents play are gated, so the distributions differ.
- Synthetic data from one generator and one default `Spec`. The filter assumes that `Spec`; a generator change would move both the data and the ceiling.
- Only the newest period is forecast.
- The JSON has no commit field.

**Reproduce.** `cd ml && uv run --group forecast python scripts/train_forecast.py --worlds 20000`

**Versions.** Features `forecast-features-2026.10.1`; generator `gen-2026.10.1`; macro `macro-2026.10.2`; contract `ml-contracts-2026.10.1`; LightGBM `4.7.0`; torch `2.14.1+cpu`; numpy `2.5.4`.

---

## 3. Anomaly detectors on the books (IsolationForest, Ledoit-Wolf, max |z|)

**What it is.** Three unsupervised detectors fit on clean book states and scored on the labelled B5 fault corpus: scikit-learn `IsolationForest`; Mahalanobis distance under a Ledoit-Wolf covariance; and `anomaly.max_abs_z`, the largest per-feature |z|. The reference is the engine's deterministic controls. Code: `src/fundforge_ml/anomaly.py`, `scripts/train_anomaly.py`.

**Intended use.** Answer one question: without knowing the control rules, can a model trained only on clean books find faulty checkpoints, and which fault classes does it miss?

**Out of scope.** Replacing the controls. Gating dealing, NAV or certificates. It does not own fills, balances, NAV, fees, risk, approvals or rankings.

**Inputs.** Not `Session.view`. This is an internal audit job, like the outbox `internal` audience. `book_state(e)` copies the books at a barrier: journal entries (entity, date, postings, no memo), broker record, pending settlements, confirmations, loans, positions, LP series. It never reads the tape, fault metadata or any control output. `features(book)` turns that into a fixed-length vector (feature version `anomaly-v1`). Memos are excluded because the fault injectors label their entries.

**Leak guarantees and the tests that enforce them.**

| Guarantee | Test |
|---|---|
| `book_state` works with the tape replaced by an object that fails on access; entries carry no memo; extra keys (variant, class, memo, controls, ...) are refused | `tests/test_anomaly.py::test_no_hidden_truth_reaches_features` |
| Features are deterministic and fixed-length | `tests/test_anomaly.py::test_features_deterministic_and_fixed_length` |

**Training data and split.** Not `split_of`: this uses the authored Case1 tape, not generated families. Clean data are seeded random-policy seasons. Split by season seed: seeds below 30 train; the rest plus the 8 B5 golden clean seasons are held out. Faults are `fault_corpus.make(cls, seed)` for each class and seed. Threshold: the score that flags at most 1% of held-out clean checkpoints.

**Evaluation.** 1 model seed. Faults detected per class (each class has 40):

| Quantity | Value | Source |
|---|---|---|
| Clean checkpoints: train; held-out random; held-out golden | 570; 190; 152 | [anomaly.json](results/anomaly.json) |
| Held-out clean flagged, each model; FPR | 3 of 342; 0.0088 | [anomaly.json](results/anomaly.json) |
| Features | 1077 | [anomaly.json](results/anomaly.json) |
| `balanced_unsupported_posting`: IF / LW / max z / controls | 0 / 33 / 31 / 40 | [anomaly.json](results/anomaly.json) |
| `phantom_or_missing_position` | 0 / 0 / 0 / 40 | [anomaly.json](results/anomaly.json) |
| `settlement` | 0 / 0 / 0 / 40 | [anomaly.json](results/anomaly.json) |
| `financing` | 0 / 30 / 30 / 40 | [anomaly.json](results/anomaly.json) |
| `lp_fee` | 0 / 20 / 12 / 40 | [anomaly.json](results/anomaly.json) |
| `statement` | 0 / 0 / 0 / 40 | [anomaly.json](results/anomaly.json) |
| Ledoit-Wolf recall [95% bootstrap CI]: unsupported posting; financing; LP fee | 0.825 [0.7, 0.925]; 0.75 [0.6, 0.875]; 0.5 [0.35, 0.65] | [anomaly.json](results/anomaly.json) |
| Controls on the random clean seasons | 0 of 760 checkpoints flagged | [anomaly.json](results/anomaly.json) |

**Known failure modes and limitations.**
- IsolationForest finds nothing. The season-end state is already at the edge of the clean range, so a gross planted fault lands in the same leaves (documented by `tests/test_anomaly.py::test_isolation_forest_saturates_outside_the_training_range`).
- The two distance models catch only faults that create account pairs clean books never contain. They miss every position, settlement and statement fault, and some variants inside detected classes (for example Ledoit-Wolf finds 0 of 10 `wrong_rate` financing faults and 0 of 9 `provision` LP-fee faults; see the JSON).
- Clean data come from a random policy, not from human or trained play.
- The threshold and the FPR come from the same held-out set.
- Corpus faults are small (at most $10k on $25m, per `docs/PROGRESS.md`).
- Single model seed. No autoencoder.
- Measured on rules `case1-rules-2026.10.15`, before the 28 October rounding fixes.

**Reproduce.** `cd ml && uv run --group anomaly python scripts/train_anomaly.py --seeds 40 --clean-seasons 40`

**Versions.** Features `anomaly-v1`; rules `case1-rules-2026.10.15`; scikit-learn `1.9.1`; numpy `2.5.4`; IsolationForest `random_state` `20261027`; commit `3785744`; controls reference `bench/results/2026-10-17-B5-b1dc767.json`.

---

## 4. VIPER decision tree (PPO distilled)

**What it is.** A scikit-learn decision tree trained to imitate a MaskablePPO teacher with a DAgger loop (Bastani et al. 2018). The tree picks the best valid action under the mask and prints its rules with encoder feature names. Code: `src/fundforge_ml/distill.py`, `scripts/distill_viper.py`.

**Intended use.** Make a learned policy readable: what does the teacher condition on?

**Out of scope.** Playing in rooms. Evidence about trading strategy. It does not own fills, balances, NAV, fees, risk, approvals or rankings.

**Inputs.** The same `obs-v1` vector and action mask as the PPO policy, so the PPO leak tests (card 1) cover it. `tests/test_distill.py` checks that the student never picks a masked action and that features are named.

**Training data and split.** The same gated `ppo-<n>` families and `split_of` split as card 1. Each state is weighted by the spread of the teacher's masked log-probabilities. This is a heuristic: real VIPER uses a Q-function, which PPO does not have. Tree depth and iteration are chosen on val.

**Evaluation.** SMOKE RUN ONLY. The teacher trained for 8,192 steps; there are 2 test worlds. The numbers show the pipeline runs end to end, not what a trained teacher distils to.

| Quantity | Value | Source |
|---|---|---|
| Teacher steps; worlds train / val / test | 8192; 30 / 4 / 2 | [viper_pm.json](results/viper_pm.json) |
| Exported tree (depth 4): leaves; nodes | 6; 11 | [viper_pm.json](results/viper_pm.json) |
| Fidelity to teacher on student states; on teacher states | 0.9; 0.9 (10 test states) | [viper_pm.json](results/viper_pm.json) |
| Tree − teacher reward, paired [95% CI] | 0.0515 [0, 0.103] on 2 worlds | [viper_pm.json](results/viper_pm.json) |
| Tree − random reward | 0.381 [0.136, 0.625] | [viper_pm.json](results/viper_pm.json) |
| Depth-2 tree: leaves; fidelity; tree − teacher | 3; 0.7; -0.034 [-0.11, 0.042] | [viper_pm.json](results/viper_pm.json) |

**Known failure modes and limitations.**
- Smoke scale. 2 test worlds cannot support any claim.
- Every leaf of the exported tree is a reduce action. It has no margin-call split, unlike `bot:v1`'s rules. With an 8,192-step teacher that is weak evidence either way (the JSON's `comparison_note`).
- The weight is a heuristic, not VIPER's Q-based weight.
- The run was made from a dirty worktree (`worktree_dirty: true`), on commit `bdcbac4`.

**Reproduce.** `cd ml && uv run --group train --with scikit-learn python scripts/distill_viper.py --steps 8192 --families 40 --workers 16 --depths 2,4 --iterations 2`. Planned full run (not done): `--steps 600000 --families 400 --workers 16`.

**Versions.** Contract `ml-contracts-2026.10.1`; encoder `obs-v1`; actions `actions-v1`; reward `reward-v1`; scikit-learn `1.9.1`; sb3-contrib `2.9.0`; teacher SHA-256 in the JSON.

---

## 5. Value-of-information belief wrapper

**What it is.** `BeliefWrapper` (`src/fundforge_ml/belief.py`, version `belief-v1`) appends one feature to the PPO observation: P(stressed) for the latest published period. Three modes share one shape: `none` (constant 0.0), `learned` (the logistic forecaster from card 2, trained on train families only) and `exact` (`forecast.bayes`). `scripts/train_voi.py` trains MaskablePPO under each mode and compares them.

**Intended use.** Measure how much reward a better belief buys the policy.

**Out of scope.** Same as card 1. It does not own fills, balances, NAV, fees, risk, approvals or rankings.

**Inputs.** The seat terminal's macro rows at the observation's as-of day. Before the first print the belief is 0.0 in every mode.

**Leak guarantees and the tests that enforce them.**

| Guarantee | Test |
|---|---|
| Belief rows and the exact posterior equal the seat terminal's | `tests/test_belief.py::test_belief_rows_and_exact_posterior_match_the_seat_terminal` |
| Altering every print published after day 15 changes no belief up to day 15, and does change it afterwards (positive control) | `tests/test_belief.py::test_canary_future_macro_print_never_changes_the_belief` |
| All modes share one observation shape; `none` is constant | `tests/test_belief.py::test_modes_share_one_shape_and_none_is_constant` |

**Training data and split.** Gated `ppo-<n>` families split with `split_of`, as in card 1. The learned forecaster uses only train families of the `forecast-<i>` worlds.

**Evaluation.** 3 seeds per mode × 100000 steps on 96 test worlds. Paired reward against `none`: exact Bayes -0.008 [-0.077, 0.061]; learned forecaster -0.089 [-0.164, -0.007] ([voi_pm.json](results/voi_pm.json)).

The one related measured number: on the forecast test set, the logistic model's Brier gap to the exact filter is 0.0178 ([forecast.json](results/forecast.json)).

Logistic regression was chosen over LightGBM so that `learned` sits clearly between `none` and `exact`.

**Known failure modes and limitations.** A better belief bought no measured return: the exact-belief interval includes zero and the learned belief is slightly worse. Random play wins every one of these worlds, so a belief can change score but not tier, and this says nothing about worlds where play can lose. Only 3 seeds per mode.

**Reproduce.** `cd ml && uv run --group train --group forecast python scripts/train_voi.py --role pm --seeds 3 --steps 100000 --families 1000 --forecast-worlds 20000 --n-envs 4 --workers 4`

**Versions.** Belief `belief-v1`; forecast features `forecast-features-2026.10.1`; plus card 1's versions. The script writes them all into the result JSON.
