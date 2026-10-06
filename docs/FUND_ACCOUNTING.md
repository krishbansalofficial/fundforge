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
