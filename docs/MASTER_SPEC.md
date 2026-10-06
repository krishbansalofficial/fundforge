# FundForge — full product and engineering specification

Version 1.0 · Prepared 6 October 2026 · Working title, not a cleared brand name

## 1. Intended outcome and scope

Build a cooperative finance game where two friends act as the managers of one virtual investment fund. Each contributes $50,000 of fictional capital. They meet for 10–15 minutes on each trading day, review a small market brief, propose and approve trades, and manage a shared portfolio. Both profits and losses are allocated to their virtual capital accounts. The objective is to make defensible decisions within a mandate and understand the consequences, not to encourage constant trading.

The deliverable should demonstrate backend engineering first and an evaluated ML system second. It must be playable by two actual people, reproducible with fixtures, and explainable in an interview. A green P&L chart alone does not establish correctness or skill. Fifteen minutes is the decision window; positions remain exposed between sessions. Overnight gaps and drawdowns still happen.

This document defines a proposed simulation. Its rules are product defaults, not universal hedge-fund practice. A full operating hedge fund involves legal entities, investors, counterparties, service providers, and obligations that cannot be reproduced simply by adding a compliance screen. The project models selected procedures while deliberately keeping all capital fictional.

### Delivery levels

| Level | Included | Completion gate |
|---|---|---|
| A: playable financial core | Two managers, invitation, virtual capital, fixtures, next-open market execution, ledger, partner approval, basic mandate, daily session, portfolio and recap | Two users complete a season; financial and isolation tests pass |
| B: credible backend product | Licensed data adapter, settlement/jobs, outbox, reconnects, observability, load and recovery evidence, corporate actions | Measured concurrency, reconciliation, recovery and authorization results |
| C: ML/quant extension | Shared backtest engine, chronological validation, HMM/baselines, registry and inference, monitoring, evidence-grounded tutor | Reproducible held-out evaluation; baseline can defeat candidate |
| D: advanced fund lab | Borrow/margin, synthetic fund fees, redemptions, richer historical scenarios, AI fund opponents | Each extension has an explicit accounting and data contract |

Do not implement all levels in one prompt. No live brokerage or deposits are on this roadmap.

## 2. Why this complements the current resume

The supplied resume already describes ML evaluation at Keshav Enterprises, CNN–Transformer quantitative research, regime detection/backtesting, a Change Assurance Runtime, and a fork/join thread pool. That gives this project a specific purpose: prove a user-facing service whose state stays correct under retries, competing decisions, and data failures, then prove a complete model-to-inference workflow. Do not merely repeat HMM training or add an LLM chat tab.

For backend applications, foreground transactional correctness, idempotency, tenant authorization, reliable jobs, auditability, and measured behavior under faults. For ML applications, foreground point-in-time features, chronological evaluation, baseline comparison, model versioning, inference contracts, and monitoring. Backend and ML variants should describe the same implemented system with different emphasis.

If the project meets those gates, Inventory Management System is a plausible older project to replace. Decide that after evidence exists. Never claim a target load, proposed test count, or expected accuracy as an accomplishment. Short-term fund performance is gameplay output, not a validated investment track record.

## 3. Game premise and daily experience

### Season setup

Both users join a private fund through an expiring single-use invitation. A fund has exactly two active managers; a pending invitation does not count as the second active manager. Trading remains locked until both accept the mandate. A user can belong to multiple funds, but every mutation is authorized against the selected fund and season.

Each fund starts with $100,000 virtual NAV and 1,000 units at $100 per unit. Each manager owns 500 units. Roles alternate between proposer/research lead and risk/review lead, but either can propose and only the other can approve. Equal ownership does not mean each trade can be accurately credited to one manager. Trade collaboration is team behavior.

Choose a name, a simple emblem from preset icons, a benchmark, and a long-only mandate. V1 benchmark is SPY. Universe selection is locked at season start. A separate synthetic tutorial is available before a scored season. Season length is 30 market trading days, based on a configured exchange calendar.

### The fifteen-minute session

| Time | Player activity | Product behavior |
|---|---|---|
| 0–2 min | Check overnight results and operations | Reconciliation status, holdings, returns, mandate breaches, stale-data badge |
| 2–5 min | Review a small market brief | Prices, sources and timestamps, benchmark, 2–3 permitted events; no endless feed |
| 5–10 min | Discuss and propose up to three trades | Thesis, quantity, projected exposure, costs, settlement, concentration lesson |
| 10–13 min | Partner approves, rejects, or requests revision | Exact order/version presented; approvals cannot silently survive edits |
| 13–15 min | Confirm orders and write a short reflection | Queue summary, one lesson, plan for next session; explicitly allow “hold” |

The server owns a single shared session deadline. Either manager starts it; the other may join late and sees the same remaining time. Changing a device clock or reconnecting cannot reset it. Proposal creation and new approvals close at the deadline. Unapproved proposals expire. Accepted orders may execute later. Missing a day causes no automatic sale and no artificial performance penalty. Collaborative practice points can reflect participation without forcing attendance when markets are closed.

Default calendar schedule: daily information cut-off at 17:00 America/New_York; one session may start between 17:00 and 23:45. It lasts 15 minutes and uses a frozen information snapshot. Accepted orders are eligible at the next regular market open. Holiday and early-close sessions come from the exchange calendar, not hard-coded weekdays. Snapshot publication must wait until the source's data is available; a missing required snapshot blocks the session rather than substituting future data.

V1 can use fixtures that advance through this schedule without real waiting. Historical play uses the same rules on a simulated clock. A future live intraday mode would require separate quote, latency, and execution assumptions; it is not a toggle over the daily-bar model.

### Making it feel like a game

Give the fund a season objective, a shared progress bar, concise mission cards, satisfying approval states, and an end-of-season debrief. Show “Market review → Proposals → Partner review → Close session” as a compact checklist. Add restrained transitions and optional sounds; honor reduced-motion preferences. A small badge for a reconciled close can matter as much as a winning trade.

