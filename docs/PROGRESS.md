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

**One next task:** (superseded below) author a research question fixture and surface per-role posteriors. Not done in Case1: its contract says reveals disclose no future price and the case ends before BRIN's refinancing resolves, so a hidden true state there would be invented content. It belongs to the authored v1 campaign scenario.

## Secondary web desk: no duplicate commands (P2), 11 October 2026

Fixes the ROADMAP defect "the frontend sent duplicate orders on double-click". `frontend/app/exclusive.ts` is a single-flight guard on a ref, so a second click in the same tick is dropped before React re-renders. The desk's `send` runs every command through it and sets `busy`, which disables the action, partner and orders controls through `<fieldset class="contents" disabled>` (no layout change) until the request and refresh finish. Each accepted submission therefore sends one order id and one idempotency key. `npm test` (Node `node:test` with type stripping) is new and runs in CI.

Validation: `npm test` **2 passed** (removing the in-flight check makes one fail); `npx tsc --noEmit`, `npm run build` and `npm audit --omit=dev --audit-level=high` (0 vulnerabilities) passed with Node 22.22. `allowImportingTsExtensions` was enabled for the `.ts` test import (`noEmit` was already set). No browser double-click run was recorded; backend and Godot unchanged.

Limitations: `View = any` and openapi-typescript types, the `{code, message}` error envelope and the Playwright two-browser run remain open P2 items.

**One next task:** P2 API v1 slice: `{code, message}` error envelope for rejected commands, with the stored outcome returned for a reused rejected key, and tests. Coordinate with the parallel session's abuse-limits work in `api.py` (fetch before starting).

## API error envelope and stored rejected keys (P2), 11 October 2026

Completed the prior next task. Every HTTP error now returns `{code, message, detail}` (`detail` mirrors `message` so the existing Godot and web clients keep working). Codes: `unauthorized`, `not_found`, `conflict`, `rejected` (a valid command the rules refused), `invalid_command` (malformed), `key_reused`, `room_incompatible`. Clients can branch on `code` rather than wording. Engine rejections still carry one generic `rejected` code; per-rule codes would need the 56 `CommandRejected` raise sites typed.

Migration `0006_rejected_keys.sql` adds append-only `rejected_commands`. `Store.apply` records a rejected command's key, user, command, message and room version after its own transaction rolls back. A retry with the same key and command returns the same rejection even after state changes that would now let it succeed; a different command under that key is `key_reused`. Rejections are outside the replayed log and change no economics, so `verify`, goldens and rules are unchanged (no `RULES_VERSION` bump). The clock's stale ticks are not recorded.

Validation: **260 backend tests passed with PostgreSQL** (new `test_rejected_key_keeps_its_outcome_after_state_changes` and envelope assertions in `test_api.py`). Skipping the rejection insert makes the store test fail. Ruff and mypy (24 modules) passed. Godot 4.7.2 (SHA512-checked official build): editor import exit 0, **79 checks, 0 failures**, headless boot with no errors. No HTTP smoke against a long-running server and no Next.js change in this slice.

Limitations: malformed commands (`invalid_command`) are not bound to their key; FastAPI request-validation errors keep their default list-shaped `detail`; ETag/304, ledger cursor and Pydantic command unions remain open API v1 items.

**One next task:** P2 API v1: `ETag: <room version>` on `/view` with `If-None-Match` returning 304, and a ledger cursor (`after_seq`), with tests; then update the Godot/web pollers to use them.

## View ETag/304 and ledger cursor (P2), 11 October 2026

Completed the prior next task. `GET /view` returns `ETag: "<process epoch>-v<room version>-<running>"` and `Cache-Control: private, no-cache`; a matching `If-None-Match` gets an empty 304 after authentication and one cheap `rooms` query (no replay or view build). The per-process epoch makes the first poll after a server restart take the full path, so a room made incompatible by new rules/tape still answers 409 `room_incompatible` instead of a stale 304 (a test drops the epoch and fails). `next_tick_in` stays correct because both clients measure it from when the full view arrived and keep that time on a 304. `GET /ledger?after=N` returns the entries following the first N (up to 1,000) plus `next`; without `after` it still returns the newest 1,000, now with `next`.

Clients: Godot `Api` sends `If-None-Match` from the last view's ETag (reset on join) and keeps the view on 304 (`WorldRules.header_value`, 2 new checks). The web desk polls through `fetchView` and shows the envelope's `message`.

Validation: **260 backend tests passed with PostgreSQL** (ETag/304/version-change/auth-first and ledger-cursor assertions in `test_api.py`; restart-epoch incompatibility in `test_terminal.py`; two test doubles updated for `clock_info`'s new `version`). Ruff and mypy (24 modules) passed. Godot: **81 checks, 0 failures**, headless boot clean. Frontend: `tsc`, `npm test` 2 passed, `npm run build` passed. Real HTTP through the Next.js rewrite proxy (API on 8000, `next start` on 3011, both stopped afterwards): first view `ETag "v0-0"` (before the epoch was added), unchanged poll 304, after a `ready` 200, and a rejected command returned `{code: "rejected", message, detail}`.

Limitations: with several API processes each has its own epoch, so polls alternating between processes mostly get 200; acceptable for the single-process deployment target. The Godot HUD journal and web ledger tab do not use the cursor yet.

**One next task:** P2 abuse limits (body size cap, per-IP room-creation limit, room TTL, bounded cache) if the parallel session has not landed them; otherwise P2 observability: JSON logs with request/room/seq/command type and Prometheus `command_seconds`, `replay_seconds`, `rejections_total{code}`.

## Abuse limits and seat token in the fragment (P2), 11 October 2026

The parallel session had not landed this task after about 25 minutes of silence, so this session took it (fetched before pushing; no conflict).

- **Body cap:** ASGI `BodyLimit` refuses bodies over `FUNDFORGE_MAX_BODY_BYTES` (64 KiB) with 413 `body_too_large`, whether declared by Content-Length or streamed chunked. It buffers at most the limit before the app runs, because FastAPI turns errors raised mid-parse into a generic 400 (first attempt, found by the test).
- **Room creation:** an in-memory sliding one-hour window per client address (`FUNDFORGE_ROOMS_PER_IP`, default 20) returns 429 `rate_limited`. Idle addresses are forgotten so the table stays bounded.
- **Room TTL:** `FUNDFORGE_ROOM_TTL_HOURS` (default 72) after creation a room becomes read-only. Commands get 410 `room_expired` (checked inside the locked command transaction); view, ledger, debrief and verify still work; the clock skips and parks it. The append-only log is never deleted, so the TTL bounds work, not storage.
- **Bounded cache:** already in place (`CACHE_ROOMS = 256` LRU).
- **Seat token:** web seat links are now `/room/<id>#t=<token>`. The fragment never reaches servers, proxies or Referer headers; old `?t=` links still work and both are stripped from the address bar after loading (`frontend/app/seat.ts`).

Validation: **262 backend tests passed with PostgreSQL** (new `test_abuse_limits_body_size_room_rate_and_ttl` covering declared and chunked 413, 201/201/429, 410 while view/verify still work and the clock skips the room; plus `test_rate_limit_window_slides_and_forgets_idle_clients`). Ruff and mypy (24 modules) passed. Frontend `tsc`, `npm test` **3 passed**, `npm run build` passed. Godot code unchanged in this slice.

Limitations: the rate limit is per process and uses the socket peer address. Behind the planned Caddy proxy, uvicorn must run with `--proxy-headers --forwarded-allow-ips=<proxy>`, or every client shares the proxy's address. There is no storage reclamation for expired rooms.

**One next task:** P2 observability: JSON request logs with request id, room, seq and command type, plus Prometheus `command_seconds`, `replay_seconds` and `rejections_total{code}` on `/metrics` (via `prometheus-client`, a free dependency), with tests.

## Observability: Prometheus metrics and JSON logs (P2), 11 October 2026

Completed the prior next task. New `fundforge/observability.py` adds three metrics:

- `fundforge_command_seconds{type}`: each `Store.apply`, including bot replies.
- `fundforge_replay_seconds`: each session rebuild from the command log.
- `fundforge_rejections_total{code}`: every HTTP error envelope.

Command-type labels are limited to the command registry plus `tick`; anything else is `unknown`, so clients cannot create new series. The API exposes them on `GET /metrics`, which is unauthenticated and must stay off the public proxy.

Every `fundforge.*` logger writes one JSON line to stderr (`FUNDFORGE_JSON_LOGS=0` disables). Each request gets a request id, taken from a valid `X-Request-ID` (≤64 characters of `[A-Za-z0-9._-]`) or generated, and echoed in the response. Access lines carry method, path, status, ms and room. Applied commands log room, seq and command type with the same request id. Paths only: seat tokens are headers and never logged (asserted).

Dependency: `prometheus-client` 0.26.0 (wheel metadata: Apache-2.0 AND BSD-2-Clause), recorded in LIBRARY_RESEARCH; `uv.lock` updated.

Validation: **263 backend tests passed with PostgreSQL** (new `test_metrics_and_json_request_logs`). Ruff and mypy (25 modules) passed. Real uvicorn run on port 8012 (stopped afterwards) printed JSON access lines with the supplied `smoke-1` request id and served `/metrics`. A bug caught before testing: the body-limit middleware built its 413 response eagerly, which would have counted a rejection on every request; it is now lazy.

Limitations: the roadmap's Grafana JSON is not written (it can't be checked here without Grafana). Metrics are per process.

**One next task:** P2 hygiene: a test rejecting real-listed tickers in fixtures needs a ticker rename, which changes tapes and goldens (rules bump). Ask the owner before renaming ALTO/BEAM/BOND/ELAN/JUNO. Meanwhile take P4 market generator: `generate(seed, gen_version, skeleton)` with a SHA-256-counter PRNG and Decimal-only shocks in the pure domain, with determinism tests.

## Seeded market generator (P4), 11 October 2026

New pure `backend/src/fundforge/generator.py`: `generate(seed, gen_version, skeleton, spec) -> raw`.

- **Randomness:** SHA-256 counter stream over `gen_version|seed|n`, turned into integers by rejection sampling (no modulo bias, no floats).
- **Shocks:** each unauthored `PUBLIC_MARK` gets a whole-basis-point market factor scaled by the regime and each instrument's beta (default 1; BOND 0 per the scenario house sensitivities), plus an idiosyncratic shock. Prices step by exact Decimal multiplication, quantized once to 6dp HALF_EVEN.
- **Regime:** a two-state calm/stressed chain; stressed multiplies the factor bound.
- **Authored inputs:** the skeleton's overrides (Case1's day-16 shock, volumes, headlines) are never changed; later days continue from the authored levels.
- **Bounds:** `Spec` rejects bounds that could take a price to zero in one step.
- **Seed secrecy:** the output records only `seed_commitment = sha256(seed)` plus the regime path, so the debrief can reveal the seed for verification.

