class_name Office3D
extends Node3D
## 3D fund office and street: Poly Haven PBR materials and HDRI sky, Quaternius humans, Kenney furniture,
## Forward+ with SDFGI, SSR, SSIL/SSAO, volumetric fog and a tilt-shift depth of field.
## FF_QUALITY=low (env var) turns off SDFGI, SSIL, SSR, volumetric fog, lamp shadows and DOF for weaker GPUs.
## Grid coordinates from WorldRules map 1 tile = 1 metre-ish unit: grid (x, y) -> world (x, 0, y).
## Pure presentation: reads the server view, never changes economics.

signal interact(location: String)
signal near_location(location: String)

const F := "res://assets/kenney/furniture/%s.glb"
const CITY := "res://assets/kenney/city/%s.glb"
const ROAD := "res://assets/kenney/roads/%s.glb"
const PH := "res://assets/polyhaven/%s"
## Poly Haven texture id -> metres covered by one texture tile (1 world unit ~ 1.95 m).
const TILE := {"herringbone_parquet": 2.4, "dirty_carpet": 1.2, "smooth_concrete_floor": 1.5,
		"painted_plaster_wall": 1.2, "asphalt_02": 1.5, "concrete_pavement": 1.5}
## Room floor -> [texture, tint]; the tint keeps each room recognisable.
const FLOORS := {
	"trading": ["dirty_carpet", Color("#7f8fa6")], "committee": ["herringbone_parquet", Color.WHITE],
	"risk": ["dirty_carpet", Color("#a08c90")], "research": ["herringbone_parquet", Color("#c9d6c0")],
	"backoffice": ["smooth_concrete_floor", Color.WHITE], "lp": ["herringbone_parquet", Color("#f2dcc0")],
	"street": ["concrete_pavement", Color.WHITE],
}
const M := 0.513  # metres -> world units, for real-scale Poly Haven models
const WALL := Vector3(1.0, 0.55, 1.0)  # cutaway height so the camera sees into rooms
## Rival funds' towers across the street: id -> [name, model, x, height at scale 3].
const RIVALS := {
	"vantage": ["Vantage Quant", "building-a", -3.2, 3.9],
	"halcyon": ["Halcyon Partners", "building-skyscraper-c", 2.2, 12.3],
	"northbeam": ["Northbeam Capital", "building-skyscraper-a", 13.8, 8.7],
	"granite": ["Granite Macro", "building-h", 18.0, 3.9],
	"copperline": ["Copperline Activist", "building-c", 21.4, 2.7],
}
const STREET_CAM := Vector3(9.8, 13.0, -13.0)
const STREET_LOOK := Vector3(9.8, 6.5, 20.0)

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
var _towers := {}  # rival id -> {beacon, label, sign, light, status, flash}
var _look := Vector3.ZERO
var _high := OS.get_environment("FF_QUALITY").to_lower() != "low"
var _cam_attr: CameraAttributesPractical  # null on low quality
var _mats := {}  # cache: texture id + tint -> StandardMaterial3D


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
	var pano := PanoramaSkyMaterial.new()
	pano.panorama = load(PH % "hdri/canary_wharf_2k.hdr")
	sky.sky_material = pano
	_env.background_mode = Environment.BG_SKY
	_env.sky = sky
	_env.sky_rotation = Vector3(0, deg_to_rad(120.0), 0)
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	_env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	_env.ambient_light_energy = 0.6
	_env.tonemap_mode = Environment.TONE_MAPPER_AGX
	_env.tonemap_exposure = 1.0
	_env.ssao_enabled = true
	_env.ssao_radius = 0.5
	_env.ssao_intensity = 1.2
	_env.ssao_power = 1.4
	_env.ssil_enabled = _high
	_env.ssil_radius = 2.0
	_env.ssil_intensity = 0.8
	_env.ssr_enabled = _high
	_env.ssr_max_steps = 48
	_env.ssr_depth_tolerance = 0.3
	_env.sdfgi_enabled = _high
	_env.sdfgi_use_occlusion = true
	_env.sdfgi_cascades = 3
	_env.sdfgi_min_cell_size = 0.1
	_env.sdfgi_energy = 0.8
	_env.glow_enabled = true
	_env.glow_intensity = 0.35
	_env.glow_bloom = 0.03
	_env.glow_hdr_threshold = 1.2
	_env.fog_enabled = true
	_env.fog_density = 0.0006
	_env.fog_light_color = Color("#b8c4cf")
	_env.fog_aerial_perspective = 0.15
	_env.volumetric_fog_enabled = _high
	_env.volumetric_fog_density = 0.002
	_env.volumetric_fog_albedo = Color("#e8e4dc")
	_env.volumetric_fog_length = 40.0
	_env.adjustment_enabled = true
	_env.adjustment_contrast = 1.12
	_env.adjustment_saturation = 1.05
	we.environment = _env
	if _high:  # tilt-shift miniature look: blur what is far behind the focus
		_cam_attr = CameraAttributesPractical.new()
		var cam := _cam_attr
		cam.dof_blur_far_enabled = true
		cam.dof_blur_far_distance = 22.0
		cam.dof_blur_far_transition = 14.0
		cam.dof_blur_amount = 0.06
		we.camera_attributes = cam
	add_child(we)
	_sun = DirectionalLight3D.new()
	_sun.shadow_enabled = true
	_sun.shadow_blur = 1.5
	_sun.light_angular_distance = 0.6
	_sun.directional_shadow_max_distance = 45.0
	_sun.light_volumetric_fog_energy = 1.5
	add_child(_sun)
	set_hour(10.0)


