# FundForge

A cooperative hedge-fund management strategy game. Two partners build an investment business, manage outside investors' capital, and survive the consequences of their decisions.

**Status: design package v2.2, 7 October 2026. No application has been implemented.** Three bounded independent reviews strengthened the existing v2.1 plan. The reported Python/Pydantic foundation and26 tests are absent from this checkout. Earlier research remains preserved.

## The game

Run a fictional $25 million long/short equity fund over 60 simulated business days, organized into six chapters. Choose research priorities, negotiate investment authority, allocate capital, manage financing, handle investor withdrawals, pay the firm's bills, and explain what happened. Sessions advance simulated time; players do not need to attend at real market hours.

The investment partner leads theses and portfolio construction. The operating/risk partner leads liquidity, financing, investor relationships and the business budget. Both can research and challenge decisions. Agreed strategy sleeves let routine actions proceed inside a jointly approved envelope; material exceptions require committee agreement. Every partner has consequential work beyond approving the other's tickets.

The objective is durable, mandate-consistent investor outcomes and a viable firm. A lucky leveraged bet does not erase unpaid obligations, broken promises, or insolvency. A disciplined winddown is a distinct outcome. All money, entities, contracts and obligations in the campaign are fictional.

## Read in this order

1. [Realism audit](docs/REALISM_AUDIT.md), then [master specification](docs/MASTER_SPEC.md): critical findings, priorities and product boundaries.
2. [Game systems](docs/GAME_SYSTEMS.md): actions, roles, capital, progression and scoring.
3. [Season scenarios](docs/SEASON_SCENARIOS.md): actual decisions and crisis arcs.
4. [Fund accounting](docs/FUND_ACCOUNTING.md): authoritative financial contracts.
5. [Implementation plan](docs/IMPLEMENTATION_PLAN.md) and [acceptance cases](docs/ACCEPTANCE_TESTS.md).
6. [Simulation architecture](docs/SIMULATION_ARCHITECTURE.md): ownership, interfaces, replay, precision, concurrency and information safety.
7. [Library research](docs/LIBRARY_RESEARCH.md): retained pinned financial-library reviews; SEO/marketing excluded.
8. [v2.2 review](docs/DESIGN_REVIEW_V2_2.md), [complete challenge authoring contracts](docs/SCENARIO_CONTRACTS.md), and [exact next milestone](docs/IMPLEMENTATION_HANDOFF.md).

9. [Full milestone work packages](docs/MILESTONE_PLANS.md): all 20 milestones through final FF8, with ordered tasks, owned files, deliverables, validation and stop gates. [Decision register](docs/PLAN_REVIEW_AND_DECISIONS.md) assigns unresolved choices/evidence to the phase that needs them. All application milestones remain pending.

For coding, start with [Claude handoff](docs/CLAUDE_HANDOFF.md), [progress](docs/PROGRESS.md), then P01 in [prompt pack](docs/PROMPT_PACK.md). The [combined Word document](documents/FundForge_Project_Spec_and_Claude_Handoff.docx) is generated from the current Markdown documents.

## First playable release

A crisis-rich two-chapter opening arc (20 simulated business days, through ordinary day21 opening administration) with two users, a reconciled long/short portfolio, borrow and margin, an investor redemption, fee accounting, separate firm runway, a committee decision, and a causal debrief. A buy/approve/chart demo is only an engineering foundation. The complete initial campaign expands that slice into all six chapters through ordinary day61 opening administration, with reproducible seeds, save/resume, failure endings and balancing evidence. These checkpoints include intervening weekend accruals, not a fresh Monday market valuation.

## Engineering direction

Next.js/TypeScript, FastAPI/Python, PostgreSQL; pure deterministic financial domain; fixed precision; immutable events and journal; as-of information access; versioned rules and fixtures. Begin with synthetic data and polling. Add workers, live providers, ML and optional read-only AI after the core game is sound. No external API is required to play the base campaign.

No trading framework is required for the initial game. Later research can use pandas, exchange_calendars and optional DuckDB; CVXPY/statsmodels need a specific evaluated advisory feature. SEO/marketing integrations are excluded from the current plan. No upstream code was copied, paid service activated, or deployment created in this revision.

The private repository is already set up. Do not rerun the legacy repository-creation scripts here. Nothing in this package represents a live fund, brokerage service, legal compliance certification, measured model result or completed software feature.
