# Full game plan: from the Case1 slice to the 60-day season

7 October 2026. Planning document, not a record of completed work. It extends [REPLAN_V3](REPLAN_V3.md) past M6 with milestones G1–G11. Accounting authority stays with [FUND_ACCOUNTING](FUND_ACCOUNTING.md), game rules with [GAME_SYSTEMS](GAME_SYSTEMS.md), challenge schedules with [SCENARIO_CONTRACTS](SCENARIO_CONTRACTS.md), and product boundaries with [MASTER_SPEC](MASTER_SPEC.md). Where this plan disagrees with one of those, the conflict is listed in §9 and must be resolved in the owning document before the milestone starts. Analytics libraries are planned in [RESEARCH_AND_ANALYTICS_PLAN](RESEARCH_AND_ANALYTICS_PLAN.md).

## 1. Starting point (what exists today)

Only what PROGRESS.md and the git log show:

| Area | Exists | Module |
|---|---|---|
| Money and journal | Decimal HALF_EVEN, residual `Accrual`, immutable balanced per-entity journal, sha256 digest | `money.py`, `journal.py` |
| LP series | Participation add-back, HWM provision, cohort allocation, partial-redemption crystallization | `series.py` |
| Risk | Gross/net exposures, initial and maintenance margin | `risk.py` |
| Execution | Quadratic-impact fill price, shared participation cap | `execution.py` |
| Tape | Case1 days 12–21, five phases per day, authoring-fault rejection, tape digest | `tape.py`, `fixtures/case1.json` |
| Engine | T+1 settlement, collateral, recall and replacement, margin call and forced liquidation, ACT/360 and ACT/365 accruals, invoicing, Tactical dealing and payment, firm payroll, reconcile after every event | `engine.py` |
| Governance | Two partners, PM ticket caps (5% NAV, 15% turnover), digest-bound packages, no self-approval, both-ready advance, as-of view | `governance.py` |
| Persistence/API | Postgres append-only command log and journal, room-row lock, idempotency keys, replay, hashed seat tokens, race tests | `store.py`, `api.py` |
| Desk | Next.js two-seat crisis desk: deadline ribbon, approvals, ledger, debrief (commit `4e4bce5`) | `frontend/app/` |

Known gaps recorded in PROGRESS: no FIFO lots or realized/unrealized split, no gates or escrow, no order cash budgets, coarse limit search, largest-value-first forced liquidation, per-process replay cache, bearer-link seats, mandate limits beyond margin and ticket caps not enforced, no playtest. M6 (deploy, README, write-ups) is the open REPLAN_V3 milestone and comes before G1.

## 2. The complete game loop

Default season (MASTER_SPEC §2, SEASON_SCENARIOS §1): $25m from three LPs (Seed $10m, Patient $8m, Tactical $7m), a separate $300k management company, 60 synthetic Mon–Fri business days from 5 January 2026, six ten-day chapters, ending at the day 61 OPEN_ADMIN checkpoint.

**Day 1 launch with zero positions.** The fund opens with $25m settled cash, 250,000 units at $100, HWM 100 per series, no holdings and no loans. The first committee approves two sleeves and a treasury reserve. The first trades execute at day 1 EXEC_A at the earliest, never at an observed mark. The Case1 warm start (130% gross book) cannot stand in for this opening (IMPLEMENTATION_PLAN FF5a).

**Chapter rhythm** (GAME_SYSTEMS §1, §12). Each chapter has three decision windows: the opening committee, a mid-chapter reassessment and the close. Material incidents (margin, recall, redemption, solvency, payroll) insert a window before their deadline. Routine days auto-run. Advance requires both partners ready against the same plan digest; a changed material plan clears readiness. Each partner has two strategic assignments per chapter.

| Chapter | Days | Central decision | Mechanics first exercised |
|---|---|---|---|
| 1 Earn the risk budget | 1–10 | Approve sleeves, choose evidence, source borrow, first delegated trades | Sleeves, research cards, locate, first fills |
| 2 Price of conviction | 11–20 | Reduce, replace borrow or defend; first dealing | Recall, margin shock (Case1 pattern), Tactical 10,000-unit redemption, first fee invoice |
| 3 Bigger is not better | 21–30 | Accept, cap or decline a new LP; hire or preserve runway | Fundraising pipeline, escrow, new series, staffing |
| 4 Right thesis, wrong deadline | 31–40 | Seed's disclosed $3m need versus a catalyst | Notices day 35, gate election, liquidity ladder |
| 5 Show your work | 41–50 | Drawdown, LP concern, recovery | Drawdown freeze, LP confidence, certified reporting, corporate actions |
| 6 Earn renewal | 51–60 | Lock in solvency or reach for return | Final dealing day 60, endings, debrief |

