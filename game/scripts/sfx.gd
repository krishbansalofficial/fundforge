class_name Sfx
extends Node
## Sound effects for typed engine events. Every sound is synthesized here from a few tones and seeded
## noise, so there are no audio files, downloads or licences to track (provenance: original, this file).
## Sounds are cosmetic: they follow the server's typed notices and fills and never drive game logic.

const RATE := 22050
const MAX_CUES := 3  # one batch of notices plays at most this many distinct sounds
const SETTINGS := "user://settings.cfg"

## cue -> segments [start_hz, end_hz, offset_s, length_s, wave, gain, decay_per_s]
const CUES := {
	"alarm": [[880, 880, 0.0, 0.18, "square", 0.22, 2.0], [660, 660, 0.2, 0.18, "square", 0.22, 2.0],
			[880, 880, 0.4, 0.18, "square", 0.22, 2.0], [660, 660, 0.6, 0.18, "square", 0.22, 2.0]],
	"crash": [[600, 110, 0.0, 0.7, "sine", 0.45, 3.0], [0, 0, 0.0, 0.35, "noise", 0.18, 9.0]],
	"rally": [[523, 523, 0.0, 0.14, "sine", 0.35, 6.0], [659, 659, 0.12, 0.14, "sine", 0.35, 6.0],
			[784, 784, 0.24, 0.14, "sine", 0.35, 6.0], [1047, 1047, 0.36, 0.3, "sine", 0.35, 5.0]],
	"bell": [[988, 988, 0.0, 0.5, "sine", 0.35, 5.0], [784, 784, 0.22, 0.7, "sine", 0.35, 4.0]],
	"halt": [[90, 60, 0.0, 0.45, "sine", 0.6, 6.0], [0, 0, 0.0, 0.12, "noise", 0.25, 25.0]],
	"chime": [[1320, 1320, 0.0, 0.7, "sine", 0.25, 4.5], [2640, 2640, 0.0, 0.4, "sine", 0.08, 8.0]],
	"cash": [[1568, 1568, 0.0, 0.07, "square", 0.15, 10.0], [2093, 2093, 0.09, 0.12, "square", 0.15, 10.0]],
	"rival": [[140, 50, 0.0, 0.9, "sine", 0.35, 2.5], [0, 0, 0.05, 0.5, "noise", 0.08, 5.0]],
	"fill": [[1500, 1400, 0.0, 0.04, "sine", 0.25, 40.0]],
}

## world effect (WorldRules.EFFECTS) -> cue
const EFFECT_CUES := {
	"alarm": "alarm", "screens_red": "crash", "screens_green": "rally", "courier": "bell",
	"letter_committee": "bell", "lp_visitor": "bell", "courier_back": "bell", "halt_board": "halt",
	"halt_warning": "bell", "research_glow": "chime", "cash_out": "cash", "rival_alarm": "rival",
	"rival_blowup": "rival",
}

var muted := false
var _players: Array[AudioStreamPlayer] = []
var _streams := {}


## 16-bit little-endian mono PCM for a cue at RATE. Deterministic: the noise uses a fixed-seed LCG.
static func synth(cue: String) -> PackedByteArray:
	var segments: Array = CUES.get(cue, [])
	var length := 0.0
	for s in segments:
		length = maxf(length, float(s[2]) + float(s[3]))
	var n := int(ceil(length * RATE))
	var mix := PackedFloat32Array()
	mix.resize(n)
	var lcg := 0x2545F491
	for s in segments:
		var f0 := float(s[0])
		var f1 := float(s[1])
		var start := int(float(s[2]) * RATE)
		var count := int(float(s[3]) * RATE)
		var phase := 0.0
		for i in count:
			var t := float(i) / RATE
			var hz := lerpf(f0, f1, float(i) / count)
			phase += TAU * hz / RATE
			var v := 0.0
			match str(s[4]):
				"sine": v = sin(phase)
				"square": v = 1.0 if sin(phase) >= 0.0 else -1.0
				"noise":
					lcg = (lcg * 1103515245 + 12345) & 0x7fffffff
					v = float(lcg) / 0x3fffffff - 1.0
			var attack := minf(1.0, t / 0.005)  # 5 ms ramp, no click
			var release := minf(1.0, float(count - i) / (0.01 * RATE))
			if start + i < n:
				mix[start + i] += v * float(s[5]) * exp(-float(s[6]) * t) * attack * release
	var out := PackedByteArray()
	out.resize(n * 2)
	for i in n:
		out.encode_s16(i * 2, int(clampf(mix[i], -1.0, 1.0) * 32767.0))
	return out


## Distinct cues for a batch of world effects, in order, at most MAX_CUES.
static func cues_for(effects: Array) -> Array:
	var out: Array = []
	for e in effects:
		var cue: String = EFFECT_CUES.get(e, "")
		if cue != "" and cue not in out and out.size() < MAX_CUES:
			out.append(cue)
	return out


## Executed (non-rejected) fills across the view's orders; a rise means trades just printed.
static func fill_count(view: Dictionary) -> int:
	var n := 0
	for o in view.get("orders", []):
		for f in o.get("fills", []):
			if not f.has("rejected"):
				n += 1
	return n


func _ready() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS) == OK:
		muted = bool(cfg.get_value("audio", "muted", false))
	for i in MAX_CUES + 1:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)


func play(cue: String) -> void:
	if muted or not CUES.has(cue):
		return
	if not _streams.has(cue):
		var w := AudioStreamWAV.new()
		w.format = AudioStreamWAV.FORMAT_16_BITS
		w.mix_rate = RATE
		w.stereo = false
		w.data = synth(cue)
		_streams[cue] = w
	for p in _players:
		if not p.playing:
			p.stream = _streams[cue]
			p.play()
			return


func play_effects(effects: Array) -> void:
	for cue in cues_for(effects):
		play(cue)


func set_muted(value: bool) -> void:
	muted = value
	if muted:
		for p in _players:
			p.stop()
	var cfg := ConfigFile.new()
	cfg.load(SETTINGS)
	cfg.set_value("audio", "muted", muted)
	cfg.save(SETTINGS)
