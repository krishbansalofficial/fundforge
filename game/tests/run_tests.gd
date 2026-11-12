extends SceneTree
## Headless unit tests for the pure world rules:
##   godot --headless --path game --script res://tests/run_tests.gd

var failures := 0

class PollTransport extends "res://scripts/api.gd":
	signal reply(id: int, response: Dictionary)
	var requests: Array[Dictionary] = []
	func request(method: int, path: String, body: Variant = null, key := "", if_none_match := "") -> Dictionary:
		var id := requests.size()
		requests.append({"method": method, "path": path, "body": body, "key": key, "etag": if_none_match})
		while true:
			var result: Array = await reply
			if result[0] == id:
				return result[1]
		return {}

class RunRecordTransport extends Node:
	signal respond
	var response: Dictionary = {}
	var calls := 0
	var options: Dictionary = {}
	func debrief(request: Dictionary) -> Dictionary:
		calls += 1
		options = request
		await respond
		return response

class TerminalTransport extends Node:
	var response: Dictionary = {}
	var last_command: Dictionary = {}
	func command(cmd: Dictionary) -> Dictionary:
		last_command = cmd
		return {"ok": false}
	func terminal() -> Dictionary:
		return response
	func liquidity(_assumptions: Dictionary) -> Dictionary:
		return response
	func debrief(_options: Dictionary) -> Dictionary:
		return response


func check(cond: bool, name: String) -> void:
	if cond:
		print("  ok   ", name)
	else:
		failures += 1
		printerr("  FAIL ", name)


