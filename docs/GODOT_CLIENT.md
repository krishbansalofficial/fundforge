# Godot desktop client notes (lane L4)

Scope: `game/**` only. Pure rules live in `game/scripts/*_rules.gd` and are tested headless by `game/tests/run_tests.gd`.

## Campaign entry

`WorldRules.SCENARIOS` lists `campaign-v1` (the server key in `backend/src/fundforge/store.py`) next to the four Case 1 options. The menu passes the key unchanged to `POST /api/rooms`.

The ending card's market line is scenario-aware: `CardRules.market_text(variant, scenario)` keeps the Case 1 day 16 wording for `case1*` scenarios, and for any other scenario reports the revealed variant name rather than Case 1's story.

## Stale connection status

`Api.poll_state()` reports `stale` and the age since the last successful server contact. The HUD shows "Connection interrupted / data stale" with the age, while NAV and the clock keep the last data. A successful poll clears it. Behaviour is covered by the headless tests in `run_tests.gd`.

## Ending card

`Hud.save_card(path)` renders `CardRules.rows` (ending label, result, return vs passive book, final NAV, drawdown, seed and its SHA-256 check, rules version, chain head, journal digest) into a 1200x630 SubViewport and saves a PNG under `user://`. The client only formats server fields; it computes no money, score or rank.

## Music

`game/scripts/music.gd` synthesizes one deterministic 16-second loop in code, with the same approach as `sfx.gd`. There are no audio files, so no licence entry is needed. It is an original composition: a four-chord loop with a plucked bass, a pad and a fixed-seed arpeggio.

- The global mute from `sfx.gd` silences music too.
- A separate music level (off, low, on) is cycled by the HUD button or the `N` key, and saved as `audio.music_level` in `user://settings.cfg`.
- Synthesis happens on first audible use and takes about 200 ms on this machine.

## Checks

Headless suite: 280 `ok` checks, 0 failures. Editor import and `--quit-after 5` boot both pass.

## Limitations

- No human playtest, listening test or graphical review was done. Headless audio uses a dummy driver.
- Music is cosmetic only and drives no game state.
- Campaign balance and the campaign's ending paths are backend concerns and were not verified from the client.