### 2.1 Mechanics, sources and code homes

| Mechanic | Rule source | Extends | New home (proposed) |
|---|---|---|---|
| LP subscriptions: prospect → qualified → diligence → commitment → escrow → admitted series at $100/HWM 100 | GAME_SYSTEMS §4 | `series.py` | `dealing.py` |
| Redemptions: notices days 15/35/55, dealing 20/40/60, pay next business day, unit-denominated requests | GAME_SYSTEMS §4, FUND_ACCOUNTING §5 | `engine._deal`, `_pay_due` | `dealing.py` |
| Gates: joint election before dealing, 20% of pre-flow post-fee NAV, pro rata including carried requests, deferred units stay exposed | GAME_SYSTEMS §4 | — | `dealing.py` |
| Escrow: committed subscription cash held outside fund NAV until admission; never firm revenue | SCENARIO_CONTRACTS Case3 | `journal.py` (third entity or memo account, decide in G2) | `dealing.py` |
| Management fee 1.5% ACT/365 on every calendar date; performance 20% provision with series HWM, crystallized only 31 Dec or on redeemed units | FUND_ACCOUNTING §6 | `series.py`, `engine._accrue_date` | unchanged homes |
| Financing: borrow fees and debit interest ACT/360 on settled quantities incl. weekends; $7.5m credit line; initial 50/60, maintenance 35/40; restricted short collateral | GAME_SYSTEMS §6, FUND_ACCOUNTING §4, §10 | `engine.py`, `risk.py` | `risk.py` gains stress scenarios |
| Research economy: assignments, evidence cards with `available_at`, reliability class; no guaranteed price | GAME_SYSTEMS §3 | `engine.assign_research` | `research.py` |
| Mandates and sleeves: owner, instruments, sides, max gross, max order, chapter turnover, expiry; delegated orders ≤5% NAV, ≤15% chapter-opening NAV turnover per sleeve | GAME_SYSTEMS §2, MASTER_SPEC §4 | `governance.py` ticket caps | `mandate.py` |
| Hard limits: gross ≤150%, net −20%..100%, issuer 15% long/8% short, sector 35%, each ETF 50%; prefix checks on multi-leg plans; drawdown 10% warn/15% freeze on flow-neutral index | GAME_SYSTEMS §7 | `risk.py` | `risk.py` |
| Emergency reduction policy: either partner, must reduce a deficit and worsen none | GAME_SYSTEMS §2 | `governance.py` | `mandate.py` |
| Staffing: analyst, operations, IR; $10k recruiting, $4–5k weekly; max two; capability = one extra assignment or prospect slot; release costs two weeks | GAME_SYSTEMS §5 | `engine` payroll | `firm.py` |
| Firm survival: runway = unrestricted company cash / weekly cost; separate 13-week forecast; COMPANY_DISTRESS with five-day cure; no owner injections or cross-entity loans | GAME_SYSTEMS §5 | `engine` payroll, `_post_pair` | `firm.py` |
| Crises: incident state machine NORMAL → WATCH → ACTION_REQUIRED → REMEDIATING → CURED / CONTROLLED_WINDDOWN / DEFAULT; recall buy-in, margin call, debt-line reduction, payroll miss | GAME_SYSTEMS §8 | `engine.incidents` | `incidents.py` |
| Corporate actions: cash distributions (cum/ex/pay, dividend-in-lieu on shorts) and integer splits | FUND_ACCOUNTING §3 | `engine.py` | `corporate.py` |
| Controls: restricted-source instruments, admin/broker breaks, correction by reversal, certification blocks dealing | GAME_SYSTEMS §10, Case3 | `engine.reconcile` | `controls.py` |
| Endings: Renewal (conditional continuation), Survival Without Renewal, Responsible Winddown, Broker Default, Company Failure; winddown horizon 10 business days | GAME_SYSTEMS §9, FUND_ACCOUNTING §10 | `engine.outcome` | `outcome.py` |
| Scoring and debrief: tier, then net TWR among tier, then drawdown; return/cost/claims bridge; paired replay is practice only | GAME_SYSTEMS §9, §10 | desk debrief tab | `debrief.py` |

