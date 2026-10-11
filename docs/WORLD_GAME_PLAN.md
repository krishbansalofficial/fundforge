# World game plan: two partners in a fund office

8 October 2026. Planning document, not a record of completed work. It was written for a 2D Phaser client; the owner later chose a Godot 4 3D desktop client (see [DECISIONS](DECISIONS.md) and [ROADMAP](ROADMAP.md) P3), so read the places and rules here, not the rendering choices. It adds a graphical, shared-world layer (milestones W1–W7) on top of the deterministic game described in [FULL_GAME_PLAN](archive/FULL_GAME_PLAN.md). Money, time and outcomes stay with `engine.py`, `governance.py` and the Postgres command log (`store.py`). Game rules stay with [GAME_SYSTEMS](GAME_SYSTEMS.md), Case1 schedule with [SCENARIO_CONTRACTS](SCENARIO_CONTRACTS.md). Nothing in this plan changes an economic rule. Where it touches one, §9 lists it.

Owner request: "I need a graphical game, not just a very basic game. I need two players playing a game in a world." Constraint: no AI wrapper, real engineering, one builder at about 15 h/week.

## 1. Concept and fantasy

**Fantasy.** You and one friend run a small hedge fund from a cramped office in a pixel-art financial district. You walk between rooms, read the letters that arrive, meet across the committee table to sign, and watch the market board go red. The numbers underneath are the same audited Decimal ledger as the desk. The world is how you live in it.

**View.** Top-down 2D pixel art (16 px tiles, 3x integer scale), one Tiled map about 48x32 tiles: an office floor plus the street outside. Top-down is cheaper than isometric to author, collide and test, and Kenney's CC0 packs are top-down.

**Places** (each maps to commands and `/view` fields that exist today; see §2):

| Place | Who works there | What it does | Backed by |
|---|---|---|---|
| Trading floor | PM | Ticket terminal, cancel, market board with marks, fills ticker | `ticket`, `cancel`, `view.marks`, `view.orders` |
| Risk room | Both | Wall of gauges: gross, net, maintenance headroom; lights go red on a margin call | `view.fund.*`, `margin_call` |
| Committee room | Both, together | Table where packages are drafted, carried and signed | `propose`, `sign`, `view.packages` |
| Research library | Either | Shelf of topics; a chosen book arrives at the next PUBLIC_MARK | `research`, `view.research`, research notices |
| Prime broker office (across the street) | MP | Broker NPC, recall letters, replacement-borrow offer | `accept_replacement`, `view.recall` |
| Treasury vault | MP | Two separate safes: the **fund** (cash, restricted collateral, reserve) and the **management company** payroll safe | `set_reserve`, `view.fund`, `view.firm` |
| LP café | MP | Investor NPCs; redemption requests, dealing results | notices, `view.series` |
| Lobby clock and bell | Both | Phase clock, day/night; ringing your bell is `ready` | `ready`, `view.clock`, `view.ready` |

The two safes are the point: subscriptions, AUM, fee receivables and restricted short proceeds visibly cannot be walked into the payroll safe. Fund versus firm separation becomes a physical layout, not a footnote.

**World time.** The phase clock is the only clock. `view.clock.phase` sets lighting: OPEN_ADMIN dawn, PUBLIC_MARK 09:30 morning, EXEC_A 10:00, EXEC_B 15:00 afternoon, CLOSE 16:00 dusk, weekends a short night fade. Real seconds never move simulated time. The world idles at a barrier until both bells ring, exactly as `Session._cmd_ready` already requires.

**Crises in the world** (all derived from `/view` after the engine publishes them, never from the tape):