Award knowledge and discipline points for justified decisions, timely review, and risk checks. Do not award XP simply for order volume, leverage, or buying volatile stocks. A hold decision with a sound reason counts. Events should ask the team to reassess its plan; there need not be one correct profitable answer. Synthetic shocks belong only to explicitly labeled synthetic seasons, never overlaid silently onto real returns.

## 4. UI specification: polished, modest, playable

Five main screens are sufficient. Desktop first, usable on a phone, accessible to keyboard and screen readers. Use a restrained dark or light theme, one accent color, red/green only with text labels, readable numbers, and standard components. Avoid 3D, cinematic intros, elaborate illustrations, perpetual animations, or a Bloomberg-sized interface.

| Screen | Primary content | Main action |
|---|---|---|
| Lobby and setup | Create/join fund, manager names, mandate, virtual contributions | Start season |
| Fund desk | NAV, cash/buying power, P&L, benchmark excess return, holdings, current session | Open today's session |
| Trading room | Frozen brief, thesis form, risk preview, partner queue, shared timer | Propose / approve / reject |
| Research lab | One instrument chart, information as-of time, approved backtest presets | Inspect evidence |
| Season report | Return, drawdown, reconciliation, lessons, mandate breaches, shared decisions | Export / replay |

Fund desk layout: a compact header with fund name, season day, paper-mode badge, and connection status; a row of four summary cards; NAV vs benchmark chart; holdings table; partner activity and pending order cards. Trading room uses two columns on desktop: instrument/thesis on the left, risk/proposal review on the right. On mobile, make these sequential with the approval action always easy to locate.

Every quote shows source, event time, availability/as-of time, and whether it is delayed. Show “Queued for next open” rather than “Bought” before a fill. A proposed position weight is an estimate at the snapshot price; the final execution check may reject it after a gap. Show error, empty, loading, offline, expired, stale quote, rejected, partial/complete, and reconnect states explicitly.

### Finance curriculum attached to decisions

Begin with five reviewed concept checks: position sizing, diversification/idiosyncratic risk, market versus limit execution, settlement/buying power, and drawdown. Attach them to relevant proposed trades or daily outcomes. Each card should contain a one-minute explanation, a small numerical example, a factual check, and a source link. Financial decisions themselves rarely have a single guaranteed best answer; grade the concept, not whether a trade happened to profit.

Later lessons cover total versus benchmark excess return, regression alpha/beta, Sharpe/Sortino and sample limitations, volatility/correlation, FIFO realized/unrealized P&L, dividends/splits, P/E/EPS and earnings information, bonds/yields/duration, leverage/short borrow, VaR/CVaR/stress tests, fund NAV/units/flows, and hypothetical fees/high-water marks. Options lessons arrive only with a supported derivative model. Fundamentals such as P/E can be unavailable or misleading for negative earnings; the brief must explain that instead of inventing a number. Record lesson versions and human review. A generated explanation is supplemental rather than an unreviewed curriculum authority.

Use existing Vercel skills only after inspecting their actual names and instructions. React performance and web-interface guidance are likely relevant; their presence or exact names are not assumed. Read only relevant skills during the frontend phase. Set a UI time budget of roughly one task for tokens/components and one task for accessibility/state polish after the core vertical slice works.

### Visual acceptance criteria

Two unfamiliar users can create/join a fund, understand their remaining session time, propose an order, and explain whether it is pending or filled without a tutorial call. The 50/50 capital split and virtual nature are visible. Review requires enough information to understand the trade. The product can be demonstrated in five minutes without scrolling through a large dashboard.

## 5. Fund mandate and governance

V1 uses long-only, unlevered U.S. listed equities and ETFs, USD, whole shares, regular market sessions, no penny stocks, options, futures, crypto, OTC, or short selling. A fixed curated universe of 10–20 liquid instruments is sufficient, with permitted local fixtures. A current curated stock universe creates survivorship/selection limitations for historical studies; label them. Broad ETF experiments reduce some individual-stock issues but do not remove all selection bias.

| Policy | Initial default | Enforcement |
|---|---|---|
| Individual company exposure | At most 15% of NAV at acquisition | Hard pre-trade and fill-time gate |
| Broad diversified ETF exposure | At most 50% per approved broad ETF | Explicit exception; no false company/sector look-through |
| Direct stock sector exposure | At most 40% of NAV | Hard gate for classified direct holdings |
| Minimum available cash after commitments | 5% of NAV | Hard gate for new purchases |
| Gross exposure | At most 100% | No borrowing or naked sells |
| Proposed trades | At most three new proposals per daily session | Game pacing; canceled proposals still count |
| Drawdown | 10% warning, 15% acquisition freeze | Risk-reducing sales allowed with partner approval |
| Approval | Other active manager on same proposal version | Hard authorization rule |
| Thesis | Brief rationale, risk, expected horizon | Required structured fields |

These limits are house rules. Market movements can produce passive breaches after a valid fill. Record the breach, display it, and block changes that worsen it; do not pretend prices remain within bounds. Trades that demonstrably reduce an existing breach can pass even if they do not remove it entirely. Drawdown is not a guaranteed loss cap: gaps can cross the threshold before the next decision window.

ETF sector exposure requires holdings data from the appropriate historical date. Without it, show direct-stock sector exposure and the separate ETF bucket, not a precise overall sector percentage. Freeze classifications with an effective date. Do not retroactively apply a modern issuer sector to all past periods.

Mandates are immutable within a season. An exceptional correction requires both managers, a recorded reason, a new mandate version, and an unranked/restarted season where comparability changes. A stopped or withdrawn manager freezes new approvals; it does not transfer their authority to an AI.

## 6. Actual fund procedures mapped into a simulator

Hedge funds differ substantially by strategy, jurisdiction, and investor agreements. Use the table as an educational operating model, not a statement that every fund follows the same procedure or fee structure. The SEC's private-fund overview describes entities, governing documents, advisers, and capital-raising considerations [S2]. This project does not create any of those real arrangements.