## PBR material from a vendored Poly Haven texture set, tiled in world space so any mesh size works.
func _pbr(id: String, tint := Color.WHITE) -> StandardMaterial3D:
	var key := "%s/%s" % [id, tint.to_html()]
	if _mats.has(key):
		return _mats[key]
	var res := "2k" if id == "herringbone_parquet" else "1k"
	var base := PH % ("%s/%s_%%s_%s.jpg" % [id, id, res])
	var m := StandardMaterial3D.new()
	m.albedo_texture = load(base % "Diffuse")
	m.albedo_color = tint
	m.normal_enabled = true
	m.normal_texture = load(base % "nor_gl")
	m.roughness_texture = load(base % "Rough")
	m.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE * (1.95 / float(TILE[id]))
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mats[key] = m
	return m


func _glass() -> StandardMaterial3D:
	if not _mats.has("glass"):
		var g := StandardMaterial3D.new()
		g.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		g.albedo_color = Color(0.75, 0.85, 0.9, 0.18)
		g.metallic = 0.2
		g.roughness = 0.03
		g.metallic_specular = 0.9
		_mats["glass"] = g
	return _mats["glass"]


## Swap a Kenney wall's flat paint for plaster and its window pane for real glass.
func _dress_wall(n: Node) -> void:
	for node in n.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		for i in mi.mesh.get_surface_count():
			var mat := mi.mesh.surface_get_material(i)
			var mname := mat.resource_name if mat else ""
			if mname == "_defaultMat":
				mi.set_surface_override_material(i, _pbr("painted_plaster_wall", Color("#efe9df")))
			elif mname == "glass":
				mi.set_surface_override_material(i, _glass())


func _model(path: String, pos: Vector3, rot_deg := 0.0, scale := 1.0) -> Node3D:
	var n: Node3D = load(path).instantiate()
	n.position = pos
	n.rotation_degrees.y = rot_deg
	n.scale = Vector3.ONE * scale
	add_child(n)
	return n


func _plane(rect: Rect2, y: float, color: Color, rough := 0.8, tex := "") -> StandardMaterial3D:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = rect.size
	var mat := StandardMaterial3D.new()
	if tex != "":
		mat = _pbr(tex, color).duplicate()  # own copy: each room floor highlights on its own
	else:
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
	_plane(Rect2(-90, -90, 200, 200), -0.02, Color("#9a9a96"), 0.95, "concrete_pavement")  # ground
	_plane(Rect2(0, 0, 24, 15), 0.0, Color("#9aa3ad"), 0.8, "smooth_concrete_floor")  # office slab
	_plane(Rect2(-12, 15, 48, 2), 0.005, Color("#d8d8d8"), 0.9, "asphalt_02")  # street
	for x in range(-11, 36, 2):  # dashed centre line
		_plane(Rect2(x, 15.97, 1.0, 0.06), 0.008, Color("#d9d4c4"), 0.6)
	_plane(Rect2(-12, 17, 48, 1), 0.02, Color("#c8c8c4"), 0.9, "concrete_pavement")  # far sidewalk
	for x in [2, 8, 14, 20]:
		_model(ROAD % "light-square", Vector3(x, 0.0, 14.8), 0.0, 2.6)
	# prime broker building across the street, flanked by the rival funds' towers
	_model(CITY % "building-e", Vector3(8.5, 0.0, 20.2), 180.0, 3.2)
	for id in RIVALS:
		_build_tower(id)
	var sign := Label3D.new()
	sign.text = "PRIME BROKER"
	sign.font_size = 96
	sign.pixel_size = 0.006
	sign.modulate = Color("#f0c27a")
	sign.outline_size = 16
	sign.billboard = BaseMaterial3D.BILLBOARD_ENABLED  # readable from the office and from street view
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


