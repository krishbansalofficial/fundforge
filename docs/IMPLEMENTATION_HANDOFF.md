# Precise implementation handoff: FF0a only

> **Superseded 7 October 2026 by [REPLAN_V3](REPLAN_V3.md).** FF0a's hand-built full dated oracle is replaced by FUND_ACCOUNTING §6 oracle tests + property tests; implementation follows M0–M6. Content below is retained as v2.2 history.

7 October 2026; source plan v2.2. No feature implementation occurred in this planning update.

Planning revision 2.2-M1 expands all 20 milestones through the final FF8 gate in [MILESTONE_PLANS](MILESTONE_PLANS.md). [PLAN_REVIEW_AND_DECISIONS](PLAN_REVIEW_AND_DECISIONS.md) assigns unresolved choices/evidence to their due phases. Read the selected detailed package before starting; a roadmap row alone is not an implementation brief. This continuation entered an already modified planning tree; the original clean-entry statement below refers to the first v2.2 review. Preserve the combined changes. The user has now explicitly authorized committing/pushing this completed planning package; no application work or installation is authorized by that request.

## Verified starting point

Local `C:\Users\krish\fundforge`, original review entry HEAD `51eda0c1aa806e0c9f94b7e2527a013b4dedb77f` was clean; full-milestone continuation preserved its uncommitted diff. The combined27-file planning package is now committed as `a404948` and successfully pushed to `origin/main`; this follow-up records publication evidence. Inspect current HEAD/status on continuation and preserve any new work. Documentation-only: no Python/Pydantic application or26 tests. Instructions, recent history, all requested docs, fixtures, two Python scripts and reviewer prompts were inspected. IMPLEMENTATION_HANDOFF was added by this planning task. Remote repository visibility/other checkouts remain unverified.

## Exact next milestone

**FF0a: compile Case1's v2.2 authored schedule into a complete validated immutable fixture, command scripts and independently calculated dated financial oracle.** This is the next implementation task, not authorization to build features during this review. Read CLAUDE_HANDOFF, DESIGN_REVIEW_V2_2, SCENARIO_CONTRACTS shared+Case1, FUND_ACCOUNTING, architecture numeric/command contracts and X01–X07 below. Do not run the old full-scaffold FF0 prompt.

Inputs: isolated arithmetic cases and explicit12–21 warm start/default tape/evidence/recall/replacement schedules. Proposed outputs: `fixtures/compiled/case1.v2_2.json`, `fixtures/commands/case1_{early_cover,replacement,forced_recovery}.json`, `docs/oracles/CASE1_DATED_ORACLE.md` with full daily fund/series/firm/claims/residual table, coverage/hashes, `backend/contracts/` loader/schema, `scripts/validate_scenarios.py`, `tests/contracts/` meaningful rejection checks. These paths do not yet exist.

Own only contracts/materialized records/independent worksheet/schema-loader/checks. Use standard-library validation for FF0a; reconsider Pydantic only at a demonstrated API/schema boundary. Economic truth must not depend on coercion. No economic reducer, Next.js/FastAPI/DB scaffold, provider calls, SEO/AI or deployment in FF0a. Source-control publication is separately authorized in the current planning session and does not authorize features.

