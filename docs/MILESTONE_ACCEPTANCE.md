# Milestone acceptance audit

13 October 2026. Bounded read-only audit of the active `ROADMAP.md`, actual source, tests, fixtures, workflow and current local edits. This is an implementation inventory, not a claim that CI or every cited test was rerun. Concurrent implementation can supersede individual findings; close a row only with the corresponding evidence.

Status: **Implemented** means source and a relevant test/evidence path exist; **Partial** means the named acceptance contract is broader; **Open** means required implementation/artifact was not found; **External** means completion needs infrastructure, credentials, hardware or a human measurement. Existing local changes are included, so implementation is not equivalent to committed or released.

## P0 — integrity

| Roadmap item | Status | Evidence / remaining acceptance |
|---|---|---|
| Atomic commands, registry dispatch, bound ready, migrations | Implemented | `store.py`, `governance.py`, migrations; `test_store.py`, `test_governance.py`, `test_api.py`. Requires current PostgreSQL suite to establish this checkout passes. |
| Pinned rules/tape, chain, SQL balance, verify, read-only cache | Implemented | `store.py` uses private command copies and append-only replay; `test_store.py` covers tampering and concurrency. |
| Golden replay digests | Implemented | `test_golden.py`, `golden.json`; local rules changes and golden changes must be reviewed together. |
| Stateful property suite | Implemented | `SessionMachine` in `test_session_stateful.py`: random seats/outsider, key reuse, reconciliation, rollback, authorization and replay. Authorization invariant covers all orders; it does not separately encode the roadmap's NAV-percentage statement. |
| Typed incidents, code-based ribbon/outcome | Implemented | `Engine.incident_events`; `outcome()` selects incident codes; related invariant/outcome tests. Human-readable incident text remains presentation. |
| Runtime invariants under fixed context and optimized Python | Implemented | `test_invariants.py`; accounting modules use `CTX`, typed failures and fixed contexts. Run optimized checks before release. |
| Python 3.13, Ruff, strict domain mypy | Implemented | `backend/pyproject.toml`, CI pinned Python 3.13; strict module overrides. CI execution is a separate gate. |

## P1 — game systems

| Roadmap item | Status | Evidence / remaining acceptance |
|---|---|---|
| Versioned compliance at ticket/sign/fill, signed rules digest | Implemented | `compliance.py`, governance/engine checks; `test_governance.py`, `test_balance.py`. |
| Scored outcome with all five requested dimensions | Partial | `Engine.score()` measures passive-benchmark excess and forced-action penalty. `max_drawdown` is an outcome fact; financing/impact drag, on-time claims and mandate breaches are not separate score components. Implement or explicitly amend the contract. |
| Degenerate-policy grid | Implemented | `test_balance.py`, `policy_grid.py`, `balance.py`; generated acceptance also uses the balance runner. Rerun against new campaign tapes. |
| Skip pacing ≤8 rounds with identical digest | Implemented | Governance skip and tests; historical progress records Case1 six rounds. A campaign must have its own pacing test. |
| Private role research, LP/broker data and budgets | Implemented | `test_research_roles.py`, governance views, visits/sharing and private terminal contracts. |
| Deterministic unranked practice partner | Implemented | `bot.py`, `test_bot.py`; two human seats remain distinct. |
| Causal debrief | Implemented | `debrief.replay()`, `test_debrief.py`: before/after state, NAV delta, omission branches, explicit rejected suffix commands, no invented approvals. Exact optimal counterfactual advice is not claimed. |
| Loan-bound recalls/replacements and exact fills | Implemented | `test_borrow_identity.py`, `test_limit_execution.py`; loan and fill identities preserved. |

## P2 — shipping

