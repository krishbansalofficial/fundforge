# Design-package validation v2.2

7 October2026. These are documentation/reference checks, not application tests, scenario execution or playtest evidence.

## Actual environment and commands

Observed Python3.14.3 on Windows; original bare `python scripts/validate_design.py` failed cp1252 decoding. `python -X utf8 scripts/validate_design.py` exposed missing python-docx through the old eager builder import. Those failures are recorded, not treated as passes. No dependency installed. Documentation scripts now read/write explicit UTF-8, optional docx import no longer blocks reference validation, and original standard-library OOXML fallback permits Word generation.

Executed successfully after correction:

```powershell
python scripts/build_documents.py
python scripts/validate_design.py
git diff --check
```

The previous v2.2 pass passed2,511 package checks across21 sections. Planning revision2.2-M1 adds all20-milestone coverage/required work-package fields and an acyclic dependency check, plus detailed plans/decision register in23 bundled sections. Its prepublication build passed3,055 checks. Final publication-evidence build passed3,056 checks across27 source Markdown files,23 bundled sections and43 Word tables/2,544 paragraphs. Counts are package assertions, not application tests. Word is structurally valid ZIP/XML with repeated table headers, heading styles, external link relationships and source hashes/visible-text comparison. No Word/LibreOffice page render was available; table widths, pagination, readability and application compatibility are unverified. The fallback preserves content, with simpler typography/list treatment than python-docx.

Checks: local Markdown links/fences; fixture JSON; dated synthetic calendar/capital; six isolated legacy NAV states;9 financial arithmetic oracles; three isolated episode checkpoints;17 pinned repository/source/license records; exact combined source inclusion; Word archive/XML/source-hash and visible-paragraph content. Added independent corrected Case2 issuer/sector/ETF/initial-margin/normalized-cash checks, exclusion of dominated hire, extended gate horizon and scale24 residual/tie arithmetic. These do not execute actual dated scenario paths. v2.2 rules complement v2.1 isolated fixture checkpoints; their complete accrued path oracles/compiler remain FF0a/FF6 work.

## Checks only proposed / limitations

No simulation, Next.js/FastAPI/Pydantic application, database, application test suite, financial reducer or complete compiled executable tape exists. No real PostgreSQL races, restore/fault/security/load tests, provider/model tests, two-human playtests or balance experiments ran. No library installed, benchmarked or compatibility-tested. The17 previous pinned records were preserved; only bounded primary-source/DTO-framework verification occurred this session.

Original entry HEAD51eda0c was clean; full-milestone continuation entered the preserved planning diff. Under the user's explicit request, commit `a404948` and `git push origin main` succeeded; PROGRESS records exact publication evidence. This follow-up documentation commit records that result; its current hash is discoverable in Git history. No deployment, paid request, installation, application feature, repository-creation script or visibility change. Word/Markdown regenerated from source docs, excluding standalone SEO/marketing integration sections; old research provenance remains labeled archived. Financial practices, fictional contracts and house simplifications remain distinct. Read PLAN_REVIEW_AND_DECISIONS and IMPLEMENTATION_HANDOFF for remaining uncertainties and exact next task.
