# Re-plan v3: feasible portfolio scope

7 October 2026. This supersedes the 20-milestone sequencing in IMPLEMENTATION_PLAN and MILESTONE_PLANS. It keeps the accounting contracts. Those files stay in place as the long-range design reference.

## Why re-plan

Two bounded reviewers argued opposite positions. An advocate defended the oracle → domain → persistence → UI order. A challenger tested whether the plan was feasible for a solo graduate building a portfolio project.

| Point | Advocate | Challenger | Verdict |
|---|---|---|---|
| Effort for the plan as written | Conceded that 20 milestones is too many for one person | About 30–40 weeks part-time before FF6c. The first UI appears around week 20 | Infeasible as written |
| Hand-authored dated oracle first (FF0a) | Cheap TDD that keeps tests independent | Weeks of spreadsheet work before any code | Keep independent oracles, but derive them from the isolated cases in FUND_ACCOUNTING §6 plus property tests. No full day-by-day hand ledger before code |
| Pure domain before the database | Fast, deterministic and rewritable | Agreed | Keep |
| Visible product timing | Conceded that FF5 is too late | A recruiter decides in about 90 s from the README, demo, CI and diagram | Put the UI in week 5 and deploy in week 6 |
| Journal, Decimal, idempotency, two-person digest, as-of safety, fund/firm split | These are what set the project apart | Keep them all | Non-negotiable. Cut breadth, not correctness |
| Per-milestone RESULTS files and decision registers | — | About 20–30% overhead, and they read as "planner, not builder" | Replaced by CI, the test suite and one `docs/ENGINEERING.md` |
| 60-day campaign, 12 instruments, Cases 2/3, staffing, FF7 ML, FF8 | Conceded the FF6–FF8 wish list | Cut | Moved to Stretch |
| Human playtest study | Keep one recorded playtest | Weeks of recruiting pairs | One recorded two-person session. No claims of a broader study |

## Scope of the shipped slice

Case1, "The borrow is not the thesis" (SCENARIO_CONTRACTS):
- Days 12–21 with the warm-start book.
- Two partners.
- Three LP series.
- The Case1 instruments.
- A broker recall with a replacement offer.
- A shock with a margin deficit.
- A Tactical redemption dealt at day 20 and paid at day 21.
- Weekly payroll for the separate management company.
- A causal debrief built from the journal.

The accounting is the existing FUND_ACCOUNTING contract, implemented for the mechanics the slice exercises:
- Management fee: ACT/365.
- Performance provision with an HWM.
- Partial-redemption crystallization.
- Borrow and debit charges: ACT/360.
- Restricted collateral.
- T+1 settlement.
- Impact-cost execution at the next event.

## Milestones (≈15 h/week)

| # | Week | Deliverable | Acceptance |
|---|---|---|---|
| M0 | 1 | Monorepo, CI, Decimal money, immutable balanced journal | Hypothesis: every entry balances, replay is idempotent, float money is rejected. CI is green |
| M1 | 2 | Fund and firm books, LP series, fees/HWM, financing accruals, replay hash | FUND_ACCOUNTING §6 isolated oracles 1–8 pass as tests. Fund NAV equals the sum of series net capital |
| M2 | 3 | Case1 tape fixture, next-event execution, shorts and collateral, recall, dealing and payment, payroll | Scripted S1/F1 paths run day 12 → day 21. Invariants hold at every close. The cash and claim separation between fund and firm holds |
| M3 | 4 | Command layer: idempotency keys, two-person digest approval, revalidation at execution, as-of views | No self-approval. Edits invalidate signatures. A retried command does not double-spend. The player view never contains a future tape |
| M4 | 5 | FastAPI + PostgreSQL. Append-only tables, serialized fund transactions, race test in CI | Two connections race one approval or spend. Exactly one wins and journal counts are correct |
| M5 | 6 | Next.js desk with a two-player room (polling), approvals, ledger and debrief | Two browsers complete Case1. Keyboard and error states work |
| M6 | 7 | Deploy, README with GIF and architecture diagram, ENGINEERING.md with three design write-ups | Live URL with seeded demo users. Every claim in the README is backed by a test or link |
| — | 8 | Buffer | — |

**Stretch, in order:**
1. Zero-position day 1–21 opening.
2. Cases 2 and 3.
3. Gates and escrow.
4. Corporate actions.
5. 60-day campaign.
6. Historical replay and advisory AI (old FF7/FF8).

## Rules carried forward

Everything in CLAUDE.md's non-negotiables still applies. Simplifications are recorded in the code with a `ponytail:` comment and in ENGINEERING.md. They are never hidden.

## After M6

The full game (G1–G11, about 25 core weeks) and the analytics stack (pandas, statsmodels, CVXPY advisory, exchange_calendars, DuckDB) are planned in [FULL_GAME_PLAN](FULL_GAME_PLAN.md) and [RESEARCH_AND_ANALYTICS_PLAN](RESEARCH_AND_ANALYTICS_PLAN.md). Analytics stay read-only and off the Decimal money path.
