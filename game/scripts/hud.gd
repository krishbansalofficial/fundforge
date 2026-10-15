class_name Hud
extends CanvasLayer
## Overlay UI: clock and speed controls, fund vitals, desk feed, location terminals and the debrief.

var role := "pm"
var view: Dictionary = {}
var caption := ""  # when set (the --demo trailer), shown instead of the clock's pause reason

var _clock: Label
var _reason: Label
var _speed_buttons := {}
var _stats: Label
var _connection: Label
var _headroom: ProgressBar
var _feed: RichTextLabel
var _prompt: Label
var _toast: Label
var _panel: PanelContainer
var _panel_title: Label
var _panel_body: VBoxContainer
var _open_location := ""
var _debrief: PanelContainer
var _run_record_box: VBoxContainer
var _run_record_loading := false
var _run_record_api: Node  # injectable transport for asynchronous recovery tests
var terminal: ForgeTerminal
var sfx: Sfx
var _mute_button: Button
var music: Music
var _music_button: Button
var _cure_draft: Array = []
var _cure_version := -1
var _cure_sending := false
const LEDGER_PAGE := 15
var _ledger_entity := ""  # journal shown in the back office, "" for none
var _ledger_offset := 0  # newest entries skipped (paging back)
var _ledgers := {}  # entity -> WorldRules.merge_ledger cache plus the room/version it was fetched at
var _ledger_loading := false


func _ready() -> void:
	var top := PanelContainer.new()
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	top.add_theme_stylebox_override("panel", _style(Color(0.06, 0.09, 0.14, 0.92)))
	add_child(top)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	top.add_child(row)
	var title := Label.new()
	title.text = "  FundForge"
	title.add_theme_font_size_override("font_size", 20)
	row.add_child(title)
	var terminal_button := Button.new()
	terminal_button.text = "Terminal [T]"
	terminal_button.pressed.connect(open_terminal)
	row.add_child(terminal_button)
	sfx = Sfx.new()
	add_child(sfx)
	_mute_button = Button.new()
	_mute_button.pressed.connect(toggle_mute)
	row.add_child(_mute_button)
	music = Music.new()
	add_child(music)
	_music_button = Button.new()
	_music_button.pressed.connect(cycle_music)
	row.add_child(_music_button)
	_show_mute()
	music.refresh(sfx.muted)
	_clock = Label.new()
	_clock.add_theme_font_size_override("font_size", 18)
	_clock.custom_minimum_size = Vector2(330, 0)
	row.add_child(_clock)
	for spec in [["Pause", 0], ["1x", 1], ["2x", 2], ["4x", 4]]:
		var b := Button.new()
		b.text = spec[0]
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_ALL
		var speed: int = spec[1]
		b.pressed.connect(func(): _set_speed(speed))
		row.add_child(b)
		_speed_buttons[speed] = b
	_reason = Label.new()
	_reason.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_reason.clip_text = true
	_reason.add_theme_color_override("font_color", Color("#f0c27a"))
	row.add_child(_reason)

	var side := PanelContainer.new()
	side.add_theme_stylebox_override("panel", _style(Color(0.06, 0.09, 0.14, 0.85)))
	side.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	side.position = Vector2(-330, 52)
	side.custom_minimum_size = Vector2(320, 0)
	add_child(side)
	var sv := VBoxContainer.new()
	side.add_child(sv)
	_stats = Label.new()
	_stats.add_theme_font_size_override("font_size", 15)
	sv.add_child(_stats)
	_connection = Label.new()
	_connection.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_connection.add_theme_color_override("font_color", Color("#f0c27a"))
	sv.add_child(_connection)
	var hl := Label.new()
	hl.text = "Maintenance headroom"
	sv.add_child(hl)
	_headroom = ProgressBar.new()
	_headroom.max_value = 1.6
	_headroom.show_percentage = false
	_headroom.custom_minimum_size = Vector2(0, 14)
	sv.add_child(_headroom)

	_feed = RichTextLabel.new()
	_feed.bbcode_enabled = true
	_feed.scroll_following = true
	_feed.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	_feed.position = Vector2(12, -230)
	_feed.size = Vector2(620, 218)
	_feed.add_theme_stylebox_override("normal", _style(Color(0.06, 0.09, 0.14, 0.8)))
	add_child(_feed)

	_prompt = Label.new()
	_prompt.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	_prompt.position = Vector2(-160, -60)
	_prompt.add_theme_font_size_override("font_size", 18)
	_prompt.add_theme_color_override("font_outline_color", Color.BLACK)
	_prompt.add_theme_constant_override("outline_size", 5)
	add_child(_prompt)

	_toast = Label.new()
	_toast.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	_toast.position = Vector2(-300, 60)
	_toast.size = Vector2(600, 30)
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast.add_theme_color_override("font_color", Color("#ff8a7a"))
	add_child(_toast)

	_panel = PanelContainer.new()
	_panel.add_theme_stylebox_override("panel", _style(Color(0.93, 0.95, 0.96, 0.98), Color("#16263a")))
	_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_panel.custom_minimum_size = Vector2(620, 420)
	_panel.position = Vector2(-310, -230)
	_panel.visible = false
	add_child(_panel)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 8)
	_panel.add_child(pv)
	var head := HBoxContainer.new()
	pv.add_child(head)
	_panel_title = Label.new()
	_panel_title.add_theme_font_size_override("font_size", 22)
	_panel_title.add_theme_color_override("font_color", Color("#16263a"))
	_panel_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(_panel_title)
	var close := Button.new()
	close.text = "Close (Esc)"
	close.pressed.connect(close_panel)
	head.add_child(close)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(600, 360)
	pv.add_child(scroll)
	_panel_body = VBoxContainer.new()
	_panel_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_panel_body)

	Api.command_failed.connect(func(msg): _show_toast(msg))
	terminal = ForgeTerminal.new()
	add_child(terminal)
	terminal.trading_requested.connect(func(): open_panel("trading"))
	terminal.cure_draft_requested.connect(func(orders, source_version):
		_cure_draft = orders
		_cure_version = source_version
		open_panel("trading"))


