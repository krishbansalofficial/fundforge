class_name ForgeTerminal
extends CanvasLayer
## Market workstation. Reviews use authenticated commands; trading returns to the governed desk.

signal trading_requested
signal cure_draft_requested(orders: Array, source_version: int)
signal open_changed(is_open: bool)

const INK := Color("#dce6ef")
const MUTED := Color("#8fa5ba")
const AMBER := Color("#ffb44a")
const GREEN := Color("#6cdfaa")
const RED := Color("#ff817c")

var data: Dictionary = {}
var page := "MON"
var symbol := "BRIN"
var _root: PanelContainer
var _body: VBoxContainer
var _entry: LineEdit
var _status: Label
var _as_of: Label
var _buttons: Dictionary = {}
var _view_version := -1
var _loading := false
var _api: Node
var _stale := false
var _lab: Dictionary = {}
var _lab_loading := false
var _lab_long := -15.0
var _lab_short := 10.0
var _lab_volume := 100.0
var _lab_horizon := 5.0
var _replay_data: Dictionary = {}
var _replay_loading := false
var _thesis_calm := ""  # survives re-renders while the partner or clock changes the room
var _thesis_sending := false


func _ready() -> void:
	_api = get_node("/root/Api")
	layer = 20
	_root = PanelContainer.new()
	_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_root.add_theme_stylebox_override("panel", _box(Color("#050b12")))
	var theme := Theme.new()
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Consolas", "DejaVu Sans Mono", "monospace"])
	theme.default_font = font
	theme.default_font_size = 14
	_root.theme = theme
	_root.hide()
	add_child(_root)
	var margin := MarginContainer.new()
	for edge in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_" + edge, 20)
	_root.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	margin.add_child(column)
	var header := HBoxContainer.new()
	column.add_child(header)
	var title := _label("FORGE TERMINAL", AMBER, 24)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var trade := Button.new()
	trade.text = "Trading desk"
	trade.pressed.connect(func(): close(); trading_requested.emit())
	header.add_child(trade)
	var close_button := Button.new()
	close_button.text = "Close [Esc]"
	close_button.pressed.connect(close)
	header.add_child(close_button)
	_as_of = _label("Connecting to the fund...", MUTED)
	column.add_child(_as_of)
	var nav := HBoxContainer.new()
	column.add_child(nav)
	for i in range(TerminalRules.PAGES.size()):
		var function: String = TerminalRules.PAGES[i]
		var b := Button.new()
		b.text = "F%d %s" % [i + 1, function]
		b.toggle_mode = true
		b.pressed.connect(func(): navigate(function))
		nav.add_child(b)
		_buttons[function] = b
	_entry = LineEdit.new()
	_entry.placeholder_text = "Function or symbol + Enter: MON / BRIN GP / PORT / RISK / NEWS / ORDERS / STREET / HELP / REPLAY / RESEARCH"
	_entry.text_submitted.connect(_command)
	column.add_child(_entry)
	_status = _label("", AMBER)
	column.add_child(_status)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	_body = VBoxContainer.new()
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_theme_constant_override("separation", 12)
	scroll.add_child(_body)
	column.add_child(_label("FICTIONAL MARKET   |   Observed marks, not executable quotes   |   Orders require the fund's normal approvals", MUTED, 12))
	_api.command_failed.connect(func(message):
		if is_open(): _status.text = message)
	var heartbeat := Timer.new()
	heartbeat.wait_time = 2.0
	heartbeat.timeout.connect(func():
		if is_open(): _fetch())
	add_child(heartbeat)
	heartbeat.start()


