# FundForge roadmap (v4)

8 October 2026. This is the **single active plan**. It supersedes REPLAN_V3, FULL_GAME_PLAN, MILESTONE_PLANS and IMPLEMENTATION_PLAN, which are kept only as reference for mechanics. The domain contracts are unchanged: FUND_ACCOUNTING, GAME_SYSTEMS and SCENARIO_CONTRACTS. The graphical layer is specified in [WORLD_GAME_PLAN](WORLD_GAME_PLAN.md), with the amendments below.

## How this plan was made

Fifty bounded, read-only reviewers attacked the previous plan, each from one perspective:

| Group | Count | Perspectives |
|---|---|---|
| Hiring | 10 | big-tech, quant, fintech CTO, system design, career fair, staff engineer, AI-wrapper skeptic, OSS maintainer, SRE, interview stories |
| Fund domain | 10 | COO/ops, prime-broker margin, administrator, LP allocator, risk, compliance, PM, microstructure, quant research, auditor |
| Game design | 8 | co-op design, pacing, onboarding, exploits, procedural content, multiplayer UX, narrative, accessibility |
| Engineering | 12 | concurrency, Postgres, event sourcing, appsec, performance (measured), testing, API, deploy, observability, determinism, simplicity, Python tooling |
| Strategy | 9 | timeline, competition, v1 scope, docs, demo, legal/IP, world tech, world design, data engineering |
| Planner | 1 | world-game planner |

Each reviewer cited files and lines. These are the findings that changed the plan.

### Defects found in shipped code

| Finding | Source | Status |
|---|---|---|
| **Case1 had a dominant degenerate strategy.** Flattening the whole book on day 12 won with the best NAV ($23.73m against the designed lines at about $22.2m). WIN was a pass/fail checklist. | exploit hunter, measured | P1 |
| Commands were not atomic. A sign whose second leg failed left the first order live. | test architect, concurrency | **fixed** `6ee2279` |
| Cached sessions were mutated while being read, so a rolled-back command could leak into reads ("phantom state"). | concurrency, Postgres, performance | **fixed** `3b5af62` |
| Replay ran whatever code was current. Rooms didn't pin rules, the stored journal was never compared, and TRUNCATE bypassed append-only. | event sourcing, auditor, determinism, Postgres | **fixed** `3b5af62` |
| `ready` was not bound to the state the player saw. Time could advance on a plan the other partner never saw. | multiplayer UX | **fixed** `6ee2279` |
| Unknown command types caused 500s. | API, staff engineer | **fixed** `6ee2279` |
| Jointly signed packages bypassed every limit, so two partners could sign a 300% gross book. | compliance | P1 |
| Recalls weren't bound to a `loan_id`, and limit orders could underfill by about 5% because of the step-down search. | prime broker, microstructure, quant | P1 |
| Narrative strings drove logic: the ribbon deadlines and the outcome both substring-matched prose. | narrative | P0 |
| The frontend sent duplicate orders on double-click (new order id and key per click), and `View = any`. | frontend | P2 |
| Some Decimal maths ran outside the fixed context. Python 3.12/3.13/3.14 were all in play. | determinism, tooling | P0 |

### Decisions

| Decision | Why | Rejected alternative |
|---|---|---|
| **Keep command sourcing.** Pin rules and tape per room and verify replay. | A deterministic engine makes commands the cheapest log. The journal is the event stream. | Domain-event store or snapshots: unneeded at a few hundred commands (measured: Case1 replay ≈10 ms) |
| **A desktop simulation game in Godot 4**, not a website. The owner decided this on 8 October 2026. The Python engine and Postgres stay authoritative, and the client is the world. | The owner wants a simulation game. A Godot desktop build (plus an optional web export) reads as an actual game, and keeping economics on the server keeps every claim about determinism and replay true. | Phaser in Next.js (still a website); Unity (heavier, license terms) |
| **Real time with pause, 1x/2x/4x and auto-pause.** Owner decision, 8 October 2026. | Feels like a sim (Two Point / Paradox style). Ticks are logged commands bound to the room version, so wall time never touches the economics. | Pure turn-based Ready barriers (kept as the "skip ahead together" action) |
| **The world's spatial rules are engine-side attention rules**, not cosmetic movement. | The skeptics were right that a free-walk skin over forms adds friction. Locations as the assignment menu add decisions. | Proximity-only signing gate (adds latency, not choices) |
| **No LLM anywhere in the product.** Use deterministic, authored, templated NPCs. | The owner wants a real project, not an AI wrapper. | LLM narration, tutor or "AI analyst" (old FF7b): cut |
| Keep the analytics libraries off the critical path. CVXPY only as a dev-time test oracle for our own Decimal margin-cure solver. | Our own algorithm is the substance; a library call isn't. | DuckDB, exchange_calendars at runtime, real-price replay (no redistribution rights): cut |
| One small VM running compose with Caddy | WebSockets, same origin, local Postgres, about $5/month | Vercel+Fly+Neon (WS proxying, connection caps, cold starts); Render free (sleeps, DB expiry) |
| One roadmap and about 8 public docs. Planning and agent process docs are archived. | Recruiters read 27 process docs as "AI-planned" | — |

