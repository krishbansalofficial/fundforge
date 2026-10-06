# FundForge — complete design and implementation handoff

Version 2.0 · 6 October 2026 · Design package; application unimplemented.

Generated from canonical repository documents. Edit the sources and rerun scripts/build_documents.py.


---

Source: `README.md`

# FundForge

A cooperative hedge-fund management strategy game. Two partners build an investment business, manage outside investors' capital, and survive the consequences of their decisions.

**Status: design package v2.0, 6 October 2026. No application has been implemented.** This revision replaces the original paper-trading-first plan. The previous version remains in Git history.

## The game

Run a fictional $25 million long/short equity fund over 60 simulated business days, organized into six chapters. Choose research priorities, negotiate investment authority, allocate capital, manage financing, handle investor withdrawals, pay the firm's bills, and explain what happened. Sessions advance simulated time; players do not need to attend at real market hours.

The investment partner leads theses and portfolio construction. The operating/risk partner leads liquidity, financing, investor relationships and the business budget. Both can research and challenge decisions. Agreed strategy sleeves let routine actions proceed inside a jointly approved envelope; material exceptions require committee agreement. Every partner has consequential work beyond approving the other's tickets.

The objective is durable, mandate-consistent investor outcomes and a viable firm. A lucky leveraged bet does not erase unpaid obligations, broken promises, or insolvency. A disciplined winddown is a distinct outcome. All money, entities, contracts and obligations in the campaign are fictional.

## Read in this order