| Roadmap item | Status | Evidence / remaining acceptance |
|---|---|---|
| Caddy TLS, unpublished DB, env secrets, non-root deployment | Implemented / External | `deploy/compose.prod.yaml`, `Caddyfile`, `smoke.sh`. Public acceptance needs a real host/domain and actual TLS/readiness/verify evidence. |
| GHCR build and SSH continuous deployment | Open / External | Only `ci.yml` was present at audit. Workflow can be authored locally now; execution needs registry publishing configuration, deploy target and SSH credentials. |
| Nightly dump, restore and same digest | Implemented | `backup.py`, `test_backup.py`, `backup-loop.sh`; CI requires pg_dump. Off-host copies and restoration on a separate host remain external operational work. |
| Body/IP limits, TTL/cache bounds, token fragment | Implemented | API/store limits, frontend fragment handling; `test_api.py`, store tests. |
| JSON request/room/seq logs, Prometheus, Grafana | Implemented | `observability.py`, `deploy/grafana/fundforge.json`; production scraping/alert ownership not established. |
| API command union/errors/rejected-key records/ETag/cursor/generated types | Implemented | `schemas.py`, API tests, `test_openapi_file.py`, ledger browser suite, generated API types. Regenerate/check after schema changes. |
| Stable form keys and in-flight controls | Implemented | `frontend/app/exclusive.ts`, unit tests; browser recovery suites protect asynchronous reads. |
| Two-browser S2 Win, axe, README GIF | Implemented | `frontend/e2e/s2.spec.ts`, `docs/images/s2-two-partners.gif`; current full browser run remains integration gate. |
| MIT LICENSE and credits | Partial / Decision | `game/CREDITS.md` inventories CC0 assets; no root LICENSE was found. Existing source ownership/license decision must be checked before applying a blanket license. Asset CC0 does not license original application code. |
| Fictional tickers with collision rejection test | Open / Decision | Existing Case1 symbols include ALTO/BEAM/BOND/ELAN/JUNO; no collision test or replacement set found. A static explicit forbidden list is reproducible; asserting globally unlisted forever needs a maintained dataset. Rename must preserve pinned-room compatibility and update goldens/tests/docs. |
| Ignore coucou and consolidate about eight docs | Open | `.gitignore` lacks `coucou/`; docs has substantially more than eight active files. Consolidation needs link preservation and archival of superseded content. |
| Green remote CI and public artifact | External | Workflow configuration exists; current remote run/public deployment evidence was not established by this audit. Local test logs cannot establish remote CI. |

## P3 — world

| Roadmap item | Status | Evidence / remaining acceptance |
|---|---|---|
| Walkable office, avatars, places, typed-event NPCs and real-time clock | Implemented | Godot `office3d.gd`, `actor3d.gd`, `main.gd`, HUD and world rules; headless tests. |
| Live WebSocket movement with no journal impact | Implemented | `presence.py`, `test_presence.py`, `coop_acceptance.py`; fallback remains available. |
| Kenney CC0 art and provenance | Implemented | Vendored art plus `game/CREDITS.md`, including Kenney, Quaternius and Poly Haven. Roadmap's art-pass wording is stale. |
| Engine-enforced locations/attention/reveals | Implemented | Governance visit/share rules and `test_research_roles.py`; emergency remedies and signatures do not depend on pixels. |
| Sound and music | Partial | Synthesized SFX with persisted mute; no music implementation found. Original deterministic synthesized music is possible without Spotify/OAuth. External integration is optional, not a prerequisite for audio acceptance. |
| Linux/Windows/macOS/web builds attached to releases | Partial / External | `export_game.sh`, export presets and CI test artifacts cover Linux/Windows. No release publication, macOS signing/notarization or web export acceptance established. A web export needs compatible renderer/network/security testing; an unsigned macOS build must be described as such. |
| Two-client crisis split, meet and sign | Implemented | `coop_acceptance.py` and CI exported-client acceptance; local certification script adds dealing-break evidence. |
| Recorded Godot trailer and human playtest | Open / External | README GIF records the web desk, not desktop co-op. Automated headless acceptance does not establish graphical usability or a 60–90-minute play session. |
| 60 fps on mid hardware | External | `measure_frames.py` and `perf.gd` exist. PROGRESS measurements specify RTX 4070 Laptop/i9-14900HX; Compatibility on the same GPU is a renderer proxy, not mid-hardware proof. Crisis outliers and unmeasured initial LP arrival remain material. |
| Bundle-size budgets | Implemented | `check_budgets.py`, `budgets.json`, CI export/frontend checks. Rerun after assets/music/export changes. |

## P4 — v1 campaign

