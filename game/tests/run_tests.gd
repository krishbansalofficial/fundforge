extends SceneTree
## Headless unit tests for the pure world rules:
##   godot --headless --path game --script res://tests/run_tests.gd

var failures := 0


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

	# partner avatar goes where their last decision was made
	var v := {"decisions": [{"role": "mp", "type": "research"}, {"role": "pm", "type": "ticket"}, {"role": "mp", "type": "accept_replacement"}]}
	check(WorldRules.partner_location(v, "mp") == "broker", "partner location from last decision")
	check(WorldRules.partner_location({"decisions": []}, "pm") == "trading", "default partner location")

	check(WorldRules.money("-1234567.4") == "-$1,234,567", "money formatting")
	check(WorldRules.headroom_ratio({"nav": "110", "maintenance_req": "100"}) > 1.09, "headroom ratio")

	print("%d failure(s)" % failures)
	quit(1 if failures else 0)
