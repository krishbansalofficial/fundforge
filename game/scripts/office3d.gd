class_name Office3D
extends Node3D
## HD 3D fund office and street (Kenney CC0 models, Forward+ lighting, shadows, SSAO, glow).
## Grid coordinates from WorldRules map 1 tile = 1 metre-ish unit: grid (x, y) -> world (x, 0, y).
## Pure presentation: reads the server view, never changes economics.

signal interact(location: String)
signal near_location(location: String)

const F := "res://assets/kenney/furniture/%s.glb"
const CITY := "res://assets/kenney/city/%s.glb"
const ROAD := "res://assets/kenney/roads/%s.glb"
const WALL := Vector3(1.0, 0.55, 1.0)  # cutaway height so the camera sees into rooms

var role := "pm"
var me: Actor3D
var partner: Actor3D
var traders: Array[Actor3D] = []

var _camera: Camera3D
var _cam_dist := 11.0
var _cam_yaw := deg_to_rad(45.0)
var _sun: DirectionalLight3D
var _env: Environment
var _screens: Array[StandardMaterial3D] = []
var _risk_screen: StandardMaterial3D
var _board: StandardMaterial3D
var _board_label: Label3D
var _alarm_light: OmniLight3D
var _research_light: OmniLight3D
var _letter: Node3D
var _floor_mats := {}
var _near := ""
var _t := 0.0
var _shake := 0.0
var _mode := ""  # "", "red", "green"
var _alarm := false
var _halt := false
var _glow_research := 0.0


func _ready() -> void:
	_environment()
	_build_city()
	_build_rooms()
	_build_furniture()
	_camera = Camera3D.new()
	_camera.fov = 38.0
	add_child(_camera)


# ---------------- scene construction ----------------

func _environment() -> void:
	var we := WorldEnvironment.new()
	_env = Environment.new()
	var sky := Sky.new()
	var mat := ProceduralSkyMaterial.new()
	mat.sky_top_color = Color("#3b5f8f")
	mat.sky_horizon_color = Color("#a9c3d9")
	mat.ground_horizon_color = Color("#6b7a86")
	sky.sky_material = mat
	_env.background_mode = Environment.BG_SKY
	_env.sky = sky
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	_env.ambient_light_energy = 0.6
	_env.tonemap_mode = Environment.TONE_MAPPER_ACES
	_env.ssao_enabled = true
	_env.ssao_radius = 0.6
	_env.ssao_intensity = 1.6
	_env.glow_enabled = true
	_env.glow_intensity = 0.6
	_env.glow_bloom = 0.08
	_env.fog_enabled = true
	_env.fog_density = 0.004
	_env.fog_light_color = Color("#a9c3d9")
	we.environment = _env
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.directional_shadow_max_distance = 45.0
	_sun.light_energy = 1.3
	add_child(_sun)
	set_hour(10.0)


func _model(path: String, pos: Vector3, rot_deg := 0.0, scale := 1.0) -> Node3D:
	var n: Node3D = load(path).instantiate()
	n.position = pos
	n.rotation_degrees.y = rot_deg
	n.scale = Vector3.ONE * scale
	add_child(n)
	return n


func _plane(rect: Rect2, y: float, color: Color, rough := 0.8) -> StandardMaterial3D:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = rect.size
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = rough
	pm.material = mat
	mi.mesh = pm
	mi.position = Vector3(rect.position.x + rect.size.x / 2.0, y, rect.position.y + rect.size.y / 2.0)
	add_child(mi)
	return mat


func _emissive(size: Vector3, pos: Vector3, color: Color, rot_deg := 0.0) -> StandardMaterial3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color.BLACK
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 1.6
	bm.material = mat
	mi.mesh = bm
	mi.position = pos
	mi.rotation_degrees.y = rot_deg
	add_child(mi)
	return mat