func _build_tower(id: String) -> void:
	var spec: Array = RIVALS[id]
	var x: float = spec[2]
	var h: float = spec[3]
	_model(CITY % spec[1], Vector3(x, 0.0, 21.0), 180.0, 3.0)
	var label := Label3D.new()
	label.text = spec[0]
	label.font_size = 72
	label.pixel_size = 0.008
	label.outline_size = 18
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true  # never hidden behind a neighbouring tower
	label.position = Vector3(x, h + 1.3, 20.0)
	add_child(label)
	var sign := Label3D.new()
	sign.text = "LIQUIDATING"
	sign.font_size = 80
	sign.pixel_size = 0.008
	sign.outline_size = 18
	sign.modulate = Color("#ff3a2a")
	sign.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sign.no_depth_test = true
	sign.position = Vector3(x, h * 0.5, 18.7)
	sign.visible = false
	add_child(sign)
	var light := OmniLight3D.new()
	light.position = Vector3(x, h * 0.5, 18.2)
	light.omni_range = 6.0
	light.light_color = Color("#ff2a1a")
	light.light_energy = 0.0
	add_child(light)
	_towers[id] = {"beacon": _emissive(Vector3(0.6, 0.35, 0.6), Vector3(x, h + 0.2, 21.0), Color("#2fd36a")),
			"label": label, "sign": sign, "light": light, "status": "", "flash": 0.0}


func _build_rooms() -> void:
	for key in WorldRules.LOCATIONS:
		if key == "broker":
			continue
		var r: Rect2i = WorldRules.LOCATIONS[key]["rect"]
		var fl: Array = FLOORS[key]
		_floor_mats[key] = _plane(Rect2(r.position.x, r.position.y, r.size.x, r.size.y), 0.01, fl[1], 0.6, fl[0])
		if key == "street":  # open-air terrace: no walls or lamp, just the floor and its sign
			_room_label(key, Vector3(r.position.x + r.size.x / 2.0, 1.9, r.position.y + 0.5))
			continue
		# back walls only (cutaway, like a management sim): along the north and west edges
		for x in range(r.size.x):
			var wall := "wallWindow" if (x % 3 == 1 and r.position.y == 2) else "wall"
			var w := _model(F % wall, Vector3(r.position.x + x, 0.0, r.position.y), 0.0)
			w.scale = WALL
			_dress_wall(w)
		for y in range(r.size.y):
			var w := _model(F % "wall", Vector3(r.position.x, 0.0, r.position.y + y + 1), 90.0)
			w.scale = WALL
			_dress_wall(w)
		var lamp := OmniLight3D.new()  # warm ceiling light, above the cutaway walls
		lamp.position = Vector3(r.position.x + r.size.x / 2.0, 1.4, r.position.y + r.size.y / 2.0)
		lamp.omni_range = maxf(r.size.x, r.size.y) * 0.9
		lamp.omni_attenuation = 1.4
		lamp.light_energy = 0.75
		lamp.light_color = Color("#ffd7a8")
		lamp.shadow_enabled = _high
		add_child(lamp)
		_room_label(key, Vector3(r.position.x + r.size.x / 2.0, 1.2, r.position.y + 0.4))


