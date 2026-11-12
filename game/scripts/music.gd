class_name Music
extends Node
## Background music, written for this project and synthesized here like the effects in sfx.gd: no files,
## downloads or licences. Three deterministic loops (a plucked bass, a soft pad and an arpeggio whose note
## order comes from a fixed-seed LCG) picked by mood_for() from public view state. Cosmetic only.
## Loops render a bounded slice per frame and stream through an AudioStreamGenerator, so nothing stalls.

const RATE := 22050
const BEATS_PER_CHORD := 4
## mood -> bpm, chords [[root_hz, [triad_hz...]]...], bass hits and arpeggio notes per chord, pad gain, seed.
const MOODS := {
	"calm": {"bpm": 90.0, "bass": 4, "arp": 8, "pad": 0.06, "seed": 0x1F2E3D4C,  # Am F C G
		"chords": [[110.0, [220.0, 261.63, 329.63]], [87.31, [174.61, 220.0, 261.63]],
			[130.81, [261.63, 329.63, 392.0]], [98.0, [196.0, 246.94, 293.66]]]},
	"tense": {"bpm": 104.0, "bass": 8, "arp": 8, "pad": 0.05, "seed": 0x5A17C0DE,  # Am Bb Am E: pulsing bass
		"chords": [[110.0, [220.0, 261.63, 329.63]], [116.54, [233.08, 293.66, 349.23]],
			[110.0, [220.0, 261.63, 329.63]], [82.41, [164.81, 207.65, 246.94]]]},
	"resolved": {"bpm": 72.0, "bass": 2, "arp": 4, "pad": 0.07, "seed": 0x00C0FFEE,  # C F G C: slow, major
		"chords": [[130.81, [261.63, 329.63, 392.0]], [87.31, [174.61, 220.0, 261.63]],
			[98.0, [196.0, 246.94, 293.66]], [130.81, [261.63, 329.63, 392.0]]]},
}
## Music volume steps for the HUD toggle: off, low, normal (linear gain).
const LEVELS := [0.0, 0.35, 0.7]
const LEVEL_NAMES := ["off", "low", "on"]
const RENDER_BUDGET := 3000  # note-sample additions per frame (~0.6 ms measured); a loop is 1.1-1.5M, so 6-8 s at 60 fps
const PUSH_MAX := 1024  # stereo frames pushed per frame; 60 fps consumes ~368
const FADE_S := 2.0

static var _loops := {}  # mood -> PackedFloat32Array, rendered once per process

var level := 2
var mood := "calm"  # target; _cur follows once its loop has rendered
var _player: AudioStreamPlayer
var _playback: AudioStreamGeneratorPlayback
var _job := {}
var _cur := ""
var _pos := 0
var _old := ""
var _old_pos := 0
var _fade := 1.0


## Mood from public view state: the ending resolves; a margin call, thin headroom, a firm that cannot cover
## payroll or a fresh alert notice is tense; otherwise calm.
static func mood_for(view: Dictionary) -> String:
	var clock: Dictionary = view.get("clock", {})
	if clock.get("finished", false):
		return "resolved"
	var fund: Dictionary = view.get("fund", {})
	if fund.get("margin_call") != null or (fund.has("maintenance_req") and WorldRules.headroom_ratio(fund) < 1.05):
		return "tense"
	var firm: Dictionary = view.get("firm", {})
	if float(firm.get("cash", "0")) < float(firm.get("payroll_payable", "0")):
		return "tense"
	var notices: Array = view.get("notices", [])
	if notices.size() > 0 and notices[-1].get("kind", "") == "alert" and notices[-1].get("day", -1) == clock.get("day", -2):
		return "tense"
	return "calm"


static func loop_seconds(m: String) -> float:
	return MOODS[m]["chords"].size() * BEATS_PER_CHORD * 60.0 / MOODS[m]["bpm"]


## Every note as [start_sample, count, hz, gain, decay_per_s, attack_s]. Notes end at their chord's
## boundary, so the loop point is silent-to-silent and does not click.
static func notes(m: String) -> Array:
	var p: Dictionary = MOODS[m]
	var n := int(round(loop_seconds(m) * RATE))
	var chord_len := BEATS_PER_CHORD * 60.0 / float(p["bpm"])
	var lcg: int = p["seed"]
	var out: Array = []
	var add := func(start_s: float, length: float, hz: float, gain: float, decay: float, attack: float):
		var start := int(round(start_s * RATE))
		out.append([start, mini(int(length * RATE), n - start), hz, gain, decay, attack])
	for c in p["chords"].size():
		var root: float = p["chords"][c][0]
		var triad: Array = p["chords"][c][1]
		var t0: float = c * chord_len
		for b in p["bass"]:
			add.call(t0 + b * chord_len / p["bass"], chord_len / p["bass"], root, 0.30, 4.0, 0.005)
		for hz in triad:  # pad: whole chord, slow swell, very quiet
			add.call(t0, chord_len, hz, p["pad"], 0.0, 0.4)
		for e in p["arp"]:  # arpeggio one octave up
			lcg = (lcg * 1103515245 + 12345) & 0x7fffffff
			add.call(t0 + e * chord_len / p["arp"], chord_len / p["arp"], float(triad[lcg % triad.size()]) * 2.0, 0.10, 7.0, 0.005)
	return out