func _box(color: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = color
	return style


func is_open() -> bool:
	return _root != null and _root.visible


func open() -> void:
	_root.show()
	open_changed.emit(true)
	_render()
	_entry.grab_focus()
	_fetch()


func close() -> void:
	_root.hide()
	_entry.release_focus()
	open_changed.emit(false)


func set_view(view: Dictionary) -> void:
	_view_version = int(view.get("version", -1))
	if is_open() and _view_version != int(data.get("version", -2)):
		_fetch()


func _input(event: InputEvent) -> void:
	if not is_open() or not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()
	elif event.keycode >= KEY_F1 and event.keycode <= KEY_F10:
		navigate(TerminalRules.PAGES[event.keycode - KEY_F1])
		get_viewport().set_input_as_handled()


func _fetch() -> void:
	if _loading:
		return
	_loading = true
	var response: Dictionary = await _api.terminal()
	_loading = false
	if not response.get("ok", false):
		_stale = true
		_status.text = "Connection interrupted. Showing the last received snapshot; reconnecting on the next update."
		_as_of.text = "DISCONNECTED / DATA MAY BE STALE"
		return
	var next: Dictionary = response.get("data", {})
	if int(next.get("version", -1)) < int(data.get("version", -1)):
		return
	var changed := int(next.get("version", -1)) != int(data.get("version", -1)) or _stale
	data = next
	if _stale:
		_status.text = ""
	_stale = false
	if is_open() and changed:
		_render()


func navigate(function: String, selected := "") -> void:
	page = function
	if selected != "":
		symbol = selected
	_status.text = ""
	_render()


func _command(command: String) -> void:
	var symbols: Array = data.get("quotes", []).map(func(q): return q["sym"])
	var result := TerminalRules.parse(command, symbols, symbol)
	if not result["ok"]:
		_status.text = result["error"]
		return
	_entry.clear()
	navigate(result["page"], result["symbol"])


func _label(text: String, color := INK, font_size := 14) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_color_override("font_color", color)
	label.add_theme_font_size_override("font_size", font_size)
	return label


func _text(text: String, color := INK, font_size := 14) -> void:
	var label := _label(text, color, font_size)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(label)


func _grid(headers: Array, parent: Node = null) -> GridContainer:
	var grid := GridContainer.new()
	grid.columns = headers.size()
	grid.add_theme_constant_override("h_separation", 22)
	grid.add_theme_constant_override("v_separation", 8)
	(parent if parent != null else _body).add_child(grid)
	for heading in headers:
		grid.add_child(_label(heading, AMBER))
	return grid


func _render() -> void:
	var focus := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
	var refocus := focus != null and focus.name == "ThesisCalm"  # keep typing through a re-render
	for child in _body.get_children():
		_body.remove_child(child)
		child.queue_free()
	for function in _buttons:
		_buttons[function].set_pressed_no_signal(function == page)
	if data.is_empty() and page != "HELP":
		_text("Loading market observations...", MUTED)
		return
	var clock: Dictionary = data.get("as_of", {})
	_as_of.text = "Day %d  %s  %s  |  %s  |  Simulated market / your seat" % [int(clock.get("day", 0)),
			clock.get("date", ""), clock.get("phase", ""), symbol]
	if _stale:
		_as_of.text += "  /  DISCONNECTED: DATA MAY BE STALE"
	match page:
		"MON": _monitor()
		"GP": _graph()
		"PORT": _portfolio()
		"RISK": _risk()
		"NEWS": _news()
		"ORDERS": _orders()
		"STREET": _street()
		"HELP": _help()
		"REPLAY": _replay_page()
		"RESEARCH": _research_page(refocus)


func _replay_page() -> void:
	_text("CAUSAL REPLAY / COMPLETED RUN", AMBER, 20)
	if not data.get("finished", false):
		_text("Replay unlocks after the season. During play, use the RISK lab for scenarios based on currently observed information.", MUTED)
		return
	var baseline := Button.new()
	baseline.text = "Replaying..." if _replay_loading else "Replay recorded run"
	baseline.disabled = _replay_loading or _stale
	baseline.pressed.connect(func(): _run_replay())
	_body.add_child(baseline)
	if _replay_data.is_empty(): return
	_text(_replay_data.get("policy", ""), MUTED)
	_text("Branch %s / NAV difference %s / %s" % [str(_replay_data.get("branch_id", "")).substr(0, 12),
			WorldRules.money(_replay_data.get("nav_difference", 0)),
			"FINISHED" if _replay_data.get("finished", false) else "UNFINISHED: original decisions no longer reach the ending"], AMBER)
	for event in _replay_data.get("incidents", []):
		_text("D%s %s / %s" % [event["day"], event["code"], event["text"]], RED)
	for rejection in _replay_data.get("rejected", []):
		_text("Decision %s rejected: %s" % [rejection["seq"], rejection["reason"]], RED)
	for decision in _replay_data.get("timeline", []):
		var after: Dictionary = decision["after"]
		_text("#%s D%s %s / %s %s / %s / NAV change %s / headroom %s" % [
				decision["seq"], after["day"], after["phase"], decision["role"], decision["type"], decision["status"],
				WorldRules.money(decision.get("nav_delta", 0)), WorldRules.money(after["headroom"])])
		if decision.get("can_omit", false):
			var omit := Button.new()
			omit.text = "Compare run without decision #%s" % decision["seq"]
			omit.disabled = _replay_loading or _stale
			omit.pressed.connect(func(): _run_replay(int(decision["seq"])))
			_body.add_child(omit)


func _run_replay(omit_seq := 0) -> void:
	if _replay_loading: return
	_replay_loading = true
	_render()
	var options := {"version": int(data.get("version", -1))}
	if omit_seq > 0: options["omit_seq"] = omit_seq
	var result: Dictionary = await _api.debrief(options)
	_replay_loading = false
	if result.get("ok", false):
		_replay_data = result["data"]
		_status.text = ""
	else:
		_status.text = str(result.get("data", {}).get("detail", "Replay unavailable.")) if result.get("data") is Dictionary else "Replay unavailable."
	if is_open(): _render()


func _monitor() -> void:
	_text("MARKET MONITOR", AMBER, 20)
	var panes := HBoxContainer.new()
	panes.add_theme_constant_override("separation", 32)
	_body.add_child(panes)
	var left := VBoxContainer.new()
	panes.add_child(left)
	var grid := _grid(["Symbol / graph", "Mark", "Last event bps", "Since start bps", "Position", "Borrow APR"], left)
	for q in data.get("quotes", []):
		var sym: String = q["sym"]
		var button := Button.new()
		button.text = sym + " >"
		button.pressed.connect(func(): navigate("GP", sym))
		grid.add_child(button)
		grid.add_child(_label("%.4f" % float(q["mark"])))
		var delta: Variant = q["change_bps"]
		var color := MUTED if delta == null else (GREEN if float(str(delta)) >= 0 else RED)
		grid.add_child(_label(TerminalRules.bps(delta), color))
		grid.add_child(_label(TerminalRules.bps(q["since_start_bps"])))
		grid.add_child(_label(str(int(q["qty"]))))
		grid.add_child(_label(TerminalRules.pct(q["borrow_rate"])))
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 12)
	panes.add_child(right)
	right.add_child(_label(symbol + " / OBSERVED MARKS", AMBER))
	var chart := TerminalChart.new()
	chart.values = TerminalRules.prices(data.get("history", []), symbol)
	right.add_child(chart)
	var risk: Dictionary = data.get("risk", {})
	right.add_child(_label("FUND WATCH", AMBER))
	right.add_child(_label("NAV %s   /   Headroom %s" % [WorldRules.money(risk.get("nav", 0)), WorldRules.money(risk.get("headroom", 0))],
			RED if float(str(risk.get("headroom", 0))) < 0 else GREEN))
	right.add_child(_label("Cash %s   /   Restricted %s" % [WorldRules.money(risk.get("cash", 0)), WorldRules.money(risk.get("restricted_collateral", 0))]))
	right.add_child(_label("LATEST PUBLISHED HEADLINES", AMBER))
	var news: Array = data.get("news", [])
	for i in range(news.size() - 1, maxi(-1, news.size() - 4), -1):
		var headline := _label("D%d / %s" % [int(news[i]["day"]), news[i]["text"]], RED if news[i]["kind"] == "alert" else INK)
		headline.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		right.add_child(headline)
	var macro: Array = data.get("macro", [])
	if not macro.is_empty():
		right.add_child(_label("STREET ACTIVITY INDEX / AS PUBLISHED (above 50 = expansion)", AMBER))
		for line in TerminalRules.macro_lines(macro, 4):
			right.add_child(_label(line))
	_text("Change is from the previous observed event. Select a symbol to inspect its history.", MUTED)