func _build_city() -> void:
	_plane(Rect2(-12, -12, 48, 48), -0.02, Color("#55606a"), 0.95)  # ground
	_plane(Rect2(0, 0, 24, 15), 0.0, Color("#2a313a"))  # office slab
	for x in range(-6, 30):  # street
		_model(ROAD % "road-straight", Vector3(x + 0.5, 0.0, 15.5), 90.0)
		_model(ROAD % "road-straight", Vector3(x + 0.5, 0.0, 16.5), 90.0)
	_plane(Rect2(-6, 17, 36, 1), 0.01, Color("#8c8f93"))  # far sidewalk
	for x in [2, 8, 14, 20]:
		_model(ROAD % "light-square", Vector3(x, 0.0, 14.8), 0.0, 2.6)
	# prime broker building across the street, plus neighbours for a skyline
	_model(CITY % "building-e", Vector3(8.5, 0.0, 20.2), 180.0, 3.2)
	_model(CITY % "building-skyscraper-c", Vector3(1.5, 0.0, 21.0), 180.0, 3.0)
	_model(CITY % "building-skyscraper-a", Vector3(15.5, 0.0, 21.0), 180.0, 3.0)
	_model(CITY % "building-h", Vector3(21.5, 0.0, 20.0), 180.0, 3.0)
	_model(CITY % "building-a", Vector3(-3.5, 0.0, 20.0), 180.0, 3.0)
	var sign := Label3D.new()
	sign.text = "PRIME BROKER"
	sign.font_size = 96
	sign.pixel_size = 0.006
	sign.modulate = Color("#f0c27a")
	sign.outline_size = 16
	sign.position = Vector3(8.5, 3.3, 18.4)
	add_child(sign)
	# exchange board on the street
	_board = _emissive(Vector3(2.6, 1.0, 0.08), Vector3(17.5, 1.4, 17.8), Color("#1f8f3a"))
	_board_label = Label3D.new()
	_board_label.text = "BEAM  LIVE"
	_board_label.font_size = 80
	_board_label.pixel_size = 0.006
	_board_label.position = Vector3(17.5, 1.4, 17.74)
	_board_label.rotation_degrees.y = 180.0
	add_child(_board_label)


func _build_rooms() -> void:
	var floors := {"trading": Color("#3a4c63"), "committee": Color("#6a4e35"), "risk": Color("#4a3a40"),
			"research": Color("#3c5440"), "backoffice": Color("#4a4a55"), "lp": Color("#6b5a3e"), "broker": Color("#3b5560")}
	for key in WorldRules.LOCATIONS:
		if key == "broker":
			continue
		var r: Rect2i = WorldRules.LOCATIONS[key]["rect"]
		_floor_mats[key] = _plane(Rect2(r.position.x, r.position.y, r.size.x, r.size.y), 0.01, floors[key], 0.6)
		# back walls only (cutaway, like a management sim): along the north and west edges
		for x in range(r.size.x):
			var wall := "wallWindow" if (x % 3 == 1 and r.position.y == 2) else "wall"
			_model(F % wall, Vector3(r.position.x + x, 0.0, r.position.y), 0.0).scale = WALL
		for y in range(r.size.y):
			_model(F % "wall", Vector3(r.position.x, 0.0, r.position.y + y + 1), 90.0).scale = WALL
		var lamp := OmniLight3D.new()
		lamp.position = Vector3(r.position.x + r.size.x / 2.0, 1.2, r.position.y + r.size.y / 2.0)
		lamp.omni_range = maxf(r.size.x, r.size.y) * 0.8
		lamp.light_energy = 0.7
		lamp.light_color = Color("#ffe2b8")
		add_child(lamp)
		var label := Label3D.new()
		label.text = WorldRules.LOCATIONS[key]["label"]
		label.font_size = 64
		label.pixel_size = 0.005
		label.outline_size = 12
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.position = Vector3(r.position.x + r.size.x / 2.0, 1.2, r.position.y + 0.4)
		add_child(label)