Validation: **271 backend tests passed with PostgreSQL** (8 new in `test_generator.py`): same seed gives the same tape digest, while seed or version changes it; authored marks match exactly after compile; the seed never appears in the output; BOND stays at 100 with beta 0 and no noise; all marks are 6dp positive strings; 5,000 draws on [-2, 2] land within 900–1,100 per value; three generated tapes play through the Engine to a valid outcome and replay to identical journal digests; regime switching alternates at `switch_bp=10000`. Ruff and mypy (26 modules) passed.

Limitations: not yet exposed as a scenario. Rooms still choose authored variants. Acceptance through the balance runner (`test_balance.py` policy grid) is not wired; that gate decides whether a generated tape is fair and must pass before any room uses one. Generated marks live in `tape.raw`, which the server already treats as hidden.

**One next task:** gate generated tapes with the balance policy grid (`tests/policy_grid.py` → a reusable `fundforge` function), then offer `case1-generated` rooms whose seed is stored server-side and revealed with its commitment in the debrief. Separately, ask the owner before renaming real-listed tickers (ALTO/BEAM/BOND/ELAN/JUNO).

## Balance gate for generated tapes (P4), 11 October 2026

The knowledge-free policy grid moved from `tests/policy_grid.py` into `fundforge/balance.py` (with `cure_qty`), unchanged in behavior. `tests/policy_grid.py` is now a thin wrapper and `test_balance.py` is untouched. New `balance.accept(tape) -> (ok, report)` checks a single world: flattening on day 12 must be refused (same journal as passive), passive must not win, and all three recall-handling lines must win. Cross-world dominance stays a tape-family property in `test_balance.py`.

Validation: **274 backend tests passed with PostgreSQL** (3 new in `test_generated_balance.py`: authored base and rally pass; an authored crash to 60/140 is rejected with `*_does_not_win`; the gate is deterministic for a generated seed). Goldens unchanged (`test_golden.py` passes). Ruff and mypy (27 modules) passed.

Measured once with the default `Spec`: of seeds `probe-0` to `probe-5`, **3 accepted and 3 rejected**, all three for `cover_recall_only_does_not_win`. The default shock bounds are therefore harsh for the minimal recall-only line; the spec needs calibration, or seed retry, before generated rooms ship. This is one small sample, not a rate estimate.

**One next task:** `case1-generated` rooms. Draw a server-side seed, retry with a counter suffix until `accept` passes (bounded attempts, all logged), store the seed and commitment with the room (new migration, pinned like variants), reveal both in the debrief, and add a test that `verify` re-derives the generated tape from the stored seed.

## Generated-market rooms (P4), 11 October 2026

Completed the prior next task without a migration. New Store scenario `case1-generated`: room creation draws a 128-bit server-side base seed and tries `seed:<base>-<n>` for up to 12 attempts until `balance.accept` passes. Each attempt is logged with its seed commitment and gate result, never the seed. The accepted seed is stored in the room's existing hidden `variant` column, so the room pins the generated tape's digest and `verify` re-derives it from the seed; a generator change makes old generated rooms incompatible like any other tape change. The seed appears in no view or terminal snapshot before the end. The finished outcome's `variant` reveals `seed:<seed>`, which players can check against `tape.raw.generator.seed_commitment`. Godot's scenario dropdown offers "Generated market".

