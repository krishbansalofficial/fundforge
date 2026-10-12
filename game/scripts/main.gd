extends Node
## Entry point: open or join a fund, then run the office world with its HUD.

var office: Office3D
var hud: Hud
var _seen_notices := 0
var _seen_fills := -1  # -1 until the first view, so joining a room does not replay its history as sound
var _joined := false
var _menu: Control
var _args := {}
var _server := "http://127.0.0.1:8000"


func _ready() -> void:
	# Flags work after `--` (editor/dev) or directly on an exported build: FundForge.exe --server=URL
	for a in OS.get_cmdline_args() + OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.trim_prefix("--").split("=", true, 1)
			_args[kv[0]] = kv[1] if kv.size() > 1 else ""
	var env_server := OS.get_environment("FUNDFORGE_SERVER")
	_server = str(_args.get("server", env_server if env_server != "" else _server))
	_build_menu()
	Api.view_changed.connect(_on_view)
	_dev_flags()


## Dev/CI flags: --server=URL --join=room:token --goto=location --terminal=MON --shot=path.png --shot-after=SECONDS --demo
## (env FUNDFORGE_SERVER also sets the default server)
func _dev_flags() -> void:
	var args := _args
	if args.has("demo"):
		_demo()
	if args.has("join"):
		var parts: PackedStringArray = args["join"].split(":")
		_enter(_server, parts[0], parts[1])
	if args.has("goto"):
		await get_tree().create_timer(1.5).timeout
		if office:
			var spot: Vector2 = WorldRules.LOCATIONS[args["goto"]]["spot"]
			office.me.walk_to(Vector3(spot.x, 0.0, spot.y))
	if args.has("terminal"):
		# Screenshot/smoke option: waits for a real room view before opening the terminal.
		for _attempt in range(100):
			if hud:
				hud.open_terminal()
				hud.terminal.navigate(str(args.get("terminal", "MON")))
				break
			await get_tree().create_timer(0.1).timeout
	if args.has("shot"):
		await get_tree().create_timer(float(args.get("shot-after", "6"))).timeout
		# Force a frame even when a hidden/minimized smoke-test window is occluded.
		RenderingServer.force_draw(false)
		get_viewport().get_texture().get_image().save_png(args["shot"])
		get_tree().quit()


func _build_menu() -> void:
	_menu = PanelContainer.new()
	_menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color("#101a26")
	_menu.add_theme_stylebox_override("panel", bg)
	var layer := CanvasLayer.new()
	add_child(layer)
	layer.add_child(_menu)
	var center := CenterContainer.new()
	_menu.add_child(center)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(560, 0)
	v.add_theme_constant_override("separation", 10)
	center.add_child(v)
	var title := Label.new()
	title.text = "FundForge"
	title.add_theme_font_size_override("font_size", 52)
	v.add_child(title)
	var tag := Label.new()
	tag.text = "Two partners. A fictional $25m fund. Ten days of crisis. Investor money can't pay your payroll."
	tag.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(tag)
	var server := _field(v, "Server", _server)
	var pm := _field(v, "Portfolio manager's name", "Ana")
	var mp := _field(v, "Managing partner's name", "Ben")
	var scenario := OptionButton.new()
	for spec in WorldRules.SCENARIOS:
		scenario.add_item(spec[1])
	v.add_child(scenario)
	var status := Label.new()
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var solo_pm := Button.new()
	solo_pm.text = "Play solo as portfolio manager (bot runs operations)"
	v.add_child(solo_pm)
	var solo_mp := Button.new()
	solo_mp.text = "Play solo as managing partner (bot trades)"
	v.add_child(solo_mp)
	var open := Button.new()
	open.text = "Open a two-player fund"
	v.add_child(open)
	var code := _field(v, "...or join with an invite code (room:token)", "")
	var join := Button.new()
	join.text = "Join fund"
	v.add_child(join)
	v.add_child(status)
	for spec in [[solo_pm, "pm"], [solo_mp, "mp"]]:
		var role: String = spec[1]
		(spec[0] as Button).pressed.connect(func():
			status.text = "Opening..."
			var res: Dictionary = await Api.create_room(server.text, pm.text, mp.text, role,
					WorldRules.SCENARIOS[scenario.selected][0])
			if not res["ok"]:
				status.text = "Couldn't reach the server at %s. Start it with: docker compose up" % server.text
				return
			var d: Dictionary = res["data"]
			_enter(server.text, d["room_id"], d["tokens"][role]))
	open.pressed.connect(func():
		status.text = "Opening..."
		var res: Dictionary = await Api.create_room(server.text, pm.text, mp.text, "",
				WorldRules.SCENARIOS[scenario.selected][0])
		if not res["ok"]:
			status.text = "Couldn't reach the server at %s. Start it with: docker compose up" % server.text
			return
		var d: Dictionary = res["data"]
		var partner_code := "%s:%s" % [d["room_id"], d["tokens"]["mp"]]
		DisplayServer.clipboard_set(partner_code)
		status.text = "Fund open. Your partner's invite code was copied to the clipboard:\n" + partner_code
		_enter(server.text, d["room_id"], d["tokens"]["pm"]))
	join.pressed.connect(func():
		var parts := code.text.strip_edges().split(":")
		if parts.size() != 2:
			status.text = "An invite code looks like room:token"
			return
		_enter(server.text, parts[0], parts[1]))


func _field(parent: Control, label: String, value: String) -> LineEdit:
	var l := Label.new()
	l.text = label
	parent.add_child(l)
	var e := LineEdit.new()
	e.text = value
	parent.add_child(e)
	return e


