# Current project state

Updated 10 October 2026. Active plan: [ROADMAP](ROADMAP.md) (v4). Graphical layer: [WORLD_GAME_PLAN](WORLD_GAME_PLAN.md) as amended in the roadmap.

Current continuation: [HANDOFF](HANDOFF.md). Terminal contract, screenshots and evidence: [TERMINAL](TERMINAL.md). Historical FF0a handoffs are superseded; do not restart from them.

## What exists and runs

| Area | State | Evidence |
|---|---|---|
| Engine (`backend/src/fundforge`) | Decimal per-entity journal, LP series and HWM, impact execution, dated Case1 session (recall, margin, settlement, dealing, firm payroll) | Oracle, property, scenario and golden-digest tests |
| Rules | Versioned compliance mandate on tickets, signatures and every fill; hidden market variants (sell-off or rally); benchmark-relative score and league rank | `test_balance.py`: flatten refused, no dominant policy |
| Market | Five rule-based rival funds whose flow moves prices. Permanent impact with resilience produces an emergent short squeeze, deleveraging, blow-ups and a crowding report | `test_market.py` |
| Governance | Two roles, digest-bound packages, all-or-nothing commands, version-bound ready, chat | Stateful Hypothesis test of random command sequences |
| Solo play | Deterministic bot partner (`bot:v1`, not an LLM) using the same commands and checks; owner decision 8 Oct 2026 | `test_bot.py`; bot rows chained and verified in Postgres |
| Time | Real-time clock (pause, 1x, 2x, 4x) with auto-pause; ticks are logged, version-bound commands | Clock tests; two schedulers racing produce one tick |
| Persistence | PostgreSQL command log with numbered migrations, pinned rules/tape/variant per room, hash chain, SQL-checked balanced `journal_lines`, TRUNCATE refused; `verify(room)` re-derives everything | Separate-connection race and tamper-detection tests |
| Game client (`game/`) | Godot 4.7 desktop simulation. The 3D office and city use Kenney CC0 models, animated characters, lighting tied to the in-world hour, rival towers, a Street league table, solo/duo menu and HUD terminals per location | Headless Godot tests and boot check in CI; screenshots verified locally |
| Web desk (`frontend/`) | Earlier Next.js two-seat desk, kept as a secondary client | `npm run build`, audit clean |
| Forge Terminal | Godot keyboard workstation with market monitor, observed price history, signed holdings, static Decimal stress, public news, orders and league. Authenticated read model, replay-derived observations, no new economic authority | `test_terminal.py`; 26 additional Godot checks; actual PNG captures and a two-seat HTTP smoke |
| Invariant enforcement | Explicit `InvariantError` guards for opening units, per-entity trial balance, positions, series claims, NAV, cash, credit and collateral. Reconciliation uses the fixed Decimal context and stays active under `-O`/`-OO` | `test_invariants.py`: 20 cases, optimized child-process probes, golden replay and session/Postgres rollback |

Previous invariant validation: **111 tests passed with PostgreSQL**, full Ruff and mypy passed. The 20 invariant tests include real corruption, session/Postgres rollback, and fresh `-O`/`-OO` processes; all four committed valid scenario goldens are unchanged in both optimization modes. At that checkpoint, `RULES_VERSION` remained `case1-rules-2026.10.3` because invariant predicates and valid economic behavior are unchanged; only internal failure reporting/enforcement is hardened. See ENGINEERING for the compatibility rationale.

Previous terminal-slice evidence: **61 Godot checks passed** on 4.7.2. The HTTP smoke required distinct partner approval, filled a 1,250-share cover at a later event and verified the stored books. Actual market/chart/risk screenshots are in `docs/images/`. No client code changed in this invariant continuation, so those client checks were not repeated. CI results and previous frontend-build evidence are not newly claimed; no push or public deployment occurred.

The pre-existing Python 3.14 `.venv` was locked by a running local server. Checks used an isolated Python 3.13 environment without stopping that server; exact paths and commands are in HANDOFF. The remaining warning is Starlette/httpx deprecation. API lifespan now closes its database pool; the latest full run has no pool cleanup warnings.

