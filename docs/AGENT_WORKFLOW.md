# Agents: adversarial review without a runaway budget

There are two different uses of agents: agents that help build this repository, and agents that act as simulated fund competitors. Neither gets a separate free quota. Subagents, parallel sessions and agent teams can consume more total usage; isolated context is useful for organization, not a guarantee of savings [S7–S10].

## Recommended development pattern

Default to one builder. For a high-risk financial/concurrency/security change, run one read-only reviewer after the builder's relevant checks pass. The reviewer reads the diff, the precise invariant and necessary neighboring code, then returns at most five concrete findings. The builder performs one repair pass; reviewer verifies only those repairs. Stop unless an actual blocker remains.

| Role | Permission / scope | Deliverable |
|---|---|---|
| Builder | Writes task-owned files in one branch | Working behavior and actual checks |
| Finance reviewer | Reads diff, ledger/risk contracts and tests | Reproduction of financial/race/leakage failures |
| Security reviewer | Reads diff, auth/session/API contracts | Reproduction of access/trust-boundary failures |
| Integrator | Owns schema/shared contracts and merges | Boundary checks and final handoff |

Run finance and security reviews sequentially when preserving budget. The supplied `.claude/agents` definitions are optional templates with read/search tools and inherited model selection; verify that those tool names/frontmatter are supported by the installed Claude version. Use the installed agent-management interface, commonly `/agents`, rather than assuming every version supports the same launch command. No template invokes itself or another agent.

Read-only tools cannot execute a reproduction. A reviewer should write the exact test/procedure to run; the builder runs it and records the result. Give a reviewer controlled shell/test access only if it is needed and configured intentionally. A prompt declaring “read only” is not an operating-system security boundary. Git worktrees isolate working files/branches, not credentials or network privileges.

## When parallel work is justified

Freeze interfaces and choose genuinely disjoint tasks. Example: implement the holdings read UI against a frozen API in one worktree, and add a standalone fixture importer in another. Do not parallelize the ledger schema, approval/reservation transaction, or one migration sequence across independent writers. UI and API work often depend on shared contracts; establish those first.

Git worktree example, after the repository has a clean committed baseline:

```bash
git status --short
git worktree add ../fundforge-ui -b feat/holdings-ui
git worktree add ../fundforge-data -b feat/fixture-import
```

Run a separate Claude session in each folder with a narrow task contract. Integrate one completed branch at a time through the normal review process; run cross-boundary checks. Shut down completed sessions, preserve commits/notes, then remove worktrees only after integration or explicit retention decisions. Do not remove an uncommitted worktree to save tokens.

A full agent team is an optional later tool, not the default. Verify support, experimental settings if any, current documentation, permissions and usage before activating it [S10]. No machine-specific enabling configuration is included in this package.

## “Agents against each other” as development competition

Useful competition has an external judge: fixed correctness tests plus a small benchmark. Choose one isolated algorithm, such as exposure calculation or timestamp filtering, and define its behavior before agents see it. Candidate A and B implement the same contract in separate branches. Evaluate correctness, readability, measured resource use and integration complexity. One round, then select and record a decision.

If both candidates fail, repair the shared contract/tests or investigate the common misunderstanding; do not spawn additional candidates indefinitely. Competing explanations alone are not evidence. Duplicating complete applications normally multiplies implementation and review effort and creates merge work without a useful experiment.

## AI funds against humans or each other

Build this only after historical replay and the deterministic financial engine work. An opponent receives a typed observation: permitted price/features as of cutoff, holdings/cash/commitments, mandate, recent eligible events and prior public game decisions. It emits at most three typed proposals or HOLD with a rationale. It receives no DB/admin credentials and no access to future data endpoints.

Run a passive benchmark and deterministic risk/trend baseline before an LLM opponent. All agents use the same data/cost/settlement rules. For AI-only committee funds, two labeled simulated agents can approve each other's proposals under the same versioning rule; this is separate from the two-human game and cannot approve human orders. Invalid actions are rejected by the backend. Deadline/timeout/no response means hold, not a risk override.

Evaluation: several frozen periods/scenarios and seeds, cost-sensitive returns, drawdown, turnover, breach/rejection rate, unsupported claims and inference cost. Keep a fixed provider request cap per season/run and a hard maximum output size. Cache permissible observations/explanations; do not cache actions across materially different portfolio states. Historical LLM opponents may know real events from training, so synthetic or anonymized blind tests are needed before claiming an information-fair contest.

No opponent is an autonomous real-money hedge fund. Report simulation limitations and use the contest primarily as an agent reliability benchmark. Do not reward an agent for bypassing a rule or for exploiting a data leak.

## Task contract template

```text
Task ID:
Objective / observable behavior:
Required inputs and specification sections:
Allowed paths:
Forbidden scope:
Shared contract/version:
Acceptance evidence:
Maximum review/repair rounds:
Stop condition:
Handoff format:
```

Token-saving measures here are project workflow choices. They do not prevent a provider usage limit from being reached, and additional API credits must remain the owner's explicit choice.
