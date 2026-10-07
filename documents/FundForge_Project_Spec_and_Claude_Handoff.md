# FundForge — complete design and implementation handoff

Version 2.2 · 7 October 2026 · Design package; application unimplemented.

Generated from canonical repository documents. Edit the sources and rerun scripts/build_documents.py.


---

Source: `README.md`

# FundForge

A cooperative hedge-fund management strategy game. Two partners build an investment business, manage outside investors' capital, and survive the consequences of their decisions.

**Status: design package v2.2, 7 October 2026. No application has been implemented.** Three bounded independent reviews strengthened the existing v2.1 plan. The reported Python/Pydantic foundation and26 tests are absent from this checkout. Earlier research remains preserved.

## The game

Run a fictional $25 million long/short equity fund over 60 simulated business days, organized into six chapters. Choose research priorities, negotiate investment authority, allocate capital, manage financing, handle investor withdrawals, pay the firm's bills, and explain what happened. Sessions advance simulated time; players do not need to attend at real market hours.

The investment partner leads theses and portfolio construction. The operating/risk partner leads liquidity, financing, investor relationships and the business budget. Both can research and challenge decisions. Agreed strategy sleeves let routine actions proceed inside a jointly approved envelope; material exceptions require committee agreement. Every partner has consequential work beyond approving the other's tickets.

The objective is durable, mandate-consistent investor outcomes and a viable firm. A lucky leveraged bet does not erase unpaid obligations, broken promises, or insolvency. A disciplined winddown is a distinct outcome. All money, entities, contracts and obligations in the campaign are fictional.

## Read in this order

