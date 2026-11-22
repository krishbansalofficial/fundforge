class_name TerminalChart
extends Control
## Lines of observed marks. Never manufactures OHLC candles or intraday ticks.
## `values` is the single-security chart; `series` (label -> values) overlays several (COMP).

const COLORS := [Color("#ffbb55"), Color("#6cdfaa"), Color("#7cb8ff"), Color("#ff817c"), Color("#d79cff"), Color("#e8e8e8")]

var values := PackedFloat32Array()
var series: Dictionary = {}
var x_range: Array = []  # optional [first label, last label], e.g. ["D12", "D18"]


func _ready() -> void:
	custom_minimum_size = Vector2(0, 240)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	resized.connect(queue_redraw)


func _lines() -> Dictionary:
	return series if not series.is_empty() else ({"": values} if not values.is_empty() else {})


func _draw() -> void:
	var font := ThemeDB.fallback_font
	var ink := Color("#89a0b5")
	var area := Rect2(Vector2(76, 20), Vector2(maxf(20, size.x - 98), maxf(20, size.y - 52)))
	draw_rect(Rect2(Vector2.ZERO, size), Color("#080f17"))
	var lines := _lines()
	var low := INF
	var high := -INF
	var longest := 0
	for key in lines:
		for value in lines[key]:
			low = minf(low, value)
			high = maxf(high, value)
		longest = maxi(longest, lines[key].size())
	if longest == 0:
		draw_string(font, Vector2(20, 40), "Waiting for observed marks", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, ink)
		return
	var pad := maxf((high - low) * 0.1, maxf(absf(high) * 0.001, 0.01))
	low -= pad
	high += pad
	for i in range(5):
		var y := area.position.y + area.size.y * i / 4.0
		draw_line(Vector2(area.position.x, y), Vector2(area.end.x, y), Color("#203041"))
		draw_string(font, Vector2(4, y + 5), "%.2f" % lerpf(high, low, i / 4.0), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, ink)
	var n := 0
	var legend_x := area.position.x
	for key in lines:
		var vals: PackedFloat32Array = lines[key]
		var color: Color = COLORS[n % COLORS.size()]
		n += 1
		if vals.is_empty():
			continue
		var points := PackedVector2Array()
		for i in range(vals.size()):
			points.append(Vector2(area.position.x + area.size.x * i / maxf(1, longest - 1),
					area.end.y - (vals[i] - low) / (high - low) * area.size.y))
		if points.size() > 1:
			draw_polyline(points, color, 2.0, true)
		draw_circle(points[-1], 4.0, color)
		if key != "":
			var tag := "%s %.2f" % [key, vals[-1]]
			draw_string(font, Vector2(legend_x, 14), tag, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, color)
			legend_x += font.get_string_size(tag, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x + 18
	if x_range.size() == 2:
		draw_string(font, Vector2(area.position.x, area.end.y + 16), str(x_range[0]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, ink)
		var last := str(x_range[1])
		draw_string(font, Vector2(area.end.x - font.get_string_size(last, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x, area.end.y + 16),
				last, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, ink)
	var footer := "%d observed events" % longest
	if lines.size() == 1:
		var only: PackedFloat32Array = lines.values()[0]
		footer += "   /   latest %.4f" % only[-1]
	var fw := font.get_string_size(footer, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x
	draw_string(font, Vector2(area.position.x + (area.size.x - fw) / 2.0, size.y - 8), footer, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, ink)