| Case | Exact required observation |
|---|---|
| X01 complete coverage | Every business date12–20 has OPEN_ADMIN/PUBLIC_MARK/EXEC_A/EXEC_B/CLOSE, all intervening calendar accruals, and day21 admin. All twelve marks/volumes/borrow/IDs, defaults materialized; end before21 market |
| X02 warm start | Assets32.5m−shorts5m−debt2.5m=25m;100k/80k/70k units,H100,F0; company240k/payroll payable4k. All economic/settled/borrow quantities, lot bases, claims explicit and independently checked |
| X03 chronology | Evidence after assignment; recall13, acceptance cutoff14, transfer15, stress16, sale opportunity18, BEAM halt20, dealing20/payment21. Future file data never player-visible at12 |
| X04 borrow | Timely acceptance transfers1,250 shares15 with no double loan; old fee ends/replacement40% starts prospectively. Late selection rejected, no cure. Cover satisfies execution deadline but fees/collateral persist through pending return |
| X05 independent dated oracle | Three scripts list actors/commands/budgets/approvals, all dated fee/carry/payroll/collateral/settlement/series/redemption postings and terminal balances. Success satisfies actual constraints, not100k bounds. Failure distinguishes forced control loss from default. Expected values do not come from a future reducer |
| X06 rejection | Missing date/mark, duplicate ID, unknown action/instrument, float/NaN/infinite money, negative volume, wrong units, conflicting fee timing, timestamp disorder, uncovered obligation each produces specific error, not silently valid package |
| X07 reproducibility/status | Repeated compile/load identical canonical bytes/hash including residuals; schema/rule/tape/control/command versions and source hashes. Label SCHEMA_VALID_AUTHORED_FIXTURE, never PLAYABLE/PASSED_ENGINE. Loader tests distinct from package arithmetic |

Done when X01–X07 evidenced, full-path numbers independently derived, conflicts resolved, actual commands/hashes retained, bounded review completed and handoff advances to FF0b. If a script is infeasible, report exact constraint/shortfall and change only a versioned authoring decision, then recalculate. Never fit a hidden tape to a player's holdings. Stop after FF0a; remaining gates need their own task.

## Continuation after the next milestone

FF0b freezes numeric/wire/checkpoint vectors, FF1a builds journal/valuation primitives, FF1b adds dated fee/series history, then FF2a execution and FF2b risk. FF2c owns the integrated pure session/payment/payroll/independent Case1 control path; FF3a owns real human command authority. Both precede FF3b's internal human experiment. Persistence/general investors follow FF4; first playable certification is FF5c; full initial-game certification is FF6c. FF7 historical/advisory and FF8 extension selection remain elective. All 20 are currently pending; completed documentation is not their acceptance evidence.

At each gate produce `docs/evidence/<milestone>/RESULTS.md` with exact executed commands, expected/observed results, input/rule/tape/control hashes, failures/limitations and one next task. Do not auto-run the whole roadmap because it is documented. Full ordered tasks, module ownership, decision deadlines and proposed commands are in MILESTONE_PLANS.

## Environment and checks

Observed Python3.14.3; python/node/npm on PATH. `psql`/`soffice` not found by Get-Command (not proof none installed elsewhere). Active Python lacks python-docx. Bare old validator failed cp1252 decoding; UTF-8 retry failed eager docx import. Tooling now uses explicit UTF-8 and original standard-library Word fallback; PACKAGING_VALIDATION records final actual commands/results. No installed dependencies, database/application/race/playtests, provider or deployment work. Word archive/XML/content can be checked; page rendering unavailable.

Actual documentation commands: `python scripts/build_documents.py`, `python scripts/validate_design.py`. State commands: `git status --short`, `git log -5 --oneline`, `rg --files`. Future `python scripts/validate_scenarios.py fixtures/compiled/case1.v2_2.json` and `python -m unittest discover -s tests/contracts` are proposed interfaces until files exist, not working commands. Packaging counts are not26 application passes.

## Decisions and unresolved assumptions

Accept issuer fix, settled replacement timing, retained collateral, narrow winddown, operating commands, removal of dominated hire, extended gate horizon, exact precision/retry, early human experiment. All reviewer dispositions are in DESIGN_REVIEW_V2_2. Reject artificial hire payoff, extra dependencies/guaranteed alpha. Preserve old research snapshots; fresh source scope is in SOURCES. Full opening campaign tape, full-path oracle totals, release/DB/auth choices, balance/enjoyment remain unverified. v2.2 overlays old isolated fixtures; never use checkpoint values as complete dated-run outputs.

Claude continuation: Read this handoff and verify the current repository state before editing. Critically review the revised plan using bounded financial, gameplay, and engineering reviewers. Resolve concrete contradictions and improve weak acceptance criteria before implementation. Then implement only the next agreed milestone, validate it against the documented acceptance cases, and update this handoff with evidence and the next task.
