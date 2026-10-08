# Research and analytics plan

7 October 2026. Planning document; nothing here is installed or implemented. It assigns pandas, exchange_calendars, DuckDB, CVXPY and statsmodels to concrete features in [FULL_GAME_PLAN](FULL_GAME_PLAN.md) milestones. It reuses the 6 October repository and license reviews in [LIBRARY_RESEARCH](LIBRARY_RESEARCH.md) and adds current release facts checked on 7 October 2026. This plan supersedes LIBRARY_RESEARCH's "defer until licensed historical data" decision for pandas and exchange_calendars only; that document should be updated to match (FULL_GAME_PLAN §9).

## 1. The boundary rule

The authoritative money path stays Decimal and pure. Analytics are read-only, may use float, and never feed back into postings.

| Rule | Enforcement |
|---|---|
| Separate package | Analytics live in `backend/src/fundforge_analytics/`. Core is `backend/src/fundforge/`. Libraries are an optional dependency group `analytics` (runtime) plus `authoring` (dev-only, for tape generation). |
| Core never imports analytics | `tests/test_import_boundary.py` parses every core module with `ast` and fails if it imports `pandas`, `numpy`, `scipy`, `duckdb`, `cvxpy`, `statsmodels`, `exchange_calendars` or `fundforge_analytics`. Stdlib `ast` is enough; no import-linter dependency. |
| Analytics see only as-of data | Analytics functions accept the player view dict (`Session.view` output) or a finished-room export, never an `Engine`, `Tape`, `Store` or journal object. The same AST test fails if `fundforge_analytics` imports `fundforge.engine`, `fundforge.tape`, `fundforge.store` or `fundforge.journal`. |
| Core runs without analytics | A CI job installs the default groups only and runs the full core suite. If a core test needs pandas, the job fails at import. |
| No float reaches a posting | Analytics outputs are reports or suggestions: whole-share integer quantities and display numbers. Money enters the ledger only through an ordinary human command that `governance.py` revalidates with Decimal at commit and again at execution. There is no API route that applies an analytic result directly. |
| Advisory is recorded, not replayed | An optimizer or report result is stored as an artifact (input view digest, library and solver versions, status, output). Replay of the game never re-runs analytics; replay hashes are unaffected by whether analytics are installed. |
| Fixtures stay Decimal | Generators may compute in float, but the committed fixture is Decimal-string JSON quantized explicitly (prices to 0.000001, volumes to integers) with a digest. `tape.compile_tape` already rejects malformed fixtures. |

## 2. No-future-information rules for every analytic

| Analytic | Allowed input | Leak test |
|---|---|---|
| In-game risk/beta report | Marks with `available_at` ≤ current barrier, from the view | Mutate every tape row after the current event; report output hash unchanged |
| Advisory optimizer | Current view, published margin coefficients, sleeve terms, current tape event volume only if already published | Same mutation test; plus an announced-but-not-effective coefficient change is only used if the view shows it |
| Post-game attribution | Full history, but only when `clock.finished` is true | API returns 409 before the room finishes; test asserts it |
| Exports (CSV/Parquet) | During play: as-of view only. After finish: full journal | Export created mid-game contains no row with event date after the clock; test compares max date |
| Tape authoring | Author-side, not player-facing | Generated fixture never shipped to the client bundle (existing rule); test greps the built frontend for tape keys |
| As-of tape store (DuckDB) | Queries must carry `as_of` and filter `available_at <= as_of`, latest revision per key at that time | Insert a later revision of an earlier price; earlier as-of query result unchanged |

## 3. Dependency facts (checked 7 October 2026)

Versions, licenses and Python support from the PyPI JSON API (`https://pypi.org/pypi/<name>/json`), read directly on 7 October 2026. The repo targets Python ≥3.12 and was tested locally on 3.14.3; all five publish CPython 3.14 Windows wheels for these releases. Pin exact versions in `uv.lock` when a milestone adds them; these numbers will age.

