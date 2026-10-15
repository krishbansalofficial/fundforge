class_name Perf
extends Node
## Frame-time recorder behind `--perf=out.json` (driven by scripts/measure_frames.py).
## Starts once the office world exists, skips `warmup` seconds, then records the wall-clock time between
## consecutive frames for `seconds` and writes a JSON summary. Run with --disable-vsync --max-fps 0 so the
## numbers are the frame's cost, not the display's refresh interval.

var out_path := ""
var warmup := 5.0
var seconds := 30.0
var started_at := -1  # usec when the world appeared; -1 until then
var _last := 0
var _frames := PackedFloat64Array()
var _gpu := PackedFloat64Array()
var _at := PackedFloat64Array()  # seconds since recording began, per frame (to place hitches on the route)
var _marks: Array = []  # [label, usec] for world events (courier, lp_visitor, ...) during the run
var _spans: Array = []  # [label, start usec, duration usec] for timed handlers (main._on_view phases)
var _proc := PackedFloat64Array()  # per recorded frame: process ms, draw calls, objects (to explain hitches)
var _draws := PackedInt32Array()
var _objs := PackedInt32Array()
var _peak := {"draw_calls": 0, "primitives": 0, "objects": 0}
var _sum := {"draw_calls": 0.0, "primitives": 0.0, "objects": 0.0, "process_ms": 0.0, "physics_ms": 0.0}


func _ready() -> void:
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)


## Note a world event so the report can show the worst frame right after it.
func mark(label: String) -> void:
	_marks.append([label, Time.get_ticks_usec()])


## Note how long a handler took (Time.get_ticks_usec() at its start), so hitches can be attributed.
func span(label: String, start_usec: int) -> void:
	_spans.append([label, start_usec, Time.get_ticks_usec() - start_usec])


func _process(_delta: float) -> void:
	var now := Time.get_ticks_usec()
	if started_at < 0:
		if get_parent().get("office") != null:
			started_at = now
			_last = now
			print("perf: world up at %.2f s" % (now / 1e6))  # measure_frames.py --crisis times its skips from this line
		return
	if now - started_at < warmup * 1e6:
		_last = now
		return
	_frames.append((now - _last) / 1000.0)
	_at.append((now - started_at) / 1e6 - warmup)
	_last = now
	_gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(get_viewport().get_viewport_rid()))
	var mon := {"draw_calls": Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME,
			"primitives": Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME, "objects": Performance.RENDER_TOTAL_OBJECTS_IN_FRAME}
	for k in mon:
		var val := int(Performance.get_monitor(mon[k]))
		_peak[k] = maxi(_peak[k], val)
		_sum[k] += val
	_draws.append(int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)))
	_objs.append(int(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)))
	_proc.append(Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0)
	_sum["process_ms"] += _proc[-1]
	_sum["physics_ms"] += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
	if now - started_at >= (warmup + seconds) * 1e6:
		set_process(false)
		_write()
		get_tree().quit()


func _write() -> void:
	var n := float(_frames.size())
	var report := stats(_frames)
	report["gpu_ms_mean"] = snappedf(_mean(_gpu), 0.001)
	report["gpu_ms_p95"] = snappedf(stats(_gpu)["p95_ms"], 0.001)
	for k in _sum:
		report["mean_" + k] = snappedf(_sum[k] / n, 0.01)
	for k in _peak:
		report["max_" + k] = _peak[k]
	var idx := range(_frames.size())
	idx.sort_custom(func(i, j): return _frames[i] > _frames[j])
	report["slowest"] = idx.slice(0, 5).map(func(i): return {"at_s": snappedf(_at[i], 0.01), "ms": snappedf(_frames[i], 0.1)})
	report["events"] = _marks.map(func(m): return _explain(after_event(_at, _frames, (m[1] - started_at) / 1e6 - warmup, m[0])))
	report["world_at_s"] = snappedf(started_at / 1e6, 0.01)  # seconds after engine start that the office appeared
	report["warmup_s"] = warmup
	report["seconds"] = seconds
	report["adapter"] = RenderingServer.get_video_adapter_name()
	report["vendor"] = RenderingServer.get_video_adapter_vendor()
	report["api_version"] = RenderingServer.get_video_adapter_api_version()
	report["driver"] = RenderingServer.get_current_rendering_driver_name()
	report["method"] = RenderingServer.get_current_rendering_method()
	report["resolution"] = "%dx%d" % [get_viewport().get_visible_rect().size.x, get_viewport().get_visible_rect().size.y]
	report["window"] = "%dx%d" % [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y]
	report["vsync"] = DisplayServer.window_get_vsync_mode() != DisplayServer.VSYNC_DISABLED
	report["godot"] = Engine.get_version_info()["string"]
	report["os"] = OS.get_name()
	report["cpu"] = OS.get_processor_name()
	var f := FileAccess.open(out_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	f.close()
	print("perf: wrote ", out_path)


## Adds the worst frame's monitors and the handler spans that ran within 3 s of the event.
func _explain(ev: Dictionary) -> Dictionary:
	var i := -1
	for j in range(_at.size()):
		if snappedf(_at[j], 0.01) == ev["worst_at_s"] and snappedf(_frames[j], 0.1) == ev["worst_ms"]:
			i = j
			break
	if i >= 0:
		ev["worst_process_ms"] = snappedf(_proc[i], 0.01)
		ev["worst_gpu_ms"] = snappedf(_gpu[i], 0.01)
		ev["worst_draw_calls"] = _draws[i]
		ev["worst_objects"] = _objs[i]
	var t: float = ev["event_at_s"]
	var spans: Array = []
	for sp in _spans:
		if absf((sp[1] - started_at) / 1e6 - warmup - t) < 3.0:
			spans.append("%s %.2f ms" % [sp[0], sp[2] / 1000.0])
	ev["spans"] = spans
	return ev


static func _mean(xs: PackedFloat64Array) -> float:
	var s := 0.0
	for x in xs:
		s += x
	return s / xs.size() if xs.size() > 0 else 0.0


## Worst frame within `window` seconds after an event at `t` (recording-relative seconds; negative = during
## warm-up, so not recorded). Returns at_s -1 when no frame was recorded in that window.
static func after_event(at: PackedFloat64Array, frames: PackedFloat64Array, t: float, label: String, window := 3.0) -> Dictionary:
	var worst := -1.0
	var worst_at := -1.0
	for i in range(at.size()):
		if at[i] >= t and at[i] <= t + window and frames[i] > worst:
			worst = frames[i]
			worst_at = at[i]
	return {"event": label, "event_at_s": snappedf(t, 0.01), "worst_ms": snappedf(worst, 0.1), "worst_at_s": snappedf(worst_at, 0.01)}


## Nearest-rank percentiles of frame times in milliseconds.
static func stats(frames_ms: PackedFloat64Array) -> Dictionary:
	var xs := frames_ms.duplicate()
	xs.sort()
	var n := xs.size()
	if n == 0:
		return {"frames": 0, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "worst_ms": 0.0, "mean_ms": 0.0, "mean_fps": 0.0}
	var rank := func(p: float) -> float: return xs[clampi(ceili(p * n) - 1, 0, n - 1)]
	var mean := _mean(xs)
	return {"frames": n, "p50_ms": snappedf(rank.call(0.50), 0.001), "p95_ms": snappedf(rank.call(0.95), 0.001),
			"p99_ms": snappedf(rank.call(0.99), 0.001), "worst_ms": snappedf(xs[n - 1], 0.001),
			"mean_ms": snappedf(mean, 0.001), "mean_fps": snappedf(1000.0 / mean, 0.1)}