func _graph() -> void:
	var q := TerminalRules.quote(data, symbol)
	if q.is_empty():
		_text("Select a known symbol from MON.", MUTED)
		return
	_text("%s / PRICE HISTORY    %.4f" % [symbol, float(q["mark"])], AMBER, 20)
	var chart := TerminalChart.new()
	chart.values = TerminalRules.prices(data.get("history", []), symbol)
	_body.add_child(chart)
	_text("Event-spaced observations / no invented candles. History begins when this fund opened.", MUTED)
	if data.get("history_truncated", false):
		_text("Only the latest 512 observations are shown.", AMBER)
	_text("Signed exposure %s   |   NAV weight %s   |   Borrowed %s shares   |   Borrow APR %s" % [
			WorldRules.money(q["mv"]), TerminalRules.pct(q["weight"]), int(q["borrowed"]), TerminalRules.pct(q["borrow_rate"])])
	_text("Last observed event capacity: %d shares. This is scenario capacity, not realized trading volume or a promise of the next fill." % int(q.get("observed_event_volume", 0)), MUTED)
	_text("RELATED NEWS", AMBER)
	var found := false
	for n in data.get("news", []):
		if symbol in str(n.get("text", "")).to_upper():
			found = true
			_text("D%d %s  %s" % [int(n["day"]), n["phase"], n["text"]])
	if not found:
		_text("No published headlines mentioning this symbol.", MUTED)