func _style(bg: Color, border := Color(0, 0, 0, 0)) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.set_content_margin_all(10)
	s.set_corner_radius_all(4)
	if border.a > 0:
		s.border_color = border
		s.set_border_width_all(2)
	return s


func _unhandled_input(event: InputEvent) -> void:
	if terminal.is_open():
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_T:
		open_terminal()
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("ui_cancel") and _panel.visible:
		close_panel()
	elif event is InputEventKey and event.pressed and event.keycode == KEY_SPACE and not _panel.visible:
		var paused: bool = view.get("clock_state", {}).get("paused", true)
		_set_speed(1 if paused else 0)
	elif event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_M:
		toggle_mute()
	elif event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_N:
		cycle_music()
	elif event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_L:
		if _open_location == "street":
			close_panel()
		else:
			open_panel("street")


func _show_toast(msg: String) -> void:
	_toast.text = msg
	var tw := create_tween()
	_toast.modulate.a = 1.0
	tw.tween_interval(3.0)
	tw.tween_property(_toast, "modulate:a", 0.0, 0.6)


func _set_speed(speed: int) -> void:
	if speed == 0:
		Api.command({"type": "pause"})
	else:
		Api.command({"type": "set_speed", "speed": speed})


# ---------------- per-frame and per-view updates ----------------

func _process(_delta: float) -> void:
	show_poll_state(Api.poll_state())


func show_poll_state(state: Dictionary) -> void:
	if not is_instance_valid(_connection):
		return
	if state.get("stale", false):
		_connection.text = "Connection interrupted / data stale\nLast server contact %ds ago. NAV and clock retained." % int(state.get("age_seconds", 0)) if state.get("has_view", false) else "Connection interrupted / waiting for first room view."
	else:
		_connection.text = ""


func update_clock(hour: float) -> void:
	var c: Dictionary = view.get("clock", {})
	if c.is_empty():
		return
	var d := Time.get_datetime_dict_from_unix_time(Time.get_unix_time_from_datetime_string(c.get("date", "2026-01-20") + "T12:00:00"))
	var days := ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
	_clock.text = "Day %d   %s %s   %s" % [c.get("day", 0), days[d.get("weekday", 0)], c.get("date", ""),
			"Season complete" if c.get("finished", false) else WorldRules.format_hour(hour)]


func set_near(location: String) -> void:
	_prompt.text = "" if location == "" else "[E] or Enter: open %s" % WorldRules.LOCATIONS[location]["label"]


