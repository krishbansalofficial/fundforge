class_name Actor3D
extends Node3D
## An animated 3D person (Quaternius CC0 humans; Kenney Blocky Characters as fallback).

signal arrived

## One world unit is ~1.95 m (a 0.75 m Kenney desk is 0.384 high), so a 1.75 m person is ~0.9 units tall.
const HUMAN_HEIGHT := 0.9
const Q := "res://assets/quaternius/%s.glb"
## Kenney letter code -> [model path, height of that model at scale 1].
const MODELS := {
	"a": [Q % "business_man", 1.857], "b": [Q % "woman_casual", 1.852],
	"k": [Q % "worker", 1.866], "m": [Q % "woman_red", 1.852],
}
const TRADER := [Q % "man_suit", 4.84]  # the only male rig with a seated clip
## Wanted clip -> candidate clip names (suffix after "Armature|"), first match wins, else idle.
const CLIPS := {
	"idle": ["idle", "Idle", "Man_Idle", "Idle_Neutral", "Man_Standing"],
	"walk": ["walk", "Walk", "Man_Walk", "Walking"],
	"sprint": ["sprint", "Run", "Man_Run", "Running"],
	"sit": ["sit", "Man_Sitting", "SitIdle", "Sitting"],
	"emote-yes": ["emote-yes", "Wave", "Man_Clapping", "Interact"],
}

var path: Array[Vector3] = []
var speed := 2.6
var free_after_path := false
var seated := false
var excited := false

var _anim: AnimationPlayer
var _model: Node3D
var _label: Label3D
var _letter: MeshInstance3D
var _current := ""


func setup(model: String, label: String, label_color := Color.WHITE) -> Actor3D:
	var spec: Array = MODELS.get(model, TRADER)
	var path: String = spec[0]
	var h: float = spec[1]
	if not ResourceLoader.exists(path):  # fallback: the original Kenney blocky character
		path = "res://assets/kenney/characters/character-%s.glb" % model
		h = 2.7
	_model = load(path).instantiate()
	_model.scale = Vector3.ONE * (HUMAN_HEIGHT / h)
	add_child(_model)
	_anim = _model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if label != "":
		_label = Label3D.new()
		_label.text = label
		_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_label.no_depth_test = true
		_label.font_size = 40
		_label.outline_size = 10
		_label.modulate = label_color
		_label.position = Vector3(0, HUMAN_HEIGHT + 0.2, 0)
		_label.pixel_size = 0.004
		add_child(_label)
	return self


func carry_letter(on: bool) -> void:
	if on and _letter == null:
		_letter = MeshInstance3D.new()
		var m := BoxMesh.new()
		m.size = Vector3(0.18, 0.12, 0.01)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color("#f4efe2")
		mat.emission_enabled = true
		mat.emission = Color("#ffe9b0")
		mat.emission_energy_multiplier = 0.4
		m.material = mat
		_letter.mesh = m
		_letter.position = Vector3(0.16, 0.45, 0.1)
		add_child(_letter)
	elif not on and _letter:
		_letter.queue_free()
		_letter = null


func place(p: Vector3) -> void:
	position = p
	path.clear()


func walk_to(p: Vector3) -> void:
	path = [p]


func follow(points: Array) -> void:
	path.clear()
	for p in points:
		path.append(p)


func is_moving() -> bool:
	return not path.is_empty()


func _clip(want: String) -> String:
	if _anim == null:
		return ""
	var names := _anim.get_animation_list()
	for cand in CLIPS.get(want, [want]) + CLIPS["idle"]:
		for n in names:
			if n == cand or n.ends_with("|" + cand):
				return n
	return ""


func _play(want: String) -> void:
	if _anim == null or _current == want:
		return
	var clip := _clip(want)
	if clip != "":
		_anim.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
		_anim.play(clip, 0.2)
	_current = want


func _process(delta: float) -> void:
	if path.is_empty():
		_play("sit" if seated else ("emote-yes" if excited else "idle"))
		return
	var target: Vector3 = path[0]
	var to := target - position
	to.y = 0.0
	var step := speed * delta
	if to.length() <= step:
		position = Vector3(target.x, position.y, target.z)
		path.pop_front()
		if path.is_empty():
			arrived.emit()
			if free_after_path:
				queue_free()
	else:
		position += to.normalized() * step
		var look := position + to.normalized()
		look_at(Vector3(look.x, position.y, look.z), Vector3.UP, true)
		_play("walk" if speed < 3.5 else "sprint")
