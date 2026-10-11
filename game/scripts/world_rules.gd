class_name WorldRules
extends RefCounted
## Pure presentation rules: no rendering, no network, so they can be unit-tested headless.
## The world only *reflects* server state; nothing here can change money, time or outcomes.

const TILE_W := 64.0
const TILE_H := 32.0

## Wall-clock hour of each engine phase (simulated scenario timestamps, see SCENARIO_CONTRACTS).
const PHASE_HOUR := {"OPEN_ADMIN": 8.0, "PUBLIC_MARK": 9.5, "EXEC_A": 10.0, "EXEC_B": 15.0, "CLOSE": 16.0}

## Places in the office/city. Each is a decision location that opens its panel.
const LOCATIONS := {
	"trading": {"label": "Trading floor", "rect": Rect2i(2, 2, 8, 6), "spot": Vector2(6, 7), "color": Color("#2b3f57")},
	"committee": {"label": "Committee room", "rect": Rect2i(11, 2, 5, 5), "spot": Vector2(13.5, 6), "color": Color("#4a3b2c")},
	"risk": {"label": "Risk and treasury", "rect": Rect2i(17, 2, 5, 5), "spot": Vector2(19.5, 6), "color": Color("#3d2b30")},
	"research": {"label": "Research library", "rect": Rect2i(2, 9, 5, 5), "spot": Vector2(4.5, 10), "color": Color("#2f4231")},
	"backoffice": {"label": "Management company", "rect": Rect2i(8, 9, 6, 5), "spot": Vector2(11, 10), "color": Color("#3a3a46")},
	"lp": {"label": "Investor lounge", "rect": Rect2i(15, 9, 7, 5), "spot": Vector2(18.5, 10), "color": Color("#463c2a")},
	"broker": {"label": "Prime broker", "rect": Rect2i(5, 18, 7, 4), "spot": Vector2(8.5, 18), "color": Color("#29404a")},
	"street": {"label": "Street view", "rect": Rect2i(0, 14, 5, 1), "spot": Vector2(2.5, 14.5), "color": Color("#3a4450")},
}
## Menu scenarios: [Store scenario key, label]. Keys must match backend store.SCENARIOS.
const SCENARIOS := [
	["case1", "Case 1: standard crisis"],
	["case1-controls", "Broker review challenge: investigate a cash statement error in Terminal RISK"],
	["case1-settlement", "Settlement failure: a tight credit line fails a BUY settlement; follow the retry in RISK"],
	["case1-generated", "Generated market: Case 1's crisis on a fresh seeded price path (seed revealed at the end)"],
]
const STREET := Rect2i(0, 15, 24, 2)
const WORLD := Rect2i(0, 0, 24, 23)

## Which location a partner's last decision puts them in (for the remote partner's avatar).
const COMMAND_LOCATION := {
	"ticket": "trading", "propose": "committee", "sign": "committee", "cancel": "trading",
	"research": "research", "accept_replacement": "broker", "set_reserve": "risk",
	"set_speed": "committee", "pause": "committee",
}

## World reactions to typed notice codes from the engine.
const EFFECTS := {
	"recall": ["courier", "letter_committee"],
	"market_shock": ["screens_red", "panic", "shake"],
	"market_rally": ["screens_green", "cheer"],
	"margin_call": ["alarm"],
	"trading_halt": ["halt_board"],
	"halt_risk": ["halt_warning"],
	"redemption_notice": ["lp_visitor"],
	"redemption_dealt": ["lp_visitor", "cash_out"],
	"research_reveal": ["research_glow"],
	"replacement_settled": ["courier_back"],
	"rival_deleveraging": ["rival_alarm"],
	"rival_blowup": ["rival_blowup", "shake"],
}


static func to_screen(grid: Vector2) -> Vector2:
	return Vector2((grid.x - grid.y) * TILE_W / 2.0, (grid.x + grid.y) * TILE_H / 2.0)


static func to_grid(screen: Vector2) -> Vector2:
	var a := screen.x / (TILE_W / 2.0)
	var b := screen.y / (TILE_H / 2.0)
	return Vector2((a + b) / 2.0, (b - a) / 2.0)


static func location_at(grid: Vector2) -> String:
	for key in LOCATIONS:
		var r: Rect2i = LOCATIONS[key]["rect"]
		if Rect2(r).has_point(grid):
			return key
	return ""


static func clamp_to_world(grid: Vector2) -> Vector2:
	return Vector2(clampf(grid.x, 0.3, WORLD.size.x - 0.3), clampf(grid.y, 0.3, WORLD.size.y - 0.3))