### 2.2 The three challenge cases

| Case | Window | What it teaches | Status |
|---|---|---|---|
| Case1 "The borrow is not the thesis" | days 12–21 | Recall, replacement borrow, margin shock, payment reserve | Implemented (M2–M5) |
| Case2 "Profitable, illiquid, and redeeming" | days 39–61 | Gate versus sale, BEAM capacity, carried units paid day 60/61 | G6 |
| Case3 "The report is balanced, the NAV is wrong" | days 29–41 (to 45 on cure) | Missing dividend liability, restriction, certification deadline, optional admission | G6 |

Challenges stay separate from the season leaderboard (GAME_SYSTEMS §9: no common return ranking across cases).

## 3. Hedge fund versus trading app

| Feels like running a fund | Why a trading app lacks it |
|---|---|
| Other people's money with contractual rights: notices, dealing dates, gates, unit-denominated claims | A trading app has one owner who can withdraw any time |
| Two balance sheets: fund NAV can be fine while the management company misses payroll | Single account balance |
| Fees that are receivables, not cash; provisions that reverse; HWM per series | No fee economics |
| Financing as a constraint: borrow recalls, collateral that cannot be spent, margin coefficient changes | Infinite borrow, instant settlement |
| Settlement time: T+1, failed settlements, payment deadlines independent of P&L | Instant cash |
| Authority: sleeves, delegated limits, a partner's signature on an exact digest | Solo click-to-trade |
| Scarce attention: four assignments per chapter across research, diligence and contingency | Unlimited free data |
| Firm decisions: hires, runway, conditional renewal | None |
| Honest reporting: certification, restatement by reversal, restricted information | None |

**Deliberately excluded:** real money, deposits, brokerage connections or order routing, real investor solicitation, investment advice or signals, cash prizes, options/futures/swaps, multi-currency, tax, real fund documents, legal/compliance assurance, public matchmaking, and any LLM that trades, approves, posts money or decides outcomes (MASTER_SPEC §10). Advisory analytics never mutate state (see the research plan).

## 4. Milestones G1–G11

Budget about 15 h/week. "Core" is needed for the full game; "stretch" is optional. Every milestone keeps the CLAUDE.md non-negotiables: Decimal money, immutable balanced journal with replay hash, exactly two humans with digest approvals, execution at a later event only, no future information in any view or export, fund/firm separation, LLMs and analytics never own economics. Each one ends with green CI, an updated PROGRESS.md and an ENGINEERING.md entry for any new invariant.

| ID | Goal | Weeks | Core? | Depends on |
|---|---|---:|---|---|
| G1 | Public landing page, SEO and accessibility pass | 1 | core | M6 |
| G2 | Ledger depth and capital flows | 3 | core | M6 |
| G3 | Mandates, sleeves and full risk limits | 3 | core | G2 |
| G4 | Chapter loop, research, LP confidence, zero-position days 1–21 | 4 | core | G3 |
| G5 | Management company: staffing, runway, distress | 2 | core | G4 |
| G6 | Cases 2 and 3: corporate actions, restrictions, breaks | 4 | core | G2, G3, G5 |
| G7 | 60-day campaign, crises, endings, scoring, debrief, balance study | 4 | core | G4–G6 |
| G8 | Hardening and one recorded two-person playtest | 2 | core | G7 |
| G9 | Analytics package: exports, debrief attribution, boundary tests | 2 | core-lite | G7 |
| G10 | Advisory quant analyst (CVXPY) | 2 | stretch | G3, G9 |
| G11 | Real session calendar variant and Parquet as-of tape store | 2 | stretch | G7, G9 |

Core G1–G9: about 25 weeks; with a 20% buffer about 30 weeks (roughly seven months part-time). Stretch adds about 4 weeks. These are estimates, not commitments.

### G1 Landing page and SEO (1 week, core)
- **Files:** `frontend/app/page.tsx` (becomes landing), `frontend/app/play/page.tsx` (room creation moves here), `frontend/app/sitemap.ts`, `frontend/app/robots.ts`, `frontend/app/opengraph-image.tsx`, `frontend/app/room/[id]/layout.tsx` (noindex), `frontend/next.config.ts` (headers).
- **Acceptance:** `/sitemap.xml` lists only public pages and no `/room/` URL; `/robots.txt` disallows `/room/` and `/api/`; room responses carry `X-Robots-Tag: noindex` and `Referrer-Policy: no-referrer`; Lighthouse on the deployed landing page reports the measured Performance, Accessibility, Best Practices and SEO scores in PROGRESS (target ≥90 each; record actuals); axe or Lighthouse shows no critical accessibility violation; zero third-party scripts on `/room/*` (checked by a test that parses the built HTML).

