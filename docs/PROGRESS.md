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

## Margin cure solver (P4 milestone), 15 October 2026

**Done in this worktree (uncommitted until the commit below):**
- `backend/src/fundforge/cure.py`: minimum-impact cure by shared-multiplier bisection in Decimal, whole-share flooring, give-back pass and pairwise local search. Method and bounds in [CURE_SOLVER](CURE_SOLVER.md).
- `liquidity.py` now draws its cure plans from `cure.solve`; `api.py` and `test_liquidity.py` updated to match.
- `backend/tests/test_cure_oracle.py`: CVXPY continuous optimum, exhaustive integer oracle and greedy comparison, plus a check that runtime code never imports cvxpy. CVXPY is a dev-only dependency in `backend/pyproject.toml`.

**Checks:** full backend suite `420 passed, 37 skipped` (`uv run pytest -q`); `ruff check src tests` clean; cure oracle and liquidity tests `176 passed`.

**Not checked:** `lint-imports` is not configured in the backend project, so the boundary rule was not run here. Mypy was not run on `cure.py`.

**Limitations:** the solver is a local optimum of the integer problem, with no global-optimum claim. The tolerances are measured, not proven: worst observed gap to the convex optimum was 7.5% on small caps.

**One next task:** run `uv run mypy src/fundforge/cure.py` (domain modules are mypy-strict per CLAUDE.md) and fix any findings.
