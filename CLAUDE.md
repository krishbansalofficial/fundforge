# FundForge working rules

Read `docs/CLAUDE_HANDOFF.md` and `docs/PROGRESS.md` first. Canonical design is v2.1. Read only documents needed for the bounded task; generated combined documents are not separate authorities.

Product: two-player cooperative hedge-fund management game. Default fictional campaign: $25m outside capital, separate $300k management company, 60 simulated business days, six chapters. LPs, long/short financing, fund versus firm accounting, fees, investor flows, governance and crises are core release mechanics. A trading-only demo is not a completed game. No real money, brokerage execution, cash prizes or paid investment signals.

Architecture: Next.js/TypeScript; FastAPI/Python modular backend; PostgreSQL authority; pure finance/game domain. Fixtures and polling first. Add queue/cache/WebSockets only for a demonstrated boundary.

Non-negotiables:
- Decimal/fixed precision with explicit rounding; immutable balanced journal and deterministic replay.
- Exactly two human partners. Delegated sleeve actions require a valid jointly approved mandate; material exceptions require distinct human consent. No self-approval of exceptions or hidden AI substitutes.
- Approvals bind to immutable contents, policy version, expiry and scope. Revalidate current risk and authority at execution.
- Fund, LP series and management-company capital are separate. AUM, fees receivable and restricted short proceeds are not spendable firm cash.
- Unique economic identities, idempotency keys, serialized fund transactions and atomic journal/state/outbox effects.
- Execute only at a later eligible market event; never at a known historical close. Daily bars do not prove intraday order paths.
- Preserve event time, available_at, data/rules versions and all revisions. No future information in player APIs, exports, research, AI or backtests.
- Financial, deadline and NPC state is computed by versioned rules; LLMs cannot own fills, balances, fees, risk, approvals or rankings.
- No invented completed milestones, metrics, tests, security/compliance claims or source provenance.
- Synthetic fixtures remain usable without external services. Secrets stay server-side; paid provider use requires prior authorization and caps.

`docs/FUND_ACCOUNTING.md` owns financial conventions; `docs/GAME_SYSTEMS.md` owns game rules; `docs/MASTER_SPEC.md` owns product boundaries; `docs/SIMULATION_ARCHITECTURE.md` owns software interfaces. `docs/REALISM_AUDIT.md` identifies design risks; `docs/LIBRARY_RESEARCH.md` records dependency evidence. If they conflict, resolve and document before implementation. House rules are not universal industry conventions. Opening series participation adds back reversible performance provisions; remaining HWM is unchanged on partial redemption; every calendar date accrues stated ACT/365 or ACT/360 costs. Never restore v2.0 /252 fee accrual or chapter performance crystallization.

Work by explicit objective, owned paths, contracts and acceptance evidence. Inspect before editing; use rg. Run meaningful checks for changed risks. After two unsuccessful repair cycles, preserve the exact failure and choose a narrower diagnosis rather than repeat the same attempts. Do not invent a CLI command or supported model name.

Default one builder; use a bounded reviewer only when authorized. No recursive delegation. The owner explicitly requested Astra/extra-high for this v2.1 design review; that is not standing authorization for unlimited agent teams. Inventory installed relevant skills once, load only applicable guidance.

At task end update `docs/PROGRESS.md` with actual state, paths, checks, limitations and one next task. Commit only task-related files when authorized. No force-push, visibility change, public deployment, paid usage or real-money capability without explicit authorization.