## Phases (about 15 h/week, solo)

Each phase ends with green CI, an updated PROGRESS and one ENGINEERING write-up where noted. Week numbers are estimates.

### P0: Integrity and honesty (week 1)

- **Done:**
  - atomic commands
  - registry dispatch
  - version-bound ready
  - migrations
  - rules/tape pin
  - hash-chained log
  - SQL deferred balance check
  - `verify(room)`
  - read-only cache
- **Golden replay digests.** Commit expected journal digests for scripted paths in `tests/golden.json`. A rules change must bump `RULES_VERSION` and update the goldens in the same commit.
- **Stateful property test.** A Hypothesis `RuleBasedStateMachine` over Session sends random commands from pm, mp and outsiders, sometimes reusing keys. It asserts:
  - reconcile passes;
  - a rejected command changes nothing;
  - every order over 5% of NAV carries the other partner's signature;
  - replaying the log gives the same digest.
- **Typed events and incidents:** `{code, day, phase, refs, amounts}`. Prose is rendered from templates, and the ribbon and outcome read codes, never text.
- **Engine hygiene:** `reconcile` raises `InvariantError` instead of using `assert`. Every ratio is computed under `localcontext(CTX)`.
- **Tooling:** Python pinned to 3.13 everywhere. Ruff, plus mypy strict on the domain modules.

### P1: Make it a game, not a puzzle with one answer (weeks 2–3)

- **Compliance ruleset.** `compliance.evaluate(book, orders, ruleset) -> breaches` runs on ticket, on sign and again at execution. The ruleset is versioned Decimal data: gross cap, a net band and a gross floor while LPs are invested, issuer cap and restricted list. Its hash goes into the package digest. Rejections are logged with their rule code.
- **Scored outcome.** The tier (Win, Survival, Distress) is kept, plus a score:
  - NAV against a passive benchmark
  - maximum drawdown
  - financing and impact drag
  - claims paid on time
  - mandate breaches

  Acceptance: `test_balance.py` runs a policy grid (nothing, flatten on day d, cover-all, S1, S2, seeded random). No degenerate policy may match the best designed line. This test fails on today's tape and must pass.
- **Pacing.** `advance_to_next_window` skips barriers with nothing material: no notice, deadline, incident, dealing, open order or pending package. A pending package blocks the skip instead of expiring. Acceptance: Case1 finishes in ≤8 Ready rounds with a digest identical to stepping through every barrier.
- **Real co-op.** The view is filtered by role. The PM privately holds research cards and capacity estimates; the MP privately holds the LP inbox, prime-broker offers and treasury forecasts. Each partner has their own research budget, and the only way to share is to tell the other partner. This resolves GAME_SYSTEMS §1's "ownership is not secrecy" in favour of asymmetric information, with mandatory notices still shared.
- **Practice mode.** A deterministic partner bot (`bot:v1`) signs within the limits and refuses outside them, giving a reason. These rooms are unranked. Recruiters can then play alone.
- **Causal debrief.** The chain is cause → state delta → consequence → counterfactual ("had you covered on day 14 …"), built from typed events.
- **Execution fixes.** Exact bisection for limit fills. Recalls and rerates bound to `loan_id`.

### P2: Ship and prove (week 4)

- **Deploy:** `deploy/compose.prod.yaml` with Caddy TLS and no published DB port, secrets in `.env`, and non-root containers.
- **CD:** a GHCR build plus an SSH deploy workflow, with actions pinned by SHA and `permissions: contents: read`.
- **Backups:** a nightly `pg_dump`. CI restores it and runs `verify` to get the same digest.
- **Abuse limits:** a body size cap, a per-IP room-creation limit, a room TTL and a bounded cache. The seat token moves to the URL fragment (`#t=`).
- **Observability:**
  - JSON logs with request, room, seq and command type
  - Prometheus `command_seconds`, `replay_seconds` and `rejections_total{code}`
  - one Grafana JSON

  No OpenTelemetry.
- **API v1:** Pydantic discriminated-union commands, a `{code, message}` error envelope, a stored outcome for rejected keys, `ETag: version` with a 304 response, a ledger cursor, and openapi-typescript types replacing `View = any`.
- **Frontend fixes:** one `order_id` and idempotency key per form submission, and buttons disabled while a request is in flight.
- **Playwright end-to-end test:** two browser contexts play S2 to a WIN, with axe checks on the desk. The same run records the README GIF.
- **Hygiene:**
  - MIT LICENSE and CREDITS.md
  - fictional tickers, plus a test that rejects real-listed symbols (ALTO, BEAM, BOND, ELAN and JUNO collide today)
  - `coucou/` ignored
  - docs consolidated to about 8 files, with the rest in `docs/archive/`

