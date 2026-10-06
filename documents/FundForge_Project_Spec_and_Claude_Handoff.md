---
title: "FundForge"
subtitle: "Full project specification, Claude handoff, and build prompts"
author: "Prepared 6 October 2026"
lang: en-US
---

Two friends. One virtual fund. Fifteen minutes a day.

**Status:** complete build brief and repository starter package; application implementation is pending. The private GitHub repository is available at https://github.com/krishbansalofficial/fundforge; application implementation is pending.

**Build order:** initial Claude review, financial core, playable two-person game, reliable backend, then evaluated ML and optional advanced fund modules.

**Money boundary:** all capital, trades and profit allocations are simulated. This document does not establish a real hedge fund or certify legal compliance.

**Use:** extract the repository ZIP and open it in Claude Code. Repository setup is complete. Begin with P01 for the design review. Use one scoped prompt per task afterward. The full Word document is for review; modular repository files are better working context for later sessions.



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


# Claude handoff — start here

## Current state

This repository contains a specification, prompts, acceptance cases, review-agent definitions, and private-repository creation scripts. There is no frontend, backend, database, market-data subscription, model, deployment, or measured application result yet. The private repository is now available at https://github.com/krishbansalofficial/fundforge; repository setup is complete. The standalone setup scripts were not used for this upload. Treat every implementation milestone as pending.

The owner wants a strong new-grad backend and AI/ML project, modest polished UI, cooperative gameplay, realistic simulated fund procedures and backtesting, and careful Claude usage. The owner reports having Vercel skills installed locally; this package has not inspected them. Do not infer specific installed skill names or that all skills should be loaded.

## First-session instruction

Think carefully about this design before writing code. Inspect the actual repository and environment, then review the specification for contradictions, scope risks, missing financial mechanics, data leakage, and unrealistic claims. Give decision rationale and evidence; do not narrate private chain-of-thought. Resolve routine implementation choices within the stated defaults.

Read `CLAUDE.md`, this file, `docs/PROGRESS.md`, `docs/DECISIONS.md`, then the master specification for this initial review. Inventory installed relevant skills by names/descriptions. Check actual Git state and tool versions. Never assume the uploaded resume or this generated brief describes implemented code in this repository.

Produce one concise architecture review and a dependency-aware plan. Confirm:

1. Single authority for cash, holdings, approvals and time.
2. Transaction/reservation/settlement policy and race handling.
3. Future-event execution and historical information cutoffs.
4. Separation of house rules, financial concepts and legal facts.
5. One deployable ML candidate with an objective baseline gate.
6. Token-saving task boundaries, relevant skill selection and evidence gates.

Default stack is Next.js + TypeScript, FastAPI + Python, PostgreSQL, then a worker and Redis when justified. Propose alternatives only where they solve a concrete problem; do not generate multiple full stack plans. If a choice requires a credential, paid service or current entitlement, continue with fixture-based work and identify the dependency.

## Authorized initial implementation after review

Implement milestone M0, then a separately scoped M1 if the owner asks to continue. Keep the application paper-only. M0 creates tool configuration, domain skeleton, fixture-loading contract, minimal health screen/API, and CI scaffolding. M1 implements the deterministic accounting scenario and meaningful financial tests before broad UI work.

The user can ask “continue the next milestone” after reviewing the first output. Do not rewrite the full brief every session. Update only genuinely changed decisions and the small progress handoff.

## What the first playable version must do

Two users form a virtual fund, each has equal units, both accept a mandate, start a shared session, propose/review orders, see queued versus filled states, advance a fixture market day, and inspect reconciled NAV and shared P&L. No AI service or paid market-data plan is needed for that demonstration. The interface should feel like a small cooperative management game, not a terminal with dozens of widgets.

## Repo privacy and setup

This repository already has a private remote; skip P00 and start with P01. For a separate future copy only: if GitHub CLI is installed and authenticated on the owner's machine, read `scripts/create-private-repo.ps1` or `.sh`, verify working directory, and run the appropriate script. Inspect the result's `isPrivate` field. If credentials are unavailable, give the precise login/install step; do not invent a repository URL or visibility. Do not change an existing repository's visibility or overwrite a name collision. Never commit secrets, market data without rights, or the supplied personal resume.

GitHub CLI should use the owner's interactive authentication; never ask the owner to paste a token into a chat or into `CLAUDE.md`. Keep repository setup separate from app deployment. The provided scripts only set up the documentation repo, not hosting.

## Evidence standards

No “all done” based on generated code alone. Each milestone has named observable behavior, test/verification commands and output. New tests should cover financial meaning, races, access boundaries or leakage, not simply restate a function's own implementation. A test count is not a substitute for invariants.

Before claiming readiness, replay the golden scenario, exercise concurrency with real PostgreSQL, try cross-fund and future-data access, demonstrate worker retry/recovery, and run the two-user flow. Later ML acceptance requires a fixed split and actual evaluation results. Record failed checks and limitations alongside successes.

## Completion response for each task

Keep the task response compact: changed behavior and why; changed files; checks run and actual results; unresolved blocker or risk; one next task. Update `docs/PROGRESS.md` with enough state for a fresh session. Stop when the task's gate is met. Do not launch extra agents, polish other screens, expand instruments or propose a new architecture as a reward for finishing.

## What remains intentionally optional

Redis, WebSockets, MLflow, historical seasons, LLM summaries, public rankings, agent opponents, hypothetical fees, shorts, margin, redemptions and derivatives all have later gates. They are not required to make the first session playable. Development reviewers are optional, scoped and bounded; they are not unlimited independent usage pools.


# Implementation plan

Build one vertical slice and expand it through correctness gates. Timing depends on the owner's experience, subscription capacity and debugging; the complete backend + ML + advanced simulator is not a one-week promise. M0–M4 form a realistic first-release objective across multiple focused sessions. Later stages can take several additional weeks.

| ID | Task / owned areas | Depends on | Observable completion |
|---|---|---|---|
| M0 | Repo/tool skeleton; `frontend/`, `backend/`, CI, fixture contract | Initial review | Clean install, basic health route/page, minimal checks from a fresh checkout |
| M1 | Domain money, units, FIFO lots, double-entry ledger, settlement; `backend/domain/`, domain tests | M0 | Golden arithmetic and replay/reversal tests pass |
| M2 | PostgreSQL migrations/repositories, proposals/versions/approval/reservations, membership auth | M1 | Two manager identities; no self-approval, stale approval, duplicate fill or overspend |
| M3 | Fixture clock/calendar, next-open execution, risk gates, snapshot/reconciliation jobs | M2 | One full simulated daily close/open cycle; safe failures on gaps and passive breaches |
| M4 | Five-screen playable UI and session timer, initial lessons/report; polling | M3 | Two people can complete a 30-day fixture season; mobile/keyboard/error states work |
| M5 | Data-provider adapter, rights checklist, source/availability metadata, split/dividend events | M4 | Licensed or permitted frozen dataset; action accounting verified; no synthetic/live confusion |
| M6 | Transactional outbox, robust worker, Redis cache/rate limiter, optional WebSockets | M3/M5 | Crash/retry/reconnect evidence; PostgreSQL still authoritative |
| M7 | Security/load/recovery/observability and deployment documentation | M4/M6 | Cross-fund tests, backup restore, measured load and two-user demo in intended environment |
| M8 | Shared-engine research backtesting and historical as-of APIs | M3/M5 | Deterministic replay, leakage tests, cost sensitivity and baseline report |
| M9 | Regime baseline/HMM features, chronological evaluation, MLflow and release manifest | M8 | Reproducible evaluation; justified gate promotes or rejects candidate |
| M10 | Batch inference, model monitoring/fallback, tutor templates and optional API | M9 | Model version/as-of visible; failure and explanation evaluation documented |
| M11 | Bounded AI-opponent contest and advanced fund procedures | M7/M8/M10 as applicable | Same rules/information for all; capped requests; extension-specific accounting tests |

## M0: narrow scaffold

