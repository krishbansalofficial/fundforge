# Development and simulated-agent workflow

The 6 October v2.1 critical review explicitly used Astra with extra-high reasoning at the owner's request. That completed design task does not imply any model, opponent or application is deployed.

Default implementation workflow: one builder owns the bounded task. For a high-risk accounting, concurrency, information or security boundary, use one scoped reviewer when authorized. Reviewer returns at most five reproducible findings; builder repairs, then verifies the changed boundary. No recursive delegation or unlimited debate. Separate worktrees prevent file collisions, not credential access. Verify agent/model syntax in the actual environment.

| Role | Ownership | Evidence |
|---|---|---|
| Builder | Task paths and implementation | Observable behavior plus actual checks |
| Finance reviewer | Read relevant diff/contracts | Arithmetic or transition counterexample |
| Security reviewer | Read auth/data/tool boundaries | Reproduction or precise denied-access expectation |
| Integrator | Shared schema, migration and event contracts | Cross-boundary consistency |

Parallel work is useful only after shared interfaces are frozen and the user has requested it or applicable instructions allow it. Never split the same ledger/approval/migration contract across independent writers. A bounded alternative-implementation experiment needs a fixed external correctness criterion; comparing persuasive explanations is not evidence.

## In-game AI

Base campaign NPCs are deterministic, stateful rules. A later optional AI opponent receives only permitted as-of observations, its balances, authority and eligible actions. Typed proposals go through the same server checks and costs. It cannot approve a human's committee exception or access future prices, administrative credentials or external historical browsing.

Start with passive and deterministic baseline policies. Optional LLM rivals require a request cap, output bounds and deterministic timeout/malformed-action fallback. Historical event memorization can make apparently blind contests unfair; synthetic held-out scenarios and explicit limitations are necessary. No agent may change authoritative prices, NAV, fees, trust, scores or contractual deadlines through prose.

The tutor explains supplied verified facts with source/time references. Untrusted research never becomes a privileged instruction. Neither fictional research credits nor the existence of a coding subscription authorizes additional real API spend.

## Task contract

Record objective, input contracts/versions, allowed paths, forbidden scope, dependencies, acceptance cases, actual commands, review boundary, stop condition and one next task. Keep context bounded; preserve decisions and failing evidence when pausing. Do not make usage-limit or weekly-completion promises.