func apply_view(v: Dictionary) -> void:
	view = v
	role = v.get("role", role)
	terminal.set_view(v)
	var cs: Dictionary = v.get("clock_state", {})
	var speed := 0 if cs.get("paused", true) else int(cs.get("speed", 0))
	for s in _speed_buttons:
		_speed_buttons[s].button_pressed = (s == speed)
	_reason.text = str(cs.get("reason", "")) if cs.get("paused", true) and cs.get("reason") != null else ""
	if caption != "":
		_reason.text = caption
	var f: Dictionary = v.get("fund", {})
	var firm: Dictionary = v.get("firm", {})
	_stats.text = "NAV  %s\n%s\nGross / net  %s%% / %s%%\nCash  %s   Debt  %s\nCredit left  %s\nFirm cash (not fund money)  %s" % [
		WorldRules.money(f.get("nav", 0)), CertificationRules.summary(v), _pct(f.get("gross")), _pct(f.get("net")),
		WorldRules.money(f.get("cash", 0)), WorldRules.money(f.get("debt", 0)),
		WorldRules.money(f.get("credit_left", 0)), WorldRules.money(firm.get("cash", 0))]
	var ratio := WorldRules.headroom_ratio(f)
	_headroom.value = minf(ratio, 1.6)
	_headroom.modulate = Color("#e05a4a") if ratio < 1.0 else (Color("#e0a14a") if ratio < 1.05 else Color("#6cbf8f"))
	var items: Array = []
	for n in v.get("notices", []):
		var col: String = {"alert": "#ff7a6a", "market": "#f0c27a", "research": "#8fd6a8"}.get(n.get("kind", ""), "#dfe7ef")
		items.append([n.get("day", 0), "[color=%s]%s[/color]" % [col, n.get("text", "")]])
	var names: Dictionary = v.get("names", {})
	for m in v.get("chat", []):
		items.append([m.get("day", 0), "[color=#9fd0ff][b]%s:[/b] %s[/color]" % [names.get(m.get("role", ""), m.get("role", "")), m.get("text", "")]])
	items.sort_custom(func(a, b): return a[0] < b[0])
	var lines := ""
	for i in range(maxi(0, items.size() - 9), items.size()):
		lines += "[color=#8aa0b8]Day %d[/color]  %s\n" % [items[i][0], items[i][1]]
	_feed.text = lines
	if _panel.visible:
		_render_panel(_open_location)
	if v.get("outcome") != null:
		_show_debrief(v["outcome"])


func _pct(s: Variant) -> String:
	return "—" if s == null else "%.1f" % (float(str(s)) * 100.0)


# ---------------- location terminals ----------------

func open_panel(location: String) -> void:
	if terminal.is_open():
		return
	_open_location = location
	_panel.visible = true
	_render_panel(location)


func toggle_mute() -> void:
	sfx.set_muted(not sfx.muted)
	music.refresh(sfx.muted)
	_show_mute()


func cycle_music() -> void:
	music.cycle(sfx.muted)
	_show_mute()


func _show_mute() -> void:
	_mute_button.text = "Sound off [M]" if sfx.muted else "Sound on [M]"
	_music_button.text = "Music %s [N]%s" % [Music.LEVEL_NAMES[music.level], " (muted)" if sfx.muted and music.level > 0 else ""]


func close_panel() -> void:
	_panel.visible = false
	_open_location = ""


func open_terminal() -> void:
	close_panel()
	terminal.open()


func _clear() -> void:
	for c in _panel_body.get_children():
		c.queue_free()


func _text(t: String, size := 15, color := Color("#16263a")) -> Label:
	var l := Label.new()
	l.text = t
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	_panel_body.add_child(l)
	return l


func _button(t: String, cb: Callable, enabled := true) -> Button:
	var b := Button.new()
	b.text = t
	b.disabled = not enabled
	b.pressed.connect(cb)
	_panel_body.add_child(b)
	return b


func _render_panel(location: String) -> void:
	_clear()
	_panel_title.text = WorldRules.LOCATIONS[location]["label"]
	match location:
		"trading": _trading()
		"committee": _committee()
		"risk": _risk()
		"research": _research()
		"backoffice": _backoffice()
		"lp": _lp()
		"broker": _broker()
		"street": _street()