func _build_furniture() -> void:
	# trading floor: six desks with dual screens and seated traders
	var models := ["c", "d", "e", "f", "g", "h"]
	for i in range(6):
		var p := Vector3(3.4 + (i % 3) * 2.2, 0.0, 3.4 + int(i / 3) * 2.3)
		_model(F % "desk", p, 180.0)
		_model(F % "computerScreen", p + Vector3(-0.15, 0.38, -0.12), 180.0)
		_model(F % "computerKeyboard", p + Vector3(-0.15, 0.38, 0.08), 180.0)
		_model(F % "chairDesk", p + Vector3(-0.2, 0.0, 0.5), 180.0)
		_screens.append(_emissive(Vector3(0.34, 0.2, 0.01), p + Vector3(-0.35, 0.56, -0.115), Color("#1d6b8f")))
		var t := Actor3D.new()
		add_child(t)
		t.setup(models[i], "")
		t.place(p + Vector3(-0.35, 0.0, 0.62))
		t.rotation_degrees.y = 180.0
		t.seated = true
		traders.append(t)
	_model(F % "pottedPlant", Vector3(9.4, 0, 2.5))
	_model(F % "kitchenCoffeeMachine", Vector3(2.4, 0.0, 7.4))
	# committee room: long table with chairs, and the recall letter appears here
	_model(F % "rugRectangle", Vector3(13.5, 0.01, 4.5), 0.0, 1.6)
	_model(F % "tableCross", Vector3(13.5, 0.0, 4.5), 90.0, 1.6)
	for dz in [-0.9, 0.0, 0.9]:
		_model(F % "chairCushion", Vector3(12.6, 0.0, 4.5 + dz), 90.0)
		_model(F % "chairCushion", Vector3(14.4, 0.0, 4.5 + dz), -90.0)
	_model(F % "pottedPlant", Vector3(15.4, 0, 2.6))
	# risk and treasury: wall of screens, desk, red alarm light
	_model(F % "cabinetTelevision", Vector3(19.5, 0.0, 2.5))
	_model(F % "televisionModern", Vector3(19.1, 0.3, 2.4))
	_risk_screen = _emissive(Vector3(1.3, 0.62, 0.02), Vector3(19.5, 1.1, 2.06), Color("#2a6e4a"))
	_model(F % "desk", Vector3(19.5, 0.0, 4.6), 180.0)
	_model(F % "laptop", Vector3(19.4, 0.38, 4.5), 180.0)
	_alarm_light = OmniLight3D.new()
	_alarm_light.position = Vector3(19.5, 1.3, 4.0)
	_alarm_light.omni_range = 5.0
	_alarm_light.light_color = Color("#ff2a1a")
	_alarm_light.light_energy = 0.0
	add_child(_alarm_light)
	# research library
	for i in range(4):
		_model(F % "bookcaseOpen", Vector3(2.5 + i * 1.0, 0.0, 9.3))
		_model(F % "books", Vector3(2.5 + i * 1.0, 0.45, 9.3))
	_model(F % "lampRoundFloor", Vector3(6.3, 0.0, 9.6))
	_model(F % "table", Vector3(4.5, 0.0, 11.8))
	_model(F % "chair", Vector3(4.5, 0.0, 12.5), 180.0)
	_research_light = OmniLight3D.new()
	_research_light.position = Vector3(4.5, 1.2, 11.0)
	_research_light.light_color = Color("#ffd27a")
	_research_light.omni_range = 4.0
	_research_light.light_energy = 0.0
	add_child(_research_light)
	# management company back office: desk, cabinets, the payroll safe
	_model(F % "deskCorner", Vector3(10.5, 0.0, 10.5), 180.0)
	_model(F % "laptop", Vector3(10.3, 0.38, 10.4), 180.0)
	_model(F % "chairDesk", Vector3(10.4, 0.0, 11.1), 180.0)
	_model(F % "bookcaseClosedWide", Vector3(12.8, 0.0, 9.4))
	_model(F % "sideTableDrawers", Vector3(9.2, 0.0, 9.4))
	_model(F % "cardboardBoxClosed", Vector3(13.2, 0.0, 12.9))
	# investor lounge
	_model(F % "rugRound", Vector3(18.5, 0.01, 11.5), 0.0, 1.8)
	_model(F % "loungeSofaLong", Vector3(18.5, 0.0, 10.0))
	_model(F % "loungeChair", Vector3(17.0, 0.0, 11.8), 90.0)
	_model(F % "loungeChair", Vector3(20.0, 0.0, 11.8), -90.0)
	_model(F % "tableCoffeeGlass", Vector3(18.5, 0.0, 11.5))
	_model(F % "pottedPlant", Vector3(21.4, 0.0, 9.5))
	_model(F % "lampSquareFloor", Vector3(15.6, 0.0, 9.5))
	_model(F % "coatRackStanding", Vector3(21.3, 0.0, 13.3))


