class_name Office
extends Node2D
## The isometric fund office and its street: rooms, furniture, NPCs, partner avatars and world effects.
## Pure presentation: it reads the server view and never changes economics.

signal interact(location: String)
signal near_location(location: String)

var me: Avatar
var partner: Avatar
var traders: Array[Avatar] = []
var role := "pm"

var _boxes: Array = []  # [grid Vector2, size Vector3, color]
var _screens_red := false
var _alarm := false
var _halt := false
var _glow_research := 0.0
var _letter_on_table := false
var _shake := 0.0
var _t := 0.0
var _near := ""
var _camera: Camera2D


func _ready() -> void:
	_build_furniture()
	var signs := Node2D.new()  # room signs float above everyone
	signs.z_index = 4000
	signs.draw.connect(func():
		for key in WorldRules.LOCATIONS:
			var r: Rect2i = WorldRules.LOCATIONS[key]["rect"]
			var p := WorldRules.to_screen(Vector2(r.position.x + 0.3, r.position.y + 0.3)) + Vector2(-30, -40)
			signs.draw_string(ThemeDB.fallback_font, p, WorldRules.LOCATIONS[key]["label"], HORIZONTAL_ALIGNMENT_LEFT,
					-1, 15, Color(1, 1, 1, 0.92)))
	add_child(signs)
	_camera = Camera2D.new()
	_camera.zoom = Vector2(1.15, 1.15)
	_camera.position_smoothing_enabled = true
	add_child(_camera)
	for i in range(6):
		var t := _spawn("", Color("#c9b49a"), Color("#3a5a7a"))
		t.place(Vector2(3.2 + (i % 3) * 2.2, 3.4 + int(i / 3) * 2.2))
		traders.append(t)


func setup(my_role: String, my_name: String, partner_name: String) -> void:
	role = my_role
	me = _spawn(my_name + " (you)", Color("#e8c9a8"), Color("#1d6fb8") if role == "pm" else Color("#b8461d"))
	me.place(WorldRules.LOCATIONS["trading" if role == "pm" else "risk"]["spot"])
	me.speed = 4.0
	var other := "mp" if role == "pm" else "pm"
	partner = _spawn(partner_name, Color("#d8b892"), Color("#1d6fb8") if other == "pm" else Color("#b8461d"))
	partner.place(WorldRules.LOCATIONS["trading" if other == "pm" else "risk"]["spot"] + Vector2(0.9, 0.7))


func _spawn(text: String, skin: Color, coat: Color) -> Avatar:
	var a := Avatar.new()
	a.label_text = text
	a.body_color = skin
	a.accent = coat
	add_child(a)
	return a


func _build_furniture() -> void:
	# trading desks with monitors
	for i in range(6):
		var g := Vector2(2.6 + (i % 3) * 2.2, 2.8 + int(i / 3) * 2.2)
		_boxes.append([g, Vector3(1.4, 0.6, 0.5), Color("#6b5a47")])
		_boxes.append([g + Vector2(0.3, 0.05), Vector3(0.8, 0.12, 0.45), Color("#101820"), "screen"])
	_boxes.append([Vector2(12, 3), Vector3(3, 1.6, 0.45), Color("#7a5634")])  # committee table
	_boxes.append([Vector2(18, 2.2), Vector3(3, 0.2, 1.4), Color("#101820"), "riskwall"])
	_boxes.append([Vector2(17.6, 4.2), Vector3(1.2, 0.8, 0.5), Color("#555")])
	for i in range(3):
		_boxes.append([Vector2(2.4, 9.4 + i * 1.4), Vector3(0.5, 1.0, 1.6), Color("#5a3e2b"), "shelf"])
	_boxes.append([Vector2(12.2, 9.4), Vector3(1.0, 1.0, 1.0), Color("#5d6b74"), "safe"])
	_boxes.append([Vector2(9, 10), Vector3(1.6, 0.8, 0.5), Color("#6b5a47")])
	_boxes.append([Vector2(16, 10), Vector3(2.0, 0.8, 0.45), Color("#7d4b4b")])  # sofa
	_boxes.append([Vector2(19, 11.5), Vector3(2.0, 0.8, 0.45), Color("#7d4b4b")])
	_boxes.append([Vector2(6, 19), Vector3(5, 0.6, 0.6), Color("#6b5a47")])  # broker counter
	_boxes.append([Vector2(16, 18), Vector3(2.0, 2.0, 0.1), Color("#101820"), "board"])  # exchange board
	_boxes.sort_custom(func(a, b): return a[0].x + a[0].y < b[0].x + b[0].y)


