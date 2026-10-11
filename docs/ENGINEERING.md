# Engineering notes

How FundForge keeps simulated money correct. Each claim links to the code and the test that backs it.

## 1. A ledger that cannot lie quietly

- **Journal.** `backend/src/fundforge/journal.py` stores immutable entries. Each entry balances on its own and belongs to exactly one entity, fund or firm. Amounts are whole-cent `Decimal`s, and floats are rejected at the boundary (`money.D`).
- **Two representations.** The engine keeps economic state (positions, loans, series claims) separately from the journal. `Engine.reconcile()` asserts after every event that they agree:
  - long securities and short liability equal position × mark;
  - each series' capital and provision accounts equal its state;
  - NAV equals the sum of series net capital;
  - cash is never negative and debt is within the credit limit.

  A balanced but wrong posting therefore fails loudly.
- **Accruals.** `Accrual` carries the sub-cent remainder of each obligation. Daily fees post in cents without drift (FUND_ACCOUNTING §6 oracle 6 is in `tests/test_journal.py`).
- **Tests:** `tests/test_journal.py` (Hypothesis checks zero trial balance and idempotent replay), `tests/test_series.py` (oracles 1–5 and 7), `tests/test_engine.py`.

## 2. Fund money and firm money stay apart

The management company has its own journal. The only path from fund cash to firm cash is a fee payment, posted as a fund entry and a firm entry together with `post_many`. Payroll is paid only from firm cash, and an unpaid bill is recorded as an incident. It is never funded from the fund. Test: `test_fund_cash_never_pays_firm_payroll`.

## 3. Two partners, bound approvals, safe retries

- **Authority.** `governance.py` gives the portfolio manager independent tickets up to 5% of NAV each and 15% turnover in total. Anything larger is a package. Its sha256 digest binds the policy version, contents and expiry. It is authorized only when the *other* partner signs that exact digest. A wrong digest, a self-signature, or an expired package is rejected.
- **Persistence.** `store.py` treats Postgres as the authority. Each room keeps an append-only command log, guarded by a trigger, plus the journal entries each command produced. A command runs in one transaction:
  1. lock the room row;
  2. check `unique(room_id, idem_key)`;
  3. replay and apply the command;
  4. append the command and its journal entries;
  5. bump the version.
- **Race tests** (`tests/test_store.py`) run against real Postgres with separate connections:
  - four concurrent signatures authorize exactly once;
  - five concurrent retries of one key create one order;
  - simultaneous "ready" from both partners advances time exactly once.

## 4. No future information

The tape stays server-side. A player view is built only from events that have already been processed. Orders accepted at a decision barrier execute at the *next* execution event, never at a mark that has already been published. Test: `test_view_never_contains_future_information`.

## 5. An as-of terminal without a second economic authority

The game now includes [Forge Terminal](TERMINAL.md). `Engine.advance()` captures effective marks only after processing and reconciliation. `terminal.snapshot()` builds quotes, signed exposure, current maintenance headroom and three hypothetical stresses from that observed state. An authenticated GET reads a consistent Postgres-backed room version; it creates no command, clears no readiness and changes no journal entry. All financial calculations remain in Decimal; Godot floats only format and plot them.

The stress arithmetic has a hand-worked opening oracle: longs $27.5m and shorts $5m under a 10% sell-off produce -$2.25m P&L, $22.75m hypothetical NAV and $10.4625m maintenance at the current 35%/40% coefficients. It is explicitly a static sensitivity, not an invented future execution model.

`test_terminal.py` poisons unprocessed prices and unreleased research, verifies output is unchanged, mutates returned nested structures and checks the engine remains untouched, compares full histories across repeated base/rally runs, and drops the session cache before checking PostgreSQL replay yields identical analytics without logging reads. Existing scenario journal goldens pass unchanged. Godot tests exercise each function's controls, preservation of partial command text and recovery from stale/late responses. See TERMINAL for local results and remaining limitations.

## 6. Accounting checks survive Python optimization

All financial guards in `engine.py` now use explicit `InvariantError` checks. An error carries a stable code, detail and the simulation day/phase. It is a `RuntimeError`, distinct from `CommandRejected` and `ValueError`, so an internal accounting break is not translated into an ordinary player-validation response. Reconciliation uses the fixed 40-digit Decimal context instead of inheriting a caller's precision.

| Guards | Failure codes |
|---|---|
| Positive total opening units before allocation | `opening_units` |
| Balanced fund/firm trial balances | `trial_balance` |
| Long and short marks reconcile to holdings | `long_securities`, `short_liability` |
| Each series' capital and performance provision reconcile | `series_capital`, `series_provision` |
| At allocated P&L, NAV equals series net claims | `series_nav` |
| Fund and firm cash, borrowing limit, restricted collateral | `negative_cash`, `credit_limit`, `negative_collateral` |