## Interpolated in-world hour between the current phase and the next one, driven by the server's
## schedule (`realtime.next_tick_in` measured when the view arrived). Purely cosmetic.
static func clock_hour(view: Dictionary, seconds_since_view: float) -> float:
	var clock: Dictionary = view.get("clock", {})
	var now_h: float = PHASE_HOUR.get(clock.get("phase", "OPEN_ADMIN"), 8.0)
	var nxt = clock.get("next")
	var rt: Dictionary = view.get("realtime", {})
	if nxt == null or not rt.get("running", false):
		return now_h
	var next_h: float = PHASE_HOUR.get(nxt.get("phase", "CLOSE"), now_h)
	if nxt.get("day", 0) != clock.get("day", 0):
		next_h += 24.0
	var window: float = maxf(0.001, float(rt.get("window_seconds", 8.0)))
	var left: float = maxf(0.0, float(rt.get("next_tick_in", 0.0)) - seconds_since_view)
	var progress := clampf(1.0 - left / window, 0.0, 1.0)
	return now_h + (next_h - now_h) * progress


static func format_hour(h: float) -> String:
	var hh := int(floor(fposmod(h, 24.0)))
	var mm := int(floor(fposmod(h, 1.0) * 60.0))
	return "%02d:%02d" % [hh, mm]


## Daylight tint for the world: dawn, day, dusk, night.
static func daylight(h: float) -> Color:
	var x := fposmod(h, 24.0)
	if x < 7.0 or x >= 19.0:
		return Color(0.45, 0.5, 0.7)
	if x < 9.0:
		return Color(1.0, 0.9, 0.8).lerp(Color.WHITE, (x - 7.0) / 2.0)
	if x < 16.0:
		return Color.WHITE
	return Color.WHITE.lerp(Color(0.95, 0.75, 0.6), (x - 16.0) / 3.0)


## Effects for notices the client has not yet shown. `seen` counts notices already processed.
static func new_effects(notices: Array, seen: int) -> Array:
	var out: Array = []
	for i in range(seen, notices.size()):
		for e in EFFECTS.get(notices[i].get("code", ""), []):
			if e not in out:
				out.append(e)
	return out


static func headroom_ratio(fund: Dictionary) -> float:
	var nav := float(fund.get("nav", "0"))
	var req := float(fund.get("maintenance_req", "0"))
	return 9.99 if req <= 0.0 else nav / req


static func partner_location(view: Dictionary, role: String) -> String:
	var decisions: Array = view.get("decisions", [])
	for i in range(decisions.size() - 1, -1, -1):
		if decisions[i].get("role", "") == role:
			if decisions[i].get("type") == "visit":
				var location: String = decisions[i].get("detail", {}).get("location", "committee")
				return location if LOCATIONS.has(location) else "committee"
			return COMMAND_LOCATION.get(decisions[i].get("type", ""), "committee")
	return "trading" if role == "pm" else "risk"


## Value of an HTTP response header (case-insensitive name), or "" when absent.
static func header_value(headers: PackedStringArray, name: String) -> String:
	var want := name.to_lower() + ":"
	for h in headers:
		if h.to_lower().begins_with(want):
			return h.substr(want.length()).strip_edges()
	return ""


static func money(s: Variant) -> String:
	var v := float(str(s))
	var neg := v < 0.0
	var whole := str(int(round(absf(v))))
	var out := ""
	while whole.length() > 3:
		out = "," + whole.substr(whole.length() - 3) + out
		whole = whole.substr(0, whole.length() - 3)
	return ("-$" if neg else "$") + whole + out


## Status beacon on a rival tower: steady green, pulsing amber, flashing red, or dark once closed.
static func beacon_color(status: String, t: float) -> Color:
	match status:
		"active": return Color("#2fd36a")
		"deleveraging": return Color("#ffb020").lerp(Color("#3a2400"), 0.5 + 0.5 * sin(t * 4.0))
		"liquidating": return Color("#ff2a1a") if fposmod(t, 0.5) < 0.25 else Color("#200000")
	return Color(0.02, 0.02, 0.02)


## League table rows from the server view, ranked by return (ties by id), with `rank` and `is_you` added.
static func league_rows(view: Dictionary) -> Array:
	var rows: Array = []
	var league: Array = view.get("league", []) if view.get("league") is Array else []
	for r in league:
		var row: Dictionary = (r as Dictionary).duplicate()
		row["return_bps"] = int(float(str(row.get("return_bps", "0"))))
		row["is_you"] = row.get("id", "") == "you"
		rows.append(row)
	rows.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return a["return_bps"] > b["return_bps"] or (a["return_bps"] == b["return_bps"] and str(a.get("id", "")) < str(b.get("id", ""))))
	for i in rows.size():
		rows[i]["rank"] = i + 1
	return rows