### G2 Ledger depth and capital flows (3 weeks, core)
- **Files:** `journal.py` (escrow entity or account), `series.py`, new `dealing.py`, `engine.py` (FIFO lots, realized/unrealized, order cash budgets), `tests/test_dealing.py`, `tests/test_lots.py`.
- **Acceptance:** FIFO: buy 100@10, buy 100@12, sell 150@15 realizes exactly $650.00; gate at 20% of pre-flow NAV allocates pro rata to the cent and unit, carried units deal at the next window without a new notice; deferred units keep exposure and fees; a $5m subscription creates its own series at $100/HWM 100, adds zero firm cash, and is not NAV or margin collateral until admitted; escrow balance is excluded from NAV and from `credit_left`; Hypothesis: for any sequence of subscriptions/redemptions, sum of series net capital equals NAV and every entry balances; replay hash identical after Postgres replay.

### G3 Mandates, sleeves and full risk (3 weeks, core)
- **Files:** new `mandate.py`, `risk.py`, `governance.py` (sleeve proposals, delegated orders, emergency reduction), `tests/test_mandate.py`, desk "Investment room" panel.
- **Acceptance:** a non-owner order without a fresh signature is rejected; splitting one ticket into five does not evade the per-sleeve turnover budget; pending orders reserve capacity and cancellation releases it; each hard limit (gross, net, issuer long/short, sector, ETF) has a reject-at-commit and a reject-at-execution test after an intervening mark; a two-leg plan whose second leg breaches is rejected at the prefix that breaches; an emergency reduction that cures margin but worsens net beyond −20% is rejected; a passive breach creates remediation, not retroactive invalidation; drawdown ≥15% on the flow-neutral index freezes risk additions and only a reconciled close above threshold clears it. Includes a Decimal **plan preview** endpoint used later by G10.

### G4 Chapter loop and the opening arc (4 weeks, core)
- **Files:** new `chapter.py`, `research.py`, `lp.py`; `tape.py` (multi-chapter fixture, evidence cards); `fixtures/opening.json` (days 1–21, four instruments); `tools/author/` (pandas-based tape generator, dev-only); desk chapter board.
- **Acceptance:** day 1 opens with zero positions and $25m cash; no fill occurs before day 1 EXEC_A; each partner has exactly two assignments per chapter, unused ones expire; an evidence card is absent from the view before its `available_at` (mutating its content changes no earlier view hash); LP confidence follows the six-step formula with stored components; at day 15 the Tactical request is max(10,000 units, confidence request), not the sum; two scripted successful policies and one failure policy run days 1 → 21 OPEN_ADMIN under reconcile; the authored fixture is Decimal-string JSON with a digest, and the pandas generator is not imported at runtime.

### G5 Management company (2 weeks, core)
- **Files:** new `firm.py`, `engine.py` payroll path, desk "Capital and operations" panel.
- **Acceptance:** hiring pays $10,000 immediately, salary and capability start at the next chapter boundary; a third hire is rejected; release costs two weeks of salary at the next weekly boundary; runway and the 13-week forecast are shown separately and accrued fee receivables are excluded from runway; a missed payroll enters COMPANY_DISTRESS with a five-business-day cure; no code path moves fund cash to firm cash except a fee payment (`test_fund_cash_never_pays_firm_payroll` extended to hires); a hire never changes any fill price or tape value (same tape, same orders, identical fills with and without a hire).