# ---------------- state from the server ----------------

func apply_view(view: Dictionary, effects: Array) -> void:
	var fund: Dictionary = view.get("fund", {})
	_alarm = fund.get("margin_call") != null
	for e in effects:
		match e:
			"screens_red": _screens_red = true
			"panic":
				for t in traders: t.panic = true
			"shake": _shake = 0.6
			"halt_board": _halt = true
			"research_glow": _glow_research = 4.0
			"courier": _send_courier(true)
			"courier_back": _send_courier(false)
			"letter_committee": _letter_on_table = true
			"lp_visitor": _send_visitor()
	var other := "mp" if role == "pm" else "pm"
	var where := WorldRules.partner_location(view, other)
	var spot: Vector2 = WorldRules.LOCATIONS[where]["spot"]
	if partner and partner.grid_pos.distance_to(spot) > 1.0 and partner.path.is_empty():
		partner.walk_to(spot + Vector2(0.6, 0.4))


func _send_courier(inbound: bool) -> void:
	var c := _spawn("Broker courier", Color("#e2c6a2"), Color("#2f6d5f"))
	c.carrying = inbound
	c.free_after_path = true
	var start := Vector2(8.5, 19.5)
	var door := Vector2(13.5, 14.5)
	c.place(start if inbound else Vector2(13.5, 6.5))
	c.follow([Vector2(8.5, 16), door, Vector2(13.5, 6.5)] if inbound else [door, Vector2(8.5, 16), start])


func _send_visitor() -> void:
	var v := _spawn("Tactical LP", Color("#d9b48f"), Color("#5b3d7a"))
	v.free_after_path = false
	v.place(Vector2(23, 15.5))
	v.follow([Vector2(18.5, 15.5), Vector2(18.5, 11)])


# ---------------- input and movement ----------------

func _unhandled_input(event: InputEvent) -> void:
	if me == null:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		me.walk_to(WorldRules.to_grid(get_global_mouse_position()))
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
		_camera.zoom = (_camera.zoom * 1.1).clamp(Vector2(0.6, 0.6), Vector2(2.2, 2.2))
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
		_camera.zoom = (_camera.zoom / 1.1).clamp(Vector2(0.6, 0.6), Vector2(2.2, 2.2))
	elif event.is_action_pressed("ui_accept") or (event is InputEventKey and event.pressed and event.keycode == KEY_E):
		if _near != "":
			interact.emit(_near)


func _process(delta: float) -> void:
	_t += delta
	_glow_research = maxf(0.0, _glow_research - delta)
	if me:
		var dir := Vector2(Input.get_axis("ui_left", "ui_right"), Input.get_axis("ui_up", "ui_down"))
		if dir != Vector2.ZERO:
			# screen-space arrows -> iso grid directions
			var g := Vector2(dir.x + dir.y, dir.y - dir.x).normalized()
			me.place(WorldRules.clamp_to_world(me.grid_pos + g * me.speed * delta))
		var loc := WorldRules.location_at(me.grid_pos)
		if loc != _near:
			_near = loc
			near_location.emit(loc)
		_camera.position = me.position + Vector2(0, -40)
	if _shake > 0.0:
		_shake -= delta
		_camera.offset = Vector2(randf_range(-6, 6), randf_range(-4, 4))
	else:
		_camera.offset = Vector2.ZERO
	queue_redraw()


# ---------------- drawing ----------------

