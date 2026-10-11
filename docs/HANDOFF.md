# Current implementation handoff

Updated 8 October 2026 after the owner's request to continue implementation, document it, and build a professional-terminal experience inside the game.

## Authority and starting point

Read `CLAUDE.md`, `ROADMAP.md`, `PROGRESS.md`, this file and `TERMINAL.md`. ROADMAP v4 supersedes the archived FF0a/M0 handoffs. Those documents contain historical mechanics, not the current next task. At entry, HEAD was `7b066f2` and the working tree already contained extensive backend, game, dependency, CI and documentation changes plus archived-file moves and untracked `ARCHITECTURE.md`/`GAME_GUIDE.md`. Preserve that work. This continuation did not commit, push, publish, change repository visibility or deploy publicly.

The code already had Case1, a deterministic Decimal journal, LP series, command sourcing, Postgres verifiability, compliance, five rival funds, a deterministic solo partner, a real-time clock and a Godot 3D world. The realistic rendering pass was already in HEAD. The stale PROGRESS next task asking to finish that pass and the ROADMAP footer asking to create already-existing golden tests needed updating.

## Implemented in this continuation

Forge Terminal is now connected to the game and authoritative local backend. It has MON/GP/PORT/RISK/NEWS/ORDERS/STREET/HELP functions, observed mark history, side-based static stress, borrow APR, public feed and order status. Opening uses T or the HUD/trading-floor button. F1-F8 navigate; Esc closes. Trading returns to the existing governed desk. Reconnection retains and labels stale data. See `TERMINAL.md` for contracts, ownership, formulas, screenshots and limitations.

No economic rule or fixture version changed. Processed observations are rebuilt by command replay; the existing journal goldens pass unchanged. There is no real-market feed, new financial execution path, LLM, Kafka or external data service.

### Subsequent invariant continuation, 8 October 2026

The owner asked to continue implementation. The next agreed invariant task is now complete: `engine.InvariantError` carries `code`, `detail`, `day` and `phase`; every financial production `assert` was replaced by an explicit guard. Opening units are checked before allocation. Reconciliation runs under `localcontext(CTX)`, checks each entity's cash separately, and preserves all original accounting predicates. It remains effective under `-O` and `-OO`.

`backend/tests/test_invariants.py` adds 20 test cases: eleven injected breaks (including balanced-but-wrong postings and a broken balance index), zero/negative opening units, low caller precision, session rollback, real PostgreSQL rollback/cache integrity, and four optimized-process probes. These subprocesses use explicit exceptions, not optimized-away test assertions. The four valid scenario paths match the existing golden JSON in both optimization modes.

No rules-version bump was made: accepted valid economics, commands, postings and predicates are unchanged. Internal failure type/diagnostics and runtime enforcement change; no previously valid zero-unit opening exists because allocation already rejected nonpositive weights. `RULES_VERSION` and golden files remain unchanged. A direct Engine caller must discard a failed transition; Session and Store already restore/roll back it. This is not an independent administrator implementation or certification of all P0 items.

## Reproducing checks

Use Python 3.13. The existing `backend/.venv` was a Python 3.14 environment locked by a running pre-existing uvicorn process, so the normal `uv run` could not replace it. We did not terminate that server. Validation used an isolated environment by setting `UV_PROJECT_ENVIRONMENT=C:/Users/krish/.cache/fundforge-terminal-venv` before running the following from `backend/`:

```text
uv run pytest -q                       # DATABASE_URL required for database tests
uv run ruff check src tests
uv run mypy -p fundforge
```

PostgreSQL was the existing local `fundforge-db-1` container on port 5432. Latest backend result after invariant enforcement: **111 passed**. Targeted invariant/golden run: **21 passed**. Ruff and mypy passed. The API-store pool cleanup and Starlette/httpx warnings remain known.

Godot 4.7.2 was downloaded from its official GitHub release into `C:/Users/krish/.cache/fundforge-godot-4.7.2`; its ZIP was checked against the release's SHA512-SUMS. It is not a repository dependency or committed binary. Run its console executable:

```text
godot --headless --path game --editor --import
godot --headless --path game --script res://tests/run_tests.gd
godot --headless --path game --quit-after 5
```

The test script reported 61 passing checks. Graphical captures are in `docs/images/`. The workstation was visually inspected, including all market rows, chart and stress table. Screenshots do not prove multiplayer graphical behavior or human enjoyment.

A separate local validation API ran on port 8011 with the isolated Python 3.13 interpreter, the same local database and `FUNDFORGE_CLOCK=0`. The default 8000 service was left alone.

After validation, that dedicated 8011 API was restarted against the latest code with the clock enabled for local play. Set the Godot menu's Server field to `http://127.0.0.1:8011`. This is a local process, not a hosted deployment. Its logs are `C:/Users/krish/.cache/fundforge-terminal-api.{out,err}.log`.

The smoke command was:

