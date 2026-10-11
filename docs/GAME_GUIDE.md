# How to play FundForge

FundForge has one scenario today: **Case1, "The borrow is not the thesis"**. It covers business days 12 to 21 of a fictional season, Tuesday 20 January to Monday 2 February 2026. The authority for every number in this guide is `fixtures/case1.json` and `backend/src/fundforge/`. If the two ever disagree, the code wins and this guide has a bug.

## 1. The fund you inherit

| | Starting state |
|---|---|
| Investors | Three LP series at $100 a unit and a $100 high-water mark: Seed (100,000 units), Patient (80,000) and Tactical (70,000). Total $25m. |
| Long book | ALTO, COVE, ELAN, GALA and IONA at 30,000 shares each; JUNO 25,000; BEAM 100,000 |
| Short book | BRIN, DART, FENN and HELI at 12,500 shares each, all borrowed |
| Financing | $5m restricted collateral, $2.5m of debt and a $7.5m credit line |
| Management company | $240,000 of its own cash and payroll of $4,000 per business day, paid every fifth day. Fund money cannot pay it. |

All tickers and firms are fictional.

## 2. Roles

There are two partners. Solo, the bot plays whichever seat you leave (§7).

| | Portfolio manager (`pm`) | Managing partner (`mp`) |
|---|---|---|
| Trade alone | Yes. Independent tickets of up to 5% of NAV each, and up to 15% of opening NAV in total. | No |
| Propose a package | Yes | Yes |
| Countersign a package | Only the other partner's | Only the other partner's |
| Assign research | Demand survey/crowding: own budget of 2 | Borrow/debt: own budget of 2 |
| Accept replacement borrow | No | Yes |
| Set the treasury reserve | No | Yes |
| Pause, set speed, mark ready | Yes | Yes |

**Packages.** A package is any trade bigger than a ticket. Its SHA-256 digest covers:

- the authority policy;
- the mandate version;
- the exact orders;
- an expiry at the next execution window.

It is authorized only when the *other* partner signs that exact digest. Editing it means proposing a new package. An unsigned package expires when time moves on.

**The mandate** (version `case1-mandate-v1`):

- gross exposure between 80% and 200% of NAV;
- net exposure between 40% and 110%;
- no single issuer above 15% (BEAM and BOND are exempt).

It is checked when you send a ticket, when a partner signs and again when the order fills. An order is refused only if it would break a limit *and* make that limit worse, so trades that reduce risk are always allowed. A signature never overrides the mandate.

## 3. Locations and terminals

Walk into a room and press `E` or `Enter` to open its terminal.

| Location | Terminal |
|---|---|
| Trading floor | Positions and marks. Choose a side, symbol and quantity. The PM can **send a ticket**; either partner can **propose a package**. Orders fill at the next execution window, with market impact. |
| Committee room | Every package with its status and the start of its digest. **Countersign** your partner's package here. *I'm ready to move on*: when both partners are ready, time jumps straight to the next window. |
| Risk and treasury | Maintenance requirement against NAV and any **margin call** deficit. The MP sets the **treasury reserve**, the cash held back from repaying debt. |
| Research library | Four topics and how many assignments are left. Findings arrive at the next day's market open. |
| Management company | Firm cash, fees receivable (not spendable until the fund pays them) and payroll owed. Shows the firm's and the fund's journals. **Verify the books** replays the whole room and shows the chain head. |
| Investor lounge | Each series: units, NAV per unit, high-water mark and performance provision. |
| Prime broker (across the street) | Recall status and borrowed shares. Once the offer is known, the MP can **accept the replacement borrow** here. |
| Street view | The league table of your fund against the five rivals. `L` opens it from anywhere. |

The HUD shows NAV, gross and net, cash, debt, credit left, firm cash, maintenance headroom, the desk feed (notices and partner messages) and the clock.

Locations are where things are done, not gates. Every terminal works no matter where your partner is.

## Forge Terminal

Press **T** or select **Terminal [T]** on the HUD. It is a financial workstation inside the game. Enter `MON`, `BRIN GP`, `PORT`, `RISK`, `NEWS`, `ORDERS`, `STREET`, `HELP` or `REPLAY`; any known symbol alone opens its chart. **F1-F9** switch functions and **Esc** closes it. The market monitor combines quotes, an observed price chart, fund headroom and published headlines. Use **Trading desk** to return to tickets and jointly approved packages.