func _trading() -> void:
	_button("Open Forge Terminal: quotes, charts, risk and news [T]", open_terminal)
	if not _cure_draft.is_empty():
		_text("HYPOTHETICAL CURE DRAFT / review before proposing", 18)
		for leg in _cure_draft:
			_text("%s %s shares of %s" % [leg["side"], leg["qty"], leg["sym"]])
		_text("Market orders at the next live event. Simulated prices are not guaranteed; live mandate and partner approval still apply.", 12)
		if _cure_version != int(view.get("version", -1)):
			_text("Fund changed since analysis. Rerun the liquidity lab before proposing.")
		elif not _cure_sending:
			_button("Propose this cure package to partner", _propose_cure)
		_button("Discard cure draft", func(): _cure_draft = []; open_panel("trading"))
	var rows := ""
	for p in view.get("positions", []):
		if int(p.get("qty", 0)) != 0:
			rows += "%-5s %9s sh  @ %7.2f   %s\n" % [p["sym"], str(p["qty"]), float(p["mark"]), WorldRules.money(p["mv"])]
	_text(rows, 14)
	var form := HBoxContainer.new()
	_panel_body.add_child(form)
	var side := OptionButton.new()
	for s in ["SELL", "COVER", "BUY", "SHORT"]:
		side.add_item(s)
	form.add_child(side)
	var sym := OptionButton.new()
	for s in view.get("marks", {}).keys():
		sym.add_item(s)
	form.add_child(sym)
	var qty := SpinBox.new()
	qty.max_value = 1_000_000
	qty.step = 100
	qty.custom_minimum_size = Vector2(130, 0)
	form.add_child(qty)
	var order := func() -> Dictionary:
		return {"order_id": "%s-%s" % [role, Api.new_key().substr(0, 8)], "sym": sym.get_item_text(sym.selected),
				"side": side.get_item_text(side.selected), "qty": int(qty.value)}
	if role == "pm":
		_button("Send ticket (up to 5% of NAV alone)", func(): Api.command({"type": "ticket"}.merged(order.call())))
	_button("Propose package to partner", func():
		Api.command({"type": "propose", "package_id": "pkg-" + Api.new_key().substr(0, 8), "orders": [order.call()]}))
	_text("Orders fill at the next execution window with market impact, never at a price you have already seen.", 12, Color("#4d5e72"))


func _propose_cure() -> void:
	if _cure_sending or _cure_draft.is_empty(): return
	_cure_sending = true
	var orders := _cure_draft.duplicate(true)
	for leg in orders:
		leg["order_id"] = "cure-" + Api.new_key()
	var result: Dictionary = await Api.command({"type": "propose", "package_id": "cure-" + Api.new_key(),
			"source_version": _cure_version, "orders": orders})
	_cure_sending = false
	if result.get("ok", false):
		_cure_draft = []
		open_panel("committee")


func _committee() -> void:
	var other := "mp" if role == "pm" else "pm"
	var any := false
	for p in view.get("packages", []):
		any = true
		var desc := LpRules.gate_terms_text(p.get("terms", {})) if p.get("kind") == "gate" else \
				", ".join(p["orders"].map(func(o): return "%s %s %s" % [o["side"], o["qty"], o["sym"]]))
		_text("%s  proposed by %s  [%s]  hash %s" % [desc, view.get("names", {}).get(p["proposer"], p["proposer"]),
				str(p["status"]).to_lower().replace("_", " "), str(p["digest"]).substr(0, 10)], 14)
		if p["status"] == "PENDING_APPROVAL" and p["proposer"] == other:
			var digest: String = p["digest"]
			var pid: String = p["package_id"]
			_button("Countersign this exact package", func(): Api.command({"type": "sign", "package_id": pid, "digest": digest}))
	if not any:
		_text("No packages on the table. Propose one from the trading floor.", 14, Color("#4d5e72"))
	_text("Skip ahead together: when both partners are ready, time jumps to the next window.", 12, Color("#4d5e72"))
	var ready: Array = view.get("ready", [])
	_button("Waiting for partner" if role in ready else "I'm ready to move on",
			func(): Api.command({"type": "ready", "version": int(view.get("version", 0))}), not role in ready)
	_button("Skip quiet windows (stops at the next notice, incident or open order)",
			func(): Api.command({"type": "ready", "version": int(view.get("version", 0)), "skip": true}), not role in ready)


func _risk() -> void:
	var f: Dictionary = view.get("fund", {})
	_text("Maintenance requirement %s against NAV %s" % [WorldRules.money(f.get("maintenance_req")), WorldRules.money(f.get("nav"))])
	if f.get("margin_call") != null:
		_text("MARGIN CALL: deficit %s. Cure at the next execution or the broker liquidates." % WorldRules.money(f["margin_call"]), 16, Color("#a9281f"))
	_text("Treasury reserve %s (cash kept back from debt repayment)" % WorldRules.money(f.get("reserve")))
	if role == "mp":
		var row := HBoxContainer.new()
		_panel_body.add_child(row)
		var amount := LineEdit.new()
		amount.placeholder_text = "Reserve in dollars"
		amount.custom_minimum_size = Vector2(200, 0)
		row.add_child(amount)
		var b := Button.new()
		b.text = "Set reserve"
		b.pressed.connect(func(): Api.command({"type": "set_reserve", "amount": amount.text.strip_edges()}))
		row.add_child(b)
	else:
		_text("Only the managing partner sets the reserve.", 12, Color("#4d5e72"))


