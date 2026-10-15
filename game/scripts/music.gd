class_name Music
extends Node
## Background music, written for this project and synthesized here like the effects in sfx.gd: no files,
## downloads or licences. One deterministic loop (A minor, i-VI-III-VII at 90 bpm): a plucked bass, a soft
## pad and an arpeggio whose note order comes from a fixed-seed LCG. Cosmetic only; it drives nothing.

const RATE := 22050
const BPM := 90.0
const BEATS_PER_CHORD := 4
## Chord roots and triads in Hz: Am, F, C, G.
const CHORDS := [[110.0, [220.0, 261.63, 329.63]], [87.31, [174.61, 220.0, 261.63]],
		[130.81, [261.63, 329.63, 392.0]], [98.0, [196.0, 246.94, 293.66]]]
## Music volume steps for the HUD toggle: off, low, normal (linear gain).
const LEVELS := [0.0, 0.35, 0.7]
const LEVEL_NAMES := ["off", "low", "on"]

static var _stream: AudioStreamWAV  # synthesized once per process

var level := 2
var _player: AudioStreamPlayer


static func loop_seconds() -> float:
	return CHORDS.size() * BEATS_PER_CHORD * 60.0 / BPM


## 16-bit little-endian mono PCM for the whole loop. Every chord's notes end at its boundary, so the loop
## point is silent-to-silent and does not click.
static func synth() -> PackedByteArray:
	var beat := 60.0 / BPM
	var n := int(round(loop_seconds() * RATE))
	var mix := PackedFloat32Array()
	mix.resize(n)
	var lcg := 0x1F2E3D4C
	var chord_len := BEATS_PER_CHORD * beat
	for c in CHORDS.size():
		var root: float = CHORDS[c][0]
		var triad: Array = CHORDS[c][1]
		var t0 := c * chord_len
		for b in BEATS_PER_CHORD:  # bass pluck on every beat
			_note(mix, t0 + b * beat, beat, root, 0.30, 4.0)
		for hz in triad:  # pad: whole chord, slow swell, very quiet
			_note(mix, t0, chord_len, hz, 0.06, 0.0, 0.4)
		for e in BEATS_PER_CHORD * 2:  # arpeggio in eighths, one octave up
			lcg = (lcg * 1103515245 + 12345) & 0x7fffffff
			_note(mix, t0 + e * beat / 2.0, beat / 2.0, float(triad[lcg % triad.size()]) * 2.0, 0.10, 7.0)
	var out := PackedByteArray()
	out.resize(n * 2)
	for i in n:
		out.encode_s16(i * 2, int(clampf(mix[i], -1.0, 1.0) * 32767.0))
	return out


## Adds one sine note: 5 ms (or `attack` s) ramp in, exponential decay, 15 ms ramp out before `length` ends.
static func _note(mix: PackedFloat32Array, start_s: float, length: float, hz: float, gain: float, decay: float,
		attack := 0.005) -> void:
	var start := int(round(start_s * RATE))
	var count := mini(int(length * RATE), mix.size() - start)
	var step := TAU * hz / RATE
	for i in count:
		var t := float(i) / RATE
		var env := minf(1.0, t / attack) * minf(1.0, float(count - 1 - i) / (0.015 * RATE)) * exp(-decay * t)
		mix[start + i] += sin(step * i) * gain * env


static func next_level(current: int) -> int:
	return (current + 1) % LEVELS.size()


## Music plays only when the global mute is off and the music level is above zero.
static func audible(muted: bool, music_level: int) -> bool:
	return not muted and music_level > 0 and music_level < LEVELS.size()


func _ready() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(Sfx.SETTINGS) == OK:
		level = clampi(int(cfg.get_value("audio", "music_level", level)), 0, LEVELS.size() - 1)
	_player = AudioStreamPlayer.new()
	add_child(_player)


## Start, stop or re-level the loop for the current global mute. Synthesizes on first audible use only.
func refresh(muted: bool) -> void:
	if not audible(muted, level):
		_player.stop()
		return
	if _stream == null:
		_stream = AudioStreamWAV.new()
		_stream.format = AudioStreamWAV.FORMAT_16_BITS
		_stream.mix_rate = RATE
		_stream.stereo = false
		_stream.data = synth()
		_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		_stream.loop_end = _stream.data.size() / 2
	_player.volume_db = linear_to_db(LEVELS[level])
	if not _player.playing:
		_player.stream = _stream
		_player.play()


func cycle(muted: bool) -> void:
	level = next_level(level)
	var cfg := ConfigFile.new()
	cfg.load(Sfx.SETTINGS)
	cfg.set_value("audio", "music_level", level)
	cfg.save(Sfx.SETTINGS)
	refresh(muted)
