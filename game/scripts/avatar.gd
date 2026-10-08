class_name Avatar
extends Node2D
## A walking person in the iso world: a partner, a trader, a courier or a visiting LP.

signal arrived

var grid_pos := Vector2.ZERO
var path: Array[Vector2] = []
var speed := 3.0  # tiles per second
var body_color := Color("#d9d2c3")
var accent := Color("#16263a")
var label_text := ""
var carrying := false  # draws a letter/document in hand
var panic := false
var free_after_path := false

var _t := 0.0
var _moving := false
var _label: Label


func _ready() -> void:
	if label_text != "":
		_label = Label.new()
		_label.text = label_text
		_label.add_theme_font_size_override("font_size", 13)
		_label.add_theme_color_override("font_color", Color.WHITE)
		_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
		_label.add_theme_constant_override("outline_size", 4)
		_label.position = Vector2(-60, -64)
		_label.size = Vector2(120, 18)
		_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		add_child(_label)
	_sync()


func place(grid: Vector2) -> void:
	grid_pos = grid
	path.clear()
	_sync()


func walk_to(grid: Vector2) -> void:
	path = [WorldRules.clamp_to_world(grid)]


func follow(points: Array) -> void:
	path.clear()
	for p in points:
		path.append(p)


func is_moving() -> bool:
	return _moving


func _process(delta: float) -> void:
	_t += delta
	_moving = not path.is_empty()
	if _moving:
		var target: Vector2 = path[0]
		var step := speed * delta
		var to := target - grid_pos
		if to.length() <= step:
			grid_pos = target
			path.pop_front()
			if path.is_empty():
				arrived.emit()
				if free_after_path:
					queue_free()
		else:
			grid_pos += to.normalized() * step
	_sync()
	queue_redraw()


func _sync() -> void:
	position = WorldRules.to_screen(grid_pos)
	z_index = int(grid_pos.x + grid_pos.y) * 10 + 5


func _draw() -> void:
	var bob := 0.0
	if _moving:
		bob = absf(sin(_t * 12.0)) * 3.0
	elif panic:
		bob = absf(sin(_t * 20.0)) * 4.0
	else:
		bob = sin(_t * 2.0) * 0.8
	# shadow
	draw_set_transform(Vector2(0, 2), 0.0, Vector2(1.0, 0.45))
	draw_circle(Vector2.ZERO, 11.0, Color(0, 0, 0, 0.28))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# legs, body, head
	var lift := Vector2(0, -bob)
	draw_rect(Rect2(Vector2(-6, -14) + lift, Vector2(4, 14)), accent.darkened(0.3))
	draw_rect(Rect2(Vector2(2, -14) + lift, Vector2(4, 14)), accent.darkened(0.3))
	draw_rect(Rect2(Vector2(-9, -36) + lift, Vector2(18, 23)), accent)
	draw_rect(Rect2(Vector2(-2, -36) + lift, Vector2(4, 9)), body_color.lightened(0.5))
	draw_circle(Vector2(0, -44) + lift, 8.0, body_color)
	if carrying:
		draw_rect(Rect2(Vector2(8, -28) + lift, Vector2(12, 9)), Color("#f4efe2"))
		draw_line(Vector2(8, -28) + lift, Vector2(14, -23) + lift, Color("#a9281f"), 1.5)
		draw_line(Vector2(20, -28) + lift, Vector2(14, -23) + lift, Color("#a9281f"), 1.5)
