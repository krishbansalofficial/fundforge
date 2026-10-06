# Implementation plan

Build one vertical slice and expand it through correctness gates. Timing depends on the owner's experience, subscription capacity and debugging; the complete backend + ML + advanced simulator is not a one-week promise. M0–M4 form a realistic first-release objective across multiple focused sessions. Later stages can take several additional weeks.

| ID | Task / owned areas | Depends on | Observable completion |
|---|---|---|---|
| M0 | Repo/tool skeleton; `frontend/`, `backend/`, CI, fixture contract | Initial review | Clean install, basic health route/page, minimal checks from a fresh checkout |
| M1 | Domain money, units, FIFO lots, double-entry ledger, settlement; `backend/domain/`, domain tests | M0 | Golden arithmetic and replay/reversal tests pass |
| M2 | PostgreSQL migrations/repositories, proposals/versions/approval/reservations, membership auth | M1 | Two manager identities; no self-approval, stale approval, duplicate fill or overspend |
| M3 | Fixture clock/calendar, next-open execution, risk gates, snapshot/reconciliation jobs | M2 | One full simulated daily close/open cycle; safe failures on gaps and passive breaches |
| M4 | Five-screen playable UI and session timer, initial lessons/report; polling | M3 | Two people can complete a 30-day fixture season; mobile/keyboard/error states work |
| M5 | Data-provider adapter, rights checklist, source/availability metadata, split/dividend events | M4 | Licensed or permitted frozen dataset; action accounting verified; no synthetic/live confusion |
| M6 | Transactional outbox, robust worker, Redis cache/rate limiter, optional WebSockets | M3/M5 | Crash/retry/reconnect evidence; PostgreSQL still authoritative |
| M7 | Security/load/recovery/observability and deployment documentation | M4/M6 | Cross-fund tests, backup restore, measured load and two-user demo in intended environment |
| M8 | Shared-engine research backtesting and historical as-of APIs | M3/M5 | Deterministic replay, leakage tests, cost sensitivity and baseline report |
| M9 | Regime baseline/HMM features, chronological evaluation, MLflow and release manifest | M8 | Reproducible evaluation; justified gate promotes or rejects candidate |
| M10 | Batch inference, model monitoring/fallback, tutor templates and optional API | M9 | Model version/as-of visible; failure and explanation evaluation documented |
| M11 | Bounded AI-opponent contest and advanced fund procedures | M7/M8/M10 as applicable | Same rules/information for all; capped requests; extension-specific accounting tests |

## M0: narrow scaffold

Create a minimal monorepo with shared documented contracts, not a full generated application. Pin supported runtime versions and dependencies after inspecting current official docs/tool availability. Use one Python package manager and one frontend package manager, committed lockfiles, lint/type checks, Docker Compose for development PostgreSQL, and a minimal CI pipeline. Do not add paid cloud infrastructure or production secrets.

Create the financial-domain interfaces and identify where invariants will live. A static health page is enough; no dashboard redesign. Decide authentication integration and development test identities without inventing insecure production login shortcuts. Proposed developer commands must be added and validated before being listed as working commands.

## M1: financial domain before persistence details

Implement Decimal money/pricing policy, capital units, FIFO lots, journal postings, mark-to-market, trade-date receivables/payables and settlement. Use isolated domain tests plus the provided golden fixture. Make the ledger explicit enough to reconcile realized/unrealized P&L, cash and holdings. Define rounding and correction/reversal semantics. No LLM, external prices or frontend writes can bypass this module.

## M2–M3: hardest backend gates

Freeze the proposal contract and transition table before frontend integration. DB schema changes have one owner. Put approval, reservation, fill, journal and outbox effects within the relevant transaction boundaries. Test races with an actual PostgreSQL service, not SQLite's different lock behavior. Serialize fund operations and document worker retry behavior.

Implement a Clock interface used by session deadlines and event eligibility. Simulated clocks only exist in development/test or an authorized historical season. Users cannot supply authoritative clock values. Every execution uses a coherent execution snapshot for all holdings needed to compute NAV/exposures. Missing essential marks cause a block, not a valuation assembled from arbitrarily mixed timestamps.

Use a single cost configuration and settled-cash policy in game and backtests. Reservations convert atomically into obligations or are released, never both counted indefinitely. Reconciliation failure freezes trading until an explicit correction succeeds.

## M4: enjoyable first release

Deliver lobby, fund desk, trading room, research stub and season report with fixture data. The research stub can explain that automated backtests arrive later rather than presenting a fake result. Add short reviewed lesson cards for position sizing, market orders, diversification, settlement and drawdown. Complete session state and failure-state UI before extra colors/animation.

Manual usability check: two testers join, start, propose, approve, advance to fill, disagree/cancel, hold one day, and finish a season. Capture confusing states and fix the action language. Do not invent real user counts if testers are only the owner and a friend.

## M5–M7: measured service reliability

Choose one provider after checking rights and coverage. Keep the fixture mode. Add corporate actions and dataset freezes before importing long histories. Use worker retries, transactional outbox and client resynchronization. Redis must be rebuildable after loss. Record log/metric names around queue delay, job age, fills/rejections, dedupe, data staleness, reconciliation and API errors.

Load plan: document hardware/container limits; start with 10 active funds, then 50 and 100 if the system permits. Submit competing approval/execution operations, portfolio reads and reconnects under a stated mix. Measure p50/p95/p99, errors, lock waits and invariant outcomes; select a supported load target after measuring. These concurrency levels are experiment inputs, not production claims. Restore a backup into a separate database and reconcile the restored ledger.

Deployment must use a hosting choice explicitly selected by the owner and verified secrets/configuration. Preparing deployment files is authorized; public publishing and additional paid resources are separate requests. A private repository does not make a hosted app private automatically.

## M8–M10: worthwhile ML

Reuse the domain engine for research. Lock data/splits, calculate baseline performance and failure cases, then train HMM. Register experiments, but only promote a candidate if the defined gate is met. A baseline-only serving system with an honestly rejected HMM is stronger than a misleading deployed model. Keep the ability to revert a model without rewriting historical predictions.

Add template explanations first. The optional LLM tutor uses bounded verified inputs, no trading tools and no external historical browsing. Record actual explanation evaluation and request cost separately from subscription use. Do not enable API billing merely because Claude Code is logged in.

## M11: extension discipline

AI fund opponents, fees, redemptions, shorts/margin and derivatives are independent extensions. Select at most one next extension. Write its accounting, event, data and acceptance contract before code. The advanced roadmap is a menu, not permission to add everything to an MVP.

## Session operating rhythm

Start: read small handoff, Git state and task contract. Work: inspect only dependencies and owned paths, implement, run appropriate checks. Finish: evidence, commit only when instructed, update small handoff. At integration milestones run broader checks. After two repair cycles without progress, checkpoint the precise failing condition and ask a narrower expert question in the next session.