### G6 Cases 2 and 3 (4 weeks, core)
- **Files:** `fixtures/case2.json`, `fixtures/case3.json`, new `corporate.py`, `controls.py`, `store.SCENARIOS`, case-specific tests.
- **Acceptance (oracles from SCENARIO_CONTRACTS and FUND_ACCOUNTING §3):** a $2 distribution with a 50→48 mark on a 100-share long gives −$200 price P&L and +$200 income, and the mirror on a short; a 2-for-1 split preserves value, lots, borrow, resting orders and locates once under one action ID; Case3 opening correction posts the $200,000 liability and $40,000 provision reversal to give NAV $26.84m, keeps the wrong report and never repeats the expense at payment; ALTO orders are blocked and resting ones cancelled from day 29 until the day 33 release event, and no command can clear the flag; missing certification by day 35 forfeits the prospect; Case2 gated units are fully paid by day 61 with equal-treatment allocation; Case2 S1 and S2 scripts and Case3 S1 and S2 scripts finish with outcomes recorded, and any infeasible script is fixed by a new fixture version, not an engine special case.

### G7 Full season (4 weeks, core)
- **Files:** `fixtures/season.json` (days 1–61, twelve instruments), new `incidents.py`, `outcome.py`, `debrief.py`, `tools/balance/` (policy runner); desk debrief.
- **Acceptance:** each of the five ending labels is reached by a named scripted policy on the authored tape (or the plan records which label is unreachable and why); Renewal requires all six GAME_SYSTEMS §9 conditions at the day 61 checkpoint, each tested by a policy that fails exactly one; winddown without authored horizon events reports UNRESOLVED_WINDDOWN; a debt-line reduction creates a dated repayment obligation; the balance runner executes passive cash, buy-and-hold, diversified long/short, concentrated gambler, and gate/fee exploit policies on the same tape and the exploit policies do not reach Renewal; the debrief bridge sums investment P&L, financing, fees and flows to the NAV change to the cent; ranking order is tier → net TWR → drawdown → stable ID.

### G8 Hardening and playtest (2 weeks, core)
- **Files:** `api.py` (session auth replacing bearer links, e.g. signed HTTP-only cookie bound to seat), `store.py` (shared replay cache or snapshot), restore script, `docs/ENGINEERING.md`.
- **Acceptance:** a revoked seat and a seat from another room are rejected; a missing partner pauses at the next safe boundary and nothing executes while paused; database restore from backup replays to the same journal digest; the existing race tests pass against the deployed configuration; one recorded two-person session is summarized in PROGRESS with observed confusion points. No broader study claim.

### G9 Analytics package (2 weeks, core-lite)
- **Files:** `backend/src/fundforge_analytics/`, `tests/test_import_boundary.py`, optional dependency group `analytics`.
- **Acceptance:** see RESEARCH_AND_ANALYTICS_PLAN: import-boundary test; core test suite passes in a CI job without the analytics group installed; LP statement and journal exports match the Decimal ledger to the cent; statsmodels recovers a planted synthetic beta; in-game risk report is unchanged when future tape rows are mutated.

### G10 Advisory quant analyst (2 weeks, stretch)
CVXPY cure/rebalance planner that drafts an ordinary package for the humans to sign. Acceptance in the research plan.

### G11 Real session calendar and as-of tape store (2 weeks, stretch)
exchange_calendars XNYS variant of the opening arc plus a DuckDB/Parquet as-of tape store. Historical real-price replay is out of scope unless data with explicit display and redistribution rights is found; that decision is recorded, not assumed.

## 5. What recruiters see at each phase

Claims below become true only when the milestone's tests pass; until then they are plans.

| After | Demo | Write-up | Measurable claim (only once observed) |
|---|---|---|---|
| M6 | Live Case1 room, GIF, architecture diagram | ENGINEERING.md: ledger, fund/firm, approvals | N backend tests; race tests on real Postgres; journal digest replay |
| G1 | Landing page with OG card, fast load | — | Lighthouse scores as measured |
| G2–G3 | Gate a redemption; sleeve blocks a split ticket | "Gates, escrow and why subscriptions are not revenue"; "Prefix checks for multi-leg plans" | Hypothesis property: series sum equals NAV across random flows |
| G4–G5 | Day 1 launch with zero positions through the first dealing | "Designing scarce attention"; "Payroll cannot touch investor cash" | Two scripted policies win, one fails, all reconciled |
| G6 | Case3 restatement walk-through | "The report balanced and was still wrong" | Case oracles as tests |
| G7 | Full season to an ending, debrief bridge | "Balancing with baseline and exploit policies" | Outcome table per policy from the balance runner |
| G8 | Two-person recorded session | Playtest notes and changes made | Restore replays to the same digest |
| G9–G11 | Debrief beta chart, analyst suggestion, real-calendar run | "Keeping float analytics out of a Decimal ledger" | Beta recovery error; optimizer cost versus heuristic baseline |