| Real-world function | Simulated procedure and artifact | Phase |
|---|---|---|
| Fund constitution and investor terms | Educational charter: strategy, authority, benchmark, liquidity, virtual ownership | A |
| Subscription/capital contribution | Each player receives 500 units; no payment rail | A |
| Investment committee | Recorded thesis, partner decision, exact proposal version | A |
| Pre-trade compliance and risk | Universe, restricted list, cash, concentration, permissions | A |
| Execution and trade capture | Simulated eligible future fills, execution cost, fill identifiers | A |
| Confirmation and settlement | Trade-date payable/receivable, calendar-aware settlement | A/B |
| Independent administration | Separate close job reconciles cash, shares, lots, NAV and capital | B |
| Valuation controls | Mark-source hierarchy, stale-price flags, approval of corrections | B |
| Prime brokerage and financing | Borrow availability, collateral, fees, recall and margin scenarios | D |
| Management/incentive fees | Optional hypothetical fee ledger with explicit terms | D |
| Subscriptions/redemptions | Optional virtual unit issuance/redemption at controlled NAV | D |
| Investor reporting | Season report, capital statement, holdings, costs and limitations | A/B |
| Audit and error correction | Append-only journal, reversal entries, versioned restatement | A/B |
| Conflicts and restricted information | Educational restricted-list/MNPI scenarios and attestations | B/D |
| Business continuity | Backup/restore exercise, worker retry/recovery and incident log | B |
| Legal/tax/regulatory filings | Educational overview only; no filing generation or compliance certificate | D |

### Operating cadence

Before the open, the worker settles due obligations, applies effective corporate actions, checks dataset freshness, and processes eligible queued orders. Each fill reruns its own risk check under the fund lock. After the close, ingestion validates prices, the administrator-style job marks positions, reconciles all state, produces a new immutable NAV snapshot, and prepares the next brief. During the daily session, managers review this state, record decisions, and approve tomorrow's orders. At season close, cancel remaining orders, finish settlement and mark outstanding positions according to the same policy; report both ending NAV and whether positions remain open.

Roles are simulated divisions of responsibility. A separate reconciliation job is not an independent regulated fund administrator. Avoid naming every background process a microservice just to make the architecture sound sophisticated.

### Virtual profit and loss sharing

No subscriptions/redemptions occur during V1. Both players keep 500 units; unit NAV changes with performance. At $108,420 fund NAV, each capital account is $54,210, and each has $4,210 of profit. At $90,000, each has $45,000 and a $5,000 loss. Losses are allocated with the same ownership rule as gains. A player cannot cash out. Personal capital figures are shares of fund NAV, not separate tradable cash wallets.

If unequal contributions are introduced later, issue units at the current approved dealing NAV. Do not divide profits using the most recent contribution percentages or grant newcomers old gains. Use time-weighted fund returns to remove external flow effects; money-weighted investor returns are a separate calculation. Keep manager attribution descriptive: who proposed, approved, and wrote the thesis, not a causal per-person return claim.

### Optional fee module

V1 has no manager fees. Advanced educational terms can use an explicitly hypothetical 1% annual management rate accrued with actual/365 calendar days and a 10% incentive rate crystallized once at season end above a per-unit high-water mark, with no hurdle. Specify fee ordering, assets included in the accrual base, day count, net/gross reporting, and cash sufficiency. These are chosen teaching terms, not industry requirements.

For example, after all management accruals, 1,000 units at $110 pre-incentive NAV and a $100 high-water mark create $10,000 eligible gain. A 10% incentive fee is $1,000; investor NAV becomes $109,000 or $109 per unit. Set the next high-water mark to $109 after crystallization. Losses below that mark generate no incentive fee. Test recovery after a loss and never reset the mark to charge for the same recovery twice. Keep the fee recipient separate from the two investor accounts; fees are not silently credited as shared investor profit. Flows and unequal investor fee bases require series/equalization or another documented methodology before implementation.

## 7. Order lifecycle and two-manager approval

An order proposal contains fund/season, proposer, instrument ID, buy/sell, integer quantity, type, time-in-force, optional limit, thesis/risk/horizon, creation time, proposal version, content hash, snapshot ID, and estimated costs/exposure. The backend is authoritative for all derived values. Clients cannot submit cash, weight, approval identity, or execution prices as trusted fields.

Lifecycle: DRAFT → PENDING_REVIEW → APPROVED_QUEUED → FILLED, EXPIRED, CANCELED or REJECTED_AT_EXECUTION. PENDING_REVIEW may become REJECTED_BY_PARTNER or EXPIRED. A revision creates a new version returning to review; it cannot mutate approved content. PARTIALLY_FILLED is introduced only when partial fills are supported. Persist an explicit transition table and reject impossible state changes.

The proposer cannot approve. The other manager's approval is bound to the immutable content/version and an active session. Repeated approvals return the same result through idempotency. A stale page attempting approval of a superseded version gets a version-conflict response with current state. Both managers may cancel a not-yet-executed order; cancellation and execution serialize on the same lock. Record actor and reason. Rejection or expiry releases reservations.

On approval, reserve cash for a buy or shares for a sell, under a fund lock. For a next-open buy, use the snapshot price plus a documented maximum cash reservation, with a default 5% price-gap buffer. The buffer caps cash commitment; it is not a guaranteed execution price or a limit-order promise. At the next open, if the entire quantity plus costs exceeds its reservation or any risk limit, reject the whole order and release the reservation. V1 does not partially fill or auto-resize an approved order. The UI explains this possibility before approval.

Process queued orders in a deterministic order by approved-at timestamp then immutable order ID. A fill changes NAV/cash/exposure, so the next order sees the new state. Competing orders cannot all pass against the same old balance. Risk check and ledger posting must share the transaction. No external API call occurs while holding the database lock; immutable eligible prices are loaded first, then freshness/snapshot identity is checked under the lock.

