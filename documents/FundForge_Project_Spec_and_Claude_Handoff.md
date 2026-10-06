# FundForge — complete design and implementation handoff

Version 2.1 · 6 October 2026 · Design package; application unimplemented.

Generated from canonical repository documents. Edit the sources and rerun scripts/build_documents.py.


---

Source: `README.md`

# FundForge

A cooperative hedge-fund management strategy game. Two partners build an investment business, manage outside investors' capital, and survive the consequences of their decisions.

**Status: design package v2.1, 6 October 2026. No application has been implemented.** This revision critically audits v2.0 using Astra with extra-high reasoning and primary-source research. Earlier versions remain in Git history.

## The game

Run a fictional $25 million long/short equity fund over 60 simulated business days, organized into six chapters. Choose research priorities, negotiate investment authority, allocate capital, manage financing, handle investor withdrawals, pay the firm's bills, and explain what happened. Sessions advance simulated time; players do not need to attend at real market hours.

The investment partner leads theses and portfolio construction. The operating/risk partner leads liquidity, financing, investor relationships and the business budget. Both can research and challenge decisions. Agreed strategy sleeves let routine actions proceed inside a jointly approved envelope; material exceptions require committee agreement. Every partner has consequential work beyond approving the other's tickets.

The objective is durable, mandate-consistent investor outcomes and a viable firm. A lucky leveraged bet does not erase unpaid obligations, broken promises, or insolvency. A disciplined winddown is a distinct outcome. All money, entities, contracts and obligations in the campaign are fictional.

## Read in this order

