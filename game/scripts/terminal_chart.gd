class_name TerminalChart
extends Control
## A line of observed marks. Never manufactures OHLC candles or intraday ticks.

var values := PackedFloat32Array()


func _ready() -> void:
	custom_minimum_size = Vector2(0, 240)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	resized.connect(queue_redraw)


func _draw() -> void:
	var font := ThemeDB.fallback_font
	var ink := Color("#89a0b5")
	var area := Rect2(Vector2(76, 20), Vector2(maxf(20, size.x - 98), maxf(20, size.y - 52)))
	draw_rect(Rect2(Vector2.ZERO, size), Color("#080f17"))
	if values.is_empty():
		draw_string(font, Vector2(20, 40), "Waiting for observed marks", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, ink)
		return
	var low := float(values[0])
	var high := low
	for value in values:
		low = minf(low, value)
		high = maxf(high, value)
	var pad := maxf((high - low) * 0.1, maxf(absf(high) * 0.001, 0.01))
	low -= pad
	high += pad
	for i in range(5):
		var y := area.position.y + area.size.y * i / 4.0
		draw_line(Vector2(area.position.x, y), Vector2(area.end.x, y), Color("#203041"))
		draw_string(font, Vector2(4, y + 5), "%.2f" % lerpf(high, low, i / 4.0), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, ink)
	var points := PackedVector2Array()
	for i in range(values.size()):
		points.append(Vector2(area.position.x + area.size.x * i / maxf(1, values.size() - 1),
				area.end.y - (values[i] - low) / (high - low) * area.size.y))
	if points.size() > 1:
		draw_polyline(points, Color("#ffbb55"), 2.0, true)
	draw_circle(points[-1], 4.0, Color("#ffbb55"))
	draw_string(font, Vector2(area.position.x, size.y - 8), "%d observed events   /   latest %.4f" % [values.size(), values[-1]],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 13, ink)