func _portfolio() -> void:
	_text("PORTFOLIO / SIGNED EXPOSURE", AMBER, 20)
	var grid := _grid(["Symbol", "Shares", "Mark", "Market value", "NAV weight"])
	for q in data.get("quotes", []):
		if int(q["qty"]) == 0: continue
		for value in [q["sym"], str(int(q["qty"])), "%.4f" % float(q["mark"]), WorldRules.money(q["mv"]), TerminalRules.pct(q["weight"])]:
			grid.add_child(_label(value, RED if int(q["qty"]) < 0 else INK))
	var r: Dictionary = data.get("risk", {})
	_text("Longs %s   /   Shorts %s   /   NAV %s" % [WorldRules.money(r.get("long_mv", 0)),
			WorldRules.money(r.get("short_mv", 0)), WorldRules.money(r.get("nav", 0))])
	_text("Short market values and weights are negative. Weights are exposure, not allocation of spendable cash.", MUTED)


func _risk() -> void:
	_text("RISK / WHAT IF?", AMBER, 20)
	var r: Dictionary = data.get("risk", {})
	var controls: Dictionary = r.get("controls", {})
	if not controls.is_empty():
		_text("BROKER / EXECUTION CONTROLS: " + str(controls.get("status", "pending")).to_upper(),
				GREEN if controls.get("status") == "checked" else RED)
		_text(controls.get("scope", ""), MUTED, 12)
		var admin: Dictionary = controls.get("administrator", {})
		if not admin.is_empty():
			_text("LP capital is the last processed calendar close, adjusted for dealt flows; intraday P&L is allocated at close.", MUTED, 12)
			_text("LP / FEE CHECK: %s / %s calendar closes / %s dealt claims" % [
					str(admin.get("status", "pending")).to_upper(), admin.get("close_count", 0), admin.get("claim_count", 0)],
					GREEN if admin.get("status") == "checked" else RED)
			var series_grid := _grid(["Independent series", "Units", "Net capital", "Provision", "HWM"])
			for series in admin.get("series", []):
				for value in [series["series_id"], series["units"], WorldRules.money(series["net"]),
						WorldRules.money(series["provision"]), series["hwm"]]:
					series_grid.add_child(_label(str(value)))
			for claim in admin.get("claims", []):
				_text("%s / %s units %s / NAV per unit %s / claim %s / crystallized fee %s" % [
						claim["date"], claim["units"], claim["series_id"], claim["price"],
						WorldRules.money(claim["payable"]), WorldRules.money(claim["crystallized_fee"])], MUTED, 12)
		for issue in controls.get("breaks", []):
			_text("%s / %s / expected %s / recorded %s" % [issue["code"], issue["subject"],
					issue.get("expected", "--"), issue.get("actual", "--")], RED)
		var broker: Dictionary = controls.get("broker", {})
		_text("Broker activity: %s movements / %s dated fee lines / %s statement revisions" % [
				broker.get("activity_count", 0), broker.get("fee_line_count", 0), broker.get("statement_count", 0)], MUTED)
		for item in controls.get("settlements", []):
			if item["status"] == "pending" or not item["failed_days"].is_empty():
				_text("%s | %s %s %s | %s | due day %s | failed days %s" % [item["obligation"], item["kind"],
						item["qty"], item["sym"], str(item["status"]).to_upper(), item["due_day"],
						", ".join(item["failed_days"].map(func(d): return str(d))) if not item["failed_days"].is_empty() else "none"],
						AMBER if item["status"] == "pending" else MUTED, 12)
		for item in controls.get("statement_queue", []):
			_text("%s | %s | MP review | age %s calendar days | revision %s" % [
					item["id"], str(item["status"]).to_upper(), item["age_calendar_days"], item["revision"]],
					GREEN if item["status"] == "resolved" else AMBER)
			for evidence in item.get("history", []):
				_text("r%s / %s / reported %s / expected %s / %s" % [evidence["revision"], evidence["source"],
						WorldRules.money(evidence["balance"]), WorldRules.money(evidence["expected"]), evidence["reason"]], MUTED, 12)
				_text("As of day %s %s / published day %s %s" % [evidence["as_of"]["day"],
						evidence["as_of"]["phase"], evidence["available_at"]["day"], evidence["available_at"]["phase"]], MUTED, 12)
			if item.get("can_resolve", false) and data.get("role") == "mp":
				var review := Button.new()
				review.text = "Accept matching correction: " + str(item["id"])
				review.disabled = _stale
				review.pressed.connect(func(): _resolve_statement(item["id"], int(item["revision"])))
				_body.add_child(review)
	_text("NAV %s   /   Maintenance %s   /   Headroom %s" % [WorldRules.money(r.get("nav", 0)),
			WorldRules.money(r.get("maintenance_req", 0)), WorldRules.money(r.get("headroom", 0))])
	_text("Cash %s   /   Restricted collateral %s   /   Debt %s   /   Credit left %s" % [WorldRules.money(r.get("cash", 0)),
			WorldRules.money(r.get("restricted_collateral", 0)), WorldRules.money(r.get("debt", 0)), WorldRules.money(r.get("credit_left", 0))])
	var grid := _grid(["Hypothetical scenario", "Mark P&L", "Stressed NAV", "Headroom", "Margin"])
	for scenario in r.get("stresses", []):
		var color := RED if scenario["margin_breach"] else GREEN
		for value in [scenario["label"], WorldRules.money(scenario["pnl"]), WorldRules.money(scenario["nav"]),
				WorldRules.money(scenario["headroom"]), "BREACH" if scenario["margin_breach"] else "WITHIN"]:
			grid.add_child(_label(value, color))
	_text("Hypothetical static shocks to current positions, using current maintenance terms. No future prices, forced-liquidation costs, settlement or financing forecast. This analysis does not place orders.", MUTED)
	_liquidity_lab()


