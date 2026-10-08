extends SceneTree
## Dev tool: print each model's bounding box (used to scale assets consistently).
##   godot --headless --path game --script res://tests/measure_assets.gd

func _aabb(n: Node, xf: Transform3D) -> AABB:
	var out := AABB()
	var first := true
	var t: Transform3D = xf * ((n as Node3D).transform if n is Node3D else Transform3D())
	if n is MeshInstance3D:
		out = t * (n as MeshInstance3D).get_aabb()
		first = false
	for c in n.get_children():
		var a := _aabb(c, t)
		if a.size != Vector3.ZERO:
			out = a if first else out.merge(a)
			first = false
	return out


func _initialize() -> void:
	for dir in ["furniture", "characters", "city", "roads"]:
		var d := DirAccess.open("res://assets/kenney/" + dir)
		for f in d.get_files():
			if f.ends_with(".glb"):
				var inst: Node = load("res://assets/kenney/%s/%s" % [dir, f]).instantiate()
				var a := _aabb(inst, Transform3D())
				print("%s/%s size=%s pos=%s" % [dir, f, a.size, a.position])
				inst.free()
	quit()
