# Independent LP and fee controls

Implemented 11 October 2026 under rules `case1-rules-2026.10.8`. Fixture remains 4.2.0. These extend the [broker controls](BROKER_CONTROLS.md); `checked` still means scoped reconciliation, not external NAV certification.

## What players see

Open **T → RISK** in a newly created room. The LP / FEE CHECK shows independent units, net capital, reversible performance provisions and high-water marks for every series. Values reflect the last processed calendar close, adjusted for dealt flows; intraday P&L is allocated at close. After redemption dealing, the panel shows its date, units, calculated NAV per unit, payable and crystallized performance fee. No future redemption estimate is presented as a dealt claim.

Existing mismatches block new BUY/SHORT risk and redemption dealing through the combined controls. Reductions and scheduled payments retain the broker-control behavior. A mismatch in a newly calculated redemption candidate raises an explicit `administrator_claim` integrity error before units, administrator claims or financial journals mutate. Session/Store retain their rollback guarantees. Players cannot dismiss these arithmetic errors with statement review or a balancing plug.

## Calculation boundary

`backend/src/fundforge/administrator.py` imports only stdlib. It has its own Decimal context, largest-remainder cent allocation, management-fee residuals, performance-provision arithmetic and redemption calculation. It does not call production `series.py`, journal posting helpers or the shared allocation/accrual functions.

Each dated close starts from a reconstructed fund value:

```text
confirmed holdings at observed marks
+ broker cash + restricted collateral - broker debit
+ unsettled sale proceeds - unsettled purchase/cover amounts
- independently computed accrued and invoiced financing
- independently tracked management/performance/redemption liabilities
```

The difference from prior independent participation capital is common P&L. Neither the journal's `common_pnl` balance nor production LP capital is used to calculate it. Common P&L is allocated by opening net capital plus reversible provision, with stable cent residuals. Each series accrues 1.5% ACT/365 on that opening participation, carrying its own fractional cents. The provision is 20% of positive capital above units × HWM, and reverses when that excess falls. Every calendar date, including weekends, produces frozen close evidence.

Invoicing moves the independently tracked fee liability. Payments reduce the corresponding claim rather than creating another expense. The administrator compares fund claims to management-company receivable and cumulative fee revenue, detecting unearned firm income even when that entity balances internally.

Before redemption, a separate preview calculates net NAV per unit, rounded payable, proportional crystallized provision, surviving units/capital/provision and unchanged surviving HWM. All are compared to the production candidate before it is applied. Partial redemption fixes only the exiting fraction's fee; a later loss reverses only the surviving provision. Fully closed series identities remain retained. Frozen claim records and close evidence rebuild deterministically from the pinned tape and command log.

Comparisons cover current series state, capital/provision journal balances, each fee/claim liability, firm receivable/revenue and posted management fees by calendar date and series. They use exact posted cents. The terminal report is a detached read and creates no journal entries.

## Limits and next task

The observations are synthetic. Market marks, execution confirmations, pending settlement instructions and actual payment confirmations remain shared upstream inputs. The pending settlement collection is not yet an independently reconstructed delivery ledger. Management-company payroll/cash is outside this calculation. January Case1 does not exercise subscriptions, annual crystallization, gates or multiple dealing windows; the new module does not implement those future campaign contracts. These limits prevent a claim of full external administrator certification.

Next bounded task: reconstruct settlement obligations from immutable execution identities and reconcile deliveries, partial failures and receipts against separate broker confirmations. Detect missing/duplicate or misallocated obligations even when the live pending collection and journal agree. Preserve as-of evidence and existing reduction/payment behavior.

## Verification

`test_administrator.py` covers all four canonical paths; unequal-cohort participation; exact independently worked fees, provisions and partial redemption; recurring weekend bases/residuals; payment neutrality; provision reversal versus fixed fees; closed identities; immutable evidence; doubled but balanced management charges; unearned firm receivables; incorrect payable/fee/units/HWM candidates before mutation; date shifts with unchanged balances; and low caller precision. The database debrief test compares reconstructed administrator closes, claims and report after cache eviction. Godot checks render the new series/claim panel.

Full checks and actual HTTP evidence are recorded in [PROGRESS](PROGRESS.md). Reproduction uses the existing backend pytest/Ruff/mypy commands, Godot headless checks and `python scripts/analysis_smoke.py --broker-challenge`. The smoke also requires 13 independent calendar closes and one checked redemption. Existing canonical journal digests and NAVs remain unchanged; only the rules tag advances.