1. [Master specification](https://github.com/krishbansalofficial/fundforge/blob/main/docs/MASTER_SPEC.md): product, boundaries and architecture.
2. [Game systems](https://github.com/krishbansalofficial/fundforge/blob/main/docs/GAME_SYSTEMS.md): actions, roles, capital, progression and scoring.
3. [Season scenarios](https://github.com/krishbansalofficial/fundforge/blob/main/docs/SEASON_SCENARIOS.md): actual decisions and crisis arcs.
4. [Fund accounting](https://github.com/krishbansalofficial/fundforge/blob/main/docs/FUND_ACCOUNTING.md): authoritative financial contracts.
5. [Implementation plan](https://github.com/krishbansalofficial/fundforge/blob/main/docs/IMPLEMENTATION_PLAN.md) and [acceptance cases](https://github.com/krishbansalofficial/fundforge/blob/main/docs/ACCEPTANCE_TESTS.md).
6. [OpenSEO assessment](https://github.com/krishbansalofficial/fundforge/blob/main/docs/OPENSEO_INTEGRATION.md): inspected code, reuse choices and research boundary.

For coding, start with [Claude handoff](https://github.com/krishbansalofficial/fundforge/blob/main/docs/CLAUDE_HANDOFF.md), [progress](https://github.com/krishbansalofficial/fundforge/blob/main/docs/PROGRESS.md), then P01 in [prompt pack](https://github.com/krishbansalofficial/fundforge/blob/main/docs/PROMPT_PACK.md). The [combined Word document](https://github.com/krishbansalofficial/fundforge/blob/main/documents/FundForge_Project_Spec_and_Claude_Handoff.docx) is generated from the current Markdown documents.

## First playable release

A crisis-rich two-chapter opening arc (20 simulated business days) with two users, a reconciled long/short portfolio, borrow and margin, an investor redemption, fee accounting, separate firm runway, a committee decision, and a causal debrief. A buy/approve/chart demo is only an engineering foundation. The complete initial campaign expands that slice into all six chapters with reproducible seeds, save/resume, failure endings and balancing evidence.

## Engineering direction

Next.js/TypeScript, FastAPI/Python, PostgreSQL; pure deterministic financial domain; fixed precision; immutable events and journal; as-of information access; versioned rules and fixtures. Begin with synthetic data and polling. Add workers, live providers, ML and optional read-only AI after the core game is sound. No external API is required to play the base campaign.

OpenSEO is assessed as an optional source for alternative-data research and integration patterns. It is not the fund engine. No source has been copied, paid service activated, or deployment created in this revision.

The private repository is already set up. Do not rerun the legacy repository-creation scripts here. Nothing in this package represents a live fund, brokerage service, legal compliance certification, measured model result or completed software feature.


---

Source: `docs/MASTER_SPEC.md`

# FundForge — hedge fund management game

Version 2.0 · Design reset · 6 October 2026 · Specification, not implemented software

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
| Season | 60 simulated business days, 12 five-day weeks, six 10-day chapters |
| Play cadence | Typically 20–30 minutes per chapter; save/resume; no real-market-hours requirement |
| Starting fund | $25,000,000 NAV; initial series price $100; 250,000 initial units across three LP series |
| Investors | Seed LP $10m; Patient LP $8m; Tactical LP $7m |
| Management company | $300,000 cash; $20,000 baseline weekly payroll and overhead |
| Fund terms | 1.5% annual management fee; 20% performance fee; no hurdle; series-specific high-water marks |
| Fee clock | 252 simulated business accrual days per year; crystallize on days 20, 40 and 60 |
| Investor dealing | Days 20, 40, 60; five-business-day notice; payment next business day |
| Optional contractual gate | 20% of pre-flow dealing NAV per window, pro-rata among eligible redemption requests |
| Universe | Twelve fictional USD instruments: ten equities in five sectors, broad equity ETF, defensive bond ETF |
| Prime broker | One fictional contract, explicit financing/collateral/borrow terms |
| Launch orders | Market and limit, whole shares, synthetic event-level tape, partial fills |
| Launch mandate | Gross <=150%; net -20% to100%; long issuer <=15%; short issuer <=8%; direct sector gross <=35%; each approved diversified ETF <=50% |
| Drawdown | 10% warning; 15% freezes risk additions, with remediation still possible |
| Data | Versioned authored synthetic scenarios; deterministic server-side tape |
| Primary outcome | Earn renewal through published scenario objectives while remaining solvent |
| Technology | Next.js/TypeScript, FastAPI/Python modular monolith, PostgreSQL authority; fixtures and polling first |

The initial $100 unit price applies to each original LP series. Later subscriptions create separate fee series; a single aggregate “NAV per unit” is then misleading. Show fund AUM, a flow-neutral performance index, and each investor's series value. Managers own the management company 50/50 in narrative terms; this does not give them ownership of all investor assets.

Full rules live in [GAME_SYSTEMS.md](https://github.com/krishbansalofficial/fundforge/blob/main/docs/GAME_SYSTEMS.md), [FUND_ACCOUNTING.md](https://github.com/krishbansalofficial/fundforge/blob/main/docs/FUND_ACCOUNTING.md) and [SEASON_SCENARIOS.md](https://github.com/krishbansalofficial/fundforge/blob/main/docs/SEASON_SCENARIOS.md). Those contracts take precedence over old tutorial defaults. The legacy $100k accounting fixture remains a deliberately isolated arithmetic exercise.

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

Either partner may cancel an unfilled order or activate the jointly pre-approved emergency reduction policy. Emergency trades must reduce a defined risk deficit without creating another hard breach; this is not a general “risk officer can trade anything” escape. Automatic margin liquidation and contractual buy-ins are system events, not unauthorized human approvals.

At disagreement, existing authorizations remain in force; no unsigned change executes. Teams can choose a smaller jointly acceptable plan, hold, or leave the window paused. The committee UI presents a small number of consequential choices, not an inbox of routine approvals.

## 5. The business simulation

The fund owns investor assets and pays disclosed fund expenses. The management company earns contractual fees and pays salaries, research services and its own overhead. It cannot silently spend investor capital on payroll or treat subscriptions as revenue.

LPs are named counterparties with capital, a contract, a preferred strategy, patience and observable concerns. Performance, style consistency, liquidity handling and honest timely reporting influence confidence. LPs also have external liquidity needs that excellent performance cannot always prevent. New capital needs a lead, due diligence, accepted terms and a dealing date; pressing “fundraise” cannot instantly cure a cash call.

A prime broker supplies a credit line and stock borrow under authored terms. Long positions, short proceeds, financing balances and restricted collateral all interact with investable cash. Borrow fees can rise, shares can be recalled and margin coefficients can tighten. These are core decisions, not flavor text.

The management company buys capability with real recurring cost. A research analyst unlocks an additional research assignment; an operations hire provides an additional contingency assignment and scenario-defined early operational warning; an investor-relations hire expands qualified lead capacity. Hiring never creates alpha, reduces ledger truth requirements or secretly changes execution luck.

## 6. Portfolio and market depth

Launch focuses on equity long/short and liquid ETF hedges. Short positions require available borrow and accrue explicit costs. Exposure is gross, net, sector and issuer, with hypothetical stress loss and liquidation time visible. Diversification is not a reward for buying many tickers that share one risk.

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

FUND_ACCOUNTING defines the strict daily phase order, series accounting, collateral, margin deadlines and flow conventions. Reconciliation failure freezes execution and reporting certification. Repair by explicit reversal/restatement; never overwrite a balance to satisfy a test.

## 10. Scope that preserves the game

| Delivery boundary | Included | Honest completion label |
|---|---|---|
| Foundation | Decimal ledger, accounting examples, event clock | Financial engine prototype |
| Integrated vertical slice | Two partners; 20-day opening arc; three LPs; sleeves; long/short; one broker; fees; firm costs; first dealing; one linked crisis | First playable fund-management slice |
| Season release | All six chapters/60 days; varied outcomes; operating choices; final renewal/winddown; recovery and security evidence | Hedge fund management game |
| Later research expansion | Permitted historical data, shared-engine backtests, evaluated ML, optional source-grounded assistant and external research integrations | Research extension |

Do not remove LPs, firm cash or financing from the integrated slice to hit an arbitrary date. Reduce scenario variety and cosmetic breadth first. Do not promise the full season in one subscription week.

Launch exclusions: options, futures, swaps, OTC, multi-currency, multi-prime optimization, tax, side pockets, real fund documents, filings, live order routing, real investor outreach, public competitive matchmaking and a freely acting LLM fund manager. Staff, gates and corporate events use the few declared rules needed by launch; deeper variants are later.

OpenSEO is a potentially useful external SEO/website-intelligence component, not a finance engine or a mandatory market-data source. Follow the separately verified integration document; do not replace it with OpenBB or imply that an untested integration already exists.

## 11. Engineering, research and evidence

Keep the modular FastAPI/PostgreSQL + Next.js architecture. Domain modules cover identity; seasons/clock; governance/sleeves; market/research; execution/borrow; treasury/margin; fund ledger/LP series; management company; scenario/LP transitions; reporting/replay. Redis, workers and WebSockets arrive only when their reliability problem is being implemented.

Auth, tenant isolation, immutable approvals, state-version conflicts, idempotency, fund locking and as-of authorization apply to every UI/API/job/export. Firm transactions use a separate ledger but shared season serialization when transferring fees. Untrusted market text is data. No LLM can approve, trade, post money, change risk or decide hidden outcomes.

A market adapter must establish coverage, rights, timestamps, feed, adjustments, corporate actions and reproducibility before historical/live use. Historical gameplay cannot silently inherit current settlement schedules or future data. Backtests reuse the execution, financing, fund and fee engine. Compare like mandates and cash/financing assumptions.

One later ML candidate is filtered HMM regime inference compared with a simple trend/volatility baseline. Fit only on chronological training data; use forward-filtered probabilities; evaluate on untouched held-out periods with trading-cost sensitivity. Rejecting a model is an acceptable result. Synthetic game success is not investment-edge evidence.

Tutorials attach to decisions: borrow recall, leverage, liquidity, unit issuance, fee recovery and conflicting stakeholder incentives. Template explanations work without AI. Optional LLM narration consumes verified event facts and cannot invent metrics or determine grades.

Follow IMPLEMENTATION_PLAN and ACCEPTANCE_TESTS for the actual build sequence. The current repository remains documentation-only. No authored fixture, architectural diagram or validation of document arithmetic constitutes a working application, tested database, paid-provider entitlement, deployed model or measured load result.

## 12. Source discipline

The simulator borrows concepts, then deliberately defines its own contracts. SEC Investor.gov hedge-fund guidance describes fees and redemption limits as terms investors must understand; it does not prescribe this game's 1.5/20 structure or dealing windows. SEC T+1 guidance concerns applicable U.S. transactions, not every market or historical era. Regulation SHO's locate/close-out framework is not reproduced by adding a “borrow available” icon. Brokerage sources describe that broker's practices, not universal contractual deadlines.

Primary reference links and verification notes belong in SOURCES. Any future educational legal claim must be verified in its jurisdiction and date. This game is not an actual fund and does not claim SEC approval or comprehensive broker compliance.


---

Source: `docs/GAME_SYSTEMS.md`

# Game systems and balance contract

Version 2.0 · Proposed, unimplemented defaults · Read with MASTER_SPEC and FUND_ACCOUNTING.

## 1. Time, attention and cooperation

A season has six chapters, each ten simulated business days. Planned windows occur before days 1/6, 11/16, 21/26, 31/36, 41/46 and 51/56, plus each chapter close. A close can also serve as the next opening committee without repeating the recap. Material margin, recall, redemption or solvency events insert a decision window before their deadline. A pause changes real waiting time, never which historical information is visible.

Each partner has two strategic assignments per chapter, four for the team. Researching a thesis, conducting LP due diligence, negotiating a contractual offer or preparing a contingency each costs one assignment. Reviewing data already obtained, discussing, placing authorized orders, responding to a mandatory notice, and reading reports are free. Unused assignments expire; no speed bonus. Emergency remediation must remain possible after attention is spent.

Role ownership focuses the default task list; it is not an information barrier. Research assignments can be owned by either partner. The Investment Partner starts with portfolio/research responsibilities; the Managing Partner starts with investors/treasury. Each must have a valuable action while the other works. The first usability test should identify idle approval waiting and remove it.

The system does routine administration automatically and exposes exceptions. Players do not click to reconcile every day or type arbitrary reports for points. They decide which risk to take, what to disclose in an LP conversation, and what to fund.

## 2. Strategy sleeves and decision authority

A sleeve contains a named owner, approved instrument set, permitted sides, max gross allocation, max order size, chapter turnover budget, thesis/invalidation evidence, fallback action, review date and expiry. Default three available slots; two active sleeves in the opening scenario. Approved maximum sleeve budgets plus a central cash/hedge reserve cannot exceed the fund's permitted risk allocation.

Orders require a valid delegation OR an immutable order-specific second signature. A delegation is itself jointly approved. The owner is acting under prior authority, not self-approving a fresh committee proposal. A non-owner needs a fresh order approval or a changed sleeve owner. No human can grant authority to themselves.

Pending orders reserve sleeve capacity, borrow and settlement resources. Fill consumes the actual executed notional; cancellation releases the remaining commitment. Turnover means the sum of absolute fill notionals, including sales and covers, not net position change. Emergency system buy-ins are reported separately and do not block remediation because an elective turnover allowance is exhausted.

Counters are new versions. Version/content hash, actor and mandate/sleeve versions are displayed together. Approving a new version cannot revive a canceled or expired earlier order.

The emergency reduction policy is agreed at season launch. Either partner can submit a reduction plan that demonstrably reduces at least one active deficit and does not worsen another hard deficit; it may close positions and cancel risk-adding orders. System liquidation uses a separately declared deterministic priority. Opening a new hedge is not automatically “reducing risk”: its liquidity, gross exposure and margin effects must pass.

## 3. Research as a game decision

Every opportunity combines:
- Public evidence already in the brief.
- One or two researchable uncertainties with authored, fallible signals.
- A time horizon and a catalyst window.
- Liquidity/borrow requirements.
- An invalidation condition that can become visible before the price catches up.

An evidence card has a source, available-at time, reliability class and scope. It can narrow the scenario's possibilities but never reveal a guaranteed target price. Contradictory evidence is intentional and labeled. Content generation may change prose only; hidden outcome facts and reveal mechanics come from the frozen scenario.

Launch example: a manufacturer appears cheap but refinancing is approaching; supplier evidence supports revenue, while an operating report reveals working-capital strain. A pair trade can hedge sector risk while creating borrow cost and recall exposure. The best trade may be to wait for evidence, size smaller, or use the liquid ETF rather than the attractive thinly traded stock.

The research lab later supports reproducible backtests. Launch offers reviewed scenario evidence and a transparent stress calculator, not fake backtest charts.

## 4. Investor relationships and capital

LP confidence is a visible 0–100 state with a causal change log. It is not a hidden dice roll or a score an LLM awards.

| Investor | Initial capital/confidence | Preference | Initial restriction |
|---|---|---|---|
| Seed LP | $10m / 72 | Consistent broad long/short process, access to partners | No day-20 redemption; a known external $3m need on day 40 |
| Patient LP | $8m / 80 | Lower drawdown, reliable liquidity planning | First redemption dealing day 60 |
| Tactical LP | $7m / 65 | Higher net performance, fast response to deteriorating thesis | Eligible all windows |

At each chapter close, compute confidence deterministically:
1. Performance delta = clip(2 × (LP chapter net return in percentage points − target), −6, +6). Targets: Seed 0.35, Patient 0.20, Tactical 0.60 percentage points.
2. An avoidable active mandate breach or an uncured passive breach after the published remediation opportunity costs 6. A mere market-driven breach before an opportunity to act costs zero.
3. A certified report delivered by the chapter close earns 1; a missing/unreconciled report earns no bonus and costs 5. The engine generates reports automatically; certification depends on actual reconciliation.
4. A relevant LP meeting can recover at most 3 confidence once per chapter after a documented concern, never above the confidence immediately before that concern. Generic meeting spam does nothing.
5. Gate use costs Seed 10, Patient 8, Tactical 15 once per dealing window. An overdue contracted payment costs 15 once per incident.
6. Clamp final confidence to 0–100. Store every component and its policy version.

Those are balance hypotheses, not investor-behavior claims. They are frozen before a scored season and tested across scenarios.

At notice cutoffs days 15/35/55, eligible LPs with confidence below 40 request 50% of their then-held units; confidence 40–54 requests 25%; 55+ causes no performance-driven request. Locked LPs wait for their first eligible cutoff. Requests are unit quantities, so their final dollar value is unknown until dealing. The Seed's external $3m need is expressed as a dollar-target request capped by its units; final units are calculated at dealing. If it also has a confidence request, use the larger request, not both.

The external need is disclosed before investment choices can reasonably fund it. Confidence cannot make an investor's external obligation disappear. In the launch First Mandate scenario, Tactical also has an externally required 10,000-unit day-20 redemption, disclosed on day1 with formal notice on day15. Use the larger of this and its confidence-based request, not their sum. This guarantees a genuine capital-flow decision in the opening slice without manipulating performance.

### Fundraising pipeline

Prospect → qualified → diligence → conditional commitment → eligible subscription → admitted. Two scarce assignments complete qualification and diligence; an IR hire can expand the number of simultaneous prospects. Offers specify amount, mandate fit, fee terms, earliest dealing date and conditions. Launch supports standard-fee offers only; custom side letters and heterogeneous fee schedules are later.

A signed fictional commitment is not NAV, settled cash or margin collateral. Subscriptions enter on a dealing date only after funding is available and conditions pass. The team may reject or cap an offer when the strategy lacks capacity. A prospect's terms can demand lower leverage or a capital lock; accepting a conflicting mandate requires a new scenario contract, not a silent settings edit.

### Gates and fairness

Both partners must elect a permitted gate before the dealing event. Maximum dealt redemption amount is 20% of pre-flow, post-fee NAV for the whole fund at that window. Allocate pro-rata across eligible requests, including carried requests; no preferential payment to a favorite LP. The undealt portion retains units, stays exposed, and rolls to the next window. The gate cannot erase notices, forgive already-created payables or freeze capital forever without consequence.

Day 60 deferred requests carry into the debrief and reduce the renewal outcome. A season cannot win by deferring its obligations past the final screenshot.

## 5. Management-company economy

Opening company cash is $300,000. Baseline overhead/payroll is $20,000 per five-day week, accrued $4,000 each simulated day and payable at each fifth-day close. It earns cash only when contractual fund fees are paid. Accrued fee receivables are assets, not spendable payroll cash.

| Hire | One-time recruiting cost | Additional weekly cost | Declared capability |
|---|---:|---:|---|
| Research analyst | $10,000 | $5,000 | One additional research assignment each full chapter |
| Operations specialist | $10,000 | $4,000 | One additional contingency assignment; scenario-defined early operational warning |
| Investor relations lead | $10,000 | $4,000 | One additional LP assignment and second concurrent prospect |

Maximum two hires in launch. Hiring is a joint firm decision; recruiting cash is paid immediately; salary/capability begin at the next chapter boundary. Releasing a hire takes effect at the next weekly boundary and costs two weeks of that hire's salary. Staff never improve the market tape, waive reconciliation or reduce objective financing costs.

Projected runway = unrestricted company cash / committed weekly recurring cash cost. Display a separate forecast including known receivables; do not combine it with “cash runway.” Company equity can be positive while payroll cash is insufficient.

No owner withdrawals, cross-entity loans or discretionary capital injections in launch. They require explicit future contracts. This prevents a bailout button and prevents fund cash being used to rescue the management company.

If payroll cannot be paid, enter COMPANY_DISTRESS, pause discretionary spending and issue a five-business-day cure deadline. Cuts or earned fee payments may cure it. Otherwise end new investment activity and enter controlled winddown; record unpaid company obligations. Do not invent a capital contribution to keep a scenario alive.

## 6. Prime broker, borrow and liquidity

Launch broker contract: borrowing limit $7.5m fixed at season start; annual debit interest 6%; ordinary borrow fee 2%; restricted short collateral 100% of marked short value. Rates accrue /252 daily. A broker shock can change future rates or coefficients on an announced effective event; it cannot retroactively charge a revised rate.

Initial margin requirement = 50% of long marked value +60% of absolute short marked value. Maintenance =35% of long value +40% of absolute short value. Margin equity is fund NAV minus any explicitly ineligible receivables; launch treats ordinary valid T+1 trade receivables as eligible and unreceived subscriptions as absent. Fund liabilities already deducted in NAV must not be deducted again.

These are deliberately simplified fictional prime-broker terms, not Reg T or portfolio-margin compliance. They require two independent tests: adequate margin equity and enough usable settlement cash/credit. A margin pass cannot spend restricted short collateral on payroll or redemptions.

Short orders need a valid locate reservation and available capacity at fill. A locate is not a promise of perpetual borrow. Borrow rates/availability are time-stamped; recalls create quantities and deadlines. The authored launch recall allows two business days to find replacement borrow or execute a cover, then forces a buy-in at the deadline's first executable event. This is a cover-execution deadline; borrowed shares return at the resulting T+1 settlement and fees continue until return. This is a game contract, not a claim about every broker.

Liquidation time shows how many future tape events at the participation cap would be needed to exit, with stressed volume sensitivity. Spread and adverse impact grow as liquidity deteriorates. The launch reference tape is exogenous; player fills consume available event liquidity across their orders, preventing ticket splitting from obtaining unlimited volume.

Fund capacity has a cost: a large inflow can make the same strategy harder to execute. The player can hold capital temporarily, expand a liquid sleeve or decline it.

## 7. Risk and mandate state

Gross exposure = (long MV + absolute short MV)/NAV. Net = (long MV − absolute short MV)/NAV. Direct sector gross sums absolute direct-equity positions in that sector. ETFs appear separately unless point-in-time constituent exposure is explicitly provided. Cash is not another equity sector.

The default long issuer cap is15%, short issuer8%, direct sector35%, ETF50%. Gross150%; net between−20% and100%. Apply all reservations, obligations and borrow commitments. A pure risk reduction can be admitted under a documented exception if it does not worsen existing hard deficits.

Drawdown is measured on the net flow-neutral fund wealth index: warning at10%, freeze new risk at15%. Recovering above the threshold clears the automatic drawdown freeze only after a reconciled close; unresolved other breaches remain active.

A concentration breach from price movement gives the team the next available decision window to present a plan and up to two simulated days to execute an achievable reduction. A halt or lack of liquidity is recorded as inability, not fictitious compliance. Broker solvency/deadline rules still apply.

A visible risk card distinguishes: hard contract; internal policy; estimated stress loss; stale/uncertain data. An estimate can guide a decision but is not a guarantee against ruin.

## 8. Crisis state machine

NORMAL → WATCH → ACTION_REQUIRED → REMEDIATING → CURED, CONTROLLED_WINDDOWN or DEFAULT.

Each incident has an objective trigger, affected obligation, created-at/effective-at times, absolute simulation deadline, permitted remedies, escalation rule and causal links. Display the deadline in business events, not only a real-time countdown.

Maintenance margin shortfall is detected after each price event. Freeze risk additions immediately; cancel unfilled risk-adding orders. Pause for a player response before the next executable event. If a valid voluntary reduction cannot cure at that next event, forced liquidation begins there. No second arbitrary “grace day” is invented. Forced liquidation must obey actual modeled liquidity and can continue across events; insolvency can occur despite liquidations.

Priority: recall buy-ins whose deadline has arrived; then margin deficit remediation by highest estimated margin release per executable dollar cost; deterministic instrument ID breaks ties. The engine recomputes after every partial fill. A future order preview cannot guarantee a forced sale will fit the tape.

Debt-line reductions are separate from maintenance margin. An announced reduction creates a contractual repayment deadline. If the next settlement sweep cannot pay an obligation within credit/collateral rules, pause in treasury distress; deadline-specific cure rules control whether the team can continue. An overdue redemption does not magically become extra broker credit.

Insolvent fund NAV<=0 stops new risk; preserve the deficit and winddown ledger rather than displaying a negative “unit price” as a normal active fund. Other insolvency/default outcomes preserve unpaid obligations for the report. Game over does not delete liabilities.

## 9. Renewal, score and progression

The default season earns renewal only if all are true at the final certified day-60 close and the day-61 settlement tail:
- Fund NAV remains positive, no broker default, no overdue dealt redemption and no unresolved ledger discrepancy.
- Net time-weighted return is at least the scenario cash benchmark over the same 60 days.
- Maximum net-index drawdown is less than12%.
- Seed confidence is at least60.
- Company cash runway is at least four weeks, after all due costs and paid fees.
- No redemption remains deferred by a gate at the season endpoint.

This is a demanding selected contract, not a universal definition of a successful hedge fund. Scenarios may publish different goals before play. A day-61 tail resolves final cash obligations without granting another investment/research turn; fee accrual and market-risk treatment for the tail are explicit in FUND_ACCOUNTING.

Awards describe outcomes: Renewal; Survival Without Renewal; Responsible Winddown; Broker Default; Company Failure. A narrower recovery objective can recognize good crisis management without relabeling a failed investment mandate as a win.

For private comparisons, rank first by outcome tier, then by net return among teams meeting that tier's published objectives, then by lower drawdown, then a stable ID. Report investor capital returned and company cash alongside the ranking. Do not combine fund AUM and company fee income into “profit,” count subscriptions as returns, or award points for turnover, leverage, prose length or an LLM's opinion.

Campaign unlocks new scenario packs and strategy mandates, not additive market advantages. No strategy has a forced role in every scenario. Balancing must include passive cash, benchmark buy-and-hold, a diversified long/short ruleset, a concentrated gambler and gate/fee exploit attempts on the same tape.

Before release, measure whether each partner makes consequential decisions, whether feasible plans can win across authored scenarios, and whether at least two different strategies can survive each teaching scenario. Those are tests to run, not results already obtained.


---

Source: `docs/SEASON_SCENARIOS.md`

# Season scenarios and playable arc

Version 2.0 · Authored design, not a complete playable tape or measured balance result.

## 1. “The First Mandate” — launch season

Two partners receive $25m from three LPs and $300k of company seed capital. They have sixty business days to prove that a small firm can invest well, keep its promises and survive its first capital squeeze. Six chapters turn individual trading decisions into a business story.

| Chapter | Days | Central tension | New decision, not just new UI |
|---|---:|---|---|
| 1 — Earn the risk budget | 1–10 | Attractive paired thesis versus conserving attention/cash | Approve two sleeves; choose evidence; source borrow; make first delegated trades |
| 2 — The price of conviction | 11–20 | Worsening financing while first investor window approaches | Reduce, replace borrow or defend a thesis; complete first fee close and dealing |
| 3 — Bigger is not always better | 21–30 | A new investor offer versus liquidity capacity and hiring cost | Accept/cap/decline capital; buy one operating capability or preserve runway |
| 4 — Right thesis, wrong deadline | 31–40 | Seed LP's disclosed $3m external need competes with a catalyst | Plan settled liquidity; sell good positions, reduce shorts, or invoke an allowed gate |
| 5 — Show your work | 41–50 | Drawdown, investor concern and a possible recovery | Demonstrate remediation, choose which evidence earns attention and rebuild confidence |
| 6 — Earn renewal | 51–60 | Lock in solvency versus reach for the last return | Fund final obligations, preserve strategy, produce a certified renewal/winddown report |

The main teaching moment is that “the security later recovered” is not a sufficient defense if the firm could not meet a cash obligation along the way. A well-run firm may also underperform; the game distinguishes decisions from luck in the debrief without pretending to identify exact causal skill from one season.

## 2. First playable vertical slice

Build chapters1–2, twenty simulated business days, as a complete 40–60-minute two-player arc. A short guided demonstration can visit the same state in five minutes. Do not require all sixty days before playtesting cooperation.

The slice includes:
- Fund/firm setup, three LPs, charter and one jointly approved delegation for each partner.
- A small research choice, one long position and one located short or liquid hedge.
- Real trade-date/settlement/collateral accounting, company overhead and fee accrual.
- A changing borrow/financing condition with at least two feasible responses.
- Tactical LP notice evaluation plus an externally required 10,000-unit day-20 redemption, disclosed on day1 and formally noticed on day15; use the larger of it and a confidence-based request, not both. First dealing/gate choice, crystallization and payment tail are real consequences even on a profitable path.
- A reconciled chapter report separating market P&L, borrow/debt cost, LP flows, fees and company cash.
- Save/resume, identity isolation and a missing-partner pause.

The opening-arc acceptance run includes day21's opening administrative payment checkpoint so the day20 redemption and fees actually settle. It stops before day21 market events; the full campaign continues into those events normally. This checkpoint is not the special day61 terminal simplification.

The slice may use four tradable instruments and one frozen event branch. Its end state is “opening arc completed,” not the full season's Renewal outcome. Three LPs still exist; locked LPs help explain why not every investor can demand money today. Fundraising and staffing can appear as a chapter3 preview until the full-season gate, but fund fees, firm runway, financing and LP obligations cannot be omitted.

### Opening opportunities

1. **Quality versus fragile competitor.** Long ALTO (industrial quality), short BRIN (industrial over-expansion). Shared sector exposure offsets some thesis risk while the short adds borrow and squeeze risk.
2. **Liquid hedge.** A broad ETF sleeve reduces net market exposure efficiently but can reduce participation in a rising market.
3. **Wait for evidence.** More cash preserves optionality and financing capacity, but the opportunity can partly reprice before research is complete.

Use fictional businesses to avoid memorized historical outcomes. Evidence reveals demand, funding pressure and catalyst timing with declared uncertainty. No LLM invents the actual catalyst.

## 3. Linked crisis example

These numbers are an isolated stress reference with costs/fees/settlement held constant, not claimed season outputs.

Before the shock: fund NAV$25m; long positions$27.5m; shorts$5m; gross130%; net90%. Initial margin requirement at50% long/60% short =$16.75m, leaving$8.25m headroom. This book can pass the default gross/net rules when issuer/sector limits are also respected.

A later tape event marks longs down5% to$26.125m and shorts up10% to$5.5m. Net market loss is$1.875m; NAV=$23.125m. Simultaneously, a previously announced broker stress schedule changes maintenance coefficients to70% long/90% short. New requirement=$23.2375m; maintenance shortfall=$112,500. Drawdown is7.5%, so a broker call can occur without the15% internal drawdown freeze.

At unchanged prices and ignoring costs, selling at least$160,714.29 of longs releases$112,500 of required maintenance margin (0.70 per dollar). Whole shares, impact, changing marks, debt repayment and actual liquidity determine the executable cure. This calculation is a preview, not a guaranteed fill.

The shock's stressed initial coefficients are80% long/100% short. New risk remains blocked until the higher initial requirement is satisfied. A reduction can cure maintenance while still leaving no initial headroom, a valuable distinction.

Possible responses:
- Reduce before the effective shock after observing broker/volatility warning: lose potential upside but preserve freedom.
- Sell the liquid hedge/long holdings after the call: immediate capacity, changed portfolio thesis.
- Cover a short: reduces borrow/recall exposure and releases maintenance requirement, but covering can be expensive and collateral only fully frees on settlement.
- Replace a recalled borrow if an authored source exists: preserve the thesis at a higher ongoing fee, without claiming it solves a margin deficit by itself.
- Accept broker liquidation: lose control over timing and pay stressed execution costs.
- Gate eligible withdrawals when permitted: preserve future liquidity, cost confidence, and leave invested redemption requests outstanding. A gate cannot cure an already-due broker obligation by retroactively erasing it.

The crisis pauses for an actual decision before its next executable deadline. “Choose option B to win” is not hard-coded. Each choice changes quantities, liabilities, deadlines and confidence through the same engine.

## 4. Capital event example

Seed's$3m external need on day40 is disclosed at season start, with formal notice on day35. A player can plan from the start but cannot assume future sale proceeds will clear at an exact price.

At day39 the liquidity ladder shows day40 executable sells, day41 T+1 receipts, final redemption pricing, restricted short collateral and fees also due. Sales made too late, a halt, or unexpectedly adverse fills can make NAV positive while cash is insufficient.

A separate Tactical redemption may join the queue if confidence crossed a threshold. The 20% gate limit is applied to all eligible requests on day40's pre-flow post-fee NAV, pro-rata. If total requests are below the cap, electing the gate does not reduce payment; it still requires a documented purpose and its confidence consequences must be visible before confirmation. UI should discourage needless activation without silently changing contract mechanics.

A day40 subscription arrives only if its funding and admission conditions were already satisfied. A last-minute conversation does not create cash. A fund may decline new capital to avoid weakening returns or accepting incompatible terms.

## 5. Scenario variation without unfair surprises

Keep one authored seed for the initial teaching release and an explicit replay label. Later ship independent fixed versions:

| Scenario | Main pressure | Different viable behavior |
|---|---|---|
| Slow confidence | No dramatic crash, fee/runway pressure and limited catalysts | Low turnover and careful staffing |
| Crowded exit | Correlated short squeeze and borrow recall | Lower gross, liquid alternatives and earlier cover |
| Patient capital | Stable LPs, less liquid opportunities and delayed catalysts | Better research and measured capacity |
| Redemption season | External capital needs despite decent investment returns | Treasury planning and restrained new inflows |
| Whipsaw | Several plausible signals fail before recovery | Smaller reversible commitments, avoiding repeated style changes |

Hidden event outcomes must be frozen independently of a player's holdings. An event can have different consequences because the portfolio differs; it should not secretly target whichever position the team chose. Authoring can condition an LP response on published confidence/contract rules, but cannot rewrite market returns to punish a profitable strategy.

Research and contingency purchases reveal information at defined times, not eliminate exogenous events. Multiple signals can be imperfect. Forecast UI shows known obligations exactly and unknown market effects as ranges.

## 6. Outcome report and learning

Produce a causal timeline, not a moral judgment: evidence available → signed authority → fill/slippage → position/financing → event → cash need → response → LP/firm outcome.

The report answers:
- How much of the result came from longs, shorts, market exposure, financing, borrow and fees?
- Did NAV grow because of performance or subscriptions?
- Which obligations were forecast correctly, and which were surprised by prices or liquidity?
- Why did a margin call happen with positive NAV?
- Did company fees leave enough cash for its committed costs?
- Which investor requests were dealt, deferred and actually paid?
- Could a smaller exposure or earlier liquidity action have changed the specific crisis?

Counterfactual replay changes one chosen decision under the same tape. It does not prove a universally best strategy, and hindsight replays do not enter blind rankings.

## 7. Fixture contract and implementation gate

fixtures/season_scenario.json records canonical configuration, actors, chapter beats, one stress arithmetic reference and authored future-event placeholders. It intentionally does not contain a complete market tape, all daily prices, a production schema, a simulator or achieved results.

Before calling the slice playable, developers must add a validated event-tape schema; generate/freeze all twenty days; give every instrument coherent mark/volume/borrow data; define every signal's available-at time; implement commands/LP transitions; and replay the complete slice with two real user identities. A fixture syntax check alone establishes none of those behaviors.

Validation must demonstrate at least one feasible solvent path and one explainable failure path, preferably two strategically distinct successful opening paths. That requirement is not permission to change the tape after watching a specific player. Balance adjustments create a new scenario version.

Future historical packs need independently licensed/available datasets and era-appropriate settlement, marks and information timing. A title such as “2008” does not imply such a dataset has been obtained.


---

Source: `docs/FUND_ACCOUNTING.md`

# Fund accounting, treasury and deterministic resolution

Version 2.0 · Launch simulation contract · Not a description of universal fund accounting or prime-broker terms.

## 1. Boundaries and precision

Maintain two legal-entity-style ledgers: investor fund and management company. Their balances are never pooled. A season-level transaction coordinator can post the two sides of an actual fee transfer atomically while each journal balances independently.

Use Decimal/fixed precision: cash cents; prices at least six decimals; fee calculations at least twelve decimal places; investor units eight decimal places. Round monetary postings HALF_EVEN to cents. Carry fractional accrual residuals per obligation instead of rounding them away every day. For pro-rata cents/units use largest remainder, ties by immutable series ID. No binary-float money, silent penny creation or rewrite of a posted journal.

Quantity/borrow/lot subledgers reconcile separately to monetary journals. One journal balancing does not prove the economic event is correct. Every event has a unique business identity, phase/order, effective time, recorded time, rule versions and reversal link.

## 2. Minimum chart of accounts

| Fund assets | Fund liabilities / capital |
|---|---|
| Unrestricted settled cash | Trade payables |
| Restricted short collateral cash | Broker debit balance |
| Trade receivables | Marked short-position liability |
| Marked long securities | Accrued borrow/debit interest |
| Dividend receivables | Dividend-in-lieu payable |
| Other explicitly eligible receivables | Management and crystallized/uncrystallized performance-fee payables |
| | Dealt redemption payables; LP series capital |

Management company: unrestricted cash; accrued contractual management-fee receivable; crystallized performance-fee receivable; payroll/overhead payable; owner capital; fee income; operating expenses. Uncrystallized performance estimates are a disclosed forecast, not recognized company cash or an enforceable receivable.

Fund NAV = unrestricted cash + restricted cash + trade receivables + long MV + other valid assets − trade payables − short MV magnitude − broker debt − all other fund liabilities.

Short quantity is negative in the position view, but the monetary balance sheet represents a short liability. Do not subtract both signed short MV and another duplicate liability. Likewise, an accrued fee already in liabilities must not be subtracted twice in reported net NAV.

Reservations are commitments, not expenses or extra liabilities. They affect available resources, never NAV by themselves.

## 3. Long and short trade meaning

At a long purchase, recognize economic shares/cost and trade payable on the trade event. At settlement, extinguish the payable against cash. At a long sale, remove sold lots, recognize trade receivable and realized gain/loss; transfer receivable to cash on settlement. Mark remaining economic positions after the trade. FIFO applies separately to long and short lots.

At a short sale, recognize trade receivable and short liability at the executed price. On settlement, route the proceeds to restricted collateral cash. A later rise in the mark raises the liability and causes a loss. A cover creates trade payable and reduces the economic short liability; realize the difference against the matched short lots. Maintain borrowed-share and pending-return quantities through settlement; a cover does not create a long share lot. Short-to-long and long-to-short reversals are explicit close and open legs with fresh borrow/risk checks.

Launch uses T+1 on its synthetic business calendar. It permits selling an economically owned unsettled long, because linked settlement obligations and broker financing are modeled; this differs from the old strict-cash tutorial. Unsupported delivery chains must be blocked rather than hidden. All trades create actual settlement obligations; net same-day eligible cash settlements under the declared broker contract, retaining gross obligation records.

Short borrow fees continue on borrowed shares until their return settles, using that day's reference close value and active fee rate/252. Dividend-in-lieu expenses apply to borrowed short entitlements under the authored ex-date/pay-date events. Splits adjust positions, lots, borrowed quantities, pending settlement and limits consistently. Launch scenario tape may omit corporate actions, but the engine must reject unsupported imported actions.

Execution slippage is embedded in executed cost/proceeds. Separate explicit commissions, if enabled, are expenses. Do not charge embedded slippage again as another expense.

## 4. Cash, collateral, funding and margin are different

Restricted collateral target =100% of marked economic short exposure plus the contractually required collateral on unsettled share returns. A sold-short receivable counts toward the collateral commitment before settlement but cannot be withdrawn. A covered short's existing collateral becomes releasable at the cover's settlement, concurrently with payment and share return. Use obligation-level records to avoid releasing it on trade date and spending it twice.

At each price/settlement phase, compute collateral shortfall or excess. Transfer between unrestricted/restricted cash, with broker funding only if the credit line and applicable margin checks permit. Excess can release only when no unsettled obligation still requires it. Collateral movements do not change NAV.

Broker debit balance is a positive liability, not negative cash. Credit limit is $7.5m initially. An authorized sweep can draw credit to meet fund settlement/collateral obligations; it cannot finance management-company costs. Debit interest accrues daily at6%/252 of the prior closing funded debt, with a separately versioned rate. Borrow fees default2%/252 and can vary by instrument.

Available credit = max(0, credit limit − funded debt − credit reserved for already accepted obligations). Initial-margin headroom = margin equity − (0.50×long MV +0.60×short MV). Maintenance headroom = margin equity − (0.35×long MV +0.40×short MV). Negative maintenance headroom triggers the call state; initial headroom is required for new risk.

Margin equity defaults to net fund NAV, with ordinary valid T+1 trade receivables eligible. A scenario may explicitly haircut named receivables; unpublished subscriptions never exist on the fund balance sheet. Do not subtract liabilities a second time.

The settlement forecast computes unrestricted cash at each future due event after collateral needs, already accepted payables, scheduled redemptions/fees and permitted credit. Resources are reserved against the earliest conflicting obligation. Projected cash cannot be presented as guaranteed when sale price/liquidity is still unknown. The new-risk checker must satisfy both the forecast and initial margin; a liquidation/cure uses the documented maintenance exception.

At a due event, the treasury sweep:
1. Settles eligible trade receivables and payables, including linked cover collateral release.
2. Tops up required collateral; draws permitted credit if needed.
3. Pays dealt redemptions due now.
4. Pays crystallized/management fees due now.
5. Repays debt from residual unrestricted cash above the chosen operating buffer if the policy permits.

No payment may create negative unrestricted cash or exceed authorized credit. A failed step creates a named unpaid obligation and distress state. Equal-priority claims use pro-rata settlement and stable residual allocation, not arbitrary order IDs. The above seniority is a disclosed game rule. Actual priority across creditors is jurisdiction/contract-dependent and not simulated as law.

The operating cash buffer is a player treasury policy, not an extra NAV asset. Defaults to2% of NAV and may be lowered jointly. Mandatory due payments take priority over the buffer. Keeping a buffer has opportunity cost but receives no direct score reward.

## 5. Series accounting and external flows

Each initial LP owns its own series at $100/unit: Seed100,000; Patient80,000; Tactical70,000. Each later subscription opens a new series at $100 and HWM100, even for an existing LP. A subscription therefore cannot inherit another cohort's performance-fee loss carryforward. Launch has one fee schedule; series exist to handle entry timing, not custom side letters.

Allocate common daily investment P&L and common fund expenses proportionally to prior-close net assets of active series, after the previous dealing flows. Series-specific fees follow after common allocation. A new subscription begins participating the next daily period. Allocate cents deterministically and reconcile all series net capital to total fund NAV.

An externally funded subscription is not revenue. Until its dealing admission, hold it outside the fund in a simulated escrow record; it is not collateral or usable fund cash. On admission, receive cash and issue units. If the scenario models escrow on the same ledger instead, an equal liability must exclude it from NAV; do not mix the two policies.

A redemption request is not a liability. At a dealing event, after valuations/fees and gate allocation, fix the accepted units and price, cancel those units, reduce that series capital and create a redemption payable. The investor no longer bears portfolio risk on the dealt amount. Payment next business day reduces cash and payable equally; that payment is not a second external flow.

Undealt gated units remain invested and fee-bearing under the existing terms. They are not a fixed dollar claim. At the next dealing date their then-current value may differ.

Fund time-weighted daily return = (net fund NAV immediately before today's dealing flows / prior-close NAV after prior dealing flows)−1. Chain those returns into a wealth index starting at100. Cash settlement of an already-recorded redemption payable is NAV-neutral. Subscriptions and dealing-date redemptions change AUM, not investment return. All time-weighted comparisons use that index, including drawdown.

Report each LP's contributions, dealt distributions, pending requests, current net capital, fees and own return. Money-weighted LP return can be added only with a specified dated-cash-flow solver and undefined-case handling.

## 6. Management and performance fees

Annual management fee1.5%; business-day basis252. For each series, daily management fee = previous-close post-flow net assets ×0.015/252. Accrue fund expense/payable and management-company contractual revenue/receivable. No fee on capital before admission. No extra weekends in this synthetic calendar. A historical calendar must select and disclose its own contract instead of silently treating this as actual/365.

Daily provisional performance fee for series s:

- Let U be its current units and H its last crystallized post-performance-fee HWM per unit.
- Let B be today's capital attributable to the series after common P&L and management fee, with its previous uncrystallized performance liability added back.
- Pre-performance NAV/unit p = B/U.
- Target liability F =0.20×max(0, p−H)×U.
- Post-fee series capital = B−F.
- Post only the change from the previous provisional liability to F, including reversals after losses.

Crystallize on days20/40/60 after the day's accruals. Transfer the provisional fee into a fixed fee payable without charging it again. Set H to max(old H, post-fee series NAV/unit). Zero the provisional bucket; never lower H to enable charging again on mere recovery. Company recognizes performance-fee revenue/receivable only at crystallization.

All series crystallize at each dealing date before flows, so a redemption cannot escape the fee accrued to that date. No separate second redemption fee. When a series redeems fully, retain its closed record and crystallized obligations. A later subscription is a new series.

Management fees accrued since the prior window and crystallized performance fees are payable at the next business-day treasury sweep, after due redemptions. Payment is a fund asset/liability decrease and a company cash/receivable transfer; it is not new fund expense or second company revenue. Insufficient fund cash is a real fee-payment liability and can leave the company short of payroll.

### Arithmetic reference cases (isolated, costs off)

1. Performance fee:1,000 units, H100, pre-fee unit NAV110 → provisional fee $2,000; net capital$108,000; crystallized H108.
2. Loss/recovery: after that crystallization, pre-fee unit NAV104 → no incentive; a later108 → none;110 → fee$400 and net unitNAV109.60. H never falls to104.
3. Reversible accrual: before crystallization, p110 produces$2,000 accrued; next p105 produces$1,000. Reverse$1,000. Crystallizing earlier would instead leave the paid fee irreversible; timing is contractual.
4. Entry fairness: old series1,000 units has H100 and p95; new$95,000 subscription opens950 units at100/H100. Next common return10%: old p104.50 → fee$900; new p110 → fee$1,900. Old investors recover their own loss before paying; new investors pay on their own gain.
5. Management fee: $25m opening net assets ×0.015/252 =$1,488.095238… daily before residual rounding. Three months is not automatically $93,750; this 60-business-day season uses60/252 and a changing fee base.

Cases isolate specific rules; they are not asserted full-season outputs.

## 7. One authoritative daily event order

Each day uses a frozen, versioned ordered tape. Commands enter only during open decision windows; each has an eligibility event strictly later than its accepted information cutoff.

1. **Opening administrative phase:** activate previously announced contract changes; process prior-trade settlements and scheduled capital/fee cash payments via treasury; activate effective staff changes. A due failure opens distress before elective trading.
2. **Opening market event:** publish newly available public information and price/volume/borrow updates; mark all affected positions coherently; test recalls, credit and margin; open a crisis window if required.
3. **Execution event:** execute due forced obligations first; then authorized voluntary orders by accepted simulation sequence and immutable ID. Revalidate authority, borrow, settlements, margin and mandate for every partial fill against the state after earlier fills. Post journals/obligations/reservation conversions atomically.
4. **Further tape events:** repeat publish → mark/risk → eligible execution in timestamp order. Material pauses allow new commands only for strictly later events.
5. **Closing accrual phase:** close-mark positions; accrue debt interest, stock borrow, dividend obligations, management fee and company payroll/overhead; allocate series P&L; recompute provisional performance fees; run margin/treasury checks.
6. **Dealing close, when scheduled:** crystallize fees; apply elected gate to eligible redemption requests; create redemption payables/cancel units; admit funded subscriptions/new series; recompute NAV/collateral/risk after capital changes. If the flow creates a margin deficit, open a crisis for the next eligible event; admission never excuses missing a due payment earlier that day.
7. **Certified close:** reconcile both ledgers, obligations, collateral, quantities and series; certify reports; apply chapter LP confidence once; create upcoming cutoff requests when that day is a notice cutoff; compute outcome/progress; persist state hash and checkpoint.

At days15/35/55, a notice cutoff uses confidence most recently certified before the cutoff; it does not use an unknown future chapter result. Request generation is a unique business event.

Initial margin is checked before admitting voluntary risk. Maintenance is rechecked after each price, fill, fee and flow phase that changes equity or requirements. No end-of-day-only loophole.

Day61 is a terminal administrative tail for day60 T+1 trades, redemptions and fee payments. No new elective trades, market marks, research, management-fee accrual, company operating day or return period is added. Existing final marks are frozen solely for this disclosed game boundary; one extra day of borrowing/debit carry on still-open funding is accrued and allocated before final settlement certification, and deducted from terminal investor value. Report day60 strategy return separately from this terminal funding adjustment. The twenty-day opening slice instead stops after the ordinary day21 opening administrative phase: settle day20 obligations, then checkpoint before market events. Do not apply the special terminal carry projection there. Continuing chapter3 resumes from that phase checkpoint without repeating settlements; normal day21 accrual happens once at its close. Later continuous campaigns replace this simplification with a full next day and must not mix ranking versions.

After day61, surviving residual positions are marked holdings, not fictionally liquidated cash. Renewal can carry them into the next season; a winddown scenario continues its explicit liquidation tail and cannot claim all investors were paid from marks alone.

## 8. Execution model

Synthetic fixtures supply ordered executable reference quotes, spread, event volume, borrow state and availability time. Per-fund participation cap defaults5% of event volume summed across all orders in that instrument/event. A deterministic queue consumes this volume. A liquidity shock changes actual later capacity, not merely a cosmetic meter.

For cumulative same-side executed quantity Q and event volume V, define total adverse execution cost C(Q) = reference × Q × [half_spread_bps + impact_coefficient_bps × (Q/V)^2] /10,000. A subsequent quantity q incurs incremental cost C(Q+q)−C(Q). Its per-share executed price is reference + side×[C(Q+q)−C(Q)]/q, where side=+1 for a buy/cover and−1 for a sell/short. Default half-spread5bps and coefficient2,000bps; scenario overrides are explicit. Quantize executed prices before computing cash and carry the resulting cost residual deterministically. Maintain separate cumulative buy and sell quantities for cost, with one shared total-volume participation cap across both sides. Splitting orders cannot reset Q or reduce total modeled impact.

Market orders carry an explicit maximum cash/credit commitment and quantity authority, not an unlimited reservation. If a gap breaches that budget, reject or fill only the preauthorized affordable quantity according to the order's immutable partial-fill policy. Display “market order with cash protection”; do not imply that a reservation buffer is a market-price guarantee.

A limit order fills only at actual tape events where the modeled executed price satisfies its limit; choose the largest eligible whole-share quantity meeting limit, remaining budget and event capacity. No fill simply because an OHLC high/low crosses. DAY remainder expires at the declared close; launch GTC orders expire at the chapter boundary unless renewed. Canceled, recalled, stale or superseded authority cannot execute.

Complete states include DRAFT, PENDING_APPROVAL, AUTHORIZED_QUEUED, PARTIALLY_FILLED, FILLED, CANCELED, EXPIRED and REJECTED. “Authorized” can reference a delegation or specific committee signatures. A remaining partial order owns only its remaining reservations. Duplicate event delivery cannot consume the same liquidity, borrow or cash twice.

## 9. Required invariants and replay evidence

- Fund assets minus liabilities equals the sum of active series net capital.
- Company assets minus liabilities equals equity plus retained income.
- Total cash movement across a paid fee is equal and opposite; payment is not a second expense.
- Series performance fee follows its own entry/HWM history through loss, recovery, flow and closure.
- External subscriptions/redemptions do not create investment return.
- Restricted collateral, receivables, reservations and spendable cash never count as the same available dollar twice.
- Economic short quantity, borrowed quantity and pending return explain every difference.
- Credit limit, margin equity and settlement sufficiency are checked separately.
- Gate allocations conserve accepted units/value and treat eligible requests pro-rata.
- Forced liquidation obeys liquidity and preserves remaining deficit; it cannot erase insolvency.
- Fixed tape + commands + rules produce identical typed events, journal balances and checkpoint hash.
- A retry, cancellation/fill race or reversed event cannot duplicate economic meaning.
- Reconciliation failure pauses economic execution and report certification without concealing the failure.

These are acceptance obligations. The current documentation does not claim that their implementation or tests exist.


---

Source: `docs/OPENSEO_INTEGRATION.md`

# OpenSEO: repository assessment and bounded integration

Design version 2.0, 6 October 2026. Assumed target: [every-app/open-seo](https://github.com/every-app/open-seo), the upstream of the similarly named afazhriel/openseo fork. The user supplied a name rather than a URL; confirm a different target if intended. This assessment does not silently substitute OpenBB. No upstream source has been copied, installed, deployed, or connected to a paid account.

## What was actually inspected

Pinned source snapshot: `ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6`, retrieved through GitHub. The README describes SEO workflows and a DataForSEO-backed service. The LICENSE is MIT, copyright 2026 Ben Senescu. The dependency manifest shows a TypeScript/React/TanStack/Cloudflare stack, unlike FundForge's planned Python financial domain. Read these pinned files before reuse:

| Inspected path | Relevant observation | FundForge decision |
|---|---|---|
| `src/server/mcp/tools/get-domain-overview.ts` | Structured domain metrics and project-scoped handler | Optional research source, not price feed |
| `src/server/mcp/tools/research-keywords.ts` | Bounded seeds, partial results, market context, estimated volumes | Evidence cards must preserve scope and missingness |
| `src/server/lib/dataforseo/core.ts` | Timeouts, error classification, bounded retries, explicit non-idempotent exception | Adopt the design principle; implement in our adapter |
| `src/server/lib/dataforseo/client.ts` | Provider/service integration with billing dependencies | Do not transplant the whole client |
| `src/server/mcp/project-auth.ts` | Resource membership checks | Apply our own fund authorization at every boundary |
| `src/server/lib/r2-cache.ts` | Parameter-based cache keys, TTL and validation caution | Extend keys with information cutoff and dataset version |
| `package.json`, `LICENSE` | Stack and source license | No wholesale fork or forced stack migration |

These are source observations, not a security audit or performance certification. Source license and underlying data rights are separate. Preserve the MIT notice if substantial code is later copied; add exact paths, snapshot, modifications, and dependencies to a third-party notice. Validate provider retention/display/export rights before incorporating real data. Current pricing and API behavior must be checked when enabling a provider; this plan authorizes no charges.

## The valuable game feature: alternative-data research desk

Make information acquisition a strategic choice. A consumer-company analyst can compare search interest for a brand, a competitor, and a product category, investigate conflicting signals, and write a falsifiable thesis. The player spends fictional analyst capacity on a question, receives a timestamped evidence card, then decides whether it changes an existing position. The same action can use an authored fixture in campaign mode or an entitled adapter in a later sandbox.

Example: search interest for a fictional retailer rises, but a second report attributes it to product recalls. Buying the first bullish narrative without triangulation is a bad process; it must not be mechanically guaranteed to lose money. Evidence influences the player's judgment, not an automatic price multiplier or a hidden correctness grade.

Proposed research products:

| Product | Decision it supports | Required caveat |
|---|---|---|
| Brand/category search-interest comparison | Demand thesis, competitor substitution | Estimated search activity is not sales or unique customers |
| Domain visibility report | Distribution/customer acquisition thesis | SEO rank/estimated organic traffic is not audited revenue |
| Competitor evidence packet | Choose what to investigate next | Domain-to-listed-company relationship must be curated and dated |
| Source disagreement card | Decide to wait, size smaller, or buy another report | Conflicting proxies can remain unresolved |

Do not sum search volumes for close variants, infer stock prices from SEO values, or pretend historical monthly estimates were available daily. CPC is an advertising metric, not a security valuation. Today's provider retrieval does not establish what was knowable in an earlier season. Company-owned GA/Search Console integrations cannot provide competitors' private analytics; exclude those from the base design.

## Integration boundary

Preferred initial approach: no runtime dependency. Author synthetic research packets against a provider-neutral schema. Later, run OpenSEO separately and access an explicitly allowlisted research interface through a server adapter, or implement a small direct provider adapter if maintaining a second application is unjustified. Compare those alternatives in a bounded spike before choosing. Keep the engine and campaign usable when either fails.

Pipeline: operator-authorized fetch → normalized observation → provenance/rights checks → immutable approved dataset → as-of information service → player evidence card. A historical campaign consumes only the approved dataset. Never fetch current external results during a historical decision and backdate them.

`ResearchObservation` contract:

```json
{
  "id": "obs-example-001",
  "entity_id": "fictional-retailer-a",
  "metric": "brand_search_volume_estimate",
  "value": "12000",
  "unit": "estimated_searches_per_month",
  "geography": "US",
  "language": "en",
  "period_start": "2026-01-01",
  "period_end": "2026-01-31",
  "source_published_at": null,
  "observed_at": "2026-02-05T12:00:00Z",
  "available_at": "2026-02-05T12:00:00Z",
  "provider": "synthetic_fixture",
  "dataset_version": "research-demo-v1",
  "revision": 1,
  "mapping_version": "entities-v1",
  "quality_flags": ["estimate", "not_revenue"],
  "license_ref": "authored-fixture",
  "synthetic": true
}
```

In real snapshots, conservatively set `available_at` no earlier than collection unless independently evidenced historical publication supports earlier availability. Null timestamps must never mean unlimited visibility. Retain revisions; do not overwrite old observations. Store a raw-source hash only where retention rights permit it. Validate entity, unit, geography, period and missing values before import. Campaign fixture times use the scenario's declared clock mapping rather than an implicit wall-clock comparison.

The fetch worker uses a service credential scoped to the research project. Players cannot supply arbitrary target URLs or access another fund's snapshots. Allowlisted domains and bounded sizes prevent research requests becoming arbitrary network fetches. Provider text is untrusted; it cannot approve orders, alter mandates, run code, or become privileged instructions.

## Budget and failure contracts

There are two separate budgets: fictional research actions inside the game, and real provider/model usage. Spending fictional credits never authorizes a paid API request. Real usage defaults to disabled, with an operator-configured currency ceiling and request cap before activation. Record estimated/reserved/actual/unknown charge states. A timeout on a chargeable request may already have incurred a charge; do not automatically retry without provider-supported reconciliation or idempotency.

Cache keys include provider, endpoint, normalized parameters, entitlement scope, dataset/revision, and historical cutoff. An expired cache is either visibly stale in the research sandbox or unavailable; it cannot silently refresh a locked campaign. Errors distinguish unavailable, stale, forbidden, budget exhausted, and malformed response. No fabricated zeroes. The game continues with its approved fixture or existing observations, with provenance unchanged.

## What not to inherit

Do not reuse OpenSEO's billing account as virtual fund accounting, its project membership as investment authority, or its crawler as a general unrestricted research agent. Do not import its full SaaS, marketing, Cloudflare deployment, telemetry, or authentication stack just to display three research metrics. It does not supply exchange execution, stock borrow, fund NAV, capital accounts, LP contracts, a deterministic simulation clock, or a game economy.

OpenSEO can also help discover search terms and audit a future public FundForge marketing site. That is separate from gameplay and is out of the present implementation scope.

## Go/no-go spike and evidence

After the core game gate, spend one bounded task on: a saved fixture → normalized observation → as-of card; source inspection of the chosen API; rights/credentials/cost decision; one adapter contract test for malformed/partial/error responses; and a dependency/spend comparison of separate OpenSEO versus direct provider adapter. Stop if no valid historical data or useful player decision results. The fixture feature remains valuable without a live connection.

Success is improved research decisions in a blind playtest and correct information cutoffs, not a claim that SEO predicts returns. Any ML experiment needs point-in-time snapshots, an ablation against price-only/fundamental baselines, entity-held-out or chronological evaluation as appropriate, and costs. No claimed alpha until measured honestly.


---

Source: `docs/IMPLEMENTATION_PLAN.md`

# Implementation plan v2.0

The game must be fun and financially coherent before optional ML or live integrations. Work is dependency-gated, not a promise to finish in a fixed week. Every implementation milestone is currently pending. The user requested this redesign and file update; that does not mean application code has been built.

| Gate | Scope | Dependencies | Observable completion |
|---|---|---|---|
| FF0 | Inspect environment; freeze domain contracts; minimal app/DB/CI skeleton | P01 review | Versioned scenario schema, event phases, entities, command results, reproducible install and health checks |
| FF1 | Journal, marks, lots, LP series, trade/settlement obligations, separate firm ledger | FF0 | Independent arithmetic fixtures, balance/replay/reversal evidence; no UI-generated money |
| FF2 | Clock, future-event execution, costs/participation, long/short borrow, financing, margin and forced actions | FF1 | Gap, recall, collateral, deadline and halt cases; no fabricated fills |
| FF3 | Two-player authorization, sleeves, committee proposals, reservations and races | FF1–FF2 contracts | PostgreSQL race tests; no expired/revoked authority, double spend or third partner |
| FF4 | LP contracts/notices/dealing, fees/HWM, management-company budget, NPC trust | FF1–FF3 | Subscriptions/redemptions/fees reconcile; fund cash cannot pay firm payroll directly |
| FF5 | Integrate the two-chapter opening arc, authored research, crisis choices, save/resume and causal debrief | FF2–FF4 | Two people finish a meaningful 20-day opening arc (two 20–30 minute chapters) offline from providers |
| FF6 | Six-chapter campaign, endings, scoring, difficulty/balance, security and recovery | FF5 | Complete 60-day run; tested failure/winddown; balanced seeds and replay; two-user playtest evidence |
| FF7 | Licensed snapshots, optional OpenSEO adapter spike, shared-engine backtests, evaluated ML | FF6 | Point-in-time data gate, provider failure/cost checks, honest baseline comparison |
| FF8 | Optional asynchronous league/opponents, extra strategies/instruments, private hosting | Relevant prior gates | Separate permission, fairness, data and instrument acceptance contracts |

FF1–FF4 are engine foundations. FF5 is the first playable two-chapter release; FF6 is the full initial game. Neither may drop LPs, financing, firm survival and a real crisis merely to declare success early. FF7 is not a prerequisite for enjoyable play.

## FF0: freeze interfaces without overbuilding

Inspect actual tools/runtime versions and repository state. Choose one Python and one frontend package manager; pin and lock versions. Set up local PostgreSQL and CI. Confirm production authentication separately from controlled development identities. Do not build five dashboards first.

Write schemas for SeasonConfig, MarketEvent, Observation, Fund, Firm, InvestorSeries, Mandate, SleeveAuthority, ProposalVersion, Order, Reservation, Fill, BorrowContract, JournalEntry, MarginCall, LPNotice, ResearchTask, ChapterCheckpoint and Debrief. Include schema/rules/data versions, monotonic event sequence, simulated time, wall-clock audit time and actor/economic identities. Validate one authored scenario; a manifest without a price tape is not a runnable season.

Proposed package boundaries: `backend/domain/accounting`, `market`, `governance`, `fund_operations`, `game`; `backend/application` for transactions; `backend/adapters` for persistence/providers; `frontend` for views. Freeze the command/result contracts before parallel implementation. A modular monolith is sufficient.

## FF1–FF2: economics before presentation

Implement cash, restricted collateral, receivables, payables, debt, holdings, short liabilities, fund fees, LP capital and firm accounts without network calls. Trade-date postings and cash settlement are different events. Keep gross assets, NAV, margin equity, liquidity available for payments and company runway separate.

Use the legacy `fixtures/golden_scenario.json` only as the no-cost accounting smoke reference. It does not define campaign investors or capital. Add independent examples for short gains/losses, borrow expense, dividends in lieu, debt interest, fees, new series, dealing and fund/firm transfers. The authored `season_scenario.json` is a design contract; implement a validated tape/loader before claiming playability.

Build a deterministic event executor with reproducible RNG streams, explicit phase ordering, pauses at material decisions, and no per-refresh RNG. Surface missing/unsupported data rather than guessing. Mark-to-market can trigger a recoverable mandate breach; broker remedies and insolvency are separate state machines. Forced actions obey their specified execution/capacity policy and can fail to cure a deficit.

## FF3: governance that creates choices

Implement immutable sleeve charters jointly approved by both partners. Routine orders can be submitted by the authorized manager within those envelopes; exceptions require another person's affirmative consent. Recheck all fund-wide combined commitments at fill. Deadlock leads to a documented hold/default, never automatic acceptance.

Fund-serialized PostgreSQL transactions protect approvals, budgets, locates, reservations, orders and journals. Tests use independent connections/barriers, not SQLite. Use a durable outbox before asynchronous critical jobs; in the earliest synchronous slice commit the domain effects atomically. Persist economic IDs so worker retries cannot repeat costs, LP dealing or payments. Reconnect from an authoritative sequence/snapshot.

## FF4–FF5: make the management game

Deliver the first two complete chapters (20 simulated business days through first dealing) with briefing, allocation of scarce analyst capacity, a trading/hedging choice, one investor or broker deadline, a budget decision and an attributable outcome. Use structured choices and optional rationale text; prose quality and word count cannot earn trust or performance points.

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


---

Source: `docs/ACCEPTANCE_TESTS.md`

# Acceptance contracts v2.0

These cases describe tests to implement, not executed application tests. Financial expectations come from independently worked arithmetic and FUND_ACCOUNTING. Use fixed precision, a deterministic clock and real PostgreSQL for races. All house-rule parameters come from the season manifest.

## Accounting and ownership

| ID | Scenario | Required result |
|---|---|---|
| A01 | Campaign capitalization | Fund $25m = Seed $10m + Patient $8m + Tactical $7m; 250,000 opening units at $100; company cash $300k is separate |
| A02 | Legacy zero-cost cash fixture | Buy/settle/mark/sell final cash $99,440 plus six shares at $110 = $100,100 NAV; primitive fixture only |
| A03 | FIFO buy 10 at100, 10 at120, sell12 at130 | Realized gain $320; remaining basis $960, absent costs |
| A04 | Borrow and short100 at50, mark45; isolated no-cost fixture | $5,000 proceeds offset $5,000 short liability initially; subsequent mark produces $500 gain; restricted proceeds not free purchasing cash |
| A05 | Cover A04 at45 then settle | Gain remains $500; liabilities/collateral released once under contract; no second gain at settlement |
| A06 | 100 short shares owe $1 distribution | $100 dividend-in-lieu expense/payable once; payment does not duplicate expense |
| A07 | Borrow notional $5,000 at5% for one simulated accrual day | $5,000 × .05 /252 under declared precision/rounding; expense and payable reconcile |
| A08 | Fund borrows $100k | Cash and debt both rise $100k; NAV unchanged before financing expense |
| A09 | Pay debt principal versus interest | Principal reduces cash/debt equally; interest reduces investor NAV; no mixed P&L |
| A10 | Balanced journal, correction and replay | Every entry balances; reversals preserve original history; recomputed balances match materialized state |
| A11 | Split and distribution | Quantity/basis update once; no NAV jump from split alone; raw-price/dividend convention prevents double credit |
| A12 | Missing valuation input | Block dealing and authoritative close; show missing data, do not silently mix incoherent marks |
| A13 | Negative NAV after gap | Preserve deficit and terminal state; never clamp NAV to zero to hide debt |
| A14 | Fee paid from fund to firm | Fund payable/cash and company receivable/cash clear once; no new second expense/revenue at payment |
| A15 | Payroll $20k per five-day week | Company expense/cash only; no unauthorized charge to investor NAV |

## LP flows and fee series

| ID | Scenario | Required result |
|---|---|---|
| L01 | Isolated no-fee, single-series reference:100 units at110; subscription1100 (campaign uses a new100/HWM100 series) | New investor receives10 units at110; old investor retains11000; no manufactured investment return |
| L02 | Same no-fee series redeems10 units at110 | Burn10; record1100 payable; later payment clears it; remaining unit NAV110 |
| L03 | Notices outside5-day lead time/lockup | Defer/reject according to contract; no immediate discretionary payout |
| L04 | Gate invoked: NAV25m, eligible redemptions10m,20% cap |5m processed pro-rata;5m remains queued in units per contract; no first-arrival advantage |
| L05 | Accrued incentive fee reverses before crystallization | Only uncrystallized amount reverses; settled prior-period fees never disappear |
| L06 | Isolated fee example:100 units, HWM100, pre-incentive NAV/unit110,20% rate | Fee200; post-fee investor capital10800; new HWM108 under specified crystallization convention |
| L07 | Series after L06 falls90 then recovers108 | No second incentive fee before a new gain above108; returning to HWM is not profit eligible again |
| L08 | New subscription after earlier loss | New series has its own entry/HWM; new investor does not inherit another series' fee holiday |
| L09 | Redemption at crystallization plus new subscription | Event order matches FUND_ACCOUNTING; redeeming units pay their accrued fee; newcomers avoid prior-period fees |
| L10 | Large subscription/redemption at unchanged marks | Time-weighted performance unchanged; raw AUM change not counted as return |
| L11 | Redemption notice versus recognition versus payment | Request is not an immediate cash payment; accepted payable is not still counted as investor capital |
| L12 | Gate, notices and fee job retried | Same cohort, allocation, payable and journal IDs; no duplicated burns/fees |

## Authority and concurrency

| ID | Attack/race | Required result |
|---|---|---|
| C01 | Two simultaneous sleeve actions individually fit but combined violate fund limit | Serialize commitments; only valid combined state accepted |
| C02 | Manager proposes and self-approves exception | Denied; delegated authority does not authorize its own expansion |
| C03 | Routine order within active joint charter | Authorized manager may act without redundant second click; fill-time limits still checked |
| C04 | Edit proposal after approval | Immutable old version; material change requires fresh consent |
| C05 | Revoke/expire sleeve before execution | Queued risk addition cannot use obsolete authority |
| C06 | Idempotency key same payload / different payload | Same result once / conflict with no second economic effect |
| C07 | Cancel/fill race or duplicate worker deliveries | One allowed transition, consistent reservation, one fill/journal |
| C08 | Crash before / after DB commit | Rollback before; durable outbox and deduped delivery after |
| C09 | Two sessions try advance same phase | One authoritative event sequence; no double day/accrual/research reward |
| C10 | Third user, revoked user or cross-fund API/export request | Denied even with guessed IDs or old idempotency keys |
| C11 | Deadline tampering/disconnect/reconnect | Server time/phase controls; documented expiry boundary and pause behavior |
| C12 | Reconciliation mismatch | Trading/dealing freeze; explicit correction/replay required |

Run economic races on independent PostgreSQL connections with barriers and bounded timeouts. Report actual isolation/locks and trials. A stress test is evidence for its scenarios, not proof of universal correctness.

## Execution, financing and risk

E01: decision using event t cannot fill at t's already-known price. E02: gap revalidation checks current combined collateral/cash/exposure before filling. E03: no locate or insufficient borrow inventory blocks short addition; locate expires by contract. E04: recalled borrow enters deadline/buy-in workflow, not an instantaneous guaranteed fill. E05: borrow fees accrue across the stated held interval and stop at the specified closure event. E06: margin warning/call/deadline/forced action/cure/deficit follow the state machine. E07: forced liquidation respects market halt/capacity and may fail to restore solvency. E08: sell or short proceeds do not become spendable cash before the correct settlement/collateral event. E09: restricted collateral transfer changes liquidity, not NAV. E10: passive mandate breach allows approved corrective action but blocks worsening exposure. E11: drawdown15% freezes risk additions, not automatic insolvency. E12: order costs, partial-fill policy, reservations and final expiration are coherent. E13: daily OHLC cannot establish intraday stop/limit order sequence; synthetic intraday events or explicit next-event policies required. E14: business-calendar settlement skips non-trading days according to scenario. E15: same-seed independent funds do not affect one another's fills unless explicit shared-liquidity mode exists.

## Information, research and AI

I01: alter every future event; observations before its available_at remain identical. I02: event_time before cutoff but available_at after cutoff stays hidden. I03: chart/export/research/AI endpoints enforce same as-of filter. I04: replay saves include rule/data/seed versions and event sequence; reopening cannot reroll hidden outcomes. I05: OpenSEO current result cannot be backdated into a historical campaign. I06: estimated SEO traffic/search volume remains labeled and never becomes audited sales. I07: missing result remains missing, not zero. I08: provider timeout/budget exhaustion leaves core game playable and incurs no automatic ambiguous-charge retry. I09: fictional research credits cannot trigger real billing. I10: research text saying ignore mandate has no privileged instruction effect. I11: optional tutor cites supplied facts and cannot invent balance/Sharpe or approve trades. I12: optional opponent sees permitted observations only; malformed/late action falls back deterministically. I13: third-party private analytics require ownership authorization and are not competitor data. I14: cache entitlement/cutoff/version isolation prevents cross-fund or future leakage.

## Performance, game balance and usability

G01: returns +10% then−10% compound to−1%. G02: wealth100,120,90,110 gives maximum drawdown25%. G03: constant returns/too few samples produce an undefined or limited statistic, not infinite competitive points. G04: benchmark-relative return is not mislabeled regression alpha. G05: external flows and fees reconcile to investor performance by series. G06: leaderboards compare identical seed/rules/data/difficulty and expose survivorship/attempt policy. G07: insolvency/unpaid terminal obligations cannot be erased by positive trading P&L. G08: honest reporting cannot be farmed by repeating text or clicking reports. G09: hold/wait is legal, with opportunity costs from scenario rather than arbitrary penalties. G10: both roles have independent material choices; record waiting time and decision counts. G11: debrief ties effects to actual causal events, not fabricated counterfactual claims. G12: context lessons and consequences are readable without hiding numerical details. G13: no arbitrary punishment for real-life absence; simulation pauses under contract. G14: tutorial/replay and ranked attempts are clearly distinct. G15: compare several strategies across versioned seeds; record dominant/exploitative policies before retuning.

## Recovery and honest evidence

R01: restore separate database and replay journals to checkpoint. R02: flush cache/drop WebSocket messages; resync from authority without changing economics. R03: sensitive values absent from logs/exports. R04: keyboard/error/offline/reduced-motion flows work. R05: provider/model unavailable, fixture game works. R06: two testers finish the first two-chapter arc and explain crisis causes. R07: optional measured load reports hardware, operation mix, latency/errors/lock waits and invariant failures. R08: schemas reject malformed/negative/out-of-range inputs; narratives are escaped. R09: generated Word/Markdown bundle agrees with canonical source docs.

Report each executed case with commit, command, environment, fixture/rule checksum, expected/observed outcome and limitation. Pending, failed and passed are distinct. No application case in this file has been executed by this documentation update.


---

Source: `docs/DECISIONS.md`

# Decision log — v2.0

These are proposed product/engineering decisions, not claims of implemented behavior. Approved scope: whole-plan redesign and file update, 6 October 2026. Astra/high led the game and financial-system redesign.

| Decision | Current choice | Why / consequence |
|---|---|---|
| Product | Cooperative investment-business strategy game | Portfolio performance, investor obligations, financing and firm survival interact |
| Time | 60 business days, six chapters, pause/resume | No real-market attendance; preserve day-level financial effects |
| Initial scale | $25m outside capital; $300k separate firm cash | LP and business choices become meaningful; managers are not the only investors |
| Core strategy | Long/short equities and broad ETFs | A bounded but recognizably hedge-fund-like strategy |
| Governance | Joint sleeve charters; independent consent for exceptions | Preserves two-person control without approving every routine click |
| Core release | Fees, flows, borrow/margin, runway, crisis and debrief | Optionalizing these produced a shallow trading app |
| Scope sequencing | One complete chapter before six-chapter campaign | Validate fun before multiplying content |
| Financial authority | Pure domain + PostgreSQL transactions + immutable journal | Reconciliation, reproducibility and concurrency correctness |
| Rules authority | Versioned scenario/contract configuration | House rules are explicit; no hidden market manipulation |
| Data | Synthetic authored fixtures first | Deterministic, no fees/credentials, avoids memorized historical outcomes |
| OpenSEO | Assess every-app/open-seo at pinned snapshot; optional research adapter | User supplied repo name only; no unsupported assumption it is a market engine |
| Upstream reuse | Adapt bounded patterns; no wholesale fork/code copied yet | Keep finance ownership and avoid unrelated SaaS dependencies |
| AI | Optional explanations/baselines after game | No LLM control over financial truth, approvals or scoring |
| Workflow | One builder, bounded review | Astra/high was explicitly requested for this redesign, not perpetual delegation |

## Superseded defaults

Original 30-day/$100k equal-manager-capital season, strict long-only release, universal per-ticket partner approval, and postponement of fees/redemptions/shorts to an optional final milestone are replaced. The old arithmetic fixture remains a deliberately small primitive reference; it is not a campaign configuration. Full original docs remain recoverable from Git history before this revision. Current generated Word/Markdown bundles must be regenerated together.

## Still open before implementation

Runtime/dependency pins, auth SDK, database migration tooling, concrete API/schema validation, complete authored price tape, calibrated score/LP/broker parameters, playtest results, exact historical data rights, provider entitlements, hosting/budget and ML target. Resolve at the corresponding gate, not by inventing availability. Fund/accounting rule conflicts must be settled before code.

Log future changes with date, rationale, affected rule/data versions and acceptance cases. Do not change a live season's rule version in place.


---

Source: `docs/CLAUDE_HANDOFF.md`

# Claude handoff — FundForge v2.0

## Actual state

Private repository: https://github.com/krishbansalofficial/fundforge. Documentation-only, no frontend/backend/database/model/provider connection/deployment. The owner asked to rethink the whole product as a full hedge-fund game and evaluate OpenSEO, using Astra at high reasoning. That design review was performed; implementation remains pending.

The old $100,000, 30-day, mandatory-approval-for-every-trade plan is superseded. Current default: two firm partners manage $25m of outside LP capital and a separate $300k company over 60 simulated business days/six chapters. Fees, investor dealing, long/short financing, firm runway, committee governance and crises belong in the first playable game.

## Start

Read CLAUDE.md, this file, PROGRESS.md, DECISIONS.md, MASTER_SPEC.md, then the relevant game/accounting contracts. Inspect current Git state and installed tools. Do not read the generated combined document in addition to its source docs. Inventory installed skills by names once; do not assume a particular local Vercel installation or model syntax.

Use P01 in PROMPT_PACK.md to review contradictions and freeze FF0 contracts. Start only the requested bounded milestone. No application work was implicitly completed by generating this design. Do not recreate the repository or force-push it.

## Core experience

Two partners brief, allocate research effort, choose investments and capital/liquidity commitments, respond to an investor/broker/business event, advance a deterministic market clock, then inspect consequences. Delegated sleeves avoid an approval-clicking simulator; exceptions still require independent agreement. The operating partner has financing, LP and staffing/budget decisions of their own.

The first playable two-chapter arc must demonstrate a long/short book, borrow/margin, an investor flow, fee accounting, separate company runway, a consequential disagreement and a causal debrief. A chart and order ticket are foundation work, not the product gate.

## Important contracts

- FUND_ACCOUNTING owns event ordering, balances, fees/series, cash settlement and financial conventions.
- GAME_SYSTEMS owns actions, roles, trust, house rules, progression and evaluation.
- SEASON_SCENARIOS owns authored arcs and the vertical slice.
- MASTER_SPEC owns architecture, scope and canonical document map.
- ACCEPTANCE_TESTS lists required observable behavior, not executed tests.
- OPENSEO_INTEGRATION pins inspected upstream code and separates optional research from the engine.

Preserve both simulated time and wall-clock audit time. External research must never reveal a future historical fact. Treat all numerical campaign settings as explicit fictional house rules. Never represent simulated LP terms as universally applicable law or real fund compliance.

## Delivery boundaries

FF0–FF4 build foundations. FF5 is a complete two-chapter opening arc through day20. FF6 is the full campaign and reliability/balance gate. FF7 adds optional data/research/ML. All pending. Fixture mode requires no credentials. An OpenSEO assessment is not an installed integration; real API spend remains disabled.

At task end record changed behavior, actual checks and limitations, then update PROGRESS with one next task. Use a bounded financial/security reviewer where needed. Do not launch extra agents or redesign the whole product after every milestone.


---

Source: `docs/PROMPT_PACK.md`

# Copy-ready implementation prompts — v2.0

Use one prompt for one bounded task. The repository already exists. All application gates are pending. Model selection is performed in the actual client, not by claiming a prompt can switch its underlying model. The owner requested Astra/high for the completed design review; verify available model names in the implementation environment.

## P01 — Inspect the redesigned game and freeze FF0

Read CLAUDE.md, docs/CLAUDE_HANDOFF.md, docs/PROGRESS.md, docs/DECISIONS.md and docs/MASTER_SPEC.md. Inspect repository and tools. Read GAME_SYSTEMS, FUND_ACCOUNTING and the first SEASON_SCENARIOS slice. Identify concrete contradictions in event order, fee series, collateral, LP dealing, delegated authority and failure conditions. Resolve routine choices; list any unresolved contract that blocks safe code. Produce a bounded FF0 task contract with schemas, owned paths and observable checks. Do not revert to the old paper-trading MVP. Do not generate the whole app or claim implementation results.

## P02 — FF0 scaffold

Implement the approved FF0 contract only. Pin actual supported runtimes and package managers, create minimal Next.js/FastAPI/PostgreSQL development scaffolding, config validation and CI. Define versioned command/event/scenario interfaces. Validate the authored scenario manifest, explicitly identifying any missing tape. No broad dashboard, provider connection or paid service. Run actual relevant checks and update PROGRESS with one next task.

## P03 — One financial contract

Implement exactly the selected FF1/FUND_ACCOUNTING contract and related acceptance cases. Use fixed precision and an immutable balanced journal. Provide independent expected arithmetic, not expected values obtained from the implementation. Separate fund, firm and investor series. Test replay/reversal and meaningful boundaries. Treat legacy golden_scenario as a primitive fixture only. Report actual commands/results and pending cases.

## P04 — Execution, borrow and margin

Implement the selected FF2 transition with deterministic future-event eligibility, borrow/collateral/debt identities, settlement and deadline rules. Show a gap/recall/halt case and exact accounting. A forced action can fail; preserve the deficit. No daily-bar invented intraday path, no LLM-owned prices, no unrestricted broker execution. Freeze the contract before adding presentation.

## P05 — Governance and transaction races

Implement FF3 for two human partners with jointly approved immutable sleeve charters and independent consent for exceptions. Test revoked/expired authority, combined commitments, idempotency collisions, edit/approve and cancel/fill races using real PostgreSQL. Atomically persist financial effects and durable publication state. No SQLite substitution or self-approved expansion of delegated scope.

## P06 — LPs and management-company survival

Implement the selected FF4 contract for investor notices/dealing, series fees/HWM, firm budget or trust. Preserve notice versus recognized payable versus cash payment. Distinguish fund NAV, restricted cash, company cash and fee receivable. Provide arithmetic and an event-order trace. Do not replace mechanics with cosmetic meters or free-text AI scoring.

## P07 — First complete playable opening arc

Deliver FF5 against verified engine APIs. Read the vertical slice in SEASON_SCENARIOS. Include research effort, thesis/hedging, partner negotiation, investor/financing/business choices, consequences and causal debrief. The operating partner needs independent agency. No fake model/provider results. Run a two-user flow through day20 dealing, including disagreement, pause/resume and one crisis resolution; record confusion and actual duration.

## P08 — Bounded adversarial review

Review only this diff, its contracts and necessary dependencies. Return at most five reproducible defects with severity, violated invariant, exact path and expected/observed behavior. Prioritize fee/flow errors, collateral double count, authority races, future leakage and score exploits. Distinguish a definite defect from an open design question. Do not rewrite the architecture or start other agents.

## P09 — Campaign and balancing gate

Complete the selected FF6 chapter or balance task. Run matched seeded baseline policies and inspect concentration, cash-only, trust farming, replay rerolls and last-day obligation exploits. Keep rules immutable within a season. Report results with seeds and limitations. Do not claim a fun or balanced game solely because unit tests pass; include playtest evidence.

## P10 — OpenSEO spike

Read OPENSEO_INTEGRATION and the pinned inspected source paths. Start with fixture observation → normalized as-of evidence card. Evaluate separate OpenSEO service versus small direct adapter without migrating the financial stack. Record exact data rights, credentials and real request/currency caps before any paid activation. Cover stale/missing/partial results, ambiguous-charge timeout and historical leakage. No live connection is required to complete the fixture spike. No copied code without license/notice records.

## P11 — Optional research and ML

Use the same cost/execution engine as the game. Freeze point-in-time data and chronological split; define a simple baseline and a concrete target before training HMM or another model. Use filtered inference, avoid future normalization and record rejected candidates. Measure prediction/gameplay value separately from strategy return. LLM explanations have no financial mutation rights. No invented alpha or deployment evidence.

## P12 — Resume or diagnose

Read the small handoff and current Git state. Continue only the documented next task. If blocked, capture the failing command, smallest reproducer, invariant, attempted fixes and next diagnostic. After two failed repair cycles change the diagnosis rather than repeating prompts. Do not reload all docs or recreate the plan without a concrete conflict.

## P13 — Limited parallel work, only when requested

Freeze shared interfaces and choose disjoint tasks with separate ownership/worktrees. Keep migrations, journals and transaction contracts under one integrator. Use bounded outputs and actual acceptance evidence, integrate sequentially, and stop completed workers. Model names and agent support must be checked in the actual client. Never use parallelism to bypass permissions or assume extra usage quota.

## P14 — Evidence and handoff

Review RECRUITER_EVIDENCE. Build a truthful demo and evidence index from actual results. Clearly separate implemented, tested, measured, simulated and proposed. Update PROGRESS, source/rules manifests and docs affected by actual changes. Regenerate combined documents if canonical design changed. Do not add performance numbers or resume claims from aspirations.


---

Source: `docs/AGENT_WORKFLOW.md`

# Development and simulated-agent workflow

The 6 October redesign explicitly used Astra with high reasoning at the owner's request. That completed design task does not imply any model, opponent or application is deployed.

Default implementation workflow: one builder owns the bounded task. For a high-risk accounting, concurrency, information or security boundary, use one scoped reviewer when authorized. Reviewer returns at most five reproducible findings; builder repairs, then verifies the changed boundary. No recursive delegation or unlimited debate. Separate worktrees prevent file collisions, not credential access. Verify agent/model syntax in the actual environment.

| Role | Ownership | Evidence |
|---|---|---|
| Builder | Task paths and implementation | Observable behavior plus actual checks |
| Finance reviewer | Read relevant diff/contracts | Arithmetic or transition counterexample |
| Security reviewer | Read auth/data/tool boundaries | Reproduction or precise denied-access expectation |
| Integrator | Shared schema, migration and event contracts | Cross-boundary consistency |

Parallel work is useful only after shared interfaces are frozen and the user has requested it or applicable instructions allow it. Never split the same ledger/approval/migration contract across independent writers. A bounded alternative-implementation experiment needs a fixed external correctness criterion; comparing persuasive explanations is not evidence.

## In-game AI

Base campaign NPCs are deterministic, stateful rules. A later optional AI opponent receives only permitted as-of observations, its balances, authority and eligible actions. Typed proposals go through the same server checks and costs. It cannot approve a human's committee exception or access future prices, administrative credentials or external historical browsing.

Start with passive and deterministic baseline policies. Optional LLM rivals require a request cap, output bounds and deterministic timeout/malformed-action fallback. Historical event memorization can make apparently blind contests unfair; synthetic held-out scenarios and explicit limitations are necessary. No agent may change authoritative prices, NAV, fees, trust, scores or contractual deadlines through prose.

The tutor explains supplied verified facts with source/time references. Untrusted research never becomes a privileged instruction. Neither fictional research credits nor the existence of a coding subscription authorizes additional real API spend.

## Task contract

Record objective, input contracts/versions, allowed paths, forbidden scope, dependencies, acceptance cases, actual commands, review boundary, stop condition and one next task. Keep context bounded; preserve decisions and failing evidence when pausing. Do not make usage-limit or weekly-completion promises.


---

Source: `docs/RECRUITER_EVIDENCE.md`

# Evidence plan — claims must follow implementation

Current claim: designed a cooperative hedge-fund management simulator and specified its accounting, game economy and data boundaries. No application, model, performance, user adoption or load result is presently demonstrated.

| Portfolio proof | What to capture after it exists |
|---|---|
| Backend correctness | Independent fee/flow/short/collateral examples, balanced-journal replay, PostgreSQL race reproduction |
| Product engineering | Two-person crisis chapter, meaningful roles, usability observations and iteration |
| Distributed reliability | Crash/retry/outbox/reconnect/restore evidence with environment and limitations |
| Data engineering | Point-in-time data manifest, revisions/rights, provider failures and no-future-information checks |
| AI/ML | Baseline, frozen split, model/evaluation artifact, rejected candidates and actual deployment/fallback behavior |
| Systems design | Fund/firm separation, immutable authority, event phases and quantified tradeoffs |
| Open-source reuse | Pinned upstream assessment, justified adapter boundary, notices for any later copied code |

Suggested final demo: both partners receive a research lead; disagree about sizing; execute within the agreed mandate; face a borrow recall and LP redemption; arrange liquidity without paying company expenses from investor money; inspect the exact ledger and decision history in the debrief. This demonstrates engineering depth more clearly than scrolling through chart widgets.

After measurement, resume bullets may state what was actually built and the exact test/load/evaluation outcome. Do not convert the proposed $25m virtual scenario into real assets under management. Do not call simulated returns investment performance. A documented baseline-only result is preferable to an unevaluated AI claim.


---

Source: `docs/SOURCES.md`

# Sources and verification boundaries

Checked 6 October 2026 for this redesign. All campaign dollar amounts, horizons, rates, gates, margin coefficients, confidence effects and victory conditions are original fictional house rules. Source material motivates financial concepts; it does not certify this simulator as accurate legal compliance or a deployable investment service.

| Source | Narrow support | Boundary |
|---|---|---|
| [Investor.gov: Hedge Funds](https://www.investor.gov/introduction-investing/investing-basics/investment-products/private-investment-funds/hedge-funds) | Pooled capital, flexible strategies, leverage, fees and limited redemption rights | Does not prescribe this game's contracts or numerical defaults |
| [SEC: T+1 implementation announcement](https://www.sec.gov/newsroom/press-releases/2024-62) | Standard settlement change for most relevant broker-dealer transactions effective May 28, 2024 | Not every instrument, historical era, calendar or broker cash policy |
| [SEC: Key Points About Regulation SHO](https://www.sec.gov/investor/pubs/regsho.htm) | Locate and close-out concepts for short sales | Educational source includes older context; do not implement its historical timing examples as current universal rules |
| [OpenSEO upstream](https://github.com/every-app/open-seo) | SEO research scope and service dependency | Not a financial data engine or evidence of predictive alpha |
| [OpenSEO pinned license](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/LICENSE) | MIT source license, copyright2026 Ben Senescu | Provider data and third-party dependencies have separate terms |
| [OpenSEO pinned manifest](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/package.json) | Actual stack/dependencies at inspected snapshot | No assumption that those versions should be installed into FundForge |
| [OpenSEO provider core](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/lib/dataforseo/core.ts) | Bounded request/error/retry pattern and non-idempotent exception | Not a completed adapter, billing safety audit or free API entitlement |
| [OpenSEO domain tool](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/mcp/tools/get-domain-overview.ts) | Structured, scoped research output | Estimated digital activity must not be represented as company revenue |
| [OpenSEO keyword tool](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/mcp/tools/research-keywords.ts) | Market-scoped keyword research, missing/partial results | Current observations are not point-in-time historical evidence |
| [OpenSEO project authorization](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/mcp/project-auth.ts) | Resource membership gate pattern | FundForge must enforce its own fund/actor authority |
| [OpenSEO cache](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/lib/r2-cache.ts) | Parameter keys, TTL and schema-validation concern | FundForge additionally needs immutable dataset and as-of boundaries |

Repository content was read using the GitHub connection, including the pinned files above and the provider client. Web references were used for public source verification. The afazhriel/openseo result identifies itself as a fork of every-app/open-seo; the upstream is the working interpretation of the user's repo name. A different intended repository remains an explicit assumption to resolve, not a claimed fact.

No source code has been copied in this revision. The proposed adaptation of research, cache, authorization and provider patterns is design work. Financial/game formulas and scenario narratives are original design choices.

Before implementing real market data, recheck provider entitlements, redistribution/retention rights, available-at history, corporate actions and calendars. Before adding a legal-rule teaching module, recheck current primary authority separately. Before implementing framework, SDK, Claude or agent commands, inspect installed versions and current official documentation. Prior package links about coding subscriptions and agent syntax are not treated as freshly verified facts in this revision.


---

Source: `docs/PROGRESS.md`

# Current project state

Updated 6 October 2026. Design v2.0. Application implementation remains not started.

- Private remote: https://github.com/krishbansalofficial/fundforge; privacy and write access inspected for this task.
- Starting commit for redesign: `797e90d87c1304ed422af6f09c961a87b75ee8ca`.
- Owner requested complete game redesign, OpenSEO repository assessment, file updates and Astra/high reasoning. Astra/high was used for core game/accounting/scenario design.
- Current concept: two partners run a $25m outside-capital fund plus a separate $300k management company over 60 simulated business days/six chapters. Core systems include investment research, delegated governance, long/short financing, LP flows, fees/HWM, firm costs, crises, endings and causal debriefs.
- Replaced old master, plan, prompts, handoff, decisions, acceptance cases, reviewer/workflow and evidence guidance; added game, accounting, scenario and OpenSEO documents plus authored scenario contract. Regenerated combined Markdown and Word document.
- OpenSEO upstream/source inspected at `ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6`. No code copied, provider connected, paid usage enabled or integration built.
- Executed `python scripts/build_documents.py` and `python scripts/validate_design.py`: packaging/reference checks passed (19 source Markdown files; 16 bundled sections; 19 Word tables). Details are in PACKAGING_VALIDATION. Those are document/reference checks, not passing application acceptance tests.
- FF0–FF8 remain pending. No auth/database credentials, runnable scenario engine, deployed model, production application or measured user/load/return outcome exists.

## Next task

Run P01: inspect actual implementation environment and freeze FF0 contracts against MASTER_SPEC, GAME_SYSTEMS, FUND_ACCOUNTING and SEASON_SCENARIOS. Resolve any remaining accounting/event/authority conflict before implementation. The scenario manifest is an authored design fixture, not a complete runnable market tape. Build foundations then the complete FF5 opening arc; do not ship a trading-only demo as the finished game.

## Update discipline

Keep actual branch/commit, changed paths, executed commands/results, unresolved risks and one next task. Determine the redesign commit from Git history rather than copying the starting commit as current HEAD. No invented completion or metrics.


---

Source: `docs/PACKAGING_VALIDATION.md`

# Design-package validation — v2.0

These checks concern the documentation, reference arithmetic and generated review bundle. They are not application acceptance tests or evidence of playable software.

Validation commands for this revision:

```bash
python scripts/build_documents.py
python scripts/validate_design.py
```

Result: PASS for the commands above. Nineteen source Markdown files, sixteen bundled sections and nineteen Word tables were checked. No application result is implied.

The validator checks Markdown fences and repository-relative link targets, JSON syntax, all six legacy cash-account NAV states, independent opening-capital/fee/high-water-mark/stress-margin/gate/compounded-return arithmetic, Word archive/XML structure, and inclusion of every canonical source section in the generated Markdown bundle. The Word and Markdown outputs are produced by the same ordered source list.

Manual consistency review covers the sixty-day/six-chapter configuration, twenty-day opening slice, independent firm cash, series high-water marks, restricted collateral, dealing-versus-payment timing, deterministic forced actions, missing-partner pause, source provenance and the separation between planned features and implemented software.

The legacy repository-creation scripts were preserved and not executed during this redesign. Previous mock-script results are in Git history; they are not newly run results. The current remote was inspected as private, with write access. Publication uses one guarded non-force Git ref update after packaging.

Limitations: no Word application/page-render inspection; no runtime engine or full executable market tape; no application unit/integration, PostgreSQL race, security, gameplay, balance, provider, load or ML checks. All implementation gates remain pending. The authored season manifest records intended behavior, not measured outcomes.

