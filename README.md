# FundForge

Two friends. One virtual fund. Fifteen minutes a day.

FundForge is a proposed cooperative paper-fund game and engineering portfolio project. Two managers share a virtual $100,000 fund, approve each other's trades, follow a mandate, and learn finance through realistic operations. No deposits, brokerage execution, cash prizes, or real distributions are implemented or authorized by this package.

**Status: specification and Claude handoff only. No application has been implemented, deployed, or benchmarked. The GitHub repository is private; application implementation is pending.**

## Start here

1. Read `CLAUDE.md` and `docs/CLAUDE_HANDOFF.md`.
2. Use prompt P01 in `docs/PROMPT_PACK.md` for the first architecture inspection.
3. Follow `docs/IMPLEMENTATION_PLAN.md`, one milestone per bounded task.
4. Keep `docs/PROGRESS.md` current after each task.

## Document map

| File | Purpose |
|---|---|
| `docs/MASTER_SPEC.md` | Product, game, fund operations, trading, risk, data, ML, backtesting, security, UI, and scoring |
| `docs/CLAUDE_HANDOFF.md` | Exact starting instructions and current state |
| `docs/PROMPT_PACK.md` | Copy-ready prompts with scope, evidence, and stopping conditions |
| `docs/IMPLEMENTATION_PLAN.md` | Dependencies and phased delivery |
| `docs/ACCEPTANCE_TESTS.md` | Financial golden cases, concurrency, authorization, and replay tests |
| `docs/AGENT_WORKFLOW.md` | Bounded adversarial review, isolated parallel work, and AI game opponents |
| `docs/RECRUITER_EVIDENCE.md` | Backend/ML proof, truthful resume templates, and demo plan |
| `docs/SOURCES.md` | Official sources and freshness checks |
| `docs/DECISIONS.md` | Decision log and resolved defaults |
| `docs/PROGRESS.md` | Small session handoff; initially all implementation is pending |
| `docs/PACKAGING_VALIDATION.md` | Package checks and unexecuted boundaries |
| `fixtures/golden_scenario.json` | Reference arithmetic for ledger implementation |

## Clone and start Claude Code

Private repository: https://github.com/krishbansalofficial/fundforge

```bash
git clone https://github.com/krishbansalofficial/fundforge.git
cd fundforge
claude
```

Authenticate Git/Claude through their normal secure sign-in flows if needed. Start with **P01** in `docs/PROMPT_PACK.md`; repository creation is already complete. Read `CLAUDE.md`, `docs/CLAUDE_HANDOFF.md` and `docs/PROGRESS.md` before implementation.

The complete Word brief is in `documents/FundForge_Project_Spec_and_Claude_Handoff.docx`. The modular Markdown files are the working source for Claude and let later sessions load only the relevant sections.

The private-repository setup scripts are retained for creating a separate future copy. They stop on an existing name or origin and should not be run to recreate this repository. Do not commit secrets, unlicensed market datasets or the personal resume.

## Chosen defaults

- TypeScript/Next.js frontend; Python/FastAPI modular backend; PostgreSQL authority.
- First playable release: fixture data, long-only whole-share stocks/ETFs, market orders, next-open execution, 50/50 virtual capital accounts, strict partner approval, settlement and reconciliation.
- Redis, WebSockets, limit orders, historical seasons, MLflow, and AI explanations arrive only after the financial core works.
- UI: restrained fund-management game, five screens, readable cards, clear actions, short feedback, no elaborate animation or photorealistic assets.
- Finance code is deterministic. The LLM cannot mutate cash, invent fills, approve orders, or bypass risk controls.

This package is a detailed build brief, not evidence of a finished product or a legal compliance certification.
