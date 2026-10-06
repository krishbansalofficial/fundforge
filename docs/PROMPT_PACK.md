# Copy-ready implementation prompts — v2.0

Use one prompt for one bounded task. The repository already exists. All application gates are pending. Model selection is performed in the actual client, not by claiming a prompt can switch its underlying model. The owner requested Astra/high for the completed design review; verify available model names in the implementation environment.

## P01 — Inspect the redesigned game and freeze FF0

Read CLAUDE.md, docs/CLAUDE_HANDOFF.md, docs/PROGRESS.md, docs/DECISIONS.md and docs/MASTER_SPEC.md. Inspect repository and tools. Read GAME_SYSTEMS, FUND_ACCOUNTING and the first SEASON_SCENARIOS slice. Identify concrete contradictions in event order, fee series, collateral, LP dealing, delegated authority and failure conditions. Resolve routine choices; list any unresolved contract that blocks safe code. Produce a bounded FF0 task contract with schemas, owned paths and observable checks. Do not revert to the old paper-trading MVP. Do not generate the whole app or claim implementation results.

## P02 — FF0 scaffold

Implement the approved FF0 contract only. Pin actual supported runtimes and package managers, create minimal Next.js/FastAPI/PostgreSQL development scaffolding, config validation and CI. Define versioned command/event/scenario interfaces. Validate the authored scenario manifest, explicitly identifying any missing tape. No broad dashboard, provider connection or paid service. Run actual relevant checks and update PROGRESS with one next task.

## P03 — One financial contract

Implement exactly the selected FF1/FUND_ACCOUNTING contract and related acceptance cases. Use fixed precision and an immutable balanced journal. Provide independent expected arithmetic, not expected values obtained from the implementation. Separate fund, firm and investor series. Test replay/reversal and meaningful boundaries. Treat legacy golden_scenario as a primitive fixture only. Report actual commands/results and pending cases.

## P04 — Execution, borrow and margin

Implement the selected FF2 transition with deterministic future-event eligibility, borrow/collateral/debt identities, settlement and deadline rules. Show a gap/recall/halt case and exact accounting. A forced action can fail; preserve the deficit. No daily-bar invented intraday path, no LLM-owned prices, no unrestricted broker execution. Freeze the contract before adding presentation.

## P05 — Governance and transaction races

Implement FF3 for two human partners with jointly approved immutable sleeve charters and independent consent for exceptions. Test revoked/expired authority, combined commitments, idempotency collisions, edit/approve and cancel/fill races using real PostgreSQL. Atomically persist financial effects and durable publication state. No SQLite substitution or self-approved expansion of delegated scope.

## P06 — LPs and management-company survival

Implement the selected FF4 contract for investor notices/dealing, series fees/HWM, firm budget or trust. Preserve notice versus recognized payable versus cash payment. Distinguish fund NAV, restricted cash, company cash and fee receivable. Provide arithmetic and an event-order trace. Do not replace mechanics with cosmetic meters or free-text AI scoring.

## P07 — First complete playable opening arc

Deliver FF5 against verified engine APIs. Read the vertical slice in SEASON_SCENARIOS. Include research effort, thesis/hedging, partner negotiation, investor/financing/business choices, consequences and causal debrief. The operating partner needs independent agency. No fake model/provider results. Run a two-user flow through day20 dealing, including disagreement, pause/resume and one crisis resolution; record confusion and actual duration.

## P08 — Bounded adversarial review

Review only this diff, its contracts and necessary dependencies. Return at most five reproducible defects with severity, violated invariant, exact path and expected/observed behavior. Prioritize fee/flow errors, collateral double count, authority races, future leakage and score exploits. Distinguish a definite defect from an open design question. Do not rewrite the architecture or start other agents.

## P09 — Campaign and balancing gate

Complete the selected FF6 chapter or balance task. Run matched seeded baseline policies and inspect concentration, cash-only, trust farming, replay rerolls and last-day obligation exploits. Keep rules immutable within a season. Report results with seeds and limitations. Do not claim a fun or balanced game solely because unit tests pass; include playtest evidence.

## P10 — OpenSEO spike

Read OPENSEO_INTEGRATION and the pinned inspected source paths. Start with fixture observation → normalized as-of evidence card. Evaluate separate OpenSEO service versus small direct adapter without migrating the financial stack. Record exact data rights, credentials and real request/currency caps before any paid activation. Cover stale/missing/partial results, ambiguous-charge timeout and historical leakage. No live connection is required to complete the fixture spike. No copied code without license/notice records.

## P11 — Optional research and ML

Use the same cost/execution engine as the game. Freeze point-in-time data and chronological split; define a simple baseline and a concrete target before training HMM or another model. Use filtered inference, avoid future normalization and record rejected candidates. Measure prediction/gameplay value separately from strategy return. LLM explanations have no financial mutation rights. No invented alpha or deployment evidence.

## P12 — Resume or diagnose

Read the small handoff and current Git state. Continue only the documented next task. If blocked, capture the failing command, smallest reproducer, invariant, attempted fixes and next diagnostic. After two failed repair cycles change the diagnosis rather than repeating prompts. Do not reload all docs or recreate the plan without a concrete conflict.

## P13 — Limited parallel work, only when requested

Freeze shared interfaces and choose disjoint tasks with separate ownership/worktrees. Keep migrations, journals and transaction contracts under one integrator. Use bounded outputs and actual acceptance evidence, integrate sequentially, and stop completed workers. Model names and agent support must be checked in the actual client. Never use parallelism to bypass permissions or assume extra usage quota.

## P14 — Evidence and handoff

Review RECRUITER_EVIDENCE. Build a truthful demo and evidence index from actual results. Clearly separate implemented, tested, measured, simulated and proposed. Update PROGRESS, source/rules manifests and docs affected by actual changes. Regenerate combined documents if canonical design changed. Do not add performance numbers or resume claims from aspirations.