| Engine state | What you see |
|---|---|
| Recall notice (`recall.open`) | Broker's courier walks from across the street to the lobby with a sealed letter; letter shows quantity and deadline event |
| Replacement offer visible (`recall.offer_visible`) | Broker NPC gains a "!" and offers terms; acceptance window shown as a stamp "valid until day 14 EXEC_B barrier" (from the notice text) |
| Price shock at PUBLIC_MARK | Market board flashes, affected tickers turn red, risk-room gauges swing |
| `margin_call` set | Risk room alarm light, red tint on the floor, "Freeze risk additions" placard on the PM terminal |
| Redemption request / dealing | An LP knocks at the café door; after CLOSE dealing they leave with a cheque for the certified amount |
| Halt (zero volume / halted instrument in view) | BEAM tile on the board shows HALTED tape |
| Forced action (`view.incidents`) | Broker courier returns with a buy-in confirmation; incident pinned to the risk-room wall |

**Asymmetric roles.** `governance.ROLES = ("pm", "mp")`. The PM owns tickets and lives on the trading floor and in the library. The MP owns replacement borrow, reserve and investors, and lives across the street, in the vault and the café. Packages need both at the committee table. In Case1 the day-14 barrier is the set piece: the MP must be at the broker to accept or refuse the 40% replacement, while the PM drafts a reduction package, and both must then meet to sign it before the bell. Role ownership is not secrecy (GAME_SYSTEMS §1): any partner can read any screen, but only the owner's place offers the action.

**NPCs** are deterministic. Dialogue is authored templates in `frontend/world/dialogue.ts`, keyed by notice `kind` and view fields, quoting the engine's notice text verbatim. No LLM, no free text generation, no NPC state outside the engine.

## 2. Core loop on engine phases and barriers

`Engine.advance()` runs OPEN_ADMIN, PUBLIC_MARK, then stops at the barrier before EXEC_A; the next `ready` pair runs EXEC_A and stops before EXEC_B; the next runs EXEC_B, CLOSE, and the next day's OPEN_ADMIN and PUBLIC_MARK. The world plays the gap as a short cutscene built from the view diff (new notices, fills, clock), then hands control back.

| Step | Engine | PM in the world | MP in the world |
|---|---|---|---|
| Dawn (OPEN_ADMIN) | Settlement, transfers, admin notices | Sees mail on desk | Courier/LP arrivals, vault balances update |
| 09:30 PUBLIC_MARK | Marks, research reveals, shocks | Board updates, research book delivered to library | Risk gauges move; letters in lobby |
| **Barrier before EXEC_A** | Commands accepted | Ticket at terminal (within 5% NAV / 15% turnover), or draft a package | Accept replacement at broker, set reserve in vault, visit LP |
| Meet to sign | `propose` then `sign` | Both stand in committee room; non-proposer signs | |
| Bell | `ready` x2 | Ring bell | Ring bell |
| 10:00 EXEC_A | Fills, forced actions | Fills scroll on the ticker | Incidents pinned to risk wall |
| **Barrier before EXEC_B** | Same as above | | |
| 15:00 EXEC_B, 16:00 CLOSE | Fills, accruals, fees, dealing | Dusk; board freezes | LP leaves with cheque; payroll safe pays on payroll days |

**Meet to sign.**
1. A partner drafts a package at their place (PM terminal or committee table). The client sends `propose` through the existing API with an idempotency key. The engine returns a digest; a paper document prop appears in the proposer's hands showing the legs and the first 8 hex of the digest.
2. The proposer carries it to the committee room and drops it on the table. A package is valid only until the next execution event (`expires = cursor + 1`), so the document shows "void after EXEC_A".
3. When both avatars are inside the committee-room zone, the non-proposer presses E at the table. The modal shows the full digest from `view.packages`, the legs and the expiry. "Sign" sends `sign` with that digest. Self-signing is impossible because the engine rejects it, not because the world hides the button.
4. The document gets two wax stamps; the PM terminal shows the queued orders.

Proximity is a **client affordance**, not a server rule: the API stays location-agnostic so desk mode and replay work and positions can never change the journal (§4). The trade-off is stated in §7.

## 3. Technology choice

**Pick: Phaser 4 (`phaser@4.2.1`) in a client-only Next.js route, React DOM overlays for every form, Tiled JSON maps, Kenney CC0 art.**

Checked on 8 October 2026 with `npm view`:

| Package | Latest | Notes |
|---|---|---|
| `phaser` | 4.2.1 (published 2026-07-09; 4.0.0 on 2026-04-10; 3.90.0 on 2025-05-23) | MIT, one runtime dependency (`eventemitter3`) |
| `pixi.js` | 8.22.0 | MIT; renderer only |
| `@pixi/react` | 8.0.5 | peers `pixi.js ^8.2.6`, `react >=19` |
| `three` / `@react-three/fiber` | 0.186.1 / 9.8.1 | 3D |
| `@playwright/test` | 1.64.0 | e2e and pure TS tests |

Pin exact versions in `package.json` at W1 and re-run `npm view` then; do not trust these numbers past this date. `phaser` unpacked is about 112 MB on npm (sources, types, builds); the shipped chunk size must be measured in W1, not assumed.

**Why Phaser.** It ships what a top-down world needs and a solo developer should not write: Tiled tilemap loader, arcade physics and tile collision, cameras, input with keyboard mapping, sprite animation, scene lifecycle, audio. That keeps W1 at two weeks.

**Rejected.**
- **PixiJS + @pixi/react.** Better React integration, but it is a renderer: tilemaps need `@pixi/tilemap` or custom code, plus hand-written collision, input and camera. More code for no player-visible gain.
- **Three.js / R3F.** 3D art, lighting and camera work are the largest time sink for a solo builder and add nothing to a two-person office game.
- **Godot web export.** Good editor, but a second language and toolchain, a multi-megabyte WASM payload, awkward bridging to the existing React panels and API client, and weaker Playwright testability. It also hides the TypeScript/React work recruiters can read.
- **Phaser 3.90.0.** More tutorials, but 4.x is the maintained line. Fallback if a Phaser 4 blocker appears in the W1 spike; record the switch in PROGRESS.

**Embedding.** New route `frontend/app/room/[id]/world/page.tsx` loads `WorldCanvas` with `next/dynamic(..., { ssr: false })`, so the landing page and desk bundles do not grow. `WorldCanvas` creates the `Phaser.Game` in `useEffect` and destroys it on unmount. React keeps owning the view: the existing `/view` fetch and `send()` from `desk.tsx` are moved into a shared hook (`frontend/app/room/[id]/useRoom.ts`) used by both desk and world. React pushes each new view into the scene through one event (`game.events.emit("view", v)`); the scene emits `interact` with a zone id and React opens the matching overlay. That is the whole bridge, one file: `frontend/world/bridge.ts`.

**Overlays are DOM, not canvas.** `Actions`, `Positions`, `Feed`, the approvals panel and the ledger in `desk.tsx` are exported and rendered as modal "terminals" over the canvas. Same forms, same validation, same accessibility, zero duplicated money formatting.

## 4. Realtime architecture

**Boundary demonstrated.** `desk.tsx` polls every 1.5 s ("no socket until it isn't"). Showing your partner walking needs about 10 updates per second between two browsers; polling `/view` cannot do that. That is the demonstrated boundary CLAUDE.md asks for. Economic state does not move to the socket.

```
browser (React + Phaser) --HTTP POST /commands (idempotency key)--> governance -> engine -> Postgres log
        ^       |                                                                  |
        |       +--WS /api/rooms/{id}/presence  pos 10 Hz (ephemeral) --+           |
        |                                                               v           |
        +------ peer positions, "view_changed" nudges <------ presence hub (in memory) <-- after commit
        +------ GET /view (authoritative) on nudge, and as polling fallback
```

**Server.** `backend/src/fundforge/presence.py`, a FastAPI WebSocket route in the existing app (`uvicorn[standard]` already brings a WebSocket implementation). An in-memory dict `room_id -> {role: (socket, last_state)}`. It never imports `engine`, `governance` or `store`'s command path; it only calls `store().auth` once per connection. After `POST /commands` commits, `api.py` calls `hub.nudge(room_id)`, which sends `{"t":"view_changed"}`; clients refetch `/view`. Lost nudges are harmless because polling stays on at a slower 5 s interval.
`# ponytail: in-process hub needs a single API worker; add Postgres LISTEN/NOTIFY when running more than one.`

