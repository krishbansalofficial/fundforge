# FundForge

FundForge is a desktop hedge-fund simulation built in **Godot 4**. You run a fictional $25m long/short fund through ten days of crisis. The prime broker recalls a borrowed short, margin terms tighten before a market shock, investors redeem, and the separate management company still has to make payroll. Five rival funds trade in the same market, and their forced selling moves your prices.

You can play solo with a deterministic **bot partner**, or with a friend as two partners. Either way, every number comes from a deterministic Python engine with PostgreSQL as the authority. Every dollar moves through an immutable, balanced journal, and every decision is a hash-chained command, so any finished game can be replayed and verified to the cent.

> **Trailer GIF: not recorded yet.** It will live at `docs/media/` once the scripted end-to-end run exists (see [PROGRESS](docs/PROGRESS.md)). Actual terminal captures and the implementation contract are in [Forge Terminal](docs/TERMINAL.md).

**No AI wrapper.** The game has no LLM in it. The bot partner (`bot:v1`) is a short rules policy in [`backend/src/fundforge/bot.py`](backend/src/fundforge/bot.py). It uses the same commands, role limits, digest signatures and mandate checks as a human, and every action it takes is logged and replayed like any other command.

## Features

- **Forge Terminal.** Press **T** for a keyboard-driven workstation: market monitor, observed price charts, signed portfolio exposure, hypothetical stress tests, published news, order blotter and rival rankings. Enter `BRIN GP` or switch functions with F1-F9. It reads the simulation's current/past data; trades still use the fund's approval rules.
- **Broker review challenge.** Select it in the Godot menu to investigate an incorrect cash statement. RISK shows dated evidence, linked corrections and an aged break queue. Unresolved discrepancies block new risk and redemption dealing; MP review preserves the original evidence. Independent broker cash and loan-fee calculations check the journal. [Scope and controls](docs/BROKER_CONTROLS.md).
- **Independent LP and fee checks.** RISK reconstructs series capital, daily management fees and performance provisions. Redemption payable, crystallized fee and surviving HWM are checked before units change. [Calculation boundary](docs/ADMINISTRATOR_CONTROLS.md).
- **Co-op evidence and analysis.** Role-specific private research with explicit sharing, attention-limited assignments, hypothetical liquidity/cure comparisons, completed-run causal replay, and independent execution/valuation checks. See [current implementation](docs/PROGRESS.md) for scope and remaining work.
- **A living fund office in 3D.** The office has a trading floor, committee room, risk and treasury, research library, management company and investor lounge, with the prime broker across the street and rival fund towers on the skyline. Each place is a terminal for that part of the job.
- **Real time with pause.** You can play at 1x, 2x or 4x, or pause. The clock pauses itself on every new notice, alert, research finding or unsigned package. Time moves only through logged clock ticks, so wall time never touches the economics.
- **Solo or duo.** Solo, you take one seat (portfolio manager or managing partner) and the bot takes the other. Duo, you share an invite code (`room:token`) with a second player.
- **Fund economics that are not a trading toy:**
  - three LP series, each with its own high-water mark, a reversible 20% performance provision and a 1.5% ACT/365 management fee;
  - borrow costs on ACT/360;
  - short proceeds held as restricted collateral;
  - a borrow recall with a deadline and a replacement-borrow offer;
  - stressed margin, and forced liquidation if a margin call goes uncured;
  - redemption dealing and payment;
  - a separate management company whose payroll investor money can never pay.
- **A mandate with teeth.** Gross, net and issuer limits are checked on every ticket, on every signature and again at every fill. A second partner's signature never overrides a hard limit.
- **Hidden market variants.** Each fund secretly draws its day-16 world, either a sell-off with a short squeeze or a broad rally. The draw is revealed only in the debrief, so no one line wins in every world.
- **Endogenous rival market.** Five rule-based rival funds trade on public marks. All order flow, yours included, leaves permanent price impact that decays over time, so squeezes, deleveraging and blow-ups emerge from the simulation.
- **Score and league table.** You get a Win, Survival or Distress tier, plus a score: your excess return over a passive copy of the opening book, minus a penalty for each forced action. You are also ranked against the rival funds.
- **Verifiable books.** You can verify the books from inside the game. Verification replays the room from its pinned tape and command log, then compares results, journal digests, the hash chain and a SQL trial balance.