Charts show processed-event marks, not candles or a prediction. The risk page's three static shocks are hypothetical sensitivities at current margin rates; they do not trade, release collateral or forecast future financing. A connection failure labels the last data stale. Opening the terminal leaves the simulation clock running, so pause from the HUD first if you need time to analyze. Full function reference and screenshots: [TERMINAL](TERMINAL.md).

## 4. Time

Each business day has five phases:

| Phase | Time | What happens |
|---|---|---|
| `OPEN_ADMIN` | 08:00 | Notices; settlement; replacement-borrow transfer; collateral true-up; payments due (redemptions first, then fees, then interest); debt repayment |
| `PUBLIC_MARK` | 09:30 | New marks; recall and research reveals; a margin call if maintenance is short |
| `EXEC_A` | 10:00 | Execution window: rivals trade first, then your queued orders fill |
| `EXEC_B` | 15:00 | Second execution window |
| `CLOSE` | 16:00 | Unfilled orders expire; payroll accrues; fees and interest accrue for every calendar day up to the next event (weekends included); redemptions are dealt |

You decide at a **barrier** before each execution window. There are 18 windows from day 12 to day 20, and the game ends at day 21's opening, when the redemption is paid.

**Clock.** The game starts paused.

- **Speed.** Press `Space` or the HUD buttons for Pause, 1x, 2x or 4x. At 1x the server advances one window every 8 seconds of real time (`FUNDFORGE_SECONDS_PER_WINDOW`); 2x takes 4 seconds and 4x takes 2.
- **Auto-pause.** The clock pauses itself when a new notice or incident arrives, when a package is waiting for a signature, and at the end of the season. The reason is shown in the top bar.
- **Skip ahead.** When both partners mark ready in the committee room, time jumps to the next window. A ready only counts for the plan you saw: if anything changed after you looked, it is refused as stale.

## 5. The crisis timeline

This is everything the game itself announces, in order.

| When | Event |
|---|---|
| Day 12, open | **Redemption notice.** Tactical will redeem 10,000 units at the day 20 dealing close, payable on day 21. **Margin terms:** from day 16 the prime broker applies stressed coefficients. Initial margin rises to 80% long and 100% short; maintenance rises to 70% long and 90% short. |
| Day 13, mark | **Recall.** The prime broker recalls 1,250 BRIN. You must cover by day 15's 15:00 window or deliver an accepted replacement borrow; otherwise a **forced buy-in** executes. No new BRIN can be borrowed from day 13. |
| Any barrier | **Research.** You have two assignments, and each reveals at the next day's mark. Topics: *BRIN borrow availability* (reveals the replacement offer), *BRIN debt schedule*, *BRIN demand survey*, and the *prime-broker crowding report*. The crowding report is computed from the street's live positions at the moment it is revealed. |
| Day 14, 15:00 | Last window to accept the replacement borrow (MP only, and only once its offer is known): 1,250 BRIN at 40% a year, transferred at day 15's open. |
| Day 15, 15:00 | Recall deadline. |
| Day 16, mark | **The hidden market.** Your fund drew one of two worlds when it was created. The world isn't shown until the debrief. The stressed margin terms apply from today. |
| After any mark | **Margin call** if maintenance is short. Cure it at the next execution window, or the broker sells your largest longs (then covers shorts) until it is met. |
| Day 18, mark | **Halt warning.** BEAM may be suspended later this week pending a sponsor review. |
| Day 20 | **BEAM is halted.** It cannot trade in either window. Weekly payroll is paid from firm cash. Fees and interest are invoiced. At the close, Tactical's redemption is **dealt**. |
| Day 21, open | **Payment.** The redemption is paid from fund cash, raising cash first if needed. The invoiced fees and interest are paid next. Then the season ends and the debrief opens. |

Rival-fund news (deleveraging, blow-ups, liquidations) can arrive at any execution window.

## 6. Rivals, score and endings

**Rivals.** All five rivals are rule-based and see only public marks:

- Halcyon Partners runs a crowded short book. It cuts 35% of its book on a margin breach.
- Northbeam Capital trades momentum.
- Granite Macro trades BEAM against BOND.
- Vantage Quant trades mean reversion.
- Copperline Activist sells into a drawdown of more than 8%.

Rivals trade before your orders at each window, and all their trades together are capped at 10% of each instrument's volume. Everyone's net flow, yours included, moves prices through a permanent-impact multiplier that is capped at ±15% and decays 25% toward fair value at every event. A rival whose NAV goes negative blows up and liquidates over the following windows. The towers on the skyline flash when that happens.

**Your fills.** You can trade at most 5% of an instrument's volume in each window. You pay a half-spread plus impact that grows with the square of your share of the volume. Splitting an order inside one window doesn't reset the impact.

