# Current project state

Updated 8 October 2026. Active plan: [ROADMAP](ROADMAP.md) (v4). Graphical layer: [WORLD_GAME_PLAN](WORLD_GAME_PLAN.md) as amended in the roadmap.

## What exists and runs

| Area | State | Evidence |
|---|---|---|
| Engine (`backend/src/fundforge`) | Decimal per-entity journal, LP series and HWM, impact execution, dated Case1 session (recall, margin, settlement, dealing, firm payroll) | Oracle, property, scenario and golden-digest tests |
| Rules | Versioned compliance mandate on tickets, signatures and every fill; hidden market variants (sell-off or rally); benchmark-relative score and league rank | `test_balance.py`: flatten refused, no dominant policy |
| Market | Five rule-based rival funds whose flow moves prices. Permanent impact with resilience produces an emergent short squeeze, deleveraging, blow-ups and a crowding report | `test_market.py` |
| Governance | Two roles, digest-bound packages, all-or-nothing commands, version-bound ready, chat | Stateful Hypothesis test of random command sequences |
| Solo play | Deterministic bot partner (`bot:v1`, not an LLM) using the same commands and checks; owner decision 8 Oct 2026 | `test_bot.py`; bot rows chained and verified in Postgres |
| Time | Real-time clock (pause, 1x, 2x, 4x) with auto-pause; ticks are logged, version-bound commands | Clock tests; two schedulers racing produce one tick |
| Persistence | PostgreSQL command log with numbered migrations, pinned rules/tape/variant per room, hash chain, SQL-checked balanced `journal_lines`, TRUNCATE refused; `verify(room)` re-derives everything | Separate-connection race and tamper-detection tests |
| Game client (`game/`) | Godot 4.7 desktop simulation. The 3D office and city use Kenney CC0 models, animated characters, lighting tied to the in-world hour, rival towers, a Street league table, solo/duo menu and HUD terminals per location | Headless Godot tests and boot check in CI; screenshots verified locally |
| Web desk (`frontend/`) | Earlier Next.js two-seat desk, kept as a secondary client | `npm run build`, audit clean |

Most recent full backend run, with Postgres: 81 passed (`886b7e2`). Game: 35 headless checks passed (`8b1f88a`). GitHub Actions has not run yet because nothing has been pushed.

## Known limitations

- Case1 is the only scenario. The 30-day v1 campaign, research cards and LP agents are P4 work in the roadmap.
- The partner avatar walks to the place of its last decision; live WebSocket presence is not built.
- Squeeze strength is limited by day-16 BRIN volume (25k shares); tuning notes are in the backend commit.
- No deployment, recorded playtest or exported game builds yet.
- A realistic-graphics pass (PBR textures, HDRI lighting, SDFGI, more realistic humans) is in progress.

## Next task

Finish the realism pass, then P2: deploy plus exported builds, an end-to-end two-client run that records the trailer, and docs consolidation.