### Execution assumptions

V1 market orders are simulations priced at the next eligible regular-session opening price, with a fixed configurable adverse cost of 5 basis points and zero commissions by default. Buy price = open × (1 + 0.0005); sell price = open × (1 − 0.0005). Label this a simplified daily-bar execution model, not a prediction of obtainable brokerage fills. Model slippage separately from commissions and use the same assumptions for every compared strategy.

An order accepted after close D can first execute at open D+1. Never let the player review close D and then buy at close D. Missing/invalid opening data or an exchange halt produces no invented fill. For DAY orders, expire at that eligible session's close if no fill occurs; publish the reason. Do not silently fill at a later day's close. Data may arrive late, but the immutable execution event must remain chronologically consistent and be published only once available.

Level B adds limit orders with a deliberately conservative daily-bar rule: execute only if the opening price, after modeled cost, satisfies the limit. Otherwise no fill that day, even if the high/low crosses. This understates fills but avoids fabricating the intraday path. A future intraday engine may fill on crossing with explicit liquidity assumptions. Stop and stop-limit orders need gap rules and intrabar ambiguity tests before activation. Investor.gov distinguishes market, limit and stop execution behavior; a stop price is not a guaranteed fill [S4].

## 8. Accounting, ledger and valuation

Use a double-entry financial journal plus a linked quantity/lot journal. Monetary debits equal credits for each posting, and instrument quantities reconcile with lots and positions. Double-entry balance alone cannot prove economic correctness: transaction meaning, marks, fees, quantities and capital allocation also require validation.

USD balances use fixed precision with explicit rounding. Store quantity as an integer in V1. Prices may carry more than two decimals; round each executed total to cents under one documented policy, such as decimal ROUND_HALF_EVEN. Specify that policy in code and fixtures, not only the README. Retain raw source prices and model parameters for reproduction.

Suggested monetary accounts: settled cash; settlement receivable; settlement payable; securities carrying value; unrealized valuation adjustment; investor capital; realized gain/loss; dividend income/receivable; transaction expense; and optional management/incentive fee payable. Journal entries carry posting ID, business-event ID, effective time, recorded time, actor/service, order/fill link, currency, amount, reason, and reversal link.

Trade-date buy: debit securities cost and credit settlement payable. On settlement, debit payable and credit settled cash. Trade-date sell: debit settlement receivable, credit securities at lot cost, and post the realized gain/loss for the difference. On settlement, debit cash and credit receivable. Reservations are commitments, not expenses or journal transfers. Prevent double-subtraction of cash already reserved and payable.

V1 uses FIFO lots. Capitalize modeled buy execution costs through the executed price; separately configured commissions follow a documented expense policy. At close, market value equals quantity times the valid mark. Either post valuation adjustments into the journal or compute an explicitly reconciled valuation subledger; choose one, do not count both. Realized and unrealized P&L must reconcile to total performance after dividends, costs and fees.

NAV = settled cash + settlement receivables − settlement payables + marked securities + other valid assets − other valid liabilities. Available buying power = settled cash − unsettled purchase payables − new buy reservations. Unsettled sale proceeds are excluded from V1 buying power until settlement. Selling an unsettled purchased lot is also blocked in the strict teaching account. This is a chosen conservative simulation policy, not a complete reproduction of every broker cash-account rule.

For current U.S. applicable securities, the SEC bulletin describes T+1 settlement beginning May 28, 2024 [S3]. Use exchange business days, including holidays. Historical replay must apply the era-appropriate settlement schedule or clearly label a fixed modern T+1 simplification. Do not apply modern T+1 silently to a 2008 season. Unsupported eras should be blocked until calendar/schedule data exists.

### Reconciliation and corrections

Rebuild cash and obligations from the journal, quantities from fills/corporate actions, cost basis from FIFO lots, and partner capital from units. Compare with materialized state and NAV snapshots. A mismatch blocks new execution and flags operations; it does not rewrite balances to make the test pass. Repair through an explicit reversal/correction and recomputation, retaining original events and a restatement version.

Use DB permissions that prevent ordinary app code from editing/deleting posted entries. This provides an application-level append-only journal; a privileged database operator can still alter records. Hash chaining plus externally retained checkpoints can add tamper evidence, but do not call it immutable against all administrators. Prefer correct reconciliation before adding cryptography.

### Golden arithmetic

With costs disabled: start $100,000 cash; buy 10 shares at $100; trade-date cash remains $100,000, payable is $1,000 and securities value $1,000, so NAV stays $100,000. After settlement cash is $99,000. Mark shares at $110: NAV is $100,100 and unrealized gain $100. Sell four at $110: sale receivable $440, six shares worth $660, realized gain $40, remaining unrealized gain $60; NAV remains $100,100. After settlement cash is $99,440 and each partner's capital is $50,050.

## 9. Market information and data provenance

Define one market-data interface and fixture adapter before selecting a paid provider. Required fields: stable instrument ID, ticker mapping as-of date, exchange/timezone/calendar, OHLCV bars, source/feed, event timestamp, available timestamp, currency, adjustment flags, ingest timestamp, dataset version and checksum. Fundamentals and news are optional until their timestamps and reuse rights are controlled.

Start with a committed synthetic fixture dataset and generated calendar. A developer demo must run with no API key and no external AI call. For actual market data, review current provider entitlements, historical coverage, adjustments, rate limits, retention, derived-data rules and redistribution/display terms. Alpaca's historical bars documentation exposes feed and adjustment choices [S6]; API availability alone does not grant permission to publish a dataset or its news content.

Live prices can be delayed; label the actual feed. An IEX-specific feed is not interchangeable with consolidated U.S. market coverage. Never mix feeds invisibly across benchmark and traded assets. Cache per dataset/instrument/date/adjustment/feed; enforce a unique ingest identity and paginate completely. Validate positive prices, OHLC ordering, nonnegative volume, duplicates, gaps and inconsistent corporate actions. Quarantine failures and show reduced availability.