Resume bullets describe what was built and the exact test outcome. No AUM, returns or "alpha" from the game are presented as investment performance (RECRUITER_EVIDENCE).

## 6. SEO and discoverability (owner override, narrow scope)

Scope: the public landing page and public docs pages only. Rooms, seats, APIs and the desk are never indexed.

| Item | Implementation | Check |
|---|---|---|
| Metadata | Next.js Metadata API in `layout.tsx` and per page: title, description, canonical URL, `metadataBase` | Rendered `<head>` snapshot test |
| Open Graph / Twitter card | `app/opengraph-image.tsx` (generated 1200×630 image showing the deadline ribbon) | OG validator by hand; image route returns 200 |
| Sitemap / robots | `app/sitemap.ts` (landing, how-it-works, engineering notes), `app/robots.ts` disallowing `/room/` and `/api/` | Test asserts no `/room/` in sitemap |
| Structured data | One JSON-LD `SoftwareApplication` block (category Game, free, no offers) | Rich Results test by hand |
| Performance | Static landing page, `next/font` self-hosted fonts, `next/image`, no client JS beyond what the page needs | Lighthouse on deployed URL, record actual scores |
| Accessibility | Semantic headings, alt text, contrast, keyboard focus, reduced motion | Lighthouse/axe, keyboard walk-through |
| Privacy | No analytics, ad, pixel or tracking scripts anywhere in the game; no paid SEO tools; seat tokens stay out of indexed URLs and referrers | Built-HTML test for third-party script tags |

Docs pages: render `README` sections and ENGINEERING.md to static pages at build. Content stays factual: what was built and tested. SEO work never changes game code or adds dependencies to the backend. Sources checked 7 October 2026: [generateMetadata](https://nextjs.org/docs/app/api-reference/functions/generate-metadata), [opengraph-image](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/opengraph-image), [sitemap](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap), [robots](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/robots), [Web Vitals](https://web.dev/articles/vitals).

## 7. Risks for a solo builder

- **Authoring cost.** The 60-day, twelve-instrument tape and Cases 2/3 are content work, not code. G4 builds the generator first; G7 may ship with fewer instruments if balance needs it (record the cut).
- **engine.py growth.** It is 635 lines for one case. Extract mechanics into the modules named in §2.1 only when a milestone touches them, with reconcile still asserting after every event.
- **Scope creep from analytics.** G9–G11 never block G1–G8. If time runs short, G10 and G11 are dropped first, then G9 shrinks to exports only.
- **Balance.** Numbers in GAME_SYSTEMS are hypotheses. G7's runner exists to test them; retuning creates a new fixture version.

## 8. Cut order if behind schedule

1. G11, then G10. 2. Twelve instruments → eight in G7. 3. Staffing to one hire type. 4. Case3's optional admission branch. Never cut: LPs, firm cash, financing, two-person authority, as-of views, reconcile.

## 9. Conflicts with existing documents (resolve before the affected milestone)

| Document | Conflict | Proposed resolution |
|---|---|---|
| CLAUDE.md, MASTER_SPEC §10, LIBRARY_RESEARCH, IMPLEMENTATION_PLAN FF7b | "No SEO or marketing" | Owner override: allow §6 scope only; update those lines (G1) |
| CLAUDE.md | "Current next task remains FF0a" | REPLAN_V3 supersedes; next task is M6 |
| PROGRESS.md | Says 44 tests, review fixes uncommitted, M5 next; git has `127fce7` and `4e4bce5` | Refresh PROGRESS with the actual suite count and M5 state |
| LIBRARY_RESEARCH | pandas/exchange_calendars deferred to licensed historical work | pandas adopted as dev-only authoring tool in G4; exchange_calendars for a synthetic real-calendar variant in G11 (no licensed data needed) |
| SCENARIO_CONTRACTS | Synthetic calendar trades on fictional holidays | Real-calendar mode is a separate scenario version; base cases unchanged |
| GAME_SYSTEMS §7 | No estimated beta at launch | statsmodels output is a labeled diagnostic beside authored betas, never a limit input |
| GAME_SYSTEMS §2 vs `governance.py` | Sleeves versus flat PM ticket caps | G3 replaces flat caps with sleeve authority; Case1 keeps its policy version |
| `tape.py` | Dates computed as Nth weekday | Explicit session list in fixture for calendar variants (G11) |
