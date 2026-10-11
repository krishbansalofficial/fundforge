# Simulation architecture — v2.2

Design-time interfaces and ownership. The as-built modules are in [ARCHITECTURE](ARCHITECTURE.md); real status is in [PROGRESS](PROGRESS.md). The architecture is a **modular monolith with one economic authority**, not a network of trading platforms. [FUND_ACCOUNTING](FUND_ACCOUNTING.md) owns exact financial/event conventions; [GAME_SYSTEMS](GAME_SYSTEMS.md) owns player permissions and gameplay; this document owns software boundaries. Resolve conflicts explicitly before FF0 freezes schemas.

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