Historical execution uses unadjusted prices plus explicit splits/dividend events. Feature calculations can use an appropriate adjusted return series, with adjustment provenance and point-in-time handling. Applying backward adjustments that encode future corporate actions can leak future information into some feature definitions; verify the chosen method. Never pay dividends in the ledger and also use total-return-adjusted marks for the same portfolio. Benchmark total returns need a consistent dividend convention as well.

At a split, adjust shares and lot unit costs while preserving total basis and economic NAV. At the ex-dividend event, recognize an entitled dividend receivable under the chosen accounting policy; transfer to cash on the payment event. Historical entitlements, reverse-split cash-in-lieu, symbol changes, spin-offs and delistings need tests. Unsupported actions block the affected instrument/season rather than being ignored. Delisted securities cannot simply disappear from the portfolio.

Historical information views filter by available_at <= decision cutoff, not merely event date. Revised economic data and filings use the version actually available then. If availability cannot be established, exclude that feature and disclose the omission. A season dataset is frozen and versioned. Corrections generate a new version and unrank/restated affected results; do not silently alter a completed leaderboard.

## 10. Risk engine

The deterministic engine returns PASS, BLOCK, or WARN with reason codes, calculations, input snapshot/version, and rule version. Preview helps the player; final fill checks are authoritative. ML scores and LLM wording never override a BLOCK.

Risk inputs include NAV/mark validity, cash commitments, unsettled obligations, holdings, lot settlement, instrument eligibility, price data, current/passive mandate breaches and all accepted reservations. Reject nonpositive NAV, invalid prices, unknown instruments, incompatible quantity precision, or unsupported products.

Estimate post-trade weights at preview, then recompute with the fill price and current accepted state at execution. Enforce no short quantities. A sale can reduce concentration and drawdown-related acquisition exposure; distinguish improving from worsening trades. Do not refuse a sale merely because pre-sale sector exposure already breaches the limit. Log the logic behind every exception.

Risk dashboard: direct company/sector weights, ETF bucket, cash, gross/net exposure, recent realized volatility and drawdown. Later add rolling beta/correlation and historical VaR/CVaR using a stated window and method. VaR is a quantile of the modeled loss distribution, not the maximum possible loss. Small samples and missing coverage produce “insufficient history,” not precise percentages.

Historical stress scenarios replay actual eligible data; synthetic scenarios apply documented hypothetical shocks to current holdings and label assumptions. Risk scores are educational summaries, not probabilities of success or suitability advice.

## 11. Performance metrics and scoring

Report total return, benchmark return, benchmark excess return, net/gross P&L where relevant, drawdown, daily volatility, turnover, costs, exposure, and reconciliation status. Benchmark excess return = fund cumulative return minus benchmark cumulative return. Do not label this difference Jensen's alpha. Regression alpha and beta require a model, risk-free rate and enough observations.

With no external flows, daily return = NAV_t / NAV_(t−1) − 1. Daily excess return subtracts the matching daily risk-free return. Annualized volatility = sample standard deviation of daily returns × sqrt(252). Sample Sharpe estimate = mean daily excess return / sample standard deviation of daily excess return × sqrt(252), under the stated assumptions. Zero variance or inadequate history means undefined, not infinity. Drawdown_t = NAV_t / historical running peak − 1; maximum drawdown is the most negative value. Total return is a compounded measure, not the sum of daily returns.

Thirty trading days is a small sample. Show “short-sample estimate” on annualized figures and omit ML/causal interpretations. Default main game ranking does not depend on Sharpe. The earlier proposed six-part score is retained as an optional research mode, not shipped as an unvalidated objective.

### Default transparent season score

Performance: 40 points; risk discipline: 30; decision process: 15; knowledge: 10; cooperative participation: 5. All rules and tie-breakers are visible before play. Score only completed, reconciled seasons with the same dataset, universe, mandate, cutoffs and execution model. Synthetic and market seasons have separate leaderboards. V1 can keep standings within the two friends' private fund; a public global board is unnecessary.

Define performance points = clip(20 + 2 × benchmark-excess-return-in-percentage-points, 0, 40). Risk points = 20 × clip(1 − absolute maximum drawdown / 0.15, 0, 1), plus up to 10 mandate-discipline points using a published passive-breach policy. Decision process uses a fixed checklist (thesis, identified risk, horizon, review response); a poor outcome can still have a good process score. Knowledge uses reviewed factual lessons. Cooperative participation allows limited missed days and measures review/reflection, not order count.

For implementation, mandate-discipline points = 10 × (1 − unresolved-breach-close-days / scored-market-close-days). A passive concentration/cash breach becomes unresolved only after two completed joint session opportunities in which it could have been addressed; its first appearance has no discipline penalty. Drawdown warnings/freeze are excluded from this count because the drawdown component already scores them. Decision-process points = 15 × the mean completion fraction of four checklist items across submitted daily reflections, with HOLD eligible and no reflections scoring zero. This measures documentation/process, not the truth of a profitable thesis. Knowledge points = 2 points for each of five reviewed concept checks answered correctly on the first scored attempt; later attempts remain available for learning. Cooperative points = 5 × min(1, jointly completed sessions / min(20, season trading days)). Up to ten missed sessions in a 30-day season therefore do not reduce this component. Round total scores to one decimal place. Ties use lower maximum drawdown magnitude, then benchmark excess return, then stable fund ID. Version these exact defaults before any ranked play.

Final scoring constants are product hypotheses. Run synthetic tests to show that a concentrated lucky gamble cannot systematically dominate disciplined teams, adjust before the first scored season, and version the score. Do not tune after observing a user's outcome. No LLM-only grade controls rankings; LLM feedback can remain qualitative and contestable.

