# FundForge — hedge fund management game

Version 2.2 · 7 October 2026 · Product specification. What is built is in [PROGRESS](PROGRESS.md); the active plan is [ROADMAP](ROADMAP.md).

Planning revision 2.2-M1 adds full task-level packages for every phase through FF8 in [MILESTONE_PLANS](archive/MILESTONE_PLANS.md), indexed by IMPLEMENTATION_PLAN. [PLAN_REVIEW_AND_DECISIONS](archive/PLAN_REVIEW_AND_DECISIONS.md) records due decisions and corrections. Release boundaries unchanged: internal prototype FF3b, first playable FF5c, full initial game FF6c, optional research FF7 and selected-extension planning FF8. No feature implementation is claimed.

## 1. The game we are building

Two partners launch a virtual hedge fund and try to earn the right to run it for another season. They find investments, allocate risk, negotiate investor capital, fund the firm, manage a prime broker, and survive situations in which their investment thesis and their business needs conflict. A profitable position can still sink the fund if the team cannot finance it until the thesis pays off.

The core fantasy is **building and running an investment firm together**. Trading is one instrument of that fantasy. The first releasable game must contain investors with different needs, separate firm finances, long/short financing, investment committee decisions, a capital event, and a crisis. A correct trading ledger is an engineering foundation; it is not the finished product.

All capital, entities, counterparties, salaries, investor communications and rewards are fictional. No deposits, real execution, real investment solicitation, cash prizes or money-linked rewards. Numerical terms below are scenario house rules, not universal hedge-fund conventions.

### Design pillars

1. **Every opportunity competes with an obligation.** Research attention, risk capacity, investor patience and payroll cash are scarce.
2. **Cooperation creates decisions.** Partners have complementary responsibilities and pre-agreed authority; neither spends the game clicking approval on routine tickets.
3. **Consequences are explainable.** The game explains the chain from a decision to a fill, liquidity problem, investor reaction or business outcome.
4. **Uncertainty is fair.** Hidden market outcomes are uncertain; contractual deadlines and rule consequences are inspectable.
5. **A complete small firm before a large instrument catalog.** One prime broker, one base currency and a small equity universe can support a deep game.

## 2. Canonical launch configuration

| Item | Default |
|---|---|
| Managers | Exactly two human partners; interchangeable chapter roles |
| Season | 60 synthetic Mon–Fri business days, 5 January–27 March 2026; 82 calendar accrual dates; six chapters |
| Play cadence | Typically 20–30 minutes per chapter; save/resume; no real-market-hours requirement |
| Starting fund | $25,000,000 NAV; initial series price $100; 250,000 initial units across three LP series |
| Investors | Seed LP $10m; Patient LP $8m; Tactical LP $7m |
| Management company | $300,000 cash; $20,000 baseline weekly payroll and overhead |
| Fund terms | 1.5% annual management fee; 20% performance fee; no hurdle; series-specific high-water marks |
| Fee clock | Dated calendar accrual: management ACT/365; financing/borrow ACT/360; performance crystallizes annually on 31 December and pro rata on redeemed units |
| Investor dealing | Days 20, 40, 60; five-business-day notice; payment next business day |
| Optional contractual gate | 20% of pre-flow dealing NAV per window, pro-rata among eligible redemption requests |
| Universe | Twelve fictional USD instruments: ten equities in five sectors, broad equity ETF, defensive bond ETF |
| Prime broker | One fictional contract, explicit financing/collateral/borrow terms |
| Launch orders | Market and limit, whole shares, synthetic event-level tape, partial fills |
| Launch mandate | Gross <=150%; net -20% to100%; single-equity issuer long <=15%, short <=8%; direct sector gross <=35%; each approved diversified ETF absolute exposure <=50% |
| Drawdown | 10% warning; 15% freezes risk additions, with remediation still possible |
| Data | Versioned authored synthetic scenarios; deterministic server-side tape |
| Primary outcome | Earn renewal through published scenario objectives while remaining solvent |
| Technology | Next.js/TypeScript, FastAPI/Python modular monolith, PostgreSQL authority; fixtures and polling first |