## Architecture

```mermaid
flowchart LR
  subgraph Clients
    G1[Godot 4 desktop client<br/>Office3D, Actor3D, Hud]
    G2[Second player or bot seat]
    W[Next.js web desk<br/>secondary client]
  end
  G1 & G2 & W -- "poll GET /view (0.5 s)<br/>POST /commands + Idempotency-Key" --> API[FastAPI]
  CL[Clock loop<br/>system actor] -- "logged tick commands" --> API
  API --> ST[Store: one transaction per command<br/>row lock, idempotency, hash chain]
  ST --> S[Session: roles, packages,<br/>ready, clock, chat]
  S --> B[bot:v1 rules policy<br/>solo rooms only]
  S --> E[Engine: dated phases, execution,<br/>settlement, margin, accrual, dealing]
  E --> C[Compliance mandate]
  E --> M[Market: 5 rival funds,<br/>permanent impact, resilience]
  E --> J[Immutable balanced journal<br/>Decimal, HALF_EVEN]
  T[Pinned scenario tape + variant<br/>fixtures/case1.json] --> E
  ST --> PG[(PostgreSQL<br/>append-only commands<br/>journal_entries + journal_lines<br/>deferred balance trigger)]
```

Postgres stores the accepted commands and the journal they produced, never mutable game state. State is rebuilt by replaying the command log against the room's pinned tape, rules version and variant. The same inputs always give the same journal digest. Details are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quickstart

