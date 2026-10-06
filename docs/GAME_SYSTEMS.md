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
