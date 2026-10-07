# Decision log — v2.1

These are proposed product/engineering decisions, not claims of implemented behavior. Approved scope: whole-plan redesign and file update, 6 October 2026. Astra/extra-high led this critical realism revision;17 repositories were checked against actual source/license snapshots.

| Decision | Current choice | Why / consequence |
|---|---|---|
| Product | Cooperative investment-business strategy game | Portfolio performance, investor obligations, financing and firm survival interact |
| Time | 60 business days, six chapters, pause/resume | No real-market attendance; preserve day-level financial effects |
| Initial scale | $25m outside capital; $300k separate firm cash | LP and business choices become meaningful; managers are not the only investors |
| Core strategy | Long/short equities and broad ETFs | A bounded but recognizably hedge-fund-like strategy |
| Governance | Joint sleeve charters; independent consent for exceptions | Preserves two-person control without approving every routine click |
| Core release | Fees, flows, borrow/margin, runway, crisis and debrief | Optionalizing these produced a shallow trading app |
| Scope sequencing | Complete two-chapter opening arc before six-chapter campaign | Validate fun before multiplying content |
| Financial authority | Pure domain + PostgreSQL transactions + immutable journal | Reconciliation, reproducibility and concurrency correctness |
| Rules authority | Versioned scenario/contract configuration | House rules are explicit; no hidden market manipulation |
| Data | Synthetic authored fixtures first | Deterministic, no fees/credentials, avoids memorized historical outcomes |
| OpenSEO | Assess every-app/open-seo at pinned snapshot; optional research adapter | User supplied repo name only; no unsupported assumption it is a market engine |
| Upstream reuse | Adapt bounded patterns; no wholesale fork/code copied yet | Keep finance ownership and avoid unrelated SaaS dependencies |
| AI | Optional explanations/baselines after game | No LLM control over financial truth, approvals or scoring |
| Workflow | One builder, bounded review | Astra/extra-high was explicitly requested for this redesign, not perpetual delegation |

## v2.2 accepted decisions,7 October2026

Planning revision 2.2-M1: accepted all 20 detailed work packages through FF8, explicit pure integration/independent Case1 controls before human experiment, winddown-tail authoring gates, generalized6a controls/restrictions, end-to-end7a historical replay and a bounded8 extension-selection gate. PLAN_REVIEW_AND_DECISIONS is the current due-decision register; no new dependency or application feature implemented. Standard-library validation selected forFF0a. Prior planning diff preserved; commit/push explicitly authorized by the latest user instruction.

DESIGN_REVIEW_V2_2 records every independent financial/gameplay/engineering finding and rationale. Retain the connected economics and modular monolith. Correct Case2 issuer basket; extend gated payment horizon61; fix replacement cutoff/transfer, retained pending-return collateral and voluntary-before-forced margin ordering. Remove active dominated Case3 hire; retain its arithmetic as teaching forecast. Add useful operating commands, exact precision/hash/retry/readiness, bounded termination, early human prototype and small milestone gates. Next is FF0a authoring/schema-loader only, not full app scaffold. SEO/marketing excluded; old row/assessment below is historical evidence, not active authorization. Release/balance/fun remain unproven.

## Superseded defaults

Original 30-day/$100k equal-manager-capital season, strict long-only release, universal per-ticket partner approval, and postponement of fees/redemptions/shorts to an optional final milestone are replaced. The old arithmetic fixture remains a deliberately small primitive reference; it is not a campaign configuration. Full original docs remain recoverable from Git history before this revision. Current generated Word/Markdown bundles must be regenerated together.

## Still open before implementation

Runtime/dependency pins, auth SDK, database migration tooling, concrete API/schema validation, complete authored price tape, calibrated score/LP/broker parameters, playtest results, exact historical data rights, provider entitlements, hosting/budget and ML target. Resolve at the corresponding gate, not by inventing availability. Fund/accounting rule conflicts must be settled before code.

Log future changes with date, rationale, affected rule/data versions and acceptance cases. Do not change a live season's rule version in place.

## v2.1 corrections and tradeoffs

| Decision | Contract now | Reason / affected checks |
|---|---|---|
| Fee cohort participation | Opening net plus reversible performance provision | Avoid unspecified redistribution between fee-accruing cohorts; V01 |
| Calendar and day count | Jan5–Mar27 synthetic Mon–Fri; calendar-date fees; management ACT/365, borrow/debit ACT/360 |252 is not a universal accrual year; V03–V05 |
| Incentive timing | Annual Dec31 plus pro-rata dealt redemptions; survivor HWM unchanged | Separate fund provision, fixed manager receivable and cash; V02/V08 |
| Endpoint | Ordinary day21/day61 opening admin, after intervening weekend accruals | Preserve obligations without artificial frozen-market carry; V09 |
| Reductions | Validate whole risk vector and feasible sequential fills | Covers can raise net; redemptions shrink denominator; V06/V07 |
| Controls | Independent simulated broker/admin records and certified NAV | Balanced internal journal can still be wrong; V12 |
| Corporate actions | Cash distributions and integer splits; reject unsupported imports | Enough lifecycle depth without full tax/claims machinery; V10/V11 |
| Dependency ownership | Original deterministic kernel, no trading framework in FF5/FF6 | Avoid duplicate clocks/ledgers; library review records alternatives |
| Research stack | Staged pandas/calendars, optional DuckDB, then justified CVXPY/statsmodels | One tool for each demonstrated need; no mass installation |
| Role experience | Automate routine work, expose exception decisions and causal recovery | Meaningful operations role requires tradeoffs, not signoff volume |

The changed contracts supersede corresponding v2.0 descriptions, not Git history. Industry examples motivate mechanics; broker coefficients, LP windows, expenses and trust rules are fictional contracts. Remaining uncertainty includes scenario difficulty, player comprehension, provider rights and release compatibility; none is established by this documentation review.