func setup(my_role: String, my_name: String, partner_name: String) -> void:
	role = my_role
	var other := "mp" if role == "pm" else "pm"
	me = Actor3D.new()
	add_child(me)
	me.setup("a" if role == "pm" else "b", my_name + " (you)", Color("#9fd0ff"))
	me.speed = 3.2
	me.place(_spot("trading" if role == "pm" else "risk"))
	partner = Actor3D.new()
	add_child(partner)
	partner.setup("b" if role == "pm" else "a", partner_name, Color("#ffc59f"))
	partner.place(_spot("trading" if other == "pm" else "risk") + Vector3(0.8, 0, 0.6))


func _spot(loc: String) -> Vector3:
	var s: Vector2 = WorldRules.LOCATIONS[loc]["spot"]
	return Vector3(s.x, 0.0, s.y)


# ---------------- daylight ----------------

func set_hour(h: float) -> void:
	var x := fposmod(h, 24.0)
	var elev := clampf(sin((x - 6.0) / 12.0 * PI), -0.25, 1.0)  # sunrise 6, noon peak, sunset 18
	_sun.rotation = Vector3(-deg_to_rad(10.0 + 55.0 * maxf(elev, 0.0)), deg_to_rad(-30.0 + (x - 12.0) * 8.0), 0.0)
	_sun.light_energy = maxf(0.05, elev) * 1.4
	_sun.light_color = Color("#ffb070").lerp(Color("#fff4e6"), clampf(elev * 1.5, 0.0, 1.0))
	_env.ambient_light_energy = 0.25 + 0.45 * maxf(elev, 0.0)


# ---------------- state from the server ----------------

func apply_view(view: Dictionary, effects: Array) -> void:
	_alarm = view.get("fund", {}).get("margin_call") != null
	for e in effects:
		match e:
			"screens_red": _mode = "red"
			"screens_green": _mode = "green"
			"panic", "cheer":
				for t in traders: t.excited = true
			"shake": _shake = 0.7
			"halt_board":
				_halt = true
				_board_label.text = "BEAM  HALTED"
			"research_glow": _glow_research = 5.0
			"courier": _send_courier(true)
			"courier_back": _send_courier(false)
			"letter_committee": _place_letter()
			"lp_visitor": _send_visitor()
	var other := "mp" if role == "pm" else "pm"
	var dest := _spot(WorldRules.partner_location(view, other)) + Vector3(0.7, 0, 0.5)
	if partner and partner.position.distance_to(dest) > 1.0 and not partner.is_moving():
		partner.follow(_route(partner.position, dest))


## Simple door-aware route: step out to the corridor in front of the rooms, walk along it, then step in.
func _route(from: Vector3, to: Vector3) -> Array:
	var corridor := 8.4 if to.z < 8.0 or from.z < 8.0 else 14.3
	return [Vector3(from.x, 0, corridor), Vector3(to.x, 0, corridor), to]


func _place_letter() -> void:
	if _letter:
		return
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.25, 0.01, 0.18)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("#f4efe2")
	mat.emission_enabled = true
	mat.emission = Color("#ffcf70")
	mat.emission_energy_multiplier = 0.6
	bm.material = mat
	mi.mesh = bm
	mi.position = Vector3(13.5, 0.36, 4.5)
	add_child(mi)
	_letter = mi


func _send_courier(inbound: bool) -> void:
	var c := Actor3D.new()
	add_child(c)
	c.setup("k", "Broker courier", Color("#9fe0c8"))
	c.carry_letter(inbound)
	c.free_after_path = true
	var start := Vector3(8.5, 0, 18.0)
	var desk := Vector3(13.5, 0, 6.2)
	c.place(start if inbound else desk)
	c.follow([Vector3(8.5, 0, 14.3), Vector3(13.5, 0, 14.3), Vector3(13.5, 0, 8.4), desk] if inbound
			else [Vector3(13.5, 0, 8.4), Vector3(13.5, 0, 14.3), Vector3(8.5, 0, 14.3), start])


