# Implementation plan v2.1

The game must be fun and financially coherent before optional ML or live integrations. Work is dependency-gated, not a promise to finish in a fixed week. Every implementation milestone is currently pending. The user requested this redesign and file update; that does not mean application code has been built.

Read REALISM_AUDIT for priorities, SIMULATION_ARCHITECTURE for ownership/interfaces, and LIBRARY_RESEARCH before adding a dependency. v2.1 corrects fee participation, day counts, annual versus redemption crystallization, cover-direction risk, post-redemption leverage and independent control evidence. Implement those contracts before adding presentation.

| Gate | Scope | Dependencies | Observable completion |
|---|---|---|---|
| FF0 | Inspect environment; freeze domain contracts; minimal app/DB/CI skeleton | P01 review | Versioned scenario schema, event phases, entities, command results, reproducible install and health checks |
| FF1 | Journal, marks, lots, LP series, dated calendar accrual, trade/settlement obligations, separate firm ledger | FF0 | Independent cohort/HWM/day-count/corporate-action arithmetic, balance/replay/reversal and external-control discrepancy evidence |
| FF2 | Clock, future-event execution, costs/participation, long/short borrow, financing, margin and forced actions | FF1 | Gap, recall, collateral, deadline and halt cases; no fabricated fills |
| FF3 | Two-player authorization, sleeves, committee proposals, reservations and races | FF1–FF2 contracts | PostgreSQL race tests; no expired/revoked authority, double spend or third partner |
| FF4 | LP contracts/notices/dealing, fees/HWM, management-company budget, NPC trust | FF1–FF3 | Subscriptions/redemptions/fees reconcile; fund cash cannot pay firm payroll directly |
| FF5 | Integrate the two-chapter opening arc, authored research, crisis choices, save/resume and causal debrief | FF2–FF4 | Two people finish 20 business days through ordinary day21 opening administration, offline from providers; target two 20–30 minute chapters, duration unmeasured |
| FF6 | Six-chapter campaign, all three scenario contracts, endings, scoring, difficulty/balance, security and recovery | FF5 | Complete 60-day run through ordinary day61 opening administration; tested failure/winddown; versioned balance/replay and two-user playtest evidence |
| FF7 | Licensed snapshots, optional OpenSEO adapter spike, shared-engine backtests, evaluated ML | FF6 | Point-in-time data gate, provider failure/cost checks, honest baseline comparison |
| FF8 | Optional asynchronous league/opponents, extra strategies/instruments, private hosting | Relevant prior gates | Separate permission, fairness, data and instrument acceptance contracts |

FF1–FF4 are engine foundations. FF5 is the first playable two-chapter release; FF6 is the full initial game. Neither may drop LPs, financing, firm survival and a real crisis merely to declare success early. FF7 is not a prerequisite for enjoyable play.

## FF0: freeze interfaces without overbuilding

Inspect actual tools/runtime versions and repository state. Choose one Python and one frontend package manager; pin and lock versions. Set up local PostgreSQL and CI. Confirm production authentication separately from controlled development identities. Do not build five dashboards first.

Write schemas for SeasonConfig, MarketEvent, Observation, Fund, Firm, InvestorSeries, Mandate, SleeveAuthority, ProposalVersion, Order, Reservation, Fill, BorrowContract, JournalEntry, MarginCall, LPNotice, ResearchTask, ChapterCheckpoint, independent ControlRecord and Debrief. Include schema/rules/data versions, monotonic event sequence, calendar dates/business-day indexes, simulated phases, wall-clock audit time and actor/economic identities. Freeze unsupported-action rejection, version conflicts and stale-mark behavior. Validate one authored scenario; a manifest without a complete tape/control records is not a runnable season.

Proposed package boundaries: `backend/domain/accounting`, `market`, `governance`, `fund_operations`, `game`; `backend/application` for transactions; `backend/adapters` for persistence/providers; `frontend` for views. Freeze the command/result contracts before parallel implementation. A modular monolith is sufficient.

## FF1–FF2: economics before presentation

Implement cash, restricted collateral, receivables, payables, debt, holdings, short liabilities, fund fees, LP capital and firm accounts without network calls. Trade-date postings and cash settlement are different events. Keep gross assets, NAV, margin equity, liquidity available for payments and company runway separate.

Use the legacy `fixtures/golden_scenario.json` only as the no-cost accounting smoke reference. It does not define campaign investors or capital. Add independent examples for short gains/losses, borrow expense, dividends in lieu, debt interest, fees, new series, dealing and fund/firm transfers. The authored `season_scenario.json` is a design contract; implement a validated tape/loader before claiming playability.

Build a deterministic event executor with reproducible RNG streams, explicit phase ordering, pauses at material decisions, and no per-refresh RNG. Surface missing/unsupported data rather than guessing. Mark-to-market can trigger a recoverable mandate breach; broker remedies and insolvency are separate state machines. Forced actions obey their specified execution/capacity policy and can fail to cure a deficit.

## FF3: governance that creates choices

Implement immutable sleeve charters jointly approved by both partners. Routine orders can be submitted by the authorized manager within those envelopes; exceptions require another person's affirmative consent. Recheck all fund-wide combined commitments at fill. Deadlock leads to a documented hold/default, never automatic acceptance.