## Known limitations

- Case1 is the only scenario. The 30-day v1 campaign, research cards and LP agents are P4 work in the roadmap.
- The partner avatar walks to the place of its last decision; live WebSocket presence is not built.
- Squeeze strength is limited by day-16 BRIN volume (25k shares); tuning notes are in the backend commit.
- No deployment, recorded playtest or exported game builds yet.
- The realistic-graphics pass is in HEAD (`c6c614c`), not an outstanding implementation task. Compatibility-renderer capture warns about the office's Forward+ effects; no GPU-performance budget has been measured.
- The terminal now includes a hypothetical liquidity/cure lab and completed-run omission replay. The lab uses frozen public assumptions and a greedy solver; it is not a forecast or globally optimal cure. Private role evidence, sharing and per-window assignments are implemented. Independent execution/holdings controls are implemented; full administrator NAV certification remains planned.
- Exact limit fills, loan-bound recalls/returns/rerates, and typed incident classification are implemented. These do not certify all P0-P5 release requirements.

## Next task

Extend independent controls to loan-fee and cash-statement reconciliation, with authored discrepancies and a persistent break queue. Keep full NAV certification explicitly pending until cash, financing and LP claims have independent sources. P2 deployment/exported builds/backups and a recorded two-client run remain open.

## Exact limit execution continuation, 8 October 2026

`execution.limit_quantity` replaces approximate 5% step-down with maximal whole-share bisection against the actual six-decimal HALF_EVEN price. Engine sizing keeps remaining quantity, shared event capacity, reduce-only and borrow inventory bounds; margin and mandate checks still run afterward. Independent expanded-cubic exhaustive oracles cover all four sides and cumulative same-side impact. A 100-share boundary now fills 99 instead of 95.

Latest validation: **137 backend tests passed with PostgreSQL**, including 26 new limit tests; targeted execution/golden run **27 passed**. Ruff and mypy passed. Known pool-cleanup and Starlette warnings persist. No client changes or new client-test claims. Rules bumped to `case1-rules-2026.10.4`; regenerated goldens retain the four market-order path digests and NAVs. Older rooms are refused by new-version servers and must use their original rules runtime; no room migration or replay rewrite occurred. The running local 8011 service has not been restarted for this rules change.

## Borrow, liquidity and replay continuation, 9 October 2026

Rules **case1-rules-2026.10.5** and fixture tape now name recall/replacement loan identities. Covers reserve exact loan returns at execution, prioritizing the recalled quantity and then financing cost; failed settlements retain those reservations. Rerates affect only their named loan. An accepted offer cannot suppress unresolved buy-ins, including after a halted deadline. Borrow balances reconcile to economic positions plus pending settlements.

RISK now contains a bounded hypothetical liquidity lab with two greedy strategies, six-decimal pricing, capacity, T+1 settlement, collateral/credit and calendar financing/management carry. First-event legs can be reviewed and proposed through the existing two-partner approval flow; stale analysis is rejected. REPLAY/F9 unlocks only after completion, reproduces the baseline exactly, and compares omission of one eligible decision. Branches have deterministic IDs, preserve signatures, report rejected suffix commands and never write to the live room. Typed incidents drive outcome/score classification independently of wording.

Latest checks: **173 backend tests passed with PostgreSQL**, **69 Godot checks passed**, Godot import/boot passed, Ruff and mypy passed (18 modules). `scripts/analysis_smoke.py` passed against the restarted local 8011 API: version 37, two liquidity strategies, exact baseline digest, completed omitted-cover branch, forced recall, NAV difference -45.42 in that randomly selected scenario, unchanged verified live books. This is one measured example, not a guaranteed strategy effect. Existing Starlette and pool-cleanup warnings persist. No public deployment or commit.

The 8011 backend now runs 2026.10.5. Create a new room; old pinned rooms are intentionally incompatible. The four existing scenario golden path NAVs/digests stayed unchanged; rules and tape digest changed. Earlier validation counts above are historical checkpoints.

