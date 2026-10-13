class_name LpRules
extends RefCounted
## Pure text for the investor lounge. Every value is a server-view field; the client never computes
## confidence, units or gate outcomes. `view.investors` is the managing partner's inbox and is null for
## the PM seat, so everything here reads the current view only and keeps nothing between views.

const BANDS := {"strong": "Strong", "stable": "Stable", "concerned": "Concerned", "withdrawal_risk": "Withdrawal risk"}
const LP_CODES := ["lp_band", "redemption_notice", "redemption_gated", "redemption_dealt", "gate_elected"]
const REVIEW_LAST_DAY := 15  # lp.REVIEW_DAYS (13, 15): contact matters only before the last review


static func band_text(band: Variant) -> String:
	return BANDS.get(str(band), str(band))


## A Decimal unit string with thousands separators, string-only so every digit the server sent is kept.
static func units(s: Variant) -> String:
	var t := str(s).strip_edges()
	var neg := t.begins_with("-")
	var parts := t.trim_prefix("-").split(".")
	var whole: String = parts[0]
	var out := ""
	while whole.length() > 3:
		out = "," + whole.substr(whole.length() - 3) + out
		whole = whole.substr(0, whole.length() - 3)
	return ("-" if neg else "") + whole + out + ("." + parts[1] if parts.size() > 1 else "")


## One line per LP for the MP inbox; empty when the view has no inbox (PM seat, authored rooms).
static func rows(view: Dictionary) -> Array:
	var inv: Variant = view.get("investors")
	if not inv is Dictionary:
		return []
	var out: Array = []
	for lp in inv.get("lps", []):
		var line := "%s   %s" % [lp["id"], band_text(lp["band"])]
		if lp.get("requested_units") != null:
			line += "\n   " + request_text(lp["requested_units"], inv.get("deal_day"))
		if lp.get("carried_units") != null:
			line += "\n   Carried by a gate: %s units, still invested" % units(lp["carried_units"])
		if lp.get("contacted", false):
			line += "\n   Contacted before the next review"
		out.append(line)
	return out


## Redemption payables are paid the business day after dealing (engine `redemption_dealt`).
static func request_text(requested: Variant, deal_day: Variant) -> String:
	var d := int(deal_day)
	return "Redemption request %s units, dealt at the day %d close, payable day %d" % [units(requested), d, d + 1]


## Why "Contact" is disabled, mirroring the server's refusal text; "" means the server may accept.
static func contact_reason(view: Dictionary, lp: Dictionary) -> String:
	if view.get("clock", {}).get("finished", false):
		return "LP contact happens at a decision barrier"
	if view.get("attention", {}).get("committed", false):
		return "attention already committed for this decision window"
	if int(view.get("clock", {}).get("day", 0)) > REVIEW_LAST_DAY:
		return "no LP review remains in this window"
	if lp.get("contacted", false):
		return "%s was already contacted before its next review" % lp["id"]
	return ""


## The terms a gate package would bind, from the inbox: the dealing day and the exact pending requests.
## Empty when no gate can be proposed now.
static func pending_gate_terms(view: Dictionary) -> Dictionary:
	var inv: Variant = view.get("investors")
	if not inv is Dictionary or inv.get("gate_elected", false) or inv.get("deal_day") == null:
		return {}
	if int(view.get("clock", {}).get("day", 0)) > int(inv["deal_day"]):
		return {}
	var req := {}
	for lp in inv.get("lps", []):
		if lp.get("requested_units") != null:
			req[lp["id"]] = str(lp["requested_units"])
	return {} if req.is_empty() else {"deal_day": int(inv["deal_day"]), "requests": req}


## Shared text for a gate package's `terms` (both seats see packages).
static func gate_terms_text(terms: Dictionary) -> String:
	var ids: Array = terms.get("requests", {}).keys()
	ids.sort()
	var parts := PackedStringArray()
	for id in ids:
		parts.append("%s %s units" % [id, units(terms["requests"][id])])
	return "GATE for the day %d dealing close, binding requests: %s. At most 20%% of pre-flow NAV is dealt, pro rata; undealt units stay invested and carry forward." % [
			int(terms.get("deal_day", 0)), ", ".join(parts)]


static func has_open_gate(view: Dictionary) -> bool:
	for p in view.get("packages", []):
		if p.get("kind") == "gate" and p.get("status") == "PENDING_APPROVAL":
			return true
	return false


## The newest LP-related notices this seat may see (the server already filters private ones by owner).
static func notices(view: Dictionary, limit := 5) -> Array:
	var out: Array = view.get("notices", []).filter(func(n): return n.get("code") in LP_CODES)
	return out.slice(maxi(0, out.size() - limit))