func _research() -> void:
	var r: Dictionary = view.get("research", {})
	var used: Array = r.get("used", []).map(func(u): return u["topic"])
	_text("Assignments left: %d. Findings arrive at the next market open." % (int(r.get("budget", 0)) - used.size()))
	var attention: Dictionary = view.get("attention", {})
	_text("One assignment per decision window. Findings stay private until you share them.", 12)
	if attention.get("committed", false):
		_text("Your attention is committed for this window. Orders, signatures and mandatory notices remain available.", 12)
	var names := {"borrow": "BRIN borrow availability", "debt_schedule": "BRIN debt schedule", "demand_survey": "BRIN demand survey",
			"crowding": "Prime broker crowding report"}
	for t in r.get("topics", []):
		var topic: String = t
		var location: String = r.get("assignments", {}).get(topic, {}).get("location", "research")
		_button(names.get(topic, topic) + " / " + location + ("  (assigned)" if topic in used else ""),
				func(): Api.command({"type": "visit", "location": location, "assignment": topic}),
				not topic in used and not attention.get("committed", false))
	for evidence in r.get("evidence", []):
		var topic: String = evidence.get("refs", {}).get("topic", "")
		var shared: bool = topic in r.get("shared", [])
		_text(("SHARED / " if shared else "PRIVATE / ") + topic.replace("_", " "), 16)
		_text(evidence["text"], 14)
		if evidence.get("refs", {}).get("owner") == role and not shared:
			_button("Share this evidence with partner", func(): Api.command({"type": "share_research", "topic": topic}))


func _backoffice() -> void:
	var firm: Dictionary = view.get("firm", {})
	_text("The management company is a separate entity. Investor money can never pay its bills.", 13, Color("#4d5e72"))
	_text("Cash %s\nFees receivable %s (not spendable until the fund pays)\nPayroll owed %s" % [
		WorldRules.money(firm.get("cash")), WorldRules.money(firm.get("fee_receivable")), WorldRules.money(firm.get("payroll_payable"))])
	_button("Show the firm's journal", func(): _show_ledger("firm"))
	_button("Show the fund's journal", func(): _show_ledger("fund"))
	_button("Verify the books (replay everything from the log)", _verify)
	if _ledger_entity != "":
		_render_ledger()


func _show_ledger(entity: String) -> void:
	_ledger_entity = entity
	_ledger_offset = 0
	_render_panel(_open_location)


## Draws the cached journal page and, when the room has moved on, fetches only the new entries.
func _render_ledger() -> void:
	var cache: Dictionary = _ledgers.get(_ledger_entity, {})
	var stale: bool = cache.get("room") != Api.room_id or int(cache.get("version", -1)) != int(view.get("version", -2))
	if stale and not _ledger_loading:
		_refresh_ledger(_ledger_entity, cache)
	if cache.get("room") != Api.room_id:
		_text("Loading the %s journal..." % _ledger_entity, 12, Color("#4d5e72"))
		return
	var shown := WorldRules.ledger_window(cache, _ledger_offset, LEDGER_PAGE)
	var total := int(cache.get("next", 0))
	var lines := "%s journal (latest first), hash %s\n" % [_ledger_entity.capitalize(), str(cache.get("digest", "")).substr(0, 16)]
	if not shown.is_empty():
		lines += "entries %d-%d of %d\n" % [total - _ledger_offset - shown.size() + 1, total - _ledger_offset, total]
	for e in shown:
		lines += "%s  %s\n" % [e["date"], e["memo"]]
		for p in e["postings"]:
			lines += "      %-26s %14s\n" % [p[0], p[1]]
	_text(lines, 12)
	var cached: int = cache.get("entries", []).size()
	_button("Newer entries", func(): _page_ledger(-LEDGER_PAGE), _ledger_offset > 0)
	_button("Older entries", func(): _page_ledger(LEDGER_PAGE), _ledger_offset + LEDGER_PAGE < cached)


func _page_ledger(delta: int) -> void:
	_ledger_offset = maxi(0, _ledger_offset + delta)
	_render_panel(_open_location)


func _refresh_ledger(entity: String, cache: Dictionary) -> void:
	_ledger_loading = true
	var room := Api.room_id
	var version := int(view.get("version", -1))
	var after: int = int(cache.get("next", -1)) if cache.get("room") == room else -1
	var res: Dictionary = await Api.ledger(entity, after)
	_ledger_loading = false
	if not res["ok"] or not res["data"] is Dictionary or room != Api.room_id:
		return
	var merged := WorldRules.merge_ledger(cache if after >= 0 else {}, res["data"], after)
	merged["room"] = room
	merged["version"] = version
	if after >= 0 and _ledger_offset > 0:  # keep the same entries in view while new ones arrive on top
		_ledger_offset += int(merged["next"]) - after
	elif after < 0:
		_ledger_offset = 0
	_ledgers[entity] = merged
	if _panel.visible and entity == _ledger_entity:
		_render_panel(_open_location)


