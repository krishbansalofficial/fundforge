# Design-package validation — v2.1

These checks concern documents, reference arithmetic and generated review files. They are not application acceptance tests or evidence of playable software.

Executed successfully:

```bash
python scripts/build_documents.py
python scripts/validate_design.py
```

The bundle contains 19 canonical source sections; 22 source Markdown files are checked. The validator reports the current check/table/paragraph counts directly. Both commands passed for this revision; subsequent canonical edits require regeneration and validation before commit.

Checks include Markdown fences and local links; JSON syntax and version/capital/calendar contracts; six legacy zero-cost cash-account NAV states; 9 separate arithmetic oracles covering fee participation, partial redemption/HWM, post-redemption leverage, cover direction, calendar accrual, short distributions, borrow dates and the terminal boundary; numerical checkpoint calculations across 3 authored cases;17 exact repository/license/source snapshot records; Word archive/XML integrity and source-section inclusion; and exact source-content inclusion in the generated Markdown bundle.

The arithmetic validator independently recomputes expected checkpoint values from fixture inputs. It does not run an application or treat expected-output JSON as gameplay evidence. Episode branches isolate their stated decisive calculations; ordinary date-by-date accrual and complete market tapes must still be compiled and tested by the future engine.

Manual consistency review covers fund/company separation, pre-provision series participation, survivor HWM, annual performance crystallization, weekend accrual, settled borrow/return, whole-vector risk checks, post-flow leverage, independent reconciliation, real data rights versus source licenses, and proposed versus implemented status. Source audit, library review and architecture are now included in the combined Word document. Table headers repeat across pages.

Existing repository-creation scripts were preserved and not executed. The remote was inspected through the GitHub connection. Publication uses an atomic commit and guarded non-force ref update against the expected existing HEAD; no visibility or hosting change is part of this task.

Limitations: no Word application/page-render inspection; no simulation runtime or complete executable market tape; no application unit/integration, PostgreSQL race, security, two-user gameplay, balance, provider, load or ML tests. Library reviews were source/license/API inspections, not installation/compatibility/benchmark/security tests. Financial sources illustrate practices within their stated scope; contract parameters and synthetic calendar remain authored game choices.
