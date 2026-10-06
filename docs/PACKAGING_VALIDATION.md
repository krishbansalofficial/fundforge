# Design-package validation — v2.0

These checks concern the documentation, reference arithmetic and generated review bundle. They are not application acceptance tests or evidence of playable software.

Validation commands for this revision:

```bash
python scripts/build_documents.py
python scripts/validate_design.py
```

Result: PASS for the commands above. Nineteen source Markdown files, sixteen bundled sections and nineteen Word tables were checked. No application result is implied.

The validator checks Markdown fences and repository-relative link targets, JSON syntax, all six legacy cash-account NAV states, independent opening-capital/fee/high-water-mark/stress-margin/gate/compounded-return arithmetic, Word archive/XML structure, and inclusion of every canonical source section in the generated Markdown bundle. The Word and Markdown outputs are produced by the same ordered source list.

Manual consistency review covers the sixty-day/six-chapter configuration, twenty-day opening slice, independent firm cash, series high-water marks, restricted collateral, dealing-versus-payment timing, deterministic forced actions, missing-partner pause, source provenance and the separation between planned features and implemented software.

The legacy repository-creation scripts were preserved and not executed during this redesign. Previous mock-script results are in Git history; they are not newly run results. The current remote was inspected as private, with write access. Publication uses one guarded non-force Git ref update after packaging.

Limitations: no Word application/page-render inspection; no runtime engine or full executable market tape; no application unit/integration, PostgreSQL race, security, gameplay, balance, provider, load or ML checks. All implementation gates remain pending. The authored season manifest records intended behavior, not measured outcomes.