Optional extended research score: 30% risk-adjusted performance, 20% benchmark excess return, 15% drawdown, 10% diversification, 10% decision quality, 10% consistency, 5% knowledge. It needs adequate return history, formal normalization and anti-gaming validation before activation. The prior example's “alpha” component should be renamed or formally calculated.

## 12. Backtesting and historical seasons

Historical gameplay and automated strategy research are different interfaces over the same domain engine. Players see only data available at their simulated date. Researchers may inspect completed periods in the lab, but an active scored historical season must not expose future data via chart endpoints, exports, queries, alerts or AI explanations. Server authorization enforces the date boundary.

Shared pipeline: frozen dataset → chronological event iterator → feature/signal generation → proposed order → mandate/risk check → future-event execution → settlement/ledger → NAV/metrics. Avoid building one simplified backtest that bypasses the live paper engine's cash/risk rules. Strategies can emit intended quantities but cannot mutate portfolio state directly.

### Evaluation protocol

1. Choose the universe, decision cutoff, labels, costs, benchmark and objective before evaluating.
2. Partition chronologically into training, validation and final holdout; fit scalers, feature selection and models on training only.
3. Tune only within training/validation. Where labels overlap future horizons, purge samples whose target intervals cross boundaries and apply a justified embargo; document why it is required.
4. Use walk-forward folds to assess changing regimes; retrain only on history available at each fold's boundary.
5. Lock the final holdout once. If repeatedly inspected, it is no longer untouched; document that fact and obtain a new evaluation period.
6. Compare against buy-and-hold, cash, simple momentum and a no-ML risk policy under the same execution/cost/calendar constraints.
7. Run cost sensitivity at 0/5/10/25 bps, missing-data cases, stress periods and multiple random seeds where applicable.
8. Report trade count, exposure, turnover, return/drawdown, costs, sample size, fold variance and limitations, not only the best Sharpe.

Synthetic fixtures provide deterministic software evidence, not evidence of investment edge. A contemporary curated stock list cannot support a broad unbiased historical market claim. Missing delisting data or unreconstructable news availability must be visible in the report. Do not silently optimize universe membership or choose start dates after seeing favorable returns.

No arbitrary forward-filling of nonexistent instruments, trade fills, halts or news. For valuation, last valid marks may be carried only within the documented hierarchy with an explicit stale flag; trading remains blocked where price freshness fails. Clock/calendar data and settlement-era policies belong in the experiment configuration.

Save config, seed, commit SHA, dataset checksum, source rights status, execution/risk versions, feature specification, split boundaries, model version and outputs for each run. A rerun of the same frozen inputs must produce the same trades and ledger, within documented numeric tolerance for model computations. Historical year names such as 2008 or 2020 are optional modules after data and settlement rules exist; no dates imply dataset coverage has already been obtained.

## 13. AI/ML: build one evaluated system

The first ML candidate is market-regime detection, reusing the user's prior HMM knowledge while adding a production-style pipeline. Start with simple volatility/trend rules as the baseline. Features can include trailing returns, realized volatility, volume changes and benchmark drawdown, all calculated strictly from available history. Avoid unrestricted feature collections and multiple unrelated models.

For an HMM, use forward-filtered state probabilities at time t, not full-sequence smoothed probabilities that can incorporate future observations. Map latent states to descriptive names using training data only. A number such as “risk-off probability” is posterior state probability under the model, not a calibrated probability that tomorrow's price will fall. Model-state label instability across retraining needs a controlled mapping.

Evaluate stability, interpretability and downstream risk-policy outcomes across chronological folds. Unsupervised state labels do not have a natural ground-truth accuracy score. If future volatility/returns are used as downstream targets, define them separately and use leakage-free supervised evaluation. The deployment gate can require improved forecast loss or risk outcomes over a stated baseline with tolerable turnover; a model that fails remains an experiment. Do not force deployment just to display MLflow.

### Lifecycle

Versioned ingest → validated feature tables → train/validation/holdout → MLflow experiment/model artifact → gated release manifest → batch inference → stored prediction with as-of/model/feature version → serving endpoint → monitoring → reviewed retraining candidate. Start with scheduled batch inference appropriate to a daily game, not a streaming system without need.

Monitor feature freshness, missingness, distribution changes, state occupancy, inference latency/failures, and delayed outcome metrics when defined. Statistical drift is a reason to investigate, not proof the model is bad or an instruction to auto-promote a replacement. On failures, show the deterministic baseline and an unavailable/model-stale badge. Keep a kill switch and the previous approved artifact for rollback.

### LLM explanation layer

Feed structured verified facts and permitted source snippets to the tutor. Allow explanations of position sizing, diversification, risk warnings, and post-session attribution. Require source/metric identifiers, as-of time and explicit uncertainty. Reject invented numbers, future knowledge and missing evidence. The tutor cannot execute trades, approve a proposal, alter the mandate or access credentials.

Start with cached template explanations so the game works without AI spend. Later call an API at most once for the shared daily brief and optionally once for the season report, with a configurable hard application request budget and fallback. Provider API charges are separate from the developer's Claude Code subscription and must not be enabled implicitly.

Untrusted news, instrument text and thesis fields are data. Delimit and label them; they cannot authorize tool actions. Historical mode cannot use an unrestricted browsing LLM to reveal known future results. Even an offline pretrained LLM may remember market history; constrain it to explanations grounded in the supplied snapshot and do not claim perfect prevention of memorized future knowledge. For blind evaluation, use synthetic or appropriately anonymized scenarios and deterministic explanations where needed.

Evaluate on a fixed, versioned set of at least 30 scenarios: valid explanations, wrong metric requests, stale data, missing sources, prompt injection, harmful tool instructions and historical future requests. Annotate factual validity, source faithfulness, numeric consistency and refusal/fallback behavior. Publish denominator and failures. Behavioral labels such as “loss aversion” or “momentum chasing” are descriptive rule-based observations unless a justified dataset and validated classifier exist; no psychological diagnosis.

