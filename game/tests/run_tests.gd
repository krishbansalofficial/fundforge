extends SceneTree
## Headless unit tests for the pure world rules:
##   godot --headless --path game --script res://tests/run_tests.gd

var failures := 0

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
	# iso projection round-trips
	for g in [Vector2(0, 0), Vector2(3.5, 7.25), Vector2(23, 1)]:
		check(WorldRules.to_grid(WorldRules.to_screen(g)).distance_to(g) < 0.001, "iso round trip %s" % g)

	# locations
	check(WorldRules.location_at(Vector2(5, 4)) == "trading", "trading floor hit test")
	check(WorldRules.location_at(Vector2(8.5, 19)) == "broker", "prime broker across the street")
	check(WorldRules.location_at(Vector2(10, 15.5)) == "", "street is not a room")
	for key in WorldRules.LOCATIONS:
		check(WorldRules.location_at(WorldRules.LOCATIONS[key]["spot"]) == key, "spot inside %s" % key)

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
	check(not TerminalRules.parse("", symbols, "BRIN")["ok"], "empty command explained")
	check(TerminalRules.prices([{"marks": {"BRIN": "100"}}, {"marks": {"BRIN": "102.5"}}], "BRIN") == PackedFloat32Array([100, 102.5]), "chart uses only supplied observations")
	check(TerminalRules.prices([], "BRIN").is_empty(), "empty chart safe")
	check(TerminalRules.pct(null) == "--" and TerminalRules.bps("-12.5") == "-12.5", "undefined and negative analytics formatting")
	var keys := WorldRules.SCENARIOS.map(func(sc): return sc[0])
	check(keys == ["case1", "case1-controls", "case1-settlement", "case1-generated"],
			"menu offers standard, broker, settlement and generated scenarios")
	_ui_checks.call_deferred()


func _ui_checks() -> void:
	# Exercise real controls, chart draw and each function without HTTP or a 3D GPU.
	await process_frame
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
	transport.free()
	terminal.close()
	check(not terminal.is_open(), "terminal closes")
	terminal.queue_free()
	await process_frame
	# Load after autoload initialization: Hud references the Api singleton.
	var hud: Variant = load("res://scripts/hud.gd").new()
	root.add_child(hud)
	hud.role = "pm"
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
	hud.queue_free()
	await process_frame

	print("%d failure(s)" % failures)
	quit(1 if failures else 0)