## Current checkpoint, 10 October 2026

**192 backend tests passed with PostgreSQL; 74 Godot checks passed; Godot import/boot, Ruff, mypy (19 modules), and the Next.js production build passed.** API pool shutdown is now explicit and tested; only the existing Starlette/httpx deprecation warning remains. The local 8011 API runs `case1-rules-2026.10.6`, fixture 4.1.0, wrapper PID 29192. New rooms use current rules; older rooms remain pinned/incompatible. No commit, push or public deployment.

Role-specific research is active: PM owns demand/crowding assignments; MP owns borrow/debt assignments. Each role has two assignments per scenario and one per decision window. `visit` validates the assignment's location server-side; desk access remains available and mandatory actions/signatures are unaffected. Findings arrive at the next public market event and remain private until owner-issued `share_research`. Views, terminal feeds and clock messages are filtered. Godot and the secondary web desk expose assignment/sharing controls. Solo MP bot shares its findings using the same command path. Ten new backend cases include database reload, auth, early/wrong-owner sharing and leak tests.

`shadow.py` independently reprices immutable execution confirmations, rebuilds holdings and checks quoted asset values and NAV conditional on supplied book cash/liabilities. It imports no engine, posting or execution code. Nine tests cover known numerical fills, all four scenario paths, confirmation corruption and a coherent phantom position which internal reconciliation accepts. Independent breaks block redemption dealing before units/claims change; RISK displays the scope/status. This is an execution/valuation control, not full independent administrator certification.

Latest real two-seat HTTP smoke: version 40, private evidence hidden then explicitly shared, two liquidity strategies, exact baseline replay, completed omission branch with forced recall, and unchanged verified live books. Measured omitted-cover NAV difference was -45.42 for that run. Earlier counts/server versions in this document are historical checkpoints. Full campaign, LP agents, independent cash/fee/claim certification, persisted arbitrary replay branches, live presence and shipping/playtest gates remain open.

Final API compatibility check: older pinned rooms return HTTP 409 for view/ledger as well as terminal/commands; targeted terminal/API tests passed (9 passed, one database case skipped in that targeted run). Full PostgreSQL suite evidence above remains the 192-test run. API reloaded after this error-reporting fix.

## Broker controls continuation, 11 October 2026

Independent broker cash/loan-fee controls and a playable statement-error challenge are implemented. `broker.py` imports only stdlib, reduces frozen cash/loan activity separately from postings, and computes ACT/360 calendar-date charges with its own rounding residuals. Checks compare cash/collateral/debt, settled loan identities/quantities/rates, accrued/invoiced financing and daily posted charge totals. Partial returns stop fees only on actual settlement; weekends and loan rerates remain dated.

`case1-controls` overlays `fixtures/broker_break_example.json` on Case1; choose **Broker review challenge** in Godot. A $100 opening-statement error opens an aged MP-owned queue item; its day-13 correction remains hidden until publication. MP `resolve_statement` binds the current room version and latest matching revision, appends immutable resolution provenance and preserves both originals without journal edits. RISK displays sources, as-of/publication coordinates and history. Solo MP bot reviews through the same command path; completed-run replay supports omitting that review.

Unresolved controls block new BUY/SHORT orders and their execution; reductions, cancellations and due payments continue. Day-20 dealing with an open break records `dealing_blocked`, leaves units/claims untouched and produces Distress at the end. Case1 has no later dealing window; this implementation does not silently backdate/catch up a missed redemption. Existing execution/valuation integrity faults retain their explicit invariant failure behavior.

Evidence: **214 backend tests passed with PostgreSQL**, **77 Godot checks**, editor import and headless boot; Ruff and mypy **20 modules** passed. Coverage includes balanced wrong cash/financing postings, offsetting wrong fee dates, partial-return/weekend/rerate/residual arithmetic, immutable revisions, future-data protection, stale/role/idempotency checks, close-arriving statements, new-risk gates, continued payments, exact replay, solo bot, authenticated HTTP and database reconstruction. The existing Starlette/httpx deprecation warning remains. The secondary Next.js client was not changed or rebuilt in this slice.

