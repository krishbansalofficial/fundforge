extends Node
## Entry point: open or join a fund, then run the office world with its HUD.

var office: Office3D
var hud: Hud
var _seen_notices := 0
var _joined := false
var _menu: Control


func _ready() -> void:
	_build_menu()
	Api.view_changed.connect(_on_view)
	_dev_flags()


## Dev/CI flags (after `--`): --server=URL --join=room:token --goto=location --shot=path.png --shot-after=SECONDS
func _dev_flags() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else ""
	if args.has("join"):
		var parts: PackedStringArray = args["join"].split(":")
		_enter(args.get("server", "http://127.0.0.1:8000"), parts[0], parts[1])
	if args.has("goto"):
		await get_tree().create_timer(1.5).timeout
		if office:
			var spot: Vector2 = WorldRules.LOCATIONS[args["goto"]]["spot"]
			office.me.walk_to(Vector3(spot.x, 0.0, spot.y))
	if args.has("shot"):
		await get_tree().create_timer(float(args.get("shot-after", "6"))).timeout
		await RenderingServer.frame_post_draw
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
	var server := _field(v, "Server", "http://127.0.0.1:8000")
	var pm := _field(v, "Portfolio manager's name", "Ana")
	var mp := _field(v, "Managing partner's name", "Ben")
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
			var res: Dictionary = await Api.create_room(server.text, pm.text, mp.text, role)
			if not res["ok"]:
				status.text = "Couldn't reach the server at %s. Start it with: docker compose up" % server.text
				return
			var d: Dictionary = res["data"]
			_enter(server.text, d["room_id"], d["tokens"][role]))
	open.pressed.connect(func():
		status.text = "Opening..."
		var res: Dictionary = await Api.create_room(server.text, pm.text, mp.text)
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
		office.interact.connect(hud.open_panel)
		office.near_location.connect(hud.set_near)
		_seen_notices = 0
	var notices: Array = view.get("notices", [])
	var effects := WorldRules.new_effects(notices, _seen_notices)
	_seen_notices = notices.size()
	office.apply_view(view, effects)
	hud.apply_view(view)


func _process(_delta: float) -> void:
	if not _joined:
		return
	var h := WorldRules.clock_hour(Api.view, Time.get_ticks_msec() / 1000.0 - Api.view_received_at)
	office.set_hour(h)
	hud.update_clock(h)