| Roadmap item | Status | Evidence / remaining acceptance |
|---|---|---|
| 30 days, three chapters, about nine decision windows | Open | Store registry contains only Case1/control/settlement/generated Case1 variants. `season_scenario.json` describes a 60-day authored design, not compiled tape; no playable 30-day campaign registered at audit. |
| Six instruments | Open | Existing Case1 uses twelve symbols. New campaign must own a six-instrument tape and coherent marks/volumes/borrow for every dated event. |
| Three founders and one prospect | Partial | Three founding profiles exist; no admission/funding prospect state machine found. A named prospect in a design fixture is not actual subscription cash. |
| Borrow/margin, gate redemption, firm-payroll crises | Partial | Case1 implements these mechanics separately; a new full campaign must link them into authored decision windows with feasible response policies and exact dated settlement. |
| All five endings | Open | Current outcome labels are `IN_PROGRESS`, `WIN`, `SURVIVAL`, `DISTRESS`; Renewal/Winddown/Default/Company Failure paths and predicates are absent. Add tests reaching each ending through valid commands, not label aliases alone. |
| Seeded variants and shareable ending card | Partial | Generator and completed seed reveal exist; no shareable final-card export found. New campaign variants need their own balance acceptance. |
| Hidden states, priors, likelihoods, Bayes, thesis Brier | Implemented / contract clarification | `research.py`, generated-regime research tests and `debrief.research_scores()`. Exact inference uses `Fraction`, then Decimal presentation; roadmap's literal Decimal-only inference wording is inaccurate. Brier does not affect financial NAV. |
| LP confidence/preference/herding/statements | Implemented | `lp.py`, `investors.py`, `test_lp_agents.py`, browser/Godot investor records; currently wired to generated Case1. New campaign must define review/chapter boundaries and opening profiles. |
| Independent NAV and dealing certification with strike/residual | Implemented | `shadow.py`, `test_shadow.py`, `test_administrator.py`, local `test_certificate.py`, certificate UI and acceptance script. Independent checks have defined scope; do not call this third-party professional certification. |
| Broker statements and aged break queue | Implemented | Controls challenge, linked corrections and blocking certification; broker/admin tests. |
| Public hypothetical shock/liquidity/cure analysis | Implemented | `liquidity.py`, `test_liquidity.py`; scenarios use public assumptions and future capacity bounds, not hidden tape. |
| Minimum-impact cure by marginal-cost Decimal bisection, CVXPY oracle | Open | `liquidity.py` explicitly states bounded greedy comparisons, not global optimality. Forced liquidation and globally optimal player drafts are not the specified solver. No CVXPY dependency/oracle found. |
| Generator with SHA counter, Decimal shocks, balance gate and room wiring | Implemented | `generator.py`, `store._draw_variant()`, `test_generator.py`, `test_generated_balance.py`, `generator_acceptance.py`. Roadmap calling gate/wiring open is stale. |
| As-of revised tape | Implemented | `asof.py`, `test_asof.py`; terminal only displays clock-visible revisions. |
| Complete 60–90-minute session | Open / Human measurement | Needs authored full campaign, two viable success policies, explainable failure, all endings, two-seat replay/verify, then timed human sessions. Nine decision windows alone does not establish duration. |

## P5 — separately scoped stretch

P5 is explicitly “Stretch, cut first”; it is not the v1 completion condition. The owner's latest request includes all milestones, so it should be tracked separately rather than silently declared finished or folded into v1.

| Stretch item | Status | Evidence / remaining acceptance |
|---|---|---|
| Canonical 60-day season | Open | `season_scenario.json` is an authored six-chapter specification; no compiled full tape or full-run oracle. |
| Cases 2 and 3 | Open | `scenario_cases.json` and `SEASON_SCENARIOS.md` contain proposed arithmetic branches. Not registered playable scenarios. |
| Staffing | Open | No executable hiring/capability/payroll staffing command model found. Fund and management-company money must remain separate. |
| World W6/W7 | Open | `WORLD_GAME_PLAN.md` needs a bounded acceptance interpretation against the current Godot retarget; roadmap does not enumerate this scope. |
| statsmodels attribution vs true generator factors | Open | No implemented attribution/oracle found; must report mechanical exposure attribution separately from causal skill claims. |
| Optional ALFRED/EDGAR vintage fixture | Optional / External provenance | Not required to finish v1. A local synthetic vintage fixture can test timing; actual external-data fixture needs dated source provenance and redistribution review. |

## Ordered remaining work and contradictions

1. Complete a compiled 30-day campaign and registry/client entry, six instruments, true prospect transitions and five ending predicates. Freeze a scenario version; cover viable/failure policies and chapter/payment administration through the final settlement checkpoint. This is the largest gap hidden by repeated client-recovery slices.
2. Implement the minimum-impact cure contract with meaningful independent oracle tests, or explicitly amend the roadmap to the bounded greedy algorithm. Complete the five requested score dimensions without mixing firm cash, LP flows or Brier skill into NAV.
3. Author deploy/release workflows and remaining export paths locally; exercise local smoke, PostgreSQL restore/verify, full backend/browser/Godot tests, schema freshness and budgets. Actual host secrets, signing credentials, public publishing and independent-device measurements cannot be invented.
4. Add music, shareable ending cards and a real Godot two-client recording. Perform timed human playtests and document hardware/frame outliers rather than infer a mid-hardware result from a renderer switch.
5. Resolve code license/ticker policy from established ownership instructions; ignore coucou and consolidate/link the docs. Preserve pinned old tape/rules compatibility when renaming.
6. Implement P5 as its own acceptance scope after or alongside bounded v1 work: compiled 60-day tape, Cases 2/3, staffing, explicitly enumerated W6/W7 and factor attribution. Optional external vintage data remains optional unless separately selected.

Contradictions requiring doc corrections: README says no exported builds while later documenting Linux/Windows exports; ROADMAP leaves art, generator wiring and settlement reconstruction open despite actual implementation; SEASON_SCENARIOS' 60-day/six-chapter design is not the active 30-day/three-chapter v1 target; P1 advertised score dimensions exceed `score()`; P4 advertised optimal cure exceeds the greedy implementation. Earlier “owner authorization” notes do not prohibit writing reversible workflows under the current explicit implementation request. External prerequisites remain actual missing inputs, not a reason to stop independent code work.