func _resolve_statement(statement_id: String, revision: int) -> void:
	var response: Dictionary = await _api.command({"type": "resolve_statement", "statement_id": statement_id,
			"revision": revision, "version": int(data.get("version", -1))})
	if response.get("ok", false):
		_status.text = "Correction reviewed. Original evidence remains in the break history."
		_fetch()


func _liquidity_lab() -> void:
	_text("LIQUIDITY / CURE LAB", AMBER, 20)
	_text("Compare liquidation paths under your assumptions. Percentages shock today's marks; volume repeats the last observed execution event.", MUTED)
	var form := HBoxContainer.new()
	_body.add_child(form)
	var fields := [["Long shock %", _lab_long, -90, 100], ["Short shock %", _lab_short, -90, 100],
			["Volume %", _lab_volume, 10, 200], ["Business events", _lab_horizon, 1, 10]]
	for i in range(fields.size()):
		var column := VBoxContainer.new()
		form.add_child(column)
		column.add_child(_label(fields[i][0], MUTED))
		var input := SpinBox.new()
		input.min_value = fields[i][2]
		input.max_value = fields[i][3]
		input.value = fields[i][1]
		input.custom_minimum_size.x = 150
		column.add_child(input)
		input.value_changed.connect(func(value):
			match i:
				0: _lab_long = value
				1: _lab_short = value
				2: _lab_volume = value
				3: _lab_horizon = value
		)
	var run := Button.new()
	run.text = "Computing..." if _lab_loading else "Compare hypothetical cure paths"
	run.disabled = _lab_loading or _stale
	run.pressed.connect(_run_lab)
	_body.add_child(run)
	if _lab.is_empty(): return
	var stale := int(_lab.get("version", -1)) != int(data.get("version", -2)) or _stale
	_text("Analysis from fund version %s%s" % [_lab.get("version", "?"), " / STALE: rerun before drafting" if stale else ""], AMBER)
	for comparison in _lab.get("comparisons", []):
		_text("%s / %s / execution cost %s / events to cure %s" % [
				"Lower cost per margin relief" if comparison["strategy"] == "cost" else "Sell longs first",
				str(comparison["status"]).replace("_", " "), WorldRules.money(comparison["execution_cost"]),
				str(comparison.get("events_to_cure", "--"))], AMBER)
		var assumptions: Dictionary = comparison.get("assumptions", {})
		_text("Evaluated shocks: longs %s, shorts %s; observed volume x%s; horizon %s. %s" % [
				TerminalRules.pct(assumptions.get("long_shock")), TerminalRules.pct(assumptions.get("short_shock")),
				assumptions.get("volume_scale", "?"), assumptions.get("horizon", "?"), assumptions.get("method", "")], MUTED, 12)
		var path := _grid(["Event", "NAV", "Headroom", "Credit left", "Settlements", "Collateral"])
		for step in comparison.get("path", []):
			for value in [str(step["event"]), WorldRules.money(step["nav"]), WorldRules.money(step["headroom"]),
					WorldRules.money(step["credit_left"]), str(step["pending_settlements"]),
					"FUNDED" if step["collateral_funded"] else "SHORTFALL"]:
				path.add_child(_label(value))
		var orders: Array = comparison.get("draft", [])
		if not orders.is_empty():
			var review := Button.new()
			review.text = "Review first-event orders at trading desk"
			review.disabled = stale
			review.pressed.connect(func():
				close()
				cure_draft_requested.emit(orders.duplicate(true), int(_lab["version"])))
			_body.add_child(review)
	_text("Cure paths are hypothetical and may breach the live mandate. Review every leg; a partner must approve the exact package before live execution.", MUTED)


