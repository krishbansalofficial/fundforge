# Claude handoff — start here

## Current state

This repository contains a specification, prompts, acceptance cases, review-agent definitions, and private-repository creation scripts. There is no frontend, backend, database, market-data subscription, model, deployment, or measured application result yet. The private repository is now available at https://github.com/krishbansalofficial/fundforge; repository setup is complete. The standalone setup scripts were not used for this upload. Treat every implementation milestone as pending.

The owner wants a strong new-grad backend and AI/ML project, modest polished UI, cooperative gameplay, realistic simulated fund procedures and backtesting, and careful Claude usage. The owner reports having Vercel skills installed locally; this package has not inspected them. Do not infer specific installed skill names or that all skills should be loaded.

## First-session instruction

Think carefully about this design before writing code. Inspect the actual repository and environment, then review the specification for contradictions, scope risks, missing financial mechanics, data leakage, and unrealistic claims. Give decision rationale and evidence; do not narrate private chain-of-thought. Resolve routine implementation choices within the stated defaults.

Read `CLAUDE.md`, this file, `docs/PROGRESS.md`, `docs/DECISIONS.md`, then the master specification for this initial review. Inventory installed relevant skills by names/descriptions. Check actual Git state and tool versions. Never assume the uploaded resume or this generated brief describes implemented code in this repository.

Produce one concise architecture review and a dependency-aware plan. Confirm:

1. Single authority for cash, holdings, approvals and time.
2. Transaction/reservation/settlement policy and race handling.
3. Future-event execution and historical information cutoffs.
4. Separation of house rules, financial concepts and legal facts.
5. One deployable ML candidate with an objective baseline gate.
6. Token-saving task boundaries, relevant skill selection and evidence gates.

Default stack is Next.js + TypeScript, FastAPI + Python, PostgreSQL, then a worker and Redis when justified. Propose alternatives only where they solve a concrete problem; do not generate multiple full stack plans. If a choice requires a credential, paid service or current entitlement, continue with fixture-based work and identify the dependency.

## Authorized initial implementation after review

Implement milestone M0, then a separately scoped M1 if the owner asks to continue. Keep the application paper-only. M0 creates tool configuration, domain skeleton, fixture-loading contract, minimal health screen/API, and CI scaffolding. M1 implements the deterministic accounting scenario and meaningful financial tests before broad UI work.

The user can ask “continue the next milestone” after reviewing the first output. Do not rewrite the full brief every session. Update only genuinely changed decisions and the small progress handoff.

## What the first playable version must do

Two users form a virtual fund, each has equal units, both accept a mandate, start a shared session, propose/review orders, see queued versus filled states, advance a fixture market day, and inspect reconciled NAV and shared P&L. No AI service or paid market-data plan is needed for that demonstration. The interface should feel like a small cooperative management game, not a terminal with dozens of widgets.

## Repo privacy and setup

This repository already has a private remote; skip P00 and start with P01. For a separate future copy only: if GitHub CLI is installed and authenticated on the owner's machine, read `scripts/create-private-repo.ps1` or `.sh`, verify working directory, and run the appropriate script. Inspect the result's `isPrivate` field. If credentials are unavailable, give the precise login/install step; do not invent a repository URL or visibility. Do not change an existing repository's visibility or overwrite a name collision. Never commit secrets, market data without rights, or the supplied personal resume.

GitHub CLI should use the owner's interactive authentication; never ask the owner to paste a token into a chat or into `CLAUDE.md`. Keep repository setup separate from app deployment. The provided scripts only set up the documentation repo, not hosting.

## Evidence standards

No “all done” based on generated code alone. Each milestone has named observable behavior, test/verification commands and output. New tests should cover financial meaning, races, access boundaries or leakage, not simply restate a function's own implementation. A test count is not a substitute for invariants.

Before claiming readiness, replay the golden scenario, exercise concurrency with real PostgreSQL, try cross-fund and future-data access, demonstrate worker retry/recovery, and run the two-user flow. Later ML acceptance requires a fixed split and actual evaluation results. Record failed checks and limitations alongside successes.

## Completion response for each task

Keep the task response compact: changed behavior and why; changed files; checks run and actual results; unresolved blocker or risk; one next task. Update `docs/PROGRESS.md` with enough state for a fresh session. Stop when the task's gate is met. Do not launch extra agents, polish other screens, expand instruments or propose a new architecture as a reward for finishing.

## What remains intentionally optional

Redis, WebSockets, MLflow, historical seasons, LLM summaries, public rankings, agent opponents, hypothetical fees, shorts, margin, redemptions and derivatives all have later gates. They are not required to make the first session playable. Development reviewers are optional, scoped and bounded; they are not unlimited independent usage pools.