func _room_label(key: String, pos: Vector3) -> void:
	var label := Label3D.new()
	label.text = WorldRules.LOCATIONS[key]["label"]
	label.font_size = 64
	label.pixel_size = 0.005
	label.outline_size = 12
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.position = pos
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
	_model(PH % "potted_plant_04/potted_plant_04_1k.gltf", Vector3(9.4, 0, 2.6), 0.0, 1.8)
	_model(F % "kitchenCoffeeMachine", Vector3(2.4, 0.0, 7.4))
	# committee room: long table with chairs, and the recall letter appears here
	_model(F % "rugRectangle", Vector3(13.5, 0.01, 4.5), 0.0, 1.6)
	_model(F % "tableCross", Vector3(13.5, 0.0, 4.5), 90.0, 1.6)
	for dz in [-0.9, 0.0, 0.9]:
		_model(F % "chairCushion", Vector3(12.6, 0.0, 4.5 + dz), 90.0)
		_model(F % "chairCushion", Vector3(14.4, 0.0, 4.5 + dz), -90.0)
	_model(PH % "potted_plant_04/potted_plant_04_1k.gltf", Vector3(15.4, 0, 2.6), 40.0, 1.8)
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
	_model(PH % "desk_lamp_arm_01/desk_lamp_arm_01_1k.gltf", Vector3(4.2, 0.4, 11.6), 30.0, 0.35)
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
	_model(PH % "desk_lamp_arm_01/desk_lamp_arm_01_1k.gltf", Vector3(10.0, 0.385, 10.2), 200.0, 0.35)
	_model(F % "chairDesk", Vector3(10.4, 0.0, 11.1), 180.0)
	_model(F % "bookcaseClosedWide", Vector3(12.8, 0.0, 9.4))
	_model(F % "sideTableDrawers", Vector3(9.2, 0.0, 9.4))
	_model(F % "cardboardBoxClosed", Vector3(13.2, 0.0, 12.9))
	# investor lounge
	_model(F % "rugRound", Vector3(18.5, 0.01, 11.5), 0.0, 1.8)
	_model(PH % "sofa_03/sofa_03_1k.gltf", Vector3(18.5, 0.0, 9.85), 0.0, M)
	_model(PH % "modern_arm_chair_01/modern_arm_chair_01_1k.gltf", Vector3(17.0, 0.0, 11.6), 90.0, M)
	_model(PH % "modern_arm_chair_01/modern_arm_chair_01_1k.gltf", Vector3(20.0, 0.0, 11.6), -90.0, M)
	_model(F % "tableCoffeeGlass", Vector3(18.5, 0.0, 11.5))
	_model(PH % "potted_plant_04/potted_plant_04_1k.gltf", Vector3(21.4, 0.0, 9.6), 0.0, 1.8)
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
	_sun.light_energy = maxf(0.05, elev) * 2.6
	_sun.light_color = Color("#ffb070").lerp(Color("#fff4e6"), clampf(elev * 1.5, 0.0, 1.0))
	_env.ambient_light_energy = 0.15 + 0.3 * maxf(elev, 0.0)


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
			"rival_alarm": _shake = maxf(_shake, 0.35)
			"rival_blowup":
				for t in traders: t.excited = true
	_apply_league(view)
	var other := "mp" if role == "pm" else "pm"
	var dest := _spot(WorldRules.partner_location(view, other)) + Vector3(0.7, 0, 0.5)
	if partner and partner.position.distance_to(dest) > 1.0 and not partner.is_moving():
		partner.follow(_route(partner.position, dest))


## Rival towers mirror the league table: name, live return, beacon status; a red flash when one turns.
func _apply_league(view: Dictionary) -> void:
	for row in WorldRules.league_rows(view):
		var id: String = row.get("id", "")
		if not _towers.has(id):
			continue
		var tw: Dictionary = _towers[id]
		var status: String = row.get("status", "active")
		var bps: int = row["return_bps"]
		var label: Label3D = tw["label"]
		label.text = "%s
%+d bps" % [row.get("name", RIVALS[id][0]), bps]
		label.modulate = Color("#7dffa8") if bps >= 0 else Color("#ff7a6a")
		(tw["sign"] as Label3D).visible = status == "liquidating"
		var prev: String = tw["status"]
		if prev != "" and prev != status and status in ["deleveraging", "liquidating"]:
			tw["flash"] = 4.0 if status == "liquidating" else 1.5
		tw["status"] = status


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
	if get_viewport().get_meta("forge_terminal_open", false):
		return
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
		if input != Vector2.ZERO and not get_viewport().get_meta("forge_terminal_open", false):
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
		var cam_pos := target + Vector3(sin(_cam_yaw), 0.95, cos(_cam_yaw)).normalized() * _cam_dist
		if _near == "street":  # street view: over the office roofline, facing the rival towers
			target = STREET_LOOK
			cam_pos = STREET_CAM
		var k := minf(1.0, delta * 4.0) if _camera.position != Vector3.ZERO else 1.0
		_camera.position = _camera.position.lerp(cam_pos, k)
		_look = _look.lerp(target, k)
		if _shake > 0.0:
			_shake -= delta
			_camera.position += Vector3(randf_range(-0.08, 0.08), randf_range(-0.05, 0.05), 0)
		_camera.look_at(_look)
		if _cam_attr:  # tilt-shift: focus on what the camera looks at, blur only what is well behind it
			_cam_attr.dof_blur_far_distance = _camera.position.distance_to(_look) + 8.0
			_cam_attr.dof_blur_far_enabled = _near != "street"  # keep rival tower labels sharp
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
		_floor_mats[key].emission_enabled = key == _near
		_floor_mats[key].emission = Color("#ffcf8a") * 0.07
	for id in _towers:
		var tw: Dictionary = _towers[id]
		var flash: float = maxf(0.0, float(tw["flash"]) - delta)
		tw["flash"] = flash
		(tw["beacon"] as StandardMaterial3D).emission = WorldRules.beacon_color(str(tw["status"]) if tw["status"] != "" else "active", _t)
		(tw["light"] as OmniLight3D).light_energy = (3.0 + 3.0 * sin(_t * 14.0)) if flash > 0.0 else 0.0
