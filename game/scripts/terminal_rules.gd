class_name TerminalRules
extends RefCounted
## Pure navigation and formatting. Client numbers are presentation only.

## F1-F10 keep the first ten; the rest are reached from the command line or the function bar.
const PAGES := ["MON", "GP", "PORT", "RISK", "NEWS", "ORDERS", "STREET", "HELP", "REPLAY", "RESEARCH",
		"DES", "HP", "COMP", "CORR", "IMAP", "ALRT"]
const SYMBOL_PAGES := ["GP", "DES", "HP"]  # functions about one security: BRIN DES, DES BRIN
const COMP_MAX := 6


## Bloomberg-style: "BRIN DES <GO>", "DES BRIN", "COMP BRIN COVE", "ALRT BRIN > 105.5". Read-only: no trade verbs.
static func parse(command: String, symbols: Array, current_symbol: String) -> Dictionary:
	var tokens := Array(command.strip_edges().to_upper().replace("<GO>", " ").split(" ", false))
	if not tokens.is_empty() and tokens[-1] == "GO":
		tokens.pop_back()
	if tokens.is_empty():
		return {"ok": false, "error": "Enter a function or symbol. HELP lists commands."}
	var head: String = tokens[0]
	if head == "COMP":
		var picked: Array = []
		for t in tokens.slice(1):
			if not t in symbols:
				return {"ok": false, "error": "Unknown symbol: " + t}
			if not t in picked:
				picked.append(t)
		if picked.is_empty():
			picked = [current_symbol]
		if picked.size() > COMP_MAX:
			return {"ok": false, "error": "COMP compares at most %d symbols." % COMP_MAX}
		return {"ok": true, "page": "COMP", "symbol": picked[0], "symbols": picked}
	if head == "ALRT" and tokens.size() > 1:
		return _alert(tokens, symbols, current_symbol)
	if tokens.size() == 1:
		if head in PAGES:
			return {"ok": true, "page": head, "symbol": current_symbol}
		if head in symbols:
			return {"ok": true, "page": "GP", "symbol": head}
		return {"ok": false, "error": "Unknown function or symbol: " + head}
	if tokens.size() == 2:
		if head in symbols and tokens[1] in SYMBOL_PAGES:
			return {"ok": true, "page": tokens[1], "symbol": head}
		if head in SYMBOL_PAGES and tokens[1] in symbols:
			return {"ok": true, "page": head, "symbol": tokens[1]}
	return {"ok": false, "error": "Use a function, a symbol, or SYMBOL FUNCTION. Examples: BRIN GP, BRIN DES, COMP BRIN COVE."}


static func _alert(tokens: Array, symbols: Array, current_symbol: String) -> Dictionary:
	if tokens.size() == 2 and tokens[1] == "CLEAR":
		return {"ok": true, "page": "ALRT", "symbol": current_symbol, "clear": true}
	if tokens.size() != 4 or not tokens[1] in symbols or not tokens[2] in [">", "<"] or not tokens[3].is_valid_float() \
			or float(tokens[3]) <= 0:
		return {"ok": false, "error": "Alert syntax: ALRT BRIN > 105.5  (or <). ALRT CLEAR removes all."}
	return {"ok": true, "page": "ALRT", "symbol": tokens[1],
			"alert": {"sym": tokens[1], "op": tokens[2], "level": float(tokens[3])}}


## Completions for the last word typed: functions first, then symbols.
static func complete(text: String, symbols: Array) -> Array:
	var words := text.to_upper().split(" ")
	var last: String = words[-1]
	if last == "":
		return []
	var out: Array = []
	for name in PAGES + symbols:
		if name.begins_with(last) and not name in out:
			out.append(name)
	return out


## Event-to-event simple returns of the observed marks (presentation analytics, not accounting).
static func returns(values: PackedFloat32Array) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	for i in range(1, values.size()):
		if values[i - 1] != 0.0:
			out.append(values[i] / values[i - 1] - 1.0)
	return out


## Pearson correlation; NAN when there are fewer than 3 pairs or a series never moves.
static func correlation(a: PackedFloat32Array, b: PackedFloat32Array) -> float:
	var n := mini(a.size(), b.size())
	if n < 3:
		return NAN
	var ma := 0.0
	var mb := 0.0
	for i in n:
		ma += a[i]
		mb += b[i]
	ma /= n
	mb /= n
	var cov := 0.0
	var va := 0.0
	var vb := 0.0
	for i in n:
		cov += (a[i] - ma) * (b[i] - mb)
		va += (a[i] - ma) * (a[i] - ma)
		vb += (b[i] - mb) * (b[i] - mb)
	if va <= 0.0 or vb <= 0.0:
		return NAN
	return cov / sqrt(va * vb)


## Rebased so the first observation is 100, for comparing securities on one chart.
static func rebased(values: PackedFloat32Array) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	if values.is_empty() or values[0] == 0.0:
		return out
	for v in values:
		out.append(v / values[0] * 100.0)
	return out


static func range_stats(values: PackedFloat32Array) -> Dictionary:
	if values.is_empty():
		return {}
	var lo := values[0]
	var hi := values[0]
	for v in values:
		lo = minf(lo, v)
		hi = maxf(hi, v)
	return {"first": values[0], "last": values[-1], "low": lo, "high": hi}


static func alert_hit(alert: Dictionary, mark: float) -> bool:
	return mark > alert["level"] if alert["op"] == ">" else mark < alert["level"]


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