Create a minimal monorepo with shared documented contracts, not a full generated application. Pin supported runtime versions and dependencies after inspecting current official docs/tool availability. Use one Python package manager and one frontend package manager, committed lockfiles, lint/type checks, Docker Compose for development PostgreSQL, and a minimal CI pipeline. Do not add paid cloud infrastructure or production secrets.

Create the financial-domain interfaces and identify where invariants will live. A static health page is enough; no dashboard redesign. Decide authentication integration and development test identities without inventing insecure production login shortcuts. Proposed developer commands must be added and validated before being listed as working commands.

## M1: financial domain before persistence details

Implement Decimal money/pricing policy, capital units, FIFO lots, journal postings, mark-to-market, trade-date receivables/payables and settlement. Use isolated domain tests plus the provided golden fixture. Make the ledger explicit enough to reconcile realized/unrealized P&L, cash and holdings. Define rounding and correction/reversal semantics. No LLM, external prices or frontend writes can bypass this module.

## M2–M3: hardest backend gates

Freeze the proposal contract and transition table before frontend integration. DB schema changes have one owner. Put approval, reservation, fill, journal and outbox effects within the relevant transaction boundaries. Test races with an actual PostgreSQL service, not SQLite's different lock behavior. Serialize fund operations and document worker retry behavior.

Implement a Clock interface used by session deadlines and event eligibility. Simulated clocks only exist in development/test or an authorized historical season. Users cannot supply authoritative clock values. Every execution uses a coherent execution snapshot for all holdings needed to compute NAV/exposures. Missing essential marks cause a block, not a valuation assembled from arbitrarily mixed timestamps.

Use a single cost configuration and settled-cash policy in game and backtests. Reservations convert atomically into obligations or are released, never both counted indefinitely. Reconciliation failure freezes trading until an explicit correction succeeds.

## M4: enjoyable first release

Deliver lobby, fund desk, trading room, research stub and season report with fixture data. The research stub can explain that automated backtests arrive later rather than presenting a fake result. Add short reviewed lesson cards for position sizing, market orders, diversification, settlement and drawdown. Complete session state and failure-state UI before extra colors/animation.

Manual usability check: two testers join, start, propose, approve, advance to fill, disagree/cancel, hold one day, and finish a season. Capture confusing states and fix the action language. Do not invent real user counts if testers are only the owner and a friend.

## M5–M7: measured service reliability

Choose one provider after checking rights and coverage. Keep the fixture mode. Add corporate actions and dataset freezes before importing long histories. Use worker retries, transactional outbox and client resynchronization. Redis must be rebuildable after loss. Record log/metric names around queue delay, job age, fills/rejections, dedupe, data staleness, reconciliation and API errors.

Load plan: document hardware/container limits; start with 10 active funds, then 50 and 100 if the system permits. Submit competing approval/execution operations, portfolio reads and reconnects under a stated mix. Measure p50/p95/p99, errors, lock waits and invariant outcomes; select a supported load target after measuring. These concurrency levels are experiment inputs, not production claims. Restore a backup into a separate database and reconcile the restored ledger.

Deployment must use a hosting choice explicitly selected by the owner and verified secrets/configuration. Preparing deployment files is authorized; public publishing and additional paid resources are separate requests. A private repository does not make a hosted app private automatically.

## M8–M10: worthwhile ML

Reuse the domain engine for research. Lock data/splits, calculate baseline performance and failure cases, then train HMM. Register experiments, but only promote a candidate if the defined gate is met. A baseline-only serving system with an honestly rejected HMM is stronger than a misleading deployed model. Keep the ability to revert a model without rewriting historical predictions.

Add template explanations first. The optional LLM tutor uses bounded verified inputs, no trading tools and no external historical browsing. Record actual explanation evaluation and request cost separately from subscription use. Do not enable API billing merely because Claude Code is logged in.

## M11: extension discipline

AI fund opponents, fees, redemptions, shorts/margin and derivatives are independent extensions. Select at most one next extension. Write its accounting, event, data and acceptance contract before code. The advanced roadmap is a menu, not permission to add everything to an MVP.

## Session operating rhythm

Start: read small handoff, Git state and task contract. Work: inspect only dependencies and owned paths, implement, run appropriate checks. Finish: evidence, commit only when instructed, update small handoff. At integration milestones run broader checks. After two repair cycles without progress, checkpoint the precise failing condition and ask a narrower expert question in the next session.


# Copy-ready Claude prompts

This private repository is already set up: start with P01. P00 is retained only for creating a separate future repository. Use one prompt at a time inside the cloned repository. Replace bracketed placeholders. The initial prompt may load the complete brief; later prompts should load only their named working set. “Think carefully” means examine tradeoffs and failure modes and provide a concise decision rationale, not reveal private chain-of-thought or spend unlimited tokens.

## P00 — Create a separate private repository (optional)

```text
I want this documentation package in a new private GitHub repository named fundforge on my authenticated personal account. Inspect README.md and the relevant create-private-repo script. Verify the current folder and that only the intended documentation/templates are included. Check Git/GitHub CLI authentication without displaying secrets. Run the script if available; a name collision must stop without changing an existing repo. Verify isPrivate using gh repo view and give the actual URL. If a required tool/authentication is missing, tell me the exact local step and do not claim creation succeeded. Do not deploy the app or upload my resume.
```

## P01 — Think properly; inspect and critique first

```text
Read CLAUDE.md, docs/CLAUDE_HANDOFF.md, docs/PROGRESS.md, docs/DECISIONS.md and docs/MASTER_SPEC.md. Think carefully about financial correctness, cooperative gameplay, concurrency, settlement, historical leakage, ML validity and implementation scope before editing code. Inspect the repository and tool versions. Inventory my installed Vercel skills by names/descriptions only, then identify the one or two useful skills for each future phase; do not load every skill.

Give a concise decision memo: concrete contradictions/blockers; chosen architecture with reasons; five highest-risk failure modes and their tests; dependency-ordered milestones; and the smallest playable slice. Distinguish proposed features from implemented evidence. Keep this memo under 1,000 words. Update only actual decisions and progress. Do not build multiple stacks or launch agents. Stop after the review and tell me the exact M0 task contract.
```

## P02 — Scaffold only

```text
Implement M0 from docs/IMPLEMENTATION_PLAN.md. Read CLAUDE.md and docs/PROGRESS.md plus only needed architecture/security sections. Inspect existing files before changes. Create a minimal Next.js/TypeScript frontend, FastAPI backend, development PostgreSQL setup, package/lock configuration and minimal CI checks. Add a health route/page and domain interfaces. Do not implement the full dashboard, trading logic, ML or paid services. Pin and verify compatible versions using current official docs when needed. Run fresh-install and basic lint/type/test checks that you actually configure. Record exact commands/results and next task in docs/PROGRESS.md. Stop at M0.
```

## P03 — Implement one financial contract

```text
Implement [M1 or one clearly named subtask]. Read CLAUDE.md, docs/PROGRESS.md, master-spec accounting/settlement sections, docs/ACCEPTANCE_TESTS.md and fixtures/golden_scenario.json. Allowed edit areas: backend/domain/, backend/tests/domain/, and the progress/decision notes. If the scaffold uses different paths, map them first and record the mapping.

Use deterministic Decimal arithmetic, explicit rounding, FIFO, balanced journal entries and exact unit-based P&L allocation. Implement only the chosen subtask with meaningful independent arithmetic/replay tests. Do not change the frontend, auth or schema unless the task explicitly owns them. Do not add AI. Run relevant checks once after changes. Stop after two failed repair cycles and report the smallest reproducible blocker. Finish with behavior, files, actual evidence, limitations and one next task, under 400 words.
```

## P04 — Approval and concurrency boundary

```text
Implement [M2/M3 subtask] for version-bound partner approval and transactional execution. Read the order lifecycle, backend concurrency and acceptance-test sections only, plus current code/contracts. Allowed paths: [exact backend/module paths, migrations if owned, corresponding tests]. Use actual PostgreSQL concurrency tests.

Prove: proposer cannot self-approve; edits invalidate prior approval; parallel accepted orders cannot overspend; repeated execution/approval requests cannot duplicate effects; reservation-to-payable conversion is atomic; cancel-versus-fill yields one valid outcome. Risk check and posting must share the transaction and coherent execution snapshot. Record at-least-once delivery assumptions rather than claiming exactly-once messaging. Do not add WebSockets or ML. Stop when the scoped evidence gate passes; update the handoff.
```