`test_invariants.py` injects real state errors and balanced-but-wrong postings. Fresh child interpreters run **both `-O` and `-OO`** and must reject all eleven corruption cases and zero opening units. Their probes use explicit exceptions; running pytest with its assertions disabled is not the evidence. Separate optimized processes compute all four existing scenario goldens and match the committed JSON.

An injected failure during execution is checked at both authority boundaries: Session restores the journal, observed history, readiness and version, while a real PostgreSQL transaction adds no failed command row, preserves verification results and leaves the committed cache intact. Direct Engine calls are not transaction wrappers: a caller must discard an engine whose transition failed rather than continue from its partially applied state.

**Compatibility decision:** no economic rules bump. Existing invariant predicates and all valid-path economic outputs are unchanged; the failure mechanism and diagnostic type change. Opening's new early guard rejects the same nonpositive total-unit inputs that `allocate` already refused. Reconciliation's fixed context changes no postings. The four normal/optimized scripted-path goldens and rules/tape hashes remain byte-for-byte equivalent. Future changes to valid fill quantities, timing or accounting require the usual rules bump and regenerated goldens; this decision is not a waiver for them.

Local checks on 8 October 2026: **111 backend tests passed with PostgreSQL**, including 20 new invariant cases; Ruff and mypy passed. The 21-test targeted run included the existing normal-mode golden test. Existing Starlette/httpx and API-store pool-shutdown warnings remain. No hosted deployment, CI run or new client check is claimed for this backend-only slice.

## Deliberate simplifications