Real HTTP validation: `analysis_smoke.py --broker-challenge` passed against local 8011, rules **2026.10.7**, fixture **4.2.0**, version 41, with private research/sharing, both liquidity strategies, exact baseline replay, omitted-cover forced recall and omitted-review blocked dealing. Live books stayed verified/unchanged by analysis. The omitted-cover NAV difference was -45.42 in this sampled variant. Local API wrapper PID **36440**, clock enabled; the default 8000 service was untouched. Create new rooms; older rule-pinned rooms remain incompatible. Four canonical path journal digests/NAVs are unchanged; goldens update the rules/tape tags.

No public deployment, commit, new graphical screenshot or human playtest is claimed. These are synthetic confirmations sharing instructed movement amounts and observed marks, not an external bank feed. Authored statement breaks have aging/history; live arithmetic differences are reported separately. Management-company cash, management/performance fees, LP claims and full administrator certification remain open. Implementation contract and reproduction: [BROKER_CONTROLS](BROKER_CONTROLS.md).

**One next task:** independently reconstruct management fees and LP series participation/provisions, then compare redemption unit price and claim before dealing. Preserve the current scoped `checked` label until all required independent components exist.

## Independent LP/fee continuation, 11 October 2026

Completed the prior next task. New stdlib-only `administrator.py` reconstructs participation from confirmed holdings at observed marks, broker balances, unsettled obligations and independent liabilities, without consuming journal common P&L or production series capital. It independently allocates common P&L, accrues per-series management fees with dated residuals, recomputes reversible provisions and validates unit/HWM/capital state. Both fund fee claims and firm fee receivable/revenue are checked, including management postings by date/series.

Each redemption candidate is independently checked for payable, crystallized fee, surviving units/net/provision and unchanged HWM before mutation. Frozen close/claim evidence survives command replay and database reconstruction. Existing LP/fee mismatches block dealing through combined controls; a bad new candidate raises `administrator_claim` before units/claims/journal change. RISK displays reconstructed series and dated dealt claims with an explicit last-close label. Read [ADMINISTRATOR_CONTROLS](ADMINISTRATOR_CONTROLS.md).

Validation: **228 backend tests with PostgreSQL**, **78 Godot checks**, editor import/boot, Ruff and mypy **21 modules** passed. Fourteen new administrator cases include independent arithmetic, recurring/weekend fees, payment neutrality, partial/full exits, provision reversal, balanced incorrect fees, unearned firm income, wrong fee dates, low precision and pre-mutation candidate refusal. Database debrief reconstruction additionally compares administrator records. Existing Starlette/httpx deprecation warning remains; no new graphical screenshot or human playtest claimed.

Real HTTP `analysis_smoke.py --broker-challenge` passed on rules **2026.10.8**, version 41: independent LP checks `checked`, 13 calendar closes, one checked redemption, exact baseline, two liquidity strategies, unchanged verified live books, omitted-review blocked dealing and omitted-cover forced recall. Sample omitted-cover NAV delta was -21.46 for that market variant; this is not a universal result. Fixture remains **4.2.0** and its digest is unchanged; canonical journal digests/NAVs remain unchanged. Local 8011 API now uses wrapper PID **5908**, clock enabled. Older rule-pinned rooms remain incompatible; use new rooms. Default 8000 and unrelated dirty work were preserved. No commit, push or deployment.

Scope: synthetic/shared market marks, pending settlement instructions and payment confirmations remain inputs. Full external certification, firm payroll/cash, annual crystallization, subscriptions and multi-window campaign mechanics are not claimed. No Next.js changes or rebuild in this slice.

**One next task:** independently reconstruct settlement obligations and receipts from immutable execution identities. Detect missing/duplicate or misallocated obligations even when the pending collection and journal agree; retain dated evidence and failed-delivery retries.