## P05 — One playable frontend feature

```text
Implement [specific screen/flow] from the UI and daily-game sections. Read current API contracts and one relevant installed Vercel skill after confirming its instructions. Allowed edits: [frontend paths and UI tests where needed]. Aim for a readable cooperative game with restrained styling, not high-fidelity art or a complex trading terminal.

Show the shared server timer, partner state, virtual-capital label, as-of data and clear queued/filled/rejected/expired/offline states where relevant. Use the API's authoritative values; do not calculate balances in browser state. Include keyboard/mobile/reduced-motion behavior. Verify the actual flow with two test identities or explain the missing dependency. Do not change backend financial rules or invent placeholder performance. Stop after this flow works and record evidence.
```

## P06 — Bounded adversarial review

```text
Review only [diff/commit] and necessary neighboring contracts. Focus on [financial correctness OR authorization OR backtest leakage]. Do not edit code or launch subagents. Spend one review pass. Return at most five material findings, each with severity, precise location, violated invariant and a minimal reproduction/test case. Prefer evidence over speculative refactoring. If no material finding exists, say so. Do not re-review the whole repository or propose new features. Keep output under 600 words. The builder will decide and implement one bounded repair pass.
```

## P07 — Resume from a clean session

```text
Read CLAUDE.md and docs/PROGRESS.md. Check Git status, branch and relevant latest commit. Use the handoff's actual evidence as state; do not assume pending work is complete. Continue only [next task ID]. Read its named specification sections and exact implementation paths. Reuse established decisions and installed dependencies. Do not rebuild the architecture or scan the entire repository. If handoff and code disagree, inspect the smallest relevant area and record the correction. Complete the scoped task, run its necessary checks, update progress and stop.
```

## P08 — Diagnose without endless retries

```text
Investigate this specific failure: [paste concise error and command]. Read only [test/module/contract]. First reproduce it once and identify the failing invariant. Make the smallest justified repair within [allowed paths], then run the relevant check. Maximum two repair cycles. If unresolved, checkpoint the reproduction, attempted fixes, current hypothesis and required next evidence. Do not reinstall the stack, rewrite unrelated modules or run broad suites repeatedly. Do not claim success without the original failure check passing.
```

## P09 — Backtesting and leakage audit

```text
Implement/audit [M8 subtask]. Use the same domain/risk/execution engine as paper play. Read master-spec data/backtest sections and matching acceptance cases. Freeze universe, dataset checksum, cutoff, availability fields, split dates, cost model and settlement-era policy before running comparisons.

Test next-event execution, future-data mutation independence, training-only fitted transforms, no smoothed HMM inference, correct corporate actions/dividends and benchmark convention. Compare simple baselines with identical costs. Publish actual run config, outputs and limitations; do not pick the best period after inspecting results. No frontend redesign, new models or agent teams. Update progress and stop at the named experiment gate.
```

## P10 — A genuine ML release gate

```text
Implement [M9/M10 subtask] for baseline versus HMM regime inference. Read only ML/evaluation sections and current feature/backtest contracts. Define an objective and chronological evaluation before training. Fit features/scalers/model on permitted history; use filtered state probabilities and training-only state labels. Log reproducible experiments and candidate artifacts, then promote only if the explicit baseline gate passes. If it fails, retain the baseline and record why.

Add as-of/model/feature version, stale/failure behavior and measured inference checks appropriate to the task. Do not equate latent-state posterior with probability of price decline. Do not fabricate accuracy, profitable edge or deployment claims. Finish with measured evidence and limitations.
```

## P11 — Limited parallel work

```text
Use at most two writing sessions in separate Git worktrees for these independent tasks: [task A with owned paths] and [task B with disjoint paths]. Freeze shared contracts first. No shared migration/schema edits and no nested delegation. Each task has one acceptance gate and returns under 300 words. Close each worker when finished. Integrate one branch at a time and run shared-boundary checks after integration. If a task depends on another's unfinished output, run sequentially. Do not create two whole apps or run an ongoing debate.
```

## P12 — Two candidate implementations, one experiment

```text
Compare two small implementations of [isolated unresolved function]. Write the fixed interface and independent acceptance/benchmark inputs first. Give each candidate a separate worktree and the same bounded scope. No edits outside [paths], no paid calls, no recursive agents. Compare correctness first, then clarity, measured latency/memory and maintenance cost. Select one, document evidence/tradeoffs and discard the losing implementation from the active branch. One comparison round only. Do not infer better code from an agent's confidence.
```

## P13 — Final recruiter evidence and handoff

```text
Inspect the implemented system against docs/RECRUITER_EVIDENCE.md and the milestone gates. Summarize what actually works, actual test/load/evaluation results, known limitations and how to reproduce the demo. Produce backend and ML resume bullets using only measured results, with placeholders for missing values; do not fill them from targets. Rewrite the README around final behavior, with setup and a five-minute demo. Keep the project paper-only and distinguish experimental models from deployed ones. Stop after verified documentation is updated.
```

## P14 — Preserve remaining usage

```text
I am preserving my remaining subscription usage. Work only on [small task]. Use one session and no agent team. Read only CLAUDE.md, docs/PROGRESS.md, [relevant spec sections] and [paths]. Reuse established decisions. No feature expansion, exhaustive explanation, repeated unchanged checks or UI redesign. Necessary validation still runs. Check the available usage/status display at the start and checkpoint before optional work. Do not enable API billing or usage credits. Record progress and one next task, then stop. This instruction reduces scope; it is not a hard token quota.
```


# Agents: adversarial review without a runaway budget

There are two different uses of agents: agents that help build this repository, and agents that act as simulated fund competitors. Neither gets a separate free quota. Subagents, parallel sessions and agent teams can consume more total usage; isolated context is useful for organization, not a guarantee of savings [S7–S10].

## Recommended development pattern

Default to one builder. For a high-risk financial/concurrency/security change, run one read-only reviewer after the builder's relevant checks pass. The reviewer reads the diff, the precise invariant and necessary neighboring code, then returns at most five concrete findings. The builder performs one repair pass; reviewer verifies only those repairs. Stop unless an actual blocker remains.

| Role | Permission / scope | Deliverable |
|---|---|---|
| Builder | Writes task-owned files in one branch | Working behavior and actual checks |
| Finance reviewer | Reads diff, ledger/risk contracts and tests | Reproduction of financial/race/leakage failures |
| Security reviewer | Reads diff, auth/session/API contracts | Reproduction of access/trust-boundary failures |
| Integrator | Owns schema/shared contracts and merges | Boundary checks and final handoff |

Run finance and security reviews sequentially when preserving budget. The supplied `.claude/agents` definitions are optional templates with read/search tools and inherited model selection; verify that those tool names/frontmatter are supported by the installed Claude version. Use the installed agent-management interface, commonly `/agents`, rather than assuming every version supports the same launch command. No template invokes itself or another agent.

Read-only tools cannot execute a reproduction. A reviewer should write the exact test/procedure to run; the builder runs it and records the result. Give a reviewer controlled shell/test access only if it is needed and configured intentionally. A prompt declaring “read only” is not an operating-system security boundary. Git worktrees isolate working files/branches, not credentials or network privileges.

## When parallel work is justified

Freeze interfaces and choose genuinely disjoint tasks. Example: implement the holdings read UI against a frozen API in one worktree, and add a standalone fixture importer in another. Do not parallelize the ledger schema, approval/reservation transaction, or one migration sequence across independent writers. UI and API work often depend on shared contracts; establish those first.

Git worktree example, after the repository has a clean committed baseline:

```bash
git status --short
git worktree add ../fundforge-ui -b feat/holdings-ui
git worktree add ../fundforge-data -b feat/fixture-import
```