func _verify() -> void:
	var res: Dictionary = await Api.verify()
	if res["ok"] and res["data"].get("ok", false):
		_text("Verified: %d commands replayed; journal %s; chain head %s" % [res["data"]["version"],
				str(res["data"]["journal_digest"]).substr(0, 12), str(res["data"]["chain_head"]).substr(0, 12)], 13, Color("#2d6e4a"))
	elif res["ok"]:
		_text("VERIFY FAILED: " + str(res["data"].get("error")), 13, Color("#a9281f"))


func _lp() -> void:
	for s in view.get("series", []):
		_text("%s   units %s   NAV/unit %s   HWM %s   provision %s" % [s["id"], s["units"], s["nav_per_unit"], s["hwm"],
				WorldRules.money(s["provision"])], 14)
	var lp_notices := LpRules.notices(view)
	if view.get("investors") == null and lp_notices.is_empty():
		_text("Tactical has noticed a 10,000-unit redemption, dealt at the day 20 close and paid day 21.", 13, Color("#4d5e72"))
	if view.get("investors") is Dictionary:
		_lp_inbox()
	elif role == "pm":
		_text("LP relationships belong to the managing partner. Formal notices and gate elections are shared.", 12, Color("#4d5e72"))
	for n in lp_notices:
		_text("Day %d  %s" % [int(n.get("day", 0)), n.get("text", "")], 12)


## The MP's LP inbox (generated rooms): bands, requests, contact and gate proposal. Reads only this view.
func _lp_inbox() -> void:
	_text("LP INBOX / bands from the last certified review", 16)
	var lps: Array = view["investors"].get("lps", [])
	var lines := LpRules.rows(view)
	for i in lps.size():
		var lp: Dictionary = lps[i]
		_text(lines[i], 14)
		var reason := LpRules.contact_reason(view, lp)
		var lp_id: String = lp["id"]
		_button("Contact %s" % lp_id if reason == "" else "Contact %s  (%s)" % [lp_id, reason],
				func(): Api.command({"type": "contact_lp", "lp": lp_id}), reason == "")
	var terms := LpRules.pending_gate_terms(view)
	if not terms.is_empty() and not LpRules.has_open_gate(view):
		_text(LpRules.gate_terms_text(terms), 13, Color("#7a4a12"))
		_button("Propose gate to partner (they must countersign in the committee room)",
				func(): Api.command({"type": "propose_gate", "package_id": "gate-" + Api.new_key().substr(0, 8)}))
	if view["investors"].get("gate_elected", false):
		_text("A gate is elected for the next dealing close.", 13, Color("#7a4a12"))


func _broker() -> void:
	var r: Dictionary = view.get("recall", {})
	if int(r.get("open", 0)) > 0:
		_text("Recall open: %d BRIN must be covered by day 15, 15:00." % int(r["open"]), 16, Color("#a9281f"))
	elif r.get("resolved_by") != null:
		_text("Recall resolved by " + str(r["resolved_by"]), 15, Color("#2d6e4a"))
	for p in view.get("positions", []):
		if int(p.get("borrowed", 0)) > 0:
			_text("%s borrowed %d shares" % [p["sym"], int(p["borrowed"])], 14)
	if r.get("offer_visible", false) and not r.get("replacement_accepted", false):
		_button("Accept replacement borrow: 1,250 BRIN at 40%", func(): Api.command({"type": "accept_replacement"}), role == "mp")
		if role != "mp":
			_text("Only the managing partner can accept borrow terms.", 12, Color("#4d5e72"))
	elif not r.get("offer_visible", false):
		_text("Ask for a desk check in the research library to learn about replacement borrow.", 12, Color("#4d5e72"))


func _street() -> void:
	var rows := WorldRules.league_rows(view)
	if rows.is_empty():
		_text("No league table from the server yet.", 14, Color("#4d5e72"))
		return
	var grid := GridContainer.new()
	grid.columns = 5
	grid.add_theme_constant_override("h_separation", 18)
	_panel_body.add_child(grid)
	for h in ["#", "Fund", "Style", "Status", "Return (bps)"]:
		grid.add_child(_cell(h, Color("#4d5e72")))
	for r in rows:
		var you: bool = r["is_you"]
		var ink := Color("#1d5fa8") if you else Color("#16263a")
		var bps: int = r["return_bps"]
		grid.add_child(_cell(str(r["rank"]), ink, you))
		grid.add_child(_cell("Your fund" if you else str(r.get("name", r.get("id", ""))), ink, you))
		grid.add_child(_cell(str(r.get("style", "")).replace("_", " "), ink, you))
		var status := str(r.get("status", ""))
		grid.add_child(_cell(status, {"deleveraging": Color("#b0700a"), "liquidating": Color("#a9281f"), "closed": Color("#6a6a6a")}.get(status, ink), you))
		grid.add_child(_cell("%+d" % bps, Color("#2d6e4a") if bps >= 0 else Color("#a9281f"), you))
	_text("Returns since the warm start, public marks. Press L to toggle.", 12, Color("#4d5e72"))