func _draw() -> void:
	for y in range(WorldRules.WORLD.size.y):
		for x in range(WorldRules.WORLD.size.x):
			var g := Vector2(x, y)
			var loc := WorldRules.location_at(g + Vector2(0.5, 0.5))
			var col := Color("#1c2430")
			if WorldRules.STREET.has_point(Vector2i(x, y)):
				col = Color("#3b3f45") if (x + y) % 2 == 0 else Color("#383c42")
			elif loc != "":
				col = WorldRules.LOCATIONS[loc]["color"]
				if (x + y) % 2 == 0:
					col = col.lightened(0.05)
				if loc == _near:
					col = col.lightened(0.12)
				if loc == "risk" and _alarm:
					col = col.lerp(Color("#a9281f"), 0.35 + 0.25 * sin(_t * 6.0))
				if loc == "research" and _glow_research > 0.0:
					col = col.lerp(Color("#d8c27a"), 0.3 * _glow_research / 4.0)
			_diamond(g, col)
	for key in WorldRules.LOCATIONS:
		_walls(WorldRules.LOCATIONS[key]["rect"], key)
	for b in _boxes:
		_box(b)
	if _letter_on_table:
		var p := WorldRules.to_screen(Vector2(13.4, 3.8)) + Vector2(0, -22)
		draw_rect(Rect2(p, Vector2(14, 10)), Color("#f4efe2"))
		draw_line(p, p + Vector2(7, 5), Color("#a9281f"), 1.5)
		draw_line(p + Vector2(14, 0), p + Vector2(7, 5), Color("#a9281f"), 1.5)


func _diamond(g: Vector2, col: Color) -> void:
	var pts := PackedVector2Array([
		WorldRules.to_screen(g), WorldRules.to_screen(g + Vector2(1, 0)),
		WorldRules.to_screen(g + Vector2(1, 1)), WorldRules.to_screen(g + Vector2(0, 1))])
	draw_colored_polygon(pts, col)
	draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0, 0, 0, 0.12), 1.0)


func _walls(r: Rect2i, key: String) -> void:
	var h := Vector2(0, -28)
	var c: Color = (WorldRules.LOCATIONS[key]["color"] as Color).darkened(0.35)
	var a := WorldRules.to_screen(Vector2(r.position))
	var b := WorldRules.to_screen(Vector2(r.position.x + r.size.x, r.position.y))
	var d := WorldRules.to_screen(Vector2(r.position.x, r.position.y + r.size.y))
	draw_colored_polygon(PackedVector2Array([a, b, b + h, a + h]), c)
	draw_colored_polygon(PackedVector2Array([a, d, d + h, a + h]), c.darkened(0.15))


## Iso box with three visible faces. b = [grid, Vector3(w_x, w_y, height_in_tiles), color, tag?]
func _box(b: Array) -> void:
	var g: Vector2 = b[0]
	var s: Vector3 = b[1]
	var col: Color = b[2]
	var tag: String = b[3] if b.size() > 3 else ""
	var up := Vector2(0, -s.z * WorldRules.TILE_H * 1.6)
	var p0 := WorldRules.to_screen(g)
	var p1 := WorldRules.to_screen(g + Vector2(s.x, 0))
	var p2 := WorldRules.to_screen(g + Vector2(s.x, s.y))
	var p3 := WorldRules.to_screen(g + Vector2(0, s.y))
	if tag == "screen" or tag == "riskwall" or tag == "board":
		col = Color("#122b1c")
		if tag == "screen" and _screens_red:
			col = Color("#5c1410").lerp(Color("#a9281f"), 0.5 + 0.5 * sin(_t * 5.0 + g.x))
		elif tag == "riskwall" and _alarm:
			col = Color("#a9281f").lerp(Color("#300"), 0.5 + 0.5 * sin(_t * 6.0))
		elif tag == "board" and _halt:
			col = Color("#050505")
	draw_colored_polygon(PackedVector2Array([p3, p2, p2 + up, p3 + up]), col.darkened(0.25))
	draw_colored_polygon(PackedVector2Array([p1, p2, p2 + up, p1 + up]), col.darkened(0.1))
	draw_colored_polygon(PackedVector2Array([p0 + up, p1 + up, p2 + up, p3 + up]), col.lightened(0.08))
	if tag == "board":
		var txt := "BEAM  HALTED" if _halt else "BEAM  ▲ LIVE"
		draw_string(ThemeDB.fallback_font, p3 + up * 0.55 + Vector2(6, 0), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 13,
				Color("#ff5a4a") if _halt else Color("#7fe08a"))