Season-serialized PostgreSQL transactions covering the fund and its separate company protect approvals, budgets, locates, reservations, orders and journals. Tests use independent connections/barriers, not SQLite. Use a durable outbox before asynchronous critical jobs; in the earliest synchronous slice commit the domain effects atomically. Persist economic IDs so worker retries cannot repeat costs, LP dealing or payments. Reconnect from an authoritative sequence/snapshot.

## FF4–FF5: make the management game

Deliver the first two complete chapters (20 simulated business days through first dealing and ordinary day21 opening administration) with briefing, allocation of scarce analyst capacity, a trading/hedging choice, one investor or broker deadline, a budget decision and an attributable outcome. Use structured choices and optional rationale text; prose quality and word count cannot earn trust or performance points.

Five main destinations: command desk, investment committee/portfolio, research room, fund operations/LP desk, and chapter debrief. Show the deadline, expected effects, uncertainty and reversibility near each action. The operating partner must have independent actions and resource tradeoffs; do not reduce the role to an approval queue. Advanced ledger details are inspectable behind clear summaries.

The first vertical slice uses fictional companies and authored evidence. It must offer at least two credible strategies, support hold/wait without arbitrary punishment, and include a difficult decision that cannot be solved by clicking every available button. Add brief contextual lessons on actual consequences rather than interrupting with a textbook.

## FF6: full campaign and balance evidence

Expand only after the opening-arc playtest. Complete all six chapters and season endings, seed/rules/data manifests, tutorial difficulty, action history and save/resume. Review whether conservative play, aggressive concentration, gaming trust, delaying reports, final-day liquidation and repeatedly reopening saves exploit the score. Keep learning replay separate from ranked attempts.

Run matched-seed baselines: cash/defensive, simple mandate-valid diversified policy, concentrated momentum, and liquidity-aware policy. These are balancing experiments, not proof of investment superiority. Record end outcomes, return/drawdown, unpaid obligations, LP retention, trust, firm cash, decisions per role and waiting time. Adjust authored parameters only between versioned scenarios. No invisible rubber-band market punishment.

Provisional usability gates: both players can explain why cash differs from NAV; each makes several consequential choices; neither spends most of the chapter waiting for approval; they can identify the cause of the crisis and one alternative decision from the debrief. Measure actual completion time and confusion, then revise the 20–30 minute design target. Accessibility includes keyboard, readable status text, loading/error/offline and reduced motion.

Security/recovery gate: cross-fund access denial, no future information, backup restore/replay, idempotent jobs and reconnect, safe exports, input bounds and escaped narrative. Profile concurrency against declared hardware and operation mix; choose a supported load target after measuring. No invented throughput claim.

## FF7 and extensions

Use `OPENSEO_INTEGRATION.md` for the bounded research spike. Data must have rights and defensible availability timestamps before historical use. Freeze datasets and share the same execution/cost engine between game and research. Begin ML with a simple baseline and defined held-out target; HMM filtered inference is optional, not guaranteed to improve gameplay or returns. Reject candidates honestly. LLMs may explain verified facts or play disclosed sandbox opponents, never grade financial truth or mutate authoritative state.

Defer derivatives, multi-currency, distressed private assets, real-time exchange microstructure, unrestricted crawling and a multi-strategy empire until the initial game is finished. Each instrument needs dedicated accounting and lifecycle cases. Public deployment and real spend are separate user decisions.

## FF7 dependency gates and exclusions

FF7a imports immutable licensed snapshots only after as-of, rights, corporate-action and calendar checks. Add pandas and exchange_calendars here; add DuckDB only for demonstrated snapshot-query needs. FF7b may evaluate CVXPY allocation suggestions or statsmodels diagnostics against a simple baseline after FF7a supplies adequate data. FF7c is an independent optional OpenSEO fixture/adapter spike; a synthetic evidence card does not depend on a real provider. FF7d trains a model only after its target, lag-safe dataset and baseline are frozen. A failed experiment closes that feature instead of expanding the stack.

FF5/FF6 exclude live feeds, real broker routes, derivatives, multi-currency, multi-fund allocation, full statutory tax/accounting, prime-broker contract negotiation engines, unrestricted scraping and LLM-controlled economics. First implement one fund, one currency, one simplified prime-broker agreement, limited corporate actions, standardized investor terms and automatic routine administration. Additional realism needs a new meaningful decision, an owned lifecycle and independent acceptance cases.

The scenario manifest, scenario cases and research manifest are design evidence. FF0 must produce a loader plus complete tape/control records before claiming a runnable scenario. Manual playtesting at FF5 and FF6 is mandatory evidence for enjoyment and role balance; document checks cannot substitute for it.

A Renewal ending is conditional continuation, not proof of a sustainable firm. At constant25m,1.5% annual management fees are375k against1.04m annualized20k/week overhead:665k structural gap before incentive income/capital/cost changes. The300k opening company balance is15 weeks at base cost; four weeks of remaining runway does not finance another12-week season. Display this gap and require an explicit continuation budget/recapitalization contract; do not award sustainability from AUM or provisional incentive alone.