func _cell(t: String, color: Color, bold := false) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", 16 if bold else 15)
	l.add_theme_color_override("font_color", color)
	if bold:
		l.add_theme_color_override("font_outline_color", color)
		l.add_theme_constant_override("outline_size", 1)
	return l


# ---------------- debrief ----------------

func _show_debrief(o: Dictionary) -> void:
	if _debrief != null:
		return
	_debrief = PanelContainer.new()
	_debrief.add_theme_stylebox_override("panel", _style(Color(0.06, 0.09, 0.14, 0.97), Color("#f0c27a")))
	_debrief.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_debrief.custom_minimum_size = Vector2(720, 700)
	_debrief.position = Vector2(-360, -350)
	add_child(_debrief)
	var scroll := ScrollContainer.new()  # the outcome facts and research block outgrow a 900 px screen
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_debrief.add_child(scroll)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(v)
	var big := Label.new()
	big.text = CardRules.LABELS.get(o["label"], o["label"])
	big.add_theme_font_size_override("font_size", 48)
	big.add_theme_color_override("font_color", {"WIN": Color("#6cbf8f"), "SURVIVAL": Color("#e0a14a")}.get(o["label"], Color("#ec6d62")))
	v.add_child(big)
	var body := Label.new()
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.text = "%s\n\nScore %s bps (fund %s bps vs passive book %s bps, minus forced-action penalties)\nEnding NAV %s\nTactical redemption paid %s\nRecall resolved by %s\nForced actions: %s\nUnpaid: %s\nReplay proof: tape %s, journal %s" % [
		CardRules.market_text(o.get("variant"), o.get("scenario")), o.get("score", "?"), o.get("fund_return_bps", "?"), o.get("benchmark_return_bps", "?"),
		WorldRules.money(o["nav"]), WorldRules.money(o["redemption_paid"]), str(o.get("recall_resolved_by", "unresolved")),
		"none" if o["forced"].is_empty() else "; ".join(o["forced"]), "none" if o["unpaid"].is_empty() else "; ".join(o["unpaid"]),
		str(o["tape_digest"]).substr(0, 12), str(o["journal_digest"]).substr(0, 12)]
	if o.get("rank") != null and o.get("funds") != null:
		body.text = "You finished #%d of %d funds

" % [int(o["rank"]), int(o["funds"])] + body.text
	var facts := CardRules.facts(o)
	if not facts.is_empty():
		body.text += "\n" + "\n".join(facts)
	v.add_child(body)
	var save := Button.new()
	save.name = "SaveCard"
	save.text = "Save ending card"
	var saved := Label.new()
	saved.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	save.pressed.connect(func():
		save.disabled = true
		var path := await save_card("user://fundforge-ending-%s.png" % Api.room_id)
		saved.text = ("Saved " + path) if path != "" else "Couldn't save the card."
		save.disabled = false)
	v.add_child(save)
	v.add_child(saved)
	_debrief_research(v)


## Render the ending card offscreen, only on demand, and save it as a PNG. Returns the absolute path, or ""
## without an outcome. Research and the chain head are optional: their rows drop if a call fails.
func save_card(path: String) -> String:
	var o: Variant = view.get("outcome")
	if not o is Dictionary:
		return ""
	var research := {}
	var res: Dictionary = await Api.debrief({"version": int(view.get("version", -1))})
	if res.get("ok", false) and res.get("data") is Dictionary:
		research = res["data"].get("research", {})
	var verify := {}
	res = await Api.verify()
	if res.get("ok", false) and res.get("data") is Dictionary:
		verify = res["data"]
	var vp := SubViewport.new()
	vp.size = CardRules.SIZE
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(vp)
	vp.add_child(_card(o, CardRules.rows(o, view.get("names", {}), research, verify)))
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	vp.queue_free()
	if img == null or img.save_png(path) != OK:
		return ""
	return ProjectSettings.globalize_path(path)


