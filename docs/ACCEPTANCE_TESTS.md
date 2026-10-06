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