static func new_job(m: String) -> Dictionary:
	var mix := PackedFloat32Array()
	mix.resize(int(round(loop_seconds(m) * RATE)))
	return {"mood": m, "mix": mix, "notes": notes(m), "i": 0, "off": 0}


## Renders at most `budget` note-samples of the job; returns how many it did. Order matches a one-shot
## render exactly, so chunked output is bit-identical.
static func render_step(job: Dictionary, budget: int) -> int:
	var used := 0
	var mix: PackedFloat32Array = job["mix"]
	job["mix"] = PackedFloat32Array()  # drop the dict's reference so writes don't copy the whole loop
	while job["i"] < job["notes"].size() and used < budget:
		var nt: Array = job["notes"][job["i"]]
		var a: int = job["off"]
		var b := mini(nt[1], a + budget - used)
		var start: int = nt[0]
		var count: int = nt[1]
		var step := TAU * float(nt[2]) / RATE
		var gain: float = nt[3]
		var decay: float = nt[4]
		var attack: float = nt[5]
		for i in range(a, b):
			var t := float(i) / RATE
			var env := minf(1.0, t / attack) * minf(1.0, float(count - 1 - i) / (0.015 * RATE)) * exp(-decay * t)
			mix[start + i] += sin(step * i) * gain * env
		used += b - a
		job["off"] = b
		if b >= count:
			job["i"] += 1
			job["off"] = 0
	job["mix"] = mix
	return used


static func done(job: Dictionary) -> bool:
	return job["i"] >= job["notes"].size()


## The whole loop in one call (tests and tools only; the game renders it in slices).
static func synth(m: String) -> PackedFloat32Array:
	var job := new_job(m)
	render_step(job, 1 << 40)
	return job["mix"]


static func next_level(current: int) -> int:
	return (current + 1) % LEVELS.size()


## Music plays only when the global mute is off and the music level is above zero.
static func audible(muted: bool, music_level: int) -> bool:
	return not muted and music_level > 0 and music_level < LEVELS.size()


func _ready() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(Sfx.SETTINGS) == OK:
		level = clampi(int(cfg.get_value("audio", "music_level", level)), 0, LEVELS.size() - 1)
	var gen := AudioStreamGenerator.new()
	gen.mix_rate = RATE
	gen.buffer_length = 0.5  # rides out a half-second hitch before underrunning
	_player = AudioStreamPlayer.new()
	_player.stream = gen
	add_child(_player)


func set_mood(m: String) -> void:
	if MOODS.has(m):
		mood = m


## Start, stop or re-level playback for the current global mute. Nothing renders while inaudible.
func refresh(muted: bool) -> void:
	if not audible(muted, level):
		_player.stop()
		return
	_player.volume_db = linear_to_db(LEVELS[level])
	if not _player.playing:
		_player.play()
		_playback = _player.get_stream_playback()


func cycle(muted: bool) -> void:
	level = next_level(level)
	var cfg := ConfigFile.new()
	cfg.load(Sfx.SETTINGS)
	cfg.set_value("audio", "music_level", level)
	cfg.save(Sfx.SETTINGS)
	refresh(muted)


func _process(_delta: float) -> void:
	if not _player.playing:
		return
	tick(_playback.get_frames_available())


## One frame of work: render a bounded slice of a missing loop, switch to the target mood once it is ready,
## and return at most PUSH_MAX frames for the generator (pushed when a playback is live).
func tick(frames_available: int) -> PackedVector2Array:
	if not _loops.has(mood):
		if _job.get("mood", "") != mood:
			_job = new_job(mood)
		render_step(_job, RENDER_BUDGET)
		if done(_job):
			_loops[mood] = _job["mix"]
			_job = {}
	elif _cur != mood:
		_old = _cur
		_old_pos = _pos
		_fade = 0.0 if _cur != "" else 1.0
		_cur = mood
		_pos = 0
	if _cur == "":
		return PackedVector2Array()
	var out := _fill(mini(frames_available, PUSH_MAX))
	if _playback and out.size() > 0:
		_playback.push_buffer(out)
	return out


## Next `n` stereo frames of the current loop, crossfading in from the previous mood over FADE_S.
func _fill(n: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	out.resize(n)
	var a: PackedFloat32Array = _loops[_cur]
	var b: PackedFloat32Array = _loops.get(_old, PackedFloat32Array())
	var df := 1.0 / (FADE_S * RATE)
	for i in n:
		var s := a[_pos]
		if _fade < 1.0:
			s = s * _fade + b[_old_pos] * (1.0 - _fade)
			_old_pos = (_old_pos + 1) % b.size()
			_fade = minf(1.0, _fade + df)
		_pos = (_pos + 1) % a.size()
		s = clampf(s, -1.0, 1.0)
		out[i] = Vector2(s, s)
	return out