### P3: The world (weeks 5–9). Started early at the owner's request.

**Done (`5ad801d`, `d41a528`):**
- Godot 4.7 desktop client in `game/`, drawing a procedural isometric office and street: trading floor, committee room, risk and treasury, research library, management company, investor lounge, and the prime broker across the street.
- Walkable partner avatars, and terminals that open each location's actions.
- NPC traders, a broker courier and LP visitors that react to typed engine events.
- A server real-time clock with pause/speed and auto-pause, with daylight tied to the in-world hour.
- Headless Godot tests in CI.

**Remaining (W2–W5, re-targeted from Phaser to Godot):**
- WebSocket presence for live partner movement. Today the partner avatar walks to the place of their last decision.
- Kenney CC0 art pass, with provenance recorded in CREDITS.md.
- Engine-enforced location assignments (below).
- Audio.
- Exported builds attached to GitHub releases: Windows, macOS, Linux, and a web export.
- A scripted two-client end-to-end run that records the trailer.

**Amendment (from the world-design and world-tech skeptics).** The world's meaningful rules are engine-side, keyed by location rather than by pixel position:
1. **Locations are the assignment menu.** The prime-broker desk, the LP lounge, the research library and the risk room each offer that place's assignments. Taking one is a command `{type: "visit", location, assignment}`, checked by the engine against each partner's per-window attention budget.
2. **You can't be in two places at once.** A partner can claim one location per decision window. Two simultaneous crises force the partners to split up or triage.
3. **Information lives in places.** Research and LP and broker letters are revealed by the visit, gated by `available_at`, and visible only to the visitor until shared.

Mandatory notices, already-authorized orders and emergency remediation stay reachable from anywhere. Signing does not require proximity. The committee room is where packages are presented, but desk mode stays fully playable.

Acceptance:
- A two-context Playwright run where both partners split up across two crises and then meet to present a package.
- A WebSocket test proving that avatar traffic never changes the journal digest.
- A 60 fps budget on mid hardware, and a bundle-size budget.

### P4: v1 complete game (weeks 10–16)

The scope follows the v1 product-manager review: one sitting of about 60–90 minutes with a real start, middle and end.

| Area | v1 scope |
|---|---|
| Season | **30 days, 3 chapters, about 9 decision windows** (a new scenario version; the 60-day default stays canonical for v2) |
| Instruments | 6 |
| LPs | 3 founding LPs plus 1 prospect |
| Crises | 3: borrow recall/margin, a redemption with a gate election, firm payroll distress |
| Endings | All 5 labels (Renewal, Survival, Winddown, Default, Company Failure) |
| Replay value | Seeded variants and a shareable ending card |

Systems:
- **Research as a skill.** Hidden discrete states with published priors. Evidence cards carry authored likelihood ratios, and the Decimal Bayes posterior is exact. Thesis tickets are scored with a Brier score, reported beside P&L but never inside it.
- **LP agents.** `lp.confidence(policy, facts) -> components` with preference terms (drawdown, response lag, contact), herding after gates, and series-level statements.
- **Independent administrator.** `shadow.py` recomputes NAV from tape, fills and loans without importing posting code. A `certify()` gate blocks dealing on a break over 1¢. NAV per unit is struck, and payable = units × price with an explicit residual.
- **Broker statements.** A statement with declared breaks, plus a break queue with aging. An open break blocks NAV certification.
- **Risk.** A stress and liquidity simulator: shock marks, then replay forced liquidation over future events with real impact and capacity, to get events-to-cure, cost and the insolvency point.
- **Margin cure.** A minimum-impact cure solved by marginal-cost bisection in Decimal. It is used both for forced liquidation and as a draft for players. CVXPY appears only in tests, as an oracle.
- **Market generator.** `generate(seed, gen_version, skeleton) -> raw` uses a SHA-256-counter PRNG with Decimal-only factor and regime shocks. The seed stays server-side until the debrief. A tape is accepted only if the balance runner passes.
- **As-of tape.** `(instrument, event_time, available_at, revision, value)`. The view resolves the latest revision visible at the current clock.

### P5: Stretch, cut first

The 60-day season, Cases 2 and 3, staffing, world W6/W7, statsmodels attribution against true generator factors, and an optional ALFRED/EDGAR vintage fixture.

## What recruiters will see

| When | Artifact |
|---|---|
| End of P2 (about week 4) | Live URL, green CI, README GIF of the two-browser S2 game, `verify` returning a chain head, an ENGINEERING write-up on the verifiable ledger |
| End of P3 (about week 9) | Two avatars splitting up across two crises, a recorded playtest |
| End of P4 (about week 16) | A complete 60–90 minute game with seeds, five endings, a causal debrief and an independent shadow NAV |

Only numbers produced by tests or measurements are ever stated.

## Next task

P0: golden digests, the stateful Session property test, typed events, and the Python 3.13 pin with ruff and mypy.