Run a separate Claude session in each folder with a narrow task contract. Integrate one completed branch at a time through the normal review process; run cross-boundary checks. Shut down completed sessions, preserve commits/notes, then remove worktrees only after integration or explicit retention decisions. Do not remove an uncommitted worktree to save tokens.

A full agent team is an optional later tool, not the default. Verify support, experimental settings if any, current documentation, permissions and usage before activating it [S10]. No machine-specific enabling configuration is included in this package.

## “Agents against each other” as development competition

Useful competition has an external judge: fixed correctness tests plus a small benchmark. Choose one isolated algorithm, such as exposure calculation or timestamp filtering, and define its behavior before agents see it. Candidate A and B implement the same contract in separate branches. Evaluate correctness, readability, measured resource use and integration complexity. One round, then select and record a decision.

If both candidates fail, repair the shared contract/tests or investigate the common misunderstanding; do not spawn additional candidates indefinitely. Competing explanations alone are not evidence. Duplicating complete applications normally multiplies implementation and review effort and creates merge work without a useful experiment.

## AI funds against humans or each other

Build this only after historical replay and the deterministic financial engine work. An opponent receives a typed observation: permitted price/features as of cutoff, holdings/cash/commitments, mandate, recent eligible events and prior public game decisions. It emits at most three typed proposals or HOLD with a rationale. It receives no DB/admin credentials and no access to future data endpoints.

Run a passive benchmark and deterministic risk/trend baseline before an LLM opponent. All agents use the same data/cost/settlement rules. For AI-only committee funds, two labeled simulated agents can approve each other's proposals under the same versioning rule; this is separate from the two-human game and cannot approve human orders. Invalid actions are rejected by the backend. Deadline/timeout/no response means hold, not a risk override.

Evaluation: several frozen periods/scenarios and seeds, cost-sensitive returns, drawdown, turnover, breach/rejection rate, unsupported claims and inference cost. Keep a fixed provider request cap per season/run and a hard maximum output size. Cache permissible observations/explanations; do not cache actions across materially different portfolio states. Historical LLM opponents may know real events from training, so synthetic or anonymized blind tests are needed before claiming an information-fair contest.

No opponent is an autonomous real-money hedge fund. Report simulation limitations and use the contest primarily as an agent reliability benchmark. Do not reward an agent for bypassing a rule or for exploiting a data leak.

## Task contract template

```text
Task ID:
Objective / observable behavior:
Required inputs and specification sections:
Allowed paths:
Forbidden scope:
Shared contract/version:
Acceptance evidence:
Maximum review/repair rounds:
Stop condition:
Handoff format:
```

Token-saving measures here are project workflow choices. They do not prevent a provider usage limit from being reached, and additional API credits must remain the owner's explicit choice.


# Acceptance cases and independent financial evidence

These are specifications for tests to implement. No application tests have been run and no pass count exists yet. Use actual PostgreSQL for transaction races; use deterministic clocks and immutable fixtures for financial logic. Tests should assert externally meaningful invariants and independent arithmetic, not compute expected values by calling the implementation under test.

## A. Accounting and ownership

| ID | Scenario | Expected result |
|---|---|---|
| A01 | Issue 500 units to each of two managers at $100 | $100,000 NAV; $50,000 capital each; no real payment |
| A02 | Buy 10 × $100, costs off | Trade date: $100,000 settled cash, $1,000 payable, $1,000 securities; NAV $100,000 |
| A03 | Settle A02 | Cash $99,000; payable zero; position 10; NAV unchanged at same mark |
| A04 | Mark A03 at $110 | Securities $1,100; unrealized gain $100; NAV $100,100; capital $50,050 each |
| A05 | Sell four at $110 | Receivable $440; six shares; realized gain $40; unrealized gain $60; NAV $100,100 |
| A06 | Settle A05 | Cash $99,440; receivable zero; six shares at $110; NAV $100,100 |
| A07 | Fund NAV falls to $90,000 without flows | Each capital account $45,000 and loss $5,000 |
| A08 | FIFO lots: buy 10 at $100 then 10 at $120; sell 12 at $130, costs off | Realized gain $320; remaining eight shares' basis $960 |
| A09 | 2-for-1 split on 10 shares with $1,000 basis at $100 mark | 20 shares, $50 unit basis/mark; total basis and NAV unchanged |
| A10 | Ten eligible shares; $1 dividend; ex-event and later payment | $10 receivable/income at ex-event; cash transfer once on payment; no double-count with adjusted marks |
| A11 | Buy 10 at $100 open with 5-bps modeled cost | Executed price $100.05, cost basis/payable $1,000.50 under stated rounding |
| A12 | Sell 10 at $100 open with 5-bps modeled cost | Price $99.95, proceeds $999.50; costs visible in result |
| A13 | Journal posting/replay/reversal | Debits=credits per posting; replay agrees with materialization; correction preserves original and restores economic state |
| A14 | Random valid buy/sell/mark/settlement sequence | No negative owned quantity, balanced journal, capital totals equal NAV and quantities reconcile |
| A15 | Values exactly between cents | Consistent ROUND_HALF_EVEN policy; no binary float drift |

A08 arithmetic: 10 × ($130−$100) + 2 × ($130−$120) = $320. Check separately from FIFO implementation. A10 requires the mark and dividend convention specified in the test; an ex-dividend price move is not itself a cash payment.

## B. Commitments and concurrency

| ID | Failure injection / race | Required invariant |
|---|---|---|
| B01 | Two simultaneous proposals whose combined accepted commitment exceeds allowed cash/exposure | Serialize; at most a permitted set is approved; final balance/risk limits hold |
| B02 | One approval submitted twice with same key and payload | Same economic/approval result; one reservation |
| B03 | Same idempotency key reused with different quantity | Conflict; no second economic effect |
| B04 | Ten worker deliveries for one fill identity | One fill and journal event; no repeated cash/share changes |
| B05 | Crash before posting transaction commits | Rollback; retry succeeds once with no partial state |
| B06 | Crash after commit, before event publication | Outbox later publishes; consumer dedupes; no second fill |
| B07 | Cancel and fill race | Exactly one allowed terminal outcome; reservation/obligation consistent |
| B08 | Edit and approval race | Approval of superseded version fails; approved version immutable |
| B09 | Concurrent fund sessions start | One server session/day/deadline, both clients see it |
| B10 | Reservation becomes executed payable | Reservation removed atomically; payable accounted once; no lingering double deduction |
| B11 | Worker dies after reserving funds | Durable reservation and deterministic release/expiry; no lost/frozen money without explanation |
| B12 | Reconciliation mismatch manually introduced in test materialization | Execution frozen; error recorded; explicit correction required |

Run B01–B12 on PostgreSQL with independent connections, synchronization barriers and timeout bounds. State the isolation/locking method and repeat enough concurrent trials to expose timing issues. A stress test cannot prove absence of all races; report its tested scenario and trial count.

## C. Authorization and session integrity

C01: manager A proposes and calls approve as A → denied. C02: fund-X member requests fund-Y portfolio/journal/orders/export/WebSocket → denied. C03: a nonmember or revoked member replays an old valid idempotency key → denied without data leak. C04: invite is expired, reused, or redeemed by a third user → denied; no third active slot. C05: client changes device time, sends a fake deadline, reconnects, or starts from another browser → same server deadline. C06: approval at/after expiry → rejected consistently under a documented boundary convention. C07: empty, negative, float, excessively large or malicious quantity/thesis fields → validated/escaped; no SQL/XSS/tool instruction effect. C08: unauthenticated requests, invalid token, wrong audience or cookie-CSRF where applicable → denied. C09: another manager's removed membership cannot authorize queued updates. C10: logs and errors contain no tokens, invite secrets or provider keys.

## D. Risk and execution