The initial $100 unit price applies to each original LP series. Later subscriptions create separate fee series; a single aggregate “NAV per unit” is then misleading. Show fund AUM, a flow-neutral performance index, and each investor's series value. Managers own the management company 50/50 in narrative terms; this does not give them ownership of all investor assets.

Full rules live in [GAME_SYSTEMS.md](GAME_SYSTEMS.md), [FUND_ACCOUNTING.md](FUND_ACCOUNTING.md) and [SEASON_SCENARIOS.md](SEASON_SCENARIOS.md). Those contracts take precedence over old tutorial defaults. The legacy $100k accounting fixture remains a deliberately isolated arithmetic exercise.

## 3. The playable loop

A chapter opens with a board: the opportunity the team could exploit, the obligations coming due, and their weakest resource. The partners choose a plan, divide attention, and commit policies. Advancing the market resolves deterministic daily events and pauses only at authored decision windows or a material threshold.

Each chapter has three planned decision windows: opening committee, mid-chapter reassessment and chapter close. A material alert can interrupt advancement. Routine accounting days run automatically; the UI must not demand sixty daily checklists.

| Phase | Meaningful choice | Consequence |
|---|---|---|
| Brief | Which uncertainty matters? | Select research, LP contact or operating preparation |
| Committee | What is the fund willing to risk? | Approve thesis sleeves, budgets and contingencies |
| Operate | What can each partner execute independently? | Place delegated orders, source borrow, work an LP lead |
| Advance | Are the plans ready? | Resolve later market events, fills, settlements and costs |
| Respond | What must be sacrificed? | Reduce exposure, seek capital, gate withdrawals or spend runway |
| Debrief | Was the result luck, process or a constraint? | Explain attribution, update relationships and choose next chapter |

There is no reward for trading volume or compulsory activity. Holding cash can preserve the firm, but it may miss the contracted investment objective and reduce future fundraising. A fee-maximizing AUM strategy can burden liquidity and disappoint LPs. The design aims for several defensible paths rather than a single optimal checklist.

The market advances only after both partners are ready at a decision window. In asynchronous play, a partner can mark ready and leave queued instructions. No wall-clock deadline silently liquidates a fund while a person is offline. When an active session disconnects, pause at the next safe event boundary. A practice-only co-pilot may explain options; it cannot supply a missing human committee approval.

## 4. Partners and the investment committee

The Investment Partner owns research and portfolio construction. The Managing Partner owns treasury, investor relationships and operating capacity. Both can inspect everything and propose anything. Roles can swap at chapter boundaries.

A jointly approved strategy sleeve names an owner, allowed instruments and sides, maximum exposure, trade size, chapter turnover allowance, thesis conditions and expiry. Its owner may submit orders inside that authority without a new partner approval. Launch limits: each delegated order <=5% of current NAV; cumulative absolute filled notional <=15% of chapter-opening NAV per sleeve per chapter. Pending commitments count conservatively until resolved. Splitting tickets does not evade a budget.

Both partners approve new sleeves, changed budgets, gate use, new investor terms, large firm hires, prime-broker changes and exceptions to previously delegated authority. The proposer cannot supply the required second signature. An edited committee proposal loses its signatures. Risk limits remain hard constraints; signatures cannot waive them.

Either partner may cancel an unfilled order or activate the jointly pre-approved emergency reduction policy. Emergency trades must reduce a defined risk deficit without creating or worsening another hard deficit, including net exposure after costs; this is not a general “risk officer can trade anything” escape. Automatic margin liquidation and contractual buy-ins are system events, not unauthorized human approvals.

At disagreement, existing authorizations remain in force; no unsigned change executes. Teams can choose a smaller jointly acceptable plan, hold, or leave the window paused. The committee UI presents a small number of consequential choices, not an inbox of routine approvals.

## 5. The business simulation

The fund owns investor assets and pays disclosed fund expenses. The management company earns contractual fees and pays salaries, research services and its own overhead. Daily performance provisions reduce investor NAV but are not company income/cash until annual or redemption crystallization; renewal carries their history forward. The short season is a quarter-long evaluation, not a fund lifetime. It cannot silently spend investor capital on payroll or treat subscriptions as revenue.