**Protocol** (JSON, validated with pydantic, max 256 bytes per message):
- Client: `{"t":"hello","token":...}` (first message, within 2 s, else close 4401); then `{"t":"pos","x","y","dir","zone","seq"}` at most 10/s; `{"t":"seen","notice":index}`.
- Server: `{"t":"peer","role","x","y","dir","zone","ts"}`, `{"t":"peer_left"}`, `{"t":"seen","role","notice"}`, `{"t":"view_changed"}`.
- The server stamps `role` from the authenticated seat; a client cannot speak for its partner. Coordinates are clamped to map bounds. Over 15 messages/s or oversized frames: drop, then close 4408 on repeat.

**Seat-token security.** The token never goes in the WS URL (URLs land in proxy logs); it is sent in the `hello` frame and checked with the same hashed lookup as HTTP. The upgrade checks `Origin` against an allowlist. A seat from another room or a revoked seat is closed 4403. After G8 replaces bearer links with an HTTP-only cookie, the cookie rides the upgrade request and `hello` carries no secret.

**Latency and reconnection.** Local avatar moves immediately (client authority over its own ephemeral position is fine; nothing is at stake). The peer is rendered 100 ms behind using linear interpolation between buffered snapshots; snap if the gap exceeds 3 tiles. Reconnect with exponential backoff (0.5 s to 8 s, jitter), resend `hello` and current position. The peer becomes a translucent "away" ghost after 3 s of silence. Presence loss never blocks play: commands are plain HTTP.

**Determinism guard.** No position, zone or `seen` flag is persisted, sent to `/commands`, or read by `engine`/`governance`. Tests in W2 enforce this (§6).

**Information boundary.** World props are computed by a pure function `deriveWorld(view) -> WorldState` in `frontend/world/deriveWorld.ts`. The view is already as-of (built only from processed events). The client contains no case schedule: no hard-coded "day 16 shock" or "BEAM halt day 20"; props react to notice kinds and view fields only. A W4 test greps the built world chunk for tape-only fixture keys.

## 5. Art, audio, accessibility and budgets

**Art (no custom drawing in core).** Kenney.nl top-down CC0 packs (for example the modern city/roguelike packs for the street and office, a character pack for avatars and NPCs, the UI pack for the document and stamps). At download, copy each pack's own license file and record pack name, URL, version/date and license in `frontend/public/world/LICENSES.md`; do not assume CC0 for any pack without its file. Maps are authored in Tiled and exported to JSON (`frontend/public/world/office.json`) with layers `ground`, `walls` (collision), `props`, and an object layer `zones` (rectangles named `trading`, `risk`, `committee`, `library`, `broker`, `vault`, `cafe`, `lobby`). Tint the two avatars per role. Programmer art is acceptable through W3.

**Audio.** Kenney CC0 interface/impact sounds: bell, stamp, paper, board click, alarm. Off by default, toggle in the HUD, no music in core.

**Accessibility.**
- Arrow keys/WASD to move, E to interact, Esc to close, Tab cycles visible hotspots; a "Go to" menu (keys 1–8) walks or, with reduced motion, teleports the avatar to a place.
- Overlays are the existing semantic DOM panels with focus trapping. The canvas is `aria-hidden`; an `aria-live` region announces world events ("Your partner entered the committee room", "Courier delivered a recall letter").
- `prefers-reduced-motion`: no screen flash or shake; red state shown by a static border and text.
- **Desk mode** stays a first-class route (`/room/[id]`), one click from the world HUD. Same commands, same rules; the game is fully playable without the canvas.

**Budgets** (targets, checked in W5):
- 60 FPS at 1280x720 on an integrated-GPU laptop; never below 30 FPS during a cutscene.
- World route JS chunk measured in W1 and capped at that figure plus 10% by a CI size check; landing and desk bundles unchanged.
- Assets under 2 MB total (PNG atlases, OGG/MP3 audio), loaded only on the world route.
- Presence traffic under 2 KB/s per client.

## 6. Milestones