func _send_visitor() -> void:
	var v := Actor3D.new()
	add_child(v)
	v.setup("m", "Tactical LP", Color("#d9b8ff"))
	v.place(Vector3(26.0, 0, 15.5))
	v.follow([Vector3(18.5, 0, 15.0), Vector3(18.5, 0, 12.6)])


# ---------------- input and camera ----------------

func _unhandled_input(event: InputEvent) -> void:
	if me == null:
		return
	if event is InputEventMouseButton and event.pressed:
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				var hit: Variant = _ground_hit(event.position)
				if hit != null:
					me.walk_to(hit)
			MOUSE_BUTTON_WHEEL_UP: _cam_dist = maxf(5.0, _cam_dist * 0.9)
			MOUSE_BUTTON_WHEEL_DOWN: _cam_dist = minf(24.0, _cam_dist * 1.1)
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		_cam_yaw -= event.relative.x * 0.006
	elif event.is_action_pressed("ui_accept") or (event is InputEventKey and event.pressed and event.keycode == KEY_E):
		if _near != "":
			interact.emit(_near)


func _ground_hit(screen: Vector2) -> Variant:
	var origin := _camera.project_ray_origin(screen)
	var dir := _camera.project_ray_normal(screen)
	if absf(dir.y) < 0.0001:
		return null
	var t := -origin.y / dir.y
	if t <= 0.0:
		return null
	var p := origin + dir * t
	var g := WorldRules.clamp_to_world(Vector2(p.x, p.z))
	return Vector3(g.x, 0.0, g.y)


func _process(delta: float) -> void:
	_t += delta
	if me:
		var input := Vector2(Input.get_axis("ui_left", "ui_right"), Input.get_axis("ui_up", "ui_down"))
		if input != Vector2.ZERO:
			var fwd := Vector3(-sin(_cam_yaw), 0, -cos(_cam_yaw))
			var right := Vector3(cos(_cam_yaw), 0, -sin(_cam_yaw))
			var move := (right * input.x - fwd * input.y).normalized() * me.speed * 1.4 * delta
			var g := WorldRules.clamp_to_world(Vector2(me.position.x + move.x, me.position.z + move.z))
			me.walk_to(Vector3(g.x, 0, g.y))
		var loc := WorldRules.location_at(Vector2(me.position.x, me.position.z))
		if loc != _near:
			_near = loc
			near_location.emit(loc)
		var target := me.position + Vector3(0, 0.5, 0)
		var offset := Vector3(sin(_cam_yaw), 0.95, cos(_cam_yaw)).normalized() * _cam_dist
		_camera.position = _camera.position.lerp(target + offset, minf(1.0, delta * 4.0)) if _camera.position != Vector3.ZERO else target + offset
		if _shake > 0.0:
			_shake -= delta
			_camera.position += Vector3(randf_range(-0.08, 0.08), randf_range(-0.05, 0.05), 0)
		_camera.look_at(target)
	# world effects
	for i in _screens.size():
		var c := Color("#1d6b8f")
		if _mode == "red":
			c = Color("#ff2a1a").lerp(Color("#5c0a05"), 0.5 + 0.5 * sin(_t * 5.0 + i))
		elif _mode == "green":
			c = Color("#2fff6a").lerp(Color("#0a4a1c"), 0.5 + 0.5 * sin(_t * 4.0 + i))
		_screens[i].emission = c
	_risk_screen.emission = Color("#ff2a1a") if _alarm and fmod(_t, 0.8) < 0.4 else Color("#2a6e4a")
	_alarm_light.light_energy = (1.5 + 1.5 * sin(_t * 7.0)) if _alarm else 0.0
	_board.emission = Color("#3a0505") if _halt else Color("#1f8f3a")
	_glow_research = maxf(0.0, _glow_research - delta)
	_research_light.light_energy = _glow_research * 0.6
	for key in _floor_mats:
		var base: Color = _floor_mats[key].albedo_color
		_floor_mats[key].emission_enabled = key == _near
		_floor_mats[key].emission = base * 0.35
