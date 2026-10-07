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
