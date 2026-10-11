class_name TerminalRules
extends RefCounted
## Pure navigation and formatting. Client numbers are presentation only.

const PAGES := ["MON", "GP", "PORT", "RISK", "NEWS", "ORDERS", "STREET", "HELP", "REPLAY"]


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