func _run_lab() -> void:
	if _lab_loading: return
	_lab_loading = true
	_render()
	var result: Dictionary = await _api.liquidity({"version": int(data.get("version", -1)),
			"long_shock": str(_lab_long / 100.0), "short_shock": str(_lab_short / 100.0),
			"volume_scale": str(_lab_volume / 100.0), "horizon": int(_lab_horizon)})
	_lab_loading = false
	if result.get("ok", false):
		_lab = result["data"]
		_status.text = ""
	else:
		_status.text = str(result.get("data", {}).get("detail", "Liquidity request failed; refresh and retry.")) if result.get("data") is Dictionary else "Liquidity request failed; refresh and retry."
	if is_open(): _render()


func _news() -> void:
	_text("NEWS / PUBLISHED FEED", AMBER, 20)
	var news: Array = data.get("news", []).duplicate()
	news.reverse()
	if news.is_empty(): _text("No published news yet.", MUTED)
	for n in news:
		_text("D%d %s / %s   %s / %s" % [int(n["day"]), n["date"], n["phase"], str(n["kind"]).to_upper(),
				str(n.get("visibility", "shared")).to_upper()], AMBER)
		_text(n["text"], RED if n["kind"] == "alert" else INK)


func _orders() -> void:
	_text("ORDER BLOTTER", AMBER, 20)
	var grid := _grid(["Symbol", "Side", "Requested", "Filled", "Remaining", "Status", "Origin"])
	var orders: Array = data.get("orders", []).duplicate()
	orders.reverse()
	if orders.is_empty(): _text("No accepted orders. Open the trading desk to draft a ticket or joint package.", MUTED)
	for order in orders:
		for value in [order["sym"], order["side"], str(int(order["qty"])), str(int(order["filled"])), str(int(order["remaining"])),
				order["status"], "Partner" if order["forced"] == null else "Broker / " + str(order["forced"])]:
			grid.add_child(_label(value))
		for fill in order.get("fills", []):
			_text("%s  %s" % [order["order_id"], str(fill)], MUTED, 12)


func _street() -> void:
	_text("STREET / RIVAL FUNDS", AMBER, 20)
	var grid := _grid(["Rank", "Fund", "Style", "Status", "Return bps"])
	for row in WorldRules.league_rows(data):
		for value in [str(row["rank"]), "Your fund" if row["is_you"] else row.get("name", row["id"]),
				str(row.get("style", "")).replace("_", " "), row.get("status", ""), TerminalRules.bps(row["return_bps"])]:
			grid.add_child(_label(value, AMBER if row["is_you"] else INK))
	_text("Public performance since the warm start. Rival holdings and unrevealed research are private.", MUTED)


