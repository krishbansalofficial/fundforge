# Copy-ready Claude prompts

This private repository is already set up: start with P01. P00 is retained only for creating a separate future repository. Use one prompt at a time inside the cloned repository. Replace bracketed placeholders. The initial prompt may load the complete brief; later prompts should load only their named working set. “Think carefully” means examine tradeoffs and failure modes and provide a concise decision rationale, not reveal private chain-of-thought or spend unlimited tokens.

## P00 — Create a separate private repository (optional)

```text
I want this documentation package in a new private GitHub repository named fundforge on my authenticated personal account. Inspect README.md and the relevant create-private-repo script. Verify the current folder and that only the intended documentation/templates are included. Check Git/GitHub CLI authentication without displaying secrets. Run the script if available; a name collision must stop without changing an existing repo. Verify isPrivate using gh repo view and give the actual URL. If a required tool/authentication is missing, tell me the exact local step and do not claim creation succeeded. Do not deploy the app or upload my resume.
```

## P01 — Think properly; inspect and critique first

```text
Read CLAUDE.md, docs/CLAUDE_HANDOFF.md, docs/PROGRESS.md, docs/DECISIONS.md and docs/MASTER_SPEC.md. Think carefully about financial correctness, cooperative gameplay, concurrency, settlement, historical leakage, ML validity and implementation scope before editing code. Inspect the repository and tool versions. Inventory my installed Vercel skills by names/descriptions only, then identify the one or two useful skills for each future phase; do not load every skill.

Give a concise decision memo: concrete contradictions/blockers; chosen architecture with reasons; five highest-risk failure modes and their tests; dependency-ordered milestones; and the smallest playable slice. Distinguish proposed features from implemented evidence. Keep this memo under 1,000 words. Update only actual decisions and progress. Do not build multiple stacks or launch agents. Stop after the review and tell me the exact M0 task contract.
```

## P02 — Scaffold only

```text
Implement M0 from docs/IMPLEMENTATION_PLAN.md. Read CLAUDE.md and docs/PROGRESS.md plus only needed architecture/security sections. Inspect existing files before changes. Create a minimal Next.js/TypeScript frontend, FastAPI backend, development PostgreSQL setup, package/lock configuration and minimal CI checks. Add a health route/page and domain interfaces. Do not implement the full dashboard, trading logic, ML or paid services. Pin and verify compatible versions using current official docs when needed. Run fresh-install and basic lint/type/test checks that you actually configure. Record exact commands/results and next task in docs/PROGRESS.md. Stop at M0.
```

## P03 — Implement one financial contract

```text
Implement [M1 or one clearly named subtask]. Read CLAUDE.md, docs/PROGRESS.md, master-spec accounting/settlement sections, docs/ACCEPTANCE_TESTS.md and fixtures/golden_scenario.json. Allowed edit areas: backend/domain/, backend/tests/domain/, and the progress/decision notes. If the scaffold uses different paths, map them first and record the mapping.

Use deterministic Decimal arithmetic, explicit rounding, FIFO, balanced journal entries and exact unit-based P&L allocation. Implement only the chosen subtask with meaningful independent arithmetic/replay tests. Do not change the frontend, auth or schema unless the task explicitly owns them. Do not add AI. Run relevant checks once after changes. Stop after two failed repair cycles and report the smallest reproducible blocker. Finish with behavior, files, actual evidence, limitations and one next task, under 400 words.
```

## P04 — Approval and concurrency boundary

```text
Implement [M2/M3 subtask] for version-bound partner approval and transactional execution. Read the order lifecycle, backend concurrency and acceptance-test sections only, plus current code/contracts. Allowed paths: [exact backend/module paths, migrations if owned, corresponding tests]. Use actual PostgreSQL concurrency tests.

Prove: proposer cannot self-approve; edits invalidate prior approval; parallel accepted orders cannot overspend; repeated execution/approval requests cannot duplicate effects; reservation-to-payable conversion is atomic; cancel-versus-fill yields one valid outcome. Risk check and posting must share the transaction and coherent execution snapshot. Record at-least-once delivery assumptions rather than claiming exactly-once messaging. Do not add WebSockets or ML. Stop when the scoped evidence gate passes; update the handoff.
```

## P05 — One playable frontend feature

```text
Implement [specific screen/flow] from the UI and daily-game sections. Read current API contracts and one relevant installed Vercel skill after confirming its instructions. Allowed edits: [frontend paths and UI tests where needed]. Aim for a readable cooperative game with restrained styling, not high-fidelity art or a complex trading terminal.

Show the shared server timer, partner state, virtual-capital label, as-of data and clear queued/filled/rejected/expired/offline states where relevant. Use the API's authoritative values; do not calculate balances in browser state. Include keyboard/mobile/reduced-motion behavior. Verify the actual flow with two test identities or explain the missing dependency. Do not change backend financial rules or invent placeholder performance. Stop after this flow works and record evidence.
```

