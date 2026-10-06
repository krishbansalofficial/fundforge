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