Validation: **276 backend tests passed with PostgreSQL**. New tests: an end-to-end generated room through the real gate (variant format, commitment, no seed in either role's view or terminal before the end, outcome reveals it, `verify` re-derives the same tape digest after clearing the cache); seed retry until acceptance, bounded failure after 12 rejections, and a bad seed variant rejected (gate mocked). Ruff and mypy (27 modules) passed. Godot: **81 checks, 0 failures** (the scenario-key check now includes `case1-generated`), headless boot clean.

Limitations: each gate attempt plays five full policies (about 1–2 s here), so room creation can take several seconds and fails after 12 rejected seeds. With the measured 3-of-6 acceptance, failing 12 in a row is unlikely, but that is not a measured rate. Generated rooms reuse Case1's research texts, notices and debrief, which describe the authored path. The secondary web desk does not offer the scenario.

**One next task:** calibrate the generator `Spec` (or add a calm-before-crisis regime) so the minimal `cover_recall_only` line wins more often. Measure acceptance over a fixed seed list in a test-time benchmark script, not as a claim, and record the numbers.

## Generator acceptance measurement, 11 October 2026

New `scripts/generator_acceptance.py` (run from `backend/`) measures gate acceptance over the fixed seeds `bench-0..bench-(N-1)` for three candidate specs. Measured once with N=20 (58 s):

| Spec | Bounds (factor / idio bp, stress ×) | Accepted | Failures |
|---|---|---|---|
| default | 150 / 100, ×3 | 7/20 | `cover_recall_only_does_not_win` ×13 |
| calmer | 100 / 75, ×2 | 10/20 | same ×10 |
| quiet | 60 / 50, ×2 | 11/20 | same ×9 |

Diagnosis on the quiet spec, seeds 0–5: 5 WIN; seed 2 ends SURVIVAL with day-16 EXEC_A forced margin sales (2,106 BEAM, 2,185 IONA). The recall-only policy sizes its cure at 2× the announced deficit, and on some generated pre-crisis paths the endogenous squeeze makes that insufficient. Lower volatility helps only modestly, so the rejections are mostly about cure sizing against the authored crisis, not raw volatility.

No spec was changed: whether the minimal recall-only line must win in every generated world, or the gate should require only that some recall-handling line wins, is a balance-design decision for the owner (GAME_SYSTEMS/ROADMAP). The current gate is conservative; with the default spec, 12 attempts make an all-reject room creation unlikely, though that is not a measured rate.

**One next task:** owner decision on the gate rule above. Meanwhile, P4 LP agents in play: compute `lp.chapter_close` facts from the engine at a chapter boundary (return per series, breaches, certification) in a pure adapter with tests, without changing Case1 economics.

## LP chapter facts from the engine (P4), 11 October 2026

New `backend/src/fundforge/investors.py`: `chapter_facts(engine, start_nav_per_unit, start_day)` derives `lp.ChapterFacts` per series still holding units, using only typed state:

- net return in percentage points from net per unit against the chapter's starting value;
- report certified when the combined control report is `checked`;
- overdue payments: unpaid-redemption incidents, counted only for series with a `redemption_dealt` notice in the window.

The docstring states three facts the engine cannot yet produce instead of guessing them: avoidable breaches are 0 (orders are refused pre-trade and passive breaches aren't typed), gate deferral is False (no gate election yet), and meeting evidence is None.

Validation: **278 backend tests passed with PostgreSQL** (2 new in `test_investors.py`: S1 facts match hand-computed returns, are certified with no overdue, and Seed's performance component caps at −6; the case1-settlement DISTRESS path gives Tactical one overdue redemption (−15) and Seed/Patient none). Ruff and mypy (28 modules) passed.

Not wired into the debrief or outcome: SCENARIO_CONTRACTS says LP concern transitions are recorded in cases, but it does not state Case1's opening confidences. Using the season-launch roster values (72/80/65) would be an invented assumption, so it waits for the owner or a contract update.

**One next task:** owner decisions recorded above (generator gate rule; Case1 opening LP confidences; renaming real-listed tickers). Without them, the next unblocked item is P3/P2 Godot ledger paging with the new `after` cursor in the HUD journal, with Godot checks.

## Godot journal paging with the ledger cursor, 11 October 2026

The HUD back-office journal now pages: `Api.ledger(entity, after)` passes the cursor, and `_show_ledger(entity, end)` shows 15 entries newest first, with the range and total, plus an "Older entries" button while earlier entries remain. The page arithmetic is the pure `WorldRules.ledger_page(end, size)`.

Validation: Godot **83 checks, 0 failures** (2 new page checks), headless boot clean. A headless Godot probe against a live local API (port 8000, stopped afterwards) fetched the newest page, then `after=0`, and matched the tail entry. That room had only its opening fund entry (total 1), so it is a minimal round trip, not a multi-page run. Backend unchanged in this slice.

**One next task:** owner decisions (generator gate rule; Case1 opening LP confidences; real-listed ticker rename). Otherwise: P2 Grafana dashboard JSON for the three metrics, validated by a test that every panel query names an exported metric.

## Grafana dashboard (P2), 11 October 2026

`deploy/grafana/fundforge.json`: four panels (command p95 latency by type, commands/s by type, replay p95, rejections/s by code) over a selectable Prometheus datasource. `test_dashboard.py` parses the dashboard and the live exposition and requires every panel's metric names and `by (...)` labels to exist; renaming one metric in the JSON makes it fail.

Validation: **279 backend tests passed with PostgreSQL**; Ruff and mypy (28 modules) passed. Not imported into a running Grafana (none available here), so rendering is unverified.

**One next task:** owner decisions (generator gate rule; Case1 opening LP confidences; real-listed ticker rename; deployment authorization for P2 deploy/CD). Without them: a P2 `deploy/compose.prod.yaml` draft (Caddy TLS, no published DB port, non-root containers, `.env` secrets), validated with `docker compose config` if Docker is available. It must not be deployed.
## HUD journal paging and production deploy stack (P2/P3), 11 October 2026

**Journal paging.** This replaces the parallel session's `ledger_page` paging above, whose journal still vanished when the panel re-rendered on the next view and downloaded up to 1,000 entries to show 15. The Godot back-office journal uses the `/ledger` `after` cursor. `WorldRules.ledger_path`, `merge_ledger` and `ledger_window` are pure: the first request takes the newest page, later ones fetch only entries after the cached `next`, a page that does not continue the cache replaces it, and the cache is capped at 1,000 entries. The HUD keeps the chosen journal open across view refreshes (it used to vanish on the next poll), refetches only when the room version changes, and pages with Newer/Older buttons that stay on the same entries while new ones arrive. Over real HTTP, a whole two-seat game fetched incrementally gave exactly the same fund (194) and firm (52) entries as one full fetch.

**Production stack.** New `deploy/compose.prod.yaml`, `Caddyfile`, `backup-loop.sh`, `.env.example` and `smoke.sh`:

- Caddy terminates TLS and routes `/api/*` to the API and the rest to the web desk. It returns 404 for `/metrics`, which is published only on host `127.0.0.1:9464` for a local scraper. Caddy runs as root to bind 80/443, with every capability dropped except `NET_BIND_SERVICE`.
- Postgres has no published port and sits on an `internal` network with no egress.
- The API (uid 10001, read-only root filesystem), web (uid 1000) and backup (uid 10001) containers run non-root with all capabilities dropped. The API image runs uvicorn from the venv, so `uv` isn't needed at runtime.
- Secrets come from `deploy/.env`; compose refuses to start without `POSTGRES_PASSWORD` and `FUNDFORGE_DOMAIN`.
- uvicorn trusts `X-Forwarded-For` only from Caddy's fixed address. Other containers are allocated from the upper half of the subnet so they can never take that address.
- New `GET /api/ready` applies migrations and pings the database, returning 503 `unavailable` otherwise. It is the API healthcheck; Caddy and backup wait for it.
- The `backup` service is built on `postgres:17-trixie`, so `pg_dump` always matches the server, with the API's Python runtime copied in. It dumps nightly at `BACKUP_AT` and restores into a scratch database with `fundforge.backup check`. An archive gets a `.verified` marker only after replay reproduces every digest and chain head; a failure leaves `.FAILED` and is never pruned.

Running it locally exposed four defects, all fixed before commit: Caddy's fixed IP taken by an earlier container, an invalid Caddyfile with an empty ACME email (removed), a root-owned backup volume, and the startup backup racing the API's lazy migrations (fixed with `/api/ready`). The dev `compose.yaml` now pins `target: api`.

Validation:
- **279 backend tests passed with PostgreSQL 16**, including the new readiness test; Ruff and mypy (27 files) passed.
- Godot 4.7.2 (SHA512-checked): import OK, **92 checks, 0 failures** (11 new ledger checks; the two `ledger_page` checks went with that helper), headless boot clean.
- Frontend `tsc`, `npm test` and `npm run build` passed (unchanged code).
- Real HTTP against a local API: `analysis_smoke.py` (standard and `--broker-challenge`, rules 2026.10.8), and a solo bot game with skip-ahead (6 rounds, verified).
- `terminal_smoke.py` was stale (it compared PM and MP snapshots, which now carry `role`); it is fixed and passes.
- `deploy/smoke.sh --no-build` passed from empty volumes. It checks TLS routing, web 200, HTTP→HTTPS redirect, public `/metrics` 404 with host `/metrics` served, no published DB port, non-root app processes, a two-seat game through Caddy to a verified journal, and a verified startup backup. Spoofed `X-Forwarded-For` was ignored both through Caddy and directly. A room survived a stack restart, and a backup containing it restored and verified.

Sandbox note: this container's proxy forbids ghcr.io blob downloads and `deb.debian.org`, so the local images were built from scratchpad copies of the Dockerfiles with the proxy CA added and a local stand-in for the `ghcr.io/astral-sh/uv` binary (uv 0.11.32; dependencies come from the frozen lockfile). The repository Dockerfiles are unchanged by that. The new CI `deploy` job builds them unmodified; its result is in CI after the push.

Limitations:
- Nothing is hosted, and a public deployment needs owner authorization.
- There is no GHCR publish/SSH CD workflow (it needs deploy secrets and a host) and no off-host backup copy.
- Caddy runs as root inside its container.
- The secondary web desk's journal does not use the cursor.

**One next task:** owner decisions still block three items (generator gate rule; Case1 opening LP confidences; renaming real-listed tickers). The next unblocked item is P2 API v1: openapi-typescript types generated from the FastAPI schema to replace `View = any` in the web desk, with a CI check that the generated file is current.

## Typed web desk from the API contract (P2 API v1), 11 October 2026

Completed the prior next task. New `backend/src/fundforge/schemas.py` describes the player-facing responses as strict Pydantic models (`extra="forbid"`, decimals stay strings):
- `SessionView` is what `Session.view` builds;
- `RoomView` adds the endpoint's `names` and `realtime`;
- `LedgerPage` and `NewRoomResponse` describe the ledger and room-creation responses.

The view endpoint still returns its own ETag `JSONResponse` and only documents `RoomView` in OpenAPI; ledger and room creation declare `response_model`, so FastAPI validates them on the way out.

`test_schemas.py` validates the JSON of every view both partners receive across whole games: Case1 base and rally, a busy script on Case1/controls/settlement, a generated seed, and solo bot games in both seats. The busy script covers research, sharing, chat with a ref, limit orders, a large purchase, a post-recall short refused at execution, and statement review. The test also asserts those paths actually reached the optional branches (filled and rejected fills, WIN and DISTRESS outcomes, margin calls, evidence, bots, chat refs, limits, attention claims, incidents). An extra field or a number where a decimal string belongs fails validation. Writing the contract found one real shape the sampling had missed: notice `refs` can hold integers (statement revisions).

`scripts/export_openapi.py` writes `frontend/openapi.json`, and `npm run types` (openapi-typescript 7.13.0, MIT, pinned devDependency) generates `frontend/app/api-types.ts`. `lib.ts` now exports `View = RoomView` and named aliases. The desk has no `any` left: fills are a `Fill | RejectedFill` union narrowed with `"rejected" in x`, and evidence refs and command `detail` (which echoes the sent command) are read explicitly. The debrief now describes `visit` and `share_research` decisions instead of printing their raw type; its old `research` case predated assignments.

Freshness: `test_openapi_file.py` fails while the committed JSON differs from the app (checked by editing it), and the frontend CI job regenerates the types and runs `git diff --exit-code`.

Validation:
- **284 backend tests passed with PostgreSQL**; Ruff and mypy (28 files) passed.
- Frontend `tsc`, `npm test` (3 passed), `npm run build` and `npm audit --omit=dev` (0 vulnerabilities) passed.
- A real Chromium run (Playwright 1.56.1 from a scratch directory, not a repo dependency) drove the production web desk against a local API through a full two-seat game. The MP shared evidence through the UI. The orders tab showed the filled cover, the broker's forced trades and "Rejected: no borrow inventory for BRIN". The ledger showed 346 rows with its hash, and the debrief listed the six decisions in words. There were no console errors.
- Godot is unchanged in this slice.

Limitations:
- Request bodies are still untyped: commands are `dict`, so the desk's `send` takes `Record<string, unknown>`.
- The terminal, debrief, liquidity and verify responses remain `dict[str, Any]`, because only the web desk's endpoints were contracted.
- The Godot client does not use the generated types.

**One next task:** P2 API v1 command contract: Pydantic discriminated-union command models in `schemas.py` for `POST /commands` (validated before `Session.handle`, with malformed bodies returning `invalid_command`), regenerate the types, and type the web desk's `send`.

## Command contract at the API boundary (P2 API v1), 12 October 2026

Completed the prior next task. `schemas.py` now also defines every player command as a strict model in one discriminated union on `type`: `Ticket`, `Propose`, `Sign`, `Cancel`, `ResearchCommand` (legacy), `Visit`, `ShareResearch`, `AcceptReplacement`, `SetReserve`, `ResolveStatement`, `Ready`, `SetSpeed`, `Say` and `Pause`. `tick` is excluded because only the server clock issues it.

`POST /commands` validates the body as `CommandBody` before the store or engine runs. It wraps the union in a `RootModel` because FastAPI's `Body()` dropped the discriminator, and that run reported every malformed command as `order_id: Field required`. The models check shapes only: roles, limits, deadlines and the mandate stay with the versioned rules.
- Decimal inputs (`limit`, `amount`) must be plain decimal strings, never JSON numbers.
- Integers accept whole JSON numbers, because Godot parses every number as a float. The log stores the validated dump, so a Godot `1250.0` and a web `1250` are the same command and the same idempotency fingerprint.

**Defects fixed (reproduced first over HTTP):**
- `set_reserve` with amount `"lots"` and a ticket with limit `"abc"` returned **500** (`decimal.InvalidOperation` escaped the handler).
- A package with limit `"1e"` was **accepted**, binding an unusable price into an approval digest and the command log until the partner signed.
- `say` accepted an object as text.

All of these now return 422 `invalid_command` and change nothing.

**Request validation:** errors on every route now use the `{code, message, detail}` envelope (`invalid_command` on commands, `invalid_request` elsewhere) instead of FastAPI's list. Messages name the field and say what to do, for example `orders.0.limit: must be a plain decimal number sent as a string, such as "95.25"`, `unknown command type 'tick'`, or `command type required`. Authentication is still checked first.

**Web desk:** `send` takes the generated `Command` type, and `SIDES` is typed `Side[]`. The Ready button now sends `version`; before, the web desk's Ready was not bound to the state the player saw. In Chromium, a partner whose page was stale was refused ("the plan changed since you looked"), and the same click after the page refreshed advanced the game and filled the ticket. Types are generated with `--default-non-nullable false`, so fields with server defaults (`skip`) are optional in requests.

**Tests:**
- The union's tags must equal `governance.COMMANDS` minus `tick`, so a new command cannot ship untyped.
- Every command logged in solo bot games (both seats) and the busy Case1/controls scripts validates. That test caught one wrong guess: the bot's chat `ref` is a string such as `"research:borrow"`, not an object.
- Client shapes, including Godot floats, validate and normalise; ten malformed shapes are refused.
- An HTTP test covers the reproduced defects, the exact messages, 401 before body validation, an unchanged room version, and the same key resubmitted with `1250.0` and `1250` returning the same result.
- The metrics test now asserts the unknown type is refused at the boundary (`invalid_command`) and never becomes a label.

**Validation:**
- **288 backend tests passed with PostgreSQL**; Ruff and mypy (28 files) passed.
- Frontend `tsc`, `npm test` (3 passed) and `npm run build` passed.
- Godot: **0 failures**, boot clean (client code unchanged).
- On the final code, against a live API: `analysis_smoke.py` (standard and broker challenge), `terminal_smoke.py`, and two Chromium runs of the production web desk. One drove the full game; the other sent a ticket with a malformed and then a valid limit, plus both partners' Ready, through the UI. There were no console errors.

**Limitations:**
- The terminal, debrief, liquidity and verify responses are still untyped.
- The Godot client doesn't use the generated types; its command shapes are covered by the tests above.
- The view's chat `ref` stays `Any`, because rooms recorded before this change may hold other shapes.

**One next task:** P2 hygiene that needs no owner decision: an MIT `LICENSE` is listed in the roadmap, but adding a license is the owner's legal call, so ask first. Without that, the next unblocked engineering item is P3 live presence: an authenticated FastAPI WebSocket for partner avatar positions, with polling fallback and a test proving presence traffic never changes the journal digest.

## Live partner presence (P3), 12 October 2026

The partner's avatar now moves live instead of jumping to the place of their last decision. New stdlib-only `backend/src/fundforge/presence.py` and `WS /api/rooms/{id}/presence`.

**Protocol:** the first frame is `{"type": "hello", "token"}`, sent within 5 s. Tokens never go in URLs, which get logged. Wrong token, wrong room, a malformed hello or silence closes with `4401`; a fifth socket for one seat closes with `4429`.

After that, `move` frames `{x, z, location}` are validated:
- finite numbers (Python's `json` accepts `NaN`/`Infinity`, so those are checked explicitly), not booleans;
- inside the 24×23 world and a known location;
- under 1 KB, rounded to centimetres;
- rate-limited by a token bucket (10/s, burst 20).

A bad frame gets an `error` frame, and the socket stays open.

**Relay:** the hub relays `presence` to the other seat, gives a late joiner the partner's last position in `welcome`, and sends `left` when a seat's last socket closes. After each successful command and each clock tick it sends `version` nudges, and clients poll `/view` at once.

**Bounds:** outbound queues are bounded (64; a slow reader loses presence frames, never the session), and empty rooms are forgotten.

**Separation from the game:** positions are cosmetic. They are never logged or replayed, and nothing in the engine reads them; research assignments stay `visit` commands checked by the rules. `Store.seat_role` adds a single indexed lookup for authentication.

**Godot client:** `Api` runs a `WebSocketPeer`:
- `ws(s)://` comes from the server URL;
- the hello is sent on open;
- moves are sent at most every 0.15 s and only after a 5 cm step;
- reconnects back off 1/2/4/8/15 s.

Polling continues regardless, so with no socket the game runs exactly as before. The office makes the partner avatar follow live positions while frames arrive, and returns to last-decision placement when they stop or the socket drops.

The hub is per process. That fits the single-process deployment target; several API processes would need a shared broker, which isn't built.

**Validation:**
- **295 backend tests passed with PostgreSQL**; Ruff and mypy (29 files) passed.
- `test_presence.py` (7 tests) covers:
  - frame validation, the token bucket, hub relay, cleanup and bounds;
  - over a real WebSocket: four bad-auth cases, the hello timeout, relay, an error frame without disconnect, the late-joiner welcome, a `version` nudge after an HTTP command, and `left`;
  - 200 moves leaving the room version, journal digest and chain head unchanged;
  - a check that the server's world bounds and locations match `game/scripts/world_rules.gd` (changing the Godot world size makes it fail).
- Mutation checks: relaying to self, dropping the command nudge, dropping `left`, sending `left` while another tab remains, removing bounds, and removing the hello deadline each made tests fail within about 7 s.
- Every receive has a 5 s deadline, and a fixture closes sockets even when a test fails, so a regression fails instead of hanging CI. The first version of the tests hung until killed; that's how this was found.
- Godot: **101 checks, 0 failures** (9 new: URLs, frames, throttling, backoff, frame handling), and headless boot is clean.
- Live run: a headless Godot client joined as PM against a local API and walked to the risk room. A Python client in the MP seat received the welcome, 30 throttled `presence` frames from (6.0, 7.0) to (19.5, 6.0, `risk`), and `left` when Godot quit. The room then verified at version 0.
- `deploy/smoke.sh` now also requires `101 Switching Protocols` for the presence socket through Caddy, and passed on freshly built images. Through the same stack, a full `wss://` exchange over Caddy's TLS authenticated both seats, relayed a move, and closed a forged token with 4401.

**Limitations:**
- No recorded two-client graphical run; the partner's motion was not visually captured.
- Godot's receive direction is covered by the unit-tested handler, not observed on screen.
- The secondary web desk does not use presence; its Next.js dev proxy does not carry WebSockets, though production Caddy does.

**One next task:** the owner decisions are still open: the MIT `LICENSE` (a legal choice, so ask), the generator gate rule, Case1's opening LP confidences, the ticker rename, and deployment authorization. The next unblocked item is P3 audio: CC0 sound effects for typed engine events (fill, margin call, recall, halt) with provenance in `game/CREDITS.md` and a mute setting, checked headlessly by event-to-sound mapping tests.

## Sound effects (P3 audio), 12 October 2026

New `game/scripts/sfx.gd`. Nine cues are synthesized at runtime into 16-bit 22.05 kHz `AudioStreamWAV`s from sine and square tones plus fixed-seed LCG noise, with a 5 ms attack and 10 ms release so nothing clicks: alarm, crash, rally, bell, halt, chime, cash, rival and fill. There are no audio files, downloads or licences; provenance is recorded in `game/CREDITS.md`.

- **Triggers:** existing world effects map to cues (margin call → alarm, market shock → crash, rally → rally, recall and LP letters → bell, halt → halt, research → chime, redemption → cash, rival distress → rival). At most three distinct cues play per batch of notices, and a soft tick plays when new non-rejected fills appear on our orders.
- **Joining:** the first view after joining plays nothing, so entering a room doesn't replay its history.
- **Mute:** a HUD "Sound on/off [M]" button and the `M` key, persisted in `user://settings.cfg`.
- **Logic:** none. Sounds follow typed notices and fills and drive nothing.

**Validation:**
- Godot: **141 checks, 0 failures** (40 new), and headless boot is clean. The checks cover:
  - every cue is audible, within 16-bit range and click-free at the start;
  - synthesis is deterministic, and an unknown cue is silent;
  - every mapped effect points to a real cue;
  - batches are deduplicated and capped;
  - the fill count ignores rejected fills.
- Live: a headless Godot client stayed joined through a full solo game against a local API (SURVIVAL, 11 notices, 3 fills, 69 view polls) with no script errors in the HUD or sound paths. Headless audio is a dummy driver, so audible output was checked separately: each cue was rendered to WAV from the same synthesis code and shared with the owner.
- Backend unchanged.

**Owner question (12 Oct):** can Spotify play in the app? Players can already run Spotify alongside the game; the OS mixes it, and the game's effects can be muted. Playing Spotify *inside* the Godot client isn't practical: Spotify's playback SDK runs in web browsers and needs Premium. What is feasible is remote-controlling the player's own Spotify app through the Web API, which needs a registered app, per-player OAuth, server-side secrets, a review of Spotify's developer terms, and the owner's authorization under CLAUDE.md's external-service rule. Not built. An original in-game soundtrack generated like the effects is the dependency-free alternative.

**One next task:** the owner's choice on music (generated soundtrack, Spotify remote control, or none), plus the earlier open decisions (license, generator gate, Case1 LP confidences, ticker rename, deployment). The next unblocked item is P3 exported builds: Godot export presets for Linux/Windows/web built in CI as workflow artifacts (not releases, which publish), with a headless boot of the Linux export.

## Desktop builds in CI (P3), 12 October 2026

New `scripts/export_game.sh GODOT TEMPLATES.tpz [OUT_DIR]`:
- checks the official `Godot_v4.7.2-stable_export_templates.tpz` (1.28 GB) against the release's published SHA-512 before extracting anything;
- installs only the Linux and Windows release templates;
- exports the existing presets to self-contained `FundForge.x86_64` and `FundForge.exe` (the presets embed the `.pck`);
- boots the **exported** Linux binary headless, failing on any script, parse or load error.

New CI job `export`: the templates are cached, the export and boot run on every push and pull request, and the binaries (about 290 MB per run) upload as artifacts only on a manual `workflow_dispatch`, with 3-day retention. That avoids a storage quota the owner hasn't approved. `.gitignore` now covers export output and the templates file.

**Validation (local, sandbox):**
- The templates' checksum verified.
- Both exports succeeded: Linux 127 MB, Windows 163 MB.
- The exported Linux build booted with no errors.
- The exported Linux binary, not the editor, joined a live local API and stayed connected through a full solo game: SURVIVAL, 11 notices, 3 fills, 70 view polls, 0 errors.
- My first run of the script wrongly required separate `.pck` files; fixed after reading the presets.
- The CI job's first real run is the push of this commit.

**Limitations:**
- The builds are unsigned test builds, not releases (publishing waits for the owner).
- There's no macOS build (it needs signing and notarization) and no web build (it needs the Compatibility renderer, and the office uses Forward+ effects).
- The Windows build was exported but not run; there's no Windows runner here.

**One next task:** the owner decisions are unchanged (music, license, generator gate, Case1 LP confidences, ticker rename, deployment). The next unblocked item is P3 acceptance: a scripted two-client run where both partners split across two simultaneous crises (broker recall and LP redemption) and then meet to present a package. Drive two headless Godot clients plus presence, assert both sets of assignments and the joint package through the API, and record the log as evidence.

## Co-op acceptance: split across two crises, then meet (P3), 12 October 2026

New `scripts/coop_acceptance.py`. Two real headless Godot clients join one room. The PM walks to the research library (the BRIN demand survey) and the MP crosses the street to the prime broker (the recall borrow); at 14 s both walk to the committee room. Each seat has an extra presence socket that observes the other avatar's actual position, so the evidence comes from the clients, not from the script's intentions.

**Assertions:**
1. The partners stand in different crisis locations at the same moment.
2. Both `visit` assignments are accepted and recorded in the same decision window.
3. Both reach the committee room; the PM proposes the BRIN cover package and the MP countersigns it (`AUTHORIZED_QUEUED`).
4. The room verifies at exactly version 4.
5. Neither client printed a script or engine error.

It writes a JSON evidence log (room, routes, timings, assignment window, package digest, verify heads, and the observed location timeline; no seat tokens).

**Client change:** `--goto` now accepts a timed route such as `research@1,committee@14`, parsed by `WorldRules.parse_route`; plain `--goto=risk` still works. The script keeps HTTP off its event loop so the observers' sockets stay serviced.

**CI:** the `export` job now starts Postgres and the API and runs the acceptance with the **exported** Linux build it just produced, then uploads the small evidence log.

**Validation:**
- Passed locally with editor clients (split at 10.1 s, met at 21.8 s) and with exported clients (split at 9.5 s, met at 21.2 s).
- The observed timeline is physically plausible: the MP walks risk → LP lounge → back office → broker; the PM walks trading → research.
- Negative check: a scratch copy where the MP follows the PM to research fails with "timed out after 25 s waiting for the partners to split up", for both client kinds.
- No client processes were left behind.
- Godot: **144 checks, 0 failures** (3 new route checks).

**Limitations:**
- Headless, so no video or GIF was recorded.
- It is scripted movement, not a human playtest.
- It uses Godot clients rather than the roadmap's browser contexts, because the Godot client is the primary player surface.

**One next task:** the owner decisions are unchanged. The next unblocked item is P2 Playwright end-to-end for the secondary web desk: two browser contexts play S2 to a WIN with axe accessibility checks, committed as a test (Playwright as a dev dependency), run in CI.

## Browser end-to-end: two partners play S2 to a Win, with axe (P2), 12 October 2026

New `frontend/e2e/s2.spec.ts` (Playwright 1.56.1 and `@axe-core/playwright` 4.13.0, pinned dev dependencies; the axe release was chosen because it had been out for two months). Two browser contexts open their seat links and play the designed S2 line entirely through the web desk:
- **Day 12:** the MP assigns the borrow research.
- **Day 14:** the MP accepts the replacement borrow.
- **Day 16:** if a margin call is announced, the PM proposes an ALTO sale sized like the designed line (5× the deficit at the fixture's stressed maintenance rate) and the MP signs it.
- **Day 18:** the PM proposes selling 20,000 BEAM and the MP signs.

Both then mark Ready to the end. The test reads the API only to know the clock.

**Assertions:** the outcome is WIN with the recall resolved by replacement borrow, both debriefs show "Win", and axe finds no serious or critical WCAG 2 A/AA violations on either desk at the start or either debrief at the end. Ready is version-bound, so a page that hasn't polled since its partner acted is refused as stale; the helper waits a poll interval and clicks again, as a player would.

**Accessibility fixes (found by the test):**
- Amber text when headroom is tight was 3.16:1 on the light background. New `--amber-text` `#875510` measures 5.34:1 and is also used for the Survival verdict; dark mode is unchanged at 7.82:1.
- The scrolling desk feed and season calendar were not keyboard-scrollable; both now take focus and have a label.

**Dependency note:** npm had auto-installed axe's `playwright-core` peer at the newest 1.64.0, a second, unpinned Playwright with incompatible types. An `overrides` entry pins it to 1.56.1. Licences are recorded in LIBRARY_RESEARCH; axe is MPL-2.0 and dev-only.

**CI:** new `e2e` job with Postgres, the API, a production `next build` and `next start`, and Chromium from `npx playwright install --with-deps`; it uploads the Playwright trace on failure.

**Validation:**
- Passed four times locally, all drawing the base market (a uniform random draw); the first run failed only on the two axe violations above.
- The rally path wasn't drawn. The test's decision logic was checked separately in the engine for both markets: base WIN with the cure, rally WIN without one (no margin call is announced there).
- Frontend `tsc`, `npm test` (3 passed), `npm audit --omit=dev` (0 vulnerabilities) and `npm run build` passed.

**Limitations:**
- The README GIF isn't recorded.
- The variant is random per room, so any one CI run covers one market.
- My local runner initially left a `next-server` holding the port (fixed with a process group); that affected only the local harness.

**One next task:** the owner decisions are unchanged (music, license, generator gate, Case1 LP confidences, ticker rename, deployment). The next unblocked items are a server-side test hook to pin a room's variant for deterministic end-to-end coverage of both markets (test-only, so it needs care not to leak the variant), or the web desk's journal using the ledger cursor.

**CI fix, 12 October 2026.** Two of three CI runs for `3cbd8f3` failed `e2e` and `export` even though their tests had **passed** (S2 WIN; co-op split, met and verified). The jobs then failed in `setup-uv`'s post-job cache prune, which waited 5 minutes on uv's cache lock and exited 2. The lock was held by the background API started with `uv run uvicorn`. The failure is intermittent because only the run that saves the uv cache prunes it. Reproduced locally: `uv cache prune --ci` blocks while a `uv run` process is alive and returns at once when the process is the venv's own Python. Fix: both jobs start the API (and the acceptance script) from `backend/.venv/bin`, and stop the background servers with an `EXIT` trap.

## Pinned market variant for end-to-end coverage (P2), 11 October 2026

Completed the prior next task. `POST /api/rooms` accepts an optional `variant`, honoured only when the API runs with `FUNDFORGE_TEST_VARIANTS=1` (`api.pinned_variant`). With the flag off, any requested variant is refused with 403 `variant_forbidden`, so a misconfigured test run fails instead of silently drawing a random market; rooms without a variant draw a hidden one as before. With the flag on, an unknown name returns 422 `invalid_request` instead of letting `TapeError` escape as a 500; generated rooms need `seed:<text>` (a pinned seed skips the balance gate, which is acceptable only for tests). Production compose does not set the flag. `store._variants` is now the public `scenario_variants`. The variant still never appears in a player view before the debrief.

`frontend/e2e/s2.spec.ts` now runs once per market, asserting the outcome's variant and that a margin call is announced only in `base`. The CI `e2e` job starts its API with the flag. `openapi.json` and `api-types.ts` were regenerated.

Validation: **292 backend tests passed, 4 skipped** (PostgreSQL 17 in Docker; the skips are `pg_dump` cases with no matching local client), including new `test_market_variant_is_pinned_only_when_the_test_flag_is_on`; making the flag check a no-op makes it fail. Ruff and mypy (29 files) passed. Frontend `tsc` and `npm test` (3) passed, `npm run build` passed. Playwright locally against a fresh API on 8021 and `next start` on 3011: **2 passed** (base WIN with the margin call cured, 1.8 min; rally WIN with none announced, 1.3 min). Godot unchanged. No commit or push.

Limitations: the flag is process-wide, so never run a shared or public server with it. The axe checks now run twice per CI job, adding about 1.5 minutes.

**One next task:** the owner decisions remain (license, generator gate rule, Case1 opening LP confidences, ticker rename, deployment, music). The next unblocked item is the web desk's journal using the ledger `after` cursor, as the Godot HUD already does.

## Local game launch and web journal continuation, 12 October 2026

The owner requested running the game first, then further implementation and fixes. The initial Windows graphical launch failed to resolve the new `Sfx` global class because local Godot import/class registration was stale. `godot_console --headless --path game --editor --import` refreshed it; the subsequent graphical game launched without script errors against the existing local API on port 8011.

New `scripts/run_game.ps1` imports the project, checks API health and launches with a configurable server. README now includes the import step and Windows launcher, and removes the nonexistent DEVELOPMENT.md link.

The web desk's Ledger uses `after=0` initially, drains full 1,000-entry pages, and refreshes from its cached cursor when the room version changes. It retains all fetched entries, removes the old 150-entry display cutoff, updates the digest even on empty pages, and ignores responses after effect cleanup. Room/token/entity changes reset the displayed journal; refresh failures retain old entries with an explicit message. Posting rows now have unambiguous keys.

Validation: Godot headless suite passed with 0 failures; graphical launch reported the RTX 4070 Vulkan renderer with no script errors. Live two-seat terminal smoke passed at day 16/version 18 with 12 quotes, 22 observations, 1,250 covered shares and verified books. Frontend TypeScript, 3 existing unit tests and production build passed. Launcher PowerShell syntax parsed successfully. Existing unrelated working-tree changes were preserved; no commit, push or deployment.

Limitations: no human playtest or new browser pagination integration test was performed; existing frontend unit tests do not exercise the journal component. The launcher requires Godot on PATH and warns if its API is unavailable. The default server is port 8000; this session used `-Server http://127.0.0.1:8011`.

**One next task:** browser integration coverage for journal pagination, incremental refresh, entity switching and delayed responses, including a journal exceeding 1,000 entries.

## Journal browser coverage and search, 12 October 2026

Continued from the owner's request to run the game and implement further work. The graphical game launched using the Windows import/health launcher. The previously running 8011 API rejected presence upgrades with HTTP 403; a fresh current-code API started with `uv run --project backend uvicorn fundforge.api:app --host 127.0.0.1 --port 8022` and the local PostgreSQL DATABASE_URL. The game was then launched against 8022. The old cached Python environment was missing prometheus-client; use the project's uv environment rather than that historical environment. Existing 8011 service was preserved.

`frontend/e2e/ledger.spec.ts` adds three browser integration tests: a 1,002-entry journal drained over two pages with incremental and empty-page digest refresh; a delayed fund response after switching to the management-company journal; and refresh failure retaining entries then retrying from the committed cursor. The actual desk renders a real initial room view while journal/view refresh responses are controlled, so these are UI contract tests rather than independent accounting tests. Development Strict Mode may initiate an extra cancelled initial GET; test assertions allow that while checking subsequent cursor use and visible entry counts.

The journal now searches loaded history by date, entry identity, memo and account, case-insensitively. It shows matching/total counts, loading and empty states, and exposes the selected entity through aria-pressed. Search does not fetch or change the authoritative journal. Browser coverage includes matching an entry beyond the first 1,000 records, no matches and uppercase account matching.

Validation: all 3 new Playwright tests passed against the local web desk; TypeScript and the 3 existing unit tests passed. Production build passed. Current-backend two-client Godot co-op acceptance passed: split at 8.49 seconds, met at 20.23 seconds, package AUTHORIZED_QUEUED, books verified at version 4. Evidence is outside the repo at `C:/Users/krish/.cache/fundforge-current-coop.json`. No human playtest, accounting rule changes, commit, push or deployment.

**One next task:** journal browser coverage for a failed second page and a version change during a multi-page refresh, proving retries neither lose nor duplicate entries.

## Journal retry and interrupted pagination, 12 October 2026

Completed the prior next task in `frontend/e2e/ledger.spec.ts`: one browser test fails the second page of a 1,002-entry journal, retries without changing the paused room version, and verifies every entry appears exactly once in reverse order. Another delays the second page, publishes a newer room view, then releases the obsolete response; all 1,003 newer entries and their digest remain intact. These extend the three existing journal browser tests.

Fixed a recovery gap in `frontend/app/room/[id]/desk.tsx`: errors previously retried only when the room version or selected entity changed. A paused room could therefore remain stuck. The new Retry journal button restarts loading from the last fully committed cursor without an economic command. Incomplete page sequences remain uncommitted; cancelled responses cannot replace newer history.

Validation: all 5 journal Playwright tests passed against the local web desk and API; TypeScript passed. Production build and 3 existing unit tests passed. No backend/game economic changes, commit, push or deployment. Browser journal data is controlled for fault injection; these tests do not certify external financial records.

**One next task:** bound journal DOM size for long histories while keeping search over all loaded entries and access to every matching entry; cover browsing and search in Playwright.

## Bounded journal window (P2 web desk), 12 October 2026

Completed the prior next task. Main first fast-forwarded to `73f3dc2` (the venv-launched CI servers that fix the red `e2e`/`export` jobs on `3cbd8f3`); the e2e API keeps `FUNDFORGE_TEST_VARIANTS=1`.

The web desk journal renders at most `JOURNAL_WINDOW` = 100 entries (newest first) instead of every loaded entry, about 2,000 rows at 1,002 entries. Newer/Older buttons move by whole windows. The last window is partial, so paging never repeats an entry. Search still filters all loaded entries, and its matches page the same way, with a "Showing a–b of n matching entries (m loaded)" status. Changing journal or search returns to the newest window. A reader on an older window keeps the same entries on screen when new ones arrive, because the window shifts by the number of new matches. The cursor fetching, retry and cancellation logic is unchanged.

Validation: Playwright **8 passed** against a fresh API on 8021 and `next start` on 3011. These are the 5 existing journal tests, updated to walk every window rather than count all rows, plus a new window/search/arrival test and both S2 markets. Rendered rows are asserted to stay within one window. The first version clamped the last window to be full, which made paging repeat 89 entries; the new walking test caught it. Frontend `tsc`, `npm test` (3) and `npm run build` passed. Backend and Godot unchanged in this slice; no commit or push.

**One next task:** commit this working tree (pinned variants, the other session's web journal and launcher work, and this window) once the owner authorizes, then confirm CI is green on main. After that, the owner decisions (license, generator gate rule, Case1 opening LP confidences, ticker rename, deployment, music) remain the blockers for P4 campaign work.

## As-of tape pure domain (P4), 12 October 2026

The previous next task (commit) needs owner authorization, so this session took the unblocked P4 item. New `backend/src/fundforge/asof.py`: an `Observation` is `(instrument, event_time, available_at, revision, value)`. `AsOfTape` refuses an observation available before its event, revision chains that are not `0..n`, and corrections that do not become available strictly later than the previous revision. `known(clock, instrument=None)` returns the highest revision of each event whose `available_at <= clock`, and `value(instrument, event_time, clock)` returns None before the first print. A correction published later therefore never appears in an earlier view, and reading at a later clock cannot change an earlier one.

Validation: `tests/test_asof.py` 8 passed. Dropping the `available_at <= clock` filter makes 2 fail. Full backend suite **266 passed, 38 skipped**. The skips are the PostgreSQL cases because this run had no `DATABASE_URL`, so the earlier PostgreSQL count is not newly claimed. Ruff and mypy (30 files) passed. Not wired into the engine or a fixture, so no rules bump and no golden change. No commit or push.

Limitations: times are integer event ordinals; mapping to `(day, phase)` happens when it is wired. Case1 marks have no revisions, so a revised series belongs to the authored v1 campaign or the generator.

**One next task:** commit the working tree once the owner authorizes and confirm CI. Unblocked alternative: have `generator.py` emit an optional revised macro/fundamental series as `Observation`s and expose `known(clock)` in the terminal's research view, with a leak test proving no future revision reaches a player API.

## Presence retry storm against older servers, 12 October 2026

The owner asked to fix crashes and errors. Godot logs (`%APPDATA%/Godot/app_userdata/FundForge/logs`) showed no crash, only a repeating pair of engine errors, `Invalid status code. Got: '403', expected '101'` and `Invalid response headers`, from `api.gd` `_process`. Cause: the local API on port 8011 predates `/api/rooms/{id}/presence` (its OpenAPI lists no presence route), so Starlette refuses every WebSocket upgrade with 403, and the client retried forever with backoff capped at 15 s. Polling kept the game working.

Fix: `WorldRules.presence_retry(attempt, ever_opened)` allows at most `PRESENCE_HANDSHAKE_TRIES` = 3 handshakes until a socket has opened since `join`. After a socket has opened, drops still reconnect without limit. Polling is unchanged.

Validation: Godot headless suite 0 failures, including a new check that fails if the limit is removed. A graphical run against the stale 8011 server logged exactly 3 handshake errors in 40 s and then stopped. A graphical run against the current API on 8022 walked five locations and opened the terminal with no errors in the log. Backend with PostgreSQL: **300 passed, 4 skipped** (the `pg_dump` cases). Frontend `tsc` and `npm test` passed. No commit or push.

Remaining: the 8011 process (PID 45340, started 11 October) still serves old code. It was left running because this session did not start it. Restart it from the current tree to get presence. The Starlette `httpx` test-client deprecation warning remains.

**One next task:** commit the working tree once the owner authorizes and confirm CI.

## Revised activity index in generated markets (P4), 12 October 2026

Completed the prior unblocked task. `generator.macro` adds a fictional `STREET_ACTIVITY` index to every generated tape. Each generated day prints the hidden regime's level (calm 52.5, stressed 47.5) plus up to ±2.0 noise, published the next day. With 30% probability a revision within ±0.5 of the level follows three days after the period. It reads its own `MACRO_VERSION` SHA-256 stream, so generated marks, and therefore balance-gate results, are unchanged. `Spec` refuses a same-day first print, which would come before that day's mark. `compile_tape` validates `raw["macro"]` through `AsOfTape` (authoring faults become `TapeError`). `GET /terminal` returns `macro` from `tape.macro.known(current day)`. The Godot MON page lists the four newest periods as "first print" or "revised" with the publication day. Case1 and other authored tapes have no `macro`, so their digests, goldens and `RULES_VERSION` are unchanged.

Validation: backend with PostgreSQL **303 passed, 4 skipped**. The three new generator tests check that marks are identical with and without revisions, that print/revision error bounds and lags hold, and that malformed macro rows are refused. A play-through checks that at every event the terminal shows exactly the latest revision published by that day. Making the terminal read two days ahead fails it. Ruff and mypy passed. Godot headless suite 0 failures, including the new row-format check. A live generated room on a fresh API (port 8023, since stopped) skipped to day 21 and showed the prints and revisions over HTTP and in a Godot MON screenshot. No commit or push.

Limitations: generated rooms created before this change now fail the stored tape-digest check and are parked as incompatible. The index is shown but not yet scored or used by research questions/Brier scoring, LP agents or the bot. The web desk does not display it.

**One next task:** commit the working tree once the owner authorizes and confirm CI. Unblocked alternative: a research question on the generated regime whose evidence is the published index, using `research.posterior` with likelihoods derived from the generator's noise bounds, and Brier-scored in the debrief.

## Regime research and thesis tickets in generated rooms (P4, builder M1), 12 October 2026

Owner-authorized parallel builders (12 Oct 2026): M1 backend research, M2 game budgets, M3 web terminal, each with its own paths, database and ports, and no commits.

`research.regime_filter` is an exact Fraction forward filter (two-state HMM; starts calm, switch p = 3/20, published prior for generated day k is (1-(1-2p)^k)/2). Its evidence is the latest published revision of each print, with uniform likelihood 1/(2b+1) inside the noise bound. A revision replaces its first print. The terminal's new `regime` field (prior, posterior, question `regime:<day>`) reads only `tape.macro.known(today)`. It is null in authored markets. New `thesis` command (`{type, question, forecast:{calm, stressed}}`, strict decimal strings summing to exactly 1) for the live question only. It is command-log only, so the journal, NAV and outcome are unchanged. The debrief adds `research`: each seat's latest thesis per question, the true regime, Brier score and mean Brier, beside P&L.

Design change by the builder, open for owner veto: ±2.0 first-print noise made calm and stressed prints disjoint, so every print settled the question. First-print noise is now ±4.0, leaving an ambiguous band of 48.5–51.5. `MACRO_VERSION` is `macro-2026.10.2`. Marks are unchanged; generated-room tape digests change.

**RULES_VERSION `case1-rules-2026.10.9`**, because the server accepts a new command type. `golden.json` changed only its rules tag; all path digests are unchanged. Older rooms are parked as incompatible.

Validation: new `tests/test_research_regime.py` (7), including a hand-derived filter (3/20 → 51/200 → certain stressed with chain prior 657/2000 → revision makes calm certain) and a leak test that flips future regimes and rewrites unpublished prints at three cutoffs. Making the terminal read `known(day+2)` fails 3 tests. Full suite against database `fundforge_m1`: **310 passed, 4 skipped**. Ruff and mypy passed. `openapi.json` and `api-types.ts` were regenerated. The coordinator re-ran 20 targeted tests (research, golden, generator, openapi freshness): passed.

Limitations: there is no thesis UI or debrief research panel in Godot or the web desk. Only the newest period can be forecast. The filter assumes the default `Spec()`.

## Forge Terminal in the web desk (P2 web desk, builder M3), 12 October 2026

New `frontend/app/room/[id]/terminal.tsx`, opened from a "Terminal" tab in the desk's Records tabs. It is read-only and sends no commands. It has:
- a market monitor whose symbols are keyboard buttons with `aria-pressed`;
- an event-spaced inline SVG history chart with `role="img"`, an aria summary and the same summary as visible text;
- fund watch, the static stress table with the backend's method caption, the STREET_ACTIVITY table (generated rooms only; newest first, "first print"/"revised", published day) and the 8 latest headlines.

`/terminal` has no ETag, so the panel refetches when the desk's `/view` version changes. Late responses are ignored, and on error the last snapshot stays with an alert. `.terminal` styles are in `globals.css`. `frontend/e2e/terminal.spec.ts` covers a case1 room (monitor, stress, no macro table, keyboard symbol switch, axe) and a pinned `seed:terminal-e2e` generated room skipped to day 16 (macro rows newest first, axe).

Validation: `tsc`, `npm test` (3) and `npm run build` passed. Playwright against a fresh API on 8031 and `next start` on 3031: **10 passed** (terminal 2, ledger 6, S2 base and rally WIN). Terminal + ledger passed again (8) after a locale fix. The coordinator re-ran `tsc` and `npm test`: passed.

Limitations: the test accepts "first print" or "revised", so showing a revision is not proven in the browser. ORDERS, STREET, REPLAY and the liquidity lab are not ported. The chart has no axes. The rest of the desk formats numbers with the system locale (seen as "1,00,000"). Repeated local e2e runs can hit the in-memory 20 rooms/hour limit; restart the API between runs.

## Frame-time and size budgets (P3 acceptance, builder M2), 12 October 2026

Frame time was measured on this laptop only: RTX 4070 Laptop GPU, i9-14900HX, Vulkan Forward+, 1600x900, V-Sync off, Godot 4.7.2. Each run skipped 5 s of warm-up, then recorded 40 s walking all 8 locations. Budget: p95 <= 16.7 ms. This is not a mid-hardware result.

| Run | frames | mean fps | p50 / p95 / p99 ms | worst ms |
|---|---|---|---|---|
| Before | 3978 | 97.4 | 7.52 / 8.62 / 11.05 | 2101.4 |
| After | 6443 | 161.0 | 6.46 / 7.09 / 8.66 | 16.9 |

Fixed a 1–2 s freeze on entering any room. `office3d.gd` toggled `emission_enabled` on the highlighted floor material, so a new shader variant compiled on the main thread. Emission now stays on and only its colour changes.

New files: `game/scripts/perf.gd` (enabled with `--perf=out.json`), `scripts/measure_frames.py` (local; exits 1 over budget), `scripts/check_budgets.py` and `scripts/budgets.json`. The budgets are about 20% above measured sizes: Linux export 126,977,552 bytes, Windows 162,726,624, gzip first-load JS `/` 116,063, `/room/[id]` 123,517 and `/_not-found` 114,083. CI runs the size check after the export and after `npm run build`. Frame time stays local because the runners have no GPU. A new frontend route fails CI until it has a budget entry. `docs/ENGINEERING.md` §12 records the measurements.

Validation: Godot headless suite 0 failures, including 2 new percentile checks. The coordinator re-ran the Godot suite (0 failures) and `check_budgets.py --next frontend/.next` (all routes within budget).

Limitations: one machine only, measured against the 8022 API, so presence was not exercised. A lower-end GPU and the Compatibility renderer are unmeasured. The JS total approximates Next's "First Load JS" column. Existing CI actions use version tags, not SHAs.

## Research play in Godot and shader warm-up (builder M6), 12 October 2026

The Forge Terminal has a 10th page, RESEARCH (F10 or `RESEARCH`). It shows the question, the published prior, the posterior labelled "from published prints", the method and the evidence count. The thesis entry takes calm in [0,1] with at most 6 decimals, checked by a regex. Stressed is the exact integer complement in 6-decimal fixed point. The page sends one `Api.command` with one idempotency key, is disabled while sending, while data is stale or after the season ends, and shows server rejections in the existing status line. `hud.gd`'s outcome screen adds "RESEARCH / REGIME FORECASTS (separate from P&L)" from the debrief. Test hook: `--thesis=0.4` types into the real input and presses the real button, so the server still validates it.

Shader warm-up: the street-view DOF is no longer toggled; its blur distance moves out of range instead. The broker courier and tactical LP visitor are instantiated once at load, hidden, and freed after 3 s, so their first mid-crisis arrival compiles nothing.

Validation: Godot suite 0 failures (171 ok). Changing the complement to `999999` fails 5 of the new checks. Live smoke on 8032 (`seed:godot-research`) at day 15 showed prior 0.671500/0.328500, posterior 0.850000/0.150000 and a recorded thesis of calm 0.7. The outcome screen showed true CALM and Brier 0.180000 (= 0.3² + 0.3²). Frame time over two runs: p95 7.05 / 7.07 ms, worst 11.7 / 11.6 ms. The coordinator re-ran the Godot suite: 0 failures.

Limitations: the perf route does not trigger the courier or LP visitor, so that warm-up is unmeasured. A previously recorded thesis is not shown on the page. `hud.gd:611` describes every non-base variant as "a broad rally", which is wrong for generated rooms.

## Research play and terminal hardening in the web desk (builder M5), 12 October 2026

`frontend/app/lib.ts` adds two helpers:
- `num()`, an en-US count formatter that replaces every bare `toLocaleString()` in `desk.tsx` and `terminal.tsx`. This fixes the "1,00,000" display.
- `complement(p)`, an exact 1 − p in integer micro-units (0..1, at most 6 decimals, else null). Both are tested in `lib.test.ts`.

The terminal has a "Regime research" block: prior, exact posterior captioned as coming from the N published prints, and a thesis form with `aria-invalid` validation. It submits through the desk's single-flight `send` and shows the seat's latest thesis from `decisions`. The debrief shows "Research record (separate from P&L)" from `POST /debrief`.

`frontend/e2e/research.spec.ts` has two tests:
- A mocked `/terminal` proves the "revised" and "first print" labels and en-US formatting. A request held across two version bumps cannot replace the newer snapshot, a 503 keeps the last snapshot with an alert, and axe is clean.
- A pinned `seed:research-e2e` room rejects "1.5", accepts 0.35/0.65, plays to the end and shows Brier scores. axe is clean.

Validation: `tsc` passed. `npm test` 5 passed. `npm run build` passed. Playwright **12 passed** (research 2, terminal 2, ledger 6, S2 base and rally). Removing the fetch guards fails the late-response test. The coordinator re-ran `tsc`, `npm test` (5) and the size budget: `/room/[id]` is 125,055 of 148,300 bytes.

Limitations: the `/terminal` and `/debrief` shapes are typed by hand because the backend returns untyped dicts. No test covers a server-side thesis rejection.

## Shareable ending card and generated-market outcome text (P4, builder M7), 12 October 2026

New `game/scripts/card_rules.gd`:
- `market_text(variant)` gives the case1 base and rally sentences, and for `seed:<x>` a generated-market sentence with the revealed seed. This fixes the `hud.gd` "broad rally" bug.
- `seed_hash` is the SHA-256 of the revealed seed.
- `money` formats Decimal strings as text only, with no float rounding.
- `rows(...)` leaves out missing optional rows rather than guessing them.

The outcome screen has "Save ending card", which renders a 1200x630 SubViewport on demand to `user://fundforge-ending-<room>.png` and shows the absolute path. The card shows label, partners, rank and score, fund vs passive-book bps, final NAV, forced-action count, mean Brier per seat, the variant or seed with its SHA-256, and the rules version, chain head and journal digest from `GET /verify`. Nothing is uploaded. Dev flag: `--save-card=path.png` with `--join`.

Validation: Godot suite 0 failures (187 ok), including 17 new checks. Graphical smokes saved and inspected cards for:
- generated `seed:card-test`: SURVIVAL, #6 of 6, NAV $21,806,458.80, seed hash equal to Python's, chain head equal to `/verify`;
- case1 base: SURVIVAL, #5 of 6, NAV $22,168,060.54.

The coordinator re-ran the Godot suite: 0 failures.

Backend gaps: no fund max-drawdown field, no post-run regimes or stressed-day count, no served seed commitment after the run, and no scenario id or fund name in the outcome. The card therefore omits those, and case1-controls and case1-settlement rooms look like case1 on the card. The Save button itself was not clicked in a smoke; the flag calls the same function.

## LP agents drive redemptions in generated rooms (P4, builder M4), 12 October 2026

LP agents run in `case1-generated` rooms only. **RULES_VERSION `case1-rules-2026.10.10`**; Case1 golden path digests are unchanged (only the rules tag changed).

- **Confidence rules.** `lp.py` (policy `lp-confidence-2026.10.2`) gives each LP drawdown, response-lag and contact costs. `review()` runs at the certified closes of days 13 and 15. Contact offsets losses but never raises confidence by itself. `chapter_close` adds herding (half of the LP's own gate penalty).
- **Redemptions.** `investors.on_close`: at the day-15 cutoff, Tactical's request is the larger of `redemption_request` and the authored 10,000 units, never the sum. Day-20 dealing goes through `allocate_gate` and the administrator-checked `series.redeem`. `engine._deal` was refactored with Case1 postings byte-identical. A WIN becomes SURVIVAL when gated units are carried.
- **Commands.** `contact_lp` (MP only; uses that window's attention) and `propose_gate`. A gate is a package bound to the dealing day and the exact requests. It is elected only by the other partner's `sign`, with the requests revalidated at signing. The bot refuses to countersign gates.
- **View.** New `investors` field (MP only, otherwise null) and package `kind`/`terms`. The shared clock-pause reason no longer reveals private notices.
- **Debrief.** Exact LP components.

Validation: new `tests/test_lp_agents.py` (6 tests):
- a hand-derived Tactical path over two reviews (65 → 59 → 52, giving a 17,500-unit request), and a drawdown that triggers a request dealt with exact units and a payable that matches the journal;
- Case1 untouched;
- a gate refused for self-approval, a wrong digest and the bot, with pro-rata deferral and herding;
- replay giving identical journal and LP log;
- a leak test using a tape that crashes from day 15.

Three mutations (ignoring confidence, ignoring the gate, a view one window ahead) each fail a test. Balance gate on seeds `bench-0..29`: 12 of 30 accepted with and without LP agents; all 18 rejections are `cover_recall_only_does_not_win`. The coordinator re-ran the full suite against database `fundforge_m1`: **316 passed, 4 skipped**. Ruff passed.

Owner decisions pending (builder's balance guesses):
- launch-roster starting confidences 72/80/65 apply to generated rooms;
- review days 13 and 15, with the costs and caps;
- herding at half the gate penalty;
- a gate can be elected even when it defers nothing;
- the bot never consents to a gate, so solo players cannot gate;
- LP bands are MP-only; formal notices and gate elections are shared.

Limitations: with launch lock-ups a gate cannot hold anything back in this window (Tactical's largest request is about 14% of NAV, under the 20% cap), so deferral is tested only with a test roster. Contact does nothing after day 15. There is no LP UI in either client.

## README demo GIF (P2, builder M8), 12 October 2026

`docs/images/s2-two-partners.gif` (5.7 MB, 141 frames, 1288x485, sped up 4x) shows Ana (PM) and Ben (MP) side by side in the web desk, from the real Playwright S2 base run: margin call on day 16, co-signed ALTO sale filled, both debriefs Win. `frontend/e2e/s2.spec.ts` records both contexts only when `FUNDFORGE_RECORD=<dir>` is set (base market only). Without the flag it runs unchanged and adds no sleeps. `scripts/make_demo_gif.py` composes the GIF using `$FFMPEG`, PATH ffmpeg or Playwright's bundled ffmpeg, plus Pillow. README shows the GIF with alt text and a dated caption.

Validation: record run 1 passed (base WIN, cure). Unflagged run 2 passed (base and rally WIN). `tsc` passed. The coordinator inspected a middle frame: margin call, book, desk feed and committee are legible.

Limitations: the GIF shows the web desk, not Godot. Ben's top bar is scrolled off for most of the clip. Small text is only just legible at README width. Pillow is not a declared dependency. The GIF must be re-recorded when the UI changes.

## Typed terminal/debrief contracts and outcome facts (P2/P4, builder M10), 12 October 2026

- **Typed contracts.** `schemas.py` has strict `TerminalView` (the full control report, stresses, news visibility, `macro`, `regime`) and `Debrief` (branch state, timeline, research Brier records, LP debrief with typed review and chapter-close checkpoints) models. `BranchOutcome` allows `IN_PROGRESS`. The new models use `DecOut` (`^-?\d+(\.\d+)?$`), because units (8dp) and the administrator claim price exceed the 6dp input pattern.
- **Endpoints.** `api.py` declares both as `response_model` with `exclude_unset`. HTTP tests assert each body exactly equals the engine output. `openapi.json` and `api-types.ts` were regenerated, and `lib.ts` exports `TerminalView`, `Debrief` and `Forecast`, replacing the web desk's hand-written types (type-only change).
- **Outcome facts.**
  - `max_drawdown` is the peak-to-trough fall of fund NAV per unit as a fraction of its running peak, rounded once to 6dp HALF_EVEN. Its points are the warm start plus each business-day CLOSE. NAV per unit is used so redemptions are not drawdown; the definition is in GAME_SYSTEMS §9.
  - The outcome also adds `scenario`. Generated rooms add `seed_commitment`, `stressed_days` and `generated_days`, only after the run.
  - RULES_VERSION stays `case1-rules-2026.10.10`: these fields are derived and never journaled, and no posting, fill, fee, label or score changes. Golden digests are unchanged.

Validation: new `tests/test_outcome_facts.py` (12) has hand-derived drawdowns including HALF_EVEN ties, an independent close-value check, and a leak test over every pre-finish view, both seats' terminals and `outcome()`. The leak test fails if the `finished()` guard is removed. `test_schemas.py` (+2) validates terminal and debrief JSON over whole games and asserts the optional parts were reached. The coordinator re-ran it: backend **330 passed, 4 skipped** (database `fundforge_m1`), mypy passed, frontend `tsc` passed. The builder also ran `npm test` (5) and `npm run build`.

Limitations: `IN_PROGRESS` is checked only against a mid-run outcome. The seed commitment is revealed only after the run, so it is not a true commit-reveal (owner decision). `RoomView` still uses the unpatterned `Dec`. Neither client shows the new outcome fields.

## Investor inbox in Godot (P4, builder M11), 12 October 2026

New `game/scripts/lp_rules.gd`: pure helpers that read only the current view, covering:
- band labels;
- exact unit strings (text only, every server digit kept);
- per-LP rows with request text such as "dealt at the day 20 close, payable day 21";
- contact-disabled reasons that mirror the server's refusals;
- the gate terms a proposal would bind, the shared gate text, open-gate detection and a notice filter.

In the investor lounge, `hud.gd` shows the MP inbox with "Contact <LP>" buttons, each disabled with its reason, the gate terms and "Propose gate". The PM sees a "belongs to the managing partner" note and shared notices only. Gate packages show their terms to both seats in the committee room and use the existing countersign. Nothing is cached across views. New `main.gd` dev flag `--open=<location>` opens a location panel for screenshots.

Validation: Godot suite 0 failures (202 ok), including 13 new LP checks. Graphical smoke on duo room `seed:lp-1`, database `fundforge_m3`:
- Day 13: MP contact accepted. A second contact was refused for committed attention, and a PM contact was refused as belonging to the managing partner.
- Day 16: the MP screen shows Tactical Concerned with a 17,500-unit request and the gate terms. The PM screen shows no bands.
- Gate: `propose_gate` accepted. MP self-sign and a wrong digest were refused. PM countersign elected the gate.

The coordinator re-ran the Godot suite: 0 failures.

Limitations: contact and propose were sent through the command path, not by clicking the client buttons. The rejection toast fades after about 3.6 s. There is no investor page in the Forge Terminal.

## Completed-run market facts in both clients, 12 October 2026

Read the updated working tree before continuing: bounded journal windows and the P4 domain/client additions were already present, so they were preserved. Completed a remaining outcome-facts UI gap from the typed-contract checkpoint.

The web desk's debrief and Godot's ending screen now show the server's scenario and maximum drawdown, labeled as NAV per unit measured at business-day closes. The server's six-decimal ratio displays as a percentage with four fractional digits. Generated runs also show stressed days out of generated days and the complete seed SHA-256. Missing optional fields remain omitted and zero stressed days are displayed. The hash is labeled as a seed hash, not proof of a pre-run commitment. Godot uses pure `CardRules.facts`; the saved ending-card layout is unchanged.

Paths: `frontend/app/room/[id]/desk.tsx`, `frontend/e2e/outcome.spec.ts`, `game/scripts/card_rules.gd`, `game/scripts/hud.gd`, `game/tests/run_tests.gd`.

Validation: 2 new Playwright tests passed for authored/generated completed debriefs, including no outcome facts before the mocked completion response, optional-field omission and zero stressed days. These control player responses rather than complete an economic run; backend leak tests remain the server-side evidence. Godot suite passed with 0 failures (3 new facts checks). TypeScript, production build and 5 frontend unit tests passed. Scoped diff whitespace check passed; an existing trailing blank line in `backend/src/fundforge/investors.py` remains outside this task. No backend rules, finance, commit, push or deployment changes.

**One next task:** web investor inbox and gate controls matching the Godot lounge, with MP/PM visibility and jointly approved gate browser coverage.

## Web investor inbox and joint gate election, 12 October 2026

Read the existing local changes and completed the prior next task without changing backend economics. `frontend/app/room/[id]/desk.tsx` now gives the MP the generated-room investor inbox: published bands, exact requested/carried unit strings, contact controls with disabled reasons, pending gate terms, and a gate proposal button. Contact consumes the existing attention command; already contacted, committed, ended and post-review states disable it. The PM receives no private inbox controls; published notices and gate packages remain shared.

Gate terms now appear in the partner's approval panel and the package table rather than an empty order list. They show the dealing day, exact requests, pro-rata 20% cap and carry-forward treatment. Proposals use the normal command path; signatures bind the server digest. The existing single-command busy guard wraps the investor panel. Pending/elected gates disable repeated proposals. Gate signatures have a gate-specific confirmation instead of claiming a trade will execute.

New `frontend/e2e/investors.spec.ts` uses two real browser seats in the pinned generated `seed:lp-1` room. The MP clicks Contact Seed, the test advances the deterministic calendar to day 16, then the MP proposes and the PM signs by clicking. It verifies attention consumption, private-control omission for PM, no proposer self-sign button, exact terms visible to the signer, both recorded signatures, elected status and replay verification. Axe finds no serious/critical WCAG 2 A/AA violations on either investor desk after election. The first test attempt checked disabled state before the contact HTTP response had completed; the test now waits for the accepted-command confirmation.

Validation: browser integration/axe test passed; TypeScript, production build and 5 unit tests passed. Local test API on 8024 used `FUNDFORGE_CLOCK=0` and `FUNDFORGE_TEST_VARIANTS=1`; it and the test web server were stopped afterward. Existing gameplay API on 8022 was preserved. No commit, push or deployment. Launch-roster gate deferral limits remain unchanged: this test proves election, not a positive deferred amount.

**One next task:** browser coverage for a stale gate proposal whose bound redemption requests change before signing; confirm the refusal is visible and a fresh proposal can recover.

## Stale gate proposal recovery, 12 October 2026

Reviewed the local changes and completed the prior next task. The web inbox previously disabled Propose gate whenever any pending gate existed, including one bound to obsolete redemption requests. It now blocks repeated proposals only when a pending package matches the current dealing day and exact request map. An MP with changed requests sees an explanation and can propose a fresh immutable package. The earlier package remains in the record. The replacement prompt is omitted after election or when no gate can be proposed.

`frontend/e2e/stale-gate.spec.ts` drives two browser seats with controlled player views/command responses: the PM sees the stale-signature refusal, the MP proposes updated terms, and the PM signs the new digest. It checks the earlier package remains unchanged and matching pending terms disable another proposal. This is a UI boundary test, not a naturally occurring calendar revision.

`backend/tests/test_lp_agents.py` adds a domain fault-injection test: change one request in the same decision window after proposal, reject the old signature, then propose/sign updated terms. It checks original terms/signatures are preserved, no gate is elected by the rejected signature, fresh digests differ, and the journal digest stays unchanged. Real calendar advances may expire packages instead; the injection deliberately isolates the terms check.

Validation: new browser test passed, all 7 LP domain tests passed, targeted Ruff passed, TypeScript passed, production build and 5 frontend unit tests passed. Scoped whitespace check passed. Existing unrelated local edits preserved; no production finance/rules changes, commit, push or deployment.

**One next task:** suppress obsolete gate signature prompts after another gate for the same dealing day is elected, while retaining both packages in the historical table; add browser coverage.

## Builders stopped by the API session limit; verification and commit, 12 October 2026

Builders M9, M12 and M13 stopped early on an API session limit (HTTP 429). The coordinator then checked the shared working tree:
- Backend against database `fundforge_m1`: **331 passed, 4 skipped**. Ruff and mypy passed.
- Frontend: `tsc` passed. `npm test` 5 passed. `npm run build` passed, and the size budget holds (`/room/[id]` 126,091 of 148,300 bytes).
- Godot suite: 0 failures. The new scripts compile.
- Full Playwright suite against a fresh API on 8031 and `next start` on 3031: **16 passed** in 4.0 min (S2 base and rally WIN, ledger 6, terminal 2, research 2, plus M12's investors, outcome ×2 and stale-gate).

**M12, web investor inbox and ending facts.** Its code was finished and is verified by those 16 tests:
- `desk.tsx` gives the MP an inbox with per-LP Contact (disabled with a reason) and Propose gate, with gate terms shown to both seats.
- The debrief shows maximum drawdown, the scenario, and for generated rooms the stressed/generated day counts and the seed SHA-256.
- The new specs are `investors`, `outcome` (authored and generated) and `stale-gate`.
- Limitation: the drawdown percentage is formatted with a JavaScript float, which is display only.

**M9, crisis frame time.** `measure_frames.py --crisis/--engine-args` and the `perf.gd` event marks were written but **never run or measured**. There are no crisis or Compatibility-renderer numbers.

**M13, NAV certification gate.** It made no code changes. `certify()`, the per-series NAV strike with payable residual, and the open-broker-break link to certification remain open.

**One next task:** run M9's crisis measurement and the Compatibility-renderer proxy. Then build the M13 certification gate.