Slotted after G8 (hardening, cookie session auth, recorded playtest) and the first public deploy, so the world sits on a stable, authenticated API. W1–W5 use only commands that exist today in Case1, so they do not depend on G2–G7 content. Owner option: run W1–W5 before G2 instead if a visible game matters more than season depth for hiring; record that choice in PROGRESS. Deploy target must support WebSockets on the API host (the static/Next host does not carry the socket).

| ID | Goal | Weeks | Class |
|---|---|---|---|
| W1 | World shell: map, avatar, zones, terminals as overlays | 2 | core |
| W2 | Presence: WebSocket, peer avatar, nudge, determinism tests | 2 | core |
| W3 | Committee room, documents, bell, day/night | 2 | core |
| W4 | Crises, NPCs, seen-notices, information-boundary test | 2 | core |
| W5 | Accessibility, audio, budgets, GIF capture | 1 | core |
| W6 | Season world: LP offices per series, staff and payroll for G5, chapter transitions | 2 | stretch |
| W7 | Replay theater: re-render a finished game's world from its command log | 2 | stretch |

Core: 9 weeks (about 135 h). Stretch: 4 weeks.

### W1 World shell (2 weeks, core)
- **Files:** `frontend/package.json` (`phaser`, `@playwright/test` exact pins), `frontend/app/room/[id]/world/page.tsx`, `frontend/app/room/[id]/useRoom.ts` (polling and `send` extracted from `desk.tsx`), `frontend/world/{WorldCanvas.tsx,scene.ts,bridge.ts}`, `frontend/public/world/{office.json,*.png,LICENSES.md}`, `frontend/e2e/world.spec.ts`, `frontend/playwright.config.ts`.
- **Acceptance:** Playwright (one context, keyboard only) walks to the trading floor, opens the terminal, submits a ticket, and the order appears in `/view`; the existing desk route still works with the shared hook; a test-only hook `window.__ffWorld` (compiled out of production) exposes avatar position for assertions; measured world chunk size and FPS recorded in PROGRESS.

### W2 Presence (2 weeks, core)
- **Files:** `backend/src/fundforge/presence.py`, `api.py` (route plus `hub.nudge` after commit), `backend/tests/test_presence.py`, `frontend/world/net.ts`.
- **Acceptance (pytest, FastAPI `TestClient` websockets):** missing or late `hello` closes 4401; another room's seat and a revoked seat close 4403; a forged `role` field is overwritten; 30 msgs/s is throttled; oversized frames dropped. **Digest invariance:** run the Case1 S1 command script twice, once with no sockets and once with two sockets streaming random positions and `seen` events between every command; the journal digest, `ledger()` and `view()` are byte-identical. An import-boundary test asserts `presence.py` imports no engine/governance module. Playwright with two browser contexts: each sees the other avatar move within 300 ms on localhost; killing one socket shows the ghost, reconnect restores it.

### W3 Committee room and documents (2 weeks, core)
- **Files:** `frontend/world/{documents.ts,committee.ts,daynight.ts}`, overlay for the package document, lobby bell.
- **Acceptance:** Playwright two contexts: PM drafts a BEAM/BRIN reduction package at the terminal, carries it to the committee room, MP walks there; "Sign" is disabled until both are in the zone; MP signs; both ring bells; after EXEC_A the fills show on the board and in `/view`. The same command sequence sent through desk mode yields the same journal digest (the world adds no commands). A package left unsigned turns "VOID" after the bell, matching `EXPIRED` in the view. Lighting follows `view.clock.phase`.

### W4 Crises and NPCs (2 weeks, core)
- **Files:** `frontend/world/{deriveWorld.ts,npcs.ts,dialogue.ts,cutscene.ts}`, `frontend/world/deriveWorld.spec.ts`, view snapshots captured from scripted Case1 runs into `frontend/e2e/fixtures/`.
- **Acceptance:** `deriveWorld` unit tests over snapshots from S1, S2 and F1: courier appears only once the recall notice exists; risk alarm iff `margin_call`; HALTED only after the halt is published; incidents pinned after forced buy-in in F1. Leak test: the built world chunk contains no tape-only keys from `fixtures/case1.json` (hidden schedule, `accept_by_day`, future marks). Every NPC line is a template from `dialogue.ts`; a test fails on any notice kind without a template. "Seen" eye icons appear when the partner opens a letter and are gone after a server restart (ephemeral by design).