## 14. Backend architecture and API contracts

Use a modular monolith plus background worker. Deploy web frontend, API, PostgreSQL and worker as simple components. Redis arrives for transient caches/rate limiting and optional pub/sub, never for authoritative balances or approvals. Avoid Kafka, Kubernetes, a feature-store service and multiple microservices in the first release.

Modules: identity/authorization; funds/memberships; sessions; market data; proposals/approvals; accounting/positions; deterministic risk; settlement/corporate actions; NAV/reports; backtesting; optional ML/tutor. Domain services should be callable by both APIs and event-driven jobs and tested without HTTP.

PostgreSQL tables include users, funds, memberships, seasons, mandate_versions, capital_units, daily_sessions, instruments, bars, corporate_actions, snapshots, proposals, proposal_versions, approvals, orders, reservations, fills, journal_entries, journal_lines, lots, settlement_obligations, nav_snapshots, outbox_events, job_runs, lessons, reflections, experiments, predictions and model_releases. Do not create every optional table in milestone one. Migrate module by module.

Required constraints: exactly one manager slot of each index per fund; only two active managers; unique fill/execution business identity; unique journal business event; positive monetary/quantity fields where appropriate; one current session per fund/day; unique approval per proposal version; immutable approved content; monotonic season clock; unique idempotency scope (user/fund/operation/key). Add indexes for fund-time queries and worker eligibility. Database constraints complement authorization checks, not replace them.

| Endpoint concept | Behavior |
|---|---|
| POST /funds, invitation/acceptance | Authorized setup; expiring single-use invitation |
| POST /funds/{id}/seasons | Both managers accept immutable charter |
| GET portfolio / brief | As-of state with snapshot and stale flags |
| POST daily-session/start | One shared deadline; idempotent concurrent starts |
| POST proposals, revision | Typed user input, risk preview, versioned content |
| POST proposals/{id}/approve | Other manager, expected version, live deadline |
| POST reject / cancel | Authorized transition and reservation release |
| GET orders / journal / report | Fund-isolated pagination and versioned evidence |
| POST backtests | Allowed dataset/config; budgeted asynchronous job |
| GET backtests/{id}, model-status | Owned result and reproducibility metadata |

Each mutation takes an Idempotency-Key and expected version where state matters. Same key + same request returns stored result; same key + different payload gets conflict. Authorization is checked again on replay: a removed member cannot retrieve a previously cached protected response. Store canonical request hash and a reference to the outcome; define retention long enough for season retries. Errors have stable reason codes and a request ID.

### Concurrency and jobs

Use a fund/season row lock for operations affecting cash, holdings, reservations and approval state. Fixed lock ordering avoids deadlocks. Workers can use SKIP LOCKED for independent fund jobs, but the ledger posting still serializes at the fund boundary. Retry a serialization/deadlock failure only with a bounded policy and same business identity.

Transactional outbox: ledger/order state and an outbox event commit together. Delivery is at-least-once; consumers deduplicate by event ID. Worker crash before commit causes a safe retry; crash after commit/before notification does not duplicate the trade. WebSocket events include monotonically increasing sequence/version. Reconnecting clients request a fresh authoritative snapshot and resume from a cursor; dropped messages must not corrupt portfolios. Polling is acceptable in Level A.

## 15. Security and authorization

Use a maintained auth provider with server-side verification. Do not implement password handling for this project. Choose either a same-origin secure-cookie/BFF architecture or a documented verified-token API flow, not an accidental mix. For cookie auth, use HttpOnly, Secure, appropriate SameSite, CSRF protection on mutations and narrow origins. The server derives identity from verified auth, never a user_id in request JSON.

Check fund membership and role on every HTTP, export, job submission, WebSocket subscription and background action. UUIDs are not authorization. Historical as-of restrictions are part of the same server policy. Test both another fund's data and another season's future data. One manager's invite link does not grant trading access until redeemed and bound to an account.

Validate inputs and price imports, use parameterized SQL, escape thesis/news text, enforce pagination and payload limits, rate-limit expensive backtests/tutor calls, and cap background job concurrency. Secrets belong in deployment secret management; `.env.example` contains placeholders only. Logs exclude tokens, invite secrets and unnecessary personal data. Do not give tutors or opponent agents infrastructure credentials.

Use minimal database roles; posted journals require privileged correction procedures. Audit security-sensitive decisions, mandate corrections and denied actions. Encrypt traffic, configure backups, test restore, patch dependencies, and add CI checks for secrets/dependency issues. A threat model should identify abuse cases and actual mitigations, not merely list tools.

Highest-priority attacks: self-approval, stale approval after an edit, cross-fund IDOR, simultaneous overspending, duplicate fills, modified session clock, future-data export, compromised market text triggering tools, costly backtest flooding and false audit claims. Review these before cosmetic work.

## 16. SEC and legal scope

This project is an educational virtual-money simulation with no brokerage integration, cash deposits, real profit payouts or money-linked rewards. This boundary reduces the investment-management features under consideration; it is not a blanket legal exemption. Avoid promising “SEC approved,” “SEC compliant,” guaranteed safety or profitable AI advice. Ordinary privacy, contracts, data licensing and consumer protection still require attention when deploying a product.

SEC investor guidance distinguishes active investment-club participation and passive members and notes fact-specific federal/state questions [S1]. Two participants or separate brokerage accounts do not automatically eliminate regulatory obligations. If real pooling, paid advice, copying/execution, custody, investor solicitation or performance compensation is ever proposed, create a separate project review with qualified counsel and broker/API requirements before implementation.

The SEC private-fund overview identifies entity/document, adviser and offering considerations [S2]. Do not encode simplistic rules such as “under a certain AUM means no regulation” or “friends do not count as investors.” Those depend on facts and jurisdictions. This brief supplies operating concepts, not real subscription agreements, tax filings, offering documents or a registration analysis.