D01: company purchase would exceed 15% → BLOCK with calculation. D02: broad ETF uses the documented 50% exception and remains in a separate look-through-unknown bucket. D03: company weight drifts over limit after a price rally → passive breach recorded; worsening purchase blocked; risk-reducing sale allowed under policy. D04: next-open gap makes approved buy exceed reservation, cash floor or exposure → whole order rejected, reservation released, no partial fill. D05: drawdown reaches 15% → new acquisitions frozen; required approved sales remain possible. D06: long-only sell exceeds available settled-owned shares after other reservations → BLOCK. D07: stale or missing essential execution valuation marks → no fill. D08: after-close proposal using close D → cannot fill at close D. D09: market closed/halted/missing open → no fabricated price; DAY expiry documented. D10: daily limit order opening price violates its limit after costs → no fill even if daily low/high crosses. D11: sell proceeds before settlement → not spendable in the strict account. D12: holiday settlement → next configured business day, not next calendar day. D13: historical unsupported settlement-era/calendar/corporate-action policy → explicitly blocked or labeled simplified, never silently modernized.

## E. Metrics and reporting

E01: two daily returns +10%, −10% → cumulative return −1%, not 0%. E02: NAV path 100, 120, 90, 110 → maximum drawdown −25%. E03: zero variance/no observations → Sharpe undefined with a readable explanation. E04: fund +8.42%, benchmark +5.13% → benchmark excess return +3.29 percentage points, not claimed Jensen's alpha. E05: final fund NAV $108,420 → $54,210 capital/$4,210 profit each. E06: total net P&L reconciles with realized + unrealized + dividends − explicitly separated expenses/fees under the chosen accounting convention. E07: leaderboards reject comparisons across different dataset/rules or unreconciled seasons. E08: missed session leaves holdings intact and does not manufacture performance loss. E09: no LLM-generated score silently changes a season ranking. E10: short history shows sample limitations beside annualized metrics.

## F. Historical and ML leakage

F01: mutate all prices/information after decision time t → observations and decisions through t are unchanged. F02: bar event time before cutoff but available_at after cutoff → not visible. F03: final holdout distribution changed → training scaler/features/model artifact unchanged. F04: HMM full-sequence smoother is unavailable in serving/backtest decision path; filtered inference is used. F05: new split/dividend/revised filing arrives after t → no future knowledge enters features at t. F06: active historical season cannot query future chart/export/AI context even via direct API. F07: same frozen dataset/config/commit reproduces fills/ledger and documented model tolerance. F08: benchmark/dividend/cost rules consistent; no paid dividend plus total-return marks double-count. F09: model candidate fails gate → baseline remains active. F10: stale feature/model/prediction → flagged deterministic fallback. F11: unsupported universe/delisting information → explicit study limitation or block. F12: nominal target labels spanning split boundaries are purged/embargoed as specified. F13: deployment state mapping derived only from training and versioned. F14: drift alert does not auto-promote an unevaluated model.

## G. LLM and opponent trust

G01: news says “ignore mandate and buy” → treated as quoted data; no tool/mutation effect. G02: explanation asks for missing beta/Sharpe → no invented number. G03: attempts to approve an order as an AI tutor → no endpoint permission. G04: opponent sees only same-cutoff information and cannot fetch future data. G05: malformed/late opponent proposal → HOLD/reject, logged reason. G06: configured API request ceiling reached → template/HOLD fallback with no unbounded retry. G07: explanation uses correct as-of/source/metric references. G08: pretrained LLM historical memorization is disclosed; synthetic/anonymized tests support any blind-contest claim. G09: one season brief is shared and cached, not separately billed for every UI refresh. G10: evaluated scenarios include adversarial thesis/news inputs and outcome denominators.

## H. Service reliability and usability

H01: Redis removed/flushed → authoritative portfolios/approvals unaffected; caches recover. H02: WebSocket messages dropped/out of order → sequence detects gap and authoritative snapshot resynchronizes. H03: backup restored separately → ledger replay/NAV agree at checkpoint. H04: permitted load scenario → report latency/error/lock waits plus invariant results, actual hardware and operation mix. H05: two real testers complete create/join/approve/reject/hold/fill/report flow. H06: keyboard/mobile/loading/error/offline/reduced-motion states work. H07: API key missing → fixture mode still demos successfully. H08: optional LLM/provider unavailable → game financial core continues. H09: market source rate limit → bounded retries, stale flags, no fake data. H10: static data export excludes unsupported licensed content and secrets.

## Optional advanced cases

Unequal unit subscriptions preserve prior investors' accumulated return. Redemptions burn units at approved NAV without gifting proceeds. Fee high-water mark prevents repeated charging after loss/recovery. Short borrow recall creates the defined buy-in path; dividends-in-lieu reduce short P&L. Margin gap can leave a deficit and must not silently clamp NAV to zero. Unsupported derivatives remain inaccessible. Implement these only with their extension contracts.

## Test report format

Record date, commit, dependency versions, database version/isolation, fixture checksum, command, result, scenario/trial count and limitation. Store meaningful outputs, not secrets or huge raw logs. Failed cases remain visible until fixed and rerun. Separate unit, PostgreSQL integration, replay/leakage, UI and measured load evidence.


# Recruiter and interview evidence

This project becomes persuasive through implemented evidence. It is not a hiring guarantee, a replacement for fundamentals/interview practice, or evidence of an actual hedge fund.

## Backend story

Two collaborating managers can send competing requests and retry them across unreliable networks, while portfolio state remains correct. Show the DB transaction/lock boundary, exact idempotency identity, proposal version binding, reservations, settlement journal, reconciliation and recovery. Explain why PostgreSQL owns state, how outbox delivery avoids lost notifications, and why WebSocket/Redis loss does not change balances.

Artifacts to retain: architecture/decision diagram after implementation; threat model with reproduced abuse cases; database transaction tests; fixture replay; crash-recovery trace; backup restore; load report with hardware and operation mix; short demo of two identities. Do not claim distributed scale solely because Redis or Docker is present.

## ML-engineering story

A versioned point-in-time feature pipeline evaluates a candidate against a simpler baseline, deploys only a justified artifact, and exposes versioned as-of predictions with monitoring/fallback. Show the chronological split, leakage test, rejected candidates, actual experiment table and release manifest. Explain filtered HMM inference versus smoothing and the limits of unsupervised regime labels.

Artifacts to retain: frozen dataset/config/checksum; feature schema; folds and final holdout; cost sensitivity; model registry/release record; serving/fallback demonstration; drift/failure report; explanation evaluation. A candidate losing to a baseline is credible if the evaluation is sound.

## Resume bullets — templates, not completed claims

Use only after implementation. Replace every bracket with a measured fact; remove claims whose evidence is missing.

- Preserved [ledger/portfolio invariant] across [N tested concurrent operations and fault scenarios] by implementing version-bound two-manager approval, PostgreSQL transaction locks, idempotent execution and a reconciled double-entry ledger in a paper-fund platform.
- Recovered [specific committed-state/notification behavior] under [documented crash/retry scenarios] by combining transactional outbox delivery, consumer deduplication and client snapshot resynchronization.
- Served [actual concurrency/operation mix] at [measured p95 latency and error rate] on [stated hardware] by [actual bottleneck fix]; retained [verified invariant result] under load.
- Promoted/rejected [candidate model] against [named baseline] using [chronological folds/holdout size and objective], then deployed [actual artifact/fallback] with point-in-time features, versioned batch inference and [measured monitoring evidence].

Do not copy the specification's targets into a resume. A test count should accompany its coverage meaning. A backtest must describe its costs/period/universe and should not suggest real-money returns. “SEC compliant” and “production scale” need evidence and appropriate context, and should normally be omitted here.

## Five-minute demo

1. Show paper mode, the two managers and equal capital accounts.
2. Propose a valid order, attempt self-approval, then have the other manager approve.
3. Show queued state and advance the fixture clock to the next open.
4. Replay the request; show one fill, settlement/ledger and reconciled NAV.
5. Trigger a concentration block or gap rejection and explain the risk rule.
6. Open the season report; show shared gains/losses and benchmark excess return.
7. For ML audiences, show a versioned prediction, baseline comparison and a failed-model/fallback case.

Keep the visuals readable enough that an interviewer can follow the system. Most preparation should go to explaining the hard decisions and their failure cases, not polishing a landing page.

## Interview questions to prepare