func _initialize() -> void:
	check(InvestorRecordRules.lines(null).is_empty(), "optional investor record omitted")
	var lp_record := {"policy": "lp-test", "final": {"Patient": {"confidence": "72.123456789", "band": "stable"}},
		"carried_units": {"Patient": "9007199254740993.000001"}, "checkpoints": []}
	var lp_lines := InvestorRecordRules.lines(lp_record)
	check("Patient / final confidence 72.123456789 / stable" in lp_lines, "investor confidence preserves exact server decimals")
	check("Patient / carried redemption units: 9007199254740993.000001 (remain invested)" in lp_lines, "carried units never use float conversion")
	check("No relationship checkpoints were reached in this run." in lp_lines, "empty investor checkpoints explained")
	lp_record["checkpoints"] = [{"kind": "review", "day": "13", "lp": "Patient", "start": "75.0", "end": "72.123456789",
		"band": "withdrawal_risk", "drawdown": "-2.876543211", "response_lag": "-1.0", "contact": "1.0", "clamp": "0.0",
		"drawdown_pp": "1.23456789", "open_alerts": "0", "policy_version": "lp-test"},
		{"kind": "chapter_close", "day": "20", "lp": "Patient", "start": "72.123456789", "end": "73.1", "band": "stable",
		"performance": "0.1", "breaches": "-0.2", "report": "0.3", "meeting": "0.4", "gate": "-0.5", "herding": "-0.6",
		"overdue": "-0.7", "clamp": "0.0"}]
	lp_lines = InvestorRecordRules.lines(lp_record)
	check("Day 13 / Patient / Interim review / confidence 75.0 to 72.123456789 / withdrawal risk" in lp_lines, "interim checkpoint named clearly")
	check("Day 20 / Patient / Chapter close / confidence 72.123456789 to 73.1 / stable" in lp_lines, "chapter checkpoint named clearly")
	check("Confidence drivers / Drawdown: -2.876543211; Response lag: -1.0; Contact: 1.0; Clamp: 0.0" in lp_lines, "interim drivers preserve signs and exact decimals")
	check("Confidence drivers / Performance: 0.1; Breaches: -0.2; Report: 0.3; Meeting: 0.4; Gate: -0.5; Herding: -0.6; Overdue: -0.7; Clamp: 0.0" in lp_lines, "all chapter drivers displayed")
	check(CertificationRules.summary({}) == "Latest dealing-close: Pending\nNo dealing-close certificate yet.\nNot a new check of current NAV.", "missing certificate remains pending")
	check(CertificationRules.summary({"certification": null}) == CertificationRules.summary({}), "null certificate remains pending")
	check(CertificationRules.summary({"certification": "certified"}) == "Latest dealing-close: Certified\nNot a new check of current NAV.", "HUD scopes certificate to latest dealing close")
	check("Latest dealing was withheld" in CertificationRules.summary({"certification": "broken"}), "broken certificate describes historical close and directs player to RISK")
	# iso projection round-trips
	for g in [Vector2(0, 0), Vector2(3.5, 7.25), Vector2(23, 1)]:
		check(WorldRules.to_grid(WorldRules.to_screen(g)).distance_to(g) < 0.001, "iso round trip %s" % g)

	# locations
	check(WorldRules.location_at(Vector2(5, 4)) == "trading", "trading floor hit test")
	check(WorldRules.location_at(Vector2(8.5, 19)) == "broker", "prime broker across the street")
	check(WorldRules.location_at(Vector2(10, 15.5)) == "", "street is not a room")
	for key in WorldRules.LOCATIONS:
		check(WorldRules.location_at(WorldRules.LOCATIONS[key]["spot"]) == key, "spot inside %s" % key)

	# ending card text: the market sentence follows the revealed variant, money keeps every Decimal digit
	check("sell-off and short squeeze" in CardRules.market_text("base"), "case1 base market text")
	check("sell-off and short squeeze" in CardRules.market_text(null), "missing variant reads as base")
	check("broad rally" in CardRules.market_text("rally"), "case1 rally market text")
	check("broad rally" in CardRules.market_text("rally", "case1-generated") and "sell-off" in CardRules.market_text("base", "case1"),
			"case1-family scenarios keep the day 16 text")
	var camp_text := CardRules.market_text("lean-company", "campaign-v1")
	check("campaign-v1" in camp_text and "lean-company" in camp_text and not "day 16" in camp_text, "campaign ending names its own variant")
	var gen_text := CardRules.market_text("seed:card-test")
	check("generated" in gen_text and "card-test" in gen_text and not "rally" in gen_text and not "squeeze" in gen_text,
			"generated market text reveals the seed, not a case1 variant")
	check(CardRules.seed_hash("seed:abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "seed SHA-256")
	check(CardRules.seed_hash("base") == "", "no seed hash for authored variants")
	check(CardRules.money("21806458.80") == "$21,806,458.80", "money keeps cents")
	check(CardRules.money("-1234567.005") == "-$1,234,567.005", "money keeps every digit, no float rounding")
	check(CardRules.money("0.1") == "$0.10" and CardRules.money("999") == "$999.00", "money pads cents")
	check(CardRules.money("90071992547409930.01") == "$90,071,992,547,409,930.01", "money beyond float precision")
	var outcome := {"label": "SURVIVAL", "nav": "21806458.80", "score": "-303.3", "fund_return_bps": "-913.6",
			"benchmark_return_bps": "-910.3", "rank": 6, "funds": 6, "forced": ["a", "b"], "variant": "seed:card-test",
			"journal_digest": "j" }
	check(CardRules.facts({}).is_empty(), "ending facts omit unavailable fields")
	var ending_facts := CardRules.facts({"scenario": "generated", "max_drawdown": "0.123456", "generated_days": 10, "stressed_days": 0, "seed_commitment": "abc"})
	check("Maximum drawdown: 12.3456% of NAV per unit, measured at business-day closes" in ending_facts, "ending drawdown preserves server precision")
	check("Generated market: 0 stressed days out of 10 generated days" in ending_facts and "Seed SHA-256: abc" in ending_facts, "ending generated facts include zero stressed days")
	check(CardRules.facts({"variant": "seed:abc", "seed_commitment": CardRules.seed_hash("seed:abc")}).size() == 1
			and CardRules.facts({"variant": "seed:abc", "seed_commitment": "f00"}).size() == 2, "outcome screen flags a seed commitment mismatch")
	var card_rows := CardRules.rows(outcome, {"pm": "Ana", "mp": "Ben"}, {}, {})
	var card_keys := card_rows.map(func(r): return r[0])
	check(not "Mean Brier" in card_keys and not "Chain head" in card_keys and not "Rules" in card_keys, "missing optional sources drop their rows")
	check(["Result", "#6 of 6 funds  /  Score -303.3 bps"] in card_rows, "rank and score row")
	check(["Final NAV", "$21,806,458.80"] in card_rows and ["Seed", "card-test"] in card_rows, "nav and revealed seed rows")
	card_rows = CardRules.rows({"label": "WIN", "nav": "1", "score": "12.5", "variant": "rally"}, {},
			{"seats": {"pm": {"theses": 2, "mean_brier": "0.25"}, "mp": {"theses": 0, "mean_brier": null}}},
			{"rules_version": "r1", "chain_head": "abc"})
	check(["Mean Brier", "PM 0.25 (2)"] in card_rows and ["Variant", "rally"] in card_rows, "brier and variant rows")
	check(["Chain head", "abc"] in card_rows and ["Rules", "r1"] in card_rows, "verify rows")
	check(["Result", "Score +12.5 bps"] in card_rows, "score row without a rank")
	# drawdown percent is string arithmetic on the server's Decimal: every digit kept, nothing rounded
	for pair in [["0.123456", "12.3456"], ["0.000000", "0.0000"], ["0.100000", "10.0000"], ["0.05", "5"],
			["0.004", "0.4"], ["1", "100"], ["0.5", "50"], ["0.999999", "99.9999"], ["0.0000005", "0.00005"]]:
		check(CardRules.percent(pair[0]) == pair[1], "percent %s -> %s" % pair)
	var abc := CardRules.seed_hash("seed:abc")
	card_rows = CardRules.rows({"label": "SURVIVAL", "nav": "1", "score": "0", "variant": "seed:abc", "max_drawdown": "0.087654",
			"scenario": "generated", "stressed_days": 0, "generated_days": 10, "seed_commitment": abc}, {}, {}, {})
	check(["Max drawdown", "8.7654% (NAV per unit, at closes)"] in card_rows and ["Scenario", "generated"] in card_rows,
			"drawdown and scenario rows")
	check(["Stressed days", "0 of 10 generated"] in card_rows and ["Seed SHA-256", abc] in card_rows, "stressed days and matching served seed commitment")
	card_rows = CardRules.rows({"label": "SURVIVAL", "nav": "1", "score": "0", "variant": "seed:abc", "seed_commitment": "f00"}, {}, {}, {})
	check(card_rows.any(func(r): return r[0] == "Seed SHA-256" and "does NOT match" in r[1] and "f00" in r[1] and abc in r[1]),
			"a served commitment that disagrees with the revealed seed is flagged")
	card_rows = CardRules.rows({"label": "SURVIVAL", "nav": "1", "score": "0", "variant": "base"}, {}, {}, {})
	card_keys = card_rows.map(func(r): return r[0])
	check(not "Max drawdown" in card_keys and not "Scenario" in card_keys and not "Stressed days" in card_keys and not "Seed SHA-256" in card_keys,
			"absent outcome facts drop their card rows")

	# clock interpolation is cosmetic and bounded by the server schedule
	var view := {"clock": {"day": 12, "phase": "PUBLIC_MARK", "next": {"day": 12, "phase": "EXEC_A"}},
			"realtime": {"running": true, "next_tick_in": 8.0, "window_seconds": 8.0}}
	check(is_equal_approx(WorldRules.clock_hour(view, 0.0), 9.5), "clock starts at the current phase")
	check(is_equal_approx(WorldRules.clock_hour(view, 4.0), 9.75), "clock halfway through the window")
	check(is_equal_approx(WorldRules.clock_hour(view, 99.0), 10.0), "clock never passes the next phase")
	view["realtime"]["running"] = false
	check(is_equal_approx(WorldRules.clock_hour(view, 4.0), 9.5), "paused clock stands still")
	check(WorldRules.format_hour(15.5) == "15:30", "format hour")

	# effects come from typed codes, once each
	var notices := [{"code": "redemption_notice"}, {"code": "recall"}, {"code": "market_shock"}]
	check(WorldRules.new_effects(notices, 1) == ["courier", "letter_committee", "screens_red", "panic", "shake"], "recall and shock effects")
	check(WorldRules.new_effects(notices, 3) == [], "no effects replayed for seen notices")
	check(WorldRules.new_effects([{"code": "market_rally"}], 0) == ["screens_green", "cheer"], "rally effects")

	# partner avatar goes where their last decision was made
	var v := {"decisions": [{"role": "mp", "type": "research"}, {"role": "pm", "type": "ticket"}, {"role": "mp", "type": "accept_replacement"}]}
	check(WorldRules.partner_location(v, "mp") == "broker", "partner location from last decision")
	check(WorldRules.partner_location({"decisions": []}, "pm") == "trading", "default partner location")
	check(WorldRules.partner_location({"decisions": [{"role": "mp", "type": "visit",
			"detail": {"location": "backoffice"}}]}, "mp") == "backoffice", "assignment location moves partner avatar")
	check(WorldRules.partner_location({"decisions": [{"role": "mp", "type": "visit",
			"detail": {"location": "invalid"}}]}, "mp") == "committee", "unknown assignment location is safe")

	check(WorldRules.money("-1234567.4") == "-$1,234,567", "money formatting")
	var hdrs := PackedStringArray(["content-type: application/json", "ETag: \"v7-1\""])
	check(WorldRules.header_value(hdrs, "etag") == "\"v7-1\"", "etag header read case-insensitively")
	check(WorldRules.header_value(hdrs, "x-missing") == "", "absent header is empty")

	# --goto routes for scripted runs
	check(WorldRules.parse_route("risk") == [["risk", 0.0]], "plain goto is an immediate route")
	check(WorldRules.parse_route("committee@15, research@1,vault@3,broker@x") == [["broker", 0.0], ["research", 1.0], ["committee", 15.0]],
			"route sorted by time, unknown places dropped, bad time means now")
	check(WorldRules.parse_route("").is_empty(), "empty route")

	# sound: synthesized cues, effect mapping and fill detection
	for cue in Sfx.CUES:
		var pcm := Sfx.synth(cue)
		var peak := 0
		for i in range(0, pcm.size(), 2):
			peak = maxi(peak, absi(pcm.decode_s16(i)))
		check(pcm.size() > 0 and pcm.size() % 2 == 0 and peak > 1000 and peak <= 32767, "cue %s is audible, 16-bit, not clipped" % cue)
		check(abs(pcm.decode_s16(0)) < 2000, "cue %s starts without a click" % cue)
	check(Sfx.synth("crash") == Sfx.synth("crash"), "synthesis is deterministic")
	check(Sfx.synth("nope").is_empty(), "unknown cue is silent")
	for effects in WorldRules.EFFECTS.values():
		for e in effects:
			check(Sfx.EFFECT_CUES.get(e, "") == "" or Sfx.CUES.has(Sfx.EFFECT_CUES[e]), "effect %s maps to a real cue" % e)
	check(Sfx.cues_for(["screens_red", "panic", "shake", "alarm", "courier", "letter_committee", "research_glow"])
			== ["crash", "alarm", "bell"], "one sound per cue, at most three per batch")
	var fv := {"orders": [{"fills": [{"qty": 5}, {"rejected": "no borrow"}]}, {"fills": [{"qty": 2}]}]}
	check(Sfx.fill_count(fv) == 2 and Sfx.fill_count({}) == 0, "fill count ignores rejected fills")

	# music: one synthesized deterministic loop, global mute wins, separate level toggle
	var t_music := Time.get_ticks_msec()
	var song := Music.synth()
	print("  music synth took %d ms" % (Time.get_ticks_msec() - t_music))
	var song_peak := 0
	for i in range(0, song.size(), 2):
		song_peak = maxi(song_peak, absi(song.decode_s16(i)))
	check(song.size() == int(round(Music.loop_seconds() * Music.RATE)) * 2, "music loop is whole chords at its tempo")
	check(song_peak > 3000 and song_peak < 32767, "music is audible and never clips")
	check(absi(song.decode_s16(0)) < 200 and absi(song.decode_s16(song.size() - 2)) < 200, "music loop seam starts and ends silent")
	check(song == Music.synth(), "music synthesis is deterministic")
	check([0, 1, 2].map(func(l): return Music.next_level(l)) == [1, 2, 0], "music toggle cycles off, low, on")
	check(Music.audible(false, 2) and Music.audible(false, 1) and not Music.audible(false, 0), "music level controls playback")
	check(not Music.audible(true, 2), "global mute silences music")

	# live presence (cosmetic): URLs, frames, throttling, backoff and the frame handler
	check(WorldRules.presence_url("http://127.0.0.1:8011/", "r1") == "ws://127.0.0.1:8011/api/rooms/r1/presence", "presence ws url")
	check(WorldRules.presence_url("https://ff.example", "r1") == "wss://ff.example/api/rooms/r1/presence", "presence wss url")
	check(WorldRules.move_frame(Vector3(5.123, 0, 4.256), "trading") == {"type": "move", "x": 5.12, "z": 4.26, "location": "trading"},
			"move frame rounds to centimetres")
	var edge := WorldRules.move_frame(Vector3(-3, 0, 99), "vault")
	check(edge["x"] == 0.0 and edge["z"] == float(WorldRules.WORLD.size.y) and edge["location"] == "", "move frame stays in the world")
	check(not WorldRules.should_send_move(Vector3.ZERO, Vector3(1, 0, 0), 0.05), "moves are rate limited")
	check(not WorldRules.should_send_move(Vector3.ZERO, Vector3(0.01, 0, 0), 1.0), "tiny steps are not sent")
	check(WorldRules.should_send_move(Vector3.ZERO, Vector3(1, 0, 0), 0.2), "a real step after the interval is sent")
	check([1, 2, 3, 4, 9].map(func(n): return WorldRules.reconnect_delay(n)) == [1.0, 2.0, 4.0, 8.0, 15.0], "reconnect backoff caps at 15 s")
	check([0, 1, 2, 3, 9].map(func(n): return WorldRules.presence_retry(n, false)) == [true, true, true, false, false]
			and WorldRules.presence_retry(9, true), "a server that never upgrades stops presence retries; drops always retry")
	var api: Node = load("res://scripts/api.gd").new()
	var seen: Array = []
	api.partner_moved.connect(func(r, pos, loc): seen.append([r, pos, loc]))
	api.partner_left.connect(func(r): seen.append(["left", r]))
	api.handle_presence({"type": "welcome", "role": "mp", "version": 0, "partners": {"pm": {"x": 2.5, "z": 3.0, "location": "risk"}}})
	api.handle_presence({"type": "presence", "role": "pm", "x": 6.0, "z": 7.5, "location": "trading"})
	api.handle_presence({"type": "left", "role": "pm"})
	api.handle_presence({"type": "error", "message": "ignored"})
	check(api.presence_live and seen == [["pm", Vector3(2.5, 0, 3.0), "risk"], ["pm", Vector3(6.0, 0, 7.5), "trading"], ["left", "pm"]],
			"welcome, presence and left frames reach the world")
	api.free()

	# journal paging with the /ledger `after` cursor
	check(WorldRules.ledger_path("r1", "fund", -1) == "/api/rooms/r1/ledger?entity=fund", "newest ledger page has no cursor")
	check(WorldRules.ledger_path("r1", "firm", 7) == "/api/rooms/r1/ledger?entity=firm&after=7", "ledger cursor in query")
	var e := func(n: int) -> Dictionary: return {"date": "d%d" % n, "memo": "m%d" % n, "postings": []}
	var first := WorldRules.merge_ledger({}, {"entries": [e.call(3), e.call(4)], "next": 5, "digest": "a"}, -1)
	check(first["start"] == 3 and first["next"] == 5 and first["entries"].size() == 2, "newest page starts the cache at its offset")
	var more := WorldRules.merge_ledger(first, {"entries": [e.call(5)], "next": 6, "digest": "b"}, 5)
	check(more["entries"].map(func(x): return x["memo"]) == ["m3", "m4", "m5"] and more["start"] == 3 and more["digest"] == "b",
			"page after the cursor is appended")
	check(WorldRules.merge_ledger(more, {"entries": [], "next": 6, "digest": "b"}, 6)["entries"].size() == 3, "empty delta keeps the cache")
	var gap := WorldRules.merge_ledger(first, {"entries": [e.call(9)], "next": 10, "digest": "c"}, 9)
	check(gap["entries"].size() == 1 and gap["start"] == 9, "a page that does not continue the cache replaces it")
	check(first["entries"].size() == 2, "merging never mutates the previous cache")
	var big: Array = []
	for i in WorldRules.LEDGER_CACHE:
		big.append(e.call(i))
	var capped := WorldRules.merge_ledger({"entries": big, "start": 0, "next": big.size()}, {"entries": [e.call(1000), e.call(1001)],
			"next": 1002}, big.size())
	check(capped["entries"].size() == WorldRules.LEDGER_CACHE and capped["start"] == 2 and capped["entries"][0]["memo"] == "m2",
			"cache is bounded, dropping the oldest entries")
	check(WorldRules.ledger_window(more, 0, 2).map(func(x): return x["memo"]) == ["m5", "m4"], "window is newest first")
	check(WorldRules.ledger_window(more, 2, 15).map(func(x): return x["memo"]) == ["m3"], "older page after an offset")
	check(WorldRules.ledger_window(more, 3, 15).is_empty() and WorldRules.ledger_window({}, 0, 5).is_empty(), "window past the cache is empty")
	check(WorldRules.headroom_ratio({"nav": "110", "maintenance_req": "100"}) > 1.09, "headroom ratio")

	# rival funds: league table and tower beacons
	check(WorldRules.location_at(Vector2(2.5, 14.5)) == "street", "street view terrace")
	var lv := {"league": [{"id": "halcyon", "status": "liquidating", "return_bps": "-2400.5"},
			{"id": "you", "status": "active", "return_bps": "310"}, {"id": "granite", "status": "active", "return_bps": "310"}]}
	var rows := WorldRules.league_rows(lv)
	check(rows.map(func(r): return r["id"]) == ["granite", "you", "halcyon"], "league ranked by return, ties by id")
	check(rows[1]["rank"] == 2 and rows[1]["is_you"] and rows[2]["return_bps"] == -2400, "league rank, you flag, bps")
	check(WorldRules.league_rows({}) == [] and WorldRules.league_rows({"league": null}) == [], "league absent is empty")
	check(WorldRules.beacon_color("active", 0.0) == WorldRules.beacon_color("active", 1.3), "active beacon is steady")
	check(WorldRules.beacon_color("deleveraging", 0.0) != WorldRules.beacon_color("deleveraging", 0.4), "deleveraging beacon pulses")
	check(WorldRules.beacon_color("liquidating", 0.1).r > 0.9 and WorldRules.beacon_color("liquidating", 0.3).r < 0.2, "liquidating beacon flashes")
	check(WorldRules.beacon_color("closed", 0.0).v < 0.05, "closed beacon is dark")
	check(WorldRules.new_effects([{"code": "rival_deleveraging"}, {"code": "rival_blowup"}], 0) == ["rival_alarm", "rival_blowup", "shake"], "rival effects")
	var symbols := ["ALTO", "BRIN"]
	check(TerminalRules.parse("  brin   gp  ", symbols, "ALTO") == {"ok": true, "page": "GP", "symbol": "BRIN"}, "terminal normalizes commands")
	check(TerminalRules.parse("ALTO", symbols, "BRIN")["page"] == "GP", "symbol opens graph")
	check(TerminalRules.parse("risk", symbols, "BRIN")["symbol"] == "BRIN", "function preserves selected security")
	check(not TerminalRules.parse("REAL GP", symbols, "BRIN")["ok"], "unknown security refused")
	check(not TerminalRules.parse("BRIN BUY 100", symbols, "BRIN")["ok"], "terminal parser cannot submit trades")
	var macro := [{"period_day": 3, "published_day": 4, "revision": 0, "value": "51.2"},
			{"period_day": 4, "published_day": 7, "revision": 1, "value": "47.9"}]
	check(TerminalRules.macro_lines(macro, 4) == PackedStringArray(["D4  47.9  revised D7", "D3  51.2  first print D4"])
			and TerminalRules.macro_lines(macro, 1).size() == 1 and TerminalRules.macro_lines([], 4).is_empty(),
			"activity index rows are newest first, labelled by revision and bounded")
	check(not TerminalRules.parse("", symbols, "BRIN")["ok"], "empty command explained")
	check(TerminalRules.prices([{"marks": {"BRIN": "100"}}, {"marks": {"BRIN": "102.5"}}], "BRIN") == PackedFloat32Array([100, 102.5]), "chart uses only supplied observations")
	check(TerminalRules.prices([], "BRIN").is_empty(), "empty chart safe")
	check(TerminalRules.pct(null) == "--" and TerminalRules.bps("-12.5") == "-12.5", "undefined and negative analytics formatting")
	var keys := WorldRules.SCENARIOS.map(func(sc): return sc[0])
	check(keys == ["case1", "case1-controls", "case1-settlement", "case1-generated", "campaign-v1"],
			"menu offers standard, broker, settlement, generated and campaign scenarios")
	var frames := PackedFloat64Array()
	for i in range(1, 101):
		frames.append(float(i))  # 1..100 ms
	var fs := Perf.stats(frames)
	check(fs["frames"] == 100 and fs["p50_ms"] == 50.0 and fs["p95_ms"] == 95.0 and fs["p99_ms"] == 99.0
			and fs["worst_ms"] == 100.0 and fs["mean_ms"] == 50.5, "frame percentiles are nearest-rank")
	check(fs["over_33_3ms"] == 67 and fs["over_100ms"] == 0, "frames over 33.3 ms and 100 ms are counted strictly")
	check(Perf.stats(PackedFloat64Array())["frames"] == 0, "empty frame report safe")
	var ats := PackedFloat64Array([0.5, 1.0, 1.5, 5.0])
	var ev := Perf.after_event(ats, PackedFloat64Array([90.0, 10.0, 30.0, 80.0]), 0.9, "courier")
	check(ev["worst_ms"] == 30.0 and ev["worst_at_s"] == 1.5, "event worst frame counts only the window after it")
	check(Perf.after_event(ats, PackedFloat64Array([1.0, 1.0, 1.0, 1.0]), -9.0, "x")["worst_at_s"] == -1.0,
			"event before recording reports no frame")
	_lp_checks()
	_ui_checks.call_deferred()


func _lp_checks() -> void:
	# LP inbox text: bands, exact Decimal units, gate terms, and nothing for the PM seat
	var inv := {"policy": "p", "deal_day": 20, "gate_elected": false, "lps": [
			{"id": "Patient", "band": "stable", "requested_units": null, "carried_units": null, "first_cutoff": 55, "contacted": false},
			{"id": "Tactical", "band": "withdrawal_risk", "requested_units": "17500.000001", "carried_units": null, "first_cutoff": 15, "contacted": true}]}
	var mp := {"role": "mp", "clock": {"day": 15}, "attention": {"committed": false}, "investors": inv, "packages": [],
			"notices": [{"day": 13, "code": "lp_band", "text": "Tactical LP relationship is now concerned."},
				{"day": 14, "code": "market", "text": "x"}]}
	check(LpRules.band_text("withdrawal_risk") == "Withdrawal risk" and LpRules.band_text("strong") == "Strong", "LP band labels")
	check(LpRules.units("17500.000001") == "17,500.000001" and LpRules.units("999") == "999"
			and LpRules.units("1234567") == "1,234,567", "LP units keep every Decimal digit")
	var lp_rows := LpRules.rows(mp)
	check(lp_rows.size() == 2 and lp_rows[0] == "Patient   Stable", "LP row without request")
	check("Redemption request 17,500.000001 units, dealt at the day 20 close, payable day 21" in lp_rows[1], "LP request row with exact units and days")
	check(LpRules.contact_reason(mp, inv["lps"][0]) == "" and "already contacted" in LpRules.contact_reason(mp, inv["lps"][1]),
			"contact allowed once per LP before review")
	check("attention already committed" in LpRules.contact_reason(mp.merged({"attention": {"committed": true}}, true), inv["lps"][0]),
			"contact disabled when attention is used")
	check("no LP review remains" in LpRules.contact_reason(mp.merged({"clock": {"day": 16}}, true), inv["lps"][0]),
			"contact disabled after the last review")
	var terms := LpRules.pending_gate_terms(mp)
	check(terms == {"deal_day": 20, "requests": {"Tactical": "17500.000001"}}, "gate terms bind deal day and exact requests")
	check(LpRules.gate_terms_text(terms).begins_with("GATE for the day 20 dealing close, binding requests: Tactical 17,500.000001 units."),
			"gate terms text")
	check(LpRules.pending_gate_terms(mp.merged({"clock": {"day": 21}}, true)).is_empty(), "no gate after the dealing close")
	check(LpRules.has_open_gate({"packages": [{"kind": "gate", "status": "PENDING_APPROVAL"}]})
			and not LpRules.has_open_gate({"packages": [{"kind": "orders", "status": "PENDING_APPROVAL"}]}), "open gate package detection")
	check(LpRules.notices(mp).size() == 1 and LpRules.notices(mp)[0]["code"] == "lp_band", "LP notices filtered by code")
	var pm := {"role": "pm", "clock": {"day": 15}, "investors": null, "packages": [], "notices": []}
	check(LpRules.rows(pm).is_empty() and LpRules.pending_gate_terms(pm).is_empty(), "PM seat sees no LP inbox")
	_campaign_checks()


## Campaign prospect admission and winddown: view-only text, gating and role filtering.
func _campaign_checks() -> void:
	var hidden := {"stage": "prospect", "reason": null, "escrow": "0", "authorized": null, "series_id": null,
			"max_amount": null, "cap_step": null, "dealing_day": null}
	var funded := {"stage": "eligible", "reason": null, "escrow": "5000000", "authorized": null, "series_id": "Anchor",
			"max_amount": "5000000", "cap_step": "1000000", "dealing_day": 20}
	var mp := {"role": "mp", "clock": {"day": 19, "finished": false}, "bots": [], "packages": [], "notices": [], "prospect": funded}
	var pm := mp.merged({"role": "pm"}, true)
	check(not LpRules.is_campaign({"prospect": null}) and not LpRules.is_campaign({}) and LpRules.is_campaign(mp),
			"campaign inferred from a prospect view when the field is absent")
	check(LpRules.is_campaign({"campaign": true}) and not LpRules.is_campaign(mp.merged({"campaign": false}, true)),
			"explicit campaign field wins over inference")
	var unknown := LpRules.prospect_lines(pm.merged({"prospect": hidden}, true))
	check(unknown.size() == 2 and "Terms unknown" in unknown[1] and not "Anchor" in " ".join(unknown),
			"unqualified prospect hides terms the seat has not learned")
	var lines := " ".join(LpRules.prospect_lines(mp))
	check("Anchor: up to $5,000,000 in $1,000,000 steps, dealing close day 20" in lines and "Escrow $5,000,000" in lines,
			"eligible prospect shows exact terms and escrow outside the fund")
	check(LpRules.admission_amounts(mp) == ["5000000", "4000000", "3000000", "2000000", "1000000"],
			"admission amounts are cap-step multiples up to escrow")
	check(LpRules.admission_amounts(pm.merged({"prospect": hidden}, true)).is_empty()
			and LpRules.admission_amounts(mp.merged({"prospect": funded.merged({"escrow": "5000000.5"}, true)}, true)).is_empty(),
			"no amounts without known or whole-dollar terms")
	check(LpRules.admission_reason(mp) == "" and LpRules.admission_reason(pm) == "", "either human partner may propose admission")
	check("eligible" in LpRules.admission_reason(mp.merged({"prospect": funded.merged({"stage": "committed"}, true)}, true)),
			"admission waits for escrow")
	check("already consented" in LpRules.admission_reason(mp.merged({"prospect": funded.merged({"authorized": "3000000"}, true)}, true)),
			"admission cannot be proposed twice after consent")
	check("awaits countersignature" in LpRules.admission_reason(mp.merged(
			{"packages": [{"kind": "admission", "status": "PENDING_APPROVAL"}]}, true)), "one open admission package at a time")
	check("partner bot will not countersign" in LpRules.admission_reason(mp.merged({"bots": ["pm"]}, true)),
			"solo admission explains the bot refusal")
	check(LpRules.decline_reason(mp, "mp") == "" and "managing partner" in LpRules.decline_reason(pm, "pm"),
			"only the managing partner declines the prospect")
	check(LpRules.decline_reason(mp.merged({"bots": ["pm"]}, true), "mp") == "", "solo MP can still decline alone")
	check("already closed" in LpRules.decline_reason(mp.merged({"prospect": funded.merged({"stage": "forfeited"}, true)}, true), "mp")
			and "no longer be declined" in LpRules.decline_reason(mp.merged({"prospect": funded.merged({"authorized": "1000000"}, true)}, true), "mp"),
			"decline refused once closed or consented")
	check(LpRules.winddown_reason(mp) == "" and LpRules.winddown_reason(pm) == "", "either partner may propose a winddown")
	check("campaign mechanic" in LpRules.winddown_reason({"clock": {}}), "no winddown outside the campaign")
	check("already declared" in LpRules.winddown_reason(mp.merged({"notices": [{"code": "winddown_declared"}]}, true))
			and "already declared" in LpRules.winddown_reason(mp.merged({"packages": [{"kind": "winddown", "status": "ELECTED"}]}, true)),
			"winddown declared once")
	check("already declared" in LpRules.winddown_reason(mp.merged({"campaign": true, "winddown": 21}, true))
			and LpRules.winddown_reason(mp.merged({"campaign": true, "winddown": null,
				"notices": [{"code": "winddown_declared"}]}, true)) == "",
			"explicit winddown field wins over inference")
	check("partner bot will not countersign a winddown" in LpRules.winddown_reason(mp.merged({"bots": ["pm"]}, true)),
			"solo winddown explains the bot refusal")
	check("before the end" in LpRules.winddown_reason(mp.merged({"clock": {"finished": true}}, true)), "no winddown after the end")
	check(LpRules.package_text({"kind": "admission", "terms": {"series": "Anchor", "amount": "3000000", "deal_day": 20,
			"issue_price": "100", "hwm": "100"}}) == "ADMIT Anchor: $3,000,000 at the day 20 dealing close, new series at 100, high-water mark 100."
			and LpRules.package_text({"kind": "winddown", "terms": {"day": 12}}).begins_with("WINDDOWN declared day 12")
			and LpRules.package_text({"kind": "orders", "orders": [{"side": "SELL", "qty": 100, "sym": "BRIN"}]}) == "SELL 100 BRIN",
			"committee text for admission, winddown and order packages")


func _ui_checks() -> void:
	# Exercise real controls, chart draw and each function without HTTP or a 3D GPU.
	await process_frame
	var polling := PollTransport.new()
	root.add_child(polling)
	polling.set_process(false)  # deterministic timestamps and no presence socket in this test
	polling.join("http://test", "old-room", "private-test-token")
	polling._poll_timer.stop()
	var first_view := {"version": 4, "fund": {"nav": "123456.78"},
		"clock": {"day": 12, "phase": "PUBLIC_MARK", "next": {"day": 12, "phase": "EXEC_A"}},
		"realtime": {"running": true, "window_seconds": 10, "next_tick_in": 10}}
	polling.reply.emit(0, {"ok": true, "status": 200, "data": first_view, "network_error": false, "headers": PackedStringArray(["ETag: test-v4"])})
	check(polling.view["fund"]["nav"] == "123456.78" and not polling.polling_stale, "successful view initializes polling heartbeat")
	var snapshot_time: float = polling.view_received_at
	polling._poll()
	check(polling.requests[1]["etag"] == "test-v4", "poll preserves validator for unchanged heartbeat")
	polling.reply.emit(1, {"ok": false, "status": 0, "data": null, "network_error": true, "headers": PackedStringArray()})
	check(polling.polling_stale and polling.view["fund"]["nav"] == "123456.78", "poll failure retains NAV and marks view stale")
	var frozen: float = WorldRules.clock_hour(polling.view, 1)
	check(WorldRules.clock_hour(polling.view, 100) == frozen, "stale clock stops interpolating")
	var age_state: Dictionary = polling.poll_state(polling.last_poll_success_at + 9.0)
	check(age_state["age_seconds"] == 9.0 and age_state["stale"], "connection age grows from last successful server contact")
	var connection_hud: CanvasLayer = load("res://scripts/hud.gd").new()
	connection_hud._connection = Label.new()
	connection_hud.add_child(connection_hud._connection)
	connection_hud.show_poll_state(age_state)
	check("data stale" in connection_hud._connection.text and "9s ago" in connection_hud._connection.text, "HUD exposes stale state and contact age")
	polling._poll()
	polling.reply.emit(2, {"ok": false, "status": 304, "data": null, "network_error": false, "headers": PackedStringArray()})
	check(not polling.polling_stale and not polling.view.has("_client_frozen_hour") and polling.view_received_at == snapshot_time,
		"304 recovers heartbeat without resetting snapshot interpolation baseline")
	connection_hud.show_poll_state(polling.poll_state())
	check(connection_hud._connection.text == "", "successful heartbeat clears stale HUD message")
	# Overlapping joins: the older completion cannot replace the new view or unlock its in-flight guard.
	polling._poll()
	polling.join("http://test", "new-room", "new-private-test-token")
	polling._poll_timer.stop()
	check(polling.view.is_empty() and polling.view_etag == "", "new join clears old seat snapshot and validator")
	polling.reply.emit(3, {"ok": true, "status": 200, "data": first_view, "network_error": false, "headers": PackedStringArray()})
	check(polling.view.is_empty() and polling._polling, "old join response neither leaks old view nor clears new request guard")
	var second_view := {"version": 1, "fund": {"nav": "987.65"}, "clock": {"day": 13, "phase": "CLOSE"}}
	polling.reply.emit(4, {"ok": true, "status": 200, "data": second_view, "network_error": false, "headers": PackedStringArray()})
	check(polling.view["fund"]["nav"] == "987.65" and not polling.polling_stale, "new join receives only its own successful view")
	polling._poll()
	check(polling.poll_state(polling.last_poll_success_at + 3.0)["stale"], "unanswered request becomes stale before network timeout")
	polling.reply.emit(5, {"ok": true, "status": 200, "data": second_view, "network_error": false, "headers": PackedStringArray()})
	check(not polling.polling_stale and not polling.view.has("_client_frozen_hour"), "fresh 200 view recovers prolonged unanswered poll")
	connection_hud.free()
	polling.queue_free()
	var ending_hud: CanvasLayer = load("res://scripts/hud.gd").new()
	var record_box := VBoxContainer.new()
	root.add_child(record_box)
	ending_hud._debrief_investors(record_box, null)
	check(record_box.get_child_count() == 0, "ending omits absent investor record controls")
	ending_hud._debrief_investors(record_box, {"policy": "lp-ui", "final": {"Patient": {"confidence": "71.000001", "band": "stable"}},
		"carried_units": {"Patient": "0.000001"}, "checkpoints": []})
	check(record_box.find_child("InvestorRecordHeading", true, false) != null, "investor heading renders independently of research theses")
	var exact_investor_label := false
	var empty_checkpoint_label := false
	for row in record_box.get_children():
		if row is Label:
			check(row.autowrap_mode == TextServer.AUTOWRAP_WORD_SMART or row.name == "InvestorRecordHeading", "investor record rows wrap in ending scroll")
			if "71.000001" in row.text: exact_investor_label = true
			if "No relationship checkpoints" in row.text: empty_checkpoint_label = true
	check(exact_investor_label and empty_checkpoint_label, "actual ending labels preserve confidence and explain missing checkpoints")
	record_box.queue_free()
	ending_hud.free()
	var recovery_hud: CanvasLayer = load("res://scripts/hud.gd").new()
	var record_transport := RunRecordTransport.new()
	root.add_child(record_transport)
	recovery_hud._run_record_api = record_transport
	recovery_hud.view = {"version": 42}
	var ending_panel := PanelContainer.new()
	root.add_child(ending_panel)
	recovery_hud._debrief = ending_panel
	var ending_box := VBoxContainer.new()
	ending_panel.add_child(ending_box)
	recovery_hud._debrief_research(ending_box)
	var record_status: Label = ending_box.find_child("RunRecordStatus", true, false)
	var record_retry: Button = ending_box.find_child("RetryRunRecord", true, false)
	check(record_status.text == "Loading run record..." and record_transport.calls == 1, "ending record shows loading during real async read")
	check(record_transport.options == {"version": 42}, "record recovery reads completed version without gameplay command")
	record_transport.response = {"ok": false}
	record_transport.respond.emit()
	await process_frame
	check("Run record unavailable" in record_status.text and record_retry.visible and not record_retry.disabled, "failed ending read exposes retry")
	record_retry.pressed.emit()
	record_retry.pressed.emit()
	check(record_transport.calls == 2 and record_retry.disabled, "duplicate retry signals share one in-flight read")
	record_transport.response = {"ok": true, "data": {"research": {"theses": [], "seats": {}},
		"investors": {"policy": "recovered", "checkpoints": [], "final": {}, "carried_units": {}}}}
	record_transport.respond.emit()
	await process_frame
	check(record_status.text == "Run record loaded." and not record_retry.visible, "retry recovers ending record")
	record_retry.pressed.emit()
	check(record_transport.calls == 2, "loaded record ignores stale retry signals and avoids duplicate rows")
	check(ending_box.find_child("InvestorRecordHeading", true, false) != null and ending_box.find_child("ResearchHeading", true, false) == null, "investors recover even without research theses")
	# A fresh pending record on a hidden panel must never attach late data.
	var stale_box := VBoxContainer.new()
	ending_panel.add_child(stale_box)
	recovery_hud._debrief_research(stale_box)
	ending_panel.hide()
	record_transport.respond.emit()
	await process_frame
	check(stale_box.find_child("InvestorRecordHeading", true, false) == null, "closed ending panel ignores late record response")
	ending_panel.show()
	var replaced_box := VBoxContainer.new()
	ending_panel.add_child(replaced_box)
	recovery_hud._debrief_research(replaced_box)
	var replacement_panel := PanelContainer.new()
	root.add_child(replacement_panel)
	var replacement_box := VBoxContainer.new()
	replacement_panel.add_child(replacement_box)
	recovery_hud._debrief = replacement_panel
	recovery_hud._debrief_research(replacement_box)
	var calls_before: int = record_transport.calls
	record_transport.respond.emit()
	await process_frame
	check(replaced_box.find_child("InvestorRecordHeading", true, false) == null and record_transport.calls == calls_before + 1, "replacement ignores old response and starts its own guarded read")
	record_transport.respond.emit()
	await process_frame
	check(replacement_box.find_child("InvestorRecordHeading", true, false) != null, "replacement ending panel receives only its own record")
	var changed_box := VBoxContainer.new()
	replacement_panel.add_child(changed_box)
	recovery_hud._debrief_research(changed_box)
	recovery_hud.view = {"version": 43}
	record_transport.respond.emit()
	await process_frame
	var changed_status: Label = changed_box.find_child("RunRecordStatus", true, false)
	var changed_retry: Button = changed_box.find_child("RetryRunRecord", true, false)
	check("Run record changed while loading" in changed_status.text and changed_retry.visible and not changed_retry.disabled,
		"same ending panel version change exposes recovery instead of loading forever")
	check(changed_box.find_child("InvestorRecordHeading", true, false) == null, "old completed version never attaches record rows")
	changed_retry.pressed.emit()
	check(record_transport.options == {"version": 43}, "version-change retry requests latest completed version")
	record_transport.respond.emit()
	await process_frame
	check(changed_status.text == "Run record loaded.", "version-change retry recovers same ending panel")
	ending_panel.queue_free()
	replacement_panel.queue_free()
	record_transport.queue_free()
	recovery_hud.free()
	var terminal := ForgeTerminal.new()
	root.add_child(terminal)
	terminal._loading = true  # suppress transport; server/API tests cover that boundary
	terminal.data = {"version": 4, "as_of": {"day": 12, "date": "2026-01-20", "phase": "PUBLIC_MARK"},
			"quotes": [{"sym": "BRIN", "mark": "100", "qty": -12500, "mv": "-1250000", "weight": "-0.05",
				"borrowed": 12500, "borrow_rate": "0.02", "change_bps": "0", "since_start_bps": "0", "observed_event_volume": 1000000}],
			"history": [{"marks": {"BRIN": "100"}}], "risk": {"stresses": [{"label": "Test stress", "pnl": "-1",
				"nav": "99", "headroom": "-1", "margin_breach": true}]},
			"news": [{"day": 12, "date": "2026-01-20", "phase": "PUBLIC_MARK", "kind": "alert", "text": "BRIN recall"}],
			"orders": [{"sym": "BRIN", "side": "COVER", "qty": 500, "filled": 100, "remaining": 400,
				"status": "PARTIALLY_FILLED", "forced": null, "order_id": "x", "fills": [{"price": "100"}]}],
			"league": [{"id": "you", "status": "active", "return_bps": "0", "style": "long_short"}]}
	terminal.open()
	check(terminal.is_open(), "terminal opens over world")
	for page in TerminalRules.PAGES:
		terminal.navigate(page)
		await process_frame
		check(terminal._body.get_child_count() > 0 and terminal.page == page, "terminal renders " + page)
	terminal.navigate("GP")
	var old_page := terminal.page
	terminal._command("unknown command")
	check(terminal.page == old_page and terminal._status.text != "", "invalid command preserves current page")
	terminal._command("RISK")
	check(terminal.page == "RISK" and terminal._status.text == "", "valid command navigates")
	terminal._entry.text = "BRIN G"
	terminal.set_view({"version": 4})
	terminal._render()
	check(terminal._entry.text == "BRIN G", "refresh preserves command entry")
	var transport := TerminalTransport.new()
	terminal._api = transport
	terminal._loading = false
	transport.response = {"ok": false}
	terminal._fetch()
	check(terminal._stale and "STALE" in terminal._as_of.text, "disconnection marks retained data stale")
	transport.response = {"ok": true, "data": terminal.data.duplicate(true)}
	terminal._fetch()
	check(not terminal._stale and terminal._status.text == "", "successful heartbeat recovers stale snapshot")
	terminal._command("invalid")
	terminal._fetch()
	check(terminal._status.text != "", "unchanged heartbeat preserves command error")
	transport.response = {"ok": true, "data": {"version": 3}}
	terminal._fetch()
	check(terminal.data["version"] == 4, "late response cannot replace a newer snapshot")
	transport.response = {"ok": true, "data": {"version": 4, "comparisons": [{"strategy": "cost",
			"status": "cured", "events_to_cure": 2, "execution_cost": "12.00", "assumptions": {},
			"path": [{"event": 1, "nav": "1000", "headroom": "10", "credit_left": "100",
				"pending_settlements": 1, "collateral_funded": true}],
			"draft": [{"sym": "BRIN", "side": "COVER", "qty": 29}]}]}}
	terminal.navigate("RISK")
	terminal._run_lab()
	check(terminal._lab.get("version") == 4 and not terminal._lab_loading, "liquidity response renders")
	var review: Button
	for child in terminal._body.get_children():
		if child is Button and child.text.begins_with("Review first-event"):
			review = child
	check(review != null and not review.disabled, "fresh liquidity draft can be reviewed")
	terminal.data["version"] = 5
	terminal._render()
	for child in terminal._body.get_children():
		if child is Button and child.text.begins_with("Review first-event"):
			check(child.disabled, "stale liquidity draft cannot be reviewed")
	terminal._lab_long = -40
	terminal._render()
	check(terminal._lab_long == -40, "lab assumptions survive refresh")
	terminal.navigate("REPLAY")
	check(terminal._body.get_child_count() == 2, "unfinished replay displays locked state")
	terminal.data["finished"] = true
	transport.response = {"ok": true, "data": {"branch_id": "test", "nav_difference": "0", "finished": true,
			"timeline": [{"seq": 1, "role": "pm", "type": "ticket", "status": "accepted", "can_omit": true,
				"after": {"day": 13, "phase": "EXEC_A", "headroom": "100"}}]}}
	terminal._run_replay()
	check(terminal._replay_data.get("branch_id") == "test", "completed replay result renders")
	var omissions := 0
	for child in terminal._body.get_children():
		if child is Button and child.text.begins_with("Compare run without"):
			omissions += 1
	check(omissions == 1, "replay offers recorded decision comparison")
	terminal.data["role"] = "mp"
	terminal.data["risk"]["controls"] = {"status": "break", "statement_queue": [
			{"id": "opening-cash", "status": "open", "age_calendar_days": 1, "revision": 2,
				"can_resolve": true, "history": []}]}
	terminal.data["risk"]["controls"]["administrator"] = {"status": "checked", "close_count": 13,
			"claim_count": 1, "series": [{"series_id": "Seed", "units": "750", "net": "81000",
				"provision": "1500", "hwm": "100"}], "claims": [{"date": "2026-01-30", "units": "250",
				"series_id": "Seed", "price": "108", "payable": "27000", "crystallized_fee": "500"}]}
	terminal.navigate("RISK")
	var admin_visible := false
	var pending_certificate := false
	for child in terminal._body.get_children():
		if child is Label and "CERTIFICATION: PENDING" in child.text: pending_certificate = true
	check(pending_certificate, "RISK certificate stays pending before a dealing close")
	terminal.data["risk"]["certification"] = {"status": "broken", "certificates": [{
			"day": 20, "date": "2026-01-30", "status": "broken", "independent_nav": "100.00",
			"book_nav": "100.02", "difference": "0.02", "tolerance": "0.01", "reasons": ["shadow_nav"],
			"strikes": [{"series_id": "Seed", "units": "1", "net": "100.00", "nav_per_unit": "100.000000"}],
			"redemptions": [{"series_id": "Seed", "payable": "10.00", "journal_payable": "9.99", "residual": "-0.01", "residual_bound": "0.06"}]}]}
	terminal.navigate("RISK")
	var broken_certificate := false
	var residual_visible := false
	for child in terminal._body.get_children():
		if child is Label and "Certification blocked: shadow nav" in child.text: broken_certificate = true
		if child is Label and "residual -0.01 / bound 0.06" in child.text: residual_visible = true
	check(broken_certificate and residual_visible, "RISK shows certificate refusal and exact redemption residual")
	var claim_visible := false
	for child in terminal._body.get_children():
		if child is Label and "LP / FEE CHECK: CHECKED" in child.text: admin_visible = true
		if child is Label and "crystallized fee" in child.text: claim_visible = true
	check(admin_visible and claim_visible, "RISK renders independent LP controls and dated redemption claim")
	var review_buttons := 0
	for child in terminal._body.get_children():
		if child is Button and child.text.begins_with("Accept matching correction"):
			review_buttons += 1
	check(review_buttons == 1, "MP can review a published matching statement correction")
	terminal._resolve_statement("opening-cash", 2)
	check(transport.last_command.get("type") == "resolve_statement" and transport.last_command.get("revision") == 2
			and transport.last_command.get("version") == terminal.data["version"], "statement command binds revision and room version")
	terminal.data["role"] = "pm"
	terminal._render()
	review_buttons = 0
	for child in terminal._body.get_children():
		if child is Button and child.text.begins_with("Accept matching correction"): review_buttons += 1
	check(review_buttons == 0, "PM sees statement evidence without MP resolution action")
	# research page: published prior/posterior, exact complement, one thesis command through the Api path
	check(TerminalRules.parse("research", [], "BRIN") == {"ok": true, "page": "RESEARCH", "symbol": "BRIN"}, "parse RESEARCH page")
	check(TerminalRules.thesis_forecast("0.35") == {"calm": "0.350000", "stressed": "0.650000"}, "thesis complement is exact")
	check(TerminalRules.thesis_forecast("0.000001") == {"calm": "0.000001", "stressed": "0.999999"}, "complement at 6dp edge")
	check(TerminalRules.thesis_forecast("1") == {"calm": "1.000000", "stressed": "0.000000"}, "certain calm")
	check(TerminalRules.micros("0.1") + TerminalRules.micros(TerminalRules.thesis_forecast("0.1")["stressed"]) == 1000000,
			"0.1 + complement sums to exactly one (no float drift)")
	for bad in ["", "1.000001", "1.5", "-0.1", "0.1234567", ".5", "50%", "0.5.0", "abc", "1e-3"]:
		check(TerminalRules.thesis_forecast(bad).is_empty(), "rejects thesis entry '%s'" % bad)
	var lines := TerminalRules.research_lines({"theses": [{"role": "pm", "question": "regime:14", "recorded_day": 15,
			"forecast": {"calm": "0.700000", "stressed": "0.300000"}, "true_regime": "calm", "brier": "0.180000"}],
			"seats": {"pm": {"theses": 1, "mean_brier": "0.180000"}, "mp": {"theses": 0, "mean_brier": null}}})
	check(lines.size() == 2 and "true CALM" in lines[0] and "Brier 0.180000" in lines[0] and lines[1].begins_with("PM mean Brier 0.180000"),
			"debrief research lines: forecast, truth, Brier, seat mean only for seats with theses")
	check(TerminalRules.research_lines({"theses": [], "seats": {}}).is_empty(), "no research panel without theses")
	terminal.data["regime"] = {"question": "regime:14", "period_day": 14, "prior": {"calm": "0.671500", "stressed": "0.328500"},
			"posterior": {"calm": "0.850000", "stressed": "0.150000"}, "evidence": 3, "method": "Exact forward filter."}
	terminal._thesis_calm = ""
	terminal.data["finished"] = false  # the replay checks above finished the season
	terminal.navigate("RESEARCH")
	var calm_input: LineEdit = terminal.find_child("ThesisCalm", true, false)
	var thesis_send: Button = terminal.find_child("ThesisSend", true, false)
	check(calm_input != null and thesis_send.disabled and calm_input.focus_mode != Control.FOCUS_NONE
			and thesis_send.focus_mode != Control.FOCUS_NONE, "thesis entry is keyboard reachable and starts disabled")
	calm_input.text = "0.25"
	calm_input.text_changed.emit("0.25")
	check(not thesis_send.disabled, "valid calm probability enables the thesis")
	transport.last_command = {}
	calm_input.text_submitted.emit("0.25")
	check(transport.last_command == {"type": "thesis", "question": "regime:14", "forecast": {"calm": "0.250000", "stressed": "0.750000"}},
			"Enter sends one exact thesis for the live question")
	terminal.data["finished"] = true
	terminal._render()
	check((terminal.find_child("ThesisSend", true, false) as Button).disabled, "finished season closes thesis entry")
	terminal.data["finished"] = false
	terminal.data["regime"] = null
	terminal._render()
	check(terminal.find_child("ThesisCalm", true, false) == null, "no thesis entry without a live question")
	transport.free()
	terminal.close()
	check(not terminal.is_open(), "terminal closes")
	terminal.queue_free()
	await process_frame
	# Load after autoload initialization: Hud references the Api singleton.
	var hud: Variant = load("res://scripts/hud.gd").new()
	root.add_child(hud)
	hud.role = "pm"
	var saved_level: int = hud.music.level
	var saved_muted: bool = hud.sfx.muted
	hud.music.level = 2
	hud.sfx.muted = false
	hud.music.refresh(false)
	check(hud.music._player.playing and hud.music._player.stream.loop_mode == AudioStreamWAV.LOOP_FORWARD, "HUD music loops when audible")
	hud.music.refresh(true)
	check(not hud.music._player.playing, "HUD music stops under the global mute")
	hud._show_mute()
	check(hud._music_button.text == "Music on [N]", "music toggle labelled separately from sound")
	hud.music.level = saved_level  # restore without writing the developer's settings file
	hud.sfx.muted = saved_muted
	hud.music.refresh(true)
	hud.view = {"attention": {"committed": true}, "research": {"budget": 2, "used": [],
			"topics": ["demand_survey"], "assignments": {"demand_survey": {"location": "research"}},
			"shared": [], "evidence": [{"text": "Private demand finding", "refs": {"topic": "crowding", "owner": "pm"}}]}}
	hud.open_panel("research")
	var can_share := false
	var assignment_disabled := false
	for child in hud._panel_body.get_children():
		if child is Button:
			if child.text.begins_with("Share this evidence"): can_share = not child.disabled
			if "demand survey" in child.text: assignment_disabled = child.disabled
	check(can_share, "owner can share evidence from research desk")
	check(assignment_disabled, "committed attention disables new assignment")
	hud.view["research"]["shared"] = ["crowding"]
	hud.open_panel("research")
	await process_frame
	var share_buttons := 0
	for child in hud._panel_body.get_children():
		if child is Button and child.text.begins_with("Share this evidence"): share_buttons += 1
	check(share_buttons == 0, "shared evidence has no duplicate share action")
	# Campaign panels: real controls in the investor lounge and committee room
	var funded := {"stage": "eligible", "reason": null, "escrow": "5000000", "authorized": null, "series_id": "Anchor",
			"max_amount": "5000000", "cap_step": "1000000", "dealing_day": 20}
	hud.role = "mp"
	hud.view = {"clock": {"day": 19, "finished": false}, "bots": [], "packages": [], "notices": [], "series": [],
			"investors": null, "prospect": funded, "ready": []}
	hud.open_panel("lp")
	var pick: OptionButton = hud._panel_body.find_child("AdmissionAmount", true, false)
	check(pick != null and pick.item_count == 5 and pick.get_item_text(0) == "$5,000,000", "lounge offers admission amounts")
	check(_button_text(hud, "Decline the prospective LP") != null, "MP lounge offers decline")
	hud.role = "pm"
	hud.open_panel("lp")
	await process_frame
	check(hud._panel_body.find_child("AdmissionAmount", true, false) != null and _button_text(hud, "Decline the prospective LP") == null,
			"PM may propose admission but not decline")
	hud.view["bots"] = ["mp"]
	hud.open_panel("lp")
	await process_frame
	check(hud._panel_body.find_child("AdmissionAmount", true, false) == null and _label_text(hud, "partner bot will not countersign") != null,
			"solo lounge explains why admission cannot complete")
	hud.open_panel("committee")
	await process_frame
	var wd: Button = _button_text(hud, "Winddown")
	check(wd != null and wd.disabled and "partner bot" in wd.text, "solo committee disables winddown with the reason")
	hud.view["bots"] = []
	hud.view["packages"] = [{"package_id": "w1", "proposer": "mp", "digest": "abcdef0123456", "status": "PENDING_APPROVAL",
			"signatures": ["mp"], "kind": "winddown", "terms": {"day": 19}, "orders": []}]
	hud.open_panel("committee")
	await process_frame
	check(_label_text(hud, "WINDDOWN declared day 19") != null and _button_text(hud, "Countersign this exact package") != null
			and _button_text(hud, "Winddown").disabled, "partner countersigns a pending winddown; no second proposal")
	hud.view["packages"] = []
	hud.open_panel("committee")
	await process_frame
	var propose_wd: Button = _button_text(hud, "Propose a controlled winddown")
	check(propose_wd != null and not propose_wd.disabled, "two-human committee can propose a winddown")
	hud.view.erase("prospect")
	hud.open_panel("committee")
	await process_frame
	check(_button_text(hud, "Winddown") == null and _button_text(hud, "Propose a controlled winddown") == null,
			"no winddown control outside the campaign")
	hud.queue_free()
	await process_frame

	print("%d failure(s)" % failures)
	quit(1 if failures else 0)


func _button_text(hud: Variant, prefix: String) -> Button:
	for child in hud._panel_body.get_children():
		if child is Button and not child.is_queued_for_deletion() and child.text.begins_with(prefix):
			return child
	return null


func _label_text(hud: Variant, part: String) -> Label:
	for child in hud._panel_body.get_children():
		if child is Label and not child.is_queued_for_deletion() and part in child.text:
			return child
	return null
