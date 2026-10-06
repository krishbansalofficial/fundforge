# Current project state

Updated 6 October 2026. Design v2.0. Application implementation remains not started.

- Private remote: https://github.com/krishbansalofficial/fundforge; privacy and write access inspected for this task.
- Starting commit for redesign: `797e90d87c1304ed422af6f09c961a87b75ee8ca`.
- Owner requested complete game redesign, OpenSEO repository assessment, file updates and Astra/high reasoning. Astra/high was used for core game/accounting/scenario design.
- Current concept: two partners run a $25m outside-capital fund plus a separate $300k management company over 60 simulated business days/six chapters. Core systems include investment research, delegated governance, long/short financing, LP flows, fees/HWM, firm costs, crises, endings and causal debriefs.
- Replaced old master, plan, prompts, handoff, decisions, acceptance cases, reviewer/workflow and evidence guidance; added game, accounting, scenario and OpenSEO documents plus authored scenario contract. Regenerated combined Markdown and Word document.
- OpenSEO upstream/source inspected at `ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6`. No code copied, provider connected, paid usage enabled or integration built.
- Executed `python scripts/build_documents.py` and `python scripts/validate_design.py`: packaging/reference checks passed (19 source Markdown files; 16 bundled sections; 19 Word tables). Details are in PACKAGING_VALIDATION. Those are document/reference checks, not passing application acceptance tests.
- FF0–FF8 remain pending. No auth/database credentials, runnable scenario engine, deployed model, production application or measured user/load/return outcome exists.

## Next task

Run P01: inspect actual implementation environment and freeze FF0 contracts against MASTER_SPEC, GAME_SYSTEMS, FUND_ACCOUNTING and SEASON_SCENARIOS. Resolve any remaining accounting/event/authority conflict before implementation. The scenario manifest is an authored design fixture, not a complete runnable market tape. Build foundations then the complete FF5 opening arc; do not ship a trading-only demo as the finished game.

## Update discipline

Keep actual branch/commit, changed paths, executed commands/results, unresolved risks and one next task. Determine the redesign commit from Git history rather than copying the starting commit as current HEAD. No invented completion or metrics.