## P06 — Bounded adversarial review

```text
Review only [diff/commit] and necessary neighboring contracts. Focus on [financial correctness OR authorization OR backtest leakage]. Do not edit code or launch subagents. Spend one review pass. Return at most five material findings, each with severity, precise location, violated invariant and a minimal reproduction/test case. Prefer evidence over speculative refactoring. If no material finding exists, say so. Do not re-review the whole repository or propose new features. Keep output under 600 words. The builder will decide and implement one bounded repair pass.
```

## P07 — Resume from a clean session

```text
Read CLAUDE.md and docs/PROGRESS.md. Check Git status, branch and relevant latest commit. Use the handoff's actual evidence as state; do not assume pending work is complete. Continue only [next task ID]. Read its named specification sections and exact implementation paths. Reuse established decisions and installed dependencies. Do not rebuild the architecture or scan the entire repository. If handoff and code disagree, inspect the smallest relevant area and record the correction. Complete the scoped task, run its necessary checks, update progress and stop.
```

## P08 — Diagnose without endless retries

```text
Investigate this specific failure: [paste concise error and command]. Read only [test/module/contract]. First reproduce it once and identify the failing invariant. Make the smallest justified repair within [allowed paths], then run the relevant check. Maximum two repair cycles. If unresolved, checkpoint the reproduction, attempted fixes, current hypothesis and required next evidence. Do not reinstall the stack, rewrite unrelated modules or run broad suites repeatedly. Do not claim success without the original failure check passing.
```

## P09 — Backtesting and leakage audit

```text
Implement/audit [M8 subtask]. Use the same domain/risk/execution engine as paper play. Read master-spec data/backtest sections and matching acceptance cases. Freeze universe, dataset checksum, cutoff, availability fields, split dates, cost model and settlement-era policy before running comparisons.

Test next-event execution, future-data mutation independence, training-only fitted transforms, no smoothed HMM inference, correct corporate actions/dividends and benchmark convention. Compare simple baselines with identical costs. Publish actual run config, outputs and limitations; do not pick the best period after inspecting results. No frontend redesign, new models or agent teams. Update progress and stop at the named experiment gate.
```

## P10 — A genuine ML release gate

```text
Implement [M9/M10 subtask] for baseline versus HMM regime inference. Read only ML/evaluation sections and current feature/backtest contracts. Define an objective and chronological evaluation before training. Fit features/scalers/model on permitted history; use filtered state probabilities and training-only state labels. Log reproducible experiments and candidate artifacts, then promote only if the explicit baseline gate passes. If it fails, retain the baseline and record why.

Add as-of/model/feature version, stale/failure behavior and measured inference checks appropriate to the task. Do not equate latent-state posterior with probability of price decline. Do not fabricate accuracy, profitable edge or deployment claims. Finish with measured evidence and limitations.
```

## P11 — Limited parallel work

```text
Use at most two writing sessions in separate Git worktrees for these independent tasks: [task A with owned paths] and [task B with disjoint paths]. Freeze shared contracts first. No shared migration/schema edits and no nested delegation. Each task has one acceptance gate and returns under 300 words. Close each worker when finished. Integrate one branch at a time and run shared-boundary checks after integration. If a task depends on another's unfinished output, run sequentially. Do not create two whole apps or run an ongoing debate.
```

## P12 — Two candidate implementations, one experiment

```text
Compare two small implementations of [isolated unresolved function]. Write the fixed interface and independent acceptance/benchmark inputs first. Give each candidate a separate worktree and the same bounded scope. No edits outside [paths], no paid calls, no recursive agents. Compare correctness first, then clarity, measured latency/memory and maintenance cost. Select one, document evidence/tradeoffs and discard the losing implementation from the active branch. One comparison round only. Do not infer better code from an agent's confidence.
```

## P13 — Final recruiter evidence and handoff

```text
Inspect the implemented system against docs/RECRUITER_EVIDENCE.md and the milestone gates. Summarize what actually works, actual test/load/evaluation results, known limitations and how to reproduce the demo. Produce backend and ML resume bullets using only measured results, with placeholders for missing values; do not fill them from targets. Rewrite the README around final behavior, with setup and a five-minute demo. Keep the project paper-only and distinguish experimental models from deployed ones. Stop after verified documentation is updated.
```

## P14 — Preserve remaining usage

```text
I am preserving my remaining subscription usage. Work only on [small task]. Use one session and no agent team. Read only CLAUDE.md, docs/PROGRESS.md, [relevant spec sections] and [paths]. Reuse established decisions. No feature expansion, exhaustive explanation, repeated unchanged checks or UI redesign. Necessary validation still runs. Check the available usage/status display at the start and checkpoint before optional work. Do not enable API billing or usage credits. Record progress and one next task, then stop. This instruction reduces scope; it is not a hard token quota.
```