## Settlement obligation control, 11 October 2026

Completed the prior next task. Each fill now carries an obligation identity `X{n}` (n-th execution confirmation) on its `Pending` record and on the broker settlement receipt (`Activity.obligation`). Failed settlement attempts are retained as dated `(day, obligation)` evidence on every retry. Stdlib-only `shadow.inspect_settlements` rebuilds one expected obligation per confirmation (side, symbol, quantity, amount, due = execution day + 1) without engine imports and reports `settlement_missing`, `settlement_duplicate` (pending or receipt), `settlement_misallocated` (unknown identity or changed economics) and `settlement_unexplained_delay` (past due with no dated failed attempt). Breaks join `control_report`, so they block new BUY/SHORT risk and dealing like other controls.

No `RULES_VERSION` bump: valid economics, postings and goldens are unchanged; the new gate only triggers on corrupted state (same rationale as the invariant continuation). Older pinned rooms remain compatible with 2026.10.8.

Validation: **230 backend tests passed with PostgreSQL** (two new in `test_shadow.py`: engine-level duplicate/misallocated/dropped pending and duplicated receipt even though the journal is untouched; direct retry-evidence cases). Ruff and mypy (21 modules) passed. Existing Starlette/httpx warning remains. No Godot, Next.js, HTTP smoke or local 8011 restart in this slice; no commit, push or deployment.

Limitations: no scenario path drives a real failed settlement end to end, so retry evidence is tested directly rather than through the engine; RISK does not yet display settlement identities; due date assumes the engine's day+1 house rule.

**One next task:** author a Case1 overlay that forces a BUY settlement failure and retry, assert the dated evidence end to end through Store/database reconstruction, and show obligation identities and retries in Terminal RISK.

## Settlement failure/retry overlay, 11 October 2026

Completed the prior next task. New Store scenario `case1-settlement` overlays Case1 with a $2.6m credit line ($100k above the $2.5m opening debt). In the tested path a day-12 BUY of 5,000 ALTO (`X1`) fails settlement on days 13 and 14 with dated evidence, then settles on day 15 after a COVE sale's proceeds arrive; the settlement control stays clear throughout. The tight line also produces realistic follow-on distress (forced buy-in, collateral shortfalls, unpaid redemption). `control_report["settlements"]` lists every obligation identity, status, due day and failed days; Godot RISK shows pending or previously failed obligations.

Validation: **231 backend tests passed with PostgreSQL**, including a new end-to-end test that drives real propose/sign/ready commands through Store, checks `X1` failed days `[13, 14]`, clears the cache, reconstructs from the database, compares the identical control report and runs `verify`. Ruff and mypy (21 modules) passed. Godot test script: 0 failures; headless boot clean. No new screenshot, HTTP smoke or 8011 restart; the Godot menu has no button for this scenario yet (create it through the API).

**One next task:** add a menu option for `case1-settlement` and capture a RISK screenshot showing the failed/retried obligation, then return to the P2 gates (exported builds, deployment plan, recorded two-client run).

## Settlement scenario menu option, 11 October 2026

Completed the menu half of the prior next task. The Godot menu's broker checkbox is now a scenario dropdown driven by `WorldRules.SCENARIOS` (`case1`, `case1-controls`, `case1-settlement`); solo and two-player creation both send the selected key. A new Godot check pins the three keys to backend `store.SCENARIOS`.

Validation: **231 backend tests passed with PostgreSQL** (baseline, unchanged code), Ruff and mypy (21 modules) passed; Godot 4.7.2 editor import passed, **79 Godot checks, 0 failures**, headless boot clean. No screenshot captured (needs a rendered window and running API); no HTTP smoke. No rules change.

## Skip-ahead pacing (P1), 11 October 2026