LPs are named counterparties with capital, a contract, a preferred strategy, patience and observable concerns. Performance, style consistency, liquidity handling and honest timely reporting influence confidence. LPs also have external liquidity needs that excellent performance cannot always prevent. New capital needs a lead, due diligence, accepted terms and a dealing date; pressing “fundraise” cannot instantly cure a cash call.

A prime broker supplies a credit line and stock borrow under authored terms. Long positions, short proceeds, financing balances and restricted collateral all interact with investable cash. Borrow fees can rise, shares can be recalled and margin coefficients can tighten. These are core decisions, not flavor text.

The management company buys capability with real recurring cost. A research analyst unlocks an additional research assignment; an operations hire provides an additional contingency assignment and scenario-defined early operational warning; an investor-relations hire expands qualified lead capacity. Hiring never creates alpha, reduces ledger truth requirements or secretly changes execution luck.

## 6. Portfolio and market depth

Launch focuses on equity long/short and liquid ETF hedges. Short positions require available borrow and accrue explicit costs. Exposure is gross, net, sector and issuer, with hypothetical stress loss and liquidation time visible. Diversification is not a reward for buying many tickers that share one risk. Show scenario-authored market/sector sensitivities and stress P&L alongside notional ratios. A short broad-equity ETF can reduce positive market exposure; a long broad ETF increases it. A bond ETF is a rate-sensitive alternative with its own shock behavior, never a guaranteed negative-equity-beta hedge. These authored sensitivities are not fitted estimates or validated forecasts.

Every thesis has a catalyst, a horizon, observable evidence, a falsification condition and a sizing rule. Research spends attention to reveal scenario-authored evidence of known quality. It does not purchase guaranteed future returns. Information visible to either partner is shareable; useful cooperation comes from attention and judgment, not forced secret screens.

The synthetic market engine includes common market and sector factors, idiosyncratic news, changing liquidity and borrow stress. Scenario authors own the causal model and publish its version. Player trades incur modeled execution costs and consume liquidity but do not alter the exogenous reference tape in launch. A later endogenous market is a separate engine contract.

Use a few intraday synthetic events with actual ordered timestamps rather than infer an intraday price path from daily OHLC. No order fills at a price the players already observed before submitting it. Limits constrain execution price; market orders can gap and partially fill. Stop orders are a later, separately tested addition; a stop price will not promise an execution price.

## 7. Risk, failure and victory

Risk gates run at commitment and execution against reservations and unsettled obligations. Passive market breaches create a remediation state; they do not retroactively invalidate an earlier valid trade. A 15% drawdown pauses risk additions, not the game. The team can deleverage, protect remaining capital and earn a recovery outcome.

The game distinguishes portfolio insolvency, inability to meet a payable, broker default, management-company insolvency and voluntary controlled winddown. A positive NAV does not prove that enough settled cash is available. A firm can close responsibly with investors largely protected and still fail its renewal objective.

Launch renewal objectives, exact LP transition rules and defeat deadlines are in GAME_SYSTEMS. Campaign progression unlocks new mandates, scenarios and contract trade-offs. It does not grant better hidden fills or permanent return bonuses. Completed scenarios support a counterfactual replay with altered decisions; replay results are practice, not a fresh blind ranking.

The end report explains investment P&L, financing/borrow drag, fees, external flows, investor outcomes and firm cash separately. Show net time-weighted return and drawdown on a flow-neutral wealth index. Benchmark excess return is not regression alpha. Sharpe, beta and alpha are diagnostics only when the sample permits a meaningful estimate; short seasons carry explicit sample caveats.

## 8. Screen structure and usability

| Workspace | What the player sees | Principal action |
|---|---|---|
| Firm desk | Season objective; next three obligations; fund capital; firm runway; risk/LP alerts | Open chapter / advance |
| Investment room | Theses, sleeves, research evidence, portfolio and execution preview | Commit strategy / place delegated order |
| Capital and operations | LP pipeline, notice queue, liquidity ladder, borrow and broker contract | Fund an obligation / negotiate a trade-off |
| Committee | Versioned consequential proposals, alternatives and consequence preview | Approve / counter / reject |
| Reports and replay | Fund/firm reconciliation, LP statements, causal timeline and outcomes | Review / export / replay |