```text
python scripts/terminal_smoke.py --server http://127.0.0.1:8011 --output C:/Users/krish/.cache/fundforge-terminal-smoke
```

Its output directory includes private room tokens; never commit it or paste it into public evidence. The safe smoke summary was day 16, 12 quotes, 22 observations, version 18, cover filled 1,250, books verified. New screenshot flag: `--terminal=MON` (or `GP`/`RISK`) with the existing local `--join`, `--server`, `--shot`, and `--shot-after` options. Screenshots explicitly force a render frame for hidden-window capture.

## One next implementation task

**Reconstruct settlement obligations independently from execution identities.** Broker and LP/fee controls are implemented; read [ADMINISTRATOR_CONTROLS](ADMINISTRATOR_CONTROLS.md). Replace the remaining trust in the engine's pending-obligation collection with a separate dated delivery/receipt ledger. Test missing/duplicate deliveries, exact loan return allocation and failed settlement retries. Preserve evidence and do not call scoped `checked` results full external certification.

Liquidity/cure, omission replay, typed incidents and role research are already implemented. Deployment, exported builds, backups, human playtests and the full campaign remain open. Do not reinitialize from archived FF0a instructions or claim P0-P5 is complete.

## Exact limit execution continuation, 8 October 2026

Completed maximal whole-share limit sizing in `execution.limit_quantity`, called from Engine after remaining/reduce-only/borrow/capacity bounds. BUY/COVER compare rounded price <= limit; SELL/SHORT compare >= limit. Upper-mid bisection includes equal-price plateaus, zero bounds and halts, preserving post-sizing margin/mandate rejection. Tests independently expand the cubic cost difference rather than importing the production pricing implementation.

26 new tests exercise all four sides, cumulative impact, exhaustive small-quantity price boundaries and microticks/midpoints, zero-impact plateaus, a 99-vs-95 underfill regression, actual balanced Engine fills, shared capacity and reduce-only positions. Full PostgreSQL suite: **137 passed**; targeted new tests/goldens: **27 passed**; Ruff and mypy passed. Existing warnings persist. No game code changed.

Rules are now `case1-rules-2026.10.4`. Goldens were regenerated; four existing market-order paths retain their exact digests/NAVs, only the fixture rules tag changes. Older rooms are intentionally refused by new-version servers (existing compatibility tests pass); do not update stored room versions to bypass this. Use their old runtime to continue them. No migration, commit, push or deployment. The previously running 8011 server still has the prior rules loaded; restart intentionally when ready to create new-version rooms.

## Latest checkpoint, 9 October 2026

Borrow identity, liquidity/cure and completed-run causal replay are implemented. See PROGRESS and TERMINAL for scope. New files: `liquidity.py`, `debrief.py`, tests `test_borrow_identity.py`, `test_liquidity.py`, `test_debrief.py`, and `scripts/analysis_smoke.py`. API: authenticated/versioned POST `/liquidity` and `/debrief`. Godot: RISK lab and REPLAY/F9; HUD reviews cure legs before normal package proposal. Exact loan reservations survive settlement failure; typed incident events determine outcome classification while legacy strings remain presentation-compatible.

Evidence: 173 backend tests with PostgreSQL, Ruff, mypy, 69 Godot checks, import/boot, real HTTP smoke. Existing warnings remain. Goldens regenerated at rules 2026.10.5 and new tape digest; existing path economics unchanged. Local API restarted on 8011, wrapper PID 36216, clock enabled; default 8000 untouched. Older rooms need their original runtime, never edit their stored version. Earlier server/checkpoint descriptions above are historical.

Lab uses frozen marks/rates and last observed event volume, includes T+1 and carry, uses a disclosed interval carry cushion, and compares greedy policies; it excludes future rivals/news/flows/invoices. It is not a global optimizer. Replay currently omits one recorded action, preserves signatures and reports rejected suffix steps; branches are reproducible read results, not persisted multiplayer rooms or arbitrary alternative strategies. Completed-only access prevents future leakage. No new rendered screenshots or human playtest claimed.

## Latest handoff, 10 October 2026

Current rules **2026.10.6**, scenario fixture **4.1.0**. New role/attention code: Engine `assign_research`, `share_research`, `visible_notices`, Session `visit`/`share_research`, filtered view/terminal, generic shared clock pause reason, solo bot sharing, Godot assignment/share controls and corresponding Next.js controls. Each role has two topics; one assignment per cursor/window; location is validated, but physical proximity is not required. Mandatory actions remain unrestricted by attention. Research assignment activity/location is public; evidence contents are private until revealed and shared. Direct engine-only scenario scripts use legacy shared research; player APIs always bind the authenticated role.

`shadow.py` is a separate arithmetic implementation with frozen execution confirmations, expanded cubic pricing and rebuilt holdings. Engine gates due redemption dealing on its execution/valuation check. It uses supplied book cash/liabilities, so full administrator certification, independent fees and external statement reconciliation remain pending. Terminal labels this scope. API lifespan now closes the cached Store pool and clears it; the real TestClient uses lifespan and asserts cleanup.