Both partners can vote `{"type": "ready", "skip": true}`. When both votes are skip, `Session._cmd_ready` keeps calling `Engine.advance()` until a new notice or incident, an open (queued/partially filled) order, or the end. One skip vote plus one plain ready advances one window. Skip is refused while a package awaits a signature (it blocks instead of expiring). Because skipping only repeats the same `advance()` calls, the journal digest and NAV equal stepping through every barrier. The solo bot mirrors the human's skip vote; the Godot HUD committee panel has a "Skip quiet windows" button. No economic rule changed, so no `RULES_VERSION` bump; non-skip results keep their exact shape.

Measured: passive Case1 finishes in **6 skip rounds versus 18** stepped rounds (same with one early ALTO ticket), identical digest and NAV (`test_skip_ahead_reaches_same_journal_in_fewer_rounds`).

Validation: **234 backend tests passed with PostgreSQL** (3 new; two tests now compare `set(s.ready)` because readiness records each vote), Ruff and mypy (21 modules) passed; Godot test script 0 failures; headless boot clean. Secondary Next.js desk has no skip button.

**One next task:** P2 backups: a `pg_dump` script plus a restore-and-`verify` check that proves a restored database reproduces the same room digests.

## Backups with restore-and-verify (P2), 11 October 2026

Confirmed the solo bot already mirrors the human's skip vote (`bot.py`), so the prior next task was this one. New `backend/src/fundforge/backup.py` (`python -m fundforge.backup dump|check ARCHIVE`, `DATABASE_URL` required). `dump` opens one repeatable-read snapshot, writes a manifest of each room's stored version, last journal digest and chain head, and runs `pg_dump --format=custom --snapshot=<that snapshot>`, so archive and manifest describe the same commands. `check` restores into a fresh scratch database, requires the restored heads to equal the manifest, then runs `Store.verify` per room; it reports `verified` only when replay reproduces the manifest digest and chain head. Rooms pinned to older rules are reported `incompatible` (heads compared, not replayed). The scratch database is dropped unless `--keep`. `PG_BIN` selects the client tools.

Validation: **238 backend tests passed with PostgreSQL 16** (4 new in `test_backup.py`, each on its own source database: two rooms restored and verified with the same digests/chain heads and the scratch DB dropped; append-only triggers survive restore; a trigger-bypassing tampered command fails the check; a manifest that disagrees with the archive fails, and an old-rules room is `incompatible`). Disabling the manifest comparison and the divergence error made 2 of the 4 fail. Ruff and mypy (22 modules) passed. Godot (unchanged code) on this machine: import OK, **79 checks, 0 failures**, headless boot clean. Running the CLI against the shared test database correctly failed on the room `test_store.py` deliberately tampers with.

CI now installs `postgresql-client-17` from the PostgreSQL apt repository, sets `PG_BIN` and `FUNDFORGE_REQUIRE_PG_DUMP=1`, so these tests fail rather than skip there; locally they skip when `pg_dump` is missing or older than the server. Not yet done: a nightly schedule (needs the P2 deploy compose/VM, which needs owner authorization to deploy) and off-host storage of archives. Archives contain seat-token hashes; treat them as secrets.

**One next task:** P2 abuse limits in the API: request body size cap, per-IP room-creation rate limit, and a bounded room TTL, each with tests.

## LP confidence rules in the pure domain (P4), 11 October 2026