**Tier** (at the end):
- **Distress:** NAV ≤ 0, or anything unpaid (a payment shortfall or failed settlement).
- **Survival:** everything was paid, but a forced action happened (a recall buy-in or a margin liquidation).
- **Win:** neither.

**Score.** Your unit return minus the return of a passive buy-and-hold of the opening book (which pays no costs), in basis points, minus **150 bps for each forced action**. Redemptions leave at NAV per unit, so investor flows don't distort it.

**Rank.** Your place in the league table among six funds, by return since the start.

The debrief shows all of this, reveals which day-16 world you were in, and prints the tape and journal digests as replay proof.

## 7. The bot partner

In solo play the other seat is played by `bot:v1`, shown as "Morgan (bot)". It is a deterministic rules policy, not an AI model. It acts after each of your commands and after each clock tick, through the same commands and checks you use, and its messages appear in the desk feed.

- **As managing partner**, it assigns the BRIN borrow check if that topic is unassigned, and shares the finding when it arrives. When the offer is known and the recall is still uncovered, it accepts the replacement borrow.
- **As portfolio manager** it covers whatever recalled BRIN is still short with a ticket (unless a replacement is accepted). On a margin call, it sells its largest non-exempt single-name long, sized to the deficit and capped at its 5% ticket limit.
- **Your packages.** It countersigns any package that passes the mandate. When a package breaches the mandate, it refuses and says why. It checks legality, not whether the trade is wise.
- **Ready.** It marks ready whenever you do.

**Limits.**
- It never proposes packages and never trades for profit.
- A large margin call can exceed what one 5% ticket can cure.
- A bot-partner room is still a two-partner room, and every bot action is a hash-chained command that `verify` replays.

## 8. Tips

These go no further than what the game tells you.

- Read the day 12 notices before pressing play. The recall, the margin step-up and the redemption are all announced in advance.
- Research takes a day to arrive, so a finding you need before a deadline has to be assigned at least a day before it.
- Stressed margin from day 16 raises your requirement even if prices don't move. Check your headroom in the risk room before then.
- You can't flatten the book to dodge the crisis, because the mandate's gross and net floors refuse it.
- BEAM is your largest long, and the exchange warns that it may halt. A halted name can't be sold to raise cash.
- Tactical's redemption is paid in cash at day 21's open. The treasury reserve and the credit line decide whether that's easy.
- Fund cash never pays firm payroll. Watch the management company terminal separately.
- You don't know which day-16 world you are in, so a plan that only works in one world is a gamble.

## Research cooperation and deeper terminal tools

Each partner can take one assignment per decision window, with two assignments each across Case1. PM topics are demand survey and crowding; MP topics are borrow availability and debt schedule. Each assignment names its location. Use the research desk to claim it, read the next-open finding and explicitly share it. The other partner sees where you are working but cannot read private evidence until you share. Signatures, trading and mandatory notices remain available while attention is committed.

On RISK, choose mark shocks, a volume assumption and a 1-10 event horizon, then compare hypothetical cure paths. Results show settlement/funding progress and assumptions. Review first-event orders at the trading desk before proposing the exact package to your partner. A changed fund version requires a fresh analysis. These are greedy hypothetical plans, not promised prices or an optimal forecast.

After the season, REPLAY/F9 reproduces the recorded run and lets you omit a selected decision. It reports consequences and any later command that no longer works. It never changes the played room. RISK also reports independent execution/valuation checks; full external cash and fee certification is still in development.

## Broker review challenge

Select **Broker review challenge** in the opening Godot menu. The broker reports an incorrect $100 opening cash balance. Open **T → RISK** to inspect the discrepancy and its age. On day 13 the broker sends a linked correction; the managing partner can accept the matching correction from RISK. Both records remain visible afterward. Solo players acting as PM have an operating bot that reviews it.

Resolve the break before day 20's dealing close. While it remains open, new BUY/SHORT risk is blocked, but SELL/COVER reductions, cancellations and due payments continue. Missing the dealing window leaves investor units untouched and records a Distress outcome; the game does not pretend the redemption happened. REPLAY lets you compare the result without the recorded review. [Control scope and evidence](BROKER_CONTROLS.md).

RISK also shows **LP / FEE CHECK**: independent series units, last-close capital, provisions and high-water marks. After dealing, inspect the actual redemption price, payable and crystallized fee. These checks guard the calculation before units change. Series capital is updated at calendar close; current intraday market P&L has not yet been allocated to investors. [Details](ADMINISTRATOR_CONTROLS.md).