1. [Realism audit](https://github.com/krishbansalofficial/fundforge/blob/main/docs\REALISM_AUDIT.md), then [master specification](https://github.com/krishbansalofficial/fundforge/blob/main/docs\MASTER_SPEC.md): critical findings, priorities and product boundaries.
2. [Game systems](https://github.com/krishbansalofficial/fundforge/blob/main/docs\GAME_SYSTEMS.md): actions, roles, capital, progression and scoring.
3. [Season scenarios](https://github.com/krishbansalofficial/fundforge/blob/main/docs\SEASON_SCENARIOS.md): actual decisions and crisis arcs.
4. [Fund accounting](https://github.com/krishbansalofficial/fundforge/blob/main/docs\FUND_ACCOUNTING.md): authoritative financial contracts.
5. [Implementation plan](https://github.com/krishbansalofficial/fundforge/blob/main/docs\IMPLEMENTATION_PLAN.md) and [acceptance cases](https://github.com/krishbansalofficial/fundforge/blob/main/docs\ACCEPTANCE_TESTS.md).
6. [Simulation architecture](https://github.com/krishbansalofficial/fundforge/blob/main/docs\SIMULATION_ARCHITECTURE.md): ownership, interfaces, replay, precision, concurrency and information safety.
7. [Library research](https://github.com/krishbansalofficial/fundforge/blob/main/docs\LIBRARY_RESEARCH.md): retained pinned financial-library reviews; SEO/marketing excluded.
8. [v2.2 review](https://github.com/krishbansalofficial/fundforge/blob/main/docs\DESIGN_REVIEW_V2_2.md), [complete challenge authoring contracts](https://github.com/krishbansalofficial/fundforge/blob/main/docs\SCENARIO_CONTRACTS.md), and [exact next milestone](https://github.com/krishbansalofficial/fundforge/blob/main/docs\IMPLEMENTATION_HANDOFF.md).

9. [Full milestone work packages](https://github.com/krishbansalofficial/fundforge/blob/main/docs\MILESTONE_PLANS.md): all 20 milestones through final FF8, with ordered tasks, owned files, deliverables, validation and stop gates. [Decision register](https://github.com/krishbansalofficial/fundforge/blob/main/docs\PLAN_REVIEW_AND_DECISIONS.md) assigns unresolved choices/evidence to the phase that needs them. All application milestones remain pending.

For coding, start with [Claude handoff](https://github.com/krishbansalofficial/fundforge/blob/main/docs\CLAUDE_HANDOFF.md), [progress](https://github.com/krishbansalofficial/fundforge/blob/main/docs\PROGRESS.md), then P01 in [prompt pack](https://github.com/krishbansalofficial/fundforge/blob/main/docs\PROMPT_PACK.md). The [combined Word document](https://github.com/krishbansalofficial/fundforge/blob/main/documents\FundForge_Project_Spec_and_Claude_Handoff.docx) is generated from the current Markdown documents.

## First playable release

A crisis-rich two-chapter opening arc (20 simulated business days, through ordinary day21 opening administration) with two users, a reconciled long/short portfolio, borrow and margin, an investor redemption, fee accounting, separate firm runway, a committee decision, and a causal debrief. A buy/approve/chart demo is only an engineering foundation. The complete initial campaign expands that slice into all six chapters through ordinary day61 opening administration, with reproducible seeds, save/resume, failure endings and balancing evidence. These checkpoints include intervening weekend accruals, not a fresh Monday market valuation.

## Engineering direction

Next.js/TypeScript, FastAPI/Python, PostgreSQL; pure deterministic financial domain; fixed precision; immutable events and journal; as-of information access; versioned rules and fixtures. Begin with synthetic data and polling. Add workers, live providers, ML and optional read-only AI after the core game is sound. No external API is required to play the base campaign.

No trading framework is required for the initial game. Later research can use pandas, exchange_calendars and optional DuckDB; CVXPY/statsmodels need a specific evaluated advisory feature. SEO/marketing integrations are excluded from the current plan. No upstream code was copied, paid service activated, or deployment created in this revision.

The private repository is already set up. Do not rerun the legacy repository-creation scripts here. Nothing in this package represents a live fund, brokerage service, legal compliance certification, measured model result or completed software feature.


---

Source: `docs/REALISM_AUDIT.md`

# FundForge v2.1 — fund realism and decision-quality audit

6 October 2026 · Design review of v2.0, with v2.1 document changes · All application behavior remains proposed/unimplemented.

The product should teach two partners to preserve the ability to invest: portfolio conviction, investor obligations, financing and the management company's survival interact. v2.0 already had the right scope: outside LP capital, a separate company, long/short finance, delegated authority, fixed information cutoffs and deterministic records. Replacing that foundation with a larger trading terminal or many libraries would weaken the product. The highest-value changes are economic consistency, a few independent controls and scenarios whose choices actually alter claims, cash and risk.

This review applies six professional lenses—portfolio manager, chief risk officer, chief operating officer, fund accountant, quant researcher and cooperative-game designer. These are review perspectives, not claims of professional appointment or regulatory certification. Primary sources were checked on 6 October 2026; exact URLs and limits are below. Calculations and game prescriptions are our analysis, not rules imposed by those sources.

v2.2 supplement (7 October 2026): [DESIGN_REVIEW_V2_2](https://github.com/krishbansalofficial/fundforge/blob/main/docs\DESIGN_REVIEW_V2_2.md) adds the three independent reviews and disposition, including post-flow issuer error, settled replacement, retained collateral and termination policy. [SCENARIO_CONTRACTS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\SCENARIO_CONTRACTS.md) owns complete bounded authoring schedules. Retain the22 useful v2.1 findings below; current roadmap and handoff supersede the old next-task description. No economic implementation exists.

## 1. Prioritized audit and disposition

Priority **P0** blocks reliable financial implementation; **P1** blocks a credible playable release; **P2** is a controlled extension or measurement need. **Practice** means a sourced real-world concept; **Contract** means a selected fictional term; **House** means a deliberate game abstraction.

| ID / priority / lens | Finding in v2.0 and why it matters | v2.1 decision and boundary | Required evidence before release |
|---|---|---|---|
| R01 P0 Accountant | Common P&L used net series capital after different reversible incentive provisions, without defining how fee-reserve assets participate. Cohorts could receive different gross returns solely because their fee histories differ. | Contract: allocate common P&L using net capital plus reversible provision; exclude fixed liabilities. Do not claim every real administrator uses this method. | Two-cohort210,000 participation/21,000 P&L oracle allocates11,000/10,000, not10,903.85/10,096.15; series reconcile to226,800 net NAV. |
| R02 P0 Accountant/COO | Annual-looking fees accrued /252 and crystallized every20 business days; this rewards cashing short-term gains and disguises company runway. | Contract: dated management ACT/365, borrow/debit ACT/360; daily incentive provision; annual31 December crystallization and pro-rata on actual redemptions. Practice: computation, crystallization and payment are different[S1,S2]. | Calendar/weekend cases; fee provision reversal; no company receivable before crystallization; no day20 whole-fund incentive payment. |
| R03 P0 Accountant | Changing to redemption crystallization without a partial-series rule could reset the survivors' HWM or charge twice. | Contract: crystallize only accepted units' share of provision, preserve surviving HWM. Annual full-series crystallization takes precedence on the same date. | U1000→750, redemption27,000, fixed fee500, surviving provision1,500/net81,000/H100. |
| R04 P0 CRO | Redemptions were mostly a cash-flow problem; cancellation of units also reduces equity before payment. Leverage can breach while cash remains positive. | Practice/accounting consequence; pre-/post-flow risk preview. A valid redemption still deals; prepare a sale/gate or enter remediation. |25m/27.5m long/5m short→5m redemption yields20m NAV,162.5% gross,112.5% net; payment is NAV-neutral. |
| R05 P0 PM/CRO | “Risk reducing” could be interpreted as any sale/cover. Covering a short increases net and can violate the net cap after even small costs. | Contract: compare every hard deficit after each executable fill prefix; no blanket close-position bypass. Mandatory broker events may create a recorded passive mandate breach. | Cover5m in25m long/5m short book plus100 cost produces net100.0004%; companion sale must execute safely first. |
| R06 P0 COO/Accountant | A balanced internal journal was too close to being called reconciliation. A missing economic event can balance perfectly. | Practice[S3,S4]; small launch control: separately authored broker cash/positions and admin NAV/fee records, source timestamps, exception owner and reversal/restatement. No real-service/audit claim. | Missing200,000 short dividend lowers net NAV160,000 after40,000 provisional-fee reversal; old report remains accessible. |
| R07 P0 COO | Freezing all execution on any reconciliation exception can itself prevent a known payment or mandatory liquidation. | House: external discrepancy blocks new risk/certification, verified obligations may resolve; failed internal invariant pauses economic transitions for repair. | Distinguish report discrepancy from corrupted ledger; never certify a missed dealing or fabricated deadline cure. |
| R08 P0 Accountant/COO | Net same-day settlements was underspecified; restricted sale proceeds and failed receipts could finance unrelated payables. | Contract: net only fund/counterparty/currency/date/eligible-netting-set matches, preserving gross claims; link cover collateral release atomically. | Simultaneous short/long settlements; failed receivable; cover release; no double spend. |
| R09 P0 Accountant | Borrow was priced /252 and the start of fees was not as clear as the return endpoint. | Practice[S5,S6], contract details ours: ordinary borrow starts on settlement and ends at settled return; calendar fees include weekends; locate is only a reservation. | Friday short→Monday settlement has no weekend ordinary borrow; Friday cover→Monday return keeps Friday–Sunday fees. |
| R10 P1 Accountant/Quant | Corporate actions could be omitted from launch; this invites phantom short alpha and double-counted adjusted data when imported. | Bounded scope: cash distributions and integer splits only; reject unsupported actions. Raw executable marks plus explicit income; no total-return-price double income. |50→48 with2 distribution gives zero pre-cost total P&L long/short; split transforms lots, borrows and pending deliveries once. |
| R11 P1 PM/CRO | “Broad ETF hedge” lacked direction; gross/net/sector names do not expose shared factors. | House: explicit signed market/sector sensitivities and several stress cards. Short broad ETF can offset long beta; long bond ETF carries rate risk. | Directional hedge tests; hedge that lowers beta but raises gross/cash need; two equities sharing a factor. |
| R12 P1 COO/Game | An artificial day61 froze marks and charged a special day of carry, mixing ending presentation with finance. | House boundary: ordinary day61 opening checkpoint, with actual intervening calendar accruals; show aged marks and a bridge. Winddown runs real subsequent events. | Resume exactly once; no duplicate weekend fees/settlement; no holdings relabeled paid cash. |
| R13 P1 COO | A research feature could imply every obtainable fact is tradable information. | Practice[S7]; tiny house control: authored restricted instruments, cancel/block elective trades, release only by a dated public/clearance event. No legal-advice simulator or LLM classifier. | Day29 private packet cannot trade ALTO before day33 release; public unrelated research remains usable. |
| R14 P1 Game/IR | Exact0–100 “trust” can look like observable psychology, while meeting clicks become score farming. | House: visible bands, concrete concerns and deterministic auditable internals; recovery needs new verified information/fulfilled commitment. | Repeated meeting does nothing; external cash need persists regardless of relationship; versioned thresholds cannot move midseason. |
| R15 P1 Game/IR | Gate penalty applied even if the cap deferred nothing; using a gate could become arbitrary UI punishment. | Contract/house: penalize actual deferred eligible units, not an ineffective election. Keep equal treatment and floating deferred-unit value[S1,S3]. | Requests below cap deal fully; carried units reprice; retroactive gating cannot erase payables. |
| R16 P1 PM/Game | The opening two15%-turnover sleeves cannot magically create the130%-gross stress-reference book in one chapter. | Keep conservative opening slice; its recall/LP decision is meaningful without a margin call. High-gross challenge declares a valid warm start. | Authored starting journals/positions/authority; no fake successful opening deployment beyond budgets. |
| R17 P1 COO/Game |25m AUM and20k/week company overhead structurally require more than management fees. A cash-rich quarter can hide annual fragility. | Preserve startup tension, expose annual run-rate and13-week forecast. Four-week Renewal is a milestone, not a financed next quarter. No silent owner/fund bailout. | Forecast excludes provisional incentives/subscriptions as company cash; thin-runway successful and failure paths remain possible. |
| R18 P1 Quant | A “cash benchmark” without a credited-cash rate makes passive-cash balance claims meaningless. | Contract: launch unrestricted/restricted cash yield0%, matched gross cash benchmark0%; management fee makes passive fund net return negative. Interest/rebate variants need separate postings. | Gross and net baselines have identical timestamps/financing; no real risk-free yield attached to non-interest-bearing game cash. |
| R19 P1 Quant/Game | Attribution and replay could be presented as exact causal skill identification. A60-day sample cannot support that conclusion. | Practice TWR concept[S8]; separate accounting attribution, ex-ante rationale and model-conditional paired replay. No Sharpe/alpha gate or hidden correctness score. | Same tape/cutoff, altered command only; disclose mechanical consequences and sample/model limits. |
| R20 P1 Game | More accurate operations could become a clerical checklist and sideline one partner. | House: automatic routine controls, visible exception choices; PM controls exposures, operating partner controls liquidity/LP/company trade-offs; only material joint decisions. | Two humans each make consequential decisions; measure idle approval time and explainability, not click count. |
| R21 P2 CRO | Initial/maintenance coefficients,2-day recall and advance broker warning can be mistaken for guaranteed real-market rights. | Contract/house clearly labeled. Real broker requirements may change and liquidation rights differ[S9]. Keep tutorial warning for fairness; future no-warning stress must be predeclared as a possible rule. | All broker notices carry effective/deadline timestamps; no retroactive rates or invented legal grace period. |
| R22 P2 Quant/Architect | A large optimizer/backtester stack could become a second account/execution truth and obscure point-in-time data. | Retain pure deterministic domain and one economic engine; use external libraries for bounded analysis/adapters only. Research/ML never adjudicates balances, fills or scores. | Shared-engine replay and baseline/holdout evaluation precede optional research integration; no installed-library claim from this audit. |

## 2. What stays deliberately simplified

The simulation is a fictional equity long/short startup, not an institutional operating manual. One broker, USD, twelve instruments, whole-share orders, no personal trading, no taxes, no derivatives and no side letters keep first-release scope achievable. The settlement rule models a selected T+1 contract rather than every exchange/era[S10]. The single-netting-set design does not reproduce central clearing or a prime brokerage legal agreement. Restricted collateral100%, coefficient margin, five-day notice, next-day redemption payment and six chapters are authored contracts/house rules.

Daily marks and independent control records can be deterministic synthetic data. Real firms do not have a perfect future market tape; the player sees only available events while the server holds the scenario's hidden realization. Research evidence changes information, not the realized exogenous market. Default staff costs and strategic assignments are balance hypotheses. Do not sell missing complexity as realism; define the boundary and test within it.

Annual performance crystallization is a **chosen** fund contract. ESMA's guidance concerns UCITS and specified AIFs, contains exceptions and does not establish that every hedge fund must crystallize annually[S2]. ACT/365 management fees are also our contract, not a sourced universal standard. Provider documentation describing one broker's360-day borrow basis supports a possible convention only[S6]. Fee-series participation accounting is mathematically specified here so fairness is testable; production fund documents and administrator methodology would control a real fund.

### Strategy, jurisdiction and counterparty variation

| Context | What changes in practice / boundary for FundForge | Launch decision |
|---|---|---|
| Equity long/short | Single-name borrow, recalls, equity factor exposure and investor dealing matter | Canonical contract; keep simple event execution and explicit cash/borrow controls |
| Market-neutral equity | Near-zero dollars need not mean near-zero beta, sector or factor exposure | A later mandate can tighten signed factor targets; do not market current net limits as neutrality |
| Global macro / futures | Variation margin, derivative multipliers, expiry, FX and cross-market calendars dominate | Deferred instrument lifecycle, not a renamed equity strategy |
| Credit / distressed | Coupon/default/recovery, stale pricing, settlement and financing terms can differ materially | Deferred; no liquid-equity mark or redemption schedule transplanted automatically |
| Private / illiquid assets | Valuation and capital-call/exit horizons do not fit daily liquid marks and next-day redemptions | Excluded rather than hiding risk in a cosmetic liquidity slider |
| Investor domicile, fund domicile and adviser regime | Offering rights, valuation duties, fee restrictions, disclosure and insolvency priority differ | No jurisdictional compliance claim; real deployment would need actual governing documents/advice |
| Different prime brokers / custodians | House margin, eligible collateral, netting, funding and liquidation discretion vary | One versioned fictional broker; no imported Reg T or global portfolio-margin promise |

### Ownership, service providers and omissions

One pooled fund owns every investment; sleeves are decision/attribution tags. Investor economic allocation follows the fee-series contract, never discretionary trade assignment. The two partners are managers, not an independent fund board, auditor or administrator. The simulated broker owns its confirmations, borrow and contractual financing notices; the simulated administrator supplies independent control NAV/series records; the manager must investigate differences. Both external records remain authored evidence until actual adapters exist. Neither provider fixes our source ledger silently.

Baseline management-company overhead bundles fictional administration/legal/audit/compliance support. Enumerated trading/financing costs and disclosed fees belong to the fund; no additional pass-through fund expenses are invented. Expense allocation varies by real fund documents; this selected policy avoids a new invoice-management subsystem.

The valuation model omits broker-quote selection for illiquid instruments, valuation committees, audit sampling and complex fair-value hierarchies. LP due diligence is a short evidence/terms/funding pipeline, omitting beneficial-owner verification, AML/KYC, tax documentation and real solicitation. The restricted-source incident omits legal classification, personal-account dealing, information-barrier negotiations and regulator reporting. These are scope boundaries, not controls proven unnecessary in a real firm.

## 3. Company economics and manager incentives

Static annual reference, before changing AUM or costs:25m×1.5%=375,000 management revenue;52×20,000=1,040,000 overhead, leaving665,000. Covering that solely with a20% incentive fee would require3,325,000 of fee-eligible profit, or13.3% of initial AUM, **after the fee model's applicable common expenses/management charge**. This is a sensitivity calculation, not an expected return or target investors are guaranteed to receive. Crystallization timing can still leave the company without cash.

The initial300,000 buys15 baseline weeks. The82-calendar-date quarter has constant-base management accrual84,246.58 and240,000 business-week expenses, suggesting144,246.58 company cash after payment before flows, hiring, changing fee bases and other liabilities. This illustrates why the first quarter can look viable while the annual business is not. Actual simulation amounts must follow daily changing bases; the static example is not a season outcome.

The end report must show a13-week company forecast with contracted management receivables, committed expenses and an explicit no-performance-fee case. A four-week cash-runway milestone does not demonstrate financing for another12-week campaign. Continuing seasons need a new, disclosed company-capital/cost contract or must permit honest firm failure; do not reset seed cash at renewal. The launch avoids personal bonuses, owner withdrawals and cross-entity lending, keeping the conflict visible without implementing a compensation platform.

Three incentives deserve explicit debriefs: accepting AUM beyond strategy capacity, preserving fee income by gating, and taking more risk to approach an incentive fee. The game's success conditions prioritize contracted LP payments, mandate and solvency. Fees can be economically legitimate while these conflicts remain. A poor investment result with honest operations should differ from a high-return path that cannot pay investors.

## 4. Why the three cases are enough for the next design gate

Case1 combines portfolio conviction, borrow, margin and a near-term investor obligation. Case2 adds external redemption needs unrelated to performance and shows the equity-denominator/cash distinction. Case3 tests independent reconciliation, short-distribution economics, information restrictions, fund-versus-firm cash and operating capacity. They give both humans decisions without new instrument types or another backend engine.

The detailed cases and arithmetic live in SEASON_SCENARIOS and fixtures/scenario_cases.json. They intentionally distinguish frozen event inputs, player choices, checkpoint arithmetic and missing full-tape compilation. No branch is a proven viable playtest until the engine runs it. The next engineering task should compile the cases into one validated event/authority/accounting contract, then build the opening slice; it should not start a broad optimization or ML project.

## 5. Primary-source register and claim boundaries

All accessed 6 October 2026. These documents supply concepts or specific examples; none supplies the game's numerical terms, certifies its compliance, or establishes that its code exists. No legal recommendation is made. Exact titles/URLs are retained for future rechecking.

| Ref | Primary source and exact URL | Inspected claim / limit |
|---|---|---|
| S1 | SEC Office of Investor Education, *Hedge Funds* investor bulletin: https://www.sec.gov/files/ib_hedgefunds.pdf | Fees, withdrawal restrictions and incentive conflicts deserve attention. Investor education, not FundForge's offering contract. |
| S2 | ESMA, *Guidelines on performance fees in UCITS and certain types of AIFs*,5 November2020, especially scope and paragraphs15–20,31–36: https://www.esma.europa.eu/sites/default/files/library/esma34-39-992_guidelines_on_performance_fees_en.pdf | Distinguishes accrual/crystallization, symmetry, investor fairness and redemption proportions; annual-frequency guidance has explicit exceptions and a limited regulatory scope. Our annual/HWM convention is a design choice, not blanket legal compliance. |
| S3 | AIMA Investor Steering Committee, *A Guide to Institutional Investors' Views and Preferences Regarding Hedge Fund Operational Infrastructures*,2011, especially5.3.2.3 and5.4: https://www.aima.org/static/uploaded/7fe04dd4-1149-4415-a707a233374597b2.pdf | Institutional operational preferences include cross-party cash/position reconciliation, valuation controls and documented conflicts. Historical industry guidance, not a binding rule or evidence every fund follows it. |
| S4 | Financial Stability Board's official IOSCO standard entry,7 May2013: https://www.fsb.org/2013/05/cos_130507/ | Confirms IOSCO valuation-policy principles. Direct IOSCO PDF https://www.iosco.org/library/pubdocs/pdf/IOSCOPD413.pdf returned403 during inspection; no claim of reading the inaccessible text. Detailed reconciliation recommendation relies on accessible S3. |
| S5 | Interactive Brokers, *Short Sale Cost*: https://www.interactivebrokers.com/en/pricing/short-sale-cost.php | Its borrow/proceeds calculations refer to settled positions; this is provider-specific. Launch omits rebates and uses its own collateral/rates. |
| S6 | IBKR Guides, *Non-Direct Hard to Borrow Details*: https://www.ibkrguides.com/reportingreference/reportguide/borrowfeedetails.htm | Documents Value×Fee Rate/360 for that report. Does not establish a universal management-fee or market calendar convention. |
| S7 | SEC, *Investment Adviser Codes of Ethics*,2 July2004: https://www.sec.gov/rules-regulations/2004/07/investment-adviser-codes-ethics | Addresses safeguarding sensitive information and policies against misuse. The launch restricted-status machine is a limited teaching abstraction, not legal determination of MNPI or a real compliance program. |
| S8 | CFA Institute, *GIPS Standards Handbook for Firms*: https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/ | Supports separating external cash flows from time-weighted investment performance. The game makes no GIPS compliance claim and does not equate benchmark excess with alpha. |
| S9 | FINRA, *Know What Triggers a Margin Call*: https://www.finra.org/investors/insights/margin-calls | Firms can impose house requirements and increase them without advance written notice. Our coefficients and fair-play warning/deadline are fictional broker terms, not Reg T/portfolio-margin replication. |
| S10 | SEC Investor.gov, *New T+1 Settlement Cycle—What Investors Need To Know*,27 March2024: https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor-bulletin | Applicable US transactions moved to T+1 from28 May2024; exceptions/market scope matter. Synthetic Mon–Fri calendar is not an actual exchange calendar. |
| S11 | SEC, *Key Points About Regulation SHO*: https://www.sec.gov/investor/pubs/regsho.htm | Locate/close-out are distinct concepts. Page includes outdated T+2 explanatory text; use S10 for modern settlement context. The game does not simulate all SHO requirements or claim real compliance. |

No contemporary performance-fee proposal was treated as enacted law. Source freshness and scope matter even on an official website: old settlement language and limited-scope guidance must not be generalized.

## 6. Actual review state and open gates

The owned v2.1 specifications and numerical fixture have been updated. Executed an independent scratch Decimal/calendar check with 38 assertions over cohort fees, partial redemption, leverage, cover direction, calendar costs, corporate-action correction, scenario fills/gates, continuation bounds, company cash and calendar counts; all passed. This checks document arithmetic only. The parent task records packaging/reference checks separately. This review did not build a backend, connect a broker/admin, run two-user playtests, measure strategy balance, obtain a market-data license, or validate investment alpha. The new independent records remain authored fixture requirements.

Open gates are intentionally narrow: implement the dated event/series contract, compile complete immutable scenario tapes, prove safe authority/settlement/replay behavior, and playtest role balance. Preserve the source-backed fixes before adding optional research providers or optimizing portfolio weights. Any future change to fees, calendar, flow ordering, scenario outcome or closing checkpoint changes the rule/scenario version and its regression oracles.


---

Source: `docs/MASTER_SPEC.md`

# FundForge — hedge fund management game

Version 2.2 · Bounded plan strengthening · 7 October 2026 · Specification, not implemented software

Planning revision 2.2-M1 adds full task-level packages for every phase through FF8 in [MILESTONE_PLANS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\MILESTONE_PLANS.md), indexed by IMPLEMENTATION_PLAN. [PLAN_REVIEW_AND_DECISIONS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\PLAN_REVIEW_AND_DECISIONS.md) records due decisions and corrections. Release boundaries unchanged: internal prototype FF3b, first playable FF5c, full initial game FF6c, optional research FF7 and selected-extension planning FF8. No feature implementation is claimed.

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

Full rules live in [GAME_SYSTEMS.md](https://github.com/krishbansalofficial/fundforge/blob/main/docs\GAME_SYSTEMS.md), [FUND_ACCOUNTING.md](https://github.com/krishbansalofficial/fundforge/blob/main/docs\FUND_ACCOUNTING.md) and [SEASON_SCENARIOS.md](https://github.com/krishbansalofficial/fundforge/blob/main/docs\SEASON_SCENARIOS.md). Those contracts take precedence over old tutorial defaults. The legacy $100k accounting fixture remains a deliberately isolated arithmetic exercise.

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

[REALISM_AUDIT.md](https://github.com/krishbansalofficial/fundforge/blob/main/docs\REALISM_AUDIT.md) records the source-backed review across portfolio management, risk, operations, accounting, research and game design. Real concepts, specific counterparty terms and deliberate game rules are labeled separately. The first release remains one fund, one broker, one currency and twelve instruments; it does not need derivatives, a complete compliance department or a large optimizer to feel like a fund.

Required small additions fix material errors: calendar accrual, annual/redemption fee timing, fair fee-series participation, post-redemption risk, signed hedge direction, one independent reconciliation exception, simple dividends/splits and a deterministic restricted-instrument state. The Managing Partner resolves funding/reporting/capital decisions; the Investment Partner resolves sizing, hedging and liquidation choices. Neither partner acts as a fictional independent administrator. Admin/broker NPCs are authored control records with separate responsibilities.

Chapter windows are compressed for play: five-business-day redemption notice, one-day payment and publicly specified broker response windows are fictional contracts. Real investors and prime brokers can have very different rights. Daily company payroll allocation and strategic-assignment budgets are house rules. The exact latent relationship score is a balance device, shown primarily as observable concerns and a relationship band.

The ending is an ordinary checkpoint after day61 opening administration, including weekend accruals and due day60 settlements. Residual investments are marked holdings with aged quotes, not liquidated cash. There is no special frozen-price terminal day. Winddown continues actual engine events. The scored 60-business-day investment result and the subsequent cash/claims bridge remain separate.

Use the updated accounting and scenario cases before implementation. Optional research libraries and architecture choices are owned by their dedicated assessment documents; no dependency should replace the authoritative economic event/ledger contract.

Renewal is displayed as **Renewal — conditional continuation**, with remaining company cash runway, a13-week forecast and any unfunded next-season gap. It is not a claim of durable business viability or a guarantee that another12-week campaign is financed. Preserve cash, liabilities and fee history into continuation; no automatic company recapitalization.

Canonical software boundary: [SIMULATION_ARCHITECTURE](https://github.com/krishbansalofficial/fundforge/blob/main/docs\SIMULATION_ARCHITECTURE.md). Dependency evidence: [LIBRARY_RESEARCH](https://github.com/krishbansalofficial/fundforge/blob/main/docs\LIBRARY_RESEARCH.md). Detailed player decision contracts are in GAME_SYSTEMS section11; the acceptance/implementation documents define pending evidence gates.


---

Source: `docs/GAME_SYSTEMS.md`

# Game systems and balance contract

Version 2.1 · Proposed, unimplemented defaults · Read with MASTER_SPEC and FUND_ACCOUNTING.

## 1. Time, attention and cooperation

v2.2 clarification (7 October 2026): SCENARIO_CONTRACTS specifies bounded challenge overrides; the base campaign retains rules below. IMPLEMENTATION_PLAN is now split into small milestones. The old isolated checkpoint fixtures remain arithmetic references, not complete tapes.

A season has six chapters, each ten simulated business days. Planned windows occur before days 1/6, 11/16, 21/26, 31/36, 41/46 and 51/56, plus each chapter close. A close can also serve as the next opening committee without repeating the recap. Material margin, recall, redemption or solvency events insert a decision window before their deadline. A pause changes real waiting time, never which historical information is visible.

Each partner has two strategic assignments per chapter, four for the team. Researching a thesis, conducting LP due diligence, negotiating a contractual offer or preparing a contingency each costs one assignment. Reviewing data already obtained, discussing, placing authorized orders, responding to a mandatory notice, and reading reports are free. Unused assignments expire; no speed bonus. Emergency remediation must remain possible after attention is spent.

Role ownership focuses the default task list; it is not an information barrier. Research assignments can be owned by either partner. The Investment Partner starts with portfolio/research responsibilities; the Managing Partner starts with investors/treasury. Each must have a valuable action while the other works. The first usability test should identify idle approval waiting and remove it.

The system does routine administration automatically and exposes exceptions. Players do not click to reconcile every day or type arbitrary reports for points. They decide which risk to take, what to disclose in an LP conversation, and what to fund.

## 2. Strategy sleeves and decision authority

A sleeve contains a named owner, approved instrument set, permitted sides, max gross allocation, max order size, chapter turnover budget, thesis/invalidation evidence, fallback action, review date and expiry. Default three available slots; two active sleeves in the opening scenario. Approved maximum sleeve budgets plus a central cash/hedge reserve cannot exceed the fund's permitted risk allocation.

Orders require a valid delegation OR an immutable order-specific second signature. A delegation is itself jointly approved. The owner is acting under prior authority, not self-approving a fresh committee proposal. A non-owner needs a fresh order approval or a changed sleeve owner. No human can grant authority to themselves.

Pending orders reserve sleeve capacity, borrow and settlement resources. Fill consumes the actual executed notional; cancellation releases the remaining commitment. Turnover means the sum of absolute fill notionals, including sales and covers, not net position change. Emergency system buy-ins are reported separately and do not block remediation because an elective turnover allowance is exhausted.

Counters are new versions. Version/content hash, actor and mandate/sleeve versions are displayed together. Approving a new version cannot revive a canceled or expired earlier order.

The emergency reduction policy is agreed at season launch. A due contractual payment or forced counterparty action is never blocked solely to keep a presentation ratio inside a limit; its consequences can create a remediation state. Either partner can submit a reduction plan that demonstrably reduces at least one active deficit and does not worsen another hard deficit; it may close positions and cancel risk-adding orders. System liquidation uses a separately declared deterministic priority. Opening a new hedge is not automatically “reducing risk”: its liquidity, gross exposure and margin effects must pass.

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

LP confidence is a deterministic internal 0–100 balance state. The normal UI shows observable concerns, contractual intentions and four bands: strong (70≤C≤100), stable (55≤C<70), concerned (40≤C<55), withdrawal risk (0≤C<40). Confidence uses Decimal values; these half-open boundaries include fractional values without gaps. The rulebook/replay can expose exact values and component changes for audit. It is not a measured probability or a claim that an actual LP's mind is observable. Notice thresholds remain predictable from the displayed band; no LLM awards the state.

| Investor | Initial capital/confidence | Preference | Initial restriction |
|---|---|---|---|
| Seed LP | $10m / 72 | Consistent broad long/short process, access to partners | No day-20 redemption; a known external $3m need on day 40 |
| Patient LP | $8m / 80 | Lower drawdown, reliable liquidity planning | First redemption dealing day 60 |
| Tactical LP | $7m / 65 | Higher net performance, fast response to deteriorating thesis | Eligible all windows |

At each chapter close, compute confidence deterministically:
1. Performance delta = clip(2 × (LP chapter net return in percentage points − target), −6, +6). Targets: Seed 0.35, Patient 0.20, Tactical 0.60 percentage points.
2. An avoidable active mandate breach or an uncured passive breach after the published remediation opportunity costs 6. A mere market-driven breach before an opportunity to act costs zero.
3. A certified report delivered by the chapter close earns 1; a missing/unreconciled report earns no bonus and costs 5. The engine generates reports automatically; certification depends on actual reconciliation.
4. A relevant LP meeting can recover at most 3 confidence once per chapter after a documented concern, never above confidence immediately before that concern, and only when it delivers new verified information or a fulfilled corrective commitment. The engine records the evidence/commitment identity; repeated promises or generic meeting spam do nothing.
5. A gate that actually defers eligible units costs Seed 10, Patient 8, Tactical 15 once per dealing window. An elected gate with no deferral has no gate penalty; record the election without pretending the LP lost access. An overdue contracted payment costs 15 once per incident.
6. Clamp final confidence to 0–100. Store every component and its policy version.

Those are balance hypotheses, not investor-behavior claims. They are frozen before a scored season and tested across scenarios.

At notice cutoffs days 15/35/55, eligible LPs with confidence below 40 request 50% of their then-held units; confidence40≤C<55 requests25%; C≥55 causes no performance-driven request. Locked LPs wait for their first eligible cutoff. Requests are unit quantities, so their final dollar value is unknown until dealing. The Seed's external $3m need is expressed as a dollar-target request capped by its units; final units are calculated at dealing. If it also has a confidence request, use the larger request, not both.

The external need is disclosed before investment choices can reasonably fund it. Confidence cannot make an investor's external obligation disappear. In the launch First Mandate scenario, Tactical also has an externally required 10,000-unit day-20 redemption, disclosed on day1 with formal notice on day15. Use the larger of this and its confidence-based request, not their sum. This guarantees a genuine capital-flow decision in the opening slice without manipulating performance.

### Fundraising pipeline

Prospect → qualified → diligence → conditional commitment → eligible subscription → admitted. Two scarce assignments complete qualification and diligence; an IR hire can expand the number of simultaneous prospects. Offers specify amount, mandate fit, fee terms, earliest dealing date and conditions. Launch supports standard-fee offers only; custom side letters and heterogeneous fee schedules are later.

A signed fictional commitment is not NAV, settled cash or margin collateral. Subscriptions enter on a dealing date only after funding is available and conditions pass. The team may reject or cap an offer when the strategy lacks capacity. A prospect's terms can demand lower leverage or a capital lock; accepting a conflicting mandate requires a new scenario contract, not a silent settings edit.

### Gates and fairness

Both partners must elect a permitted gate before the dealing event. Maximum dealt redemption amount is 20% of pre-flow, post-fee NAV for the whole fund at that window. Allocate pro-rata across eligible requests, including carried requests; no preferential payment to a favorite LP. The undealt portion retains units, stays exposed, and rolls to the next window. The gate cannot erase notices, forgive already-created payables or freeze capital forever without consequence.

Day 60 deferred requests carry into the debrief and reduce the renewal outcome. A season cannot win by deferring its obligations past the final screenshot.

## 5. Management-company economy

Opening company cash is $300,000. Baseline overhead/payroll is $20,000 per five-day week, accrued $4,000 each simulated day and payable at each fifth-day close. It earns cash only when contractual fund fees are paid. Management fees accrue on calendar dates and pay after each dealing window; performance provisions generally stay uncrystallized until 31 December, with only accepted redeemed units crystallizing earlier. The 60-business-day season cannot accelerate incentive income to rescue payroll. Accrued fee receivables are assets, not spendable payroll cash.

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

Launch broker contract: borrowing limit $7.5m fixed at season start; annual debit interest 6%; ordinary borrow fee 2%; restricted short collateral 100% of marked short value. Borrow/debit rates accrue ACT/360 on actual calendar dates, including weekends, against settled borrowed shares/debt under FUND_ACCOUNTING. Management fees use a separate ACT/365 convention. A broker shock can change future rates or coefficients on an announced effective event; it cannot retroactively charge a revised rate.

Initial margin requirement = 50% of long marked value +60% of absolute short marked value. Maintenance =35% of long value +40% of absolute short value. Margin equity is fund NAV minus any explicitly ineligible receivables; launch treats ordinary valid T+1 trade receivables as eligible and unreceived subscriptions as absent. Fund liabilities already deducted in NAV must not be deducted again.

These are deliberately simplified fictional prime-broker terms, not Reg T or portfolio-margin compliance. They require two independent tests: adequate margin equity and enough usable settlement cash/credit. A margin pass cannot spend restricted short collateral on payroll or redemptions.

Short orders need a valid locate reservation and available capacity at fill. A locate is not a promise of perpetual borrow. Borrow rates/availability are time-stamped; recalls create quantities and deadlines. The authored launch recall allows two business days to find replacement borrow or execute a cover, then forces a buy-in at the deadline's first executable event. This is a cover-execution deadline; borrowed shares return at the resulting T+1 settlement and fees continue until return. This is a game contract, not a claim about every broker.

Liquidation time shows how many future tape events at the participation cap would be needed to exit, with stressed volume sensitivity. Spread and adverse impact grow as liquidity deteriorates. The launch reference tape is exogenous; player fills consume available event liquidity across their orders, preventing ticket splitting from obtaining unlimited volume.

Fund capacity has a cost: a large inflow can make the same strategy harder to execute. The player can hold capital temporarily, expand a liquid sleeve or decline it.

## 7. Risk and mandate state

Gross exposure = (long MV + absolute short MV)/NAV. Net = (long MV − absolute short MV)/NAV. Direct sector gross sums absolute direct-equity positions in that sector. ETFs appear separately unless point-in-time constituent exposure is explicitly provided. Cash is not another equity sector.

The default single-equity issuer caps are15% long and8% short; direct sector35%; each approved diversified ETF has a50% absolute exposure cap in either direction instead of the single-equity issuer cap. ETF positions still count in fund gross/net, factor, liquidity and financing tests. Gross150%; net between−20% and100%. Apply all reservations, obligations and borrow commitments. A reduction exception requires improvement in an active deficit and no new or worsened hard deficit after fees/costs and reserved obligations. Test signed net exposure, gross, issuer, sector, margin, borrow and cash separately. Closing a short raises net exposure; selling a long hedge can increase factor risk even as gross falls. Check each executable prefix of a multi-leg plan; do not grant imaginary atomic basket execution. Mandatory broker buy-ins can unavoidably create a new mandate deficit; record that passive consequence and remedy it without calling the forced fill invalid.

Drawdown is measured on the net flow-neutral fund wealth index: warning at10%, freeze new risk at15%. Recovering above the threshold clears the automatic drawdown freeze only after a reconciled close; unresolved other breaches remain active.

A concentration breach from price movement gives the team the next available decision window to present a plan and up to two simulated days to execute an achievable reduction. A halt or lack of liquidity is recorded as inability, not fictitious compliance. Broker solvency/deadline rules still apply.

Known redemption notices trigger a pre-flow and post-flow risk preview. A $5m redemption from a $25m book with $27.5m longs/$5m shorts raises gross130%→162.5% and net90%→112.5% at unchanged marks; paying the resulting liability does not cause a second increase.

A visible risk card distinguishes: hard contract; internal policy; estimated stress loss; stale/uncertain data. Authored factor exposures use signed quantities: market sensitivity = sum(position MV signed × authored beta)/NAV. Show market-up/down and sector shocks, a rates-up bond-ETF shock and a liquidity/borrow shock. These scenarios are not statistical VaR; no covariance optimizer or estimated beta is required at launch. An estimate can guide a decision but is not a guarantee against ruin.

## 8. Crisis state machine

NORMAL → WATCH → ACTION_REQUIRED → REMEDIATING → CURED, CONTROLLED_WINDDOWN or DEFAULT.

Each incident has an objective trigger, affected obligation, created-at/effective-at times, absolute simulation deadline, permitted remedies, escalation rule and causal links. Display the deadline in business events, not only a real-time countdown.

Maintenance margin shortfall is detected after each price event. Freeze risk additions immediately; cancel unfilled risk-adding orders. Pause for a player response before the next executable event. If a valid voluntary reduction cannot cure at that next event, forced liquidation begins there. No second arbitrary “grace day” is invented. Forced liquidation must obey actual modeled liquidity and can continue across events; insolvency can occur despite liquidations.

Priority: recall buy-ins whose deadline has arrived; then margin deficit remediation by highest estimated margin release per executable dollar cost; deterministic instrument ID breaks ties. The engine recomputes after every partial fill. A future order preview cannot guarantee a forced sale will fit the tape.

Debt-line reductions are separate from maintenance margin. An announced reduction creates a contractual repayment deadline. If the next settlement sweep cannot pay an obligation within credit/collateral rules, pause in treasury distress; deadline-specific cure rules control whether the team can continue. An overdue redemption does not magically become extra broker credit.

Insolvent fund NAV<=0 stops new risk; preserve the deficit and winddown ledger rather than displaying a negative “unit price” as a normal active fund. Other insolvency/default outcomes preserve unpaid obligations for the report. Game over does not delete liabilities.

## 9. Renewal, score and progression

The default season earns renewal only if all are true at the certified day60 close and ordinary day61 opening administration checkpoint:
- Fund NAV remains positive, no broker default, no overdue dealt redemption and no unresolved ledger discrepancy.
- Net time-weighted return is at least the scenario cash benchmark over the same 60 days.
- Maximum net-index drawdown is less than12%.
- Seed confidence is at least60.
- Company cash runway is at least four weeks, after all due costs and paid fees.
- No redemption remains deferred by a gate at the season endpoint.

This is a demanding selected contract, not a universal definition of a successful hedge fund. Scenarios may publish different goals before play. The day61 checkpoint includes actual intervening weekend accruals and due settlements, before that Monday's market event. Last observed marks retain their timestamps. It is neither a fresh Monday NAV nor a completed winddown; FUND_ACCOUNTING specifies the bridge and continuation. Annual fee/HWM history carries across renewal.

Awards describe outcomes: Renewal; Survival Without Renewal; Responsible Winddown; Broker Default; Company Failure. A narrower recovery objective can recognize good crisis management without relabeling a failed investment mandate as a win.

For private comparisons, rank first by outcome tier, then by net return among teams meeting that tier's published objectives, then by lower drawdown, then a stable ID. Seed/scenario/rule versions must match. Do not compare three deliberately different challenge cases on a common return leaderboard. Report investor capital returned and company cash alongside the ranking. Do not combine fund AUM and company fee income into “profit,” count subscriptions as returns, or award points for turnover, leverage, prose length or an LLM's opinion.

Campaign unlocks new scenario packs and strategy mandates, not additive market advantages. No strategy has a forced role in every scenario. Balancing must include passive cash, benchmark buy-and-hold, a diversified long/short ruleset, a concentrated gambler and gate/fee exploit attempts on the same tape.

Before release, measure whether each partner makes consequential decisions, whether feasible plans can win across authored scenarios, and whether at least two different strategies can survive each teaching scenario. Those are tests to run, not results already obtained.

## 10. Information restrictions, operations and economic incentives

Research provenance can affect tradability. A scripted, explicitly flagged restricted-source event places affected instruments in RESTRICTED status until an authored public-release or compliance-clearance event. New elective trades in either direction and resting elective orders are blocked/canceled; both partners can escalate and use untainted public information on unrelated instruments. Players and LLMs cannot self-clear a restriction or relabel the same private fact as public. Mandatory broker disposition follows its separate incident contract, not an elective insider-information exception. This narrowly teaches information handling; it is not a simulation or assurance of legal compliance. Personal trading, wall-crossing negotiations and jurisdictional advice are excluded.

Independent broker/admin controls can flag a missing dividend liability, duplicate trade or stale mark. Players choose how to investigate, disclose and fund the consequence; they cannot select a favorable accounting number. Routine controls are automatic and do not consume assignments. A hire can provide an earlier warning/additional contingency capacity, never buy truthful accounting or waive a break. Correcting an honest error is preferable to concealing it, but the true cash loss and contractual deadlines still apply.

The firm has a genuine incentive conflict: more AUM can increase management fees, more risky upside can increase incentive fees, and a gate can preserve the fee base. Outcomes privilege LP obligations and mandate fidelity over fee extraction. Disclose separate investor net results, provisioned/fixed/paid manager fees, company runway, redemption fairness and style changes. Selecting a low-risk cash book may yield a responsible survival result but misses the launch net-return goal after management fees, since the matched zero-yield cash benchmark does not pay the manager's fees. Never invent guaranteed alpha so that hiring pays for itself.

The short quarter does not validate an investment business over a full drawdown/recovery cycle. Renewal is a scenario milestone, not evidence of enduring skill. Debriefs distinguish accounting P&L attribution, the team's ex-ante decision rationale, and a paired replay under the same exogenous tape. A replay can show the mechanical consequence of a changed command in this model; it does not identify real-world causal alpha or allow altered future evidence.

Renewal is displayed as **Renewal — conditional continuation**, with remaining company cash runway, a 13-week forecast and any unfunded next-season gap. It is not a claim of durable business viability or a guarantee that another12-week campaign is financed. Preserve cash, liabilities and fee history into continuation; no automatic company recapitalization.

The launch has one pooled investor fund: sleeve tags attribute approved decisions and turnover, not separate legal accounts or independently selectable LP trade allocations. Every executed fund position participates through the accounting allocation contract; players cannot assign a losing fill to one LP or a profitable fill to the company. Baseline company overhead bundles fictional administrator, legal, audit and compliance support; the fund pays only the explicitly enumerated investment/financing/management/performance costs. This is a house expense policy, not a claim that real funds universally allocate these costs to the manager.

## 11. Decision contracts: turn financial detail into play

These summarize existing rules; they do not introduce extra currencies or approval steps. Routine bookkeeping, accrual, screening and reporting run automatically. A player decision is warranted when there is a choice with a material consequence.

**Mandate and portfolio construction.** Players see the investable universe, signed exposures, thesis horizon and approved capacity. The Investment Partner proposes a sleeve/size/hedge; the Managing Partner challenges cash, borrow and LP compatibility. The joint charter commits authority immediately and constrains later orders. Success is an investable portfolio consistent with its promise; a rejected proposal costs no arbitrary points. Recovery is a smaller or revised allocation supported by new evidence, not a signature that waives hard limits.

**Research and thesis review.** Both see dated public facts, competing explanations and unresolved questions. The Investment Partner chooses which thesis uncertainty to investigate; the Managing Partner may spend an assignment on liquidity, a counterparty or investor diligence. Limited assignments force selection. Evidence arrives at its authored time and may justify holding, resizing or waiting. Success means a defensible decision under uncertainty, not guessing the future outcome. Contradictory evidence allows thesis revision; a lost trade is not automatically a failed research process.

**Hedging and stress.** Players see factor direction, stress losses, liquidity assumptions and margin headroom. The Investment Partner selects hedge exposure; the Managing Partner evaluates financing and payment consequences. A hedge consumes gross exposure, borrow or cash immediately and changes later stress response. Success reduces the intended vulnerability without creating an unaffordable obligation. Failure can be a basis/direction or cash mismatch; recovery uses a feasible sequence of reductions, not an imaginary simultaneous basket.

**Execution and settlement.** Players see order authority, next-event eligibility, cost/capacity estimates and the cash ladder. The Investment Partner chooses quantity, price protection and timing; the Managing Partner reserves resources for settlement and LPs. A fill changes economic exposure now; cash/borrow settle later, partials retain only remaining reservations. Success executes an affordable plan at accepted costs. A gap, halt or partial fill requires cancel/reprice/reduce/wait, with the resulting deadline risk visible. Every fill belongs to the pooled fund; sleeves are attribution tags, not discretionary allocation among investors.

**Borrow and financing.** Players see inventory, rate notices, collateral, deadlines and separate initial/maintenance tests. The Investment Partner decides which conviction to sacrifice; the Managing Partner chooses an available replacement/funding response and tests payment sufficiency. Reservations and replacement terms constrain the immediate plan; daily carry, recalls and broker remedies arrive later. Success funds obligations and preserves deliberate risk. A forced buy-in or liquidation may salvage survival while losing the voluntary-control objective; an uncured deficit remains visible.

**Investor dealing and fundraising.** Both see investor terms, notice dates, external cash needs, offer conditions and projected post-flow leverage. The Managing Partner proposes gate/admission/payment planning; the Investment Partner identifies capacity and sales required. Joint decisions cannot erase contractual rights. Dealing fixes claims and changes equity now; payment and reduced fee revenue follow later. Success honors accepted obligations and appropriate capacity. Recovery may use a permitted pre-dealing gate, earlier sale or honest winddown; a late gate cannot undo a payable and a commitment is not cash.

**NAV and operational exceptions.** Both receive a reconciled summary or an actionable broker/admin discrepancy, with the disputed evidence and deadline. The Managing Partner leads investigation/disclosure; the Investment Partner explains position/corporate-action effects and re-plans exposure. Truth is fixed by evidence, not a player's choice. Correction changes NAV/fees and preserves the old report immediately; LP decisions and payable dates follow. Success restores certified reporting and funds real claims. Concealment cannot produce a certified NAV; correction can recover operations without recovering a missed offer.

**Fees, staffing and firm survival.** Players see provisioned, fixed and paid fees separately, plus cash runway and a 13-week forecast. The Managing Partner proposes staffing/cost decisions; the Investment Partner judges the research capacity sacrificed or gained. Both approve a hire. Recruiting cash leaves now, capacity/salary start at the declared boundary, and fund fees pay only when due and fundable. Success is funded operations, not larger AUM alone. Recovery uses collectible earned fees or allowed cost cuts; there is no investor-cash bailout. Baseline company overhead bundles fictional administration/legal/audit/compliance support under the chosen expense policy.

**Restrictions and conflicts.** Players see the affected instrument, source flag, blocked actions and dated clearance rule. The Investment Partner can redirect to public/unrelated research; the Managing Partner handles the incident and reporting consequences. Both remain constrained by restricted status, regardless of signatures. Orders are canceled/blocked immediately; market opportunity and investor diligence evolve later. Success respects the control while continuing permissible work. Clearance comes from a recorded event; neither partner nor an LLM can remove the flag by assertion.

**Chapter review, recovery and continuation.** Both see an event-linked return/cost/claims bridge and the next obligations. The Investment Partner revises thesis/risk; the Managing Partner revises liquidity, LP and company plans. Remaining resources and obligations carry forward. Success is the published scenario outcome with honest outstanding claims; a conditional Renewal is not a financed next quarter. Responsible winddown and survival after a mistake remain meaningful results. Paired replay teaches model-conditional alternatives without changing the ranked attempt or implying real-world alpha.

## 12. Concrete operating actions and session contract v2.2

Both partners see the same brief, deadlines, cash ladder, constraints and evidence available at the current barrier. At opening the PM chooses a thesis/sizing/research alternative; the Managing Partner chooses contingency/borrow terms and a binding treasury reserve. At reassessment they independently execute within charters, update feasible plans and propose only material exceptions jointly. Each marks ready against the same state/plan digest; a changed material plan clears readiness. Advance resolves deterministic events and auto-admin until next authored barrier/material incident. Response offers alternative sacrifices with cost/cash/deadline previews, then advance resolves later fills. Close explains real results and remaining obligations. No sixty-day checklist. Opening-arc target40–60minutes and challenge target20–30minutes are unmeasured design hypotheses.

| Command / authority | Available information / alternatives | Immediate effect / delayed consequence | Success, failure, recovery / automation |
|---|---|---|---|
| TreasuryReserve: operating partner may raise within joint policy; jointly approve lowering below known signed obligations | Settled cash/credit, dated claims, conditional sales; reserve payment capacity versus finance more exposure | Earmark current resources/credit against named dated obligations; reserve is not NAV liability or cash receipt. Elective orders cannot consume it; mandatory payments consume it | Obligations fundable; opportunity cost lower investable capital. Insufficient current resources produces a conditional forecast, not fictional reserved cash. Revise exposures/borrow jointly; sweeps automatic |
| SelectReplacementBorrow: operating partner independently inside pre-approved rate/quantity ceiling | Time-stamped offer/transfer/cutoff and recall; replace versus cover/allow buy-in | Reserves offered inventory now, actual transferred loan cancels recall later and switches carry rate | Transfer by deadline succeeds; expired offer rejected; locate alone fails. PM chooses cover exposure; operating partner compares cost/cash. Borrow accrual automated |
| AssignResearch/Contingency: either owns assigned task | Public evidence/release times, reliability, remaining assignments; thesis versus counterparty versus wait | Consumes1 assignment once; authored reveal arrives later, not guaranteed return | Useful uncertainty reduction without future price. Spent attention cannot block free mandatory response; use public evidence/hold. No meeting spam or report clicks |
| Capital/report choices: operating partner proposes; admission/gate jointly signed | True certified NAV, unit/dollar requests, diligence/funding, post-flow capacity; pay/gate/decline/cap | Gate only before dealing; optional admission only after funding/certification; routine true report auto-generated | Investor obligations honored/deferrals visible, fee base changes later. Correct a real break, cannot choose a NAV or spend new fund capital on company payroll |

Risk reservations use the earliest due obligation first, with explicit resource/economic IDs and expiration. Reserve total cannot exceed currently allocable cash+permitted free credit after collateral and higher-priority claims; show a shortfall as forecast. Do not double reserve the same signed payable and its tagged treasury earmark. Reservations survive save/load and release only on cancellation/reallocation/settlement; claim payment outranks discretionary debt sweep. No command can create liquidity by promising a future sale.

The two-role test must log actions and subsequent feasible-set changes, not just click counts. Opening window: operating partner's attention on replacement inventory competes with thesis evidence; crisis: its reserve can prevent a new order spending payment cash; PM chooses which exposure/return potential to sacrifice. Routine report generation/free controls are automated. A hire in the full campaign must buy a specified future task opportunity; Case3's currently dominated hire is only a teaching forecast. Failure remains understandable: explain missed event, resource or constraint and a feasible recovery/controlled winddown under FUND_ACCOUNTING §10.


---

Source: `docs/SEASON_SCENARIOS.md`

# Season scenarios and playable arc

Version 2.1 · Authored design, not a complete playable tape or measured balance result.

v2.2 authority: [SCENARIO_CONTRACTS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\SCENARIO_CONTRACTS.md) supplies complete bounded authoring schedules and supersedes conflicting challenge text below. These designs still have no compiled tape, full dated numerical path oracle or simulator. The ordinary day1–21 opening campaign remains separately to be authored. The old checkpoint values deliberately hold additional daily charges fixed.

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
- Tactical LP notice evaluation plus an externally required 10,000-unit day-20 redemption, disclosed on day1 and formally noticed on day15; use the larger of it and a confidence-based request, not both. First dealing/gate choice, pro-rata redemption crystallization and ordinary payment checkpoint are real consequences even on a profitable path.
- A reconciled chapter report separating market P&L, borrow/debt cost, LP flows, fees and company cash.
- Save/resume, identity isolation and a missing-partner pause.

The opening-arc acceptance run includes day21's opening administrative payment checkpoint so the day20 redemption and fees actually settle. It stops before day21 market events; the full campaign continues into those events normally. Both this and day61 use the ordinary calendar/administration path, including intervening weekend accrual. Neither freezes a future market or pretends that remaining holdings are cash.

The slice may use four tradable instruments and one frozen event branch. Its end state is “opening arc completed,” not the full season's Renewal outcome. Three LPs still exist; locked LPs help explain why not every investor can demand money today. Fundraising and staffing can appear as a chapter3 preview until the full-season gate, but fund fees, firm runway, financing and LP obligations cannot be omitted.

### Opening opportunities

1. **Quality versus fragile competitor.** Long ALTO (industrial quality), short BRIN (industrial over-expansion). Shared sector exposure offsets some thesis risk while the short adds borrow and squeeze risk.
2. **Liquid hedge.** A **short** broad-equity ETF sleeve reduces positive market exposure but requires borrow/collateral and loses on a rally. Buying the broad ETF increases market exposure. The bond ETF offers a different rate-sensitive exposure, not a guaranteed equity hedge.
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

A separate Tactical redemption may join the queue if confidence crossed a threshold. The 20% gate limit is applied to all eligible requests on day40's pre-flow post-fee NAV, pro-rata. If total requests are below the cap, electing the gate does not reduce payment; it still records the election and purpose, but no deferral means no gate confidence penalty. UI should discourage needless activation without silently changing contract mechanics.

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

Produce an evidence-linked timeline with mechanical explanations: evidence available → signed authority → fill/slippage → position/financing → event → cash need → response → LP/firm outcome.

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

fixtures/season_scenario.json records canonical configuration, actors, chapter beats, a stress reference and future-event contracts. fixtures/scenario_cases.json records the three cases below and arithmetic oracles. They are authored specifications; neither is a generated full market tape. It intentionally does not contain a complete market tape, all daily prices, a production schema, a simulator or achieved results.

Before calling the slice playable, developers must add a validated event-tape schema; generate/freeze all twenty days; give every instrument coherent mark/volume/borrow data; define every signal's available-at time; implement commands/LP transitions; and replay the complete slice with two real user identities. A fixture syntax check alone establishes none of those behaviors.

Validation must demonstrate at least one feasible solvent path and one explainable failure path, preferably two strategically distinct successful opening paths. That requirement is not permission to change the tape after watching a specific player. Balance adjustments create a new scenario version.

Future historical packs need independently licensed/available datasets and era-appropriate settlement, marks and information timing. A title such as “2008” does not imply such a dataset has been obtained.

## 8. Three detailed decision cases

These are **proposed playable case designs**, not implemented games or observed outcomes. Each can be a 20–30-minute warm-start challenge using the same two-player engine; Case1 also informs the low-exposure opening arc. Their seeded portfolios are explicit starting states, not positions magically built under the opening two sleeves' small turnover budgets. Do not require a high-leverage margin call in the opening campaign: a smaller book still faces a real borrow recall and investor cash need. A challenge's fixed objectives replace the full-season Renewal test and are published at start.

The numerical branches below isolate the decisive event and hold other daily accruals fixed; exact full-date fee/carry amounts remain governed by FUND_ACCOUNTING and must be added when compiling the complete tape. This prevents a rounded educational calculation from masquerading as an implemented full-season balance. Costs use the same execution formula with displayed reference/volume; no option applies a magic cash adjustment. All future quotes and outcomes stay server-side. `scenario_cases.json` supplies expected calculation values and the remaining implementation gate.

### Case1 — The borrow is not the thesis

**Situation and goal.** Day12, the partners inherit a valid $25m long/short fund with $27.5m longs and $5m shorts. Company cash $240,000, weekly overhead $20,000; the firm can survive the episode without incentive income. The goal through day21 opening is to resolve the known borrow obligation, meet the Tactical payment, maintain positive NAV, and avoid involuntary broker liquidation. A lower-return voluntary deleveraging path can succeed. No annual performance fee date occurs.

**Opening balance sheet, costs already included:** long assets $27.5m, restricted cash $5m, economic shorts $5m, broker debt $2.5m, unrestricted cash zero; NAV $25m. Gross130%, net90%, ordinary initial requirement $16.75m. Six equity longs: ALTO/COVE/ELAN/GALA/IONA $3m each, JUNO $2.5m; BEAM broad ETF long $10m. BRIN/DART/FENN/HELI shorts $1.25m each. Paired sectors are ALTO/BRIN industrial, COVE/DART consumer, ELAN/FENN technology, GALA/HELI health, IONA/JUNO finance. All opening marks100, whole-share quantities follow from notional/100. No issuer, sector or ETF cap is breached.

**Information available at day12 opening.** BRIN's financing weakens but its near-term customer survey remains positive. Harbor Prime announces stressed coefficients effective day16: initial80% long/100% short, maintenance70%/90%. The players know the rule change and must forecast it; they do not know the day16 prices. Tactical's already-disclosed10,000-unit redemption will price day20 and pay day21. LP withdrawal dollars are not yet fixed. Research reveals either a dated public debt maturity schedule or a noisy customer survey; neither predicts the squeeze with certainty. One contingency assignment reveals a replacement borrow offer at40% annual, available for the recalled quantity only; acceptance cutoff day14 before EXEC_B, settled transfer day15 opening.

| Time | Observable event and decision | Frozen author outcome / mechanical consequence |
|---|---|---|
| Day12 window | PM proposes earlier long reduction or holds conviction; operating partner reserves payment liquidity and investigates borrow | Partners can jointly authorize a reduction package beyond delegated ticket/turnover limits; hard limits still apply |
| Day13 opening | Broker recalls1,250 BRIN shares, cover-execution deadline day15 final executable event; settled replacement can cancel that recall | Replacement costs40% ACT/360 on replaced shares, not on unrelated borrows; locate alone cannot satisfy recall |
| Day15 final event | Replacement must already have transferred at day15 opening; cover must be queued before the final executable event | Otherwise contractual buy-in follows the published priority; event tape has sufficient capacity for1,250 shares at this deadline |
| Day16 opening | All remaining long marks95; all short marks110; stressed coefficients activate | On the unreduced reference book NAV23.125m; maintenance23.2375m; shortfall112,500. No15% drawdown freeze is needed for a broker call |
| Day16 response event | BEAM ref95/volume42,120; BRIN ref110/volume25,000; spread5bps/impact coefficient2,000;5% participation | Up to2,106 BEAM shares or1,250 BRIN shares fit the respective event. Exactly filling5% incurs10bps average adverse cost |
| Day17 opening | Day16 sales/covers settle; collateral return releases only at the linked cover settlement | Margin can improve on trade date, while spendable cash waits for settlement |
| Day20 close → day21 opening | Price Tactical redemption, crystallize only its dealt units' provision, pay redemption/fixed invoices | A gate is ineffective if requests fall below its cap; no invented subscription rescues missed cash |

The recall resolution on day15 changes subsequent holdings, so the unreduced day16 margin arithmetic is a separate replacement-borrow branch. Holding the quantity by replacing borrow preserves the reference short book; covering it produces a different actual shock result. Never apply both branch positions simultaneously.

**Partner choices.** The PM chooses which exposure to sacrifice and whether public thesis evidence warrants the carrying cost. The Managing Partner chooses replacement versus paying for a cover, reserves enough T+1 cash for Tactical, and presents the after-redemption leverage forecast. Either can cancel orders or execute the pre-approved safe reduction policy; neither can spend restricted proceeds or sign for the other.

**Numerical response branches, starting at the unreduced day16 reference state:**

| Branch | Exact decisive fill / state | Trade-off |
|---|---|---|
| Sell liquid long | Sell2,106 BEAM at94.905; gross reference reduction200,070; proceeds199,869.93; cost200.07. NAV23,124,799.93; maintenance23,097,451; positive headroom27,348.93 | Small voluntary cure preserves shorts but still fails stressed initial margin; more reduction is needed before new risk or later redemption |
| Cover a short | Cover1,250 BRIN at110.11; payable137,637.50; cost137.50. NAV23,124,862.50; maintenance23,113,750; headroom11,112.50 | Relieves short/borrow risk and increases net exposure. Collateral137,500 releases at settlement; extra137.50 needs usable cash/credit |
| Keep borrow only | Replace recalled1,250 shares at40%: at110 the replaced137,500 reference exposure costs152.777… per calendar date; other11,250 BRIN shares stay at their own stated rate | This resolves a recall but releases zero margin; it is not a standalone response to the day16 margin call |
| No valid response | The published broker algorithm liquidates eligible positions at the same tape prices/capacity | This can preserve solvency but fails the episode's voluntary-control objective; it does not automatically mean fund insolvency |

**Success and recovery.** An early conservative reduction can avoid the call entirely; a replacement-plus-later-voluntary-cure path can retain more thesis exposure but must build adequate day20 payment headroom. Each path must actually pay Tactical at day21 opening. A minimal margin cure alone is not the episode win. A forced-liquidation path may earn Survival after meeting cash obligations; an overdue redemption records a real failure. A concrete continuation for either voluntary day16 cure is frozen as follows: day18 BEAM reference95, volume400,000, default costs, permits a20,000-share sale at94.905, proceeds1,898,100 and cost1,900; it settles day19. All remaining reference marks stay95 for longs/110 for shorts through day20. The treasury reserves1.25m for the investor/invoices before optional debt repayment. In the long-sale branch, before further ordinary charges, NAV23,122,899.93 and maintenance21,767,451 result. With all original250,000 units still active, Tactical10,000 units is4% of post-fee NAV. Even allowing a conservative100,000 additional fund-charge allowance, post-redemption NAV is at least22,101,983.93, leaving334,532.93 maintenance headroom; the redemption plus at most100,000 due invoices fits the1.25m reserve. This allowance is a feasibility bound, not a substituted expense posting. The cover branch plus the same day18 sale also has over300,000 maintenance headroom under that bound. Players see future prices only when those events arrive. A missed day18 order loses this receipt; the last day20 BEAM event is a disclosed halt, so an order left until then cannot fund Monday payment. Do not tailor the halt to a player's holdings; earlier planned sales can succeed on that same tape.

**Debrief.** Separate BRIN price result, replacement-borrow expense, financing, trade cost, performance provision and LP cash. The thesis later becoming correct does not undo a recall deadline. Compare the same-tape earlier reduction only as a mechanical counterfactual, with the information that was available then.

### Case2 — Profitable, illiquid, and redeeming

**Situation and goal.** Day39, the fund has performed adequately but two LPs each require a $3m dollar-target redemption at day40. This standalone challenge expressly adds Tactical's external dollar target; the base campaign's10,000-unit day20 request remains a different contract. Both requests were disclosed day30 and properly noticed day35. Neither disappears with a good meeting. The partners must meet day41 payments, keep the post-flow book within its mandate, and explain any permitted gate fairly. The v2.2 challenge extends through day61 administration so deferred units actually reprice and pay. A day58 BEAM sale/reserve plan is specified in SCENARIO_CONTRACTS; full-season Renewal still disallows a terminal deferred request.

**Decision-comparison balance**, normalized after ordinary day40 charges common to both branches: NAV $25m; longs $25.5m, shorts $5m, restricted cash $5m, unrestricted cash $2.1m, debt $2.5m, fixed fees/financing payable $100,000 due day41. Check:2.1+5+25.5−5−2.5−0.1=25m. Performance is below the relevant series HWMs in this case, so no provisional incentive liability. BEAM is $8m of longs at100; the remaining17.5m is six2.5m equity longs (ALTO/COVE/ELAN/GALA/IONA/JUNO) plus2.5m BOND, all at100. Shorts BRIN/DART/FENN/HELI1.25m each. This v2.2 correction prevents post-flow issuer breaches. Ordinary initial/maintenance coefficients apply; credit remains capped at7.5m.

**What players know.** The public broad-equity earnings survey is unresolved; preserving BEAM retains broad market exposure, not a named thin-stock catalyst. The author-only fixed day43 BEAM104 realization is specified in SCENARIO_CONTRACTS and is not available to players at day39. BEAM has an executable day40 event but sale price remains uncertain until then. The prime broker confirms only eligible same-date cash netting; short collateral is unavailable for withdrawals. A new LP offers$5m, but diligence completes after day40 and funding earliest day60. The offer cannot cure this window. PM can request an extra liquidity estimate; the Managing Partner can negotiate a next-window plan, neither of which changes the binding current request.

| Time | Choices and event rules | Consequence |
|---|---|---|
| Day39 committee | Jointly approve a long-sale plan and cash reservation; elect or decline the20% gate before dealing | Preview both pre-flow and post-flow ratios; signatures cannot waive investor rights |
| Day40 executable event | BEAM reference100; volume840,000; cap42,000 shares; default spread/impact | A42,000-share sale fits and receives99.90 average; a32,000-share sale has lower impact on this same tape |
| Day40 final pre-dealing control | Broker/admin balances and fee NAV reconcile | Without certified values, record missed dealing/notification incident rather than invent a redemption price |
| Day40 dealing | Gate cap20% of actual post-cost/post-fee NAV; allocate equal dollar requests pro rata | Dealt units cease market participation now; undealt units remain exposed |
| Weekend → day41 opening | Ordinary dated carry; settle sales; pay dealt redemptions, then100,000 invoice | Holdings at day41 are still marked using last observed quotes; no phantom Monday sale before payment |

Both branches use the same fixed840,000-share volume event and six-decimal HALF_EVEN execution prices. The32,000-share order receives99.920975 under the cumulative impact model; it does not pay the42,000-share order's10bps average cost. The tape never changes in response to a gate choice.

| Branch | Cash and NAV at dealing/payment | Portfolio and LP consequence |
|---|---|---|
| 2A: pay all, sell42,000 BEAM | Reference sale4.2m; proceeds4,195,800; cost4,200; pre-flow NAV24,995,800. Deal6m → NAV18,995,800. Day41 cash before other later invoices:2,100,000+4,195,800−6,000,000−100,000=195,800 | Longs21.3m/shorts5m; gross138.4517%, net85.8084%; all requests paid, less liquid hedge retained |
| 2B: gate, sell32,000 BEAM | Proceeds3,197,471.20; cost2,528.80; pre-flow NAV24,997,471.20. Gate4,999,494.24; each LP dealt2,499,747.12; each deferred500,252.88 at that dealing price. Post-flow NAV19,997,976.96. Cash2,100,000+3,197,471.20−4,999,494.24−100,000=197,976.96 | Longs22.3m/shorts5m; gross136.5138%, net86.5088%. Genuine gate confidence penalties apply; deferred units' future dollar values float |
| Gate without a sale | At unchanged25m NAV cap5m, but only2.1m unrestricted and constrained future resources | A gate reduces6m to5m, not to available cash. Extra credit may fit the line but cannot by itself cure the resulting leverage ratios |
| No preparation, no gate | Deal6m at unchanged holdings → NAV19m; gross160.5263%, net107.8947% | A due withdrawal can create a passive mandate crisis despite profits and positive NAV. Borrowing to pay does not restore investor equity |

For illustration the reported195,800/197,976.96 cash excludes only subsequent newly accrued but not-yet-due weekend liabilities; these still reduce the day41 NAV bridge and remain payable at their contractual next invoice. Existing100,000 fixed fees were already liabilities: their payment is NAV-neutral. Unit rounding follows FUND_ACCOUNTING, retaining a cent reconciliation; the deferred dollar figures are dealing-date values, not guaranteed next-window claims.

**Failure and recovery.** A player cannot call escrow, unsigned commitments or short proceeds cash. A sell order entered after the last day40 event cannot pay at day41 opening. If a selected fixed tape includes a halt, cash from the blocked sale does not arrive; the case enters treasury distress, with the named unpaid amount visible. A permitted pre-dealing gate and larger earlier liquid sale can prevent that state; a late gate cannot erase already-created redemption payables. Responsible winddown remains available if cure is impossible.

**Role balance and debrief.** The PM decides which expected return to give up and checks hedge direction after sales. The Managing Partner owns notices, netting, payment order, gate explanation and the later capital offer. Review dollars dealt versus paid versus deferred, fee-base reduction and post-flow leverage. Do not award a higher grade merely because a gate preserved manager revenue or because new capital raises displayed AUM.

### Case3 — The report is balanced, the NAV is wrong

**Situation and goal.** Day29, a new LP is considering $5m for day40. The partners must provide a certified report, respond to a corporate-action discrepancy, and fund their company through day41. The challenge tests honest control and business capacity, not maximizing a short-period return. A routine accurate report is possible without buying an operations hire; the hire buys an earlier warning/additional contingency assignment only.

**Visible checkpoint.** All fund250,000 units share HWM100 for this case. Internal pre-performance capital B=$27.5m, provision F=$500,000, displayed net NAV=$27m. Assets: cash5.035m, restricted collateral4.8m, longs22.5m; liabilities before the incentive provision are short BEAM4.8m and a fixed35,000 management-fee payable matching the company receivable. Thus pre-performance capital remains27.5m. The seeded35,000 is already earned with the disclosed day41 payment date; incremental future accruals are outside this isolated cash oracle and still run in the compiled case. The100,000-share BEAM short had marked50 before its$2/share distribution and now marks48. The internal journal balances, but it omitted the$200,000 dividend-in-lieu payable. Broker control record includes it, independently authored admin control flags the difference. Company cash$72,000, baseline$20,000 weekly costs; accrued management-fee receivable/invoice due day41 is a fixed$35,000 in this isolated company cash case. The$500,000 provisional incentive forecast is not company cash or revenue.

**Known information and restrictions.** A day29 research packet contains an explicitly flagged confidential issuer sales schedule for ALTO. ALTO enters RESTRICTED until its authored public release day33; queued elective ALTO buys/sells cancel, no self-clearance is possible. The PM can investigate an unrelated public thesis or reduce unrestricted holdings with valid authority. This fact never grants privileged certainty about BEAM or another company. The prospective LP's standard-fee offer requires a corrected/certified report by day35 and actual funding before day40 admission. It can be capped or declined if capacity is inadequate.

| Time | Player decision / engine event | Exact consequence or control |
|---|---|---|
| Day29 window | Operating partner reviews broker break; PM explains short dividend economics and chooses a permitted research alternative | Internal balance alone cannot certify. Discretionary ALTO trades are blocked regardless of consent |
| Day29 correction | Post200,000 dividend-in-lieu expense/payable; recompute performance provision | B27.3m; F460,000; true net NAV26.84m. Net drop160,000 includes40,000 fee reversal; do not subtract200,000 again later at payment |
| Day30 close | Company baseline weekly payment20,000 | No-hire company cash52,000; if hired ops for10,000 immediately, cash42,000 |
| Day31 boundary | Ops hire, if selected, starts24,000 total weekly burn | No hire creates no extra capacity but no extra salary |
| Day33 | Authored public ALTO release | Restriction clears only through the versioned event; price may already have moved before a later eligible order |
| Day35 | Corrected report reaches LP; weekly payroll | No-hire cash32,000; hire branch18,000. Missing report closes this offer under its published condition, not a random trust punishment |
| Day40 close | Weekly payroll; funded eligible LP admission optional | No hire cash12,000; hire can pay18,000 of24,000 and records6,000 unpaid, COMPANY_DISTRESS. A5m subscription increases fund AUM, not company cash |
| Day41 opening | Fund pays previously fixed35,000 management fee when its treasury can pay | No-hire cash47,000; hire branch receives35,000, pays6,000 arrears, cash29,000 and exits distress within the five-day cure window |

**Corrected valuation logic.** The$200,000 short price gain on ex-date was offset by the omitted$200,000 distribution expense. Correcting a false profit reverses$40,000 of the20% provisional fee. It does not reclaim a fee already crystallized on past redemptions. The independent record identifies a true economic event; neither partner chooses its amount. Pay-date movement reduces cash and payable together. The report retains original/corrected versions and event identities.

**v2.2 active-choice correction.** Hiring here is removed from the playable action set: its warning arrives after the known break and no useful extra task was defined. Hiring cash numbers below remain a dominated forecast teaching example, not a second strategic success path. Active alternatives are independent diligence/public-research attention and cap/admit/decline capital; exact histories/reveals are in SCENARIO_CONTRACTS.

**Choices with consequences.** The PM can insist on a clean public research path, choose smaller unrelated exposures, or spend an assignment on explaining the real source of the apparently strong return. The Managing Partner can keep staffing lean, hire knowing a temporary cash shortfall is forecast, or decline/cap capital to match liquidity. Investor admission remains jointly approved; the archived hire arithmetic is not an active choice in this challenge. No action unlocks spending the fund's5m subscription on payroll or banking the460,000 surviving performance provision. At constant new capital,5m creates only205.479… of management-fee accrual per calendar date; its first28 dates would yield at most5,753.42 before fee-base erosion, paid at a later window. That does not rescue day40 payroll.

**Success branches.** Correct promptly, allocate an assignment to diligence and admit/cap the compatible LP; or correct promptly, allocate attention to public portfolio evidence and decline capital. The hire/cure path is an arithmetic forecast example only, excluded from active gameplay and success-path counts. A solvent decline-capital path also succeeds if it meets the report and cash objectives. Case outcome reports47,000/20,000=2.35 weeks versus29,000/24,000=1.2083 weeks of company cash runway, not the full-season four-week Renewal result.

**Failure and recovery.** Ignoring the break leaves official reporting/dealing uncertified and loses the conditional offer. Trying to certify a known wrong report or bypass the restriction is blocked and logged, not rewarded as a clever strategy. If the fund cannot pay its35,000 fee at day41, the archived hire forecast's6,000 unpaid payroll would remain; a prospective subscription does not itself pay the company. Apply the ordinary five-business-day cure deadline and then controlled winddown if no earned/collectible fee or permitted cost reduction can cure it. Correcting an error later can restore reporting but does not fabricate the missed offer or erase arrears.

**Debrief.** Contrast internal accounting balance with external reconciliation, economic return with dividend mechanics, provisional incentive fees with recognized cash, and larger fund assets with business runway. The corrected report and source cutoff matter even if the next stock movement would have made the prohibited trade profitable.

## 9. Scenario authoring acceptance gate

Before any case is called playable, compile its warm-start balanced journals, per-series history, every quote/volume/borrow/corporate-action/control record, subsequent accrual/settlement dates and all success/failure routes into the validated engine schema. Freeze the branch-independent tape and information reveal schedule. Use one fixed volume path per scored version; do not select a more punitive tape after seeing a command. Warm starts preserve valid fee histories and authorizations; they do not bypass mandate constraints.

For each case execute two strategically distinct success plans plus an explainable failure/recovery plan with two authenticated humans or a clearly labeled automated command script. Verify cash/claims and stopping-phase hashes, resource budgets, LP transitions, fee-series fairness and no future data. Numerical checkpoint oracles are inputs to this work, not passing playtests. Review whether each partner had a consequential choice and whether the debrief distinguishes information available then from hindsight. Balance updates create a new scenario version.


---

Source: `docs/FUND_ACCOUNTING.md`

# Fund accounting, treasury and deterministic resolution

Version 2.1 · Proposed launch contract · Not implemented and not universal fund accounting, law or prime-broker terms.

## 1. Boundaries, calendar and precision

Maintain separate investor-fund and management-company ledgers. A season transaction coordinator posts actual inter-entity fee transfers atomically while each journal balances independently. LP capital, fund AUM, management-company equity and partner ownership are different claims. No fund asset finances company payroll.

Use Decimal/fixed precision: cash cents, prices at least six decimals, fee calculations at least twelve decimals, investor units eight decimals. Monetary postings round HALF_EVEN; carry fractional accrual residuals per obligation. Allocate pro-rata cents/units by largest remainder, ties by immutable series ID. No binary-float money or rewriting journals. Preserve gross economic identities even when cash settles net.

**Calendar contract.** Day1 is Monday 5 January 2026; day20 30 January, day40 27 February, day60 27 March, day61 30 March. The fictional calendar trades Monday–Friday and deliberately ignores exchange holidays; it is not a NYSE calendar. Initialize capital immediately before day1 opening, with no prelaunch fee. Every calendar date from 5 January has one end-of-date accrual, including Saturdays and Sundays. The scored period through day60 contains 82 calendar accrual dates and 60 business days. Calendar dates, business-day indexes and wall-clock audit times are separate fields. Historical packs must replace this calendar explicitly.

For calendar date D: management fees use the previous calendar close's post-flow capital before reversible performance provisions (initialized opening capital for day1); borrow/debit costs use D's closing settled borrowed shares/debt. New settled borrows incur D's charge; a return completed at D opening incurs none for D. Rates effective at D opening apply prospectively for that date; an intraday rate notice first affects the next date. Nonbusiness dates repeat the same close process with carried last available marks, their original mark timestamps and no trades or company payroll. A daily balance convention is a disclosed contract simplification, not intraday interest integration. ACT/365 means actual calendar dates divided by a fixed 365; ACT/360 uses a fixed 360. Never silently substitute 252 or leap-year ACT/ACT.

## 2. Balance sheet and independent records

| Fund assets | Fund liabilities / capital |
|---|---|
| Unrestricted settled cash | Trade payables |
| Restricted short collateral cash | Broker debit balance |
| Trade receivables | Marked short-position liability |
| Marked long securities | Accrued borrow/debit interest |
| Dividend receivables | Dividend-in-lieu payable |
| Other explicitly eligible receivables | Management, crystallized and provisional performance-fee liabilities |
| | Dealt redemption payables; LP series capital |

Company accounts include unrestricted cash, contractual management-fee receivable, crystallized performance-fee receivable, operating payables, owner capital, fee income and operating expenses. Provisional performance fees are only a company forecast, with no company receivable/revenue until crystallization under this game convention. This is a management-book simulation, not a GAAP/IFRS assertion.

Fund NAV = unrestricted cash + restricted cash + trade receivables + long MV + valid other assets − trade payables − short MV magnitude − debt − other liabilities. Do not subtract both a signed short MV and the short liability. Fees already in liabilities are not deducted again. Reservations are resource commitments, never extra expenses or NAV liabilities.

Balanced internal journals are necessary but insufficient. Reconcile economic/settled/borrowed quantities, cash and settlement records against separately authored broker statements; compare series, fees and NAV to independent administrator control records. Fixture control records must not be produced by calling the same posting function being checked. This is simulated external evidence, not an actual appointed administrator or audit. Record source, as-of time, expected timing differences, tolerance, owner and resolution for every break. Cash tolerance is one cent only where specified rounding explains it; quantities and economic identities match exactly. No unexplained plug.

A valid internal ledger with an external discrepancy blocks new risk and official NAV/dealing certification while the team investigates; verified mandatory payments, cancels and authorized risk reductions can continue from reconciled resources. An internally failed invariant is a technical integrity fault: pause economic transitions until repaired/replayed, without pretending financial deadlines have been satisfied. Correct errors through linked reversal/reposting and an explicit restatement, not a player-selected favorable mark. Missing or stale prices remain visible; a stale price may support a provisional estimate but cannot silently become a fresh executable quote.

## 3. Trades, settlement, borrow and corporate actions

Recognize long economic shares/cost and a trade payable at purchase execution; settle cash later. A sale removes FIFO lots, creates a trade receivable and realizes gain/loss. At a short sale, recognize receivable and short liability; proceeds settle into restricted cash. The economic short changes with marks on trade date, whereas settled borrowed shares begin on delivery/borrow settlement. Covers create trade payables and reduce economic short liability; borrowed shares and pending returns remain until settlement. A cover never creates a long lot. Position reversal consists of explicit close/open legs, with fresh locate/risk checks on the new short.

Synthetic T+1 means next business date on the declared calendar. Selling an economically owned unsettled long requires an explicitly supported delivery chain and broker funding. Net cash only among due obligations with the same fund, counterparty, currency, settlement date and contractually eligible netting set. Restricted short proceeds cannot be netted into freely withdrawable long-sale proceeds. Retain gross obligations and settlement status; a failed receivable cannot fund a payable merely because their projected totals offset. Atomic cover settlement may release its linked collateral to pay the cover and return shares; only residual collateral becomes unrestricted.

Borrow fees = settled borrowed quantity × reference closing price × active annual rate /360 for each calendar date, including pending returns and weekends. No ordinary fee on a locate or unfilled reservation. Pre-borrow is excluded. If a short sells Friday and settles Monday, ordinary borrow starts Monday; if covered Friday and returned Monday, Friday–Sunday fees continue. Weekend closes use the last available reference price, including for a zero-economic-short pending return.

Support two launch corporate actions with dedicated cases: cash distributions and integer splits. A distribution event declares entitlement snapshot, ex-date, pay date and amount. Determine economic long/short entitlement at the immediately preceding cum-dividend close; recognize long receivable or short dividend-in-lieu expense/payable at ex-date, settle at pay-date. Preserve any manufactured-payment/settlement-chain record so a closed-but-undelivered position cannot double count entitlement. This is the synthetic contract, not a full tax or market-claims engine. A $2 distribution with a $50→$48 mark on an unchanged 100-share long yields −$200 price P&L +$200 income; on a short it yields +$200 price P&L −$200 expense. It is not free alpha.

An integer split adjusts economic and settled shares, lots, borrow, pending delivery quantities, per-share costs, resting order quantities/prices and locate reservations once under one action identity; invariant value is preserved at the reciprocal price. Fractional entitlements, reverse splits producing fractions, rights, spin-offs, mergers and special tax classifications are excluded; reject such imported actions. Raw execution marks plus explicit distributions are authoritative; adjusted total-return series must never generate a second dividend. Slippage is already in executed cost/proceeds; explicit commissions alone post separately.

## 4. Cash, collateral, credit and margin

Restricted collateral target = 100% of marked economic short exposure plus collateral contractually retained for pending share returns. A short-sale receivable commits to collateral before settlement and is not withdrawable. Map collateral to obligations so a covered short cannot release cash on trade date and spend it again at settlement. Transfers between restricted/unrestricted cash do not change NAV.

Initial credit limit $7.5m, annual debit rate 6% ACT/360, ordinary borrow rate 2% ACT/360. Broker debt is a positive liability, never negative cash. Credit funds authorized fund obligations, never the company. Cash earns 0% in the launch contract, as does restricted short collateral; the matched cash benchmark uses this same zero rate. Future interest/rebate variants require explicit rates, eligibility and posting, not an external risk-free rate attached to non-interest-bearing game cash.

Available credit = max(0, limit − funded debt − reserved credit). Initial requirement = 0.50×long MV +0.60×short MV; maintenance =0.35×long MV +0.40×short MV. Margin equity is net NAV unless an expressly named receivable has a haircut; valid ordinary T+1 receivables are eligible. Liabilities already deducted from NAV are not deducted twice. A margin pass is not a cash pass. Neither test grants legal rights against a real broker.

Forecast each due-event cash balance after collateral, trades, redemptions, fees and permitted credit. Reserve resources for the earliest competing commitment. Unexecuted future sales are conditional scenarios, not settled resources. Test the book after an anticipated redemption as well as before it: canceling units creates a liability and shrinks risk-bearing equity even before cash leaves. A timely valid redemption is not refused merely to preserve a leverage ratio; players must plan sales, use the contractually permitted gate before dealing, or enter a real remediation/default state.

At each treasury sweep: (1) settle eligible trade obligations, including linked cover collateral release; (2) top up collateral using permitted credit; (3) pay due dealt redemptions; (4) pay due fixed fees and financing invoices; (5) repay debt above the policy cash buffer only after reserving already-known subsequent obligations. Each priority group is netted only where eligible; equally ranked short-funded claims pay pro rata with stable residuals. No negative cash or unauthorized credit. Record unpaid obligations and distress. These payment priorities are a fictional contract, not insolvency-law priority.

Cash buffer defaults to 2% of NAV and can be lowered jointly; mandatory obligations outrank it. It is not another asset or a direct score reward. Accrued borrow/debit interest is invoiced at each day20/40/60 close and due next business opening; unpaid accrual remains a liability and does not silently capitalize into credit. New series admitted at close do not inherit earlier common expenses.

## 5. Series participation, flows and return

Original series: Seed100,000 units, Patient80,000, Tactical70,000, each at $100 and HWM100. Each subscription creates a new series at100/HWM100. One fee schedule applies; different entry histories are not custom side letters.

**Common P&L weights use opening participation capital A_s = prior calendar-close net series capital N_s + its reversible performance provision F_s.** Exclude crystallized fees, management liabilities and dealt redemption liabilities; those claims no longer participate. Allocate common investment P&L and common fund expenses using A_s/sum(A). Series-specific management and performance fees follow. A subscription participates from the next calendar period. Intraday investment P&L remains allocated to opening participants because all dealing is at close. Zero/negative total participation capital enters distress rather than division by zero.

This avoids charging a fee-accruing cohort for a smaller fraction of subsequent recovery/loss merely because its provision differs from another cohort's. It is an explicit launch allocation contract; alternative equalization methods are not interchangeable. A net-capital weighting can be coherent under a different fee-reserve investment policy, but v2.0 never defined such a policy. All allocated cents and series net capital must reconcile to fund NAV after provisions.

A subscription remains outside the fund in a simulated escrow until funded and eligible at dealing. Admission receives cash/issues units, not revenue. A request is not a liability. At dealing, use certified values, fees and any gate to fix accepted units/net amount; crystallize only their pro-rata provision when appropriate, cancel accepted units and create redemption payable. That amount immediately ceases portfolio participation. Payment is cash/payable reduction, not a second flow. Gated units remain invested and fee-bearing with unchanged fee history.

Calendar-period net return = pre-flow net NAV / prior close post-flow net NAV −1; geometrically chain into a wealth index starting100. Business-day reports roll nonbusiness subperiods into the next business period; retain calendar subperiods for fees and audit. All subscriptions and dealt redemptions are excluded from investment return. Cash payment of an existing liability is NAV-neutral. Aggregate returns can reflect changing cohort/fee mix; also show gross investment return and each LP's net series return. An aggregate NAV/unit across different fee series is misleading.

Show LP contributions, dealt/paid distributions, requests, remaining capital and own fees. Money-weighted return is deferred until a dated solver/undefined-case contract exists. Net TWR, fee drag and market contribution are accounting decompositions; none identifies skill or proves causal alpha.

## 6. Management fee, performance provision and crystallization

Management rate is1.5% ACT/365 fixed. For date D, fee_s = opening A_s ×0.015/365. This base is after earlier common expenses and fixed liabilities, before reversible incentive provisions and today's management charge. Accrue fund expense/payable and company contractual revenue/receivable. Pay amounts accrued through day20/40/60 at the next business opening. Weekend accrual after a dealing close belongs to the next payment window. No fee on escrow capital or canceled units.

Let U_s be active units, H_s the last annual crystallized post-fee HWM, and B_s be current participation capital after common P&L/expenses and the current management charge, before the current reversible performance provision. Target F_s =0.20×max(0, B_s/U_s−H_s)×U_s; net capital N_s=B_s−F_s. Post only change in F, including reversals. Reconstructing B from a net ledger means adding back the **previous** reversible provision exactly once. No fee hurdle; cash interest would be fee-eligible if a future contract enabled it.

Annual performance crystallization is **31 December**, for all active series, after that calendar date's accruals. The January–March launch season never reaches it. Convert F into fixed fee payable without another expense; recognize company revenue/receivable; reset F to0 and H to max(old H, post-fee NAV/unit). New subscriptions use the same fund year-end, not a new anniversary. A short inaugural annual period is contractual. If year-end is a nonbusiness date, use the ordinary dated close and pay next business opening. Retain HWM and provisional claims through renewal; restarting a season cannot reset losses or collect a provisional fee.

At an earlier redemption, crystallize F_s×(accepted units/U_s), with deterministic residual allocation, and reduce surviving F and U in the same proportion. **Surviving H stays unchanged.** Do not reset a whole series HWM because one investor fraction redeems. An annual full-series crystallization on the same date takes precedence, so redemption never charges a second fee. Full closure preserves the closed record. Crystallized performance fees are due at the same next-business opening as the redemption. A later loss reverses only surviving uncrystallized provision; fixed fees are not refunded under this contract.

Accrual, crystallization and payment are distinct: provisional liability reduces LP net NAV; crystallization makes the manager's claim fixed/recognized; payment turns its receivable into cash. A manager cannot spend a forecast or accelerate the annual date to meet payroll. Winddown crystallization applies only to actual final investor liquidation under its explicit termination contract, never merely because a season score is displayed.

### Isolated arithmetic oracles (other costs/flows off)

1. U1000/H100/B110000 → F2000/N108000. Annual crystallization H108; later B104000 or108000 produces no fee, B110000 produces400 and net109600.
2. Before annual crystallization, B110000→105000 reverses provision2000→1000. Previously fixed/paid fees would not reverse.
3. Entry fairness: old1000 units/H100/B95000, new950 units/H100/B95000; common return10% produces oldB104500/F900 and newB104500/F1900. Net capitals103600/102600.
4. Cohort allocation: seriesA N108000/F2000/A110000; underwater seriesB N100000/F0/A100000/H120 with1000 units each. Common P&L21000 allocates11000/10000, not10903.85/10096.15. Closing A B121000/F4200/N116800; B B110000/F0/N110000; total NAV226800.
5. Partial redemption: U1000/H100/B110000/F2000/N108000; accept250 units → redemption27000, fixed performance fee500, remaining U750/F1500/N81000/H100. No full-series H108 reset.
6. $25m fixed opening fee base ×0.015/365 =1027.397260273973… per calendar date; displayed first posting1027.40 with residual. Three constant-base dates sum3082.19178082…→3082.19. Actual recurring bases change with posted accruals, so this is an isolated constant-base oracle. $3m settled debt at6%/360 costs500/date. $1m settled borrow at2%/360 costs55.555555…/date; three dates total166.67 after residual rounding.
7. Redemption leverage: NAV25m/L27.5m/S5m gives gross130%, net90%. Deal5m at unchanged holdings → NAV20m, gross162.5%, net112.5%. Payment itself creates no additional ratio change.
8. Cover direction: NAV25m/L25m/S5m gives net80%; cover all5m, costs off → net100%, gross100%. With just$100 cost net becomes100.0004%, so a cover-only plan breaches a100% net cap. Sell enough long exposure first/alongside under separately executable safe prefixes; never assume an atomic basket on an event tape.

These cases are expected arithmetic, not executed application tests.

## 7. Authoritative event order and endpoint

Business date:
1. Opening administration: activate effective contracts, process prior-trade settlements and due payments, settle corporate-action cash and effective staff changes. Due failure enters distress before elective trading.
2. Opening market: publish available public evidence/quotes/borrow and ex-date actions; mark coherently; recheck recalls, credit, margin and mandates. Material crisis pauses before its next eligible execution event.
3. Execution: due forced obligations first, then authorized voluntary orders in stable acceptance order. Revalidate authority, restriction status, available resources and every risk dimension for each partial fill; post journal/obligations/reservations/outbox atomically.
4. Further tape events repeat publish → mark/risk → eligible execution. New commands require a strictly later information/execution event.
5. Close: mark, accrue calendar-date financing/dividends/common expenses, allocate common P&L, accrue management fees and recompute provisional performance fees; accrue/pay business-day company costs as due; run risk/treasury and independent reconciliation controls.
6. Certified dealing close: annual crystallization if its actual date; compute eligible requests/gate on certified pre-flow post-provision NAV; crystallize accepted redemptions pro rata; cancel units/create payables; admit funded subscriptions; recheck post-flow risk. An unresolved certification break blocks the dealing operation and produces an explicit missed-event incident, not stale-price dealing. Fund an obligation due earlier today before considering tonight's subscription.
7. Certified checkpoint: certify both ledgers/series/independent controls, apply chapter relationship transitions once, create notice-cutoff requests, record outcomes/hash. Cutoffs15/35/55 use the latest certified relationship state then available, not the future dealing result.

Nonbusiness dates run only dated accrual/provision and control/risk checks, carrying mark timestamps. Material alerts pause before the next tradable event; they cannot create weekend executable liquidity. No company business-day payroll on weekends. One event identity per date/phase prevents replay double charges.

The first slice checkpoints after the ordinary day21 opening administration. The full season checkpoints after ordinary day61 opening administration. Both include their intervening Saturday/Sunday accruals, settle due prior-day obligations, and stop **before** that Monday's market event or daily accrual. There is no frozen terminal market or synthetic one-day carry charge. Day60 performance remains the scored investment period; separately bridge day60 net NAV to the day61 opening cash/holdings state, including weekend expenses, provisional-fee reversals and already-recorded flows. The checkpoint carries last observed Friday marks with their age; it is not a fresh Monday valuation or proof of liquidated proceeds. Continuing resumes the next pending event exactly once.

Renewal carries holdings, debt, series HWM, provisional fees, requests and claims into the next season. A winddown continues actual market/settlement/calendar events and charges until final liquidation/payment or documented default. Do not manufacture final investor cash by marking remaining positions. Endpoint obligations, including newly accrued not-yet-due fees, remain in the balance sheet and debrief.

## 8. Execution model

Synthetic fixtures supply ordered executable reference quotes, spread, event volume, borrow state and availability time. Per-fund participation cap defaults5% of event volume summed across all orders in that instrument/event. A deterministic queue consumes this volume. A liquidity shock changes actual later capacity, not merely a cosmetic meter.

For cumulative same-side executed quantity Q and event volume V, define total adverse execution cost C(Q) = reference × Q × [half_spread_bps + impact_coefficient_bps × (Q/V)^2] /10,000. A subsequent quantity q incurs incremental cost C(Q+q)−C(Q). Its per-share executed price is reference + side×[C(Q+q)−C(Q)]/q, where side=+1 for a buy/cover and−1 for a sell/short. Default half-spread5bps and coefficient2,000bps; scenario overrides are explicit. Quantize executed prices before computing cash and carry the resulting cost residual deterministically. Maintain separate cumulative buy and sell quantities for cost, with one shared total-volume participation cap across both sides. Splitting orders cannot reset Q or reduce total modeled impact.

Market orders carry an explicit maximum cash/credit commitment and quantity authority, not an unlimited reservation. If a gap breaches that budget, reject or fill only the preauthorized affordable quantity according to the order's immutable partial-fill policy. Display “market order with cash protection”; do not imply that a reservation buffer is a market-price guarantee.

A limit order fills only at actual tape events where the modeled executed price satisfies its limit; choose the largest eligible whole-share quantity meeting limit, remaining budget and event capacity. No fill simply because an OHLC high/low crosses. DAY remainder expires at the declared close; launch GTC orders expire at the chapter boundary unless renewed. Canceled, recalled, stale or superseded authority cannot execute.

Complete states include DRAFT, PENDING_APPROVAL, AUTHORIZED_QUEUED, PARTIALLY_FILLED, FILLED, CANCELED, EXPIRED and REJECTED. “Authorized” can reference a delegation or specific committee signatures. A remaining partial order owns only its remaining reservations. Duplicate event delivery cannot consume the same liquidity, borrow or cash twice.

## 9. Required invariants and evidence

- Assets minus liabilities equals the sum of active series net capital; adding back provisional performance liabilities reconciles to participation capital.
- Company equity/revenue/receivables/cash remain distinct; paid fees are equal/opposite transfers, never repeated expense/revenue.
- Cohort allocation, admission, HWM, partial redemption and annual crystallization conserve both claims and units.
- Borrow starts on settlement and continues through, but not including, settled return date; weekends and split quantities cannot be lost.
- Netting respects counterparty/date/currency/collateral eligibility; failed receipts do not fund payments.
- External flows do not create return; redemption changes equity at dealing, not again at payment.
- Initial margin, maintenance, credit, settlement sufficiency, mandate deficits and restricted-list status are independent checks.
- Corporate actions preserve economic value correctly; adjusted data cannot double count income.
- A gate conserves accepted/deferred quantities and allocates eligible claims fairly.
- A reduction checks all resulting ratios, including net exposure and post-flow denominators; forced action records any unavoidable breach rather than concealing it.
- Independent broker/admin discrepancies are detectable even when the internal journal balances; corrections preserve the original evidence.
- Fixed tape/commands/rules reproduce events, balances and hash; retries and partial-fill races cannot duplicate meaning.
- Day21/day61 resume at the saved phase without duplicated weekend accrual, settlement or Monday returns.

These are required future acceptance behaviors. Document arithmetic and fixture syntax checks do not establish an implemented engine or independent financial certification.

## 10. v2.2 collateral, recall and termination contracts

These fictional broker/termination choices supersede ambiguous v2.1 wording, not universal industry practice. Rationale: DESIGN_REVIEW_V2_2; schedules: SCENARIO_CONTRACTS.

**Collateral mapping.** Track settled loan lots, unsettled deliveries, pending returns and linked cash. For economic shorts not covered, target = shares × current reference mark. An unsettled sale earmarks its collectible proceeds; only excess target above earmarked proceeds requires usable cash/credit. Never add proceeds commitment to a second full target. A failed receipt is not cash. Settled collateral is cash held by broker. At cover execution, covered shares move from active marked target to a pending-return target frozen at that event's **reference** price, not cost-inclusive fill. Retained collateral does not re-mark; pending-share borrow fees still use daily current marks until actual return. This is a selected simplification, not a real broker guarantee.

If allocated cash differs from the frozen target, top up/transfer only the difference once; never release frozen cash on trade date. At linked settlement release retained target atomically to cover payable, source shortfall from usable cash/credit, return shares and release remainder; otherwise record failed settlement/retained borrow/collateral. Partial return releases proportional collateral; event identity dedupes. Split changes quantities/reference prices, not retained aggregate cash. Case1 frozen137,500 pays137,637.50 with137.50 extra funding; a later mark changes borrow expense, not frozen cash. Remaining active shorts re-mark normally.

**Replacement borrow.** Locate/reservation is not settled borrow. Terms name cutoff, inventory, transfer event, old/new loan identities and rate. Case1 cutoff day14 before EXEC_B; transfer day15 OPEN_ADMIN. Atomically replace1,250 shares/cancel matching recall, changing no economic short/collateral/NAV.40% starts day15 accrual; old2% ends before that date. Late selection rejected; absent transfer means no timely cure.

**Margin response order.** Shock creates deficit/freeze/pause. At next execution: due recall buy-ins first; then valid authorized voluntary margin remedies in accepted order; recompute each fill; then forced margin liquidation on remaining deficit using residual capacity. Pending escalation is not a due mandatory fill that outranks the promised voluntary window. A new deficit at execution pauses before next event; an overdue recall receives no extra grace. Mandatory fills may cause a recorded mandate breach. Never assume atomic baskets.

**Controlled termination.** Season ending is not termination/crystallization. Joint winddown consent cancels elective additions and starts WINDDOWN; existing liabilities, participation, fees, borrow/collateral and company costs continue. Liquidate under actual tape/cost/capacity; restricted holdings await clearance except contractual mandatory dispositions. Declaring termination earns no bonus or spendable fee.

Recovery horizon is ten further business days plus intervening calendar dates. Author those events before claiming completed winddown; missing tape means UNRESOLVED_WINDDOWN. At a certified solvent final close with securities/returns settled and other claims reserved/fixed, crystallize surviving provision once under this termination contract, burn remaining units, fix investor distributions and pay next business admin in fictional treasury priority. Management fees end on final dealing date because participation ceases; unpaid fees/claims persist. Company overhead ends next weekly boundary on termination of activities; accrued obligations persist. No admission in winddown.

If NAV<=0 or claims cannot be paid, record cash/unpaid claims/positions/pending returns/uncertified estimates, not fabricated investor proceeds. The game's treasury priority is not a legal insolvency waterfall. Halt/unsettled assets at horizon give unresolved residual claims, not COMPLETED_LIQUIDATION. Technical integrity faults require repair/restore, never erase deadlines/liabilities. Statutory/tax/real administrator termination remains excluded.


---

Source: `docs/LIBRARY_RESEARCH.md`

# Library research and dependency decisions — v2.1

Reviewed 6 October 2026 against actual repository files and official APIs. This is a source review, **not an installation, compatibility test, security audit or benchmark**. Exact commits, source blobs and license blobs appear in [library_review.json](https://github.com/krishbansalofficial/fundforge/blob/main/fixtures\library_review.json). Default-branch timestamps are narrow maintenance signals, not release pins or support guarantees. At implementation, select supported releases, lock transitive dependencies and review their licenses.

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


---

Source: `docs/SIMULATION_ARCHITECTURE.md`

# Simulation architecture — v2.2

Proposed interfaces and ownership, not implemented services. The architecture is a **modular monolith with one economic authority**, not a network of trading platforms. [FUND_ACCOUNTING](https://github.com/krishbansalofficial/fundforge/blob/main/docs\FUND_ACCOUNTING.md) owns exact financial/event conventions; [GAME_SYSTEMS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\GAME_SYSTEMS.md) owns player permissions and gameplay; this document owns software boundaries. Resolve conflicts explicitly before FF0 freezes schemas.

## Ownership and interfaces

| Component / owner | Authoritative state | Inputs → outputs | Must not do |
|---|---|---|---|
| Season clock | Dated phase, sequence, pause/checkpoint, calendar version | Advance command + ready/exception state → next phase/event IDs | Read wall clock to accrue economics or let refresh advance time |
| Information service | Immutable observations/revisions, available-at and entitlement metadata | Actor, scenario cutoff, query → permitted evidence with source/time/quality | Expose future tape, corrected history or hidden scenario triggers |
| Market simulator | Approved tape, frozen latent process state, event volume/borrow/marks | Seeded scenario + phase → ordered market events | Reward a player's thesis by changing future prices or call live APIs |
| OMS/execution | Orders, authority references, reservations, fills, remaining capacity | Valid command + strictly later eligible event → fill/cancel/expire/reject | Own a second portfolio or invent an intraday path from OHLC |
| Risk/treasury | Versioned constraint policy, deficits/calls, deadlines, forecasts | Authoritative book + commitments + proposed deltas/flows → constraint vector/action eligibility | Treat lower gross as proof that every risk falls or cash as NAV |
| Fund journal/valuation | Accounts, lots, economic/settled quantities, obligations, certified snapshots | Economic events + coherent marks → balanced postings and NAV bridge | Fetch prices, silently plug reconciliation breaks or count reservations as expenses |
| Investor accounts | Units, participation capital, HWM/provisions, notices/dealt claims | Certified close + LP contract → fees/accepted units/payables/series statements | Turn a notice into a payment or pay new cohorts for old returns |
| Management company | Separate cash, receivables, payroll/providers, staffing commitments | Fixed earned fees and budgets → invoices, cash forecast, capacity/insolvency events | Spend fund assets or reversible performance provisions |
| Scenario engine | Versioned public/hidden events, prerequisite/branch state, NPC decisions | Allowed triggers + deterministic state → notices, evidence, incidents and debrief causes | Directly overwrite balances, price outcomes or scores via narrative |
| Transaction coordinator | Commands, economic IDs, sequence, journal/outbox commit boundary | Typed intent → accepted/pending/rejected result + atomic domain effects | Let UI, provider workers, AI or projections mutate economics independently |

All economic mutations pass through the coordinator. Read models and WebSocket/polling feeds are rebuildable projections, never authorities. Keep modules callable in-process and finance/game functions free of network calls. A small synchronous executor is acceptable first; background work must preserve the same transaction boundaries.

## Proposed contracts

Names describe schema intent, not existing endpoints.

- `Command`: command_id, idempotency_key, actor_id, season_id, expected_state_version, type, immutable payload, submitted_at, policy_version. Hash normalized payload before accepting a retry. Authorization is rechecked even for old idempotency keys.
- `CommandResult`: status, reason_codes, resulting_version, event_ids, affected_obligation_ids, earliest_execution_event, resource_preview. A preview is not an approval or guaranteed fill.
- `MarketEvent`: event_id, tape_index, calendar_date, business_day, phase, instrument_id, reference price, spread, volume, borrow state, quote timestamp and quality. Decimal values serialize as strings; enum/size bounds are explicit.
- `Observation`: observation_id, entity, metric/unit, economic_period, published_at if evidenced, observed_at, available_at, revision, source, mapping_version, rights_ref, quality, payload_hash. This describes evidence, not a tradeable quote.
- `EconomicEvent`: monotonic sequence, unique economic_id, parent/cause IDs, simulated timestamp/phase, actor, command, policy/data/schema versions and typed payload.
- `RiskSnapshot`: gross/net/issuer/sector/factor exposures, liquidity ladder, collateral/credit usage, initial/maintenance requirements, post-flow forecasts, uncertainty/mark age, breach vector and deadlines. Every metric has denominator and as-of metadata.
- `LedgerBatch`: entity, economic_id, debit/credit lines, currency, residual accounts, obligation/lot/series references, reversal_of when relevant. Fund and company balance independently.
- `Checkpoint`: next pending phase/event, last sequence, state/journal hashes, rule/data/calendar/model versions, RNG states, open orders/reservations/claims, scenario branches, certification status and attempt identity.

Use immutable instrument/entity IDs; tickers and provider symbols are dated aliases. Do not aggregate distinct obligations merely because UI labels match. Unknown enums, missing monetary inputs, infinities, NaNs and unsupported corporate actions fail validation.

## Clock and deterministic replay

Freeze scenario rules, manifest, price/event tape, research packets and provider-independent RNG algorithm/version at season creation. Use distinct named streams for market, research and NPC events, keyed by stable event identity, not number of UI calls. Prefer materialized approved tapes for the initial campaign. Save/load must not reroll a research result, price, borrower recall or investor preference.

The canonical event order is FUND_ACCOUNTING §7. The initial calendar is dated Monday–Friday, starts 5 January 2026 and deliberately ignores exchange holidays. Every elapsed calendar date accrues fees/carry, including weekends. Business-day indexes never replace actual day-count dates.

User actions are accepted at decision barriers; an order must wait for a strictly later eligible tape event. Advance is rejected while required decisions/technical integrity faults remain unresolved. A partner disconnect pauses at the specified safe barrier; no wall-clock penalty silently ages a simulated obligation. Deadline expiry occurs only through a recorded simulation event.

Replay feeds the recorded **accepted command order** and frozen exogenous events to the reducer. Canonical hashing sorts stable keys, represents decimals consistently and excludes wall-clock logs, request timing and UI caches. Concurrent sessions need not produce the same acceptance order across separate runs; once accepted, that order is part of the replay input. Record both economic state hash and event log hash. An incompatible new rules version requires migration/new season, never silent reinterpretation.

First-playable completion is ordinary day21 opening administration after intervening weekend closes; full-season completion is ordinary day61 opening administration. Stop before Monday market/accrual. Report day20/day60 investment results and a separate weekend/settlement bridge. Continuing resumes the next pending phase; remaining debt, fee accruals, HWM, pending returns and LP claims persist. Winddown advances actual remaining events and obligations rather than selling at a stale terminal mark.

## Money, estimates and reconciliation

Use Decimal from validated strings, explicit local precision/context, HALF_EVEN postings and the residual rules in FUND_ACCOUNTING. Prices have at least six decimals; calculations at least twelve; units eight; cash posts cents. Choose exact PostgreSQL NUMERIC scales large enough for intermediate contracts, reject overflow and serialize decimal strings through JSON. Keep cash rounding in domain code: PostgreSQL NUMERIC rounding behavior is not automatically the same as the selected HALF_EVEN policy.

Python's [Decimal documentation](https://docs.python.org/3/library/decimal.html) describes precision, rounding contexts and float-mixing traps. PostgreSQL's [numeric documentation](https://www.postgresql.org/docs/current/datatype-numeric.html) distinguishes exact numeric from inexact floating types. These support the implementation choice; they do not define our fee contracts.

Statistical estimates may use floating point outside the journal. They carry method/window/version/uncertainty and produce advisory target weights. Convert proposals to bounded whole-share orders and rerun authoritative Decimal/resource tests. Never round away insolvency or use solver tolerances as permission to break a mandate.

Separate internal invariant failure from an external reconciliation discrepancy. An invariant failure stops economic transitions. A coherent internal ledger with mismatched independent broker/admin records blocks new risk and certified NAV/dealing; verified mandatory payments/cancels/permitted reductions can proceed under the control policy. Maintain pending, indicative, certified and restated snapshots. Only certified valuations support dealing. A break's source, scope, aging and correction must remain inspectable.

Broker statements and administrator controls must be independently authored or independently computed. Comparing two views of the same function cannot establish reconciliation. Corporate-action control cases include economic versus settled shares, distributions in lieu and exactly-once split propagation. No player chooses a favorable price to resolve a break.

## Concurrent players and persistence

Proposed first implementation: one PostgreSQL transaction locks the season aggregate row for every financial/authority/clock mutation. This deliberately serializes a two-person season and includes its fund and management company. Fixed lock order is season → related entity rows → obligations. Use unique constraints for economic_id and for actor/season/idempotency scope. Recheck current authorizations, restrictions, resource reservations and complete risk vector under the lock before committing.

Persist command result, immutable events, balanced fund/company postings, derived state/version and any outbox record atomically. An internal inter-entity payment either updates both books or neither. No provider or LLM call occurs while holding economic locks. Posting retries never execute an external side effect again. An expired/revoked actor cannot retrieve protected results by recycling a key.

Version conflicts return current version and an inspectable reason; do not silently resubmit a changed financial decision. Worker duplicates replay the committed result by economic identity. Keep bounded deadlock/serialization retry handling, with one immutable request; publish notifications only after commit. Client optimistic UI cannot assert an executed fill.

[PostgreSQL row-lock documentation](https://www.postgresql.org/docs/current/explicit-locking.html) supports this narrow mechanism. It is not evidence of implemented race safety. Test independent connections with barriers for cancel/fill, advance/advance, subscription/fee, collateral/cover, payroll/fee receipt and competing authority reservations. Report actual lock/isolation settings and outcomes. Fine-grained locking is deferred until measured need.

## Information integrity and three modes

| Mode | Market/evidence authority | Time/fills | Claims and restrictions |
|---|---|---|---|
| Synthetic campaign: launch | Authored fictional tape/evidence plus frozen seeded branches | Paused simulated clock; explicit executable events and capacity | Reproducible house economy; teaches decisions, not actual strategy performance |
| Historical replay: FF7 | Licensed immutable as-of snapshots; point-in-time universe, revisions/actions/calendars | Historical event resolution limits fills; daily data cannot invent intraday order priority | Historical prices, **simulated** fills/financing/LP behavior. Cannot claim realistic historical borrow from present-day availability |
| Future live-data sandbox | Entitled server adapter producing timestamped cached observations | Observational paper sandbox; explicit delay, outage and stale policies; no external execution | Separate from ranked campaign; no real-money orders, no assumed exchange redistribution rights or retroactive changing of completed outcomes |

Filter by information availability at every query/export/chart/AI boundary, not only the front-page research list. A period-end figure published later stays hidden until evidenced availability. Corrections append revisions with later available_at; missing publication history cannot be filled by assigning the economic period end. Use unadjusted prices plus explicit actions for accounting; adjusted returns can be an identified analytical series, not an additional source of dividends.

Preserve delisted instruments, dated classifications, symbol changes, universe membership and vintage fundamentals before making historical claims. Screen benchmark/factor series for publication lags and revisions too. Forward/nearest time joins are dangerous when they can select future observations. Entity mappings and alternatives such as SEO estimates need their own dated evidence.

Provider imports happen outside a locked campaign. Validate schema, units, timestamps, entitlements and bounds, then approve an immutable dataset. Real secrets stay server-side. Define failure classes (unavailable, forbidden, stale, malformed, partial, rate-limited, budget-exhausted, ambiguous charge). No silent zero filling, hidden current-data replacement or automatic retry of an uncertain charge. A provider failure cannot change existing campaign economics; an entitled live sandbox can pause affected research/quotes with visible quality state. SEO/marketing integration is excluded from the current plan.

## Scenario interface and bounded AI

A scenario manifest declares prerequisites, starting certified balance sheet, public briefings, hidden but fixed event schedule, branch predicates, action space, deadlines, authored control records, expected invariant checks and recovery/winddown triggers. Branches may respond to disclosed behavior (late report loses trust); they cannot secretly make the market punish whichever stock was bought. Each consequence references cause IDs. Counterfactual debriefs rerun a fork with stated changed decisions and limits, never invent a reassuring alternative outcome.

Deterministic rules own prices, fills, margin, restrictions, fees, LP rights, cash movements, authority, deadlines and scores. NPC trust is a bounded transition table driven by events; prose is explanatory. Machine learning is optional for a defined forecast/diagnostic with chronological splits, lag-safe preprocessing, baselines, calibration and held-out evaluation. A complex model losing to a baseline is rejected.

An optional LLM tutor receives only sanitized permitted facts and may explain them with citations. An optional committee critic can point to risk metrics or missing thesis evidence, never approve an exception. Store outputs when they affect what a player saw. Failures fall back to deterministic text, not made-up figures. Hidden tape, keys, mutation tools and external browsing are absent from historical opponent contexts; memorized historical knowledge remains an explicit fairness limitation. No AI feature is needed to finish FF5/FF6.

## Implementation and evidence gates

Planning revision 2.2-M1: FF2c explicitly owns the in-process session runner, atomic reducer composition, narrow LP/firm closure and independent Case1 controls for arbitrary allowed human paths; FF3a connects human command authority before FF3b. FF4a persists the same semantics. FF6a generalizes independent controls/restrictions/restatements. FF7a must prove one actual shared-engine historical scenario, not only ingestion. Exact work packages and recovery-tail coverage gates are in MILESTONE_PLANS; no additional distributed services are proposed.

v2.2 sequencing supersedes the broad gates below: IMPLEMENTATION_PLAN splits FF0a–FF6c and inserts FF3b internal human challenge. This section's evidence remains required; no engine exists.

Freeze schema and one hand-authored event trace at FF0. At FF1–FF4, prove ledger/series, execution/treasury, authority races and LP/firm contracts before building rich views. FF5 must connect these through the complete first two chapters. FF6 proves campaign endings, recovery, versioned balance experiments and actual two-person play. FF7 earns each optional library/provider/model independently.

Required evidence includes independent Decimal oracles, same-input replay hashes, future-data mutation tests, shuffled retry/race tests, fault injection before/after transaction commit, independent reconciliation breaks and successful checkpoint resume. Scenario manifests and prose do not satisfy these engine tests. The current repository still contains no implemented simulation runtime.

## v2.2 exact implementable contracts

Module calls remain in-process. Clock selects `(calendar_date,phase,event_index)`; scenario returns immutable inputs for that position; information returns only authorized observations; execution proposes fills/obligations; risk evaluates candidate prefixes; accounting returns balanced batches; investor service produces series/flow claims; company returns earned-fee/payroll events. The coordinator applies all effects once or none. Each module accepts immutable typed values and returns `events, state_delta, explanations`; no module commits a DB transaction. Reporting is a projection. Calendar/authority/accounting are dependency roots; scenario/market/OMS depend on their types, not on UI/provider modules. Clock advances only with current ready digest; game rule failures return reason codes; invariant faults stop transitions.

**Exact numeric protocol.** Local Decimal context precision40, ROUND_HALF_EVEN; trap InvalidOperation/DivisionByZero/Overflow/FloatOperation; never construct money from float. Money posts scale2; reference/fill prices scale6; investor units scale8; HWM/unit valuation scale12; rates scale12. Intermediate calculations retain context40 until specified posting boundary. Persist accrual residuals scale24 by entity/series/obligation/currency/rate-version, using `previous_residual + today_unrounded_charge − today_posting`; scale24 quantization is explicit HALF_EVEN and bounded error <=0.5e−24 per calculation. Carry the old rate bucket's residual explicitly to its successor on a rate change, never discard it. Quantize price first, multiply quantity, quantize cash once, derive cost from reference notional minus cash; never post slippage twice. Unit conversion truncates toward zero before stable largest-remainder pro-rata assignment without exceeding held/requested units; one-cent leftovers follow series-ID order and conservation, never make negative units. All independent oracles use this exact ordering.

DB fields: money NUMERIC(24,2), price(24,6), units(24,8), HWM(28,12), rate(18,12), residual(38,24). Validate field bounds and quantize in domain before DB write; DB coercion is not the rounding policy. Fail numeric overflow with no commit. Arithmetic maximums are checked before operations. No claimed economic certification from a type validator.

**Canonical bytes.** UTF-8 JSON, sorted object keys, compact separators, no BOM, no NaN/Infinity, no escaped non-ASCII requirement (`ensure_ascii=False`). Every decimal is a string with its field's fixed scale; normalize negative zero to positive zero, no exponent form. Integers are JSON integers. Event arrays retain sequence order; identity sets sorted by immutable ID; distinguish null from missing. Dates YYYY-MM-DD; simulated timestamp includes date/phase/event index; wall-clock audit timestamps normalized UTC with six fractional digits but excluded from economic hash. SHA-256 of canonical bytes; separate state/event/tape/rules/commands/control hashes. Exclude caches, delivery notifications and wall-clock timing; include residuals, settled/pending obligations, loan lots, order/resource state, next phase and certified-status/history references. Any excluded field must not affect future economics. FF0b freezes test-vector bytes and hashes, including1.0 represented as the declared scale and residual restore midway through accrual.

**Coordinator ordering.** Authenticate current season membership first (even old retries). Under READ COMMITTED acquire one season row `FOR UPDATE`, spanning its fund and firm. Look up `(season_id,actor_id,idempotency_key)` with normalized immutable payload hash including command type/expected version/policy references. Identical committed retry returns original result even if expected version now stale or market changed; current access denial conceals result without undoing prior economics. Different payload is IDEMPOTENCY_CONFLICT. For a new key check expected version, current authority/restrictions/resources, then apply effects/journal/result/outbox and increment version atomically. Accepted commands and domain rejections are stored consistently; infrastructure failures roll back and are retryable. Stale-version rejection is final for that key; rebase uses new key. Unique economic-ID constraints protect fills/accruals/dealing/payment. Bounded DB deadlock retries preserve payload/key; exhausted retries report unavailable, never partially commit.

**Readiness.** Ready binds to window ID, state version, proposal/resource-plan digest and actor. A material mutation revokes both readiness marks; metadata-only chat does not. Advance requires distinct ready partners on the same digest and records accepted sequence. No silent liquidation from wall-clock absence. An expired simulated deadline arises only from advance; missing partner holds at a safe barrier. Retry of successful advance returns same next phase, not an extra day.

Financial/plan mutations increment economic `state_version`; readiness/chat/rejected-command bookkeeping increments only `administrative_revision`. Expected versions and ready digests reference economic version. Two sequential Ready commands can endorse the same plan and advance once; an intervening economic mutation invalidates both marks.

Residual example, $1m×2%/360: date1 posting55.56/residual−0.004444444444444444444444; date2 posting55.55/residual0.001111111111111111111112; date3 posting55.56/residual−0.003333333333333333333332, using scale24 recurrence. Halfway0.0000000000000000000000005 rounds0 at scale24; error equals0.5e−24. These are reference values for FF0b, not engine outputs.

**Failure/recovery surfaces.** Provider import never occurs inside this transaction; approved immutable snapshots only. Missing/unsupported tape record is SCENARIO_INVALID; no guessed price. External controls block certification/new risk while verified obligations/reductions continue; internal ledger integrity fault halts economics until repair. Shared scenario tapes stay branch-independent; path-specific control ledgers are independently authored, not copied from the reducer. Synthetic launch, licensed historical replay and observational live sandbox remain distinct modes; no economic network/LLM calls. Optional tutor evaluation uses20 curated permitted fact packets, fact-source accuracy, zero forbidden mutation, leakage prompts, comprehension versus deterministic templates and cost; adoption requires improvement, not fluent prose. AI remains deferred and is unnecessary for initial game.


---

Source: `docs/IMPLEMENTATION_PLAN.md`

# Dependency-aware implementation plan v2.2

7 October 2026. All application milestones pending. The local checkout has documentation tooling, not the reportedly completed foundation/26 tests. DESIGN_REVIEW_V2_2 records reconciliation; SCENARIO_CONTRACTS freezes challenge schedules; IMPLEMENTATION_HANDOFF owns the exact next task. The old roadmap remains in Git history, not authoritative.

Planning revision 2.2-M1 expands **all 20 milestones through final FF8** in [MILESTONE_PLANS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\MILESTONE_PLANS.md). Each package defines purpose, input evidence, module/file ownership, ordered tasks, deliverables, independent acceptance, proposed verification, failure behavior and completion/stop gate. [PLAN_REVIEW_AND_DECISIONS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\PLAN_REVIEW_AND_DECISIONS.md) records this pass's corrections and unresolved decisions with their due milestone. This table remains the navigation/dependency summary, not the complete task instructions.

## Release definitions and sequencing

The smallest internal end-to-end experiment is Case1's warm-start crisis: two roles, research/borrow choice, signed/delegated reduction, settlement, Tactical dealing, separate firm cash and causal report through day21 administration. A simple local two-role interface follows pure economics. Label it **internal challenge prototype**, not first release or evidence of secure multi-user hosting. It can invalidate tedious or one-sided gameplay before broad content work.

**First playable release (FF5)** is the ordinary zero-position day1 launch through day21 opening administration: two authenticated human identities, three LPs, four tradable instruments, two chapters, scarce evidence/contingency, long/short/financing, investor payment, separate firm bills, disagreement/pause/resume and debrief. Require two defensible successful policies, an explainable recovery path, independent accounting/replay/concurrency evidence and actual two-human playtests. Warm starts cannot replace that opening campaign. Staffing/fundraising previews may wait.

**Full initial game (FF6)** is six chapters/60 business days through day61 administration, up to twelve instruments, standard fundraising and useful staffing tradeoffs, all three challenges, restrictions/control incidents, conditional Renewal/Survival/Winddown/Default/Company Failure, security/restore/balance/human-study evidence. No provider, ML or finance framework is required. Release labels need evidence, not estimated dates.

Ledger and dated obligations come first because each interesting choice changes claims, cash or authority; fake UI balances hide affordability. Authoring comes before economics so builders do not invent outcomes. The first human experiment follows only necessary Case1 mechanics; catalog breadth follows evidence of agency.

## Small verifiable milestones

Each row requires a bounded diff, assumptions, actual commands/results with runtime/rule/tape/command/control hashes, updated handoff and no unreported failures. Paths under backend/frontend/tests are proposed. Row acceptance plus this evidence record is its definition of done. Dependencies mean demonstrated output, not a checked box.

| ID / purpose | Inputs / prerequisites | Outputs / affected modules | Acceptance / definition of done |
|---|---|---|---|
| FF0a: compile one challenge, no engine | Current rules, Case1 complete authoring schedule, old isolated oracles | compiled Case1 fixture, three actor-tagged scripts, independent daily oracle, coverage/hash report; contracts/loader and rejection checks | X01–X07 in handoff: complete12–21 tape/openings/series/authority/residuals, specific missing/invalid rejection, full-path independently calculated balances. Schema validity is not playability |
| FF0b: exact wire/replay values | FF0a, numerical conventions | frozen schemas/canonical vectors; contracts/serialization | V22–V24 string decimals, finite bounds, negative zero, HALF_EVEN, residual round-trip, expected canonical bytes/hash; no implicit DB rounding |
| FF1a: balanced immutable journal/lots | FF0a, FF0b | accounting, fund/firm openings, obligations/lots/reversal | A01–A06,A08–A11,A14–A15; Case1 opening balances; deliberately wrong balanced event not called reconciled; separate entity journals balance |
| FF1b: dated series fees/carry | FF1a + dated oracle worksheet | accounting/series/calendar, residual persistence and HWM | V01–V05,V08–V11,V20; every date once, Friday/Monday borrow endpoints; reversible provision never company receivable; partial redemption conserves claims |
| FF2a: future-event execution/settlement | FF1b + Case1 tape | market/OMS/borrow/treasury, whole-share budgeted partial fills | E01–E05,E08–E09,E12,V25; exact costs/cumulative impact, unsettled top-up, retained collateral, failed settlement; no duplicate borrow/cash |
| FF2b: risk/financing/deadlines | FF2a | deficit vector, replacement transfer, voluntary/forced queues | A22,V26,V27; all constraint prefixes; timely transfer/late rejection; voluntary cure before forced margin, real shortfall after costs; forced fills can leave deficits |
| FF2c: narrow Case1 payment/firm lifecycle | FF1b, FF2b | pure session runner/checkpoint, Tactical dealing/payment, baseline payroll/cure and independent Case1 controls | V02,V06,V08,V09,V16,V18 and dated full oracle; actual claims/payment21 and allowed non-scripted controls, not scripted balance edits. General gates/subscriptions deferred to FF4b |
| FF3a: two-role command authority | FF2b + frozen commands | governance/reducer, ready digest, immutable signatures/idempotency | C02–C07,C09,C13–C16 pure tests; distinct consent, edits reset readiness, no double resource spend. No PostgreSQL safety claim yet |
| FF3b: early human crisis experiment | FF3a, FF2c + economic scripts meet independent oracles | minimal local CLI/one-page desk, causal report/checkpoint; controlled two-role identities | Two humans resolve recall/payment and failure recovery; role choices/wait/confusion recorded. Exact save/replay. Not production auth or first releasable game |
| FF4a: persisted authority/API skeleton | FF3b + transaction contracts | PostgreSQL adapters/coordinator/uniqueness/outbox/migrations; minimal FastAPI | Real separate-connection C01,C07–C10,C13–C16 races and crash rollback/outbox; allowed result pairs/journal counts; versions pinned when needed |
| FF4b: standard dealing/firm obligations | FF1b, FF4a | notices/gate/escrow, payroll/receivables/distress, cross-entity transfer | L01–L12,V06,V13,V15–V16; units/cents reconcile; redemption cannot be refused for leverage; no provisional-fee payroll; payment NAV-neutral |
| FF5a: author zero-position opening | FF3b observations + FF4b | complete1–21 four-instrument tape/evidence/controls, two success + failure scripts | Authority permits actual initial trades; each role has two consequential choices; no130%-warm-start shortcut; independent daily outcomes and coverage; retuning creates new version |
| FF5b: first playable UI/identity | FF5a, FF4a, FF4b | Next.js desk/committee/portfolio/operations/debrief; two-human rooms, polling |20-day arc/payment bridge with users; cross-fund/revoked identity denied, partner absence pauses, no future chart/export, keyboard/error/reduced-motion checks |
| FF5c: certify first release | FF5b | financial/replay/race evidence and human observations | Independent totals, replay/restore hashes, playtest gates; unresolved major agency/comprehension defects block release.40–60min target measured, never assumed |
| FF6a: compile Cases2/3 and operations | FF5c + authored schedules | compiled tapes/oracles, independent arbitrary-path controls, restrictions/correction/restatement and offer predicates | A22,V12,V14,V28–V30: all issuer limits, gated units paid61, balanced wrong report detected, deadline loss retained, dominated hire excluded |
| FF6b: full campaign/endings | FF6a | complete1–61 campaign, prospects, useful staffing, termination | Two feasible survivor policies; five ending labels preserve liabilities; funded continuation forecast; hire trades concrete task capacity for cash, not alpha |
| FF6c: full release evidence | FF6b | held-out balance study, human study, restore/security/load evidence | Baseline/exploit policies; no save reroll/trust spam/terminal gate escape; V31–V32 winddown; hardware/load measured before claims; failed/undefined cases published |
| FF7a: optional historical replay | FF6c + specific licensed dataset requirement | immutable/as-of read-only adapter, one historical scenario using shared economic engine, independent oracle, justified dataframe/calendar tool | Rights/retention/export, vintage/calendar/actions/era settlement, resolution-safe fills and actual one-case replay; failures preserve campaigns, no invented historic borrow; reject nonreproducible data |
| FF7b: optional advisory/AI | FF6c; FF7a additionally if historical data needed; measurable use | one diagnostic/optimizer/tutor and protocol | Baseline/holdout/calibration/errors/cost evidence; no mutation authority; remove if no utility. No SEO/marketing |
| FF8: selected-extension planning gate | FF6c + explicit one new user story and relevant evidence | concrete extension SPEC/PLAN/ACCEPTANCE and dependency/rights/cost decision; no automatic build | Complete lifecycle/permissions/failure/independent acceptance and bounded implementation steps; unknown future products are deferred, not initial-release criteria |

FF1/2 are pure in-process work. PostgreSQL arrives at the multi-user persistence boundary, not as authoring prerequisite. FF0a has one scenario and no financial reducer, UI/API/database. Subsequent work locks supported dependencies when needed; no mass installation.

## Experiments and evaluation

Use independent Decimal worksheets and claim identities, not expected values copied from tested functions. Replay records commit/runtime/rules/tape/commands/control hashes and canonical state/economic-event hashes. Races record immutable requests, permitted result pairs, journal/reservation counts and failure boundary. Mutate hidden prices/revisions without changing past observations.

Enjoyment is a separate planned study in ACCEPTANCE_TESTS: novice and financially literate pairs, role agency/comprehension, facilitator intervention distinguished, raw anonymous observations, versioned iteration. No study has run. A challenge can disprove the premise; more staffing/instruments cannot substitute for repair.

Compare cash/defensive, simple diversified, liquidity-aware and concentration/gate/trust exploit policies on identical tapes, then a held-out version. Report completion/unpaid claims/return/drawdown/company cash/role decisions; do not optimize one seed or call game returns empirical alpha. Complexity earns no credit without independent evidence.


---

Source: `docs/ACCEPTANCE_TESTS.md`

# Acceptance contracts v2.2

v2.2 supplements below supersede ambiguous ordering/scenario-success assumptions. All application cases remain pending. See IMPLEMENTATION_HANDOFF for X01–X07 authoring/loader cases; none is a working test here.

Planning revision 2.2-M1: MILESTONE_PLANS maps these cases to all 20 full work packages. Required acceptance of an unavailable later subsystem is not claimed early: fee transformations atFF1b are primitives, actual Case1 dealing/payment/run composition atFF2c, pure authority atFF3a, real DB races atFF4a, authenticated two-user UI atFF5b and human release evaluation atFF5c/FF6c. Independent narrow Case1 controls precede arbitrary human action; fixed expected script records alone cannot certify another path. Winddown V31–V32 requires authored tail coverage and actual liquidation. Historical replay atFF7a requires a full shared-engine case, not schema-valid import.

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
| A07 | Settled borrow notional $5,000 at5% for one calendar accrual date | $5,000 × .05 /360 with carried residual; weekends accrue, unsettled locate does not; expense/payable reconcile |
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
| L06 | Isolated annual full-series crystallization:100 units, HWM100, pre-incentive NAV/unit110,20% rate | Provision200; net capital10800; at Dec31 convert once to fixed payable, HWM108. Ordinary chapter close only recomputes provision |
| L07 | Series after L06 falls90 then recovers108 | No second incentive fee before a new gain above108; returning to HWM is not profit eligible again |
| L08 | New subscription after earlier loss | New series has its own entry/HWM; new investor does not inherit another series' fee holiday |
| L09 | Partial redemption plus new subscription | Crystallize only accepted units pro rata; surviving HWM unchanged; annual crystallization takes precedence if same date; newcomers avoid prior-period fees |
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
| C12 | Independent external reconciliation mismatch versus internal invariant failure | External break blocks new risk/certified dealing while verified payments and allowed reductions may proceed; internal integrity failure pauses economic transitions; preserve original evidence and linked correction |

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

## v2.1 regression contracts: corrected realism

All cases remain **pending application implementation**. The packaging validator only checks independent arithmetic/reference consistency where stated; it does not execute the behaviors below.

| ID | Given / action | Required result |
|---|---|---|
| V01 | Series A net108000/provision2000; B net100000/provision0/HWM120,1000 units each; common gain21000 | Participation110000:100000 gives11000:10000 gain; resulting net A116800/B110000; never allocate using108000:100000 |
| V02 | U1000/H100/B110000/F2000/N108000; redeem250 | Fixed incentive500, redemption27000, survivor U750/F1500/N81000/H100; crystallization itself does not double-expense |
| V03 | Jan5 opening25m; isolated fixed fee base for three dates | ACT/365 management fee sum3082.19 with residual; no prelaunch fee; recurring production base changes, so do not multiply constant-base oracle across a season |
| V04 | Friday short sale settles Monday; later Friday cover returns Monday | Ordinary borrow starts first Monday, runs through later Sunday, stops at settled Monday return; locate/unsettled sale does not itself charge ordinary borrow |
| V05 | Closing settled debt3m at6%; borrowed reference notional1m at2% | Calendar-date charges500 and55.555555… before monetary residual rounding; accruals remain liabilities until invoiced/paid |
| V06 | NAV25m/L27.5m/S5m, then deal5m at unchanged marks | Gross130%→162.5%, net90%→112.5%; cash payment later makes no second NAV/ratio change |
| V07 | NAV25m/L25m/S5m; cover all short with100 cost | Net becomes100.0004%: cover-only plan cannot pass100% net mandate merely because gross falls; require feasible safe prefixes or explicit forced-breach record |
| V08 | U1000/H100/B110000/F2000 at ordinary day20/40/60 | Provision is reversible; no annual crystal, no company performance receivable/cash. Partial redemption crystallizes only its share |
| V09 | Friday day60 close then Saturday/Sunday then Monday day61 opening | Two ordinary weekend accruals, no Friday repeat or full Monday accrual; process due obligations; save next phase before Monday market. Resume exactly once |
| V10 | 100 long/short shares,2 distribution,50→48 ex-date mark | Long price loss200 offsets receivable200; short gain200 offsets expense200. Payment and adjusted data cannot duplicate income |
| V11 | Integer split with economic/settled/borrowed shares, pending deliveries, orders and locates | All relevant quantities/prices change once; preserve value and cost basis; reject unsupported fractional corporate actions |
| V12 | Internal journal balances but administrator/broker record reveals missing liability | Detect external break, withhold certification/dealing, link correction/restatement and recompute fees; balancing alone is insufficient |
| V13 | Known future redemption, contingent subscription and unexecuted sale | Forecast separate scenarios; reserve dated obligations; do not count contingent receipts as settled resources or spend today's obligation against tonight's admission |
| V14 | Restricted/security-conflict evidence arrives before partial fill | Recheck current restriction and authority at each fill; information cannot be used by an LLM to bypass controls; policy governs allowed exits |
| V15 | Two human partners share one investment fund | Every fill belongs100% to the fund; sleeve attribution cannot create personal LP ownership. Multi-fund/block allocation is deferred |
| V16 | Payroll due and a fund-to-firm fee receipt retry/race | Season-serialized transaction updates each balanced entity exactly once; fund cash/provisional incentive cannot directly pay firm salaries |
| V17 | Provider import changed/revised after campaign starts | Frozen campaign unchanged; new dataset version only; current observation cannot overwrite prior available-at vintage |
| V18 | Same fixed rule/tape/accepted commands after restore | Same event and economic hashes; excluded wall-clock/cache/notification ordering cannot change economics |
| V19 | Scenario2 gate and full-pay branches on identical tape | Both respect whole-share capacity and actual costs; re-evaluate gate amount after execution-cost NAV, not a rounded5m target |
| V20 | Scenario3 corrected short-dividend liability and performance provision | Gross liability200000, provision reverses40000, net NAV27m→26.84m; company cannot recognize reversible incentive as revenue |

Scenario branch prerequisites and exact reference arithmetic are in SEASON_SCENARIOS and its fixtures. Do not claim all branches pass by checking only their expected-output JSON. Implement an independent loader/engine, test actual outputs and retain failure/default branches.

V21: equity issuer limits apply to individual equities; each approved diversified ETF uses its separate absolute50% cap in either direction. Case3's short BEAM remains subject to gross/net/factor/borrow/financing tests. Neither applying an unintended8% ETF cap nor treating ETF exposure as unlimited is valid.

## v2.2 precise independent acceptance cases

| ID | Given / action | Independent required observation |
|---|---|---|
| A22 | Case2 normalized pay-all/gate branches with corrected six2.5m equities plus2.5m BOND/8m BEAM | All issuer/sector/ETF/gross/net/margin/credit/cash constraints independently checked; largest equity2.5m /18,995,800 <15%, with dated carry rechecked. Old five3m basket must fail even though gross/net pass |
| V22 | Decimal serialization/DB round-trip | Fixed declared scales, positive zero, no exponent/float/nonfinite/overflow, HALF_EVEN ties1.005→1.00/1.015→1.02; field bounds rejected before commit |
| V23 | Fee thirds/residual checkpoint mid-accrual then restore | Three $1m×2%/360 dates total166.67 after residual; uninterrupted and restored balances/residuals/canonical hashes identical |
| V24 | Same typed state with reordered object keys, array event order, audit timestamps | Key order/audit time do not change economic hash; changed event order/residual/next phase does. FF0b pins independent bytes/SHA256 test vectors |
| V25 | Sell100 shares at50 unsettled, mark55, later cover40 at56.056 (reference56), return next business date after mark60 | Initial receivable5000 earmarked; mark55 needs500 top-up, not5500 extra. At cover frozen pending target2240; remaining60 active re-mark. Return releases2240 against2242.24 cover, needs2.24 extra; pending borrow fees use actual marks until return. Failed return keeps loan/cash; split preserves aggregate retained cash |
| V26 | Case1 accept1,250 replacement before14 EXEC_B versus after cutoff | Timely transfer15 cancels matching recall/no economic short change; loan total unchanged;40% starts15,2% ceased for subset. Late rejected/no signature or locate can cure; deadline buy-in still possible |
| V27 | Margin shock16, valid voluntary sale queued before next event, no overdue recall | Execute valid voluntary cure first at eligible event; zero residual call means no forced fill. Partial insufficient cure uses remaining capacity for forced action; no fabricated fill on halt. Due recall remains first |
| V28 | Case2 gate and pay-all dated scripts through61 | All dealt claims paid; deferred units reprice at60 and fully paid61; no phantom fixed deferred dollars; initial195,800/197,976.96 cash is isolated, not accrued output. No-sale branch can breach leverage without necessarily defaulting if permitted credit suffices |
| V29 | Case3 balanced wrong opening + independently truthful broker/admin record |200k expense/payable,40k reversal,26.84m corrected opening NAV; old report retained, correction once. New dated fees/ALTO gain alter later NAV; certificate cannot copy opening26.84m indefinitely |
| V30 | Case3 diligence/admit versus public-research/decline | Both can meet honest-report/solvency goal; admission issues new series and zero company cash. Missed35 certification loses prospect even if later corrected. Dominated hire not counted as independent strategy |
| V31 | Joint winddown, executable capacity and solvent fully settled closing assets | Actual liquidation/cost/carry, final certified participation termination, surviving provision fixed once, units burned/final claims paid; scored endpoint alone does none of this |
| V32 | Winddown halt/unreturned borrow or NAV<=0 at ten-day horizon | Preserve residual assets/claims/fees/collateral, UNRESOLVED_WINDDOWN/default classification; no stale terminal fill or invented payable forgiveness |

Concurrency case initial states and permitted pairs (real PostgreSQL at FF4a):

- C13: version10, two distinct new commands both expecting10 and competing for the same finite reserve. Barrier releases two connections. Exactly one commits version11; other VERSION_CONFLICT, zero loser journal/reservation/outbox economic effect. Rebase with a new key may still be rejected for resources. Repeat100 trials per declared environment; trial count is scenario evidence, not formal universal proof.
- C14: same actor/key/payload expected10 repeated after original committed11 and current state advanced12. Both current authorized retries return the original committed result; no fresh risk test/fee/fill or version increase. Changed payload yields IDEMPOTENCY_CONFLICT. Revoked/cross-season actor denied without revealing original result; original economics unchanged.
- C15: cancel versus fill share same order/version and event. Allowed pairs: cancellation accepted then fill no-op, or fill committed then cancellation affects remainder only. Filled quantity/capacity/journal identity exactly once, released reservation equals actual unfilled quantity; no negative remainder. Crash precommit leaves no effect; postcommit retry returns stored result/outbox can deliver twice without economic duplication.
- C16: two ready partners against digestD/version10, then material order/reserve mutation to11. Old-ready advance rejected. Both ready on new digest, duplicate advance one phase only; accepted log fixes sequence. Metadata chat neither changes economics nor authorizes advance.

## Planned gameplay/evaluation protocol (no results yet)

FF3b recruits at least three two-person pairs for internal challenge; FF5c at least six pairs (three novice-finance pairs and three with finance familiarity), consented observation without collecting financial/personal data. These are practical pilot sample sizes, not statistical-power claims. Counterbalance role assignment; independent observation tracks timestamps, command IDs, role, available evidence, rejected actions, facilitator help and causal effects. Target chapter duration20–30min, opening40–60min is a hypothesis; publish median/range rather than claim tested target.

Predeclared provisional release criteria: each partner makes at least two consequential choices changing exposure/resources/information/capital outcomes over opening arc; no partner spends >25% of decision-window time waiting solely for the other's required approval; both explain cash versus NAV, next binding deadline and one immediate/delayed consequence; after failure both identify one available recovery or honest winddown without financial coaching. Ask separately whether each wants another chapter (1–5) and why; target median>=4 while retain dissent and confused cases. Automated scripts cannot satisfy human gates. Unresolved repeated role starvation or misunderstood mandatory obligations blocks release; revise options/info/order, not add dashboards to distract.

Evaluate research usefulness with matched authored cards/public-only/wait scripts and observations of changed ex-ante choices; no bonus for hindsight correctness. Evaluate dominant strategies with versioned cash, diversified, liquidity-aware, concentrated gambler, trust spam, repeat gate and last-day exploit policies on identical tapes, then held-out versions. Report all outcomes, unpaid claims, fee/firm/LP effects and worst paths; no single-seed balance claim. Counterfactual replay changes one command under same tape and availability; it establishes mechanical model effect, not empirical causal skill.

Evidence file per run records commit/runtime/command/schema/rules/tape/control hashes, expected/observed totals, source of oracle, pass/fail/pending, and limitations. Correctness/replay/race/information/scenario/human evidence are separate gates. No experiment in this section ran during planning.


---

Source: `docs/DECISIONS.md`

# Decision log — v2.1

These are proposed product/engineering decisions, not claims of implemented behavior. Approved scope: whole-plan redesign and file update, 6 October 2026. Astra/extra-high led this critical realism revision;17 repositories were checked against actual source/license snapshots.

| Decision | Current choice | Why / consequence |
|---|---|---|
| Product | Cooperative investment-business strategy game | Portfolio performance, investor obligations, financing and firm survival interact |
| Time | 60 business days, six chapters, pause/resume | No real-market attendance; preserve day-level financial effects |
| Initial scale | $25m outside capital; $300k separate firm cash | LP and business choices become meaningful; managers are not the only investors |
| Core strategy | Long/short equities and broad ETFs | A bounded but recognizably hedge-fund-like strategy |
| Governance | Joint sleeve charters; independent consent for exceptions | Preserves two-person control without approving every routine click |
| Core release | Fees, flows, borrow/margin, runway, crisis and debrief | Optionalizing these produced a shallow trading app |
| Scope sequencing | Complete two-chapter opening arc before six-chapter campaign | Validate fun before multiplying content |
| Financial authority | Pure domain + PostgreSQL transactions + immutable journal | Reconciliation, reproducibility and concurrency correctness |
| Rules authority | Versioned scenario/contract configuration | House rules are explicit; no hidden market manipulation |
| Data | Synthetic authored fixtures first | Deterministic, no fees/credentials, avoids memorized historical outcomes |
| OpenSEO | Assess every-app/open-seo at pinned snapshot; optional research adapter | User supplied repo name only; no unsupported assumption it is a market engine |
| Upstream reuse | Adapt bounded patterns; no wholesale fork/code copied yet | Keep finance ownership and avoid unrelated SaaS dependencies |
| AI | Optional explanations/baselines after game | No LLM control over financial truth, approvals or scoring |
| Workflow | One builder, bounded review | Astra/extra-high was explicitly requested for this redesign, not perpetual delegation |

## v2.2 accepted decisions,7 October2026

Planning revision 2.2-M1: accepted all 20 detailed work packages through FF8, explicit pure integration/independent Case1 controls before human experiment, winddown-tail authoring gates, generalized6a controls/restrictions, end-to-end7a historical replay and a bounded8 extension-selection gate. PLAN_REVIEW_AND_DECISIONS is the current due-decision register; no new dependency or application feature implemented. Standard-library validation selected forFF0a. Prior planning diff preserved; commit/push explicitly authorized by the latest user instruction.

DESIGN_REVIEW_V2_2 records every independent financial/gameplay/engineering finding and rationale. Retain the connected economics and modular monolith. Correct Case2 issuer basket; extend gated payment horizon61; fix replacement cutoff/transfer, retained pending-return collateral and voluntary-before-forced margin ordering. Remove active dominated Case3 hire; retain its arithmetic as teaching forecast. Add useful operating commands, exact precision/hash/retry/readiness, bounded termination, early human prototype and small milestone gates. Next is FF0a authoring/schema-loader only, not full app scaffold. SEO/marketing excluded; old row/assessment below is historical evidence, not active authorization. Release/balance/fun remain unproven.

## Superseded defaults

Original 30-day/$100k equal-manager-capital season, strict long-only release, universal per-ticket partner approval, and postponement of fees/redemptions/shorts to an optional final milestone are replaced. The old arithmetic fixture remains a deliberately small primitive reference; it is not a campaign configuration. Full original docs remain recoverable from Git history before this revision. Current generated Word/Markdown bundles must be regenerated together.

## Still open before implementation

Runtime/dependency pins, auth SDK, database migration tooling, concrete API/schema validation, complete authored price tape, calibrated score/LP/broker parameters, playtest results, exact historical data rights, provider entitlements, hosting/budget and ML target. Resolve at the corresponding gate, not by inventing availability. Fund/accounting rule conflicts must be settled before code.

Log future changes with date, rationale, affected rule/data versions and acceptance cases. Do not change a live season's rule version in place.

## v2.1 corrections and tradeoffs

| Decision | Contract now | Reason / affected checks |
|---|---|---|
| Fee cohort participation | Opening net plus reversible performance provision | Avoid unspecified redistribution between fee-accruing cohorts; V01 |
| Calendar and day count | Jan5–Mar27 synthetic Mon–Fri; calendar-date fees; management ACT/365, borrow/debit ACT/360 |252 is not a universal accrual year; V03–V05 |
| Incentive timing | Annual Dec31 plus pro-rata dealt redemptions; survivor HWM unchanged | Separate fund provision, fixed manager receivable and cash; V02/V08 |
| Endpoint | Ordinary day21/day61 opening admin, after intervening weekend accruals | Preserve obligations without artificial frozen-market carry; V09 |
| Reductions | Validate whole risk vector and feasible sequential fills | Covers can raise net; redemptions shrink denominator; V06/V07 |
| Controls | Independent simulated broker/admin records and certified NAV | Balanced internal journal can still be wrong; V12 |
| Corporate actions | Cash distributions and integer splits; reject unsupported imports | Enough lifecycle depth without full tax/claims machinery; V10/V11 |
| Dependency ownership | Original deterministic kernel, no trading framework in FF5/FF6 | Avoid duplicate clocks/ledgers; library review records alternatives |
| Research stack | Staged pandas/calendars, optional DuckDB, then justified CVXPY/statsmodels | One tool for each demonstrated need; no mass installation |
| Role experience | Automate routine work, expose exception decisions and causal recovery | Meaningful operations role requires tradeoffs, not signoff volume |

The changed contracts supersede corresponding v2.0 descriptions, not Git history. Industry examples motivate mechanics; broker coefficients, LP windows, expenses and trust rules are fictional contracts. Remaining uncertainty includes scenario difficulty, player comprehension, provider rights and release compatibility; none is established by this documentation review.


---

Source: `docs/CLAUDE_HANDOFF.md`

# Claude handoff: FundForge v2.2

7 October2026. Planning only. Original v2.2 review entry HEAD `51eda0c1aa806e0c9f94b7e2527a013b4dedb77f` was clean; this continuation entered its preserved planning diff. The user requested publication of the completed plans; see PROGRESS for actual publication evidence and inspect current Git state before editing. Repository visibility was not freshly verified. Local tree has audit/docs/fixtures and document scripts, **no application, Python/Pydantic foundation or26-test suite**. Do not assume work in another session transferred.

Full-milestone continuation, planning revision 2.2-M1: this follow-up started with the previous planning diff already present, not a clean tree. All 20 phases through final FF8 now have full work packages in [MILESTONE_PLANS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\MILESTONE_PLANS.md), with task order/ownership/deliverables/acceptance/failure/stop. [PLAN_REVIEW_AND_DECISIONS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\PLAN_REVIEW_AND_DECISIONS.md) assigns 13 unresolved or selected decisions to their due milestone. The user explicitly requested commit/push; application implementation and dependencies remain forbidden in this planning turn. Inspect Git history/status for actual publication state rather than infer it from an earlier clean-entry snapshot.

Read CLAUDE.md, this handoff, IMPLEMENTATION_HANDOFF, PROGRESS and DESIGN_REVIEW_V2_2; then only the current task's contracts. Source docs are canonical, generated combined Word/Markdown are projections. FUND_ACCOUNTING owns economics, GAME_SYSTEMS player rules, MASTER_SPEC release scope, SIMULATION_ARCHITECTURE interfaces, SCENARIO_CONTRACTS the tightened three challenge authoring schedules. Old JSON branch dollars remain isolated arithmetic, not full dated runs.

For implementation also read IMPLEMENTATION_PLAN plus the selected MILESTONE_PLANS section and due decisions; do not reload all later phase details or treat optional FF7/FF8 as base-game requirements. This pass explicitly adds the pure session/independent arbitrary-path control prerequisite before the early human prototype, recovery-tail coverage, actual control/restriction mechanics in6a, end-to-end historical replay in7a and a bounded final extension-planning gate.

## What changed and why

Three independent read-only financial, gameplay and engineering reviewers were requested and completed; all findings/dispositions are recorded in DESIGN_REVIEW_V2_2. Accepted Case2 post-flow issuer correction, settled replacement timing, frozen pending-return collateral, bounded termination, extended gate horizon, useful operating actions, exact precision/hash/retry/readiness, smaller milestones and earlier human test. Removed dominated active Case3 hiring; kept forecast arithmetic. Rejected artificial capability rewards, additional finance frameworks and SEO/marketing integrations. Useful prior financial-library/source research retained; only uncertain material choices rechecked.

The full initial game remains two human partners,25m investor fund and300k separate firm,60 synthetic weekdays/six chapters, LP terms, equity long/short financing, fees, firm survival and crises. First releasable game remains a complete day1–21 opening arc, not a chart/ticket demo. New FF3b is an explicitly internal short challenge to test role agency before building the full UI/campaign. Optional providers/AI/ML remain deferred; no real-money/paid activity.

## Next agreed task and stop condition

**FF0a only:** materialize Case1's complete authored12–21 schedule, schema/loader, three actor-tagged scripts and independent daily financial oracle/coverage/hashes. Exact paths and X01–X07 are in IMPLEMENTATION_HANDOFF. No economic reducer, full frontend/backend scaffold, DB, provider, feature expansion or deployment. A validated authored fixture is not a working game. After evidence/review update handoff and stop before FF0b.

Unresolved: full-path dated oracle totals/feasibility, compiled challenge tapes, ordinary zero-position opening/full campaign tape, release/DB/auth/migration choices, staffing payoff in full game, balance and enjoyment. The record-complete authoring schedules still need materialization and independent calculations; don't turn100k safety bounds or omitted weekend charges into actual postings. Case2 no-sale leverage breach does not necessarily mean payment default if allowed credit suffices. Case3 seeded47k firm cash oracle excludes later newly collected fees. Termination cannot cash provisional incentive merely because season scoring ends.

## Commands and actual evidence

State: `git status --short`, `git log -5 --oneline`, `rg --files`. Docs: `python scripts/build_documents.py`, `python scripts/validate_design.py`. PACKAGING_VALIDATION records final executed results. Original validator failed Windows cp1252; UTF-8 retry exposed missing python-docx. Scripts now have explicit UTF-8 and standard-library Word fallback; no package installed. Python3.14.3 observed, node/npm on PATH; psql/soffice not found on PATH. No application/race/security/playtest/provider/ML checks ran. Word structure/content checked, pages not rendered. Future loader/test commands are proposed, clearly labeled in IMPLEMENTATION_HANDOFF.

Claude continuation: Read this handoff and verify the current repository state before editing. Critically review the revised plan using bounded financial, gameplay, and engineering reviewers. Resolve concrete contradictions and improve weak acceptance criteria before implementation. Then implement only the next agreed milestone, validate it against the documented acceptance cases, and update this handoff with evidence and the next task.


---

Source: `docs/PROMPT_PACK.md`

# Copy-ready implementation prompts — v2.2

Use one prompt for one bounded task. The repository already exists. All application gates are pending. Model selection is performed in the actual client, not by claiming a prompt can switch its underlying model. The owner requested Astra/extra-high for this completed v2.1 critical review; verify available model names in the implementation environment.

Planning revision 2.2-M1: all 20 milestone packages through FF8 are in MILESTONE_PLANS. A prompt selects one package; it does not supersede its prerequisites, owned files, due decisions or stop gate. PLAN_REVIEW_AND_DECISIONS owns unresolved choices/evidence deadlines. Current planning turn permits documents plus requested commit/push, not application features or dependency installation.

## P01 — Verify and challenge the v2.2 plan

Read CLAUDE.md, both handoffs, PROGRESS and DESIGN_REVIEW_V2_2. Verify Git/files/tools; do not assume the reported foundation/26 tests exists. Use bounded independent financial/gameplay/engineering reviewers for concrete contradictions (no recursive agents/edits). Reconcile findings and weak acceptance before implementation. Preserve useful existing research and uncommitted planning work. Next agreed task is FF0a, not a full scaffold.

## P02 — FF0a complete one authored package

Implement only IMPLEMENTATION_HANDOFF's FF0a/X01–X07. Materialize Case1 defaults/overrides, actor-tagged command scripts and independently calculated dated oracle. Add schema/loader/rejection checks; no financial reducer, UI/API/DB/provider. Freeze covered-share collateral, replacement transfer, costs, fees/series/residuals and complete12–21 coverage. Report schema validity separately from engine/playability. Update handoff, stop before FF0b.

Use the full FF0a work package in MILESTONE_PLANS and standard-library validation. Complete independent full-date financial cells before calling success paths feasible; report missing evidence explicitly. Do not create an application foundation in this authoring package.

## P03 — One financial contract

Implement exactly the selected FF1/FUND_ACCOUNTING contract and related acceptance cases. Use fixed precision and an immutable balanced journal. Provide independent expected arithmetic, not expected values obtained from the implementation. Separate fund, firm and investor series. Implement opening participation net plus reversible provision; preserve surviving HWM on partial redemption. Use ACT/365 management and ACT/360 settled borrow/debit calendar accrual with residuals. Test replay/reversal and meaningful boundaries. Treat legacy golden_scenario as a primitive fixture only. Report actual commands/results and pending cases.

## P04 — Execution, borrow and margin

Implement the selected FF2 transition with deterministic future-event eligibility, borrow/collateral/debt identities, settlement and deadline rules. Show a gap/recall/halt case and exact accounting. Check the entire constraint vector: covering can raise net exposure, redeeming can shrink margin equity, and pending returns keep borrow costs/collateral until settlement. A forced action can fail; preserve the deficit. No daily-bar invented intraday path, no LLM-owned prices, no unrestricted broker execution. Freeze the contract before adding presentation.

## P05 — Governance and transaction races

Implement FF3a pure authority or FF4a persisted race safety, whichever is the agreed bounded task. Two human partners need jointly approved immutable sleeves and distinct consent. Test revoked authority, commitments, idempotency/edit/cancel/fill; use real PostgreSQL only for FF4a race claims. Atomically persist effects/publication there. No SQLite substitution or self-approved delegation expansion.

## P06 — LPs and management-company survival

Implement the selected FF4 contract for investor notices/dealing, series fees/HWM, firm budget or trust. Preserve notice versus recognized payable versus cash payment. Distinguish fund NAV, restricted cash, company cash and fee receivable. Provide arithmetic and an event-order trace. Do not replace mechanics with cosmetic meters or free-text AI scoring.

## P07 — First complete playable opening arc

Deliver FF5 against verified engine APIs. Read the vertical slice in SEASON_SCENARIOS. Include research effort, thesis/hedging, partner negotiation, investor/financing/business choices, consequences and causal debrief. The operating partner needs independent agency. No fake model/provider results. Run a two-user flow through day20 dealing and ordinary day21 opening administration, including weekend accrual, disagreement, pause/resume and one crisis resolution; record confusion and actual duration.

## P08 — Bounded adversarial review

Review only this diff, its contracts and necessary dependencies. Return at most five reproducible defects with severity, violated invariant, exact path and expected/observed behavior. Prioritize fee/flow errors, collateral double count, authority races, future leakage and score exploits. Distinguish a definite defect from an open design question. Do not rewrite the architecture or start other agents.

## P09 — Campaign and balancing gate

Complete the selected FF6 chapter or balance task. Run matched seeded baseline policies and inspect concentration, cash-only, trust farming, replay rerolls and last-day obligation exploits. Keep rules immutable within a season. Report results with seeds and limitations. Do not claim a fun or balanced game solely because unit tests pass; include playtest evidence.

## P10 — Excluded scope

SEO and marketing integrations are outside the current planning/implementation roadmap. Do not run the archived OpenSEO spike.

## P11 — Optional research and ML

Read LIBRARY_RESEARCH and SIMULATION_ARCHITECTURE. Select only the dependency needed for this measured task; do not install the candidate list. Use the same cost/execution engine as the game. Freeze point-in-time data and chronological split; define a simple baseline and a concrete target before training HMM or another model. Use filtered inference, avoid future normalization and record rejected candidates. Measure prediction/gameplay value separately from strategy return. LLM explanations have no financial mutation rights. No invented alpha or deployment evidence.

## P12 — Resume or diagnose

Read the small handoff and current Git state. Continue only the documented next task. If blocked, capture the failing command, smallest reproducer, invariant, attempted fixes and next diagnostic. After two failed repair cycles change the diagnosis rather than repeating prompts. Do not reload all docs or recreate the plan without a concrete conflict.

## P13 — Limited parallel work, only when requested

Freeze shared interfaces and choose disjoint tasks with separate ownership/worktrees. Keep migrations, journals and transaction contracts under one integrator. Use bounded outputs and actual acceptance evidence, integrate sequentially, and stop completed workers. Model names and agent support must be checked in the actual client. Never use parallelism to bypass permissions or assume extra usage quota.

## P14 — Evidence and handoff

Review RECRUITER_EVIDENCE. Build a truthful demo and evidence index from actual results. Clearly separate implemented, tested, measured, simulated and proposed. Update PROGRESS, source/rules manifests and docs affected by actual changes. Regenerate combined documents if canonical design changed. Do not add performance numbers or resume claims from aspirations.

## P15 — Implement one authored scenario contract

Read SEASON_SCENARIOS, fixtures/season_scenario.json, fixtures/scenario_cases.json and FUND_ACCOUNTING. Choose one case and freeze its prerequisites, phase ordering, public/hidden observations, executable tape, capacity and independently authored controls. Convert the design contract into a complete runnable fixture without inventing absent data. Implement success, failure and recoverable branches; run engine outputs against independent reference arithmetic. Keep paid services disabled. Record branch results and limitations. A valid manifest or expected-values JSON is not a playable scenario.

## P16 — Dependency or data-source decision

Read LIBRARY_RESEARCH, its 17 pinned evidence records and the proposed feature's acceptance contract. Recheck the exact release/license/module/API using current primary sources, including transitive/solver obligations. Separate software reuse from dataset display/retention/redistribution rights, credentials and real costs. Compare a small original implementation or existing dependency against the candidate. Return adopt/adapt/reference/defer/reject with one concrete integration boundary and actual evidence. Install only if the current task authorizes the implementation and no paid activation is needed; otherwise retain a fixture-based deliverable. Do not equate an API key with redistribution permission.

## P17 — Execute one fully specified milestone

Read CLAUDE_HANDOFF/IMPLEMENTATION_HANDOFF/current Git state, then IMPLEMENTATION_PLAN, selected MILESTONE_PLANS package and its due decision-register entries. Verify prerequisite evidence exists; resolve only concrete blockers for this package. Execute its ordered tasks within owned paths, run the defined independent acceptance, record actual commands/hashes/results/limitations, update handoff with one next gate and stop. Proposed CLIs/tests do not exist until implemented; don't claim them run. Do not auto-start later milestones or optional FF7/FF8.

## P18 — Final-phase extension decision

Execute FF8's design gate only after selecting one real requested extension. Produce bounded SPEC/PLAN/ACCEPTANCE with user value, lifecycle/authority, dependency/rights/cost and independent failure/recovery cases. No unknown feature wishlist or automatic deployment/live feed/league/derivatives build. A concrete defer/reject is valid if required evidence is absent. Initial-game completion remains FF6c.

Claude continuation: Read this handoff and verify the current repository state before editing. Critically review the revised plan using bounded financial, gameplay, and engineering reviewers. Resolve concrete contradictions and improve weak acceptance criteria before implementation. Then implement only the next agreed milestone, validate it against the documented acceptance cases, and update this handoff with evidence and the next task.


---

Source: `docs/AGENT_WORKFLOW.md`

# Development and simulated-agent workflow

The 6 October v2.1 critical review explicitly used Astra with extra-high reasoning at the owner's request. That completed design task does not imply any model, opponent or application is deployed.

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

Current claim: designed a cooperative hedge-fund management simulator and specified its accounting, game economy and data boundaries; critically reviewed 17 repository/license snapshots and 22 prioritized realism gaps in v2.1. No application, model, performance, user adoption or load result is presently demonstrated.

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

The three authored challenge designs and independent arithmetic checks are design evidence, not implemented gameplay. Report library candidates as reviewed/adoptable/deferred, never installed integrations. A source review is not a security or license-compliance audit. The larger combined Word file measures documentation coverage, not engineering completion.


---

Source: `docs/SOURCES.md`

# Sources and verification boundaries

## Fresh bounded verification,7 October2026

Prior research remains dated6 October; it was not all repeated. The following primary sources were opened for material current financial/engineering distinctions. Old publication dates remain old; fictional numbers and corrections are design judgments, not source prescriptions.

| Exact source | Freshly checked narrow evidence | Design judgment / limitation |
|---|---|---|
| [SEC T+1 release,21 May2024](https://www.sec.gov/newsroom/press-releases/2024-62) | Applicable most broker-dealer transactions moved to T+1 effective28 May2024 | FundForge deliberately uses a holiday-free synthetic calendar; not an exchange/era universal rule |
| [Investor.gov Hedge Funds](https://www.investor.gov/introduction-investing/investing-basics/investment-products/private-investment-funds/hedge-funds) | Fund terms, leverage, valuation, fees and withdrawal limits/incentive conflicts need attention | Our1.5/20 fee terms, gates, lockups, redemption payment and investor behavior are authored contracts |
| [IBKR short-sale cost](https://www.interactivebrokers.com/en/pricing/short-sale-cost.php) | One broker distinguishes borrow fees and short-proceeds interest; availability/rates depend on security | Our zero rebate,40% replacement, frozen pending-return collateral and deadlines are fictional choices, not IBKR promises |
| [ESMA performance-fee guidelines PDF](https://www.esma.europa.eu/sites/default/files/library/esma34-39-992_guidelines_on_performance_fees_en.pdf) | Scoped UCITS/certain-AIF guidance distinguishes performance-fee methodology/crystallization | Does not govern every equity hedge fund; our annual/redemption/termination dates and series methodology are explicit contract design |
| [FINRA Margin Calls](https://www.finra.org/investors/insights/margin-calls) | Retail margin-risk context includes changed house requirements/liquidation risk | Not institutional prime-broker contract authority; no legal grace period inferred. Two other guessed FINRA URLs failed and are not evidence |
| [Python Decimal](https://docs.python.org/3/library/decimal.html) | Exact decimal contexts/rounding/traps | Our precision40/scales/residual policy must be independently tested; no implementation claim |
| [PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) | Row FOR UPDATE locking semantics, concurrency/deadlock considerations | Season-wide lock is our architecture choice; requires real race/fault evidence |
| [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/) and [strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) | Typed model validation API and strict behavior | Optional boundary tooling; cannot replace independent financial oracles. License/purpose/fit details in LIBRARY_RESEARCH |

No real fund/legal compliance claim is made. Portfolio factor sensitivities/stress outcomes, counterparty timings and NPC confidence are authored abstractions. Historical strategy/jurisdiction/broker variation and omitted AML/tax/illiquid valuation remain explicitly scoped in REALISM_AUDIT. SEO entries below preserve earlier research provenance only and are excluded from the active plan and generated package's standalone sections.

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

## v2.1 expanded research register

The critical financial audit's primary-source register and claim boundaries are in [REALISM_AUDIT](https://github.com/krishbansalofficial/fundforge/blob/main/docs\REALISM_AUDIT.md), references S1–S11. It adds SEC investor/ethics material, explicitly scoped ESMA performance-fee guidance, AIMA institutional operating preferences, the FSB's IOSCO valuation entry, IBKR settled-borrow examples, GIPS return methodology and FINRA house-margin guidance. Historic publication dates are retained; accessing an older source in 2026 does not turn it into a new rule. Inaccessible IOSCO text is not claimed as inspected.

The software review is in [LIBRARY_RESEARCH](https://github.com/krishbansalofficial/fundforge/blob/main/docs\LIBRARY_RESEARCH.md), with17 exact repository/commit/source/license records in [library_review.json](https://github.com/krishbansalofficial/fundforge/blob/main/fixtures\library_review.json). It distinguishes current resolved repository owners from old aliases, development snapshots from release pins, and restricted licensing from permissive licensing. No candidate was installed or benchmarked and no upstream implementation was copied. The ledger/concurrency choices also cite Python Decimal and PostgreSQL official documentation in [SIMULATION_ARCHITECTURE](https://github.com/krishbansalofficial/fundforge/blob/main/docs\SIMULATION_ARCHITECTURE.md).

Source categories are intentionally separate: industry concepts, a particular provider's practice, a fund's negotiated contract, and our game simplifications. The synthetic calendar, fees, LP windows, leverage, costs and outcome thresholds are authored settings. Historical/live mode needs its own venue/jurisdiction/era/entitlement review; the initial fictional US-style cash-equity mechanics do not establish real regulatory compliance.


---

Source: `docs/PROGRESS.md`

# Current project state

Updated7 October2026. Design v2.2; application implementation not started locally.

Continuation revision 2.2-M1: the entry tree contained the earlier uncommitted planning work at51eda0c, which was preserved. All 20 milestones through FF8 now have full packages in MILESTONE_PLANS; PLAN_REVIEW_AND_DECISIONS records current corrections,13 due decisions and pending evidence. Added pure session/arbitrary-path Case1 controls before human prototype, explicit recovery tails, controls/restriction mechanics and actual historical-replay delivery. The user subsequently authorized commit/push of the completed documentation. Remote fetch confirmed main/origin/main both51eda0c before publication; final publication result must be recorded after it occurs.

Original review entry HEAD51eda0c was clean; this follow-up preserved its planning changes. Recent commits confirm v2.1 audit, prior redesign and original document package. No backend/frontend/dependency manifest/test directory, Pydantic foundation or26 tests found. Existing source paths/Claude instructions/fixtures/scripts inspected. No work assumed transferred from other checkouts. The first planning pass did not commit/push; this continuation publishes its combined documentation under the user's explicit request. No deployment/installation/application implementation occurred.

Planning changes: three bounded read-only independent reviews; evidence/consequences/dispositions in DESIGN_REVIEW_V2_2. Corrected Case2 issuer concentration, explicit replacement cutoff/transfer, frozen covered collateral, voluntary margin priority and termination; removed dominated active Case3 hire; extended gated-unit horizon; authored complete bounded schedules; concrete operating commands, precise numeric/hash/retry/readiness and measured playtest plan. Split large gates and added early internal human experiment. SEO/marketing excluded. Prior financial research retained with narrowly updated sources/dependency choices.

Changed canonical master/game/accounting/scenario/architecture/plan/acceptance/review/library/source/decisions/Claude handoff/prompts and fixture annotations; added SCENARIO_CONTRACTS, DESIGN_REVIEW_V2_2, IMPLEMENTATION_HANDOFF. Combined Markdown/Word regenerated with portable documentation tooling. See PACKAGING_VALIDATION for exact actual results and original environment failures. These are package/arithmetic checks, not application tests. Full independent accrued path totals, compiled executable tapes, economic runtime/concurrency/playtest results remain pending.

## One next task

FF0a only as detailed in IMPLEMENTATION_HANDOFF/X01–X07: compile Case1 authored12–21 record schedule, typed schema/loader/rejection checks, three actor-tagged scripts and independent dated financial oracle with coverage/hashes. Do not start full scaffold/economic features or declare playable status. After verified FF0a update handoff to FF0b. Original P01/P02 scaffold instructions superseded by the revised prompt pack.

Then follow the documented gates: FF0b, FF1a/b, FF2a/b/c and FF3a/b, FF4a/b, FF5a/b/c first playable, FF6a/b/c full initial game; FF7a/b and FF8 optional final extension decision. All application milestones remain pending. No application tests, DB/concurrency experiments, playtests, provider/model calls or installs occurred while expanding these plans.

## Evidence discipline

Inspect current uncommitted planning diff before editing; preserve it. Record actual commands/versions/hashes and pass/fail/pending separately. Original packaging claims from6 October are historical; current command results in PACKAGING_VALIDATION. No measured fun, sustainable firm, empirically calibrated market, database safety or investment skill claim exists. Conditional Renewal does not fund the next quarter. Word rendering/compatibility is unverified despite valid OOXML/package checks.


---

Source: `docs/PACKAGING_VALIDATION.md`

# Design-package validation v2.2

7 October2026. These are documentation/reference checks, not application tests, scenario execution or playtest evidence.

## Actual environment and commands

Observed Python3.14.3 on Windows; original bare `python scripts/validate_design.py` failed cp1252 decoding. `python -X utf8 scripts/validate_design.py` exposed missing python-docx through the old eager builder import. Those failures are recorded, not treated as passes. No dependency installed. Documentation scripts now read/write explicit UTF-8, optional docx import no longer blocks reference validation, and original standard-library OOXML fallback permits Word generation.

Executed successfully after correction:

```powershell
python scripts/build_documents.py
python scripts/validate_design.py
git diff --check
```

The previous v2.2 pass passed2,511 package checks across21 sections. Planning revision2.2-M1 adds full20-milestone coverage/required work-package fields and an acyclic dependency check, plus the detailed plans/decision register in23 bundled sections. Current exact check/table/paragraph counts are printed by the validator and recorded after final generation. Counts are package assertions, not application tests. Word is structurally valid ZIP/XML with repeated table headers, heading styles, external link relationships and source hashes/visible-text comparison. No Word/LibreOffice page render was available; table widths, pagination, readability and application compatibility are unverified. The fallback preserves content, with simpler typography/list treatment than python-docx.

Checks: local Markdown links/fences; fixture JSON; dated synthetic calendar/capital; six isolated legacy NAV states;9 financial arithmetic oracles; three isolated episode checkpoints;17 pinned repository/source/license records; exact combined source inclusion; Word archive/XML/source-hash and visible-paragraph content. Added independent corrected Case2 issuer/sector/ETF/initial-margin/normalized-cash checks, exclusion of dominated hire, extended gate horizon and scale24 residual/tie arithmetic. These do not execute actual dated scenario paths. v2.2 rules complement v2.1 isolated fixture checkpoints; their complete accrued path oracles/compiler remain FF0a/FF6 work.

## Checks only proposed / limitations

No simulation, Next.js/FastAPI/Pydantic application, database, application test suite, financial reducer or complete compiled executable tape exists. No real PostgreSQL races, restore/fault/security/load tests, provider/model tests, two-human playtests or balance experiments ran. No library installed, benchmarked or compatibility-tested. The17 previous pinned records were preserved; only bounded primary-source/DTO-framework verification occurred this session.

Original entry HEAD51eda0c was clean; full-milestone continuation entered the preserved planning diff. The user then explicitly requested commit/push; actual publication evidence is recorded in PROGRESS after execution. No deployment, paid request, installation, application feature, repository-creation script or visibility change. Word/Markdown regenerated from source docs, excluding standalone SEO/marketing integration sections; old research provenance remains labeled archived. Financial practices, fictional contracts and house simplifications remain distinct. Read PLAN_REVIEW_AND_DECISIONS and IMPLEMENTATION_HANDOFF for remaining uncertainties and the exact next task.


---

Source: `docs/DESIGN_REVIEW_V2_2.md`

# FundForge v2.2: critical review and decisions

7 October 2026. Planning only. This review supplements the useful v2.1 research; it does not claim implemented software.

## Verified state and blunt assessment

Starting HEAD: `51eda0c1aa806e0c9f94b7e2527a013b4dedb77f`. `git status --porcelain=v1` was empty. Recent history is the v2.1 audit (`51eda0c`), game redesign (`5ae8a5a`), document package (`797e90d`), and initial README (`1c04c3f`). Tracked instructions are `CLAUDE.md` and two read-only reviewer files under `.claude/agents`; no AGENTS.md was found. Canonical sources are in `docs/`, design JSON in `fixtures/`, generated Markdown/Word in `documents/`.

The local project is a substantial specification, not a Python/Pydantic foundation. There is no backend, frontend, database schema, dependency manifest, application test directory or 26-test suite. The two Python scripts build/validate documentation. We did not inspect another checkout or infer work from an earlier conversation. Repository visibility was not freshly verified remotely.

The design's strengths are its connected economics, separate fund/firm claims, realistic failure distinctions, delegated authority, synthetic information timing and original deterministic engine. Its weakness is that persuasive scenario prose and narrow arithmetic checks conceal missing executable contracts. Case2 actually fails a constraint its success text promises. Some supposed alternatives are dominated or end before their obligations resolve. Broad FF0–FF4 gates defer discovering whether two humans enjoy the game. More libraries will not solve these problems.

| Category | Local evidence | Status |
|---|---|---|
| Implemented | Documentation builder and packaging/reference validator | Tooling only; portability fixed in this revision |
| Tested previously / rerun here | Independent arithmetic and package consistency | See PACKAGING_VALIDATION for actual current command/results |
| Proposed | All economic modules, UI, persistence, scenarios, recovery | No application behavior established |
| Unresolved | Full opening campaign tape, runtime pins, economic feasibility under every path, enjoyment | Explicit milestone gates; no invented results |

## Prioritized gaps and acceptance

| ID / priority | Evidence | Consequence | Correction / dependency | Acceptance criterion |
|---|---|---|---|---|
| D01 / P0 | SEASON_SCENARIOS §8 Case2 inherits five $3m equities; pay-all NAV $18,995,800 | Each is 15.793%, outside 15% cap; gated branch is 15.001517% | Replace inherited basket with fully specified <=$2.5m names; FF0a authoring before FF2b risk | Every issuer, sector, ETF, gross/net, initial/maintenance and cash test checked at every reference branch and actual execution prefix |
| D02 / P0 | Scenario JSON `not_yet_compiled`, FF0 versus P01 disagreement | Schema-valid manifest may be mistaken for runnable game | SCENARIO_CONTRACTS supplies complete design schedules; FF0a compiles Case1 only; full opening arc at FF5a | Coverage report, opening balances/series/settled borrow, dated events, command scripts, independent oracle ledger; status never says runnable until engine exists |
| D03 / P0 | FUND_ACCOUNTING §4 collateral lacks unsettled-lot mapping | Short gap can reserve proceeds twice or omit a top-up; cure sale sweep can spend needed cash | Explicit collateral lots and linked cover release; FF2a | Unsettled short marked above sale price, partial cover, failed settlement, split and duplicate delivery conserve collateral/resources |
| D04 / P0 | FUND_ACCOUNTING §7 says forced actions first; GAME_SYSTEMS §8 offers voluntary response | Engine could liquidate before timely player cure | Separate due recall buy-ins from pending margin escalation; FF2b | Timely valid voluntary cure consumes available event first; residual deficit then forced; expired recall priority preserved |
| D05 / P1 | Case2 ends day41, leaves gate claims and unnamed catalyst | Gate upside/recovery cannot be evaluated | Extend same fixed tape to day61; describe preserved broad exposure and floating claims | Pay-all and gate scripts honor obligations through day61, with fee/carry bridge and residual units shown; returns not used as universal strategy proof |
| D06 / P1 | Case3 hire after known break, no relevant future use | Costly dominated action masquerades as strategy | Remove active hire choice from challenge; retain cash arithmetic as forecast counterexample | Active choices are report/attention/capacity/admission; no success count earned by intentionally worse staffing branch |
| D07 / P1 | GAME_SYSTEMS §11 operating role mostly previews | Second player may only calculate/sign | TreasuryReserve and SelectReplacementBorrow commands; existing attention allocation | Each role changes at least two material outcomes/opportunities in the opening playtest; log actor/effect |
| D08 / P1 | Precision uses 'at least'; hashing and retry precedence unspecified | Lost residuals, unstable replay, committed retry conflicts | Exact architecture wire/context/coordinator contracts; FF0b/FF3a | HALF_EVEN/negative zero/overflow/round-trip canonical vectors; stale-version retry returns original committed result without effects |
| D09 / P1 | FF0–FF4 encompass nearly whole engine before human play | Product risk discovered too late | Split milestones; internal short Case1 experiment FF3b | Two human roles complete a crisis before campaign/UI expansion; retain failure observations |
| D10 / P1 | Validator default cp1252 and eager docx import | Document evidence cannot be repeated locally | Explicit UTF-8; standard-library Word fallback; documentation tooling only | Bare documented build/validate commands pass without package installation; structural validation distinguished from rendering |
| D11 / P1 | Case3 fee seed and no per-series history; Case2 'after charges' called day39 | Warm starts can omit liabilities or accrue twice | Distinguish unit-test checkpoints from dated challenge openings; SCENARIO_CONTRACTS | All intervening dates accrue; exact full-path numbers independently computed before release; isolated oracles never substituted for accrued path |
| D12 / P2 | Library/source reviews already done 6 October | Repeated research distracts from game; SEO outside task | Retain pinned finance-library evidence; exclude SEO from all current plans/prompts/bundle | No SEO milestone/dependency; optional library receives its own unmet-requirement gate |

## Independent reviewer reconciliation

Three bounded read-only agents were explicitly requested and used: financial realism (PM/CRO/accountant/COO), gameplay, engineering/evaluation. Each returned at most five findings. No recursive delegation or reviewer file edits occurred. The following records all returned recommendations; references name the original v2.1 sections, not stable post-edit line numbers.

| Reviewer / finding | Disposition | Reason and destination |
|---|---|---|
| Finance F1: Case2 post-flow issuer breach | Accept | Concrete arithmetic defect; corrected basket and A22 |
| Finance F2: replacement transfer/cutoff undefined | Accept | Explicit day14 cutoff/day15 settled transfer and fee switch; FUND_ACCOUNTING §10 / V26 |
| Finance F3: retained return collateral ambiguous | Accept | Freeze covered-share reference target through settlement; FUND_ACCOUNTING §10 / V25 |
| Finance F4: termination economics missing | Accept bounded policy | Ten-business-day authored recovery horizon, actual liquidation/final dealing, persistent claims; V31–V32. Full statutory waterfall deferred |
| Gameplay G1: dominated Case3 hire | Accept removal; reject adding an artificial hire benefit | Smallest correction preserves truthful automatic accounting; §8 Case3 |
| Gameplay G2: gate payoff and later plan missing | Accept | Extend horizon and fixed liquidity plan; SCENARIO_CONTRACTS Case2 |
| Gameplay G3: operating role may only approve | Accept | Commands and resource consequences; GAME_SYSTEMS §12 |
| Gameplay G4: evidence timing/content incomplete | Accept | Exact evidence matrix and wait path; scenario schedules |
| Gameplay G5: scenario proof versus fun proof; measured protocol | Accept | Separate financial scripts from human studies; ACCEPTANCE_TESTS §v2.2 |
| Engineering E1: full scenario artifact gate | Accept in bounded form | Compile one case next; reject making all three engines/full campaign a prerequisite to starting accounting |
| Engineering E2: earlier human experiment | Accept | FF3b internal challenge, explicitly not first releasable game |
| Engineering E3: exact precision/canonical form | Accept | SIMULATION_ARCHITECTURE §v2.2 |
| Engineering E4: retry/version precedence and race oracles | Accept | Coordinator order and C13–C16 |
| Engineering E5: portable validator / optional generation | Accept | Documentation-tooling correction; no application implementation |

## Retain, simplify, remove, defer

Bounded follow-up reviews accepted eight corrections: finance closed the cheap BRIN inventory bypass and placed accrual before certified dealing; gameplay fixed instrument-ID price assignment, added day14 pre-EXEC_B barrier and simplified Case3 capital-decline path without a research-alpha claim; engineering moved pure LP/firm payment to FF2c before prototype, separated readiness bookkeeping revision and corrected cumulative residual recurrence/rate-change carry/tie bound. No reviewer edits or recursive delegation; these are document corrections, not economic-test results.

Retain one USD equity long/short fund, one fictional prime broker, distinct investor series/firm cash, calendar carry, partial fills, initial versus maintenance margin, real investor obligations, restrictions, independent controls, causal explanations and responsible winddown. These interactions are the game.

Simplify administration into automatic accrual/reconciliation/report production; surface meaningful exceptions. Four instruments suffice for the releasable opening arc; twelve remain the full campaign ceiling. Use authored stress sensitivities rather than covariance fitting. Commission is zero in these challenges; explicit spread/impact remains. No new dashboards, approval layers or distributed services.

Remove active Case3 hiring and its claim to a second strategic success path. Remove SEO/marketing from current implementation scope, prompts and generated package; preserve the old assessment as archived research only. Remove the full frontend/DB scaffold from the immediate FF0a task. Reject a production trading framework, purchasable accurate accounting, guaranteed research alpha, hidden player-targeted shocks and free fund-to-firm bailout.

Defer staffing gameplay to the full campaign where a capability must compete with a defined task; defer real data, optimizers, ML, AI tutors, asynchronous leagues, derivatives, taxes, multi-currency and real broker execution. No scenario or playtest result is declared complete. A referee-like NPC cannot provide the second human signature.

## Rigor and limitations

The graduate-level claim is falsifiable: independent financial derivations, invariant conservation, fixed-tape replay, fault/race evidence, controlled balance experiments and candid human-study results. Hypotheses and failure observations matter more than feature count. Synthetic pricing/counterparty rules are not empirical hedge-fund calibration. Fictional notices/margin priorities are contracts, not universal practice. Full campaign content and release compatibility remain unresolved. Next task is precisely FF0a in IMPLEMENTATION_HANDOFF, not feature implementation during this review.


---

Source: `docs/SCENARIO_CONTRACTS.md`

# Three scenario design contracts v2.2

7 October 2026. These are complete bounded **authoring specifications**, not implemented scenarios, full compiled market tapes, demonstrated feasible engine paths or playtests. They tighten SEASON_SCENARIOS §8. Existing `scenario_cases.json` numbers remain isolated checkpoint oracles; full dated runs MUST include all subsequent accruals. If an oracle described below has not been independently calculated, mark it pending, never fill it from engine output.

## Shared contract and exhaustive defaults

All unused instruments begin at reference100 at the warm start and retain that mark unless explicitly overridden. Held instruments use their declared opening marks (Case3 BEAM48). Initial quotes do not execute seeded holdings; opening holdings are journaled inherited assets/loans. No missing prior quote is inferred. This makes the first PUBLIC_MARK record complete for all twelve IDs.

Use the synthetic dated Mon–Fri calendar and ordinary event/accrual order in FUND_ACCOUNTING. Day N is the Nth weekday from 5 January 2026, including fictional holiday trading. Each business date has OPEN_ADMIN, PUBLIC_MARK at 09:30, a decision barrier, EXEC_A at 10:00, EXEC_B at 15:00, CLOSE at16:00 in ordered subphases: final coherent marks, daily accrual/common allocation, management fee/performance provision, reconciliation/certification, dealing, checkpoint. No second accrual after dealing. Each execution may have an authored preceding decision barrier; day14 before EXEC_B is an explicit replacement-cutoff window. These are simulated scenario timestamps, not claims about an actual exchange. Publish each event only when reached. An order accepted after a barrier cannot execute at the preceding PUBLIC_MARK. If a margin call occurs at PUBLIC_MARK, the barrier permits a voluntary cure for EXEC_A; due recalls precede it and forced margin actions consume residual capacity after its valid fills. New incidents during EXEC_A pause before EXEC_B.

Every instrument receives a mark at PUBLIC_MARK and both executions, even if halted. Default references carry unchanged from prior event; no interpolation/randomness. CLOSE uses the last event's coherent marks. Default volume is 1,000,000 shares per instrument per execution; half-spread 5bps, impact coefficient 2,000bps, combined-side participation 5%, commission zero. Market capacity is per fund/instrument/event. Default borrow inventory is opening settled shorts plus 50,000 extra shares in each shortable instrument, rate 2% ACT/360; all twelve instruments are shortable unless restricted. Debt rate 6%, line $7.5m. Ordinary coefficients apply unless overridden. On weekends there are no quotes/trades/payroll; each date accrues ordinary fees/carry against aged last marks. Unknown extra securities/actions are rejected.

Instrument universe: ALTO/BRIN industrial, COVE/DART consumer, ELAN/FENN technology, GALA/HELI health, IONA/JUNO finance; BEAM broad-equity ETF, BOND defensive bond ETF. Default beta: equities and BEAM 1; BOND 0 equity / negative rate sensitivity. For authored stress only: equity market ±10% moves equity/BEAM ±10%; direct sector ±10% affects its names; rates-up shock moves BOND −5%. These are explicit house sensitivities, not fitted forecasts. No actions/splits/dividends except Case3's historical omitted distribution. No subscriptions/extra notices except declared below. Case objectives replace campaign Renewal and confidence-generated requests; LP concern transitions are recorded, but cannot invent additional claims in these challenges. This override is public at start.

Opening economic and settled quantities coincide; all shorts are already borrowed; no trade receivables/payables/locates/returns unless named. Money/fee residuals start zero at the warm start. Costs before it are embodied in stated cash/capital; prior fees already settled except named invoices. Seed/Patient/Tactical have 100,000/80,000/70,000 units respectively. Series allocation is proportionate to units at opening, with HWM specified per case. Opening lot basis equals opening reference prices; past profit is capital history, not a new trade gain. Author opening journal as assets versus liabilities/series capital, not fictional execution at the current known price. Firm owner capital plus accumulated prior P&L balances its stated assets/payables; no inter-entity plug. Pay weekly cost at every day divisible by five; accrue $4,000/business day. Opening payroll payable is stated for each start so the next weekly bill is $20,000, not double-accrued.

Public legal/authority setup: two authenticated partners, active emergency policy, no self-signature. Default independent tickets obey 5% current NAV and 15% chapter-opening NAV turnover. A jointly signed specific reduction package may exceed elective turnover, but never hard risk/cash restrictions. Warm-start holdings were inherited under earlier valid authority. Joint approval of package describes quantity maximum, allowed instruments, cost ceiling, expiry and valid fill prefixes; it does not make legs atomic. Managing Partner independently chooses replacement borrow inside the previously joint-approved ceiling and creates/raises a treasury reserve; lowering it below signed obligations requires joint agreement. PM chooses execution exposure. All current facts are shared; role ownership is not secrecy.

Player action set: choose/no research, allocate contingency, create/counter/sign/cancel package, submit/cancel market or limit order, select replacement when eligible, create treasury reserve, elect/no gate before dealing, certify corrected evidence-backed report, cap/decline/admit eligible capital, advance/hold, request controlled winddown. Routine daily closes/report generation never need clicks. Rejected impossible commands give reasons and leave economics unchanged; choosing hold advances only when both ready, with due-event consequences visible.

Control evidence: independent reference workbooks/scripts (NOT the posting code) must derive opening journal, one voluntary-success path, one alternative success path and one failure/recovery path per case. For each path provide broker settled cash/positions/borrow and admin series/NAV/fee claims at opening, each named shock, dealing and ending. Controls are necessarily path-specific once trades differ; the author stores separately calculated records keyed by command-script hash. An arbitrary player path requires the independent control calculator or invariant/cross-record checks; it cannot compare against a different path's fixed statement. All hidden tape/control material stays server-side. Compilation materializes every default/override into versioned records and reports coverage. A missing record is an authoring fault, never a guessed quote.

## Case1: The borrow is not the thesis

**Start/end.** Before day12 OPEN_ADMIN (20 January); end after day21 OPEN_ADMIN (2 February), before market. Fund assets: longs $27.5m, restricted cash $5m, cash zero. Liabilities: shorts $5m, debt $2.5m. NAV $25m, provision zero, each HWM100. Long quantities at100: ALTO/COVE/ELAN/GALA/IONA 30,000 each, JUNO25,000, BEAM100,000; shorts BRIN/DART/FENN/HELI12,500 each. Firm cash240,000, payroll payable4,000 from day11. All opening observations and known investor terms are public. Initial gross130%, net90%; no mandate deficit.

| Date/event | Public information/window | Fixed hidden input / obligation |
|---|---|---|
| day12 opening | Tactical10,000-unit day20 request, settled replacement terms, forthcoming coefficients disclosed | All marks100 through day15; coefficients effective day16: initial80/100%, maintenance70/90% |
| day12 research choice | Each assignment costs1; do nothing is legal | Debt schedule reveals at day13 PUBLIC_MARK: maturity within next quarter and refinancing unresolved. Survey reveals there instead: recent demand stable, coverage only last month. Neither discloses future price |
| day12 contingency or day13 barrier | Investigate borrow rather than spend same assignment on thesis | Reveal offer at next PUBLIC_MARK: replace up to1,250 BRIN, rate40%, no upfront fee; acceptance deadline day14 EXEC_B barrier; transfer at day15 OPEN_ADMIN |
| day13 opening | Broker recall1,250 BRIN; execute cover by day15 EXEC_B or deliver replacement | Recall quantity is a subset of settled loan, not all12,500 shares |
| day14 final acceptance | Operating partner selects bounded replacement or allows offer to expire | Accepted eligible offer reserves inventory. Transfer atomically returns1,250 old loan shares and creates same replacement quantity at day15 opening; collateral unchanged; old rate ends before day15 accrual,40% begins day15. Late selection is rejected, never accepted as an on-time cure |
| day15 EXEC_B | Last voluntary cover event; cover accepted before this event may execute | After eligible voluntary recall covers, unresolved recall executes forced buy-in using residual volume. Cover execution satisfies deadline even though borrowed shares return T+1 |
| day16 PUBLIC_MARK | Publish shock and pause | ALTO/COVE/ELAN/GALA/IONA/JUNO/BEAM95; BRIN/DART/FENN/HELI110; BOND100, regardless of holdings/side. These per-instrument references apply to unused instruments too. Short collateral topped up under treasury rules before voluntary fills; debt may rise. Stressed coefficients now effective |
| day16 EXEC_A | PM chooses long sale versus short cover; operating partner reserves future cash | BEAM95/volume42,120, BRIN110/volume25,000. EXEC_B reverts default volume; forced cure cannot invent capacity at EXEC_A |
| day17 opening | Settlement/collateral release | Day16 covers return borrowed shares; unpaid short borrow remains charged until then |
| day18 EXEC_A | A future opportunity to fund payment; prior planning matters | BEAM95/volume400,000; 20,000 sell gets94.905 and$1,898,100. ALTO/COVE/ELAN/GALA/IONA/JUNO/BEAM remain95, BRIN/DART/FENN/HELI110 through day20; BOND100 |
| day20 both executions | Previously disclosed possibility of BEAM trading suspension, not forecast certainty | BEAM halted; other instruments retain default volume. Earlier prepared sale and other feasible sales are allowed; failure is not hard-coded merely for missing day18 |
| day20 close / weekend / day21 opening | Certified dealing, actual invoices, payment checkpoint | Tactical10,000 units, no additional requests; no subscription. Crystallize only those units; pay actual dated claims/invoices after settlement, preserving weekend liabilities for next invoice |

**Borrow-availability override.** Day13 through21 BRIN new ordinary inventory is zero; recalled returned shares leave the lending pool and do not replenish it. Only the1,250-share40% transferred replacement offer can replace this recall; other11,250 original shares retain2% while outstanding. New BRIN shorts cannot cover/reopen into cheap borrow. Later restoration requires a separately authored future event; none occurs in this case. Other instruments retain default inventory.

**Decision tensions.** Early reduction sacrifices upside/control budget for margin freedom. Replacement preserves BRIN exposure at much higher carry and does not cure a margin deficit. Cover lowers short/borrow risk but raises signed net; sell-long lowers net and thesis exposure. Reserve at least$1.25m for investor/invoices before discretionary debt repayment; this changes what credit-funded elective positions can be accepted. A reserve is not an expense or bank cash. A survey/debt/borrow assignment competes for the same finite attention; public recall response never requires buying research.

**Scripts and independent oracles.** S1 jointly approve reduction, cover1,250 BRIN and sell20,000 BEAM at day14 EXEC_A under the signed package, retain payment reserve, then fund Tactical. Sell at99.942 gives1,998,840 proceeds/1,160 cost on default1m volume; cover100.050031 gives125,062.54 payable after cash rounding. Exact dated carry/collateral still belongs to the independent full-path ledger. S2 investigate day12, accept replacement day14, sell2,106 BEAM day16 EXEC_A and20,000 day18 EXEC_A, maintain payment reserve. Each script must calculate exact further quantities/affordability from the independent daily ledger before being called successful. Existing margin oracles $27,348.93/$11,112.50 isolate decisive fills, not carry-inclusive headroom. Check borrower-rate switch, debt for collateral, every prefix, residuals and Tactical series separately. Failure F1 refuse replacement/cover and then hold: forced buy-in is expected; voluntary-control objective fails while solvent recovery can still succeed by paying claims. Recovery F2 reduce later with available other securities; no halt fabricates insolvency. Winning requires positive NAV, resolved recall, paid Tactical and no forced liquidation; Survival reports forced actions honestly. Missing independent complete-path numerical ledgers are a compilation blocker, not a promise both scripts work.

## Case2: Profitable, illiquid, and redeeming

**Start/end.** Day39 OPEN_ADMIN (26 February) through day61 OPEN_ADMIN (30 March). Extend beyond day41 to resolve deferred gate units. Day39 opening is the stated25m balance **before new accrual**: cash2.1m, collateral5m, longs25.5m, shorts5m, debt2.5m, prior fixed fee/financing invoice100,000 due day41. Each series participates at100 per unit, HWM120, provision0. Invoice split: management70,000 matching firm receivable, financing30,000; already expensed. Firm cash180,000; payroll payable12,000 from days36–38. HWM120 prevents provisional incentives on the specified reference trajectories; verify under actual actions rather than assume under arbitrary new trades.

Corrected long basket at100: ALTO/COVE/ELAN/GALA/IONA/JUNO25,000 each ($15m), BOND25,000 ($2.5m), BEAM80,000 ($8m). Shorts BRIN/DART/FENN/HELI12,500 each. This preserves aggregate checkpoint arithmetic but removes the inherited $3m issuer breaches. Both Seed and Tactical have properly noticed external dollar targets3m each, disclosed day30/noticed35, capped at their units. No other requests through61. Deferred units automatically eligible at60; no repeated notice required.

| Range/event | Public information and choices | Fixed branch-independent realization |
|---|---|---|
| day39 barrier | PM considers keeping broad market participation versus cash. Operating partner commits reserve, elects gate or full pay. Prospect5m cannot fund until60; it is NOT cash | All marks100 through42; no shocks/dividends. Offer is declined in benchmark scripts; admission optional only under shared contract |
| day39 research | Cost1, reveal day40 PUBLIC_MARK | Public index-company earnings survey suggests improving demand with uncertainty, not a target return; liquidity research reveals next-window BEAM capacity contract, not future price |
| day40 EXEC_A | Package/limit committed earlier; execute then re-evaluate all limits | BEAM100/volume840,000. EXEC_B BEAM volume0 (other instruments default). Original42,000 and32,000 comparison branches retain reference fills99.900000/99.920975 |
| day40 close /41 admin | Deal6m or gate20% of true post-cost/post-fee NAV, pay T+1 | New day39/40 management/carry charges exist; old normalized branch dollars remain unit-test oracles only. Dollar requests convert to units using certified series values; accepted units burn once |
| day43 PUBLIC_MARK | Publish broad rally; investors can understand the gated exposure retained | BEAM104 through day59; other marks100. No named thin-stock catalyst. Gate retained an extra10,000 BEAM shares versus reference full pay: incremental gross mark gain40,000, before expenses, versus deferred LP exposure/fee/concern costs |
| day55 barrier | Next-window reserve and reduction choice | Forecast deferred-unit redemption at current values; full-pay has no carried claims. Don't guarantee future dollars |
| day58 EXEC_A | Existing signed gate contingency sells20,000 BEAM unless revised to another feasible plan | BEAM104/default volume; settle59. Hold at least$1.25m for deferred claims before discretionary debt sweep. Price/tape known only at its time; capacity schedule known from liquidity card |
| day60 /61 | Price all remaining carried units, no second gate in reference S2; pay | BEAM103 at day60 PUBLIC_MARK and executions; other marks100. Ordinary fees/carry/settlements. Case ends with zero deferred units/overdue investor claims and all hard deficits cured |

**Alternatives/outcomes.** S1 full pay,42,000 BEAM sold40, no new positions/extra gate, retain funding for invoices. S2 gate/32,000 sale, then20,000 sale58 and full next-window payment. These are contrasting control/exposure/liquidity choices, not a claim gating is best. Both require dated independent projections, all issuer/sector/ETF/credit/margin tests and unit/cents reconciliation; the original reference payment cash195,800/197,976.96 excludes future charges. The gate's confidence penalty is real and claims float; its additional $40,000 mark gain does not establish net superiority. Optional admission cannot be counted until funded and certified.

F1 no sale/no gate creates post-flow gross160.5263%/net107.8947% at the isolated checkpoint; enter passive mandate remediation. It is NOT necessarily payment default: available debt capacity may cover cash, subject to collateral/rules. F2 a late sale after40 EXEC_A cannot settle41, but the engine must compute actual permissible credit before calling payment impossible. Recovery sells liquid holdings at41 or later, cures exposure and preserves truthful late-claim history if any. Separate halt variants are new fixed scenario versions, not reactive punishment. Success at61 requires positive NAV, no overdue dealt/remaining deferred claims, reconciled reports, mandate compliance and equal-treatment gate allocation. No full-season return hurdle or unfair comparison with Case1.

## Case3: The report is balanced, the NAV is wrong

**Start/end.** Day29 OPEN_ADMIN (12 February) through day41 OPEN_ADMIN (2 March), with a missed-payroll cure continuation to day45 CLOSE only if necessary. Fund opening erroneous recorded values match old oracle: cash5.035m, restricted4.8m, long22.5m, short4.8m, fixed management payable35,000, reversible provision500,000, apparent NAV27m. Six longs ALTO/COVE/ELAN/GALA/IONA/JUNO30,000 at100 ($18m), BOND45,000 at100 ($4.5m); BEAM short100,000 at48. All original series HWM100; allocate pre-performance B27.5m in unit proportions. The missing200,000 distribution payable is the sole opening discrepancy, not genuine return. Broker/admin truthful opening evidence is B27.3m/F460,000/N26.84m. Correction expense is allocated using opening gross participation, with fee reversals and per-series residuals.

BEAM cum-date day28 preceding close was50; distribution entitlement100,000 short shares×2, ex-date29, payment day34. Opening journal incorrectly included its200,000 price gain but omitted expense; run ex-date economic identity only once (the correction links to that event). Do not create another short price gain by changing48 again. All marks stay at opening values29–41 except ALTO:102 at day33 opening then unchanged. Extra $60,000 long ALTO gain is an explicit future market consequence, not a reward for using confidential information.

Firm cash72,000, payroll payable12,000 from26–28; seeded earned management receivable35,000 due41, all other past costs paid. Daily new fee accrual continues and is separately invoiced at40 due41; therefore47,000 is the **isolated seeded-receipt cash oracle**, not full-run cash. Baseline weekly bill20,000. Active hiring is removed: it had no defined useful capability and merely worsened cash. Old hire29k/6k-arrears calculations remain a labeled dominated forecast example, outside distinct-success counting.

| Event | Information/action | Fixed consequence |
|---|---|---|
| day29 public/barrier | Both see broker dividend confirmation/admin break. Correct now versus prioritize other work while certification remains blocked | Routine investigator produces exact correction evidence free; no assignment needed to make accounting true. Preserve wrong/original report |
| day29 research packet | Explicitly flagged ALTO private sales schedule | Restrict ALTO buys/sells/resting orders until public release33; no self-clearance. Mandatory broker disposition policy remains separate |
| day29 allocation | Two assignments remain for team in chapter3 warm start: one owned each; qualification already done | One assignment completes LP diligence, reveal day31 opening; one can investigate public portfolio-capacity evidence, reveal31: the BEAM dividend is a financing cost rather than free short alpha, and BOND has negative rates-up sensitivity; the card suggests reducing a large duration concentration or retaining cash, without predicting a price. No card guarantees a payoff on this flat reference realization. Verified report needed35, funding conditional; spending both on portfolio evidence loses this offer, not investor solvency |
| day30 close /31 | Baseline weekly payment20k; no hire | Seeded-receipt-only cash52k. LP offered up to5m at standard terms, optional cap in1m increments |
| day33 | Public ALTO release/102 mark | Clear restriction via recorded event; any subsequent order waits next eligible execution. Past restricted orders remain canceled |
| day34 admin | Pay missing distribution200k | Reduce cash/payable once, no repeat expense. Correction complete before certification |
| day35 close | Certification deadline/diligence condition; weekly payment | Missing certification forfeits prospect; no guessed NAV. Seeded-only company cash32k |
| day39 admin | Funded prospect escrow appears if diligence/report passed | Escrow outside fund until40 admission; no company revenue. Players can decline/cap to avoid mismatched capacity |
| day40 close /41 admin | Weekly20k payroll; optional certified admission; invoices/payments | Seeded-only cash12k then47k; full cash adds actual new collected fees, after due arrears. Provision460k (plus subsequent changes) still not spendable |

**Meaningful choices.** PM chooses public evidence versus using an assignment to support offered capital's capacity, and plans a permitted portfolio under current restrictions. Managing Partner chooses diligence versus reserve attention, proposes admit5m/cap/decline, and preserves cash for fixed claims. Both approve admission; generating truth is automatic. S1 correct promptly, allocate diligence, admit/cap funded LP after checking post-flow capacity. S2 correct promptly, decline optional capital after reviewing current capacity and keep the firm lean; lower AUM/fees, same honest core success. Portfolio-capacity research is optional, not a claimed useful alpha alternative or required second-path unlock. These alternatives use existing mechanics rather than inventing an operations hire reward. F1 ignore the break through35: lose offer, cannot certify dealing; late correction restores reporting but not missed opportunity. F2 fund fee payment unavailable in a separately authored stress version leaves genuine company arrears; do not manufacture this failure on the base cash-rich tape. Recovery truthfully corrects/report/reduces permissible costs and follows five-day cure/termination contract.

**Independent oracles.** Opening correction:200,000 liability,40,000 provision reversal, net NAV26.84m; inter-entity35,000 invoice matches. Restriction mutation/future-information tests; cash payments never repeat expense; a5m subscription issues its own100/HWM100 series and adds zero company cash; full management receivable/payment ledger includes changing daily bases. Both successful scripts require corrected certified report, no prohibited trade, positive fund NAV/company cash at41 and honest LP/cash statements; admission is optional. Independent full-date totals, compiler JSON, race outputs and actual enjoyment remain pending.

## Compilation and certification gate

Defaults plus overrides completely specify these design tapes. There is still **no compiled executable tape or simulator** in this checkout. FF0a materializes Case1 first, records hashes, independently finishes daily oracle totals and fixes any infeasible reference script by a documented version change. FF6a compiles Cases2/3 before implementing them. The full opening 1–20 campaign and full60-day market tapes remain separately unauthored; challenge warm starts cannot be substituted for them. Exact per-path accrued totals are pending oracle work, explicitly separate from the old no-extra-accrual checkpoints. A record-complete design is not a proven viable scenario.


---

Source: `docs/IMPLEMENTATION_HANDOFF.md`

# Precise implementation handoff: FF0a only

7 October 2026; source plan v2.2. No feature implementation occurred in this planning update.

Planning revision 2.2-M1 expands all 20 milestones through the final FF8 gate in [MILESTONE_PLANS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\MILESTONE_PLANS.md). [PLAN_REVIEW_AND_DECISIONS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\PLAN_REVIEW_AND_DECISIONS.md) assigns unresolved choices/evidence to their due phases. Read the selected detailed package before starting; a roadmap row alone is not an implementation brief. This continuation entered an already modified planning tree; the original clean-entry statement below refers to the first v2.2 review. Preserve the combined changes. The user has now explicitly authorized committing/pushing this completed planning package; no application work or installation is authorized by that request.

## Verified starting point

Local `C:\Users\krish\fundforge`, entry HEAD `51eda0c1aa806e0c9f94b7e2527a013b4dedb77f`, clean at entry. Current planning changes are uncommitted; preserve them. Documentation-only: no Python/Pydantic application or26 tests. Instructions, recent history, all requested docs, fixtures, two Python scripts and reviewer prompts were inspected. No IMPLEMENTATION_HANDOFF existed. Inspect status/HEAD on continuation; remote visibility/other checkouts unverified.

## Exact next milestone

**FF0a: compile Case1's v2.2 authored schedule into a complete validated immutable fixture, command scripts and independently calculated dated financial oracle.** This is the next implementation task, not authorization to build features during this review. Read CLAUDE_HANDOFF, DESIGN_REVIEW_V2_2, SCENARIO_CONTRACTS shared+Case1, FUND_ACCOUNTING, architecture numeric/command contracts and X01–X07 below. Do not run the old full-scaffold FF0 prompt.

Inputs: isolated arithmetic cases and explicit12–21 warm start/default tape/evidence/recall/replacement schedules. Proposed outputs: `fixtures/compiled/case1.v2_2.json`, `fixtures/commands/case1_{early_cover,replacement,forced_recovery}.json`, `docs/oracles/CASE1_DATED_ORACLE.md` with full daily fund/series/firm/claims/residual table, coverage/hashes, `backend/contracts/` loader/schema, `scripts/validate_scenarios.py`, `tests/contracts/` meaningful rejection checks. These paths do not yet exist.

Own only contracts/materialized records/independent worksheet/schema-loader/checks. Use standard-library validation for FF0a; reconsider Pydantic only at a demonstrated API/schema boundary. Economic truth must not depend on coercion. No economic reducer, Next.js/FastAPI/DB scaffold, provider calls, SEO/AI or deployment in FF0a. Source-control publication is separately authorized in the current planning session and does not authorize features.

| Case | Exact required observation |
|---|---|
| X01 complete coverage | Every business date12–20 has OPEN_ADMIN/PUBLIC_MARK/EXEC_A/EXEC_B/CLOSE, all intervening calendar accruals, and day21 admin. All twelve marks/volumes/borrow/IDs, defaults materialized; end before21 market |
| X02 warm start | Assets32.5m−shorts5m−debt2.5m=25m;100k/80k/70k units,H100,F0; company240k/payroll payable4k. All economic/settled/borrow quantities, lot bases, claims explicit and independently checked |
| X03 chronology | Evidence after assignment; recall13, acceptance cutoff14, transfer15, stress16, sale opportunity18, BEAM halt20, dealing20/payment21. Future file data never player-visible at12 |
| X04 borrow | Timely acceptance transfers1,250 shares15 with no double loan; old fee ends/replacement40% starts prospectively. Late selection rejected, no cure. Cover satisfies execution deadline but fees/collateral persist through pending return |
| X05 independent dated oracle | Three scripts list actors/commands/budgets/approvals, all dated fee/carry/payroll/collateral/settlement/series/redemption postings and terminal balances. Success satisfies actual constraints, not100k bounds. Failure distinguishes forced control loss from default. Expected values do not come from a future reducer |
| X06 rejection | Missing date/mark, duplicate ID, unknown action/instrument, float/NaN/infinite money, negative volume, wrong units, conflicting fee timing, timestamp disorder, uncovered obligation each produces specific error, not silently valid package |
| X07 reproducibility/status | Repeated compile/load identical canonical bytes/hash including residuals; schema/rule/tape/control/command versions and source hashes. Label SCHEMA_VALID_AUTHORED_FIXTURE, never PLAYABLE/PASSED_ENGINE. Loader tests distinct from package arithmetic |

Done when X01–X07 evidenced, full-path numbers independently derived, conflicts resolved, actual commands/hashes retained, bounded review completed and handoff advances to FF0b. If a script is infeasible, report exact constraint/shortfall and change only a versioned authoring decision, then recalculate. Never fit a hidden tape to a player's holdings. Stop after FF0a; remaining gates need their own task.

## Continuation after the next milestone

FF0b freezes numeric/wire/checkpoint vectors, FF1a builds journal/valuation primitives, FF1b adds dated fee/series history, then FF2a execution and FF2b risk. FF2c owns the integrated pure session/payment/payroll/independent Case1 control path; FF3a owns real human command authority. Both precede FF3b's internal human experiment. Persistence/general investors follow FF4; first playable certification is FF5c; full initial-game certification is FF6c. FF7 historical/advisory and FF8 extension selection remain elective. All 20 are currently pending; completed documentation is not their acceptance evidence.

At each gate produce `docs/evidence/<milestone>/RESULTS.md` with exact executed commands, expected/observed results, input/rule/tape/control hashes, failures/limitations and one next task. Do not auto-run the whole roadmap because it is documented. Full ordered tasks, module ownership, decision deadlines and proposed commands are in MILESTONE_PLANS.

## Environment and checks

Observed Python3.14.3; python/node/npm on PATH. `psql`/`soffice` not found by Get-Command (not proof none installed elsewhere). Active Python lacks python-docx. Bare old validator failed cp1252 decoding; UTF-8 retry failed eager docx import. Tooling now uses explicit UTF-8 and original standard-library Word fallback; PACKAGING_VALIDATION records final actual commands/results. No installed dependencies, database/application/race/playtests, provider or deployment work. Word archive/XML/content can be checked; page rendering unavailable.

Actual documentation commands: `python scripts/build_documents.py`, `python scripts/validate_design.py`. State commands: `git status --short`, `git log -5 --oneline`, `rg --files`. Future `python scripts/validate_scenarios.py fixtures/compiled/case1.v2_2.json` and `python -m unittest discover -s tests/contracts` are proposed interfaces until files exist, not working commands. Packaging counts are not26 application passes.

## Decisions and unresolved assumptions

Accept issuer fix, settled replacement timing, retained collateral, narrow winddown, operating commands, removal of dominated hire, extended gate horizon, exact precision/retry, early human experiment. All reviewer dispositions are in DESIGN_REVIEW_V2_2. Reject artificial hire payoff, extra dependencies/guaranteed alpha. Preserve old research snapshots; fresh source scope is in SOURCES. Full opening campaign tape, full-path oracle totals, release/DB/auth choices, balance/enjoyment remain unverified. v2.2 overlays old isolated fixtures; never use checkpoint values as complete dated-run outputs.

Claude continuation: Read this handoff and verify the current repository state before editing. Critically review the revised plan using bounded financial, gameplay, and engineering reviewers. Resolve concrete contradictions and improve weak acceptance criteria before implementation. Then implement only the next agreed milestone, validate it against the documented acceptance cases, and update this handoff with evidence and the next task.


---

Source: `docs/PLAN_REVIEW_AND_DECISIONS.md`

# Milestone-plan review and decision register

7 October 2026, planning revision 2.2-M1. This pass reviewed the existing local v2.2 work and expanded all 20 milestones through FF8. No new application/reviewer/test result is claimed. Earlier three-agent findings remain in DESIGN_REVIEW_V2_2; this follow-up was performed by the primary agent. The entry tree was already modified by the previous planning task at HEAD51eda0c; that work has been preserved. The user subsequently authorized committing and pushing the completed planning changes.

## Findings accepted in this planning pass

| ID / priority | Existing evidence / consequence | Planning correction | Owner / acceptance |
|---|---|---|---|
| M01 / P0 | IMPLEMENTATION_PLAN had one row per milestone; no ordered tasks or per-package stop gates | MILESTONE_PLANS defines inputs, owned paths, ordered tasks, outputs, independent acceptance, failure/stop and next task for all 20 | Every roadmap ID must have exactly one matching detailed package |
| M02 / P0 | Pure modules plus narrow payment did not explicitly name a shared date/phase runner before FF3b | FF2c owns pure all-or-none session runner, checkpoint and full scripted economics; FF3a plugs human authority into it | Actual dated Case1 transitions, not scripted balance assignment, before human experiment |
| M03 / P0 | Fixed path controls cannot certify arbitrary human actions; general controls appeared only at FF6a | FF2c derives narrow Case1 broker/admin controls independently; FF6a generalizes them and intentionally wrong-report lifecycle | Separate derivation may share value types but cannot import posting/fee/risk functions under test; actual allowed paths certify or show break |
| M04 / P1 | FUND_ACCOUNTING permits10-business-day winddown but challenge/base tapes stop21/41/61 | Explicit recovery-tail artifact before claimed winddown completion; first prototype never claims terminal liquidation without tail | FF5a/FF6a/FF6b tail coverage, V31–V32; preserve unresolved positions/claims on shortage |
| M05 / P1 | FF6a wording mainly 'compile' although controls/restrictions still need mechanics | Detailed FF6a implements independent controls, correction/restatement, restrictions and offer predicates using verified economic modules | V12,V14,V28–V30 plus original/corrected report and deadline evidence |
| M06 / P1 | FF7a data import alone could be called historical replay | Optional FF7a includes one shared-engine historical case, eligible resolution/fill policy, rights/vintage and independent lifecycle oracle | Import valid != replay valid; unavailable rights/coverage leads to defer/reject |
| M07 / P1 | FF5b real identity choice absent; early prototype actor selection risks becoming auth claim | Explicitly separate controlled local harness, persisted development-auth seam and first-playable protected sessions | FF4a is race authority; FF5b provides unforgeable actor/member/session enforcement and access tests |
| M08 / P1 | FF8 contains unknown future product requirements | Fully specify an extension selection/design gate; implementation scope waits for one actual selected story | No speculative derivatives/live/league/hosting build or irreversible activity without selected contract |
| M09 / P1 | Handoffs said 'clean at entry' without distinguishing subsequent planning turn | Record first-review clean entry versus current dirty planning entry and pending/pushed status honestly | Current Git evidence and publish record; don't discard earlier uncommitted docs |

No new finance/trading frameworks, paid services or feature implementation were accepted. Runtime pins/library maintenance research remains scoped to the future milestone that needs it. A more detailed plan is not evidence any milestone is completed.

## Decision status and due gates

'Resolved design' is a selected fictional/engineering convention, not implemented behavior. 'Open evidence' means a specified contract still needs a calculation or experiment. 'Open choice' needs a bounded choice under actual environment/user constraints. A due unresolved decision blocks only dependent work, not unrelated earlier packages.

| ID / status | Decision or uncertainty | Provisional direction / required evidence | Due milestone / owner |
|---|---|---|---|
| O01 / open evidence | Case1 complete accrued path feasibility and exact terminal amounts | Independently work every date, margin/cash/policy prefix and fee series for early-cover/replacement/forced recovery; old checkpoint and100k allowance remain isolated | FF0a, scenario/oracle author |
| O02 / open edge details | Dollar/rate/unit validation bounds and last-cent/allocation remainder at scale limits | Retain context40, field scales/HALF_EVEN/residual recurrence and stable series-ID allocation. Freeze explicit over-redemption/maximum-bound vectors; do not change policy silently | FF0a validation subset, FF0b complete freeze, contract owner |
| O03 / open choice | Dollar-target request across an LP's multiple fee series | Specify fair within-investor allocation using disclosed rule, then gate across all eligible fund claims; preserve HWM/unit ownership. Case1 unit request is unaffected | FF4b, investor/accounting owner; verify0a unit limits only |
| O04 / resolved design; tape open | Four-instrument first-playable universe and opening exposures | ALTO/BRIN/BEAM/BOND selected; build moderate positions under real delegated limits, complete tape/oracles still required. Twelve-name warm-start challenge is separate | FF5a, scenario owner |
| O05 / open environment choice | Supported Python/DB/driver/migrations/frontend/auth/session versions | Choose minimum compatible stack when needed; record official docs/releases/license and lock it. No provider account needed for synthetic play. Do not expose controlled actor selection as production auth | FF4a storage/runtime; FF5b frontend/identity; integration owner |
| O06 / resolved boundary; implementation pending | Independent controls for non-scripted player paths | Narrow Case1 control derivation before prototype; generalized broker/admin evaluator at6a. Never import tested financial functions or copy current ledger as external evidence | FF2c then FF6a, accounting/control owner |
| O07 / open authoring evidence | Winddown tail markets/liquidity and completion classification | Ten-business-day selected horizon; reuse frozen in-horizon tape, author missing future records. Voluntary winddown cannot mint cash/provisional fees; horizon can end unresolved | FF5a opening recovery; FF6a challenges; FF6b full termination, scenario/game owner |
| O08 / open gameplay choice | Staff capability actually worth its salary/recruitment/severance | Name future competing tasks/reveal timing for each retained hire; test two feasible funded configurations. Remove a dominated hire rather than invent an alpha bonus | FF6b, game/company owner |
| O09 / open experiment | Campaign outcome calibration and enjoyable balanced alternatives | Published thresholds frozen per version; pilot human feedback plus matched policies/held-out versions. No current claim of measured fun or calibrated markets | FF3b, FF5c, FF6c respective gates, game/evaluation owner |
| O10 / open measured bound | Supported concurrency/workload and performance budget | Define hardware/active-seasons/command mix before profiling; record latency/error/lock waits/invariants, select support claim only after measurement | FF6c, engineering/evaluation owner |
| O11 / deferred choice | Exact historical dataset/rights/as-of/retention/era coverage | One demonstrable historical teaching use; licensed immutable records including revisions/actions/universe. Reject nonreproducible/nonentitled data; no inferred historical borrow | Optional FF7a, data owner |
| O12 / deferred choice | One advisory aid, utility target/baseline/model/dependency/cost cap | Default deterministic templates/stress cards. Choose one unmet task, freeze evaluation and spend before runtime; remove if utility absent | Optional FF7b, evaluation owner |
| O13 / deferred user scope | Actual future extension | Choose one requested hosting/live/league/instrument story and its rights/permissions/lifecycle/budget; then write bounded implementation plan | FF8 decision gate, project owner |

## Readiness and evidence index

All FF0a–FF8 application milestones remain PENDING. Actual current checks are documentation build/packaging/reference arithmetic and Git diff consistency only, recorded in PACKAGING_VALIDATION. Future evidence directories/tests/CLIs in MILESTONE_PLANS do not exist yet. No installation, application implementation, database run, human study or provider activation occurred in this pass.

Next executable milestone remains FF0a; then FF0b, FF1a and FF1b. Stop each milestone at its own gate and update the handoff. The full roadmap reaches first playable FF5c, full initial game FF6c, optional historical/advisory FF7 and selected-extension planning FF8. Publishing documents does not advance any application milestone.


---

Source: `docs/MILESTONE_PLANS.md`

# Detailed milestone work packages

Planning revision 2.2-M1, 7 October 2026. All 20 milestones are pending. These plans expand the existing [roadmap](https://github.com/krishbansalofficial/fundforge/blob/main/docs\IMPLEMENTATION_PLAN.md); they do not implement software or claim completed tests. Existing uncommitted v2.2 work is preserved. One builder owns each bounded package; additional agents are used only when explicitly authorized. Application paths and execution commands below are proposed until created by the corresponding implementation task.

## How to execute one package

Before editing, inspect Git status, current handoffs and the selected package's inputs. Confirm its prerequisite evidence actually exists. Resolve that package's due decisions in [PLAN_REVIEW_AND_DECISIONS](https://github.com/krishbansalofficial/fundforge/blob/main/docs\PLAN_REVIEW_AND_DECISIONS.md). Do not rebuild completed research or implement later rows to make the current one appear complete. If an input is missing, identify the specific artifact/contract, repair it within the bounded scope or record a blocked prerequisite; never substitute an assumed result.

Each numbered task is intended to fit one reviewable change. Commit creation is a separate user instruction; this planning request does not authorize commits/pushes. Follow tasks in order within a package; independent calculations may be prepared alongside schema work by the same builder. The default sequence is FF0a through FF6c. After FF2b, FF2c and FF3a are logically independent, but one builder may complete them sequentially. Both must pass before FF3b. FF7/FF8 are optional and never prerequisites for initial-game completion.

**Common evidence contract.** Every package creates or updates `docs/evidence/<milestone>/RESULTS.md`: entry/exit commit and dirty-state description, owned paths, prerequisite evidence references, Python/Node/DB/tool versions actually used, rule/schema/tape/command/control hashes, exact commands and exit codes, expected/observed results, failures/pending checks, limitations and one next task. Attach acceptance-specific artifacts, not just a checkmark. No raw secrets or identifiable tester data. Evidence files do not exist yet. A passing package means its own acceptance cases passed, not that later release gates passed.

**Common completion gate.** No unresolved contradiction in an exercised contract; meaningful cases pass; independent numbers/provenance retained; original journals/inputs not overwritten; source docs and handoff updated; generated review bundle refreshed if canonical text changed. Economic changes preserve deterministic replay and explain their effect. A required unavailable test is pending, not passed. Unit tests cannot satisfy real PostgreSQL races or two-human playtests. Documentation checks today are distinct from all proposed application commands below.

**Common exclusions.** No real money, broker execution, SEO/marketing, hidden AI decision-maker, paid provider activation, mass dependencies, premature distributed system or unsupported compliance claim. Financial truth comes from the original deterministic kernel; player/client/adapters cannot directly post authoritative balances. A requirement that adds no meaningful choice should be automated or removed, with rationale.

## FF0a — Compile Case1 and independent dated reference ledgers

**Purpose and value.** Eliminate missing inputs before builders write economics. A complete authored fixture is a specification artifact, not a playable game. The current isolated shock numbers and $100,000 expense bound are insufficient full-path oracles.

**Entry / inputs.** No application prerequisite. Read SCENARIO_CONTRACTS shared defaults and Case1, FUND_ACCOUNTING including section 10, architecture numeric profile and IMPLEMENTATION_HANDOFF X01–X07. Inventory old JSON checkpoints; retain their isolated status. Decide O01/O02/O03 using the decision register. Use standard-library schema/validation for this package; no dependency installation is required.

**Ownership / outputs.** `backend/contracts/` scenario record types/loader; `scripts/validate_scenarios.py`; `tests/contracts/`; `fixtures/compiled/case1.v2_2.json`; three actor-tagged scripts under `fixtures/commands/`; `docs/oracles/CASE1_DATED_ORACLE.md`; FF0a evidence. These are proposed new paths. No economic reducer, API, DB or UI.

**Ordered tasks.**

1. Freeze the smallest scenario schema covering IDs/versions, calendar/phase/subphase, instrument quotes/volume/borrow, public observations, obligations, openings/series/residuals and policy/authority. Add schema status distinguishing authored/validated/executed; unknown records fail explicitly.
2. Materialize defaults plus every Case1 override for business days 12–20, weekend accrual dates and day21 opening administration. Include the pre-EXEC_B replacement cutoff barrier, prospective loan transfer, zero new BRIN inventory, instrument-ID price shock and BEAM halt. Specify opening references for unused instruments. No RNG or external data.
3. Author fund and company opening account/lot/loan/series balances independently. Declare their preexisting payroll and prior settled fee history; avoid inventing current-price trades to create warm-start holdings. Add exact public versus hidden release times.
4. Write early-cover, replacement-plus-sale and forced-recovery scripts with immutable actor IDs, policy/proposal hashes, quantities, cash ceilings, readiness and event eligibility. Scripts can include state-conditioned remediation with declared calculation; fix their final numbers in the independent worksheet before labeling them viable.
5. Independently calculate every dated mark, cash movement, margin/collateral/credit, fee/carry residual, investor provision/units/dealing claim and company payroll through day21. Record before/after balances and all constraint ratios. Do not copy expected values from the loader or future reducer. Resolve infeasible paths by a documented authored version change.
6. Add loader coverage and adversarial schema rejection checks; publish canonical artifact hashes and the oracle derivation. Retain the original isolated checkpoint values beside their limited scope.

**Acceptance / verification.** X01–X07 must each have evidence: complete records, $25m opening fund and separate $240k company with $4k payroll claim, timely/late replacement, one accrual per date, actual two voluntary paths plus forced-recovery expected balances and exact rejection reasons. A proposed command is `python scripts/validate_scenarios.py fixtures/compiled/case1.v2_2.json`; loader tests use `python -m unittest discover -s tests/contracts`. The financial worksheet is independently reviewed against claims conservation; these commands must not claim engine execution.

**Failure and stop.** Missing tape/control/oracle cells, unpriced obligations or infeasible alleged success block completion. Do not drop expenses to force success. Stop with SCHEMA_VALID_AUTHORED_FIXTURE and an evidence-linked handoff to FF0b; no app scaffold.

## FF0b — Freeze numerical types, canonical serialization and checkpoint schema

**Purpose and value.** Give all later modules one exact definition of money, residuals, identities, economic versions and replay hashes. Prevent incompatible implementations from passing rounded-value comparisons.

**Entry / inputs.** FF0a complete authored package and derivation. Apply the already specified Decimal context/scales and state-version distinction; resolve O02, rather than silently inventing another precision policy. FF0a uses the textual profile; FF0b formally freezes it, so FF0a does not depend on nonexistent FF0b code.

**Ownership / outputs.** `backend/contracts/values.py`, `serialization.py`, command/event/checkpoint schemas; `fixtures/canonical_vectors.json`; `tests/contracts/`; a schema/version migration note. Names are interface intent, not installed framework names.

**Ordered tasks.**

1. Encode field-specific bounds/scales, price-before-cash rounding and explicit Decimal traps. Reject float/nonfinite inputs and extra fields; define string decimal/rate/unit validation.
2. Implement residual recurrence and rate-bucket transfer, largest-remainder allocation and whole-share/unit conversion contracts. Explain where a cent/last unit remains and prohibit over-redemption.
3. Freeze canonical UTF-8 JSON bytes, sorted keys, ordered event arrays, identity-set order, positive zero, fixed decimal strings and SHA-256. List included/excluded fields and prove excluded administrative metadata cannot affect future economics.
4. Define checkpoint state with next pending phase/subphase, unsettled claims/returns, remaining capacity/reservations, rate residuals, authority, LP history and rule/tape identity. Separate economic state_version from administrative_revision.
5. Create independently authored vectors for HALF_EVEN ties, residual thirds, negative zero, numeric overflow, malformed timestamps and save-mid-accrual. Hash fixed expected bytes, not output produced by the function under test.

**Acceptance / verification.** V22–V24 and O02 boundary cases: first three borrow postings 55.56/55.55/55.56 sum166.67 with documented scale24 residuals; identical economic state under audit-time/key-order changes hashes identically; changing an obligation/residual/phase changes hash. Proposed: `python -m unittest discover -s tests/contracts -p 'test_serialization*.py'`. Test object→canonical bytes→object round-trip and checkpoint rejection across incompatible versions.

**Failure and stop.** Ambiguous rounding/allocation or a hash that ignores future-economic state is blocking. Any changed FF0a numerical result requires a versioned fixture/oracle update. Stop at frozen types/wire profile, hand off to FF1a.

## FF1a — Immutable journal, positions and valuation primitives

**Purpose and value.** Create an inspectable balance sheet and history for both entities before execution logic. Every later game consequence must be representable as balanced entries and obligations.

**Entry / inputs.** FF0a openings/oracles and FF0b values/checkpoints; accounting account definitions, FIFO and raw-price/corporate-action rules. A ledger entry cannot rely on future execution/persistence modules.

**Ownership / outputs.** `backend/domain/accounting/` account/chart definitions, journals, lots, marks and obligations; `tests/domain/accounting/`; primitive golden cases. No network or DB writes.

**Ordered tasks.**

1. Define distinct fund/company account IDs, asset/liability/capital/expense/income signs and entity ownership. Import balanced opening journal batches from explicit fixture facts.
2. Post immutable balanced batches keyed by economic identity, preserving source/cause IDs. Derive balances from journal; reject unbalanced/mixed-entity/mixed-currency/duplicate postings atomically.
3. Add economic long lots/FIFO disposal, short liabilities, trade receivables/payables and coherent mark snapshots. Expose NAV, gross assets and settled cash separately; no clamp hides negative NAV.
4. Implement reversal/reposting links and indicative/certified/restated valuation states. A balanced but missing economic event stays distinguishable from a corrupted ledger; independent broker/admin records are external inputs, not another view of the same function.
5. Test primitive distributions and integer lot transformations here; settled-borrow/order/locate propagation is completed with FF2a. Reject unsupported corporate actions rather than partially applying them.

**Acceptance / verification.** A01–A06, A08–A14 within primitive scope: FIFO 10@100 +10@120, sell12@130 realizes320 and leaves960 basis; legacy final cash99,440 plus six shares110 gives100,100 NAV. Borrowing100k adds equal cash/debt, not return. Fee payment against seeded claims clears both books, without repeating income/expense. Replay/reversal reproduces balances. Proposed: `python -m unittest discover -s tests/domain/accounting`.

**Failure and stop.** Failed internal invariant rejects the entire batch; do not plug cash. Do not claim full corporate-action lifecycle or actual payroll processing before later modules exist. Stop at tested journal/lot/valuation primitives; next FF1b.

## FF1b — Calendar accrual, fair series participation and fee history

**Purpose and value.** Ensure carrying a position, earning a fee or receiving new capital changes the correct claim over actual dates. Prevent provisional incentive from financing the firm.

**Entry / inputs.** FF1a journals, FF0b numeric contract, FF0a daily worksheet; exact calendar and fee-series formulas. No live calendars or research libraries are needed.

**Ownership / outputs.** `backend/domain/accounting/series.py`, `fees.py`, `accruals.py`; `backend/domain/clock/` dated calendar primitives; `tests/domain/accounting/` fee/day-count cases; independent series bridges.

**Ordered tasks.**

1. Build synthetic dated business/calendar iterators and unique per-date accrual identities. Initialize immediately before day1; weekend uses original last-mark timestamps, no executable event or company business-day payroll.
2. Accrue management ACT/365 against opening participation, debit/settled-borrow ACT/360 against stated closing basis, with carried residuals and prospective rate changes. Exclude unsettled locates, end borrow only at actual returned settlement.
3. Allocate common P&L/expenses by net capital plus reversible provision. Show sum of participation, common P&L, management liability, provisional incentive and investor net capital.
4. Recompute reversible incentive/HWM; implement pure annual and partial-redemption fee transformations. The actual notice/dealing/payment orchestration comes at FF2c/FF4b. Annual full crystallization takes precedence if same date; preserve survivor HWM.
5. Recognize contractual management revenue/receivable and fixed incentive only when due under contract; keep provisional amount a forecast. Restore halfway through residual/series history and compare uninterrupted result.

**Acceptance / verification.** V01–V05,V08–V10,V20 plus fee portions of L05–L09. The210,000 participation/21,000 gain allocates11,000/10,000; total net226,800. Redeem250 of1,000 at B110k: payable27k/fixed500/survivor F1,500/N81k/H100. Quarter close never crystalizes the whole fund. Friday short/Monday settlement versus Friday cover/Monday return prove endpoints. Proposed: `python -m unittest discover -s tests/domain/accounting -p 'test_fees*.py'` and corresponding accrual tests.

**Failure and stop.** Invalid total participation or missing mark basis produces visible distress/error, not division by zero or silent substitution. A partial-fee helper passing is not a dealing-flow pass. Stop at deterministic dated fees/carry; next FF2a.

## FF2a — Future-event execution, cash settlement and stock-borrow lots

**Purpose and value.** Turn a budgeted intention into an actual later fill, partial position and dated payment. Make liquidity and short financing consequences credible.

**Entry / inputs.** FF1a/b, FF0b types, complete Case1 tape; execution formula, collateral mapping, settlement priority and whole-share rules. Initially call modules with a validated authority object; human command routing comes at FF3a. This seam is private domain code, not a client bypass.

**Ownership / outputs.** `backend/domain/market/`, `execution/`, `treasury/`, `borrow/`; settlement and corporate-action linkage; `tests/domain/execution/`; order/fill/settlement trace. No broker/trading framework.

**Ordered tasks.**

1. Select strictly later eligible events; load coherent instrument reference/spread/volume/borrow/quality. Track per-event total participation capacity and separate buy/sell cumulative impact quantities.
2. Implement immutable market/limit order budgets and partial-fill policy, DAY/chapter expiration, cancellation and explicit closing/opening reversal legs. Compute largest affordable whole-share limit fill; no OHLC inference.
3. Translate fills to economic holdings and trade obligations using the existing journal; price-round then cash-round once. Reserve/release remaining notional, credit and locate capacity without booking reservation expense.
4. Settle T+1 gross obligations in allowed netting sets; short proceeds restricted, active shorts marked, covered target frozen until matched return. Failed receipts do not fund payments; failed return keeps loan/collateral.
5. Propagate supported distributions/splits through settled/economic shares, pending deliveries/returns/orders/locates once. Preserve original mark/action IDs; raw executable prices plus explicit distribution, never double income.

**Acceptance / verification.** E01–E05,E08–E09,E12–E15,V04,V10–V11,V25. Splitting a ticket cannot reset impact/capacity; buy at known prior close denied; halt yields zero fill. Case1 2,106 BEAM sale94.905 yields199,869.93, cost200.07; 1,250 BRIN cover110.11 yields137,637.50 payable with frozen137,500 collateral. The V25 unsettled sale/mark/return case rejects double top-up. Proposed: `python -m unittest discover -s tests/domain/execution`.

**Failure and stop.** Insufficient resources rejects or fills only preauthorized affordable quantity; no negative settled cash. Partials expose remaining obligations and event capacity. Stop at tested execution/settlement lifecycle, not complete risk/governance; next FF2b.

## FF2b — Complete risk vector, replacement borrow and crisis escalation

**Purpose and value.** Make timely voluntary choices matter without letting signatures waive solvency or mandate. Distinguish leverage, equity margin, actual settlement cash and company risk.

**Entry / inputs.** FF2a and Case1 full oracle; risk coefficients/deadlines/quantities, replacement acceptance/transfer contract and stress sensitivities. Use original deterministic calculations, no optimizer or fitted VaR.

**Ownership / outputs.** `backend/domain/risk/`, `treasury/forecasts.py`, `borrow/replacements.py`, `incidents/`; `tests/domain/risk/`; exact explanation/reason-code snapshots.

**Ordered tasks.**

1. Calculate gross/net, equity issuer/sector caps, separate ETF caps, signed stress factors, initial/maintenance equity, debt-line use and dated cash adequacy including reservations/claims. Tag every result by denominator/as-of/input quality.
2. Preview every executable order prefix and anticipated redemption; track deficit changes individually. A cover may raise net exposure; emergency reduction cannot worsen another hard deficit.
3. Implement timed inventory reservation/settled loan replacement. Case1 zero new BRIN inventory prevents cheap cover/reopen; original unaffected11,250-share loan keeps2%, replaced1,250 switches40% on15.
4. Implement watch/call/remediation/cure/default incidents with simulation deadlines and cancellation of risk-adding remainder. Process due recalls, then authorized voluntary margin cure, then residual forced margin action; recheck after each partial fill.
5. Add deterministic forced priority/tie-break and shortage/halts. Explanations identify the specific ratio/cash obligation, feasible remedies and remaining deficits, not a generic red meter.

**Acceptance / verification.** A22,V06–V07,V26–V27,E06–E07,E10–E11; Case1 complete dated before/after snapshots. Separate unreduced reference23.125m NAV/23.2375m maintenance gap112,500 from the actual paid-fee/modified-book path. Short cover with100 cost beyond net100% rejected unless another safe prefix fixes it. Debt-funded redemption cannot restore investor equity. Proposed: `python -m unittest discover -s tests/domain/risk`.

**Failure and stop.** Forced liquidation can fail to cure; record original liabilities/passive breaches rather than invalidate mandatory fills. Stale/missing marks block decisions that require certification. Stop at crisis state-machine correctness; then FF2c and FF3a.

## FF2c — Case1 investor payment, firm payroll and pure session runner

**Purpose and value.** Close the economic loop needed by the early human experiment. Merely prescribing an investor payment in a script is insufficient.

**Entry / inputs.** FF1b/FF2b and independent Case1 daily ledgers; Tactical10,000-unit notice/dealing, company payroll/cure and daily close order. Do not require generalized gates/subscriptions or DB.

**Ownership / outputs.** `backend/domain/investors/` narrow notice/claim/dealing functions, `company/` baseline payroll/receivables/cure, `backend/application/in_memory_session.py`, `backend/tools/run_scenario.py`, `tests/scenarios/`; Case1 full economic traces. The application runner is in-process, not deployed API or persistent authority.

**Ordered tasks.**

1. Wire pure modules into one date/phase/subphase reducer applying effects all-or-none in memory, with event identities and next pending phase. This fills the previously implicit integration seam; individual modules cannot own their own clocks.
2. Validate Tactical notice/units; at certified20 close allocate fee/crystalize only dealt units, cancel units and create claim; pay only at ordinary21 admin after actual settlement/weekend carry.
3. Accrue/pay baseline company payroll from company cash, collect earned due fund fees as matched inter-entity transfers, and enter/cure timed company distress. No fund-payroll or provisional-fee bailout.
4. Derive narrow independent Case1 broker/admin controls from opening facts, confirmed fills/settlements, raw marks/rates and separate fee/series derivation. They may share exact value types, not the posting/fee/risk functions tested. Support allowed non-scripted prototype choices; a different script's fixed statement cannot certify them.
5. Execute all FF0a command scripts with validated domain authority placeholders; compare every dated fund/series/loan/firm/claim value to independent worksheet, not only terminal totals.
6. Capture complete checkpoints; resume after Friday close/weekend/settlement exactly once. Produce pre-flow/flow/payment/weekend bridges and incident causes for later UI.

**Acceptance / verification.** V02,V06,V08,V09,V16,V18 and full Case1 success/failure oracles. One notice, one dealt claim, one payment; no quarterwide incentive fee. Default/forced recovery retains liabilities. Proposed `python -m backend.tools.run_scenario --scenario fixtures/compiled/case1.v2_2.json --commands fixtures/commands/case1_replacement.json --output docs/evidence/FF2c/replacement` plus `python -m unittest discover -s tests/scenarios -p 'test_case1*.py'`; this CLI does not exist today.

**Failure and stop.** A same-source expected/output comparison does not pass. Any stage drift or unpaid claim must be explained numerically. Stop at real pure economic Case1 closure; FF3a must add actual human authority before FF3b.

## FF3a — Human authority, readiness and resource reservation commands

**Purpose and value.** Enable complementary independent actions inside agreed boundaries, with material exceptions needing the other human. Prevent repetitive approvals and silent authority expansion.

**Entry / inputs.** FF2b contracts, FF0b command values and GAME_SYSTEMS sections2/12. FF2c is not necessary to isolated governance tests, but both are prerequisite to the integrated human challenge.

**Ownership / outputs.** `backend/domain/governance/`, `backend/application/commands.py` in-memory coordinator, actor membership/role contracts, resource reservations; `tests/domain/governance/`. No production identity SDK or PostgreSQL safety claim yet.

**Ordered tasks.**

1. Define exactly two partner IDs, actor-bound roles, immutable proposals/sleeves and version/content/policy/scope/expiry signatures. New/edit/counter proposals require fresh distinct approval; nonowners cannot expand themselves.
2. Route submit/cancel/order package, AssignResearch, TreasuryReserve and SelectReplacementBorrow through typed permission/resource checks. Link receipts/claims/reserves so the same liability is not double-reserved.
3. Store in-memory idempotency scope and payload conflicts; return original accepted result on identical committed retry, reject same-key changed payload. New/stale requests obey exact economic-version policy; auth checked even for old results.
4. Bind Ready to window/economic version/plan digest while updating administrative revision only. Financial/plan mutation clears both; advance needs two matching ready partners. Disconnect/hold cannot advance simulated deadlines.
5. Remove fixture authority placeholders from human-accessible routes. Recheck current restriction and authority at each partial fill; preserve system forced-action rules separately.

**Acceptance / verification.** C02–C07,C09,C11,C13–C16 in pure sequential/order-permutation scope; actor self-approval/third-user attempts denied. Each routine permitted ticket avoids a fresh approval. Two consecutive ready commands on unchanged economic version permit one advance; reserve/order mutation invalidates both. Proposed: `python -m unittest discover -s tests/domain/governance`. Pure simulations do not establish real DB concurrency.

**Failure and stop.** Disagreement leaves existing approved policies active and window paused, not auto-consent. Stale authority denies addition without losing recorded original economics. Stop at correct in-memory authority; next FF3b after FF2c.

## FF3b — Internal two-person crisis experiment

**Purpose and value.** Test whether interacting finance obligations create enjoyable cooperation before UI/content breadth. This is an internal challenge prototype, not the first playable release.

**Entry / inputs.** FF2c full economic traces and FF3a human command routing, Case1 fixed artifacts, playtest protocol. At least two viable independent scripts must already satisfy the financial oracle.

**Ownership / outputs.** `prototype/` minimal local CLI or single-page adapter, actor-tagged action history, checkpoint/resume, deterministic explanatory debrief; anonymous FF3b observations. Choose the simpler interface; no Next.js scaffold is required here.

**Ordered tasks.**

1. Build one command desk showing next binding obligations, public evidence, cash/NAV/company distinction and actionable constraints. Show a small table of choices instead of a dashboard suite; hidden tape stays outside observation output.
2. Let two controlled local identities sign/act/read/ready independently with actual domain commands. Identity selection is disclosed development harness, not production authentication or isolation evidence.
3. Run three pairs through the fixed challenge using the existing unmeasured20–30minute target; no facilitator financial solution unless intervention is explicitly logged. Rotate role assignment across pairs.
4. Record consequential choice/effect per role, approval-only wait, misunderstood cash/deadlines, actual duration, failure/recovery explanations and desire to continue. Allow save/disagreement/resume; no real-world absence penalty.
5. Separate presentation defects from finance failures and authored dominance. Improve clarity/options within a versioned change, rerun affected economic checks and report remaining problems before advancing.

**Acceptance / verification.** R06/G09–G14 and prototype protocol: both roles can change future feasible actions/resources; neither becomes merely an approval queue. Exact replay/resume hashes still match. Retain raw anonymous observations; absent pairs mean pending human gate. Financial scripts cannot satisfy this gate. No promised fun result.

**Failure and stop.** Repeated role starvation or inability to explain a binding obligation blocks progression to the richer UI. Repair choice/info design, not add another library/dashboard. Case1 prototype demonstrates within-horizon voluntary/forced recovery; it cannot claim completed winddown beyond its supplied tape. Explicitly show an unsupported tail as unresolved, or author/test a bounded tail before exposing that ending. Stop with explicit GO/REVISE decision and limitations, then FF4a if passed.

## FF4a — PostgreSQL authority, atomic transactions and minimal API

**Purpose and value.** Replace the development in-memory store with durable authority capable of two concurrent clients and safe retries/crashes. Keep one season serialization boundary across fund and firm.

**Entry / inputs.** FF3b go evidence, FF0b types and FF3a coordinator policy. Resolve O05 supported Python/PostgreSQL/driver/migration/auth-boundary choices when implementation is authorized. Actual DB provisioning is a future implementation step, not this documentation task.

**Ownership / outputs.** `backend/adapters/persistence/`, `backend/application/coordinator.py`, minimal FastAPI `backend/api/`, migrations and runtime locks; `tests/integration/`; local setup/restore guide. No Redis, distributed worker or externally hosted identity required.

**Ordered tasks.**

1. Freeze supported local runtime and one direct DB access/migration strategy; pin/lock only required dependencies and document clean setup. Define a replaceable development-auth seam that cannot be mistaken for production credentials.
2. Create season/member/command/event/journal/state/obligation/series/order/reservation/outbox schema with exact NUMERIC scales and identity uniqueness. Persist all future-economic checkpoint state; fail overflow before DB coercion.
3. Implement current membership→season lock→idempotency→new-request version/authority/resources→atomic effect/result/outbox order. Fixed season/entity/obligation lock order; domain calls do not commit independently or perform network calls.
4. Expose minimal command submission, current permitted state, history and checkpoint endpoints using the same reducer. No client-supplied financial result or forecast can replace server state.
5. Add separate-connection barrier races, commit fault injection and bounded timeout/deadlock retry. Persist original committed result even after version/market change; replay from stored events restores exact economic state.

**Acceptance / verification.** C01,C07–C10,C13–C16,V16,V18; one winning mutation, no loser journals/reserves/events, atomic matched fund/firm transfer, crash before commit rollback, after commit deduped recovery/outbox. Repeat100 trials per declared race/environment; record allowed result pairs and lock/isolation settings. Proposed: `python -m unittest discover -s tests/integration -p 'test_postgres*.py'` against documented test DB, never a user's existing database. Missing DB means pending, not SQLite pass.

**Failure and stop.** Infrastructure error rolls back, bounded retry preserves key/payload, no partial success. Outbox publication occurs only after commit. Stop at durable command authority and minimal API; real production-facing auth/tenant UI is FF5b.

## FF4b — General LP contracts, dealing, escrow and management-company survival

**Purpose and value.** Generalize narrow Case1 obligations into the initial-game investor and company lifecycle without rewriting tested economic primitives.

**Entry / inputs.** FF1b, FF2c narrow dealing/payroll and FF4a persistence. Selected standard investor terms, gate/escrow allocation and distress rules; resolve O03 unit/cent edge cases first.

**Ownership / outputs.** `backend/domain/investors/`, `company/`, `game/relationships.py`; API command adapters, persistence fields; `tests/domain/investors/`, `tests/integration/`; complete dealing/firm forecast traces.

**Ordered tasks.**

1. Implement notice lead/lockups, unit requests and dollar-target conversion, maximum of external versus confidence request, queue identity and carried eligible units. A notice is not yet an NAV liability.
2. Deal only on certified post-fee pre-flow NAV; joint gate elected beforehand, one pro-rata fund cap, accepted units burn once, rejected/deferred units remain invested. Preserve HWM/provision history; no first-arrival favoritism.
3. Stage funded prospect escrow outside fund until eligible admission; create new fee series at100/H100; contribution never becomes performance or company revenue. Enforce capacity/certification, cap/decline options and no instant funding.
4. Generalize earned/fixed/incentive receipts, weekly payroll/provider claims, 13-week forecast and five-business-day company cure. Separate cash runway from receivable-based forecast and provisional fees.
5. Apply confidence/concern/report/meeting transitions once with component IDs; visible bands, fulfilled-evidence recovery, no repeated meeting/report reward. Test fee/flow/payment and cross-entity concurrency together.

**Acceptance / verification.** L01–L12,V01–V03,V06,V13,V15–V16,G05/G08; gate10m requests on25m deals5m fairly, ineffective gate no confidence penalty. Redemption shrinks NAV once before payment; valid investor entitlement cannot be refused for leverage. Paid matched fee receipt cannot directly move LP capital to payroll. Proposed: `python -m unittest discover -s tests/domain/investors` and PostgreSQL subscription/payment races.

**Failure and stop.** Uncertified close records missed dealing incident, not guessed unit price. Unpaid claims/company arrears persist and trigger authored cure; no rescue subscription unless actually eligible/funded. Stop at standard flows/firm lifecycle; next FF5a.

## FF5a — Author the ordinary zero-position two-chapter campaign

**Purpose and value.** Turn a warm-start engineering challenge into an actual fund launch with credible constrained initial decisions. Prove the opening authority can build the proposed book.

**Entry / inputs.** FF3b human observations, FF4b mechanics, existing SEASON_SCENARIOS opening goals. Resolve O04 four-instrument scope and observation schedule; inherit12-instrument challenge coverage only as a separate artifact.

**Ownership / outputs.** `fixtures/compiled/opening.v2_2.json`, public briefs/evidence/contingencies, actor-tagged success/wait/failure scripts, independent daily control records/oracles; scenario and information rule modules; `tests/scenarios/` opening gates.

**Ordered tasks.**

1. Freeze the opening tradable universe ALTO/BRIN/BEAM/BOND, base25m three-series/300k company opening and two joint sleeves with one owned by each partner. Nontradeable names cannot enter via arbitrary IDs; Case1 remains twelve-name warm start.
2. Author all business1–20 plus day21 administration and calendar accrual records. Choose a modest located short/long book under actual5% ticket/15% sleeve chapter turnover, not the inherited130%-gross challenge book.
3. Schedule research/public evidence, contingency/borrow recall and formal Tactical notice. Give PM a meaningful exposure/evidence choice and operating partner independent reserve/borrow/attention tradeoffs each chapter. Public obligations inspectable; future price outcomes remain hidden.
4. Create two strategically defensible success scripts, cash/wait baseline and an explainable failure/recovery script on the same tape. Use independently calculated journal/control/series totals for each; include post-flow ratios and due investor/firm cash.
5. Integrate observations with server as-of filtering: mutate future/revised facts and show earlier brief/chart/export state unchanged. Build causal debrief references without fabricated counterfactual profits.
6. Add bounded liquidation-tail fixtures for failure paths and declare final unresolved obligations if the tail cannot settle. Tail behavior follows O07; finishing21 without liquidation does not turn remaining holdings into cash.

**Acceptance / verification.** Opening contract from MASTER_SPEC/SEASON_SCENARIOS, I01–I04,I14,G09–G11,V09/V18. Both actual success scripts obey all sleeve/mandate/settlement constraints, investor paid21, company bills reflected, no whole-fund quarter incentive. At least two material opportunities per role are authored; human experience is validated later. Proposed scenario-runner calls and `python -m unittest discover -s tests/scenarios -p 'test_opening*.py'`.

**Failure and stop.** Missing quotes, authority overspend or same hidden market changed by holdings is blocking. Retune scenario versions, preserve prior failed-policy evidence. Stop at a fully executable and independently verified opening campaign; next FF5b.

## FF5b — First playable interface, real identities and reconnect

**Purpose and value.** Let two humans understand and act on the verified campaign through a reliable, accessible interface. Build the minimum view for consequential decisions.

**Entry / inputs.** FF5a opening artifacts, FF4a/b APIs and O05 authentication/session choice. Define one local/test identity setup and the protection needed for a distributable first playable; controlled FF3b actor selection is not acceptable authentication here.

**Ownership / outputs.** `frontend/` Next.js/TypeScript command desk, committee, investment/operations views and debrief; auth/session middleware, permitted observation/query/export endpoints; `tests/e2e/`; local two-user setup. Rich charts are secondary.

**Ordered tasks.**

1. Freeze frontend runtime/package-manager/necessary dependencies and API DTO generation/contract checks. Establish exactly two member season creation/join/invite policy and protected sessions; prevent actor IDs from being forged by clients.
2. Implement desk with next obligations, settled/restricted/fund/firm cash, resource budget and active incident reasons. Use clear calculation/alternative labels; deeper ledger is an inspectable drawer.
3. Add proposals/sleeves and independent routine commands, research/borrow/reserve choices and uncertainty previews. Edited proposals clear signatures; rejected requests retain user intent and show current state/version without silent resubmission.
4. Show permitted market/position/LP reports and causal debrief; all queries/exports enforce actor entitlement and availability cutoff. Browser bundles/downloads contain no hidden tape or private control workbook.
5. Implement polling/reconnect from authoritative sequence/checkpoint, version conflict recovery, duplicate-click safety, missing-partner pause and save/resume. Optimistic order UI says pending, never invents a fill.
6. Verify keyboard navigation, readable numeric labels, error/loading/offline states, reduced motion and small-screen review. Add only the automation needed to repeat the two-user critical path, not a general browser framework collection.

**Acceptance / verification.** C10–C11,I01–I04,I14,R03–R04/G12–G14; two real sessions finish ordinary opening21 with signatures/roles visible. Third/revoked/cross-season identity and stale-key retrieval denied; CSRF/session-expiry behavior matches selected auth design; raw narrative escaped and bounded. Proposed frontend type/build and selected browser-runner commands are pinned/documented only when that tool exists; backend query tests are independently reproducible.

**Failure and stop.** A local role dropdown is not a production session. Hidden tape exposure, wrong-actor consent or fabricated balances blocks completion even if UI is attractive. Stop at working first-playable candidate; FF5c decides release.

## FF5c — Certify the first playable release

**Purpose and value.** Make a truthful release claim from combined economic, safety and two-human evidence. Freeze the opening experience before expanding to six chapters.

**Entry / inputs.** FF5b playable candidate, FF5a independent policies, FF4a race evidence and FF3b observations. No optional AI, historical provider or staffing breadth prerequisite.

**Ownership / outputs.** `docs/evidence/FF5c/` financial/replay/race/information/accessibility/human study, reproducible first-playable manifest/demo guide and explicit release decision. Fixes belong only to exercised modules and receive regression evidence.

**Ordered tasks.**

1. Re-run the two success, wait and failure/recovery policies against frozen manifests; compare full dated balances/claims, not only returns. Record independent oracle provenance and old-versus-new evidence validity.
2. Restore a copied test database and replay to multiple subphase checkpoints; confirm exact economic hashes/next phase and no duplicated weekend fee or payment. Exercise reconnect and duplicate delivery.
3. Verify cross-season/revoked users, proposal edit/readiness, future mutation/exports and protected result retrieval; rerun only affected concurrency suites plus required end-to-end proof.
4. Run six consented anonymous pairs, three novice-finance and three finance-familiar, with counterbalanced roles and recorded facilitator intervention. Gather duration, both-player agency, approval-only wait, financial comprehension, failure recovery and desire to continue.
5. Decide RELEASE_CANDIDATE/REVISE from predeclared gates; publish negative results/limitations. If changes alter economics, issue new rule/tape version and refresh dependent oracles; cosmetic fixes do not reroll tape.

**Acceptance / verification.** Each partner at least two consequential choices; neither >25% decision-window time solely waiting for approval; both explain cash vs NAV, next deadline and one immediate/delayed consequence; failure pair can identify recovery/winddown without financial coaching. Record actual40–60minute target distribution and median interest rating target>=4/5, with dissent. All required financial/replay/security cases pass; human gate is pending until observed, not satisfied by scripts.

**Failure and stop.** Any material financial/permission/leakage failure or repeated agency/comprehension failure blocks release. Small pilot does not establish statistical proof of fun. Stop at evidence-backed first playable; next FF6a, not optional tooling.

## FF6a — Compile Cases2/3 and implement operations/restrictions

**Purpose and value.** Add capital-flow/valuation tensions without increasing instrument complexity. Finish the missing downstream contracts before the full campaign.

**Entry / inputs.** FF5c evidence, SCENARIO_CONTRACTS Cases2/3, corrected baskets and isolated arithmetic. Resolve O06 path-specific independent control computation and O07 liquidation tail. Do not revive the dominated Case3 hire choice.

**Ownership / outputs.** compiled Case2/3 and recovery tails, independent dated oracles/scripts/control records, `backend/domain/controls/`, `restrictions/`, report/restatement/offer predicates; `tests/scenarios/` and control/restriction integration cases.

**Ordered tasks.**

1. Materialize Case2 day39–61 references/borrow/volumes/claims/company/series histories and Case3 day29–41 plus conditional cure through45, including ordinary intervening weekend fees. Clearly distinguish seeded35k/100k invoices from new accruals.
2. Independently calculate full-pay versus gated-sale-and-later-payment scripts, every issuer/sector/ETF/margin ratio, fair unit conversion and actual floating carried request. Verify constrained credit before labeling a no-sale path payment default.
3. Build an independently derived control evaluator/records for arbitrary valid player paths using separate derivation, not importing posting/fee/risk functions under test. Define timing differences/tolerance/source hashes; fixed scripts also get hand-authored records.
4. Implement discrepancy triage and correct/reverse/restated evidence; known false NAV cannot certify. Free routine truth checks do not consume paid research or require an operations hire.
5. Enforce restricted-source instrument state/canceled resting orders/clearance event at each partial fill; public unrelated research remains available. Case3 capital-diligence/cap/decline and report deadline have declared deterministic consequences.
6. Integrate actual success/failure/recovery scripts and debriefs through their stated horizon; include independently authored winddown tail if invoked. Recheck observation leakage and restoration around corrections.

**Acceptance / verification.** A22,V28–V30,V12,V14,C12; gated claims pay61 with zero unresolved deferred units; corrected Case3 opening26.84m follows200k expense/40k provision reversal, preserves original report, pays distribution once. Admission zero company cash; report missed35 offer stays lost. Proposed `python -m unittest discover -s tests/scenarios -p 'test_case[23]*.py'` and control/restriction tests.

**Failure and stop.** Calling the production fee function an independent admin is a failed oracle. Uncertified closes/remaining carried units/hire-only success counting block completion. Stop at two additional verified cases, not full campaign proof; next FF6b.

## FF6b — Full campaign, useful staff capacity and complete endings

**Purpose and value.** Deliver the initial game as a connected investment business, carrying obligations/fee history across all six chapters and meaningful endings.

**Entry / inputs.** FF6a verified cases, FF5c role findings, company/LP standard mechanics. Resolve O08 staffing payoffs, O09 full campaign objectives and O07 termination tail. No derivatives/multicurrency/live sandbox.

**Ownership / outputs.** full1–61 authored campaign plus up to10-business-day winddown/cure tails, chapter/evidence manifests, standard prospects/staff assignments, continuation forecast, outcome/score/winddown reducers, independent full campaign oracles; `tests/scenarios/`, `tests/domain/game/`.

**Ordered tasks / subgates.**

1. FF6b.1 — Freeze chapters3–6 tensions, visible obligations/briefs, information quality, named action alternatives and role ownership. Each window has one investment and one operations choice; merge repeated recap/approval work.
2. FF6b.2 — Author complete future-independent market/borrow/volume/action/restriction tape, plus scenario-independent ending tails. No hidden punishment based on current holdings; NPC reactions depend only on published behavioral rules.
3. FF6b.3 — Add qualified/diligent/funded standard prospects with capacity/cap/decline; staff hiring/releasing uses recruiting cash, next-chapter capacity and weekly salary/severance. Each hire buys a named additional assignment that competes with another real task; it cannot improve price luck or buy true accounting.
4. FF6b.4 — Integrate chapters incrementally and extend independent success/defensive/failure ledgers at each dealing40/60. Preserve earlier histories; validate post-redemption leverage and thin-runway manager reality.
5. FF6b.5 — Implement published Renewal conditions at certified60 close/ordinary61 admin, Survival, Responsible Winddown, Broker Default and Company Failure. Preserve terminal unpaid claims; scenario challenges do not share a return leaderboard with campaign.
6. FF6b.6 — Implement joint controlled winddown/finite tail, actual executable liquidations, settled return, final certified fee/units/distributions and company closure. Horizon expiry with halt/claims means unresolved winddown, not invented proceeds or legal waterfall.
7. FF6b.7 — Generate certified financial attribution, LP statements, separate firm runway/13-week continuation forecast and evidence-linked debrief. Counterfactual replay alters only selected commands on the same tape; it is practice, not fresh blind scoring.

**Acceptance / verification.** Full six-chapter scripts through61 and every outcome label; G01–G08,G11,G14,V09,V18,V31–V32. Salary/release timing exact, performance provision never spent on payroll,4-week conditional Renewal never implies financed next quarter. Winddown raises no incentive cash merely from scored end. Two distinct solvent policies exist on frozen authored versions; gate/fee/concentration/wait exploits have recorded outcomes. Proposed scenario-runner manifest matrix and `python -m unittest discover -s tests/domain/game` plus full campaign tests.

**Failure and stop.** A chapter implemented with narrative-only money changes fails; a staffing payoff with no actual useful task is removed/deferred. Maintain compatibility or start a new campaign version after a rule change. Stop at full initial-game candidate; FF6c supplies release evidence.

## FF6c — Full release evaluation, recovery and reproducibility package

**Purpose and value.** Demonstrate financial correctness, role balance, exploit resistance and recovery with reproducible experiments. Measure rigor through evidence rather than architecture/library count.

**Entry / inputs.** FF6b complete candidate and all earlier evidence. Resolve O09 outcome/balance hypotheses and O10 supported workload/hardware before measuring. Existing tests remain valid only when their input/rule hashes match.

**Ownership / outputs.** `docs/evidence/FF6c/` experiment protocols/manifests/raw anonymous observations/results; reproducibility/evidence index, limitations and release disposition; bounded necessary fixes only.

**Ordered tasks.**

1. Freeze training/balance-tuning versions and at least one separately authored held-out version. Run cash/defensive, diversified, liquidity-aware, concentrated gambler, trust spam, repeated gate and terminal-holding policies with identical costs/availability. Keep all failure/undefined outcomes.
2. Report return/drawdown/LP capital returned/claims deferred or overdue/company cash/forced actions separately. Show deterministic mechanical paired replays; make no empirical investment-skill or real-world alpha inference.
3. Run novice/finance-familiar full-season paired sessions, rotating role assignment and save/resume across chapters. Predeclare observation windows and success/agency/recovery comprehension criteria; distinguish facilitated runs and actual duration.
4. Restore backup to a separate DB, replay to checkpoints before/after all dealing/forced/correction events, inject pre/postcommit crashes and reconnect/message loss. Verify no altered economic hash or duplicate identity.
5. Execute access/secret/input bounds/escaped narrative/as-of tests plus all required PostgreSQL financial races. Profile the declared hardware/operation mix/active seasons, record latency/error/lock waits and invariant failures; select supported load from results, not aspirations.
6. Publish RELEASE/REVISE with links from each claim to actual artifacts, current unsupported behaviors and sample/model limits. Future enhancements must cite a demonstrated need; do not inflate graduate claims using unused frameworks.

**Acceptance / verification.** No unresolved major financial/authority/leakage/recovery defect; all required cases pass; human role/comprehension criteria sustained across chapters; exploits unable to erase obligations/reroll outcomes. Measured throughput is evidence only for the tested load/environment. Record baseline failures without selective reporting. Proposed domain/integration/scenario/E2E matrix is captured with exact pinned commands at this milestone; unavailable tester/load infrastructure stays pending.

**Failure and stop.** Pilot observations cannot establish universal enjoyment; a held-out failure needs honest diagnosis/versioned repair and fresh evidence. Stop at supported full initial-game release and limitations. FF7/FF8 are elective, not a requirement to declare a correct completed initial game.

## FF7a — Optional licensed historical replay, end to end

**Purpose and value.** Determine whether one historical dataset can deliver reproducible as-of gameplay using the same economics. Importing data alone is not historical replay.

**Entry / inputs.** FF6c passed and a separate selected research task. Resolve O11 exact dataset/rights/coverage/cost and historical epoch-specific accounting/settlement/borrow assumptions. No paid activation implicit. If no dataset meets criteria, the valid result is DEFER/REJECT.

**Ownership / outputs.** rights/coverage decision, frozen snapshot manifest/import adapter, read-only historical scenario compiler, replay policy and one bounded playable historical case; `backend/adapters/data/`, `backend/domain/market/` adapter interface, `tests/data/`; independent historical economic oracles.

**Ordered tasks.**

1. Choose one case/instrument universe/date interval and unmet learning objective. Verify official provider terms and actual schema/example; separate software license from display/retention/export/derivation/replay rights and costs. Do not repeat the entire candidate-list research.
2. Require publication/availability/revision history, raw prices and explicit corporate actions, universe/delisting/symbol continuity and era calendar/settlement conventions. State authored financing/LP behavior; present-day borrow cannot masquerade as historical borrow.
3. Freeze immutable entitled inputs with versions/hashes and rights retention policy. Import outside locked gameplay; malformed/stale/partial/forbidden/timeouts remain distinct. No zeros or current revisions silently replace missing historical facts.
4. Select only one needed dataframe/calendar tool from existing research; DuckDB only for demonstrated query need. Compile explicit future-eligible events appropriate to data resolution; daily OHLC cannot promise intraday path/priority.
5. Run the same command/execution/ledger/series/firm engine on one historical case, prove as-of leakage mutations and shared-engine parity. Track source staleness/resolution uncertainty; label prices historical, fills/financing/investors simulated.
6. Evaluate educational utility and reproduce from retained licensed artifacts, or close the task with a reasoned rejection if required rights/coverage are unavailable.

**Acceptance / verification.** I01–I04,I07–I08,I14,V17–V18,E13–E14; immutable permitted replay, actual one-case shared-engine run, independent costs/flow/corporate-action oracle and explicit historical limitations. Proposed `python -m unittest discover -s tests/data` and historical scenario-runner commands. No real provider call is needed for early adapter failure tests.

**Failure and stop.** A hash cannot recreate a dataset forbidden to be retained; reject such replay claims. No as-of evidence means unsupported observation, not a guessed date. Stop at one supported historical pack or documented deferral, not live data/ML.

## FF7b — Optional advisory aid with a falsifiable usefulness test

**Purpose and value.** Add one read-only aid only if it improves a measured task beyond existing deterministic templates/stress cards. This is not an AI platform or requirement for fun.

**Entry / inputs.** FF6c, plus FF7a only if the selected aid needs historical data. Resolve O12 selecting exactly one aid, evaluation target/dataset/baseline and allowed spend. Default recommendation is deterministic explanations; no AI runtime until an actual unmet comprehension need is documented.

**Ownership / outputs.** one advisory adapter, sanitized observation interface, fixed evaluation packets/rubrics, experiment report and adopt/remove decision; `backend/adapters/advisory/`, `tests/advisory/`, evidence. No economic/governance mutation interface.

**Ordered tasks.**

1. Choose one bounded candidate: source-grounded tutor for cash/obligation explanation, constraint-based allocation suggestion, or measured diagnostic. Write target/end-user benefit and deterministic baseline before selecting a dependency/model. Do not implement all three.
2. Define frozen permitted packets and withheld future facts; tutor uses20 curated fact packets plus leakage/injection/malformed/outage adversarial packets. If statistical forecast chosen instead, freeze lag-safe train/validation/held-out chronological split and simple baseline.
3. Build a read-only typed proposal/explanation boundary; every allocation suggestion converts to whole-share commands and reruns original risk/authority. No tool can approve, execute, post balances, set trust or score.
4. Evaluate fact-source accuracy, forbidden-fact disclosure, numerical hallucination, human comprehension change versus templates, latency and actual cost under authorized capped usage. Optimizer/diagnostic evaluation includes feasibility/conversion/cost sensitivity and baseline error, not persuasive prose.
5. Require deterministic unavailable/timeout/invalid fallback, bounded retries and server-only secrets; store what players saw for audit without changing frozen economics. Publish rejected results and remove unused dependency if utility is absent.

**Acceptance / verification.** I08–I12,I14; zero mutation privilege, no hidden tape, facts/citations verifiable, errors/outages preserve core play. Utility threshold and cost cap are frozen before the test; there is no presently verified model advantage. Proposed `python -m unittest discover -s tests/advisory` and protocol-specific evaluation command once chosen. Live-model calls need their own authorized budget; fixture tests alone do not prove model utility.

**Failure and stop.** Missing paid approval/data/target yields DEFER with deterministic baseline retained. Strong writing alone is not adoption evidence. Stop after one aid decision; do not launch ML/provider workstreams automatically.

## FF8 — Future-extension decision gate, not an unbounded build promise

**Purpose and value.** Keep speculative hosting/live data/leagues/new instruments from corrupting initial-game scope. A full implementation plan for an unknown product request would invent requirements; this milestone fully specifies how a selected extension earns such a plan.

**Entry / inputs.** Full initial game evidence, explicit new requested extension and unmet-need statement. Resolve O13 selecting one extension/budget/permissions. Existing future ideas are not authorization for deployment, billing, external messages or real execution.

**Ownership / outputs.** `docs/extensions/<selected>/SPEC.md`, `PLAN.md`, `ACCEPTANCE.md`, updated dependency/risk/rights decision and explicit go/defer/reject. No implementation paths owned until an extension plan is selected and agreed.

**Ordered tasks.**

1. Specify one user story, actors, mode, constraints and desired change in observable behavior. Demonstrate why current campaign cannot deliver it; reject cosmetic complexity without a useful decision.
2. Choose the appropriate boundary: hosting needs identity/security/cost/recovery; live sandbox needs entitlements/timestamps/outage/no-real-execution; league needs attempt/fairness/seed/version policy and isolation; new instrument needs lifecycle/valuation/collateral/settlement/accounting cases.
3. Map unchanged versus new authoritative state/commands/events/invariants and exact schema/migration compatibility. Preserve synthetic deterministic campaigns; optional service failure cannot rewrite prior economics.
4. Verify only the specific primary docs/rights/license/API needed, against a small original implementation alternative. Document recurring cost/cap, infrastructure/credential requirements and affected permissions without activating them.
5. Produce disjoint small implementation milestones with independent oracles, reproducible experiment, failure/restore cases and stop gates; resolve blockers before assigning a builder. Seek actual authorization only for genuinely irreversible/external/billed action.

**Acceptance / verification.** Selected extension has measurable success/failure, complete lifecycle/permissions/rights/cost boundaries, dependency-aware owned steps and independent validation. Rejected/deferred decisions include exact missing evidence; no fictional implemented result. Document checks can validate packaging, not hosting/market/legal functionality.

**Failure and stop.** No selected extension means NOT_STARTED, not a reason to expand the stack. Stop at a concrete reviewed extension plan or deferral. Real-money trading remains excluded from FundForge's scope.

