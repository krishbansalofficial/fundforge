class_name TerminalRules
extends RefCounted
## Pure navigation and formatting. Client numbers are presentation only.

const PAGES := ["MON", "GP", "PORT", "RISK", "NEWS", "ORDERS", "STREET", "HELP", "REPLAY", "RESEARCH"]


static func parse(command: String, symbols: Array, current_symbol: String) -> Dictionary:
	var tokens := command.strip_edges().to_upper().split(" ", false)
	if tokens.is_empty():
		return {"ok": false, "error": "Enter a function or symbol. HELP lists commands."}
	var symbol := current_symbol
	var page := "GP"
	if tokens.size() == 1:
		if tokens[0] in PAGES:
			page = tokens[0]
		elif tokens[0] in symbols:
			symbol = tokens[0]
		else:
			return {"ok": false, "error": "Unknown function or symbol: " + tokens[0]}
	elif tokens.size() == 2 and tokens[0] in symbols and tokens[1] == "GP":
		symbol = tokens[0]
	else:
		return {"ok": false, "error": "Use a function, a symbol, or SYMBOL GP. Example: BRIN GP."}
	return {"ok": true, "page": page, "symbol": symbol}


static func prices(history: Array, symbol: String) -> PackedFloat32Array:
	var values := PackedFloat32Array()
	for observation in history:
		var marks: Dictionary = observation.get("marks", {})
		if marks.has(symbol):
			values.append(float(str(marks[symbol])))
	return values


static func bps(value: Variant) -> String:
	return "--" if value == null else "%+.1f" % float(str(value))


static func pct(value: Variant) -> String:
	return "--" if value == null else "%.2f%%" % (float(str(value)) * 100.0)


static func quote(data: Dictionary, symbol: String) -> Dictionary:
	for row in data.get("quotes", []):
		if row.get("sym") == symbol:
			return row
	return {}


## Street activity index rows, newest period first: what each period reads as of today and whether it was revised.
static func macro_lines(macro: Array, limit: int) -> PackedStringArray:
	var out := PackedStringArray()
	for i in range(macro.size() - 1, maxi(-1, macro.size() - 1 - limit), -1):
		var m: Dictionary = macro[i]
		out.append("D%d  %s  %s D%d" % [int(m["period_day"]), str(m["value"]),
				"revised" if int(m["revision"]) > 0 else "first print", int(m["published_day"])])
	return out


## Exact 6-decimal fixed point: "0.65" -> 650000 micro-units, or -1 unless a plain decimal in [0, 1] with <= 6 dp.
static func micros(text: String) -> int:
	var m := RegEx.create_from_string(r"^([01])(?:\.(\d{1,6}))?$").search(text.strip_edges())
	if m == null:
		return -1
	var value := int(m.get_string(1)) * 1000000 + int(m.get_string(2).rpad(6, "0"))
	return value if value <= 1000000 else -1


static func fixed6(units: int) -> String:
	return "%d.%06d" % [units / 1000000, units % 1000000]


## A thesis forecast from the calm probability; stressed is its exact complement. {} if the entry is invalid.
static func thesis_forecast(calm_text: String) -> Dictionary:
	var calm := micros(calm_text)
	if calm < 0:
		return {}
	return {"calm": fixed6(calm), "stressed": fixed6(1000000 - calm)}


## Debrief research rows, one per scored thesis, then each seat's mean. Brier sits beside P&L, never in it.
static func research_lines(research: Dictionary) -> PackedStringArray:
	var out := PackedStringArray()
	for t in research.get("theses", []):
		var f: Dictionary = t["forecast"]
		out.append("%s  %s (recorded D%d)  calm %s / stressed %s  ->  true %s  /  Brier %s" % [str(t["role"]).to_upper(),
				t["question"], int(t["recorded_day"]), f["calm"], f["stressed"], str(t["true_regime"]).to_upper(), t["brier"]])
	var seats: Dictionary = research.get("seats", {})
	for role in ["pm", "mp"]:
		var seat: Dictionary = seats.get(role, {})
		if int(seat.get("theses", 0)) > 0:
			out.append("%s mean Brier %s over %d question(s)" % [role.to_upper(), seat["mean_brier"], int(seat["theses"])])
	return out