### W5 Polish and evidence (1 week, core)
- **Acceptance:** a keyboard-only Playwright run completes Case1 S1 in the world; reduced-motion run has no flash; CI size check on the world chunk; FPS sample recorded; audio toggle persists per viewer; three GIFs recorded (§8) and linked from README.

### W6, W7 (stretch)
W6 grows the map as G4–G7 land: one LP office per series with deterministic concern states, management-company staff desks and a payroll safe that empties visibly in distress (G5), chapter-close transitions. W7 replays a finished room's command log through the engine and renders the world at each event (no positions exist, so avatars stand at each command's owning place), a debrief GIF generator.

## 7. Risks and how the world earns its place

| Risk | Mitigation |
|---|---|
| **The world is a skin over forms** | Each place owns a real authority (only the MP's places offer `accept_replacement`/`set_reserve`; only the committee table offers `sign`). Signing needs both bodies in one room. Documents carry the real digest and expiry. Two physically separate safes teach fund versus firm. Information is spatial: letters land in the lobby, research books in the library, and the partner's "seen" eye shows who has actually read the recall. If the W3 playtest shows players ignoring places, shrink the map before adding features. |
| **Art and content time** | Kenney packs only, one map, no custom animation in core; programmer art allowed through W3; art changes timeboxed to 3 h per week. W6/W7 are dropped first. |
| **Scope creep (chat, emotes, more rooms, avatars)** | No text chat (players talk out of band; avoids moderation). No avatar customisation beyond role tint. New rooms only when an engine command needs a home. |
| **Proximity is client-side** | Deliberate: server-enforced proximity would make ephemeral positions economic and break replay and desk mode. A determined player can sign from desk mode; that is an accessibility feature, documented, not a bug. |
| **"Travel time" temptation** | Rejected: charging phase budget for walking would let movement change economics, and GAME_SYSTEMS has no speed bonus. Pressure comes from authority and sequencing (MP at broker, PM drafting, both at table before one bell), and from assignments that already exist. |
| **Realtime ops** | Single worker hub with polling fallback; deploy host must support WebSockets; presence failure degrades to "partner away", never to wrong money. |
| **Canvas e2e flakiness** | Drive and assert through the test hook and DOM overlays, not pixels; fixed timestep in test builds. |
| **Phaser 4 maturity** | W1 spike day 1–2; fallback to 3.90.0 recorded if blocked. |

## 8. What recruiters see

**GIF moments.**
1. Two avatars walk into the committee room; the reduction package lands on the table with a hash stamp; the second partner signs; the bell rings and dawn breaks into fills on the board.
2. Day 16 at 09:30: the market board flashes red, the risk-room alarm lights, and the broker's courier crosses the street with a letter.
3. Toggle from world to desk mode mid-game: same numbers, same pending package.
4. An LP leaves the café with a cheque after dealing while the payroll safe next door stays untouched.

**Systems story** (one diagram in README, from §4): realtime presence is ephemeral, best-effort and tested to be economically inert; money flows only through idempotent, digest-approved commands into a deterministic engine and an append-only Postgres log that replays to the same digest. Evidence to link: the digest-invariance test, the two-context Playwright signing test, the WS auth tests and the information-leak test. Claims stay limited to what those tests show.

## 9. Touch points with existing documents

- `desk.tsx` comment "no socket until it isn't": W2 adds a socket for presence and view nudges only; polling remains the fallback and the authority path is unchanged.
- G8 session auth: W2 ships the `hello`-frame token first and switches to the cookie when G8 lands. If W runs before G8 (owner option in §6), keep the `hello` path and its tests.
- GAME_SYSTEMS §1 (no speed bonus, pauses change waiting time only) is preserved: the world never advances simulated time on its own.
- PROGRESS.md is not updated by this planning document; the next builder records the chosen slot (after G8, or before G2) and the W1 measurements there.