These are listed in [PROGRESS](PROGRESS.md#known-limitations) and marked in code where relevant. Earlier scope cuts are recorded in [REPLAN_V3](archive/REPLAN_V3.md); the active continuation is ROADMAP v4 and HANDOFF.

## 7. Exact limit quantities

The old 5% quantity step-down could skip the largest executable fill. `execution.limit_quantity` uses upper-mid integer bisection on the existing six-decimal HALF_EVEN price function: positive reference and nonnegative impact make adverse average incremental price monotone; rounding preserves ordering and permits plateaus. Zero is an unpriced sentinel. Complexity is logarithmic in bounded quantity. This sizes the price-acceptable quantity only; Engine still enforces volume participation shared across sides, cumulative same-side impact, reduce-only positions, borrow inventory, initial margin and governance. A risk-rejected leg is not rescaled by this search.

`test_limit_execution.py` independently expands the cubic difference to average impact, exhaustively enumerates small quantities for all sides and prior fills, and checks equal/adjacent microtick/midpoint limits. The regression limit prices 99 shares exactly: the old search moved from 100 to 95, the new one fills 99. Real Engine fills reconcile and preserve capacity and position bounds.

Evidence: 26 new cases, 137 full PostgreSQL tests passing, Ruff/mypy passing. Rules `case1-rules-2026.10.4` are economically distinct even though the four existing market-order golden paths are unchanged. Regenerated goldens update only their rules tag. Store rejects incompatible rooms; existing room records were not migrated. Local running servers must reload deliberately, and old rooms require their original runtime. Loan-bound recalls remain the next implementation task.

## 8. Loan identity and detached analysis

Recall and replacement fixture records name old/new loan IDs. Execution reserves exact loan returns on each pending cover, first the outstanding recalled quantity, then the most expensive available loan. The reservation survives financing failures and rate changes. Pending shorts receive identities at execution so same-event close orders can reserve the correct future loan. Reconciliation checks uniqueness, reservation bounds and `settled borrow + pending shorts - pending covers == economic shorts`. Replacement cannot consume reserved shares. Rates change only for a named loan on the effective public event; an absent retired loan remains absent. Unresolved recalls retry after a halted deadline even if an offer was accepted. Rules 2026.10.5; fixture version pin changed; baseline path NAVs/digests remain unchanged.

`liquidity.py` reuses execution/settlement/accounting on a deep copy with current margin terms frozen and no event advancement. A bounded greedy comparison includes calendar carry and a carry cushion; `test_liquidity.py` independently checks quantity relief and execution cost, live-state isolation, future-tape exclusion, funding shortfalls, insolvency, slower low-capacity recovery and stale governance. `debrief.py` reconstructs a completed Session, optionally omits one decision, rebinds version-only time tokens, preserves signatures and records rejections. Tests cover deterministic baseline/branch digests, consequence differences, signature refusal, clock and ready paths, completed-only access and PostgreSQL reload without new writes.

Incidents now have code/day/phase/refs/amounts/text. Outcome classification uses explicit codes; display strings remain compatible with existing clients. A test replaces every incident message and verifies classification/score remain stable.

9 October evidence: 173 full backend tests, 69 Godot checks, lint/types, import/boot, and `analysis_smoke.py` against real local HTTP/PostgreSQL. Limits: the lab is not a globally optimal solver or independent accountant; replay alternatives are single-action omissions, not persisted branch sessions. Future campaign, private research, administrator certification and shipping milestones remain separate.

## 9. Role-bound evidence and independent execution controls

Scenario 4.1.0 / rules 2026.10.6 adds per-role topic ownership, location validation, two assignments per role and one per decision window. Assignment activity is shared; revealed evidence is filtered until the owner shares. `visible_notices` centralizes visibility for views/terminal, and clock pause reasons avoid private text. Database replay and malicious role-query tests prove the boundary. Direct engine scenario scripts retain unowned/shared research for existing numerical path oracles; authenticated command routes always supply the role. Godot and Next.js expose sharing, and the deterministic MP bot uses the same command.

`shadow.py` is independently implemented with its own Decimal context and expanded cubic repricing. It rebuilds positions from frozen execution confirmations and computes market values, then NAV conditional on supplied book cash/liabilities. A coherent phantom position plus balancing posting passes internal `reconcile` but fails this check. Redemption dealing checks it before burning units. This is not full independent cash/financing/LP certification: those inputs need external records and a break-resolution workflow. Tests state that scope rather than certify the entire administrator milestone.

10 October: 192 backend tests passed, 74 Godot checks, import/boot, Ruff, mypy (19 modules), Next.js build. API lifespan/test ownership now closes pools cleanly; Starlette/httpx deprecation remains. Real HTTP smoke on current rules proved private research hidden then shared, exact baseline replay and unchanged verified books after both analyses. No commits/public deployment or human playtest.

## 10. Independent broker activity and correction provenance

`broker.py` uses only stdlib and a private Decimal context. Frozen dated activity drives a separate cash/collateral/debt and loan reducer; daily loan/debit fee lines use independent ACT/360 arithmetic and per-identity residuals. Journal comparison checks aggregate posted charges by date as well as accrued/invoiced balances. A balanced extra financing charge and offsetting wrong-date entries fail these checks while passing internal trial balance. A low-precision caller cannot change control results.

Authored statements are versioned observations with separate as-of and publication coordinates. Revisions form a validated source/account/as-of chain. Historical broker snapshots support late arrival without comparing to today's balance. Resolution appends provenance after an authenticated MP command verifies the exact current version/revision and matching evidence. It never updates statements or posts a balancing plug. Replay, including PostgreSQL reconstruction, regenerates activity, evidence and resolutions; fixture and rules pins prevent silent reinterpretation.

The playable challenge extends the existing tape with a small statement overlay instead of a duplicated market fixture. New-risk acceptance and execution recheck the combined controls. Dealing checks before units burn; an unresolved broker break records a missed window instead of rolling evidence back. Independent execution integrity failures still abort. This boundary allows ongoing payments and risk reduction while preserving the discrepancy. See [BROKER_CONTROLS](BROKER_CONTROLS.md) for limitations, especially shared transaction inputs and pending LP/management-fee certification.

11 October evidence: 214 full backend tests with PostgreSQL; 21 focused broker cases also pass after context-isolation hardening; 77 Godot checks, import/boot, Ruff and mypy (20 modules). Real local HTTP challenge smoke includes successful review, unchanged live books and an omitted-review branch that blocks dealing. Four canonical journal digests and NAVs remain unchanged; rules/tape tags advance to 2026.10.7 / fixture 4.2.0.

## 11. Independent LP capital and redemption candidates

The stdlib-only administrator calculates common P&L from reconstructed assets less independent claims, rather than copying posted P&L. It uses a separate largest-remainder allocation, per-series fee residuals and algebraic capital-above-HWM provision calculation. Frozen calendar closes retain inputs/outputs. Redemption preview compares every surviving capital/unit/HWM field and monetary claim before application. Fund fee liabilities are independently reconciled to the manager's receivable/revenue. Dated fee tests catch compensating wrong-date postings despite matching final balances.

Evidence: 228 PostgreSQL-backed backend tests, 78 Godot checks, import/boot, Ruff/mypy (21 modules) and real two-seat HTTP challenge smoke. Canonical economics and tape digest are unchanged, rules advance to 2026.10.8. The administrator still shares observed marks, pending settlement instructions and payment confirmations; it is not an external certifier. Full design, limits and next settlement-identity task: [ADMINISTRATOR_CONTROLS](ADMINISTRATOR_CONTROLS.md).