Regulation SHO guidance addresses short-sale marking, price-test, locate and close-out requirements in the applicable real-world context [S5]. Advanced simulated shorts can teach borrow availability, fee accrual and recall but must not claim the game implements broker compliance. Pattern-day-trading/margin rules, reporting thresholds, and offering/adviser exemptions are intentionally not hard-coded from recollection; verify current primary rules if an educational module covers them.

No actual hedge fund is established by creating this repository. The full simulation roadmap is distinct from legal permission to launch a real fund.

## 17. Advanced trades and operations

Level D only, after the accounting and validation gates:

- Short selling: separate borrowed-share liability, restricted proceeds/collateral, borrow rate and day-count accrual, locate availability, recall/buy-in, dividend-in-lieu obligations and unlimited-loss explanation.
- Leverage/margin: marked equity, initial/maintenance assumptions, financing expense, liquidation sequence, gap failure and deficit handling. Thresholds are explicit scenario assumptions, not universal broker rules.
- Long/short mandate: gross exposure (sum of absolute marked positions / NAV) and net exposure (signed marked positions / NAV), with risk at both approval and fill.
- Virtual redemptions: dealing dates, notice, cash availability, unit redemption at approved NAV, simulated gates and audit trail. No player withdraws real money.
- Options/futures: contract multipliers, expiry, exercise/assignment, margin, valuation and reliable data; likely a separate project extension rather than an MVP feature.
- Economic/earnings events: dated public sources and available-at cutoffs. Missing historical earnings availability means omit the feature.
- Compliance learning: restricted lists, conflicts, inside-information scenarios and personal-trading disclosure concepts; education only, not legal determinations.

Do not silently add instruments whose mechanics the ledger cannot represent. Every product type needs event and risk tests before players can trade it.

## 18. AI agents in development and in the game

Development agents can provide adversarial review: one builder proposes/implements and one read-only reviewer attempts to break financial or security invariants. Limit the reviewer to changed files and named boundaries, require concrete reproductions, and allow one revision plus one verification. Endless “agents arguing” burns usage without an objective stop condition. See the dedicated workflow and prompt pack.

Parallel implementations are useful only for a small unresolved algorithm with fixed tests, such as a risk-policy evaluator or feature computation. Run candidates in separate worktrees and evaluate correctness, clarity, latency and memory under the same inputs. The winner is selected by evidence. Do not commission two complete apps or have multiple agents edit shared migrations.

In-game AI fund opponents are a later unranked lab. They submit typed trade proposals against the same frozen information, costs, mandates and ledger as humans. They see no future prices and cannot bypass checks. A proposal must receive the configured approval policy; an AI cannot approve on behalf of an absent human in the cooperative game. For purely AI-versus-AI funds, use a separately labeled two-agent committee.

Useful opponent styles: passive benchmark; deterministic trend/risk rules; risk-conservative agent; momentum agent; an evidence-constrained LLM agent. Measure run cost, invalid proposals, rejected risk actions, turnover, return and drawdown across many frozen scenarios/seeds. No live market browsing in historical contests. Keep LLM request ceilings and timeouts; invalid/missing actions default to hold. This is an agent evaluation harness, not proof that an AI can run a profitable real hedge fund.

## 19. Token-budget operating plan

There is no honest guarantee that this entire project fits one Claude subscription week. The user's plan, remaining allocation, model, conversation length, tool use, retries and agents are unknown. Anthropic documents shared Claude/Claude Code subscription limits [S7]. Multiple agents do not multiply the included quota. In-game API calls are separate usage.

Start with one planning review and one implementation session per milestone, with narrow file contracts and an updated handoff. Choose an available lower-cost capable model for routine work; reserve stronger reasoning for the accounting/concurrency/leakage decisions. Check the installed client's usage/status commands and subscription usage settings before and after a representative task. A plain prompt word cap limits output, not hidden reasoning or total tool consumption.

Suggested weekly allocation of the user's actually available capacity: 10% design/inspection, 55% implementation, 20% correctness/debugging, 5% UI polish, 10% reserve. These are planning shares, not provider quotas. At about 70% usage, stop launching optional agent/research work; at 85%, checkpoint and postpone new milestones. Actual enforcement depends on monitoring and configured provider/app controls, not a line in this document.

Load the full brief once for the initial architecture critique. Later tasks read `CLAUDE.md`, the small progress file and only relevant sections/files. Do not repeatedly regenerate plans, inspect unchanged files, install all skills, run every suite after a one-line edit or repeatedly ask for exhaustive explanations. Necessary broad checks still run at integration boundaries. Start fresh sessions at completed milestone boundaries; a fresh session still consumes context to reload its working set and is not itself a discount guarantee.

Anthropic's documentation discusses context management, scoped prompts, subagents and multi-agent cost [S8–S10]. This package applies those ideas with explicit scopes and stopping conditions. One targeted reviewer can improve correctness; an unrestricted agent team is inappropriate when preserving a small weekly budget.

## 20. Definition of a strong finished project

A backend-ready project has a working two-user demo; safe failure on stale approval or overspending; zero duplicated economic events during a documented retry/crash scenario; journal reconciliation; tenant isolation; a recovered backup; and a reproducible load report with hardware, dataset, concurrency, operation mix, latency distribution and errors.

An ML-ready project additionally has a frozen dataset and features; baselines and chronological holdout; explicit rejected-model cases; a versioned deployed inference artifact; stale/drift/failure monitoring; a tested fallback; and a fixed explanation-evaluation set with results. A chatbot, an untested Sharpe estimate or an MLflow screenshot is insufficient.

Target checks are gates to implement, not accomplished metrics: zero unauthorized access in defined tests, no double fills or negative buying power under concurrency, deterministic frozen replay, and a short usable session. Load numbers should emerge from measurement rather than a fictional “production-scale” claim.

The next action is inspection and an architecture decision, followed by the smallest playable financial vertical slice. Nothing in this package indicates that implementation has already occurred.