1. [Realism audit](https://github.com/krishbansalofficial/fundforge/blob/main/docs/REALISM_AUDIT.md), then [master specification](https://github.com/krishbansalofficial/fundforge/blob/main/docs/MASTER_SPEC.md): critical findings, priorities and product boundaries.
2. [Game systems](https://github.com/krishbansalofficial/fundforge/blob/main/docs/GAME_SYSTEMS.md): actions, roles, capital, progression and scoring.
3. [Season scenarios](https://github.com/krishbansalofficial/fundforge/blob/main/docs/SEASON_SCENARIOS.md): actual decisions and crisis arcs.
4. [Fund accounting](https://github.com/krishbansalofficial/fundforge/blob/main/docs/FUND_ACCOUNTING.md): authoritative financial contracts.
5. [Implementation plan](https://github.com/krishbansalofficial/fundforge/blob/main/docs/IMPLEMENTATION_PLAN.md) and [acceptance cases](https://github.com/krishbansalofficial/fundforge/blob/main/docs/ACCEPTANCE_TESTS.md).
6. [Simulation architecture](https://github.com/krishbansalofficial/fundforge/blob/main/docs/SIMULATION_ARCHITECTURE.md): ownership, interfaces, replay, precision, concurrency and information safety.
7. [Library research](https://github.com/krishbansalofficial/fundforge/blob/main/docs/LIBRARY_RESEARCH.md) and [OpenSEO assessment](https://github.com/krishbansalofficial/fundforge/blob/main/docs/OPENSEO_INTEGRATION.md): 17 pinned repository reviews, reuse decisions and data-rights boundaries.

For coding, start with [Claude handoff](https://github.com/krishbansalofficial/fundforge/blob/main/docs/CLAUDE_HANDOFF.md), [progress](https://github.com/krishbansalofficial/fundforge/blob/main/docs/PROGRESS.md), then P01 in [prompt pack](https://github.com/krishbansalofficial/fundforge/blob/main/docs/PROMPT_PACK.md). The [combined Word document](https://github.com/krishbansalofficial/fundforge/blob/main/documents/FundForge_Project_Spec_and_Claude_Handoff.docx) is generated from the current Markdown documents.

## First playable release

A crisis-rich two-chapter opening arc (20 simulated business days, through ordinary day21 opening administration) with two users, a reconciled long/short portfolio, borrow and margin, an investor redemption, fee accounting, separate firm runway, a committee decision, and a causal debrief. A buy/approve/chart demo is only an engineering foundation. The complete initial campaign expands that slice into all six chapters through ordinary day61 opening administration, with reproducible seeds, save/resume, failure endings and balancing evidence. These checkpoints include intervening weekend accruals, not a fresh Monday market valuation.

## Engineering direction

Next.js/TypeScript, FastAPI/Python, PostgreSQL; pure deterministic financial domain; fixed precision; immutable events and journal; as-of information access; versioned rules and fixtures. Begin with synthetic data and polling. Add workers, live providers, ML and optional read-only AI after the core game is sound. No external API is required to play the base campaign.

No trading framework is required for the initial game. Later research can use pandas, exchange_calendars and optional DuckDB; CVXPY/statsmodels need a specific evaluated advisory feature. OpenSEO is a separate optional alternative-data source. No upstream code was copied, paid service activated, or deployment created in this revision.

The private repository is already set up. Do not rerun the legacy repository-creation scripts here. Nothing in this package represents a live fund, brokerage service, legal compliance certification, measured model result or completed software feature.


---

Source: `docs/REALISM_AUDIT.md`

# FundForge v2.1 — fund realism and decision-quality audit

6 October 2026 · Design review of v2.0, with v2.1 document changes · All application behavior remains proposed/unimplemented.

The product should teach two partners to preserve the ability to invest: portfolio conviction, investor obligations, financing and the management company's survival interact. v2.0 already had the right scope: outside LP capital, a separate company, long/short finance, delegated authority, fixed information cutoffs and deterministic records. Replacing that foundation with a larger trading terminal or many libraries would weaken the product. The highest-value changes are economic consistency, a few independent controls and scenarios whose choices actually alter claims, cash and risk.

This review applies six professional lenses—portfolio manager, chief risk officer, chief operating officer, fund accountant, quant researcher and cooperative-game designer. These are review perspectives, not claims of professional appointment or regulatory certification. Primary sources were checked on 6 October 2026; exact URLs and limits are below. Calculations and game prescriptions are our analysis, not rules imposed by those sources.

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

Version 2.1 · Realism and implementation review · 6 October 2026 · Specification, not implemented software

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

OpenSEO is a potentially useful external SEO/website-intelligence component, not a finance engine or a mandatory market-data source. Follow the separately verified integration document; do not replace it with OpenBB or imply that an untested integration already exists.

## 11. Engineering, research and evidence

Keep the modular FastAPI/PostgreSQL + Next.js architecture. Domain modules cover identity; seasons/clock; governance/sleeves; market/research; execution/borrow; treasury/margin; fund ledger/LP series; management company; scenario/LP transitions; reporting/replay. Redis, workers and WebSockets arrive only when their reliability problem is being implemented.

Auth, tenant isolation, immutable approvals, state-version conflicts, idempotency, fund locking and as-of authorization apply to every UI/API/job/export. Firm transactions use a separate ledger but shared season serialization when transferring fees. Untrusted market text is data. No LLM can approve, trade, post money, change risk or decide hidden outcomes.

A market adapter must establish coverage, rights, timestamps, feed, adjustments, corporate actions and reproducibility before historical/live use. Historical gameplay cannot silently inherit current settlement schedules or future data. Backtests reuse the execution, financing, fund and fee engine. Compare like mandates and cash/financing assumptions.

One later ML candidate is filtered HMM regime inference compared with a simple trend/volatility baseline. Fit only on chronological training data; use forward-filtered probabilities; evaluate on untouched held-out periods with trading-cost sensitivity. Rejecting a model is an acceptable result. Synthetic game success is not investment-edge evidence.

Tutorials attach to decisions: borrow recall, leverage, liquidity, unit issuance, fee recovery and conflicting stakeholder incentives. Template explanations work without AI. Optional LLM narration consumes verified event facts and cannot invent metrics or determine grades.

Follow IMPLEMENTATION_PLAN and ACCEPTANCE_TESTS for the actual build sequence. The current repository remains documentation-only. No authored fixture, architectural diagram or validation of document arithmetic constitutes a working application, tested database, paid-provider entitlement, deployed model or measured load result. The three numerical cases in SEASON_SCENARIOS are authored playable specifications with explicit paths, not implemented or balance-tested episodes.

## 12. Source discipline

The simulator borrows concepts, then deliberately defines its own contracts. SEC Investor.gov hedge-fund guidance describes fees and redemption limits as terms investors must understand; it does not prescribe this game's 1.5/20 structure or dealing windows. SEC T+1 guidance concerns applicable U.S. transactions, not every market or historical era. Regulation SHO's locate/close-out framework is not reproduced by adding a “borrow available” icon. Brokerage sources describe that broker's practices, not universal contractual deadlines.

Primary reference links and verification notes belong in SOURCES. Any future educational legal claim must be verified in its jurisdiction and date. This game is not an actual fund and does not claim SEC approval or comprehensive broker compliance.

## 13. v2.1 realism boundaries and build decisions

[REALISM_AUDIT.md](https://github.com/krishbansalofficial/fundforge/blob/main/docs/REALISM_AUDIT.md) records the source-backed review across portfolio management, risk, operations, accounting, research and game design. Real concepts, specific counterparty terms and deliberate game rules are labeled separately. The first release remains one fund, one broker, one currency and twelve instruments; it does not need derivatives, a complete compliance department or a large optimizer to feel like a fund.

Required small additions fix material errors: calendar accrual, annual/redemption fee timing, fair fee-series participation, post-redemption risk, signed hedge direction, one independent reconciliation exception, simple dividends/splits and a deterministic restricted-instrument state. The Managing Partner resolves funding/reporting/capital decisions; the Investment Partner resolves sizing, hedging and liquidation choices. Neither partner acts as a fictional independent administrator. Admin/broker NPCs are authored control records with separate responsibilities.

Chapter windows are compressed for play: five-business-day redemption notice, one-day payment and publicly specified broker response windows are fictional contracts. Real investors and prime brokers can have very different rights. Daily company payroll allocation and strategic-assignment budgets are house rules. The exact latent relationship score is a balance device, shown primarily as observable concerns and a relationship band.

The ending is an ordinary checkpoint after day61 opening administration, including weekend accruals and due day60 settlements. Residual investments are marked holdings with aged quotes, not liquidated cash. There is no special frozen-price terminal day. Winddown continues actual engine events. The scored 60-business-day investment result and the subsequent cash/claims bridge remain separate.

Use the updated accounting and scenario cases before implementation. Optional research libraries and architecture choices are owned by their dedicated assessment documents; no dependency should replace the authoritative economic event/ledger contract.

Renewal is displayed as **Renewal — conditional continuation**, with remaining company cash runway, a13-week forecast and any unfunded next-season gap. It is not a claim of durable business viability or a guarantee that another12-week campaign is financed. Preserve cash, liabilities and fee history into continuation; no automatic company recapitalization.

Canonical software boundary: [SIMULATION_ARCHITECTURE](https://github.com/krishbansalofficial/fundforge/blob/main/docs/SIMULATION_ARCHITECTURE.md). Dependency evidence: [LIBRARY_RESEARCH](https://github.com/krishbansalofficial/fundforge/blob/main/docs/LIBRARY_RESEARCH.md). Detailed player decision contracts are in GAME_SYSTEMS section11; the acceptance/implementation documents define pending evidence gates.


---

Source: `docs/GAME_SYSTEMS.md`

# Game systems and balance contract

Version 2.1 · Proposed, unimplemented defaults · Read with MASTER_SPEC and FUND_ACCOUNTING.

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


---

Source: `docs/SEASON_SCENARIOS.md`

# Season scenarios and playable arc

Version 2.1 · Authored design, not a complete playable tape or measured balance result.

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

**Information available at day12 opening.** BRIN's financing weakens but its near-term customer survey remains positive. Harbor Prime announces stressed coefficients effective day16: initial80% long/100% short, maintenance70%/90%. The players know the rule change and must forecast it; they do not know the day16 prices. Tactical's already-disclosed10,000-unit redemption will price day20 and pay day21. LP withdrawal dollars are not yet fixed. Research reveals either a dated public debt maturity schedule or a noisy customer survey; neither predicts the squeeze with certainty. One contingency assignment reveals a replacement borrow offer at40% annual, available for the recalled quantity only until day15 close.

| Time | Observable event and decision | Frozen author outcome / mechanical consequence |
|---|---|---|
| Day12 window | PM proposes earlier long reduction or holds conviction; operating partner reserves payment liquidity and investigates borrow | Partners can jointly authorize a reduction package beyond delegated ticket/turnover limits; hard limits still apply |
| Day13 opening | Broker recalls1,250 BRIN shares, cover-execution deadline day15 final executable event; settled replacement can cancel that recall | Replacement costs40% ACT/360 on replaced shares, not on unrelated borrows; locate alone cannot satisfy recall |
| Day15 final event | Replacement or cover must be committed to an eligible future event before the deadline | Otherwise contractual buy-in follows the published priority; event tape has sufficient capacity for1,250 shares at this deadline |
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

**Situation and goal.** Day39, the fund has performed adequately but two LPs each require a $3m dollar-target redemption at day40. This standalone challenge expressly adds Tactical's external dollar target; the base campaign's10,000-unit day20 request remains a different contract. Both requests were disclosed day30 and properly noticed day35. Neither disappears with a good meeting. The partners must meet day41 payments, keep the post-flow book within its mandate, and explain any permitted gate fairly. The goal allows a gate with a funded next-window plan; full-season Renewal still disallows a terminal deferred request.

**Decision-comparison balance**, normalized after ordinary day40 charges common to both branches: NAV $25m; longs $25.5m, shorts $5m, restricted cash $5m, unrestricted cash $2.1m, debt $2.5m, fixed fees/financing payable $100,000 due day41. Check:2.1+5+25.5−5−2.5−0.1=25m. Performance is below the relevant series HWMs in this case, so no provisional incentive liability. BEAM is $8m of longs at100; the remaining17.5m long/specified short basket follows Case1's issuer/sector distribution. Ordinary initial/maintenance coefficients apply; credit remains capped at7.5m.

**What players know.** A thin equity's catalyst is due day43, after redemption payment. BEAM has an executable day40 event but sale price remains uncertain until then. The prime broker confirms only eligible same-date cash netting; short collateral is unavailable for withdrawals. A new LP offers$5m, but diligence completes after day40 and funding earliest day60. The offer cannot cure this window. PM can request an extra liquidity estimate; the Managing Partner can negotiate a next-window plan, neither of which changes the binding current request.

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

**Choices with consequences.** The PM can insist on a clean public research path, choose smaller unrelated exposures, or spend an assignment on explaining the real source of the apparently strong return. The Managing Partner can keep staffing lean, hire knowing a temporary cash shortfall is forecast, or decline/cap capital to match liquidity. Both must approve a hire and investor admission. No action unlocks spending the fund's5m subscription on payroll or banking the460,000 surviving performance provision. At constant new capital,5m creates only205.479… of management-fee accrual per calendar date; its first28 dates would yield at most5,753.42 before fee-base erosion, paid at a later window. That does not rescue day40 payroll.

**Success branches.** Correct the report promptly, retain lean staffing and admit/cap the compatible LP; or correct promptly and hire with the disclosed35,000 day41 receivable sufficient to cure the6,000 shortfall, accepting much shorter runway. A solvent decline-capital path also succeeds if it meets the report and cash objectives. Case outcome reports47,000/20,000=2.35 weeks versus29,000/24,000=1.2083 weeks of company cash runway, not the full-season four-week Renewal result.

**Failure and recovery.** Ignoring the break leaves official reporting/dealing uncertified and loses the conditional offer. Trying to certify a known wrong report or bypass the restriction is blocked and logged, not rewarded as a clever strategy. If the fund cannot pay its35,000 fee at day41, the hire branch's6,000 unpaid payroll remains; a prospective subscription does not itself pay the company. Apply the ordinary five-business-day cure deadline and then controlled winddown if no earned/collectible fee or permitted cost reduction can cure it. Correcting an error later can restore reporting but does not fabricate the missed offer or erase arrears.

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


---

Source: `docs/LIBRARY_RESEARCH.md`

# Library research and dependency decisions — v2.1

Reviewed 6 October 2026 against actual repository files and official APIs. This is a source review, **not an installation, compatibility test, security audit or benchmark**. Exact commits, source blobs and license blobs appear in [library_review.json](https://github.com/krishbansalofficial/fundforge/blob/main/fixtures/library_review.json). Default-branch timestamps are narrow maintenance signals, not release pins or support guarantees. At implementation, select supported releases, lock transitive dependencies and review their licenses.

## Recommended small stack

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

Source: `docs/OPENSEO_INTEGRATION.md`

# OpenSEO: repository assessment and bounded integration

Design version 2.1, 6 October 2026. Assumed target: [every-app/open-seo](https://github.com/every-app/open-seo), the upstream of the similarly named afazhriel/openseo fork. The user supplied a name rather than a URL; confirm a different target if intended. This assessment does not silently substitute OpenBB. No upstream source has been copied, installed, deployed, or connected to a paid account.

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

## v2.1 cross-review

The same upstream snapshot and domain-overview module were rechecked on 6 October 2026; no new integration was implemented. See [LIBRARY_RESEARCH](https://github.com/krishbansalofficial/fundforge/blob/main/docs/LIBRARY_RESEARCH.md) and [library_review.json](https://github.com/krishbansalofficial/fundforge/blob/main/fixtures/library_review.json) for the 17-candidate comparison, exact repository/commit/license evidence and recommendation. OpenBB's provider framework is a separate candidate and is not OpenSEO.

Alternative-data relevance depends on the issuer's business, domain mapping and a falsifiable question; an industrial company with little direct consumer search exposure may gain no useful evidence from these tools. A real provider cannot be attached just to make the research room look sophisticated. Fixture evidence and its uncertainty already support the game's decision. Marketing-site SEO remains a separate deferred use.

At FF7, choose separate OpenSEO service versus direct provider adapter using one fixture task, operational burden, measured useful decisions and entitlements. Persist observation revisions and charge-resolution states independently of the economic journal. Server outages may block a new research purchase but never change a frozen campaign, execute an order or silently spend real currency. No current-data refresh can repair a missing historical vintage.


---

Source: `docs/SIMULATION_ARCHITECTURE.md`

# Simulation architecture — v2.1

Proposed interfaces and ownership, not implemented services. The architecture is a **modular monolith with one economic authority**, not a network of trading platforms. [FUND_ACCOUNTING](https://github.com/krishbansalofficial/fundforge/blob/main/docs/FUND_ACCOUNTING.md) owns exact financial/event conventions; [GAME_SYSTEMS](https://github.com/krishbansalofficial/fundforge/blob/main/docs/GAME_SYSTEMS.md) owns player permissions and gameplay; this document owns software boundaries. Resolve conflicts explicitly before FF0 freezes schemas.

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

Provider imports happen outside a locked campaign. Validate schema, units, timestamps, entitlements and bounds, then approve an immutable dataset. Real secrets stay server-side. Define failure classes (unavailable, forbidden, stale, malformed, partial, rate-limited, budget-exhausted, ambiguous charge). No silent zero filling, hidden current-data replacement or automatic retry of an uncertain charge. A provider failure cannot change existing campaign economics; an entitled live sandbox can pause affected research/quotes with visible quality state. OpenSEO's separate contract covers charge reservation and capped requests.

## Scenario interface and bounded AI

A scenario manifest declares prerequisites, starting certified balance sheet, public briefings, hidden but fixed event schedule, branch predicates, action space, deadlines, authored control records, expected invariant checks and recovery/winddown triggers. Branches may respond to disclosed behavior (late report loses trust); they cannot secretly make the market punish whichever stock was bought. Each consequence references cause IDs. Counterfactual debriefs rerun a fork with stated changed decisions and limits, never invent a reassuring alternative outcome.

Deterministic rules own prices, fills, margin, restrictions, fees, LP rights, cash movements, authority, deadlines and scores. NPC trust is a bounded transition table driven by events; prose is explanatory. Machine learning is optional for a defined forecast/diagnostic with chronological splits, lag-safe preprocessing, baselines, calibration and held-out evaluation. A complex model losing to a baseline is rejected.

An optional LLM tutor receives only sanitized permitted facts and may explain them with citations. An optional committee critic can point to risk metrics or missing thesis evidence, never approve an exception. Store outputs when they affect what a player saw. Failures fall back to deterministic text, not made-up figures. Hidden tape, keys, mutation tools and external browsing are absent from historical opponent contexts; memorized historical knowledge remains an explicit fairness limitation. No AI feature is needed to finish FF5/FF6.

## Implementation and evidence gates

Freeze schema and one hand-authored event trace at FF0. At FF1–FF4, prove ledger/series, execution/treasury, authority races and LP/firm contracts before building rich views. FF5 must connect these through the complete first two chapters. FF6 proves campaign endings, recovery, versioned balance experiments and actual two-person play. FF7 earns each optional library/provider/model independently.

Required evidence includes independent Decimal oracles, same-input replay hashes, future-data mutation tests, shuffled retry/race tests, fault injection before/after transaction commit, independent reconciliation breaks and successful checkpoint resume. Scenario manifests and prose do not satisfy these engine tests. The current repository still contains no implemented simulation runtime.


---

Source: `docs/IMPLEMENTATION_PLAN.md`

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


---

Source: `docs/ACCEPTANCE_TESTS.md`

# Acceptance contracts v2.1

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

# Claude handoff — FundForge v2.1

## Actual state

Private repository: https://github.com/krishbansalofficial/fundforge. Documentation-only, no frontend/backend/database/model/provider connection/deployment. The owner asked to rethink the whole product as a full hedge-fund game and evaluate OpenSEO, using Astra. The v2.1 critical review used Astra with extra-high reasoning, researched 17 pinned repositories and corrected the contracts; implementation remains pending.

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
- MASTER_SPEC owns product scope and the canonical document map; SIMULATION_ARCHITECTURE owns software interfaces.
- REALISM_AUDIT lists prioritized gaps and industry-versus-contract-versus-game distinctions.
- LIBRARY_RESEARCH and fixtures/library_review.json record17 actual source/license reviews. No dependency was installed.
- ACCEPTANCE_TESTS lists required observable behavior, not executed tests.
- OPENSEO_INTEGRATION pins inspected upstream code and separates optional research from the engine.

Preserve both simulated time and wall-clock audit time. External research must never reveal a future historical fact. Treat all numerical campaign settings as explicit fictional house rules. Never represent simulated LP terms as universally applicable law or real fund compliance.

## Delivery boundaries

FF0–FF4 build foundations. FF5 is a complete two-chapter opening arc through ordinary day21 opening administration. FF6 is the full campaign through ordinary day61 opening administration and reliability/balance gate. FF7 adds optional data/research/ML. All pending. Fixture mode requires no credentials. An OpenSEO assessment is not an installed integration; real API spend remains disabled.

At task end record changed behavior, actual checks and limitations, then update PROGRESS with one next task. Use a bounded financial/security reviewer when authorized. Do not launch extra agents or redesign the whole product after every milestone.

## Critical v2.1 contracts

Opening series participation is net capital plus reversible incentive provision. Management fee1.5% ACT/365 and settled borrow/debit ACT/360 accrue on calendar dates, including weekends; statistical252 annualization is a different calculation. Performance crystallizes annually on Dec31 and pro rata on dealt redemptions. A partial redemption does not ratchet surviving HWM. The Jan–Mar campaign does not pay an annual incentive merely because it ends.

Check all constraints on reductions: a short cover can increase net exposure, and a dealt redemption shrinks equity before payment. Borrow persists until settled return. Independently authored broker/admin controls can reveal a balanced but wrong journal. Corporate actions cover cash distributions and integer splits only. The synthetic calendar deliberately ignores real exchange holidays.

The minimal first-playable stack is the planned app/database plus our own deterministic domain. pandas/exchange_calendars, optional DuckDB, then optional CVXPY/statsmodels belong to justified FF7 tasks. OpenBB/OpenSEO are possible data adapters; LEAN/Nautilus are references; rateslib default rights and vectorbt Commons Clause prevent treating them as unrestricted dependencies. Recheck exact versions before reuse.

A Renewal ending is conditional continuation, not proof of a sustainable firm. At constant25m,1.5% annual management fees are375k against1.04m annualized20k/week overhead:665k structural gap before incentive income/capital/cost changes. The300k opening company balance is15 weeks at base cost; four weeks of remaining runway does not finance another12-week season. Display this gap and require an explicit continuation budget/recapitalization contract; do not award sustainability from AUM or provisional incentive alone.


---

Source: `docs/PROMPT_PACK.md`

# Copy-ready implementation prompts — v2.1

Use one prompt for one bounded task. The repository already exists. All application gates are pending. Model selection is performed in the actual client, not by claiming a prompt can switch its underlying model. The owner requested Astra/extra-high for this completed v2.1 critical review; verify available model names in the implementation environment.

## P01 — Inspect the redesigned game and freeze FF0

Read CLAUDE.md, docs/CLAUDE_HANDOFF.md, docs/PROGRESS.md, docs/DECISIONS.md and docs/MASTER_SPEC.md. Inspect repository and tools. Read REALISM_AUDIT, SIMULATION_ARCHITECTURE, GAME_SYSTEMS, FUND_ACCOUNTING and the first SEASON_SCENARIOS slice. Consult LIBRARY_RESEARCH before choosing dependencies. Check the dated calendar, per-date accrual, pre-provision participation, annual versus partial-redemption crystallization, post-flow risk and independent reconciliation. Identify concrete unresolved contradictions, not a new feature wishlist. Resolve routine choices; list any unresolved contract that blocks safe code. Produce a bounded FF0 task contract with schemas, owned paths and observable checks. Do not revert to the old paper-trading MVP. Do not generate the whole app or claim implementation results.

## P02 — FF0 scaffold

Implement the approved FF0 contract only. Pin actual supported runtimes and package managers, create minimal Next.js/FastAPI/PostgreSQL development scaffolding, config validation and CI. Define versioned command/event/scenario interfaces. Validate the authored scenario manifest, explicitly identifying any missing tape. No broad dashboard, provider connection or paid service. Run actual relevant checks and update PROGRESS with one next task.

## P03 — One financial contract

Implement exactly the selected FF1/FUND_ACCOUNTING contract and related acceptance cases. Use fixed precision and an immutable balanced journal. Provide independent expected arithmetic, not expected values obtained from the implementation. Separate fund, firm and investor series. Implement opening participation net plus reversible provision; preserve surviving HWM on partial redemption. Use ACT/365 management and ACT/360 settled borrow/debit calendar accrual with residuals. Test replay/reversal and meaningful boundaries. Treat legacy golden_scenario as a primitive fixture only. Report actual commands/results and pending cases.

## P04 — Execution, borrow and margin

Implement the selected FF2 transition with deterministic future-event eligibility, borrow/collateral/debt identities, settlement and deadline rules. Show a gap/recall/halt case and exact accounting. Check the entire constraint vector: covering can raise net exposure, redeeming can shrink margin equity, and pending returns keep borrow costs/collateral until settlement. A forced action can fail; preserve the deficit. No daily-bar invented intraday path, no LLM-owned prices, no unrestricted broker execution. Freeze the contract before adding presentation.

## P05 — Governance and transaction races

Implement FF3 for two human partners with jointly approved immutable sleeve charters and independent consent for exceptions. Test revoked/expired authority, combined commitments, idempotency collisions, edit/approve and cancel/fill races using real PostgreSQL. Atomically persist financial effects and durable publication state. No SQLite substitution or self-approved expansion of delegated scope.

## P06 — LPs and management-company survival

Implement the selected FF4 contract for investor notices/dealing, series fees/HWM, firm budget or trust. Preserve notice versus recognized payable versus cash payment. Distinguish fund NAV, restricted cash, company cash and fee receivable. Provide arithmetic and an event-order trace. Do not replace mechanics with cosmetic meters or free-text AI scoring.

## P07 — First complete playable opening arc

Deliver FF5 against verified engine APIs. Read the vertical slice in SEASON_SCENARIOS. Include research effort, thesis/hedging, partner negotiation, investor/financing/business choices, consequences and causal debrief. The operating partner needs independent agency. No fake model/provider results. Run a two-user flow through day20 dealing and ordinary day21 opening administration, including weekend accrual, disagreement, pause/resume and one crisis resolution; record confusion and actual duration.

## P08 — Bounded adversarial review

Review only this diff, its contracts and necessary dependencies. Return at most five reproducible defects with severity, violated invariant, exact path and expected/observed behavior. Prioritize fee/flow errors, collateral double count, authority races, future leakage and score exploits. Distinguish a definite defect from an open design question. Do not rewrite the architecture or start other agents.

## P09 — Campaign and balancing gate

Complete the selected FF6 chapter or balance task. Run matched seeded baseline policies and inspect concentration, cash-only, trust farming, replay rerolls and last-day obligation exploits. Keep rules immutable within a season. Report results with seeds and limitations. Do not claim a fun or balanced game solely because unit tests pass; include playtest evidence.

## P10 — OpenSEO spike

Read OPENSEO_INTEGRATION, LIBRARY_RESEARCH and the pinned inspected source paths. Verify every-app/open-seo remains the intended upstream; do not substitute OpenBB. Start with fixture observation → normalized as-of evidence card. Evaluate separate OpenSEO service versus small direct adapter without migrating the financial stack. Record exact data rights, credentials and real request/currency caps before any paid activation. Cover stale/missing/partial results, ambiguous-charge timeout and historical leakage. No live connection is required to complete the fixture spike. No copied code without license/notice records.

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

The critical financial audit's primary-source register and claim boundaries are in [REALISM_AUDIT](https://github.com/krishbansalofficial/fundforge/blob/main/docs/REALISM_AUDIT.md), references S1–S11. It adds SEC investor/ethics material, explicitly scoped ESMA performance-fee guidance, AIMA institutional operating preferences, the FSB's IOSCO valuation entry, IBKR settled-borrow examples, GIPS return methodology and FINRA house-margin guidance. Historic publication dates are retained; accessing an older source in 2026 does not turn it into a new rule. Inaccessible IOSCO text is not claimed as inspected.

The software review is in [LIBRARY_RESEARCH](https://github.com/krishbansalofficial/fundforge/blob/main/docs/LIBRARY_RESEARCH.md), with17 exact repository/commit/source/license records in [library_review.json](https://github.com/krishbansalofficial/fundforge/blob/main/fixtures/library_review.json). It distinguishes current resolved repository owners from old aliases, development snapshots from release pins, and restricted licensing from permissive licensing. No candidate was installed or benchmarked and no upstream implementation was copied. The ledger/concurrency choices also cite Python Decimal and PostgreSQL official documentation in [SIMULATION_ARCHITECTURE](https://github.com/krishbansalofficial/fundforge/blob/main/docs/SIMULATION_ARCHITECTURE.md).

Source categories are intentionally separate: industry concepts, a particular provider's practice, a fund's negotiated contract, and our game simplifications. The synthetic calendar, fees, LP windows, leverage, costs and outcome thresholds are authored settings. Historical/live mode needs its own venue/jurisdiction/era/entitlement review; the initial fictional US-style cash-equity mechanics do not establish real regulatory compliance.


---

Source: `docs/PROGRESS.md`

# Current project state

Updated 6 October 2026. Design v2.1. Application implementation remains not started.

- Private remote: https://github.com/krishbansalofficial/fundforge. Existing Git history is preserved; this revision starts from `5ae8a5a4f04e339eeb6697ff8a264989fada7106`.
- The owner requested a critical realism audit and repository update using Astra with extra-high reasoning. Astra/extra-high reviewed the financial/game contracts; current primary sources and actual source/license snapshots were inspected.
- Added REALISM_AUDIT, LIBRARY_RESEARCH and SIMULATION_ARCHITECTURE. The audit prioritizes 22 realism gaps; the library review covers 17 repositories and records exact commit/blob evidence. The architecture assigns one deterministic economic authority.
- Revised master, game, accounting and season documents. Corrected cohort participation, calendar accrual, annual versus redemption incentive timing, survivor HWM, borrow settlement/return, signed reductions, post-flow leverage, independent controls, corporate actions and checkpoint semantics. Exposed the management company's structural annual cost gap.
- Added three detailed authored challenge designs with two-player decisions, numerical branches, failure/recovery and explicit compilation gates. Updated season_scenario and added scenario_cases with 9 independent arithmetic oracles. A complete executable tape/engine is still pending.
- Synchronized acceptance cases, dependency-aware roadmap, decisions, Claude rules/handoff/prompts, workflow, source register, evidence guidance and OpenSEO review. Regenerated combined Markdown and Word documents from 19 canonical sections.
- Ran `python scripts/build_documents.py` and `python scripts/validate_design.py`: document/package and reference-arithmetic checks passed. The validator checks source links/fences, JSON, dated calendar, series/fees, risk, episode checkpoint calculations,17 pinned repository records and Word archive/source inclusion. See PACKAGING_VALIDATION for scope and limitations.
- No third-party implementation was copied, library candidate installed, paid account activated, visibility changed, public deployment created or real-money trading capability added. OpenSEO remains an optional fixture/adapter proposal; its intended upstream is a documented assumption.
- FF0–FF8 remain pending. No frontend/backend/database, runnable scenario engine, deployed model, actual user/load/security/provider result or measured investment outcome exists.

## Next task

Run P01: inspect the implementation environment and freeze FF0 against MASTER_SPEC, SIMULATION_ARCHITECTURE, GAME_SYSTEMS, FUND_ACCOUNTING and SEASON_SCENARIOS. Use REALISM_AUDIT's P0 findings and the independent oracle fixtures. Resolve remaining API/schema and full-tape/control-record details before declaring a runnable scenario. Build FF0–FF4 foundations, then the complete FF5 opening arc through ordinary day21 opening administration. Do not substitute a trading-only demo or a broad dependency installation for that goal.

## Update discipline

Record actual commit, changed behavior, commands/results, limits and one next task. Determine this revision's final commit from Git history; the starting commit above is not a claim about current HEAD. Keep proposed, implemented, tested and measured states distinct. A four-week Renewal milestone does not fund the next quarter; continuing seasons need a disclosed budget/capital contract or honest failure.


---

Source: `docs/PACKAGING_VALIDATION.md`

# Design-package validation — v2.1

These checks concern documents, reference arithmetic and generated review files. They are not application acceptance tests or evidence of playable software.

Executed successfully:

```bash
python scripts/build_documents.py
python scripts/validate_design.py
```

The bundle contains 19 canonical source sections; 22 source Markdown files are checked. The validator reports the current check/table/paragraph counts directly. Both commands passed for this revision; subsequent canonical edits require regeneration and validation before commit.

Checks include Markdown fences and local links; JSON syntax and version/capital/calendar contracts; six legacy zero-cost cash-account NAV states; 9 separate arithmetic oracles covering fee participation, partial redemption/HWM, post-redemption leverage, cover direction, calendar accrual, short distributions, borrow dates and the terminal boundary; numerical checkpoint calculations across 3 authored cases;17 exact repository/license/source snapshot records; Word archive/XML integrity and source-section inclusion; and exact source-content inclusion in the generated Markdown bundle.

The arithmetic validator independently recomputes expected checkpoint values from fixture inputs. It does not run an application or treat expected-output JSON as gameplay evidence. Episode branches isolate their stated decisive calculations; ordinary date-by-date accrual and complete market tapes must still be compiled and tested by the future engine.

Manual consistency review covers fund/company separation, pre-provision series participation, survivor HWM, annual performance crystallization, weekend accrual, settled borrow/return, whole-vector risk checks, post-flow leverage, independent reconciliation, real data rights versus source licenses, and proposed versus implemented status. Source audit, library review and architecture are now included in the combined Word document. Table headers repeat across pages.

Existing repository-creation scripts were preserved and not executed. The remote was inspected through the GitHub connection. Publication uses an atomic commit and guarded non-force ref update against the expected existing HEAD; no visibility or hosting change is part of this task.

Limitations: no Word application/page-render inspection; no simulation runtime or complete executable market tape; no application unit/integration, PostgreSQL race, security, two-user gameplay, balance, provider, load or ML tests. Library reviews were source/license/API inspections, not installation/compatibility/benchmark/security tests. Financial sources illustrate practices within their stated scope; contract parameters and synthetic calendar remain authored game choices.

