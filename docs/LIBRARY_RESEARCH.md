# Library research and dependency decisions — v2.1

Reviewed 6 October 2026 against actual repository files and official APIs. This is a source review, **not an installation, compatibility test, security audit or benchmark**. Exact commits, source blobs and license blobs appear in [library_review.json](../fixtures/library_review.json). Default-branch timestamps are narrow maintenance signals, not release pins or support guarantees. At implementation, select supported releases, lock transitive dependencies and review their licenses.

## Recommended small stack

v2.2 decision,7 October2026: retain the17 pinned reviews as6 October evidence rather than redo completed research. SEO/marketing is excluded; the every-app/open-seo entry below is archived research, not an approved candidate or future milestone. No finance-library decision changed. pandas/calendars remain deferred until licensed historical work; DuckDB only if measured snapshot queries justify it. All initial economic systems are original domain code.

The immediate FF0a schema/loader can use Python standard-library types. Pydantic is an adopt-at-API/schema-boundary option, not mandatory economics infrastructure. Fresh official [models](https://docs.pydantic.dev/latest/concepts/models/) and [strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) docs show BaseModel/model_validate and strict validation; strict mode alone does not establish our decimal-string/timestamp/unknown-field rules. [Repository](https://github.com/pydantic/pydantic), [MIT license](https://github.com/pydantic/pydantic/blob/main/LICENSE); retain notices for covered copies and review pydantic-core/transitives when pinning. Current docs/source accessed7 October; no release pin, installed compatibility or performance claim. Low integration effort for bounded typed DTOs; local no credentials/data/API charges; reject using type coercion as financial validation. Use independent financial invariants regardless of schema library.

Retain planned FastAPI ([body models/API](https://fastapi.tiangolo.com/tutorial/body/), [repository/license](https://github.com/fastapi/fastapi/blob/master/LICENSE), MIT) at FF4a, Next.js ([App Router docs](https://nextjs.org/docs/app/getting-started), [repository/license](https://github.com/vercel/next.js/blob/canary/license.md), MIT) at FF5b, PostgreSQL ([row-lock interface](https://www.postgresql.org/docs/current/explicit-locking.html), [license](https://www.postgresql.org/about/licence/)) at persistence. Official current docs/license pages checked7 October, maintenance evidence limited to active docs/source; supported releases/node/python wheels/auth/migration tooling still need milestone validation. Medium app integration, no account required for local operation; DB/dev-server hardware costs and future hosting separate. These frameworks provide transport/UI/transactions, not financial contracts. No cloud, broker, market data or AI credentials required. Document builder has a standard-library fallback; python-docx is optional presentation tooling and not a game dependency.

Keep the proposed Python/FastAPI/Pydantic application, PostgreSQL transaction authority and Next.js interface. These scaffold choices still require FF0 environment/version validation. Build the economic kernel in original Python with standard-library Decimal, typed contracts and an immutable journal. **No trading/backtesting framework is required for FF5 or FF6.**

| Stage | Direct additions | Why and boundary |
|---|---|---|
| First playable / full initial game | No financial framework required; Decimal and authored fixtures | Small equity universe, deterministic costs/risk and investor/firm accounts are custom game rules |
| Historical research FF7 | pandas; exchange_calendars; DuckDB only if snapshot SQL is useful | One dataframe library, explicit venue schedule, read-only analytics; no second writable ledger |
| Evaluated aids FF7 | CVXPY and statsmodels, each behind a justified task | One constrained proposal tool and exposure diagnostics; neither can transact |
| Provider gate FF7 | One narrow entitled adapter; consider OpenBB/OpenSEO only for a demonstrated need | Offline campaign stays independent; rights/cost/failure gate precedes real requests |

NumPy and solver/runtime dependencies may arrive transitively; freeze them with the chosen release instead of assembling every package below. No cloud database, cache cluster, message broker, vector database or AI subscription is required by this design. A PostgreSQL outbox and one worker suffice when asynchronous work is introduced.

FundForge must build its clock/information policy, simultaneous-action serialization, mandate/sleeve authority, settlement/borrow/collateral state machines, fund and firm journals, investor series/fees, scenario causality, recovery/winddown and player-facing explanation. Quant libraries do not supply this connected game.

## Comparison

Effort in the profiles means relative integration/verification burden, not a time estimate. Recommendations apply to the initial equity long/short game.

| Exact repository | License at inspected snapshot | Recommendation |
|---|---|---|
| [openbq-org/OpenBB](https://github.com/openbq-org/OpenBB) | Apache-2.0 | defer |
| [QuantConnect/Lean](https://github.com/QuantConnect/Lean) | Apache-2.0 | reference |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | LGPL-3.0 | reference |
| [lballabio/QuantLib](https://github.com/lballabio/QuantLib) | BSD-style; see notices | reference; defer dependency |
| [attack68/rateslib](https://github.com/attack68/rateslib) | source-available NC/commercial; not open source | reject default-license integration |
| [pandas-dev/pandas](https://github.com/pandas-dev/pandas) | BSD-3-Clause | adopt for research |
| [pola-rs/polars](https://github.com/pola-rs/polars) | MIT | defer |
| [duckdb/duckdb](https://github.com/duckdb/duckdb) | MIT | adopt at historical-data gate |
| [PyPortfolio/PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt) | MIT | defer |
| [dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | BSD-3-Clause | defer |
| [cvxpy/cvxpy](https://github.com/cvxpy/cvxpy) | Apache-2.0; solver terms separate | adopt optional advisory at FF7 |
| [statsmodels/statsmodels](https://github.com/statsmodels/statsmodels) | BSD-3-Clause | adopt optional diagnostics at FF7 |
| [bashtage/arch](https://github.com/bashtage/arch) | NCSA-style permissive | defer |
| [gerrymanoim/exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) | Apache-2.0 | adopt at historical-data gate |
| [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | Apache-2.0 with Commons Clause | reference; reject core dependency |
| [mementum/backtrader](https://github.com/mementum/backtrader) | GPL-3.0-or-later | reject core dependency |
| [every-app/open-seo](https://github.com/every-app/open-seo) | MIT; data rights separate | adapt patterns; defer service |

## Licenses and market-data rights are separate

MIT requires retaining its copyright/permission notice in covered copies; BSD variants add their stated notice/disclaimer/nonendorsement requirements. Apache-2.0 includes license/notice preservation, marking modifications and patent provisions. LGPL/GPL add source/distribution conditions. Restricted licenses are not interchangeable with these. These are engineering screening notes, not a finding that every possible deployment is permitted. Maintain third-party notices and check exact versions/distribution before copying or shipping code.

None of these software licenses grants exchange/provider data display, retention, derived-data, export, training or redistribution rights. Record entitlement scope, audience, venue, territory, retention period, permitted transformations, historical replay rights and deletion obligations. Public accessibility or an API key is insufficient. If retaining raw data is forbidden, a hash alone cannot recreate a replayable dataset: reject that dataset for reproducible replay or obtain suitable rights. No charge was activated.

## Candidate evidence and decisions

### openbq-org/OpenBB

[Repository](https://github.com/openbq-org/OpenBB) · [pinned source/example](https://github.com/openbq-org/OpenBB/blob/ae0268771f761b036996d81bd21522ce79d95415/openbb_platform/core/openbb_core/provider/abstract/fetcher.py) · [pinned license](https://github.com/openbq-org/OpenBB/blob/ae0268771f761b036996d81bd21522ce79d95415/LICENSE). Reviewed branch `develop`, head `ae0268771f76`, committed 2026-10-02. License: Apache-2.0.

**Purpose and evidence.** Provider-neutral financial research ingestion. The inspected `Fetcher` interface separates query transformation, extraction and response transformation and defaults to requiring credentials. This is a useful adapter pattern, not LP accounting. The former OpenBB-finance URL resolves to **openbq-org/OpenBB**; the inspected current license is Apache-2.0, so older AGPL descriptions must not be applied to this snapshot.

**Documentation/maintenance.** Recent dependency work; typed provider contracts and linked documentation are useful, but available fields and entitlements remain provider-specific.

**Fit, effort and cost.** Defer to FF7. Medium: isolate a narrow Python provider adapter and normalize snapshots into our information service. Needs entitled datasets and, often, provider keys; request quotas, hosting and data charges are separate from source licensing.

**Limits/decision.** Defer until one chosen dataset justifies the dependency. Broad provider access is not point-in-time correctness, rights to redistribute, a game market or a broker contract. Prefer a small direct adapter when only one endpoint is needed.

### QuantConnect/Lean

[Repository](https://github.com/QuantConnect/Lean) · [pinned source/example](https://github.com/QuantConnect/Lean/blob/80e7843f645673bcbeaab963049f76f20f6785e1/Common/Securities/BuyingPowerModel.cs) · [pinned license](https://github.com/QuantConnect/Lean/blob/80e7843f645673bcbeaab963049f76f20f6785e1/LICENSE). Reviewed branch `master`, head `80e7843f6456`, committed 2026-10-06. License: Apache-2.0.

**Purpose and evidence.** Algorithmic backtesting/trading engine. `BuyingPowerModel.cs` uses decimal initial/maintenance requirements and validates parameter ranges. Its customizable brokerage/risk structure is a useful counterexample to one universal leverage rule.

**Documentation/maintenance.** Current financial-behavior fixes and code documentation; broad engine ecosystem, but the inspected class is only one buying-power model.

**Fit, effort and cost.** Reference only. Embedding would be high effort: C#/.NET engine, Python interop, separate clock and portfolio semantics to reconcile. Local source does not require a QuantConnect cloud subscription; market data, cloud tooling and services may have separate requirements.

**Limits/decision.** Do not install as a second authoritative engine. Its account models do not establish FundForge's investor-series, firm-ledger or game contracts. Learn test patterns and explicit brokerage assumptions; write original game rules.

### nautechsystems/nautilus_trader

[Repository](https://github.com/nautechsystems/nautilus_trader) · [pinned source/example](https://github.com/nautechsystems/nautilus_trader/blob/4f021bafc2e99c5490cee204b0fc2bd2c83baab4/crates/backtest/src/engine.rs) · [pinned license](https://github.com/nautechsystems/nautilus_trader/blob/4f021bafc2e99c5490cee204b0fc2bd2c83baab4/LICENSE). Reviewed branch `develop`, head `4f021bafc2e9`, committed 2026-10-06. License: LGPL-3.0.

**Purpose and evidence.** Event-driven trading/backtesting infrastructure. Rust `BacktestEngine` owns a virtual clock, data iteration, simulated venues and result state. The inspected README announces a v2 migration; develop is not a safe release pin.

**Documentation/maintenance.** Very recent engine activity and extensive source concepts, with migration risk to API examples.

**Fit, effort and cost.** High: Rust/Python toolchain and another execution/account lifecycle. Backtesting can run on local data; live adapters need venue credentials and fees. No such live adapter is authorized here.

**Limits/decision.** Use as reference for event ordering and replay, defer all embedding. LGPL-3.0 distribution requires its notices/license and applicable library source/modification and relinking obligations; merely calling it permissive would be wrong. Review the exact linking/distribution arrangement before reuse. It adds machinery beyond a 60-day authored campaign.

### lballabio/QuantLib

[Repository](https://github.com/lballabio/QuantLib) · [pinned source/example](https://github.com/lballabio/QuantLib/blob/966a4cc101049ca36a888b2ce223aa96d3f3b22d/ql/time/daycounters/actual360.hpp) · [pinned license](https://github.com/lballabio/QuantLib/blob/966a4cc101049ca36a888b2ce223aa96d3f3b22d/LICENSE.TXT). Reviewed branch `master`, head `966a4cc10104`, committed 2026-10-03. License: BSD-style; see notices.

**Purpose and evidence.** Financial instrument valuation and conventions. `Actual360` computes calendar-day fractions with an explicit endpoint option; it is evidence that a funding day count must be named, not replaced by 252 trading days.

**Documentation/maintenance.** Recent release preparation; clear C++ header and established API/reference material, though integration needs binding-specific documentation.

**Fit, effort and cost.** Low as a convention reference; medium/high as a C++/Python dependency. Valuation needs curves, quotes and instrument terms not supplied by the library. No provider credential is intrinsic to the day counter.

**Limits/decision.** Reference conventions now; defer dependency until derivatives have full lifecycle contracts. Our simple cash-equity fees use our own tested Decimal formulas. Preserve the BSD-style license and relevant embedded notices/nonendorsement conditions if code is reused; inspect bindings separately.

### attack68/rateslib

[Repository](https://github.com/attack68/rateslib) · [pinned source/example](https://github.com/attack68/rateslib/blob/1c4e6f060e1b251f166221a03323336c295ba68a/README.md) · [pinned license](https://github.com/attack68/rateslib/blob/1c4e6f060e1b251f166221a03323336c295ba68a/LICENCE). Reviewed branch `main`, head `1c4e6f060e1b`, committed 2026-04-09. License: source-available NC/commercial; not open source.

**Purpose and evidence.** Fixed-income valuation/curves. Official examples expose `Curve`, `Solver`, and `XCS.rate/npv`; these address rate instruments, not equity fund operations. Review was limited to license, README and public API documentation.

**Documentation/maintenance.** Detailed worked API documentation; sampled default-branch head is an April 2026 license change. That date does not establish whether commercial development is inactive.

**Fit, effort and cost.** Poor initial-game fit. Commercial use and integration require separately agreed paid terms; our task authorizes no purchase.

**Limits/decision.** **Reject integration under the default license.** The inspected source-available noncommercial terms prohibit incorporation into another product, redistribution and modification; this is not an open-source library. Do not assume an educational game qualifies. Reconsider only for a justified future fixed-income feature with explicit suitable rights. No code copied or installed.

### pandas-dev/pandas

[Repository](https://github.com/pandas-dev/pandas) · [pinned source/example](https://github.com/pandas-dev/pandas/blob/85986ab8167ae7eaf968737097562c766a603306/doc/source/user_guide/merging.rst) · [pinned license](https://github.com/pandas-dev/pandas/blob/85986ab8167ae7eaf968737097562c766a603306/LICENSE). Reviewed branch `main`, head `85986ab8167a`, committed 2026-10-06. License: BSD-3-Clause.

**Purpose and evidence.** Tabular research/preparation. The merging guide and official `merge_asof` API show sorted time-based matching with backward/forward/nearest modes. FundForge must use availability timestamps and backward matching, plus entity/revision filters; a date join alone is insufficient.

**Documentation/maintenance.** Recent CSV correctness work and detailed API examples make a narrow research dependency supportable.

**Fit, effort and cost.** Adopt for offline FF7 research and fixture tooling when needed; low effort in the planned Python stack. Local processing needs no credentials, but imported financial data still needs rights and storage.

**Limits/decision.** Never use floating DataFrame balances as the authoritative ledger. A convenient join does not prevent revisions, survivorship or publication-lag leakage. Prefer one tabular library initially. Install a supported release with a lockfile at implementation time, not the inspected development SHA.

### pola-rs/polars

[Repository](https://github.com/pola-rs/polars) · [pinned source/example](https://github.com/pola-rs/polars/blob/a3e0097fd186aac6ed82d85ad585abe8f0d4c5f0/py-polars/src/polars/lazyframe/frame.py) · [pinned license](https://github.com/pola-rs/polars/blob/a3e0097fd186aac6ed82d85ad585abe8f0d4c5f0/LICENSE). Reviewed branch `main`, head `a3e0097fd186`, committed 2026-10-06. License: MIT.

**Purpose and evidence.** Rust-backed dataframe/lazy query processing. The inspected Python `LazyFrame` source and official `join_asof` API support lazy workflows and time matching.

**Documentation/maintenance.** Recent record-batch work; detailed typed API documentation. This review did not benchmark FundForge data.

**Fit, effort and cost.** Low/medium Python adapter effort, local compute/memory/storage only unless connected to paid services. Source can be used without Polars Cloud.

**Limits/decision.** Defer until profiling shows pandas preparation is a material bottleneck. Adding both now increases conversion semantics and dependency work without a demonstrated benefit. Sortedness, availability, dtype and revision rules still belong to FundForge; never make lazy evaluation order determine economic events.

### duckdb/duckdb

[Repository](https://github.com/duckdb/duckdb) · [pinned source/example](https://github.com/duckdb/duckdb/blob/5070de3585e846718fac121b5b149f4236e6a58a/src/include/duckdb/main/connection.hpp) · [pinned license](https://github.com/duckdb/duckdb/blob/5070de3585e846718fac121b5b149f4236e6a58a/LICENSE). Reviewed branch `v2.0-cyanoptera`, head `5070de3585e8`, committed 2026-10-06. License: MIT.

**Purpose and evidence.** Embedded analytical SQL. `Connection` exposes query/prepare operations; official Parquet documentation describes direct file queries with filtering/projection. Useful for reproducible snapshot exploration and debrief analytics.

**Documentation/maintenance.** Recent numeric fixes and focused query examples. The reviewed default branch is a development branch, not a production recommendation.

**Fit, effort and cost.** Adopt at FF7's historical-data gate if SQL over frozen files is useful; low/medium local Python integration. No server credentials for local files; storage and data licensing remain separate costs.

**Limits/decision.** Read-only analytics over immutable exports. PostgreSQL remains multiplayer command authority. Do not introduce DuckDB as a second writable fund database, assume extension safety, or allow players arbitrary file/network SQL. Whitelist inputs; record query/schema versions.

### PyPortfolio/PyPortfolioOpt

[Repository](https://github.com/PyPortfolio/PyPortfolioOpt) · [pinned source/example](https://github.com/PyPortfolio/PyPortfolioOpt/blob/a6638d2e06dae6f444fd022cfd4b3c528902a85b/pypfopt/efficient_frontier/efficient_frontier.py) · [pinned license](https://github.com/PyPortfolio/PyPortfolioOpt/blob/a6638d2e06dae6f444fd022cfd4b3c528902a85b/LICENSE). Reviewed branch `main`, head `a6638d2e06da`, committed 2026-07-07. License: MIT.

**Purpose and evidence.** Portfolio optimization convenience layer. `EfficientFrontier` uses CVXPY and exposes weight bounds, covariance and portfolio objectives. Its default bounds are long-only; a long/short game cannot inherit those silently. The former robertmartin8 URL now resolves to **PyPortfolio/PyPortfolioOpt**.

**Documentation/maintenance.** Clear class documentation and examples; sampled July head updates README links, which is maintenance evidence but not proof of recent optimization improvements.

**Fit, effort and cost.** Low/medium research integration; requires defensible expected returns/covariance, not credentials by itself. Solvers and data have separate terms.

**Limits/decision.** Defer. Good educational baseline if that becomes the research task, but direct CVXPY is a cleaner single choice for custom mandate/cash constraints. Floating target weights are not integer, borrowable, settled trades, and optimizer output cannot override reservations or margin.

### dcajasn/Riskfolio-Lib

[Repository](https://github.com/dcajasn/Riskfolio-Lib) · [pinned source/example](https://github.com/dcajasn/Riskfolio-Lib/blob/7b1b26ac9760974c12ecefe290a9d3bd37b66b7a/riskfolio/src/Portfolio.py) · [pinned license](https://github.com/dcajasn/Riskfolio-Lib/blob/7b1b26ac9760974c12ecefe290a9d3bd37b66b7a/LICENSE.txt). Reviewed branch `master`, head `7b1b26ac9760`, committed 2026-10-04. License: BSD-3-Clause.

**Purpose and evidence.** Broad portfolio/risk optimization. `Portfolio.py` exposes numerous risk measures and constraints and imports CVXPY, SciPy, scikit-learn, pandas and compiled support.

**Documentation/maintenance.** Recent documentation work; extensive parameter/reference coverage, with a greater learning and verification burden than this game needs.

**Fit, effort and cost.** Medium/high integration and solver validation. Historical returns/factors are required; some formulations need solver capabilities with separately checked licenses/costs.

**Limits/decision.** Defer. Its breadth overlaps CVXPY, PyPortfolioOpt and our risk service; selecting a library does not validate tail estimates from a short season. Add only for a specific evaluated diagnostic, not to populate many menus. No bundled investor/fund accounting solution.

### cvxpy/cvxpy

[Repository](https://github.com/cvxpy/cvxpy) · [pinned source/example](https://github.com/cvxpy/cvxpy/blob/5c569b461c62aa7d93e06fd3994213ae3fc4af5c/cvxpy/problems/problem.py) · [pinned license](https://github.com/cvxpy/cvxpy/blob/5c569b461c62aa7d93e06fd3994213ae3fc4af5c/LICENSE). Reviewed branch `master`, head `5c569b461c62`, committed 2026-10-04. License: Apache-2.0; solver terms separate.

**Purpose and evidence.** Convex modeling. The `Problem` implementation and official quadratic-program example expose variables, objectives, constraints, solution status and dual values. These can explain why a proposed allocation is constrained.

**Documentation/maintenance.** Recent solver fix; a concise worked portfolio/QP example provides a strong starting point.

**Fit, effort and cost.** Adopt one optional advisory optimizer at FF7, after hand-authored/heuristic baselines. Medium effort: freeze inputs, tolerance, solver and version; handle infeasible, unbounded, inaccurate and timeout outcomes. CPU use locally; solver licenses must be reviewed separately and a paid solver is not authorized.

**Limits/decision.** Cannot solve every real fund tradeoff as a convex problem. Borrow discreteness, fill capacity, deadlines and integer trades need later validation. Suggestions become ordinary proposals; deterministic Decimal checks own acceptance. Record the suggestion artifact for replay instead of assuming bitwise solver reproducibility.

### statsmodels/statsmodels

[Repository](https://github.com/statsmodels/statsmodels) · [pinned source/example](https://github.com/statsmodels/statsmodels/blob/8278e2d218cc85bac2c7af02feb9a19a0e499b04/examples/python/rolling_ls.py) · [pinned license](https://github.com/statsmodels/statsmodels/blob/8278e2d218cc85bac2c7af02feb9a19a0e499b04/LICENSE.txt). Reviewed branch `main`, head `8278e2d218cc`, committed 2026-10-06. License: BSD-3-Clause.

**Purpose and evidence.** Statistical estimation/diagnostics. `examples/python/rolling_ls.py` fits rolling market/three-factor regressions and shows confidence intervals and missing early-window outputs.

**Documentation/maintenance.** Recent OLS-influence work and an explanatory worked example, suitable for teaching exposure estimation uncertainty.

**Fit, effort and cost.** Adopt optional FF7 attribution diagnostics, medium effort. Needs a sufficiently long as-of training history and identified factor series; downloading example financial datasets is not a grant of redistribution rights.

**Limits/decision.** The 60 gameplay days alone are not a defensible estimation history. Campaign factor exposure can use disclosed authored coefficients first. Keep ex-post descriptive attribution separate from available-at forecasts; residual return is not proof of manager skill or causal alpha.

### bashtage/arch

[Repository](https://github.com/bashtage/arch) · [pinned source/example](https://github.com/bashtage/arch/blob/65e7df12eed42d7544ede7cfa25dd8e5f45ac268/arch/univariate/mean.py) · [pinned license](https://github.com/bashtage/arch/blob/65e7df12eed42d7544ede7cfa25dd8e5f45ac268/LICENSE.md). Reviewed branch `main`, head `65e7df12eed4`, committed 2026-10-06. License: NCSA-style permissive.

**Purpose and evidence.** Time-series volatility/econometrics. The inspected `arch.univariate.mean` module connects mean models with GARCH-family volatility/distributions and forecasting machinery.

**Documentation/maintenance.** Recent lint activity; module documentation is detailed, but the sampled commit does not demonstrate a new model improvement.

**Fit, effort and cost.** Medium research effort: calibration, out-of-sample targets, convergence and forecasting evaluation. No credential needed for local fitting; sufficient licensed historical returns are needed.

**Limits/decision.** Defer until a simple historical/stress baseline fails a stated requirement. A more elaborate volatility fit must not create unjustified confidence in liquidation risk. License is permissive NCSA-style with retained notices/disclaimers and nonendorsement, rather than casually relabeling it MIT.

### gerrymanoim/exchange_calendars

[Repository](https://github.com/gerrymanoim/exchange_calendars) · [pinned source/example](https://github.com/gerrymanoim/exchange_calendars/blob/bbda29fed902374bdb75acab008f421fbd567823/exchange_calendars/exchange_calendar_xnys.py) · [pinned license](https://github.com/gerrymanoim/exchange_calendars/blob/bbda29fed902374bdb75acab008f421fbd567823/LICENSE). Reviewed branch `master`, head `bbda29fed902`, committed 2026-09-15. License: Apache-2.0.

**Purpose and evidence.** Exchange sessions/holidays. The XNYS implementation includes historical holiday and early-close rules. Useful when the game first consumes dated real-market observations.

**Documentation/maintenance.** Recent exchange-specific closure fix and documented calendar classes; calendar revisions still require frozen versions and regression dates.

**Fit, effort and cost.** Adopt at FF7, low/medium Python integration. Local schedules need no credentials. Match supported venue, era and timezone; persist the resolved schedule.

**Limits/decision.** Exchange sessions are not a universal settlement/banking calendar. The base authored game deliberately uses its explicit Monday–Friday synthetic calendar and no exchange holidays. Do not retroactively change it by installing this package. A real-calendar mode needs separately defined settlement and funding dates.

### polakowo/vectorbt

[Repository](https://github.com/polakowo/vectorbt) · [pinned source/example](https://github.com/polakowo/vectorbt/blob/ceffc501f2d37033a79dd86a9f883e69ec6977bd/vectorbt/portfolio/base.py) · [pinned license](https://github.com/polakowo/vectorbt/blob/ceffc501f2d37033a79dd86a9f883e69ec6977bd/LICENSE.md). Reviewed branch `master`, head `ceffc501f2d3`, committed 2026-09-26. License: Apache-2.0 with Commons Clause.

**Purpose and evidence.** Fast vectorized backtesting/research. `portfolio/base.py` documents `Portfolio.from_orders/from_signals` and portfolio simulation examples.

**Documentation/maintenance.** Recent documentation updates and approachable examples; this review made no speed comparison.

**Fit, effort and cost.** Medium/high to reconcile vectorized cash/positions with our chronological ledger and two-person commands. Local historical data may be enough for a study; Numba/runtime and dataset requirements remain.

**Limits/decision.** Reference only; reject as core dependency. Current license is **Apache-2.0 with Commons Clause**, restricting sale of products/services whose value derives substantially from its functionality; it is not plain Apache and does not simply prohibit every commercial use. Any future inclusion needs a distribution-specific rights decision. No reason to build a second, economically different simulator for the MVP.

### mementum/backtrader

[Repository](https://github.com/mementum/backtrader) · [pinned source/example](https://github.com/mementum/backtrader/blob/b853d7c90b6721476eb5a5ea3135224e33db1f14/backtrader/brokers/bbroker.py) · [pinned license](https://github.com/mementum/backtrader/blob/b853d7c90b6721476eb5a5ea3135224e33db1f14/LICENSE). Reviewed branch `master`, head `b853d7c90b67`, committed 2023-04-19. License: GPL-3.0-or-later.

**Purpose and evidence.** Python event-driven strategy backtesting. `BackBroker` documents next-bar market execution, limit/stop handling and a configurable filler; the default filler configuration is not FundForge's capacity/partial-fill contract.

**Documentation/maintenance.** Useful source documentation, but the inspected default-branch head is April 2023 (repository push metadata alone is newer). Treat compatibility/maintenance as unproven, not conclusively abandoned.

**Fit, effort and cost.** High semantic integration despite Python compatibility; local data can avoid service credentials. Third-party feeds have separate access/cost.

**Limits/decision.** Reject core dependency. GPL-3.0-or-later obligations on distribution of covered/combined work need review; a private repository is not a blanket license solution. It overlaps our engine without providing LP series, firm survival or joint authority. Keep the explicit future-event lesson; build the small game executor.

### every-app/open-seo

[Repository](https://github.com/every-app/open-seo) · [pinned source/example](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/mcp/tools/get-domain-overview.ts) · [pinned license](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/LICENSE). Reviewed branch `main`, head `ccd2077d47c3`, committed 2026-10-06. License: MIT; data rights separate.

**Purpose and evidence.** SEO research/marketing service, separate from OpenBB. The domain-overview tool returns scoped estimated digital-activity metrics with project authorization, geography/language and credit-charging behavior.

**Documentation/maintenance.** Current upstream blog/README activity and typed tool implementations; no full service/security or billing audit was performed. The user's earlier name remains interpreted as every-app/open-seo, upstream of afazhriel/openseo, not conclusively confirmed intent.

**Fit, effort and cost.** Adapt limited engineering patterns; defer runtime service to FF7. Medium for a narrow fixture/adapter, high for operating its whole TypeScript/Cloudflare application. DataForSEO credentials and real provider charges are distinct from fictional research points.

**Limits/decision.** No initial runtime dependency. See OPENSEO_INTEGRATION for source mapping, rights, charging failures and cutoff contract. Estimated traffic/search interest is not sales, market data or alpha. Marketing-site SEO is a separate future use, not gameplay infrastructure. MIT code rights do not grant rights to provider data.

## Official API supplements and verification limits

- [pandas merge_asof](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html): sorted time matching and direction.
- [Polars LazyFrame.join_asof](https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.join_asof.html): lazy as-of API.
- [DuckDB Parquet documentation](https://duckdb.org/docs/stable/data/parquet/overview): file-query examples; follow current redirected documentation when implementing.
- [CVXPY quadratic programming](https://www.cvxpy.org/examples/basic/quadratic_program.html): objective, constraints and dual outputs.
- [rateslib official API examples](https://rateslib.com/py/en/latest/): fixed-income capability and license boundary.
- [OpenBB company information](https://openbb.co/company/about/): OpenBQ stewardship context; the pinned repository license controls this review.

No source implementation was copied. Recommendations are architectural judgments from the inspected evidence, not upstream claims. The lower-effort alternative is our own small deterministic game engine, not an unexamined trading framework. Future alternatives require a concrete unmet requirement and the same review fields.