func _card(o: Dictionary, rows: Array) -> Control:
	var bg := PanelContainer.new()
	bg.size = Vector2(CardRules.SIZE)
	bg.add_theme_stylebox_override("panel", _style(Color("#0f1a27"), Color("#f0c27a")))
	var m := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		m.add_theme_constant_override("margin_" + side, 30)
	bg.add_child(m)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	m.add_child(v)
	var head := Label.new()
	head.text = "FUNDFORGE  /  fictional fund, no real money"
	head.add_theme_color_override("font_color", Color("#8fa5ba"))
	head.add_theme_font_size_override("font_size", 18)
	v.add_child(head)
	var big := Label.new()
	big.text = CardRules.LABELS.get(o["label"], o["label"])
	big.add_theme_font_size_override("font_size", 60)
	big.add_theme_color_override("font_color", {"WIN": Color("#6cbf8f"), "SURVIVAL": Color("#e0a14a")}.get(o["label"], Color("#ec6d62")))
	v.add_child(big)
	var market := Label.new()
	market.text = CardRules.market_text(o.get("variant"), o.get("scenario"))
	market.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	market.custom_minimum_size.x = CardRules.SIZE.x - 80
	market.add_theme_font_size_override("font_size", 18)
	v.add_child(market)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 24)
	grid.add_theme_constant_override("v_separation", 4)
	v.add_child(grid)
	for r in rows:
		for i in 2:
			var l := Label.new()
			l.text = r[i]
			l.add_theme_font_size_override("font_size", 17)
			if i == 0:
				l.add_theme_color_override("font_color", Color("#8fa5ba"))
			grid.add_child(l)
	return bg


## Research scores come from the completed-run debrief; shown under the P&L result, never mixed into it.
func _debrief_research(box: VBoxContainer) -> void:
	var record := VBoxContainer.new()
	record.name = "RunRecord"
	box.add_child(record)
	_run_record_box = record
	var status := Label.new()
	status.name = "RunRecordStatus"
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	record.add_child(status)
	var retry := Button.new()
	retry.name = "RetryRunRecord"
	retry.text = "Retry run record"
	retry.hide()
	retry.pressed.connect(_fetch_run_record)
	record.add_child(retry)
	_fetch_run_record()


func _fetch_run_record() -> void:
	if _run_record_loading or not is_instance_valid(_run_record_box) or not is_instance_valid(_debrief) or not _debrief.visible:
		return
	if _run_record_box.get_meta("loaded", false):
		return
	var box := _run_record_box
	var panel := _debrief
	var version := int(view.get("version", -1))
	var status: Label = box.get_node("RunRecordStatus")
	var retry: Button = box.get_node("RetryRunRecord")
	status.text = "Loading run record..."
	retry.disabled = true
	_run_record_loading = true
	var transport: Node = _run_record_api if _run_record_api != null else Api
	var res: Dictionary = await transport.debrief({"version": version})
	_run_record_loading = false
	if not is_instance_valid(box) or box.is_queued_for_deletion() or not is_instance_valid(panel) or panel.is_queued_for_deletion() or panel != _debrief or not panel.visible or box != _run_record_box:
		# Replacement panels may have waited on this same transport guard; start their own read now.
		if is_instance_valid(_run_record_box) and _run_record_box != box:
			_fetch_run_record()
		return
	if version != int(view.get("version", -1)):
		status.text = "Run record changed while loading. Retry to read the latest completed version."
		retry.disabled = false
		retry.show()
		return
	if not res.get("ok", false) or not res.get("data") is Dictionary:
		status.text = "Run record unavailable. Retry to load research and investor relationships."
		retry.disabled = false
		retry.show()
		return
	status.text = "Run record loaded."
	box.set_meta("loaded", true)
	retry.hide()
	_debrief_investors(box, res["data"].get("investors"))
	var research: Dictionary = res["data"].get("research", {})
	var lines := TerminalRules.research_lines(research)
	if lines.is_empty():
		return
	var heading := Label.new()
	heading.name = "ResearchHeading"
	heading.text = "RESEARCH / REGIME FORECASTS (separate from P&L)"
	heading.add_theme_color_override("font_color", Color("#f0c27a"))
	box.add_child(heading)
	for line in lines:
		var row := Label.new()
		row.text = line
		box.add_child(row)
	var policy := Label.new()
	policy.text = str(research.get("policy", ""))
	policy.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	policy.add_theme_color_override("font_color", Color("#8fa5ba"))
	policy.add_theme_font_size_override("font_size", 12)
	box.add_child(policy)


func _debrief_investors(box: VBoxContainer, record: Variant) -> void:
	var lines := InvestorRecordRules.lines(record)
	if lines.is_empty():
		return
	var heading := Label.new()
	heading.name = "InvestorRecordHeading"
	heading.text = "INVESTOR RELATIONSHIPS / COMPLETED RUN"
	heading.add_theme_color_override("font_color", Color("#f0c27a"))
	box.add_child(heading)
	for line in lines:
		var row := Label.new()
		row.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		row.text = line
		box.add_child(row)