| Package | Latest release (upload date) | License | Requires-Python | Notable runtime deps | Source pages checked |
|---|---|---|---|---|---|
| pandas | 3.0.6 (2026-09-17) | BSD-3-Clause | ≥3.11 | numpy ≥2.3.3 on 3.14, python-dateutil, tzdata (Windows) | [PyPI JSON](https://pypi.org/pypi/pandas/json), [merge_asof docs](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html) |
| exchange_calendars | 4.13.2 (2026-03-10) | Apache-2.0 | ≥3.10, <4 | pandas, numpy (via its own deps) | [PyPI JSON](https://pypi.org/pypi/exchange-calendars/json), [repository](https://github.com/gerrymanoim/exchange_calendars) |
| duckdb | 1.5.6 (2026-09-28) | MIT (classifier) | ≥3.10 | none required | [PyPI JSON](https://pypi.org/pypi/duckdb/json), [Parquet docs](https://duckdb.org/docs/stable/data/parquet/overview) |
| cvxpy | 1.9.3 (2026-09-19) | Apache-2.0 | ≥3.11 | numpy ≥2, scipy, osqp (Apache-2.0), clarabel (Apache-2.0), scs (MIT), highspy | [PyPI JSON](https://pypi.org/pypi/cvxpy/json), [solver docs](https://www.cvxpy.org/tutorial/solvers/index.html); bundled solver licenses from their PyPI JSON |
| statsmodels | 0.15.0 (2026-08-27) | BSD-3-Clause | ≥3.10 | numpy, scipy, pandas, patsy, formulaic | [PyPI JSON](https://pypi.org/pypi/statsmodels/json), [regression docs](https://www.statsmodels.org/stable/regression.html) |

Notes:
- pandas 3.0 is a major release; code written against 2.x examples (copy-on-write, string dtype defaults) needs checking when G4 starts.
- duckdb's PyPI metadata has no `license_expression`; the MIT classifier matches the pinned LICENSE reviewed in LIBRARY_RESEARCH.
- highspy's license was not confirmed from PyPI metadata in this check (field empty); confirm before shipping a container that includes it.
- The CVXPY quadratic-program example page cited in LIBRARY_RESEARCH returned HTTP 503 on 7 October; the solver page loaded. Recheck before G10.
- No paid solver, data provider or hosted service is needed for anything below.

## 4. Feature assignments

Candidates evaluated against: does it make the game or the engineering better, can it be tested falsifiably, and can it stay outside the money path.

| Candidate | Verdict | Reason |
|---|---|---|
| pandas for tape authoring, exports and the balance study | Adopt (G4 authoring, G9 exports) | The 60-day, twelve-instrument tape is real authoring work; generating it from a factor model is the cheapest honest way. Exports are what LPs and recruiters read |
| statsmodels beta report and post-game attribution | Adopt (G9) | Connects the authored factor model to an estimated one; planted-beta recovery is a clean test. Must be labeled diagnostic (60 days is a short sample) |
| CVXPY advisory "quant analyst" | Adopt as stretch (G10) | The cure problem in Case1 (cheapest feasible reduction under margin, mandate and capacity) is convex and has a ready baseline: the engine's largest-value-first heuristic |
| exchange_calendars real-session variant | Adopt as stretch (G11) | Holidays make ACT/365, ACT/360 and T+1 tests harder in a useful way, with no data licensing |
| DuckDB/Parquet as-of tape store | Adopt as stretch (G11), optional | Earns its place only for versioned, revisable tapes and multi-run balance queries. pandas covers single-run analysis, so DuckDB is not added earlier |
| Historical replay with real prices | Not planned | Needs data with display, retention and redistribution rights (LIBRARY_RESEARCH §Licenses). Revisit only if such a dataset is identified |

### 4.1 pandas — tape authoring (G4) and exports (G9)

**Authoring tool** `tools/author/generate_tape.py` (dev-only `authoring` group): from a declared market factor, five sector factors and idiosyncratic shocks with authored betas, a seeded `numpy.random.Generator` (PCG64, seed recorded) produces daily reference prices and volumes; pandas assembles the event table; a final step quantizes to Decimal strings and writes the fixture plus a manifest (generator version, seed, parameter hash, fixture digest).

**Exports** in `fundforge_analytics/exports.py`: LP statements per series, fund and firm journal CSV/Parquet, chapter bridge tables. Money columns are written from the Decimal strings in the journal, not recomputed in float.

Tests:
- Same seed and parameters produce a byte-identical fixture (digest equality).
- Every generated price is positive and quantized to 0.000001; volumes are positive integers; `tape.compile_tape` accepts it.
- Realized betas in the generated tape, estimated with statsmodels OLS, fall within the authored beta's 95% interval for at least 95% of instruments across 20 seeds (author-side sanity check, not a game claim).
- Export totals equal `Journal.balances` to the cent for every account; an export taken mid-game has no rows after the current clock.

### 4.2 statsmodels — risk diagnostic and debrief attribution (G9)

**In-game diagnostic**: on the risk card, beside the authored market sensitivity (GAME_SYSTEMS §7), show a rolling OLS beta of the fund's flow-neutral index on the published market ETF returns, with its confidence interval and the sample size. Hidden when fewer than 20 observations exist. Labeled "estimate; authored sensitivities drive stress tests".

**Debrief attribution** (finished rooms only): regress daily fund index returns on market and sector factor returns over the season; report coefficients, intervals, R² and residual. Present residual as "unexplained by these factors", never as alpha or skill (MASTER_SPEC §7, GAME_SYSTEMS §10).

Tests:
- Planted beta recovery: synthetic series with beta 0.8, known noise and 60 observations; estimated beta within the reported 95% interval in at least 93 of 100 seeds (a test of interval calibration, with slack for sampling).
- With beta 0 planted, the interval covers 0 at the same rate.
- Fewer than 20 observations: the diagnostic returns "insufficient sample", not a number.
- Leak test from §2; debrief endpoint returns 409 before finish.
- Evaluation, not a pass/fail: report the gap between estimated and authored portfolio beta across G7 balance-runner policies, in ENGINEERING.md.

### 4.3 CVXPY — advisory quant analyst (G10, stretch)

**Feature**: on a margin call or a requested rebalance, either partner can ask the analyst for a draft. It solves for per-instrument trade quantities that cure the deficit at least impact cost, subject to:
- maintenance requirement after trades plus total impact cost ≤ NAV (the engine's `C(Q) = ref·Q·[h + k(Q/V)²]/10⁴` is convex for Q ≥ 0, so this is a convex constraint with per-side nonnegative variables);
- per-event participation capacity from the published volume;
- gross, net, issuer, sector and ETF limits; sleeve sides and turnover remaining; restricted instruments fixed at zero trade;
- optional: keep net exposure within a band the players choose.

The continuous solution is rounded to whole shares, then sent to the G3 Decimal **plan preview**. Only a draft that passes the preview at every executable prefix is shown. The draft appears as an unsigned package; the proposer and the other partner must sign its digest like any package. The analyst cannot sign, submit, or count as a partner, and it is never called by the engine for forced liquidation.

Outcomes handled explicitly: optimal, infeasible (show which constraint group blocks, from the problem's duals or by dropping groups), solver error or timeout (show "no suggestion"). Solver chosen once and pinned (a bundled open-source one: Clarabel, OSQP or SCS); its name and version go into the stored artifact.

Tests and evaluation:
- Feasibility: on Case1 day 16 and on 200 randomly generated books, every displayed draft passes the Decimal preview with zero hard-limit breaches; drafts that fail after rounding are counted and reported, not shown.
- Infeasible fixture (deficit larger than all published capacity can cure) returns infeasible, not a partial draft presented as a cure.
- Baselines on the same books: (a) the engine's largest-value-first forced-liquidation heuristic, (b) pro-rata sale of all longs. Report median and worst-case impact cost and residual deficit. The feature ships only if the optimizer's cure cost is no worse than baseline (a) on every book where both are feasible; otherwise it is dropped and the result is recorded.
- Authority: a test that an analyst draft cannot be executed without two human signatures on its digest, and that the analyst module has no import path to `governance.py` command handlers.
- Leak test from §2.

### 4.4 exchange_calendars — real session calendar variant (G11, stretch)

**Feature**: an optional scenario version of the days 1–21 opening arc on the XNYS 2026 calendar. The base campaign keeps its synthetic Mon–Fri calendar with fictional holiday trading (SCENARIO_CONTRACTS); this is a separate fixture, not a change to existing cases.

Calendar resolution happens at authoring time: the tool resolves sessions with exchange_calendars and writes an explicit session list and the package version into the fixture. `tape.py` reads that list instead of computing the Nth weekday, so core never imports the package and a later calendar release cannot change a replay. Settlement uses the same session list as a declared house rule; exchange sessions are not a full banking calendar (LIBRARY_RESEARCH).

Tests:
- XNYS sessions exclude Monday 19 January and Monday 16 February 2026; the fixture's session list matches the package output for the season range.
- A Friday 16 January trade settles Tuesday 20 January (T+1 on the session list).
- Management fee ACT/365 and borrow ACT/360 accrue for every calendar date including the holiday, so the Tuesday 20 January close accrues four dates (17–20 January).
- Changing the installed package version does not change the replay hash of an existing room (the fixture carries the dates).

### 4.5 DuckDB — Parquet as-of tape store and balance-study queries (G11, stretch)

**Feature**: tapes and evidence stored as Parquet with `(instrument, event_time, available_at, revision)`; a read-only DuckDB connection answers as-of queries for authoring and analysis. The G7 balance runner writes one Parquet file per (policy, tape version, rules version) run, and DuckDB queries compare outcomes across runs. PostgreSQL remains the only writable authority for live rooms; DuckDB is never in the request path of a game command, and players cannot submit SQL.

Tests:
- The as-of query with `available_at <= as_of` returns the latest revision visible at that time; inserting a later revision of an earlier price leaves earlier query results unchanged.
- A tape loaded from Parquet through the authoring tool produces the same fixture digest as the JSON source.
- Balance-study query totals match the per-run JSON outcomes produced by the engine.
- DuckDB connections open with `read_only=True` on the store files.

Adoption rule: if by G11 the balance study is small enough that pandas handles it in under a few seconds, the DuckDB part is skipped and the decision recorded.

## 5. Milestone map

| Milestone | Library | Feature | Group |
|---|---|---|---|
| G4 | pandas (+ numpy) | Tape generator for the opening arc and later season | `authoring` (dev) |
| G7 | pandas | Balance runner result tables | `authoring` (dev) |
| G9 | pandas, statsmodels | Exports, risk diagnostic, debrief attribution, boundary tests | `analytics` |
| G10 | CVXPY + one pinned open-source solver | Advisory quant analyst | `analytics` |
| G11 | exchange_calendars, DuckDB | Real-calendar variant, as-of Parquet store | `authoring` / `analytics` |

## 6. What this plan does not claim

No library listed here is installed in the repository today. No accuracy, speed or cost-saving number exists yet; each test above produces one when run. A recovered synthetic beta shows the estimator works on planted data, not that the game's markets resemble real ones. An optimizer that beats a heuristic in this model says nothing about real portfolio construction. Game results are not investment performance.
