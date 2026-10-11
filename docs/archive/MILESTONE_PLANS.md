# Detailed milestone work packages

Planning revision 2.2-M1, 7 October 2026. All 20 milestones are pending. These plans expand the existing [roadmap](IMPLEMENTATION_PLAN.md); they do not implement software or claim completed tests. Existing uncommitted v2.2 work is preserved. One builder owns each bounded package; additional agents are used only when explicitly authorized. Application paths and execution commands below are proposed until created by the corresponding implementation task.

## How to execute one package

Before editing, inspect Git status, current handoffs and the selected package's inputs. Confirm its prerequisite evidence actually exists. Resolve that package's due decisions in [PLAN_REVIEW_AND_DECISIONS](PLAN_REVIEW_AND_DECISIONS.md). Do not rebuild completed research or implement later rows to make the current one appear complete. If an input is missing, identify the specific artifact/contract, repair it within the bounded scope or record a blocked prerequisite; never substitute an assumed result.

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