Prerequisites: Docker, plus [Godot 4.7.2](https://godotengine.org/) for the game client. Full setup is in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

```bash
docker compose up -d db api      # PostgreSQL on :5432, FastAPI on :8000 (SQL migrations apply automatically)
```

Then start the game. Either open `game/project.godot` in the Godot editor and press Play, or run:

```bash
godot --path game
```

There are no exported builds yet. Export presets are in progress.

On the menu (the server defaults to `http://127.0.0.1:8000`):

- **Solo:** choose *Play solo as portfolio manager* (the bot runs operations) or *Play solo as managing partner* (the bot trades).
- **Duo:** choose *Open a two-player fund*. Your partner's invite code (`room:token`) is copied to your clipboard. Your partner pastes it into *Join fund* on their machine, pointing *Server* at your API.

The older two-seat web desk still works: `docker compose up --build` also starts it at <http://localhost:3000>.

## Controls

| Input | Action |
|---|---|
| Left click | Walk to a point |
| Arrow keys | Walk relative to the camera |
| Right mouse drag | Rotate the camera |
| Mouse wheel | Zoom |
| `E` or `Enter` | Open the terminal of the location you are standing in |
| `Esc` | Close the terminal panel |
| `Space` | Pause, or resume at 1x |
| HUD buttons | Pause, 1x, 2x, 4x |
| `L` | Toggle the Street league table |

How to play, including the crisis timeline and scoring, is in [docs/GAME_GUIDE.md](docs/GAME_GUIDE.md).

## Evidence

All numbers below were observed at commit `7b066f2` on 8 October 2026.

| Suite | Command | Result |
|---|---|---|
| Backend, no database | `cd backend && uv run pytest -q` | 66 passed, 15 skipped (Postgres tests) |
| Backend, with Postgres | `DATABASE_URL=postgresql://fundforge:fundforge@localhost:5432/fundforge uv run pytest -q` | 81 passed |
| Game client, headless | `godot --headless --path game --script res://tests/run_tests.gd` | 35 checks ok, 0 failed |

Desktop builds (12 October 2026): `scripts/export_game.sh GODOT_BINARY Godot_v4.7.2-stable_export_templates.tpz [OUT_DIR]` verifies the official templates' SHA-512, exports self-contained Linux and Windows executables, and boots the Linux build headless. CI runs it on every push; running the workflow by hand also uploads both builds as artifacts for 3 days. Run a build against a server with `FundForge.x86_64 --server=https://your-host`. These are unsigned test builds: macOS needs signing and notarization, and a web build needs the Compatibility renderer, so neither exists yet.

What the tests cover:

- accounting oracles (HWM crystallization, provision reversal, cohort allocation, partial redemption, residual rounding);
- Hypothesis properties on the journal;
- committed golden journal digests for four scripted Case1 paths;
- a Hypothesis stateful model of random two-partner command sequences;
- a balance grid proving that flattening is refused and no policy dominates;
- rival-market behaviour;
- the bot partner;
- real-Postgres race tests (concurrent signatures, retries, ready and clock ticks);
- tamper detection by `verify`.

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs the backend against a Postgres service, the frontend audit, typecheck and build, and the Godot headless tests plus a boot smoke test. CI runs on GitHub. On 13 October 2026 the latest `main` run had failing `export` and `e2e` jobs; the fix (`ci: run background servers from the venv`) passed on branch `claude/handoff-phases-mms73g` and is not yet merged.

Performance: the engine benchmark (B1) runs a full Case1 season in about 17 to 18 ms (fastest of 50 samples) on a 2 CPU cloud machine, and the independent control report in about 0.5 ms. Method, machine and the other planned benchmarks (Postgres latency, API load, frame time, fault detection, balance) are in [BENCHMARKS](docs/BENCHMARKS.md); raw results are in `bench/results/`.

Engineering write-ups: [docs/ENGINEERING.md](docs/ENGINEERING.md).

## Repository map

| Path | Contents |
|---|---|
| `backend/src/fundforge/` | Engine, journal, series, execution, compliance, market, governance, bot, store, API, SQL migrations |
| `backend/tests/` | pytest and Hypothesis suites, `golden.json` and the balance `policy_grid.py` |
| `game/` | Godot 4 client: `scripts/` (Api autoload, WorldRules, Office3D, Actor3D, Hud, main), `tests/`, CC0 `assets/` with [CREDITS](game/CREDITS.md) |
| `frontend/` | Next.js landing page and the earlier two-seat web desk |
| `fixtures/case1.json` | The Case1 scenario tape: calendar, book, LPs, recall, research, notices, mandate, variants and rival funds |
| `docs/` | Guides, architecture, engineering, decisions, progress, the [roadmap](docs/ROADMAP.md) and the domain contracts. Superseded plans are in [`docs/archive/`](docs/archive/README.md) |
| `compose.yaml` | `db`, `api` and `web` services for local development |
| `deploy/` | Production stack (`compose.prod.yaml`: Caddy TLS, unpublished Postgres, non-root app containers, nightly verified backups) and `smoke.sh`, which CI runs |

## Status and limitations

FundForge is a playable vertical slice, not a finished game. See [PROGRESS](docs/PROGRESS.md) for the live state and [ROADMAP](docs/ROADMAP.md) for the plan.

- Only one scenario exists: Case1, days 12–21. The 30-day v1 campaign, research cards, LP agents and five endings are planned (ROADMAP P4).
- The other partner's avatar moves live over an authenticated WebSocket (cosmetic only; it never touches the books). Without the socket it falls back to walking to the place of their last decision.
- Research assignments now enforce role, location, per-role budgets and one assignment per decision window. Physical proximity is not required; signatures and mandatory remedies remain reachable.
- In progress: an independent shadow NAV, plus ruff and mypy tooling; exported builds; and a recorded trailer run.
- Not done: a public deployment (the production stack is written and smoke-tested locally and in CI, but nothing is hosted), music (sound effects exist and can be muted with M), recorded playtests.
- Everything is fictional. The tickers are invented (some collide with real symbols; renaming them is on the roadmap). There is no brokerage connection, no real money and no investment advice.
