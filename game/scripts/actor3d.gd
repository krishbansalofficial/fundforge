class_name Actor3D
extends Node3D
## An animated 3D person (Kenney Blocky Characters): partner, trader, courier or LP.

signal arrived

const SCALE := 0.3

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
	_model = load("res://assets/kenney/characters/character-%s.glb" % model).instantiate()
	_model.scale = Vector3.ONE * SCALE
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
		_label.position = Vector3(0, 1.05, 0)
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


func _play(name: String) -> void:
	if _anim and _current != name and _anim.has_animation(name):
		_anim.play(name, 0.2)
		_current = name


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