Latest evidence: **192 backend tests with PostgreSQL**, Ruff including `analysis_smoke.py`, mypy **19 modules**, **74 Godot checks**, editor import and boot, Next.js production build. Only Starlette/httpx warning remains; pool shutdown warnings disappeared. `analysis_smoke.py` with two authenticated seats passed privacy-to-sharing, liquidity, exact baseline and omitted-cover replay, with unchanged verified books (version 40; branch NAV delta -45.42 in this run).

Local 8011 service reloaded to current code, clock enabled, wrapper PID **29192**. Default 8000 untouched. No room migration, commit, push, deployment or paid service. Use new rooms. All four scenario golden path digests/NAVs remain unchanged; rules and tape digest updated. New controls have headless/UI and HTTP evidence, not new screenshots or a human playtest. Secondary web UI work used the local `vercel-react-best-practices` skill. Repository still contains pre-existing unrelated changes and `coucou/`; preserve them.

Final API compatibility check: older pinned rooms return HTTP 409 for view/ledger as well as terminal/commands; targeted terminal/API tests passed (9 passed, one database case skipped in that targeted run). Full PostgreSQL suite evidence above remains the 192-test run. API reloaded after this error-reporting fix.

## Latest handoff, 11 October 2026

Implemented the prior next task: independent broker cash/loan-fee reconciliation, authored dated statement revisions, an aged break queue and MP resolution. Read [BROKER_CONTROLS](BROKER_CONTROLS.md) for exact contracts and limits. New module `backend/src/fundforge/broker.py`; new tests `test_broker.py`; new fixture `broker_break_example.json`. Engine records broker operations independently of journal helpers, runs separate daily financing calculations, gates new risk/dealing, and emits `dealing_blocked` for a missed close. `resolve_statement` uses normal authenticated/versioned/idempotent commands. Statement corrections change evidence, not financial postings. Raw future revisions never reach terminal responses.

Godot menu exposes `case1-controls`; RISK shows review/history; solo MP bot resolves matching corrections; REPLAY can omit review and retains the resulting dealing failure. The standard case has a correct opening cash statement. The challenge is a separately pinned tape assembled by Store from the same market fixture and the authored statement overlay. No new infrastructure dependency or database migration.

Rules **2026.10.7**, fixture **4.2.0**. **214 backend tests with PostgreSQL**, **77 Godot checks**, editor import/boot, Ruff and mypy **20 modules** passed. Real local HTTP challenge smoke passed at version 41, including exact baseline, omitted-cover forced recall, omitted-review blocked dealing and unchanged verified live books. Canonical path economics/digests stay unchanged. The only existing warning is Starlette/httpx deprecation. Current 8011 API wrapper **36440**, clock enabled; 8000 untouched. No commit, push, deployment or new screenshot/playtest. Extensive preexisting edits and `coucou/` remain preserved.

The queue ages authored statement breaks; live arithmetic breaks appear separately. Confirmations are synthetic and share instructed movements/marks. Independent LP/management-fee/claim certification remains next. A missed Case1 dealing window stays missed and is recorded honestly; do not invent automatic late dealing without a versioned claim/window contract. Secondary web UI has not yet acquired the challenge selector or review controls; Godot is the implemented player surface.

## Latest LP-control handoff, 11 October 2026

Management-fee and LP-claim reconstruction is implemented in `administrator.py`, with no finance-module imports. Engine feeds a reconstructed value from confirmed holdings, marks, broker balances and pending settlements; independent fee/claim liabilities determine common P&L. The reducer never reads production common P&L or series capital. It retains frozen dated closes and dealt claims, checks fund and manager fee balances, and validates redemption candidates before mutation. RISK shows last-close series capital and actual dealt claims. See [ADMINISTRATOR_CONTROLS](ADMINISTRATOR_CONTROLS.md) for formulas and limitations.

Rules **2026.10.8**, fixture still **4.2.0**. Canonical economics/digests and tape digest remain unchanged; only the rules tag changes. **228 backend tests with PostgreSQL**, **78 Godot checks**, editor import/boot, Ruff and mypy **21 modules** passed. Real HTTP challenge smoke passed with 13 independently checked closes, one redemption, exact replay, unchanged live books and preserved omission consequences. Sample omitted-cover delta -21.46 in this run. Only the existing Starlette/httpx warning remains.

Local API 8011 reloaded to latest code, wrapper PID **5908**, clock enabled; 8000 untouched. New rooms required for this rules version. No commit/deployment, new screenshot, human playtest or secondary web UI work. Next task is independent settlement identities/receipts: the reducer still shares the engine's pending-obligation inputs. Do not label current controls full external NAV certification or infer annual/subscription support from this January Case1 slice.