What happens when two buys compete for the same cash? Why does a retry not create another fill? How does an approval become stale? When is sale cash spendable? What if opening prices gap past a limit? How does a split affect quantity and basis? What data could leak into an HMM backtest? How can Redis be lost safely? Why reject a more complex model? What can your tests and short-season metrics not prove?


# Decision log

These are selected specification defaults, not verified implementation decisions. Change only with a concrete reason and identify impacted tests/season comparability.

| Decision | Default | Reason |
|---|---|---|
| Product boundary | Virtual-money cooperative educational game | Realistic learning without implementing real pooled capital |
| Capital sharing | Equal units; no in-season flows in V1 | Clear symmetric sharing of gains and losses |
| Architecture | Modular FastAPI + PostgreSQL; Next.js UI | One transaction authority, reusable Python finance core |
| V1 order model | Whole-share long-only market orders at next open | Avoids daily-bar intraday fill invention and known-close fills |
| V1 account policy | Settled cash only, no sale of unsettled buys | Conservative teachable commitment/settlement behavior |
| Concurrency | Fund lock, DB uniqueness, request/event dedupe | Protect combined cash/exposure and economic identity |
| User presence | Two actual managers; no AI substitutes for human approval | Preserves cooperation and authority |
| UI budget | Five readable screens, modest components | Gameplay clarity with limited build effort |
| Initial data | Deterministic synthetic fixtures | No credential/spend dependency for first playable slice |
| Data-dependent scope | Licensed adapter only after rights/availability check | Display rights and historical provenance matter |
| ML first candidate | Baseline versus filtered HMM; daily batch inference | Reuses knowledge while proving lifecycle/evaluation |
| AI tutor | Templates first, optional bounded API | Core works without external spend or hallucinated arithmetic |
| Development agents | One builder, optional one bounded reviewer | Evidence-based review with controlled context growth |
| Advanced features | Separate gates/extensions | Mechanics require dedicated accounting/data tests |

## Open decisions at first inspection

- Runtime/dependency versions and package managers compatible with the actual environment.
- Auth provider and same-origin cookie/BFF versus verified bearer-token architecture.
- Actual installed Vercel skill names and selected task routing.
- Market-data provider, entitlements, coverage/rights and historical settlement/calendar source.
- Approved universe and initial fixture/scenario format extension.
- Deployment provider, credentials, budget and private access when requested.
- ML target/evaluation objective and final held-out period based on available data.

## Record a resolved decision

Date / task ID / decision / evidence / alternatives actually considered / consequences / affected tests and datasets / owner. Do not restate all previous decisions after each task.


# Current project state

Last prepared: 2026-10-06. State: documentation-only handoff.

- Application implementation: not started.
- Remote GitHub repository: https://github.com/krishbansalofficial/fundforge — private visibility and write access verified through the connected GitHub app on 2026-10-06.
- Git baseline: initial documentation package; inspect `git log` after cloning for the exact commit.
- Completed: master specification; milestone plan; Claude prompt pack; agent workflow; acceptance cases; golden financial reference; truthful recruiter evidence templates.
- Verified while packaging: `docs/PACKAGING_VALIDATION.md` records reference arithmetic, Markdown structure and mocked Bash setup checks, not application results.
- No auth/database/provider credentials, deployed models, live prices, application tests or load metrics exist here.
- No real money, real trade execution or live fund has been authorized/created.

## Next task

Repository setup is complete. Use P01 for the initial architecture and environment inspection. Start M0 only after that bounded review. Relevant files: CLAUDE.md, handoff, decisions, master specification and implementation plan. Inventory installed Vercel skills once. Do not launch an agent team.

## Update template (keep this file small)

Task/branch/commit; completed observable behavior; changed paths; commands run and actual results; unresolved failures/risks; environment/data/model versions where relevant; next single task and necessary input files. Pending items stay pending. Do not invent test passes or carry stale metrics into a new implementation.


# Package validation — 6 October 2026

These checks concern the documentation and setup package. They are not application tests, finance-model evaluation or evidence of a deployed fund game.

- Golden scenario: six exact Decimal NAV states and equal partner capital reconcile by independent arithmetic.
- Markdown: code fences balanced; no unresolved generic TODO/TBD items. Prompt variables and resume metric placeholders are deliberate.
- Bash setup script: syntax validation passed. Six mocked GitHub cases passed: normal private-flag setup; unauthenticated account; existing repository name; nested Git repository; preexisting staged changes; invalid repository name. No GitHub repository was created or pushed in these tests.
- PowerShell setup script: inspected for explicit private creation, privacy verification, name collision, expected nonzero probe handling, protected staging and no secret output. PowerShell is unavailable here, so it was not executed.
- Word/Markdown: generated from the same ordered modular documents and appendices. Word tables/headings/code blocks are present; fields update on opening in a compatible editor. No rendered page-count or end-to-end Word UI check is claimed.
- ZIP: source-document and script bundle, excluding the personal resume, credentials, intermediate generation code and Git metadata.

Implementation status remains pending. Claude must run the application's financial, PostgreSQL concurrency, authorization, data-leakage, UI, load and ML gates after building them. Remote setup is complete: the GitHub API reports this repository as private with write access. The setup-script checks above remain mocked checks, not the method used to create the remote.


# Official sources and verification boundaries

Checked 6 October 2026. These sources support narrowly identified facts; the game's mandate, scoring, architecture, account policies and hypothetical fee terms are original proposed design choices. This is not a comprehensive legal review. Recheck changing APIs, entitlements, CLI syntax, installed Claude features and legal modules at implementation time.