func _help() -> void:
	_text("FUNCTION DIRECTORY", AMBER, 20)
	for row in ["MON       Market monitor; select a symbol for its chart", "BRIN GP   Observed price history for BRIN (any known symbol works)",
			"PORT      Signed holdings and NAV weights", "RISK      Static stress and liquidity/cure scenarios",
			"NEWS      Shared notices and research visible to your seat", "ORDERS    Accepted orders and fill status",
			"STREET    Rival-fund league table", "REPLAY    Completed-run causal comparisons",
			"RESEARCH  Regime question, published prior/posterior and your thesis (generated markets)"]:
		_text(row)
	_text("F1-F10 switch functions. Enter selects a function. Escape returns to the office. T opens the terminal from the world.", MUTED)
	_text("Use Trading desk to submit a ticket or propose a package. Your partner's signature and all risk limits still apply.", MUTED)


func _research_page(refocus := false) -> void:
	_text("RESEARCH / REGIME QUESTION", AMBER, 20)
	var regime: Variant = data.get("regime")
	if not regime is Dictionary:
		_text("No live research question. Generated markets ask one once the first Street activity print is published.", MUTED)
		return
	var q: Dictionary = regime
	_text("%s: was the Street calm or stressed in the period of day %d?" % [q["question"], int(q["period_day"])])
	var grid := _grid(["", "Calm", "Stressed"])
	for row in [["Published prior (regime chain alone)", q["prior"]], ["Posterior from published prints", q["posterior"]]]:
		grid.add_child(_label(row[0], MUTED))
		grid.add_child(_label(str(row[1]["calm"])))
		grid.add_child(_label(str(row[1]["stressed"])))
	_text("%s Evidence: %d published print(s)." % [q.get("method", ""), int(q.get("evidence", 0))], MUTED, 12)
	_text("YOUR THESIS", AMBER)
	var form := HBoxContainer.new()
	form.add_theme_constant_override("separation", 12)
	_body.add_child(form)
	form.add_child(_label("Calm probability (0 to 1, up to 6 dp)", MUTED))
	var calm := LineEdit.new()
	calm.name = "ThesisCalm"
	calm.text = _thesis_calm
	calm.placeholder_text = str(q["posterior"]["calm"])
	calm.custom_minimum_size.x = 140
	form.add_child(calm)
	var stressed := _label("")
	form.add_child(stressed)
	var send := Button.new()
	send.name = "ThesisSend"
	form.add_child(send)
	var update := func(text: String) -> void:
		_thesis_calm = text
		var f := TerminalRules.thesis_forecast(text)
		stressed.text = "Stressed " + (f["stressed"] if not f.is_empty() else "--")
		send.disabled = f.is_empty() or _thesis_sending or _stale or data.get("finished", false)
		send.text = "Season over: theses are closed" if data.get("finished", false) else (
				"Sending..." if _thesis_sending else "Record thesis for " + str(q["question"]))
	update.call(_thesis_calm)
	calm.text_changed.connect(update)
	calm.text_submitted.connect(func(_t): if not send.disabled: _submit_thesis(str(q["question"])))
	send.pressed.connect(func(): _submit_thesis(str(q["question"])))
	if refocus:
		calm.call_deferred("grab_focus")
	_text("Only the newest period can be forecast. Theses are Brier-scored in the debrief beside P&L; they never move money, NAV or rank.", MUTED, 12)


## One submission = one Api.command call = one idempotency key; the server validates question and sum.
func _submit_thesis(question: String) -> void:
	var forecast := TerminalRules.thesis_forecast(_thesis_calm)
	if forecast.is_empty() or _thesis_sending:
		return
	_thesis_sending = true
	_render()
	var response: Dictionary = await _api.command({"type": "thesis", "question": question, "forecast": forecast})
	_thesis_sending = false
	if response.get("ok", false):
		_status.text = "Thesis recorded for %s: calm %s / stressed %s." % [question, forecast["calm"], forecast["stressed"]]
	if is_open(): _render()
	_fetch()