The first screen answers “what needs our decision?” before it shows a chart. The user should see the price of an action in attention, cash, risk or trust. Explain blocked actions with the calculation and a feasible next action. A read-only ledger drawer provides depth without occupying the main game loop.

Accessibility, keyboard use, readable numeric tables, reduced motion, reconnect states and mobile review are required. Avoid decorative terminal density. A five-minute demonstration should show one shared decision, a trade, an investor obligation, a crisis and reconciled consequences.

## 9. Deterministic engine and authority

The domain engine is a pure state transition over a versioned event log. Inputs are a season configuration, hidden market/event tape, authorized player commands and prior state. Outputs are typed domain events, journals, projections and explanations. No network or model call occurs inside accounting, execution or risk evaluation.

Store event_time, available_at, recorded_at, simulation phase, event identity, scenario/dataset/rule versions and actor. Hidden future tapes remain server-side; downloaded fixtures are developer resources and must never become client bundles in blind play. Fix the pseudorandom algorithm as well as its seed, or pre-generate the complete versioned tape. Separate random streams for market, evidence and LP exogenous needs so opening a panel cannot consume the next market random draw.

Commands use an idempotency key, expected state/proposal version and verified actor. PostgreSQL serializes economically conflicting operations at the fund boundary. A single transaction posts fills, journals, obligations, reservations, sleeve consumption and outbox events. Use bounded retries and unique business identities. Delivery can be at least once; economic posting must deduplicate. Replays restore the same state and journals.

FUND_ACCOUNTING defines the strict daily phase order, series accounting, collateral, margin deadlines and flow conventions. An internal integrity failure pauses economic transitions; an external broker/admin discrepancy blocks new risk and official NAV/dealing certification while verified obligations can still resolve under the accounting contract. A balanced journal alone is not independent reconciliation. Repair by explicit reversal/restatement; never overwrite a balance to satisfy a test.

## 10. Scope that preserves the game

| Delivery boundary | Included | Honest completion label |
|---|---|---|
| Foundation | Decimal ledger, accounting examples, event clock | Financial engine prototype |
| Integrated vertical slice | Two partners; 20-day opening arc; three LPs; sleeves; long/short; one broker; fees; firm costs; first dealing; redemption-only performance crystallization; one linked crisis | First playable fund-management slice |
| Season release | All six chapters/60 days; varied outcomes; operating choices; final renewal/winddown; recovery and security evidence | Hedge fund management game |
| Later research expansion | Permitted historical data, shared-engine backtests, evaluated ML, optional source-grounded assistant and external research integrations | Research extension |

Do not remove LPs, firm cash or financing from the integrated slice to hit an arbitrary date. Reduce scenario variety and cosmetic breadth first. Do not promise the full season in one subscription week.

Launch exclusions: options, futures, swaps, OTC, multi-currency, multi-prime optimization, tax, side pockets, real fund documents, filings, live order routing, real investor outreach, public competitive matchmaking and a freely acting LLM fund manager. Staff, gates and corporate events use the few declared rules needed by launch; deeper variants are later.

SEO and marketing integrations are excluded from the active plan. The previous OpenSEO assessment is archived research, not a dependency, acceptance gate or future task.

## 11. Engineering, research and evidence

Keep the modular FastAPI/PostgreSQL + Next.js architecture. Domain modules cover identity; seasons/clock; governance/sleeves; market/research; execution/borrow; treasury/margin; fund ledger/LP series; management company; scenario/LP transitions; reporting/replay. Redis, workers and WebSockets arrive only when their reliability problem is being implemented.

Auth, tenant isolation, immutable approvals, state-version conflicts, idempotency, fund locking and as-of authorization apply to every UI/API/job/export. Firm transactions use a separate ledger but shared season serialization when transferring fees. Untrusted market text is data. No LLM can approve, trade, post money, change risk or decide hidden outcomes.

A market adapter must establish coverage, rights, timestamps, feed, adjustments, corporate actions and reproducibility before historical/live use. Historical gameplay cannot silently inherit current settlement schedules or future data. Backtests reuse the execution, financing, fund and fee engine. Compare like mandates and cash/financing assumptions.