Taken instead of the API abuse-limits task because a second builder session on this branch had already claimed that task (its commit `6c77b3c` also landed the backup slice this session had duplicated; this session's copy was discarded unpushed). New stdlib/Decimal `backend/src/fundforge/lp.py` implements GAME_SYSTEMS §4 exactly as written, policy `lp-confidence-2026.10.1`: half-open bands (strong/stable/concerned/withdrawal_risk); chapter-close components (performance `clip(2 × (return − target), −6, +6)` with Seed 0.35/Patient 0.20/Tactical 0.60 pp targets, −6 per avoidable breach, +1 certified / −5 missing report, gate deferral −10/−8/−15, −15 per overdue payment, clamp to 0–100), each returned with the policy version; meeting recovery of at most 3 only after a documented concern, never above the confidence immediately before that concern, once per evidence identity; and notice-cutoff requests (days 15/35/55: 50% of units below 40, 25% from 40 to below 55, rounded down to 8dp; larger of that and an external need, capped by held units; lock-ups make Seed's first notice day 35 and Patient's day 55).

Validation: **252 backend tests passed with PostgreSQL** (14 new in `test_lp.py`). Removing the evidence-reuse check or the concern ceiling makes 1 and 2 of them fail respectively. Ruff and mypy (23 modules) passed. No rules version bump: nothing in the engine, tapes or goldens uses the module yet. No Godot or client change.

Limitations and interpretations: not wired into any scenario (Case1's contract replaces confidence-generated requests). "Documented concern" is modeled as any chapter-close fall in confidence; the meeting cap is applied after the chapter's other components. Seed's dollar-denominated $3m need must be converted to units at dealing by the caller. Herding after gates, preference terms beyond the rulebook and series statements are not specified numerically in GAME_SYSTEMS, so they are not invented here.

**One next task:** pro-rata gate allocation (20% of pre-flow post-fee NAV across eligible and carried requests, undealt units roll forward) in the pure domain with tests, so LP requests from `lp.py` have a deterministic dealing path.

## Pro-rata redemption gate allocation (P4), 11 October 2026

Completed the prior next task. `lp.allocate_gate(nav, requests, unit_price, gated)` splits each LP's requested units (new plus carried) into dealt and carried-forward units. With a gate elected, dealt value is at most 20% of the supplied pre-flow, post-fee NAV, using one common fraction of each request's value so no LP is preferred; units round down to 8dp, so rounding only leaves value undealt. Without a gate, or when requests fit under the cap, everything is dealt.

Validation: **254 backend tests passed with PostgreSQL** (2 new in `test_lp.py`: exact per-LP dealt units, dealt + carried = requested, dealt value ≤ cap and within 1e-7 of it, equal fractions; ungated/small/zero/invalid-NAV cases). Ignoring the `gated` flag makes the allocation test fail. Ruff and mypy (23 modules) passed. Not wired into the engine; Case1 has no gate election, so no rules bump.

Limitations: the caller supplies NAV and per-series unit prices (from the administrator strike) and the two-partner gate election; the payable/fee per dealt unit still comes from `series.redeem`. Gate confidence penalty is applied via `ChapterFacts.gate_deferred` only when carried units are non-zero for that LP.

**One next task:** P4 research-as-skill pure domain: hidden discrete states with published priors, evidence cards with authored likelihood ratios, exact Decimal Bayes posterior and Brier scoring of thesis tickets, with tests.

## Research-as-skill pure domain (P4), 11 October 2026

Completed the prior next task. New `backend/src/fundforge/research.py`: a `Question` has published priors over discrete hidden states (positive, summing to exactly 1); a `Card` carries authored likelihoods P(evidence | state) and an `available_at` day. `posterior(question, cards, day)` is exact Bayes in `fractions.Fraction` (Decimal division would round), order-independent, uses only cards available by `day`, rejects double-counted cards, incomplete or out-of-range likelihoods and evidence impossible under every state. `shown()` renders 6dp HALF_EVEN Decimals for display; the fractions stay authoritative. `brier(forecast, true_state)` is the exact multi-state Brier score (0 perfect, 2 certain and wrong).

Validation: **259 backend tests passed with PostgreSQL** (5 new in `test_research.py`, including hand-derived 4/5 and 8/15 posteriors, all card permutations, future-card exclusion and Brier values). Dropping the `available_at` filter makes the future-evidence test fail. Ruff and mypy (24 modules) passed. No engine wiring, so no rules bump.

Limitations: not connected to the existing role research assignments, thesis tickets or the debrief; no authored question/card fixture yet; the hidden true state must come from the scenario tape/generator and stay server-side until the debrief.

**One next task:** author a Case1 research question fixture (priors, two cards per role keyed to existing assignment findings) and surface per-role exact posteriors in the role-filtered view, with leak tests showing the other role's unshared cards never move a partner's posterior.
