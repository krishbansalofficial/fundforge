# Broker controls and statement challenge

Implemented 11 October 2026. Rules `case1-rules-2026.10.7`, fixture 4.2.0.

## Play the challenge

In Godot's opening menu, select **Broker review challenge**, then start solo or a two-player fund. API clients can create a room with `scenario: "case1-controls"`. The ordinary `case1` scenario has a matching opening cash statement; the challenge overlays `fixtures/broker_break_example.json` on the same market scenario and hashes the resulting tape. Market variants remain hidden until the debrief.

The broker initially reports $100 of opening unrestricted cash. The independent activity record expects $0. Open **T → RISK** to inspect the statement, source, as-of time, publication time, reported balance and expected balance. The discrepancy blocks BUY/SHORT acceptance and execution. SELL/COVER reductions, cancellation, research, signatures for valid reductions, and scheduled payments remain available.

On day 13 at PUBLIC_MARK, the broker publishes revision 2, removing its duplicate $100 credit. The correction is unavailable to players before that event. The managing partner must select **Accept matching correction**. The portfolio manager can read the evidence but cannot resolve it. In solo PM mode the operating bot performs this review through the same command path.

Review appends a resolution and leaves both statement revisions intact. It makes no cash adjustment and posts no journal entry: this example corrects the broker's statement, not the fund's books. An actual book discrepancy cannot be dismissed by this command or fixed with an unexplained plug.

An unresolved break at day 20's dealing close prevents unit burning and payable creation. A typed `dealing_blocked` incident records the missed window, and the ending is Distress. Case1 has only one dealing window: there is no automatic late dealing or backdated catch-up. Existing due payments still run. A later campaign must explicitly author another dealing window and its claim/late-payment rules.

## Independent calculation boundary

`backend/src/fundforge/broker.py` imports only the standard library. It never imports the engine, journal, execution pricing or shared accrual helpers.

| Evidence | Calculation/check |
|---|---|
| Opening fixture balances and loan identities | Initialize a separate fund cash/collateral/debt and settled-loan book |
| Frozen dated activity confirmations | Reduce draws, repayments, collateral transfers, successful settlements, loan issues/returns/rerates, invoices and payments independently of journal legs |
| Calendar-date fee lines | Recompute each outstanding loan's quantity × observed mark × APR / 360, plus broker debit × APR / 360; use independent HALF_EVEN cent rounding and per-identity fractional residuals |
| Book financing postings | Compare accrued and invoiced balances and aggregate charges for each calendar date; do not identify charges by display memo |
| Dated authored statements | Compare the reported balance with the broker snapshot at the statement's original as-of event, not today's balance |
| Original and corrected statements | Retain immutable revisions and resolution records, including source, reason, owner and calendar-day age |

A cover execution reserves a return but does not stop fees. Only its successful settlement records a loan return. Partial returns reduce that specific identity; new settled loans and rate changes have separate activity records. Weekend dates accrue separately. Invoicing moves an independently calculated liability; paying it reduces that liability without charging another expense.

Cash and financing comparisons are exact at posted cents. No one-cent discrepancy is silently forgiven. Existing `shadow.py` retains its separately implemented execution/holdings checks and disclosed valuation tolerance. RISK's combined result remains `checked` or `break`, never full NAV certification.

The simulated confirmations share the engine's instructed transaction amounts, identities and observed marks. This detects posting omissions/corruption and independently checks financing arithmetic; it does not prove the instructions themselves came from an external bank. Both reducers could share a bad upstream instruction. Management-company cash, management/performance fee allocation, LP claims and full administrator NAV certification are outside this slice. Live arithmetic discrepancies appear in the control report; the aged, manually resolved queue currently covers authored statement discrepancies.

## Authoring and command contracts

`broker_statements` records contain `id`, positive sequential `revision`, `source`, `account` (`cash`, `collateral` or positive `debt`), `balance` as a finite nonnegative cent-valued string, `as_of: {day, phase}` and `available_at: {day, phase}`. Revisions after 1 must name the previous revision in `supersedes`, retain source/account/as-of coordinates, provide a nonempty correction reason and arrive at a strictly later event. Invalid records fail tape compilation.

Snapshots represent the event's broker balances. CLOSE statements are observed before the dealing gate. A late statement compares to its retained historical snapshot. Future statement payloads are not included in player projections. Statement history and resolutions rebuild from pinned fixture data plus the ordinary command log, including after the PostgreSQL cache is cleared.

The authenticated MP command is:

```json
{"type":"resolve_statement","statement_id":"opening-cash","revision":2,"version":4}
```

Supply the room's current version, not the example value. Existing `Idempotency-Key` handling applies. The server requires a decision barrier, current version, latest published matching revision, an open queue item and no current book discrepancies. The client never supplies a replacement balance or mark. Repeat delivery of the same accepted key returns the original result without adding another resolution.

Completed-run REPLAY can omit `resolve_statement`. Branches rebind review/ready/tick version tokens while preserving the exact statement ID/revision and all signed package contents. The omitted-review branch keeps the unresolved break and records the blocked dealing action. It does not mutate the live room.

## Evidence and reproduction

Full backend suite: **214 passed with PostgreSQL**. Godot: **77 checks passed**, editor import and headless boot passed. Ruff and mypy passed across 20 modules. Only the existing Starlette/httpx deprecation warning remains. No new human playtest, graphical capture, public deployment or external-bank integration is claimed.

Tests cover a balanced-but-wrong financing/cash posting, date-shifted charges with unchanged balances, independently worked partial-return/weekend/rate/residual examples, real T+1 cover fee dates, immutable evidence, no future corrections, stale/wrong-role review, idempotency, new-risk execution rechecks, continued reductions/payments, a statement arriving at the dealing close, successful review, omission replay, solo bot review, authenticated HTTP and PostgreSQL reconstruction.

```text
python scripts/analysis_smoke.py --server http://127.0.0.1:8011 --broker-challenge
```

The real two-seat run passed with rules 2026.10.7, version 41, two liquidity strategies, exact baseline replay, unchanged verified live books, explicit private-evidence sharing, and blocked dealing when review was omitted. Tokens stay in memory and are not printed. The omitted-cover NAV difference was -45.42 in that run, a scenario-specific observation.

The subsequent management-fee/LP-claim slice is now implemented; see [ADMINISTRATOR_CONTROLS](ADMINISTRATOR_CONTROLS.md). Next: independent settlement obligation/receipt identities. The historical limits above describe the broker-only slice; combined controls still do not constitute external NAV certification.
