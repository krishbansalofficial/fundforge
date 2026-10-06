# FundForge working rules

Read `docs/CLAUDE_HANDOFF.md` and `docs/PROGRESS.md` first. Read only the specification sections needed for the current task. Do not load the entire prompt pack or every installed skill on every turn.

Product: cooperative two-player educational paper-fund game, $100,000 virtual capital, one shared 15-minute daily session, 30-trading-day seasons. Backend accuracy and usable gameplay matter more than visual polish. No real money, brokerage execution, cash prizes, or paid investment signals.

Architecture defaults: Next.js/TypeScript frontend; FastAPI/Python modular backend; PostgreSQL source of truth. Start with fixtures and polling. Add Redis/workers/WebSockets only in the scheduled phase. Finance domain code is independent of network and UI.

Non-negotiables:
- Use Decimal/fixed precision for financial arithmetic and explicit rounding; no float balances.
- Exactly two active managers; proposer cannot approve their own order.
- Approval binds to immutable proposal contents and version. A change requires new approval.
- Revalidate risk at execution; serialize competing ledger changes in PostgreSQL.
- Unique idempotency keys plus DB transactions; do not promise exactly-once message delivery.
- Approved orders execute only at a later eligible event, never at a already-known close.
- Ledger entries balance, replay deterministically, and reconcile with materialized state.
- Preserve event time, availability time, feed, adjustments, and dataset versions.
- No future data in historical gameplay, training, or backtests.
- LLMs explain verified facts; they do not own balances, fills, risk limits, or approvals.
- No invented metrics, completed milestones, test results, or compliance claims.
- Use synthetic/public permitted fixtures; secrets stay server-side and out of Git.

Work in small contracts: scope, allowed paths, behavior, acceptance evidence, done condition. Inspect before editing. Use rg and narrow file reads. Run relevant checks once; broaden when a failure or changed boundary requires it. Stop after two failed repair cycles and write a precise blocker.

Installed Vercel skills: inventory names/descriptions once and record relevant skills in `docs/DECISIONS.md`; load at most one or two pertinent skills per task. Do not reinstall everything, read all skills, redesign the product, or substitute skill conventions for financial invariants. Verify tool/model/agent syntax against the installed Claude version.

Agent default: one builder. At most one bounded reviewer on high-risk changes. No recursive delegation, autonomous debate loops, or full-team architecture recreation. Read-only reviewer findings require a reproduction or precise invariant. Separate worktrees for concurrent writers.

At task end update `docs/PROGRESS.md` with branch/commit, changed paths, commands and actual results, unresolved risks, and one next task. Keep it under roughly 800 words. Commit only task-related files when instructed. Never force-push, change repo visibility, deploy publicly, enable extra paid usage, or add real-money capability without an explicit request.
