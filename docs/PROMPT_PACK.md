# Copy-ready implementation prompts — v2.1

Use one prompt for one bounded task. The repository already exists. All application gates are pending. Model selection is performed in the actual client, not by claiming a prompt can switch its underlying model. The owner requested Astra/extra-high for this completed v2.1 critical review; verify available model names in the implementation environment.

## P01 — Inspect the redesigned game and freeze FF0

Read CLAUDE.md, docs/CLAUDE_HANDOFF.md, docs/PROGRESS.md, docs/DECISIONS.md and docs/MASTER_SPEC.md. Inspect repository and tools. Read REALISM_AUDIT, SIMULATION_ARCHITECTURE, GAME_SYSTEMS, FUND_ACCOUNTING and the first SEASON_SCENARIOS slice. Consult LIBRARY_RESEARCH before choosing dependencies. Check the dated calendar, per-date accrual, pre-provision participation, annual versus partial-redemption crystallization, post-flow risk and independent reconciliation. Identify concrete unresolved contradictions, not a new feature wishlist. Resolve routine choices; list any unresolved contract that blocks safe code. Produce a bounded FF0 task contract with schemas, owned paths and observable checks. Do not revert to the old paper-trading MVP. Do not generate the whole app or claim implementation results.

## P02 — FF0 scaffold

Implement the approved FF0 contract only. Pin actual supported runtimes and package managers, create minimal Next.js/FastAPI/PostgreSQL development scaffolding, config validation and CI. Define versioned command/event/scenario interfaces. Validate the authored scenario manifest, explicitly identifying any missing tape. No broad dashboard, provider connection or paid service. Run actual relevant checks and update PROGRESS with one next task.

## P03 — One financial contract

Implement exactly the selected FF1/FUND_ACCOUNTING contract and related acceptance cases. Use fixed precision and an immutable balanced journal. Provide independent expected arithmetic, not expected values obtained from the implementation. Separate fund, firm and investor series. Implement opening participation net plus reversible provision; preserve surviving HWM on partial redemption. Use ACT/365 management and ACT/360 settled borrow/debit calendar accrual with residuals. Test replay/reversal and meaningful boundaries. Treat legacy golden_scenario as a primitive fixture only. Report actual commands/results and pending cases.

## P04 — Execution, borrow and margin

Implement the selected FF2 transition with deterministic future-event eligibility, borrow/collateral/debt identities, settlement and deadline rules. Show a gap/recall/halt case and exact accounting. Check the entire constraint vector: covering can raise net exposure, redeeming can shrink margin equity, and pending returns keep borrow costs/collateral until settlement. A forced action can fail; preserve the deficit. No daily-bar invented intraday path, no LLM-owned prices, no unrestricted broker execution. Freeze the contract before adding presentation.

## P05 — Governance and transaction races

Implement FF3 for two human partners with jointly approved immutable sleeve charters and independent consent for exceptions. Test revoked/expired authority, combined commitments, idempotency collisions, edit/approve and cancel/fill races using real PostgreSQL. Atomically persist financial effects and durable publication state. No SQLite substitution or self-approved expansion of delegated scope.

## P06 — LPs and management-company survival

Implement the selected FF4 contract for investor notices/dealing, series fees/HWM, firm budget or trust. Preserve notice versus recognized payable versus cash payment. Distinguish fund NAV, restricted cash, company cash and fee receivable. Provide arithmetic and an event-order trace. Do not replace mechanics with cosmetic meters or free-text AI scoring.

## P07 — First complete playable opening arc

Deliver FF5 against verified engine APIs. Read the vertical slice in SEASON_SCENARIOS. Include research effort, thesis/hedging, partner negotiation, investor/financing/business choices, consequences and causal debrief. The operating partner needs independent agency. No fake model/provider results. Run a two-user flow through day20 dealing and ordinary day21 opening administration, including weekend accrual, disagreement, pause/resume and one crisis resolution; record confusion and actual duration.

