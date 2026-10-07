# FundForge v2.2: critical review and decisions

7 October 2026. Planning only. This review supplements the useful v2.1 research; it does not claim implemented software.

## Verified state and blunt assessment

Starting HEAD: `51eda0c1aa806e0c9f94b7e2527a013b4dedb77f`. `git status --porcelain=v1` was empty. Recent history is the v2.1 audit (`51eda0c`), game redesign (`5ae8a5a`), document package (`797e90d`), and initial README (`1c04c3f`). Tracked instructions are `CLAUDE.md` and two read-only reviewer files under `.claude/agents`; no AGENTS.md was found. Canonical sources are in `docs/`, design JSON in `fixtures/`, generated Markdown/Word in `documents/`.

The local project is a substantial specification, not a Python/Pydantic foundation. There is no backend, frontend, database schema, dependency manifest, application test directory or 26-test suite. The two Python scripts build/validate documentation. We did not inspect another checkout or infer work from an earlier conversation. Repository visibility was not freshly verified remotely.

The design's strengths are its connected economics, separate fund/firm claims, realistic failure distinctions, delegated authority, synthetic information timing and original deterministic engine. Its weakness is that persuasive scenario prose and narrow arithmetic checks conceal missing executable contracts. Case2 actually fails a constraint its success text promises. Some supposed alternatives are dominated or end before their obligations resolve. Broad FF0–FF4 gates defer discovering whether two humans enjoy the game. More libraries will not solve these problems.

| Category | Local evidence | Status |
|---|---|---|
| Implemented | Documentation builder and packaging/reference validator | Tooling only; portability fixed in this revision |
| Tested previously / rerun here | Independent arithmetic and package consistency | See PACKAGING_VALIDATION for actual current command/results |
| Proposed | All economic modules, UI, persistence, scenarios, recovery | No application behavior established |
| Unresolved | Full opening campaign tape, runtime pins, economic feasibility under every path, enjoyment | Explicit milestone gates; no invented results |

## Prioritized gaps and acceptance

| ID / priority | Evidence | Consequence | Correction / dependency | Acceptance criterion |
|---|---|---|---|---|
| D01 / P0 | SEASON_SCENARIOS §8 Case2 inherits five $3m equities; pay-all NAV $18,995,800 | Each is 15.793%, outside 15% cap; gated branch is 15.001517% | Replace inherited basket with fully specified <=$2.5m names; FF0a authoring before FF2b risk | Every issuer, sector, ETF, gross/net, initial/maintenance and cash test checked at every reference branch and actual execution prefix |
| D02 / P0 | Scenario JSON `not_yet_compiled`, FF0 versus P01 disagreement | Schema-valid manifest may be mistaken for runnable game | SCENARIO_CONTRACTS supplies complete design schedules; FF0a compiles Case1 only; full opening arc at FF5a | Coverage report, opening balances/series/settled borrow, dated events, command scripts, independent oracle ledger; status never says runnable until engine exists |
| D03 / P0 | FUND_ACCOUNTING §4 collateral lacks unsettled-lot mapping | Short gap can reserve proceeds twice or omit a top-up; cure sale sweep can spend needed cash | Explicit collateral lots and linked cover release; FF2a | Unsettled short marked above sale price, partial cover, failed settlement, split and duplicate delivery conserve collateral/resources |
| D04 / P0 | FUND_ACCOUNTING §7 says forced actions first; GAME_SYSTEMS §8 offers voluntary response | Engine could liquidate before timely player cure | Separate due recall buy-ins from pending margin escalation; FF2b | Timely valid voluntary cure consumes available event first; residual deficit then forced; expired recall priority preserved |
| D05 / P1 | Case2 ends day41, leaves gate claims and unnamed catalyst | Gate upside/recovery cannot be evaluated | Extend same fixed tape to day61; describe preserved broad exposure and floating claims | Pay-all and gate scripts honor obligations through day61, with fee/carry bridge and residual units shown; returns not used as universal strategy proof |
| D06 / P1 | Case3 hire after known break, no relevant future use | Costly dominated action masquerades as strategy | Remove active hire choice from challenge; retain cash arithmetic as forecast counterexample | Active choices are report/attention/capacity/admission; no success count earned by intentionally worse staffing branch |
| D07 / P1 | GAME_SYSTEMS §11 operating role mostly previews | Second player may only calculate/sign | TreasuryReserve and SelectReplacementBorrow commands; existing attention allocation | Each role changes at least two material outcomes/opportunities in the opening playtest; log actor/effect |
| D08 / P1 | Precision uses 'at least'; hashing and retry precedence unspecified | Lost residuals, unstable replay, committed retry conflicts | Exact architecture wire/context/coordinator contracts; FF0b/FF3a | HALF_EVEN/negative zero/overflow/round-trip canonical vectors; stale-version retry returns original committed result without effects |
| D09 / P1 | FF0–FF4 encompass nearly whole engine before human play | Product risk discovered too late | Split milestones; internal short Case1 experiment FF3b | Two human roles complete a crisis before campaign/UI expansion; retain failure observations |
| D10 / P1 | Validator default cp1252 and eager docx import | Document evidence cannot be repeated locally | Explicit UTF-8; standard-library Word fallback; documentation tooling only | Bare documented build/validate commands pass without package installation; structural validation distinguished from rendering |
| D11 / P1 | Case3 fee seed and no per-series history; Case2 'after charges' called day39 | Warm starts can omit liabilities or accrue twice | Distinguish unit-test checkpoints from dated challenge openings; SCENARIO_CONTRACTS | All intervening dates accrue; exact full-path numbers independently computed before release; isolated oracles never substituted for accrued path |
| D12 / P2 | Library/source reviews already done 6 October | Repeated research distracts from game; SEO outside task | Retain pinned finance-library evidence; exclude SEO from all current plans/prompts/bundle | No SEO milestone/dependency; optional library receives its own unmet-requirement gate |