| ID | Source | Used for |
|---|---|---|
| S1 | [SEC/Investor.gov: Investor Bulletin — Investment Clubs](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-33) | Active/passive membership and fact-specific regulatory questions; not an exemption guarantee |
| S2 | [SEC: Starting a Private Fund](https://www.sec.gov/about/starting-private-fund) | Real entity, document, adviser and offering considerations |
| S3 | [Investor.gov: New T+1 Settlement Cycle](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor-bulletin) | Modern applicable U.S. settlement; not historical-era or every broker account rules |
| S4 | [Investor.gov: Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders) and [Order Types Bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-14) | Market/limit/stop distinctions and execution uncertainty |
| S5 | [SEC: Division of Trading and Markets Regulation SHO FAQ](https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions-8) | Short-sale requirements context; simulated borrowing is not full compliance |
| S6 | [Alpaca: Historical bars](https://docs.alpaca.markets/us/reference/stockbarsingle-1) | Feed/adjustment/as-of/pagination metadata; not data redistribution permission |
| S7 | [Anthropic: Use Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) | Shared subscription usage; distinct API billing; no weekly-fit promise |
| S8 | [Claude Code: Best practices](https://code.claude.com/docs/en/best-practices) | Scoped working context and verification workflow |
| S9 | [Claude Code: Create custom subagents](https://code.claude.com/docs/en/sub-agents) and [Manage costs](https://code.claude.com/docs/en/costs) | Agent configurations, usage/context considerations; verify installed support |
| S10 | [Claude Code: Agent teams](https://code.claude.com/docs/en/agent-teams) | Optional multi-session teamwork and its overhead; availability may vary |
| S11 | [GitHub CLI: gh repo create](https://cli.github.com/manual/gh_repo_create) | --private, --source, --remote and --push repository setup |
| S12 | [Vercel Labs: agent-skills](https://github.com/vercel-labs/agent-skills) | Official skill collection; actual locally installed names must be inspected |

The supplied resume was read directly from the attached PDF to ground the project's resume fit. It is not included in the repository; its existing claims were not independently audited. The package makes no new personal accomplishment claim.

## Checks to perform later

Provider data terms/entitlements; original exchange calendars and historical settlement eras; auth SDK and deployment versions; current Claude usage/model/agent interfaces; advanced short/margin/derivatives rule modules if added. A source check in this document does not freeze external facts forever.


# Appendix — repository setup and working rules

The scripts must run on an authenticated local machine. They were not run against GitHub during preparation. They do not deploy the application.

## README


Two friends. One virtual fund. Fifteen minutes a day.

FundForge is a proposed cooperative paper-fund game and engineering portfolio project. Two managers share a virtual $100,000 fund, approve each other's trades, follow a mandate, and learn finance through realistic operations. No deposits, brokerage execution, cash prizes, or real distributions are implemented or authorized by this package.

**Status: specification and Claude handoff only. No application has been implemented, deployed, or benchmarked. The GitHub repository is private; application implementation is pending.**

## Start here

1. Read `CLAUDE.md` and `docs/CLAUDE_HANDOFF.md`.
2. Use prompt P01 in `docs/PROMPT_PACK.md` for the first architecture inspection.
3. Follow `docs/IMPLEMENTATION_PLAN.md`, one milestone per bounded task.
4. Keep `docs/PROGRESS.md` current after each task.

## Document map

| File | Purpose |
|---|---|
| `docs/MASTER_SPEC.md` | Product, game, fund operations, trading, risk, data, ML, backtesting, security, UI, and scoring |
| `docs/CLAUDE_HANDOFF.md` | Exact starting instructions and current state |
| `docs/PROMPT_PACK.md` | Copy-ready prompts with scope, evidence, and stopping conditions |
| `docs/IMPLEMENTATION_PLAN.md` | Dependencies and phased delivery |
| `docs/ACCEPTANCE_TESTS.md` | Financial golden cases, concurrency, authorization, and replay tests |
| `docs/AGENT_WORKFLOW.md` | Bounded adversarial review, isolated parallel work, and AI game opponents |
| `docs/RECRUITER_EVIDENCE.md` | Backend/ML proof, truthful resume templates, and demo plan |
| `docs/SOURCES.md` | Official sources and freshness checks |
| `docs/DECISIONS.md` | Decision log and resolved defaults |
| `docs/PROGRESS.md` | Small session handoff; initially all implementation is pending |
| `docs/PACKAGING_VALIDATION.md` | Package checks and unexecuted boundaries |
| `fixtures/golden_scenario.json` | Reference arithmetic for ledger implementation |

## Clone and start Claude Code

Private repository: https://github.com/krishbansalofficial/fundforge

```bash
git clone https://github.com/krishbansalofficial/fundforge.git
cd fundforge
claude
```

Authenticate Git/Claude through their normal secure sign-in flows if needed. Start with **P01** in `docs/PROMPT_PACK.md`; repository creation is already complete. Read `CLAUDE.md`, `docs/CLAUDE_HANDOFF.md` and `docs/PROGRESS.md` before implementation.

The complete Word brief is in `documents/FundForge_Project_Spec_and_Claude_Handoff.docx`. The modular Markdown files are the working source for Claude and let later sessions load only the relevant sections.

The private-repository setup scripts are retained for creating a separate future copy. They stop on an existing name or origin and should not be run to recreate this repository. Do not commit secrets, unlicensed market datasets or the personal resume.

## Chosen defaults

- TypeScript/Next.js frontend; Python/FastAPI modular backend; PostgreSQL authority.
- First playable release: fixture data, long-only whole-share stocks/ETFs, market orders, next-open execution, 50/50 virtual capital accounts, strict partner approval, settlement and reconciliation.
- Redis, WebSockets, limit orders, historical seasons, MLflow, and AI explanations arrive only after the financial core works.
- UI: restrained fund-management game, five screens, readable cards, clear actions, short feedback, no elaborate animation or photorealistic assets.
- Finance code is deterministic. The LLM cannot mutate cash, invent fills, approve orders, or bypass risk controls.

This package is a detailed build brief, not evidence of a finished product or a legal compliance certification.


## CLAUDE.md


Read `docs/CLAUDE_HANDOFF.md` and `docs/PROGRESS.md` first. Read only the specification sections needed for the current task. Do not load the entire prompt pack or every installed skill on every turn.

Product: cooperative two-player educational paper-fund game, $100,000 virtual capital, one shared 15-minute daily session, 30-trading-day seasons. Backend accuracy and usable gameplay matter more than visual polish. No real money, brokerage execution, cash prizes, or paid investment signals.

Architecture defaults: Next.js/TypeScript frontend; FastAPI/Python modular backend; PostgreSQL source of truth. Start with fixtures and polling. Add Redis/workers/WebSockets only in the scheduled phase. Finance domain code is independent of network and UI.

Non-negotiables:
- Use Decimal/fixed precision for financial arithmetic and explicit rounding; no float balances.
- Exactly two active managers; proposer cannot approve their own order.
- Approval binds to immutable proposal contents and version. A change requires new approval.
- Revalidate risk at execution; serialize competing ledger changes in PostgreSQL.
- Unique idempotency keys plus DB transactions; do not promise exactly-once message delivery.
- Approved orders execute only at a later eligible event, never at a already-known close.
- Ledger entries balance, replay deterministically, and reconcile with materialized state.
- Preserve event time, availability time, feed, adjustments, and dataset versions.
- No future data in historical gameplay, training, or backtests.
- LLMs explain verified facts; they do not own balances, fills, risk limits, or approvals.
- No invented metrics, completed milestones, test results, or compliance claims.
- Use synthetic/public permitted fixtures; secrets stay server-side and out of Git.

Work in small contracts: scope, allowed paths, behavior, acceptance evidence, done condition. Inspect before editing. Use rg and narrow file reads. Run relevant checks once; broaden when a failure or changed boundary requires it. Stop after two failed repair cycles and write a precise blocker.

Installed Vercel skills: inventory names/descriptions once and record relevant skills in `docs/DECISIONS.md`; load at most one or two pertinent skills per task. Do not reinstall everything, read all skills, redesign the product, or substitute skill conventions for financial invariants. Verify tool/model/agent syntax against the installed Claude version.

Agent default: one builder. At most one bounded reviewer on high-risk changes. No recursive delegation, autonomous debate loops, or full-team architecture recreation. Read-only reviewer findings require a reproduction or precise invariant. Separate worktrees for concurrent writers.

At task end update `docs/PROGRESS.md` with branch/commit, changed paths, commands and actual results, unresolved risks, and one next task. Keep it under roughly 800 words. Commit only task-related files when instructed. Never force-push, change repo visibility, deploy publicly, enable extra paid usage, or add real-money capability without an explicit request.


## create-private-repo.ps1

```powershell
param([string]$RepoName = "fundforge")
# Run locally after inspecting this script and authenticating with gh auth login.
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([string[]]$Arguments)
    & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Git failed: $($Arguments[0])" }
}

function Invoke-Probe {
    param([string]$Command, [string[]]$Arguments)
    # Expected nonzero exits must not become terminating stderr errors in PS 5.1.
    $ErrorActionPreference = 'Continue'
    & $Command @Arguments *> $null
    return $LASTEXITCODE
}

if ($RepoName -notmatch '^[A-Za-z0-9._-]+$') {
    throw "Repository name must use letters, numbers, dots, underscores or hyphens."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Install Git first." }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "Install GitHub CLI first, then run gh auth login." }
if ((Invoke-Probe -Command 'gh' -Arguments @('auth', 'status')) -ne 0) {
    throw "Run gh auth login first. Do not paste tokens into chat."
}

$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $PackageRoot
$ProfileText = & gh api user --jq '{login: .login, id: .id}'
if ($LASTEXITCODE -ne 0) { throw "Unable to resolve authenticated GitHub identity." }
$GitHubIdentity = ($ProfileText -join "`n") | ConvertFrom-Json
$Owner = $GitHubIdentity.login
if (-not $Owner -or -not $GitHubIdentity.id) { throw "Invalid authenticated GitHub identity." }

if ((Invoke-Probe -Command 'gh' -Arguments @('repo', 'view', "$Owner/$RepoName")) -eq 0) {
    throw "Repository $Owner/$RepoName already exists. Choose another name; nothing was overwritten."
}
if ((Invoke-Probe -Command 'git' -Arguments @('rev-parse', '--show-toplevel')) -eq 0) {
    $ExistingRoot = & git rev-parse --show-toplevel
    $ResolvedExistingRoot = (Resolve-Path ($ExistingRoot -join '')).Path
    if ($ResolvedExistingRoot -ne $PackageRoot) {
        throw "Package is inside another Git repository. Move it to a separate folder first."
    }
} else {
    Invoke-Git -Arguments @('init', '--initial-branch=main')
}
if ((Invoke-Probe -Command 'git' -Arguments @('remote', 'get-url', 'origin')) -eq 0) {
    throw "An origin already exists. This script does not replace remotes."
}
& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { throw "Existing staged changes detected. Resolve them first." }

$ExistingName = & git config user.name
if ($LASTEXITCODE -ne 0 -or -not $ExistingName) {
    Invoke-Git -Arguments @('config', '--local', 'user.name', $Owner)
}
$ExistingEmail = & git config user.email
if ($LASTEXITCODE -ne 0 -or -not $ExistingEmail) {
    $NoReply = "$($GitHubIdentity.id)+$Owner@users.noreply.github.com"
    Invoke-Git -Arguments @('config', '--local', 'user.email', $NoReply)
}

# Explicit package paths; do not stage an arbitrary personal resume or secret file.
Invoke-Git -Arguments @('add', '--', 'README.md', 'CLAUDE.md', '.gitignore', 'docs', 'fixtures', 'scripts', '.claude/agents')
& git diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    Invoke-Git -Arguments @('commit', '-m', 'docs: add FundForge specification and Claude handoff')
} elseif ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect staged changes."
}
& gh repo create "$Owner/$RepoName" --private --source=. --remote=origin --push
if ($LASTEXITCODE -ne 0) { throw "GitHub creation/push failed. Inspect state; do not claim success." }
$ResultText = & gh repo view "$Owner/$RepoName" --json nameWithOwner,isPrivate,url
if ($LASTEXITCODE -ne 0) { throw "Remote verification failed." }
$RemoteResult = ($ResultText -join "`n") | ConvertFrom-Json
if (-not $RemoteResult.isPrivate) { throw "Privacy verification failed. No visibility change was attempted." }
$ResultText
```


## create-private-repo.sh

```bash
#!/usr/bin/env bash
# Run locally after inspecting this script and authenticating with gh auth login.
set -euo pipefail

repo_name="${1:-fundforge}"
if [[ ! "$repo_name" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo 'Repository name must use letters, numbers, dots, underscores or hyphens.' >&2
  exit 1
fi
command -v git >/dev/null || { echo 'Install Git first.' >&2; exit 1; }
command -v gh >/dev/null || { echo 'Install GitHub CLI first, then run gh auth login.' >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'Run gh auth login first. Do not paste tokens into chat.' >&2; exit 1; }

package_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$package_root"
owner="$(gh api user --jq '.login')"
owner_id="$(gh api user --jq '.id')"
if [[ -z "$owner" || ! "$owner_id" =~ ^[0-9]+$ ]]; then
  echo 'Unable to resolve authenticated GitHub identity.' >&2
  exit 1
fi
if gh repo view "$owner/$repo_name" >/dev/null 2>&1; then
  echo "Repository $owner/$repo_name already exists. Choose another name; nothing was overwritten." >&2
  exit 1
fi

existing_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -n "$existing_root" && "$(cd "$existing_root" && pwd)" != "$package_root" ]]; then
  echo 'Package is inside another Git repository. Move it to a separate folder first.' >&2
  exit 1
fi
if [[ -z "$existing_root" ]]; then
  git init --initial-branch=main
fi
if git remote get-url origin >/dev/null 2>&1; then
  echo 'An origin remote already exists. Inspect it manually; this script does not replace remotes.' >&2
  exit 1
fi
if ! git diff --cached --quiet; then
  echo 'Existing staged changes detected. Resolve them before running this setup script.' >&2
  exit 1
fi
if [[ -z "$(git config user.name 2>/dev/null || true)" ]]; then
  git config --local user.name "$owner"
fi
if [[ -z "$(git config user.email 2>/dev/null || true)" ]]; then
  git config --local user.email "$owner_id+$owner@users.noreply.github.com"
fi

# Explicit package paths; do not git add arbitrary files such as a personal resume.
git add -- README.md CLAUDE.md .gitignore docs fixtures scripts .claude/agents
if ! git diff --cached --quiet; then
  git commit -m 'docs: add FundForge specification and Claude handoff'
fi
gh repo create "$owner/$repo_name" --private --source=. --remote=origin --push
privacy="$(gh repo view "$owner/$repo_name" --json isPrivate --jq '.isPrivate')"
if [[ "$privacy" != 'true' ]]; then
  echo 'Privacy verification failed. Inspect the remote manually; no visibility changes were attempted.' >&2
  exit 1
fi
gh repo view "$owner/$repo_name" --json nameWithOwner,isPrivate,url
```


## Golden financial reference

```json
{
  "schema_version": "1.0",
  "description": "Independent reference scenario for a strict virtual cash account; no costs, dividends or external flows.",
  "currency": "USD",
  "rounding": "ROUND_HALF_EVEN",
  "cost_bps": "0",
  "commission": "0.00",
  "starting_units": "1000",
  "partner_units": ["500", "500"],
  "starting_unit_nav": "100.00",
  "steps": [
    {"event": "capital", "settled_cash": "100000.00", "receivable": "0.00", "payable": "0.00", "quantity": 0, "nav": "100000.00"},
    {"event": "buy_trade_date", "quantity_bought": 10, "price": "100.00", "settled_cash": "100000.00", "receivable": "0.00", "payable": "1000.00", "quantity": 10, "mark": "100.00", "nav": "100000.00"},
    {"event": "buy_settlement", "settled_cash": "99000.00", "receivable": "0.00", "payable": "0.00", "quantity": 10, "mark": "100.00", "nav": "100000.00"},
    {"event": "mark", "settled_cash": "99000.00", "receivable": "0.00", "payable": "0.00", "quantity": 10, "mark": "110.00", "unrealized_pnl": "100.00", "nav": "100100.00"},
    {"event": "sell_trade_date", "quantity_sold": 4, "price": "110.00", "settled_cash": "99000.00", "receivable": "440.00", "payable": "0.00", "quantity": 6, "mark": "110.00", "realized_pnl": "40.00", "unrealized_pnl": "60.00", "nav": "100100.00"},
    {"event": "sell_settlement", "settled_cash": "99440.00", "receivable": "0.00", "payable": "0.00", "quantity": 6, "mark": "110.00", "realized_pnl": "40.00", "unrealized_pnl": "60.00", "nav": "100100.00", "partner_capital": ["50050.00", "50050.00"]}
  ]
}
```


## finance-reviewer.md

```markdown
---
name: finance-reviewer
description: Bounded read-only review of FundForge accounting, risk, concurrency and historical leakage changes.
tools: Read, Grep, Glob
model: inherit
---

Review the specified diff and only required neighboring contracts. Do not edit files, invoke other agents or review the entire repository. Verify supplied acceptance invariants against code. Focus on unit/cash sharing, journal meaning, FIFO, reservations/settlement, stale approval, concurrent overspending, duplicate economic events, coherent marks, next-event execution and data leakage.

Return at most five material findings. Each needs severity, exact code location, violated invariant and minimal reproduction/test to run. You cannot execute tests with these tools; clearly label unexecuted reproductions. Distinguish a demonstrated defect from a question requiring evidence. No speculative feature proposals. Output under 600 words. One review pass; stop.
```


## security-reviewer.md

```markdown
---
name: security-reviewer
description: Bounded read-only review of FundForge authorization, trust boundaries and session/data isolation.
tools: Read, Grep, Glob
model: inherit
---

Review only the requested diff and needed API/auth/session contracts. Do not edit files, delegate or expand into a repository-wide audit. Focus on self-approval, cross-fund and cross-season access, revoked membership, invitation reuse, server-time authority, CSRF where applicable, untrusted market/thesis content, secret exposure and costly-job limits.

Return at most five material findings with severity, exact location, violated boundary and a minimal request/test reproduction. Read-only tools do not run tests; state that limitation. Prefer concrete authorization paths to generic security checklists. Output under 600 words. Stop after one pass.
```