## P08 — Bounded adversarial review

Review only this diff, its contracts and necessary dependencies. Return at most five reproducible defects with severity, violated invariant, exact path and expected/observed behavior. Prioritize fee/flow errors, collateral double count, authority races, future leakage and score exploits. Distinguish a definite defect from an open design question. Do not rewrite the architecture or start other agents.

## P09 — Campaign and balancing gate

Complete the selected FF6 chapter or balance task. Run matched seeded baseline policies and inspect concentration, cash-only, trust farming, replay rerolls and last-day obligation exploits. Keep rules immutable within a season. Report results with seeds and limitations. Do not claim a fun or balanced game solely because unit tests pass; include playtest evidence.

## P10 — OpenSEO spike

Read OPENSEO_INTEGRATION, LIBRARY_RESEARCH and the pinned inspected source paths. Verify every-app/open-seo remains the intended upstream; do not substitute OpenBB. Start with fixture observation → normalized as-of evidence card. Evaluate separate OpenSEO service versus small direct adapter without migrating the financial stack. Record exact data rights, credentials and real request/currency caps before any paid activation. Cover stale/missing/partial results, ambiguous-charge timeout and historical leakage. No live connection is required to complete the fixture spike. No copied code without license/notice records.

## P11 — Optional research and ML

Read LIBRARY_RESEARCH and SIMULATION_ARCHITECTURE. Select only the dependency needed for this measured task; do not install the candidate list. Use the same cost/execution engine as the game. Freeze point-in-time data and chronological split; define a simple baseline and a concrete target before training HMM or another model. Use filtered inference, avoid future normalization and record rejected candidates. Measure prediction/gameplay value separately from strategy return. LLM explanations have no financial mutation rights. No invented alpha or deployment evidence.

## P12 — Resume or diagnose

Read the small handoff and current Git state. Continue only the documented next task. If blocked, capture the failing command, smallest reproducer, invariant, attempted fixes and next diagnostic. After two failed repair cycles change the diagnosis rather than repeating prompts. Do not reload all docs or recreate the plan without a concrete conflict.

## P13 — Limited parallel work, only when requested

Freeze shared interfaces and choose disjoint tasks with separate ownership/worktrees. Keep migrations, journals and transaction contracts under one integrator. Use bounded outputs and actual acceptance evidence, integrate sequentially, and stop completed workers. Model names and agent support must be checked in the actual client. Never use parallelism to bypass permissions or assume extra usage quota.

## P14 — Evidence and handoff

Review RECRUITER_EVIDENCE. Build a truthful demo and evidence index from actual results. Clearly separate implemented, tested, measured, simulated and proposed. Update PROGRESS, source/rules manifests and docs affected by actual changes. Regenerate combined documents if canonical design changed. Do not add performance numbers or resume claims from aspirations.

## P15 — Implement one authored scenario contract

Read SEASON_SCENARIOS, fixtures/season_scenario.json, fixtures/scenario_cases.json and FUND_ACCOUNTING. Choose one case and freeze its prerequisites, phase ordering, public/hidden observations, executable tape, capacity and independently authored controls. Convert the design contract into a complete runnable fixture without inventing absent data. Implement success, failure and recoverable branches; run engine outputs against independent reference arithmetic. Keep paid services disabled. Record branch results and limitations. A valid manifest or expected-values JSON is not a playable scenario.

## P16 — Dependency or data-source decision

Read LIBRARY_RESEARCH, its 17 pinned evidence records and the proposed feature's acceptance contract. Recheck the exact release/license/module/API using current primary sources, including transitive/solver obligations. Separate software reuse from dataset display/retention/redistribution rights, credentials and real costs. Compare a small original implementation or existing dependency against the candidate. Return adopt/adapt/reference/defer/reject with one concrete integration boundary and actual evidence. Install only if the current task authorizes the implementation and no paid activation is needed; otherwise retain a fixture-based deliverable. Do not equate an API key with redistribution permission.
