# Engineering notes

How FundForge keeps simulated money correct. Each claim links to the code and the test that backs it.

## 1. A ledger that cannot lie quietly

- **Journal.** `backend/src/fundforge/journal.py` stores immutable entries. Each entry balances on its own and belongs to exactly one entity, fund or firm. Amounts are whole-cent `Decimal`s, and floats are rejected at the boundary (`money.D`).
- **Two representations.** The engine keeps economic state (positions, loans, series claims) separately from the journal. `Engine.reconcile()` asserts after every event that they agree:
  - long securities and short liability equal position × mark;
  - each series' capital and provision accounts equal its state;
  - NAV equals the sum of series net capital;
  - cash is never negative and debt is within the credit limit.

  A balanced but wrong posting therefore fails loudly.
- **Accruals.** `Accrual` carries the sub-cent remainder of each obligation. Daily fees post in cents without drift (FUND_ACCOUNTING §6 oracle 6 is in `tests/test_journal.py`).
- **Tests:** `tests/test_journal.py` (Hypothesis checks zero trial balance and idempotent replay), `tests/test_series.py` (oracles 1–5 and 7), `tests/test_engine.py`.

## 2. Fund money and firm money stay apart

The management company has its own journal. The only path from fund cash to firm cash is a fee payment, posted as a fund entry and a firm entry together with `post_many`. Payroll is paid only from firm cash, and an unpaid bill is recorded as an incident. It is never funded from the fund. Test: `test_fund_cash_never_pays_firm_payroll`.

## 3. Two partners, bound approvals, safe retries

- **Authority.** `governance.py` gives the portfolio manager independent tickets up to 5% of NAV each and 15% turnover in total. Anything larger is a package. Its sha256 digest binds the policy version, contents and expiry. It is authorized only when the *other* partner signs that exact digest. A wrong digest, a self-signature, or an expired package is rejected.
- **Persistence.** `store.py` treats Postgres as the authority. Each room keeps an append-only command log, guarded by a trigger, plus the journal entries each command produced. A command runs in one transaction:
  1. lock the room row;
  2. check `unique(room_id, idem_key)`;
  3. replay and apply the command;
  4. append the command and its journal entries;
  5. bump the version.
- **Race tests** (`tests/test_store.py`) run against real Postgres with separate connections:
  - four concurrent signatures authorize exactly once;
  - five concurrent retries of one key create one order;
  - simultaneous "ready" from both partners advances time exactly once.

## 4. No future information

The tape stays server-side. A player view is built only from events that have already been processed. Orders accepted at a decision barrier execute at the *next* execution event, never at a mark that has already been published. Test: `test_view_never_contains_future_information`.

## Deliberate simplifications

These are listed in [PROGRESS](PROGRESS.md#known-limitations-deliberate-recorded-in-code) and marked in code where relevant. They are scope cuts from [REPLAN_V3](REPLAN_V3.md), not hidden behavior.