## Independent reviewer reconciliation

Three bounded read-only agents were explicitly requested and used: financial realism (PM/CRO/accountant/COO), gameplay, engineering/evaluation. Each returned at most five findings. No recursive delegation or reviewer file edits occurred. The following records all returned recommendations; references name the original v2.1 sections, not stable post-edit line numbers.

| Reviewer / finding | Disposition | Reason and destination |
|---|---|---|
| Finance F1: Case2 post-flow issuer breach | Accept | Concrete arithmetic defect; corrected basket and A22 |
| Finance F2: replacement transfer/cutoff undefined | Accept | Explicit day14 cutoff/day15 settled transfer and fee switch; FUND_ACCOUNTING §10 / V26 |
| Finance F3: retained return collateral ambiguous | Accept | Freeze covered-share reference target through settlement; FUND_ACCOUNTING §10 / V25 |
| Finance F4: termination economics missing | Accept bounded policy | Ten-business-day authored recovery horizon, actual liquidation/final dealing, persistent claims; V31–V32. Full statutory waterfall deferred |
| Gameplay G1: dominated Case3 hire | Accept removal; reject adding an artificial hire benefit | Smallest correction preserves truthful automatic accounting; §8 Case3 |
| Gameplay G2: gate payoff and later plan missing | Accept | Extend horizon and fixed liquidity plan; SCENARIO_CONTRACTS Case2 |
| Gameplay G3: operating role may only approve | Accept | Commands and resource consequences; GAME_SYSTEMS §12 |
| Gameplay G4: evidence timing/content incomplete | Accept | Exact evidence matrix and wait path; scenario schedules |
| Gameplay G5: scenario proof versus fun proof; measured protocol | Accept | Separate financial scripts from human studies; ACCEPTANCE_TESTS §v2.2 |
| Engineering E1: full scenario artifact gate | Accept in bounded form | Compile one case next; reject making all three engines/full campaign a prerequisite to starting accounting |
| Engineering E2: earlier human experiment | Accept | FF3b internal challenge, explicitly not first releasable game |
| Engineering E3: exact precision/canonical form | Accept | SIMULATION_ARCHITECTURE §v2.2 |
| Engineering E4: retry/version precedence and race oracles | Accept | Coordinator order and C13–C16 |
| Engineering E5: portable validator / optional generation | Accept | Documentation-tooling correction; no application implementation |

## Retain, simplify, remove, defer

Bounded follow-up reviews accepted eight corrections: finance closed the cheap BRIN inventory bypass and placed accrual before certified dealing; gameplay fixed instrument-ID price assignment, added day14 pre-EXEC_B barrier and simplified Case3 capital-decline path without a research-alpha claim; engineering moved pure LP/firm payment to FF2c before prototype, separated readiness bookkeeping revision and corrected cumulative residual recurrence/rate-change carry/tie bound. No reviewer edits or recursive delegation; these are document corrections, not economic-test results.

Retain one USD equity long/short fund, one fictional prime broker, distinct investor series/firm cash, calendar carry, partial fills, initial versus maintenance margin, real investor obligations, restrictions, independent controls, causal explanations and responsible winddown. These interactions are the game.

Simplify administration into automatic accrual/reconciliation/report production; surface meaningful exceptions. Four instruments suffice for the releasable opening arc; twelve remain the full campaign ceiling. Use authored stress sensitivities rather than covariance fitting. Commission is zero in these challenges; explicit spread/impact remains. No new dashboards, approval layers or distributed services.

Remove active Case3 hiring and its claim to a second strategic success path. Remove SEO/marketing from current implementation scope, prompts and generated package; preserve the old assessment as archived research only. Remove the full frontend/DB scaffold from the immediate FF0a task. Reject a production trading framework, purchasable accurate accounting, guaranteed research alpha, hidden player-targeted shocks and free fund-to-firm bailout.

Defer staffing gameplay to the full campaign where a capability must compete with a defined task; defer real data, optimizers, ML, AI tutors, asynchronous leagues, derivatives, taxes, multi-currency and real broker execution. No scenario or playtest result is declared complete. A referee-like NPC cannot provide the second human signature.

## Rigor and limitations

The graduate-level claim is falsifiable: independent financial derivations, invariant conservation, fixed-tape replay, fault/race evidence, controlled balance experiments and candid human-study results. Hypotheses and failure observations matter more than feature count. Synthetic pricing/counterparty rules are not empirical hedge-fund calibration. Fictional notices/margin priorities are contracts, not universal practice. Full campaign content and release compatibility remain unresolved. Next task is precisely FF0a in IMPLEMENTATION_HANDOFF, not feature implementation during this review.