func _enter(url: String, room: String, token: String) -> void:
	Api.join(url, room, token)


func _on_view(view: Dictionary) -> void:
	if not _joined:
		_joined = true
		_menu.get_parent().queue_free()
		office = Office3D.new()
		add_child(office)
		var names: Dictionary = view.get("names", {})
		var role: String = view.get("role", "pm")
		office.setup(role, names.get(role, role), names.get("mp" if role == "pm" else "pm", "Partner"))
		hud = Hud.new()
		add_child(hud)
		hud.terminal.open_changed.connect(func(is_open): get_viewport().set_meta("forge_terminal_open", is_open))
		office.interact.connect(hud.open_panel)
		office.near_location.connect(hud.set_near)
		var partner_role := "mp" if role == "pm" else "pm"
		Api.partner_moved.connect(func(r: String, pos: Vector3, _loc: String):
			if r == partner_role: office.partner_presence(pos))
		Api.partner_left.connect(func(r: String): if r == partner_role or r == "": office.partner_gone())
		_seen_notices = 0
	var notices: Array = view.get("notices", [])
	var effects := WorldRules.new_effects(notices, _seen_notices)
	_seen_notices = notices.size()
	var fills := Sfx.fill_count(view)
	if _seen_fills >= 0:
		hud.sfx.play_effects(effects)
		if fills > _seen_fills:
			hud.sfx.play("fill")
	_seen_fills = fills
	office.apply_view(view, effects)
	hud.apply_view(view)


func _process(delta: float) -> void:
	if not _joined:
		return
	if _args.has("demo"):
		office._cam_yaw += delta * 0.06  # slow cinematic orbit
	Api.send_move(office.me.position, office._near)  # throttled; a no-op until presence is live
	var h := WorldRules.clock_hour(Api.view, Time.get_ticks_msec() / 1000.0 - Api.view_received_at)
	office.set_hour(h)
	hud.update_clock(h)


# ---------------- scripted trailer (--demo) ----------------
## Plays a solo season as the PM against the live API. Every money/time outcome comes from the server;
## the script only picks the camera, the two day-14 decisions and how long to linger. Time moves by the
## joint 'ready' command (not the wall-clock ticker) and pacing uses game-time timers, so the trailer is
## the same length under Movie Maker (--write-movie ... --fixed-fps 30) however slowly frames render.

const DEMO_TOUR := [[12, "trading"], [14, "committee"], [15, "street"], [17, "risk"], [19, "trading"]]


func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout


func _demo() -> void:
	Api.base_url = _server.trim_suffix("/")
	if not (await Api.request(HTTPClient.METHOD_GET, "/api/health"))["ok"]:
		push_error("demo: no API at %s" % _server)
		get_tree().quit(1)
		return
	var res: Dictionary = await Api.create_room(_server, "Ana", "Morgan", "pm")
	if not res["ok"]:
		push_error("demo: could not create a room")
		get_tree().quit(1)
		return
	_enter(_server, res["data"]["room_id"], res["data"]["tokens"]["pm"])
	while office == null:
		await _wait(0.1)
	var stage := ""
	var traded := false
	hud.caption = "Trailer: time advances one execution window at a time"
	await _wait(4.0)  # opening shot of the trading floor
	while Api.view.get("outcome") == null:
		var day: int = Api.view.get("clock", {}).get("day", 0)
		var want := stage
		for step in DEMO_TOUR:
			if day >= step[0]:
				want = step[1]
		if want != stage:
			stage = want
			var spot: Vector2 = WorldRules.LOCATIONS[stage]["spot"]
			office.me.place(Vector3(spot.x, 0.0, spot.y))
		if day >= 14 and not traded:
			traded = true
			await _demo_trade()
		var seen: int = Api.view.get("notices", []).size()
		var said: int = Api.view.get("chat", []).size()
		await _demo_advance()
		var notable := ""
		for n in Api.view.get("notices", []).slice(seen):
			if n.get("kind", "") in ["alert", "market", "research"]:
				notable = n.get("text", "")
		if notable != "" or Api.view.get("chat", []).size() > said:
			if notable != "":
				hud.caption = notable
			await _wait(3.5)  # linger on the event, as the live clock's auto-pause would
		else:
			await _wait(0.7)  # one window per ~0.7 s: the 4x pace (2 s) compressed for the trailer
	hud.caption = ""
	await _wait(1.0)
	hud.close_panel()
	await _wait(10.0)  # hold on the debrief
	get_tree().quit()


## Mark ready (Morgan readies in the same transaction, so the clock jumps one window); wait for the new view.
func _demo_advance() -> void:
	var v := int(Api.view.get("version", 0))
	await Api.command({"type": "ready", "version": v})
	for i in 30:
		if int(Api.view.get("version", 0)) > v:
			return
		await _wait(0.1)
		Api._poll()


## Day 14: cover 1,250 BRIN on a PM ticket, and put a 20,000 BEAM sale to Morgan, who countersigns.
func _demo_trade() -> void:
	await Api.command({"type": "ticket", "order_id": "pm-demo-brin", "sym": "BRIN", "side": "COVER", "qty": 1250})
	await Api.command({"type": "propose", "package_id": "pkg-demo-beam",
			"orders": [{"order_id": "pm-demo-beam", "sym": "BEAM", "side": "SELL", "qty": 20000}]})
	hud.open_panel("committee")
	await _wait(3.5)
	hud.close_panel()
