# Current project state

Updated 7 October 2026. The active plan is [REPLAN_V3](REPLAN_V3.md), a seven-week Case1 vertical slice. Design contracts v2.2 (FUND_ACCOUNTING, SCENARIO_CONTRACTS) remain the accounting authority.

## Done (committed on main)

| Milestone | Commit | What exists |
|---|---|---|
| Re-plan | `53bb24f` | Advocate and challenger review recorded in REPLAN_V3. The 20-milestone sequence is superseded, and FF6–FF8 are now stretch |
| M0 | `1013dc5` | `backend/src/fundforge/money.py` (Decimal, HALF_EVEN, residual `Accrual`) and `journal.py` (immutable, balanced, per-entity, idempotent entry IDs, sha256 digest). CI workflow |
| M1 | `d71fd1f` | `series.py`: participation add-back, HWM provision, cohort allocation, partial-redemption crystallization. `risk.py`: exposures and margin |
| M2 | `77f5289`, `d3e4147`, `f03001f` | `fixtures/case1.json` plus `tape.py`: materialized day 12–21 tape, authoring-fault rejection and tape digest. `execution.py`: quadratic impact and a shared participation cap. `engine.py`: dated phases, T+1 settlement, collateral, recall/replacement, margin call and forced liquidation, ACT/360 and ACT/365 accruals, invoicing, dealing and payment, and firm payroll. State is reconciled against the journal after every event |
| M3 | `99a5a6e` | `governance.py`: two distinct partners; PM tickets capped at 5% of NAV and 15% turnover; digest-bound joint packages with no self-approval; MP-only borrow and reserve; time advances only when both are ready; as-of player view |
| M4 | `ea868b6` | `store.py` plus `api.py`: Postgres append-only command log and journal (enforced by trigger), room-row lock per command, idempotency keys, replay-rebuilt state, hashed seat tokens. `compose.yaml`, backend Dockerfile, and CI with a Postgres service |

## Evidence actually observed (local, Windows, Python 3.14.3, Postgres 17 in Docker)

- `cd backend && DATABASE_URL=... uv run pytest -q` passed 44 tests (45 collected, 1 warning) at `ea868b6`. These include the FUND_ACCOUNTING §6 oracles 1–7, the Case1 fill prices from the contract, and four separate-connection race tests, which were run three times.
- Case1 scripted outcomes:
  - S1 (early cover plus BEAM sale): WIN.
  - S2 (replacement borrow plus cure): WIN.
  - F1 (inaction): SURVIVAL through a forced buy-in. It stays solvent with about $13k of maintenance headroom.
  - F2 (keep the full BRIN short, no cure): forced margin liquidation.
- `docker compose up api`: `/api/health` and room creation answered over HTTP.
- GitHub Actions CI has not yet been observed passing remotely. Nothing has been pushed in this session.

## In progress (uncommitted at the time of writing)

- **Fixes from the bounded finance review**, applied in `engine.py` and `governance.py` with regression tests in `test_engine.py`:
  1. The replacement transfer is capped at the open recall, and the most expensive loan is returned first.
  2. A cover or buy settlement that hits a cash shortfall is recorded as a failed settlement and stays pending, so cash never goes negative.
  3. Collateral is netted per symbol, so frozen cash is never released on trade date.
  4. The default treasury buffer is 2% of NAV plus known payables.
  5. Closed series are skipped during accrual.

  Test status for these fixes: **pending re-run**.
- `frontend/`: a Next.js 15.5.4 scaffold has been created but not installed or built. Design plan: a blue-grey "prime-broker statement" palette, IBM Plex Sans Condensed with tabular figures, and a deadline ribbon as the single bold element.

## Known limitations (deliberate, recorded in code)

- No FIFO lots or realized/unrealized split.
- No gates or escrow.
- No cash budgets on market orders.
- Limit-price search uses coarse quantity steps.
- Forced margin liquidation uses a largest-value-first heuristic.
- The replay cache is per process.
- Seat tokens are bearer links, not production auth.
- Mandate limits other than margin and the ticket caps are not enforced.
- No human playtest has run.
- No balance, load or security study has been done.

## One next task

Re-run the backend suite on the review fixes and commit them. Then build M5: a Next.js desk that polls `/api/rooms/{id}/view`, with the ticket/package/sign flow, MP borrow and reserve controls, ready state, ledger and debrief.
