# Claude handoff — FundForge v2.1

## Actual state

Private repository: https://github.com/krishbansalofficial/fundforge. Documentation-only, no frontend/backend/database/model/provider connection/deployment. The owner asked to rethink the whole product as a full hedge-fund game and evaluate OpenSEO, using Astra. The v2.1 critical review used Astra with extra-high reasoning, researched 17 pinned repositories and corrected the contracts; implementation remains pending.

The old $100,000, 30-day, mandatory-approval-for-every-trade plan is superseded. Current default: two firm partners manage $25m of outside LP capital and a separate $300k company over 60 simulated business days/six chapters. Fees, investor dealing, long/short financing, firm runway, committee governance and crises belong in the first playable game.

## Start

Read CLAUDE.md, this file, PROGRESS.md, DECISIONS.md, MASTER_SPEC.md, then the relevant game/accounting contracts. Inspect current Git state and installed tools. Do not read the generated combined document in addition to its source docs. Inventory installed skills by names once; do not assume a particular local Vercel installation or model syntax.

Use P01 in PROMPT_PACK.md to review contradictions and freeze FF0 contracts. Start only the requested bounded milestone. No application work was implicitly completed by generating this design. Do not recreate the repository or force-push it.

## Core experience

Two partners brief, allocate research effort, choose investments and capital/liquidity commitments, respond to an investor/broker/business event, advance a deterministic market clock, then inspect consequences. Delegated sleeves avoid an approval-clicking simulator; exceptions still require independent agreement. The operating partner has financing, LP and staffing/budget decisions of their own.

The first playable two-chapter arc must demonstrate a long/short book, borrow/margin, an investor flow, fee accounting, separate company runway, a consequential disagreement and a causal debrief. A chart and order ticket are foundation work, not the product gate.

## Important contracts

- FUND_ACCOUNTING owns event ordering, balances, fees/series, cash settlement and financial conventions.
- GAME_SYSTEMS owns actions, roles, trust, house rules, progression and evaluation.
- SEASON_SCENARIOS owns authored arcs and the vertical slice.
- MASTER_SPEC owns product scope and the canonical document map; SIMULATION_ARCHITECTURE owns software interfaces.
- REALISM_AUDIT lists prioritized gaps and industry-versus-contract-versus-game distinctions.
- LIBRARY_RESEARCH and fixtures/library_review.json record17 actual source/license reviews. No dependency was installed.
- ACCEPTANCE_TESTS lists required observable behavior, not executed tests.
- OPENSEO_INTEGRATION pins inspected upstream code and separates optional research from the engine.

Preserve both simulated time and wall-clock audit time. External research must never reveal a future historical fact. Treat all numerical campaign settings as explicit fictional house rules. Never represent simulated LP terms as universally applicable law or real fund compliance.

## Delivery boundaries

FF0–FF4 build foundations. FF5 is a complete two-chapter opening arc through ordinary day21 opening administration. FF6 is the full campaign through ordinary day61 opening administration and reliability/balance gate. FF7 adds optional data/research/ML. All pending. Fixture mode requires no credentials. An OpenSEO assessment is not an installed integration; real API spend remains disabled.

At task end record changed behavior, actual checks and limitations, then update PROGRESS with one next task. Use a bounded financial/security reviewer when authorized. Do not launch extra agents or redesign the whole product after every milestone.

## Critical v2.1 contracts

Opening series participation is net capital plus reversible incentive provision. Management fee1.5% ACT/365 and settled borrow/debit ACT/360 accrue on calendar dates, including weekends; statistical252 annualization is a different calculation. Performance crystallizes annually on Dec31 and pro rata on dealt redemptions. A partial redemption does not ratchet surviving HWM. The Jan–Mar campaign does not pay an annual incentive merely because it ends.

Check all constraints on reductions: a short cover can increase net exposure, and a dealt redemption shrinks equity before payment. Borrow persists until settled return. Independently authored broker/admin controls can reveal a balanced but wrong journal. Corporate actions cover cash distributions and integer splits only. The synthetic calendar deliberately ignores real exchange holidays.

The minimal first-playable stack is the planned app/database plus our own deterministic domain. pandas/exchange_calendars, optional DuckDB, then optional CVXPY/statsmodels belong to justified FF7 tasks. OpenBB/OpenSEO are possible data adapters; LEAN/Nautilus are references; rateslib default rights and vectorbt Commons Clause prevent treating them as unrestricted dependencies. Recheck exact versions before reuse.

A Renewal ending is conditional continuation, not proof of a sustainable firm. At constant25m,1.5% annual management fees are375k against1.04m annualized20k/week overhead:665k structural gap before incentive income/capital/cost changes. The300k opening company balance is15 weeks at base cost; four weeks of remaining runway does not finance another12-week season. Display this gap and require an explicit continuation budget/recapitalization contract; do not award sustainability from AUM or provisional incentive alone.