One later ML candidate is filtered HMM regime inference compared with a simple trend/volatility baseline. Fit only on chronological training data; use forward-filtered probabilities; evaluate on untouched held-out periods with trading-cost sensitivity. Rejecting a model is an acceptable result. Synthetic game success is not investment-edge evidence.

Tutorials attach to decisions: borrow recall, leverage, liquidity, unit issuance, fee recovery and conflicting stakeholder incentives. Template explanations work without AI. Optional LLM narration consumes verified event facts and cannot invent metrics or determine grades.

Follow IMPLEMENTATION_PLAN and ACCEPTANCE_TESTS for the actual build sequence. The current repository remains documentation-only. No authored fixture, architectural diagram or validation of document arithmetic constitutes a working application, tested database, paid-provider entitlement, deployed model or measured load result. The three cases have detailed bounded authoring schedules in SCENARIO_CONTRACTS. Compiled tapes, independently completed daily path totals, engine outputs and balance/playtest results remain pending. DESIGN_REVIEW_V2_2 records accepted/rejected recommendations; IMPLEMENTATION_HANDOFF limits the next task to FF0a.

## 12. Source discipline

The simulator borrows concepts, then deliberately defines its own contracts. SEC Investor.gov hedge-fund guidance describes fees and redemption limits as terms investors must understand; it does not prescribe this game's 1.5/20 structure or dealing windows. SEC T+1 guidance concerns applicable U.S. transactions, not every market or historical era. Regulation SHO's locate/close-out framework is not reproduced by adding a “borrow available” icon. Brokerage sources describe that broker's practices, not universal contractual deadlines.

Primary reference links and verification notes belong in SOURCES. Any future educational legal claim must be verified in its jurisdiction and date. This game is not an actual fund and does not claim SEC approval or comprehensive broker compliance.

## 13. v2.1 realism boundaries and build decisions

[REALISM_AUDIT.md](REALISM_AUDIT.md) records the source-backed review across portfolio management, risk, operations, accounting, research and game design. Real concepts, specific counterparty terms and deliberate game rules are labeled separately. The first release remains one fund, one broker, one currency and twelve instruments; it does not need derivatives, a complete compliance department or a large optimizer to feel like a fund.

Required small additions fix material errors: calendar accrual, annual/redemption fee timing, fair fee-series participation, post-redemption risk, signed hedge direction, one independent reconciliation exception, simple dividends/splits and a deterministic restricted-instrument state. The Managing Partner resolves funding/reporting/capital decisions; the Investment Partner resolves sizing, hedging and liquidation choices. Neither partner acts as a fictional independent administrator. Admin/broker NPCs are authored control records with separate responsibilities.

Chapter windows are compressed for play: five-business-day redemption notice, one-day payment and publicly specified broker response windows are fictional contracts. Real investors and prime brokers can have very different rights. Daily company payroll allocation and strategic-assignment budgets are house rules. The exact latent relationship score is a balance device, shown primarily as observable concerns and a relationship band.

The ending is an ordinary checkpoint after day61 opening administration, including weekend accruals and due day60 settlements. Residual investments are marked holdings with aged quotes, not liquidated cash. There is no special frozen-price terminal day. Winddown continues actual engine events. The scored 60-business-day investment result and the subsequent cash/claims bridge remain separate.

Use the updated accounting and scenario cases before implementation. Optional research libraries and architecture choices are owned by their dedicated assessment documents; no dependency should replace the authoritative economic event/ledger contract.

Renewal is displayed as **Renewal — conditional continuation**, with remaining company cash runway, a13-week forecast and any unfunded next-season gap. It is not a claim of durable business viability or a guarantee that another12-week campaign is financed. Preserve cash, liabilities and fee history into continuation; no automatic company recapitalization.

Canonical software boundary: [SIMULATION_ARCHITECTURE](SIMULATION_ARCHITECTURE.md). Dependency evidence: [LIBRARY_RESEARCH](LIBRARY_RESEARCH.md). Detailed player decision contracts are in GAME_SYSTEMS section11; the acceptance/implementation documents define pending evidence gates.
