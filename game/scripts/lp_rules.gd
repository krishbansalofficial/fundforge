class_name LpRules
extends RefCounted
## Pure text for the investor lounge. Every value is a server-view field; the client never computes
## confidence, units or gate outcomes. `view.investors` is the managing partner's inbox and is null for
## the PM seat, so everything here reads the current view only and keeps nothing between views.

const BANDS := {"strong": "Strong", "stable": "Stable", "concerned": "Concerned", "withdrawal_risk": "Withdrawal risk"}
const LP_CODES := ["lp_band", "redemption_notice", "redemption_gated", "redemption_dealt", "gate_elected",
		"prospect_open", "prospect_committed", "prospect_escrow", "prospect_consent", "prospect_admitted",
		"prospect_forfeited", "prospect_declined", "winddown_declared"]
const PROSPECT_CLOSED := ["admitted", "forfeited", "declined"]  # investors.CLOSED
const STAGES := {"prospect": "Introduced, not yet qualified", "qualified": "Qualified, diligence pending",
		"diligence": "Diligence complete, awaiting the day 15 certified report", "committed": "Signed a conditional commitment",
		"eligible": "Funded in escrow, awaiting both partners' consent", "admitted": "Admitted as a new series",
		"forfeited": "Offer lapsed", "declined": "Declined by the fund"}
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
	return has_open(view, "gate")


static func has_open(view: Dictionary, kind: String) -> bool:
	for p in view.get("packages", []):
		if p.get("kind") == kind and p.get("status") == "PENDING_APPROVAL":
			return true
	return false


# ---------- campaign: prospect admission and joint winddown (view.prospect exists only in prospect rooms) ----------

## Campaign rooms carry `prospect`; the view has no other campaign flag, so this is the client's only signal.
static func is_campaign(view: Dictionary) -> bool:
	if view.has("campaign"):
		return bool(view["campaign"])
	return view.get("prospect") is Dictionary  # fallback for a server without SessionView.campaign


## Pipeline text from the seat-filtered prospect view; terms the seat has not learned stay hidden.
static func prospect_lines(view: Dictionary) -> Array:
	var p: Variant = view.get("prospect")
	if not p is Dictionary:
		return []
	var out: Array = ["PROSPECTIVE LP / %s" % STAGES.get(str(p["stage"]), str(p["stage"]))]
	if p.get("reason") != null:
		out.append("Reason: " + str(p["reason"]).replace("_", " "))
	if p.get("series_id") == null:
		out.append("Terms unknown to this seat until the managing partner qualifies it at the LP desk.")
	else:
		out.append("%s: up to $%s in $%s steps, dealing close day %d" % [p["series_id"], units(p["max_amount"]),
				units(p["cap_step"]), int(p["dealing_day"])])
	if str(p.get("escrow", "0")).to_float() != 0.0:
		out.append("Escrow $%s, outside the fund: not NAV, cash or margin collateral" % units(p["escrow"]))
	if p.get("authorized") != null:
		out.append("Both partners consented to admit $%s at the dealing close" % units(p["authorized"]))
	return out


## Admission amounts the server would accept by step: multiples of cap_step up to escrow, largest first.
## ponytail: whole-dollar escrow and step only (the fixture's are); a fractional value offers nothing.
static func admission_amounts(view: Dictionary) -> Array:
	var p: Variant = view.get("prospect")
	if not p is Dictionary or p.get("cap_step") == null:
		return []
	var escrow := str(p.get("escrow", "0"))
	var step := str(p["cap_step"])
	if not escrow.is_valid_int() or not step.is_valid_int() or int(step) <= 0:
		return []
	var out: Array = []
	var a := int(escrow) - int(escrow) % int(step)
	while a > 0:
		out.append(str(a))
		a -= int(step)
	return out


static func _solo_refusal(view: Dictionary, what: String) -> String:
	return "" if view.get("bots", []).is_empty() else 			"solo game: the partner bot will not countersign %s; it needs a second human partner" % what


## Why proposing an admission is disabled; "" means the server may accept (capacity is checked there).
static func admission_reason(view: Dictionary) -> String:
	var p: Variant = view.get("prospect")
	if not p is Dictionary:
		return "no prospective LP in this scenario"
	if view.get("clock", {}).get("finished", false):
		return "admission is proposed at a decision barrier"
	if p.get("authorized") != null:
		return "both partners already consented to this admission"
	if p.get("stage") != "eligible":
		return "no funded, eligible subscription awaits admission"
	if has_open(view, "admission"):
		return "an admission package already awaits countersignature"
	return _solo_refusal(view, "an admission")


## Why declining is disabled for this seat; "" means the server may accept.
static func decline_reason(view: Dictionary, role: String) -> String:
	var p: Variant = view.get("prospect")
	if not p is Dictionary:
		return "no prospective LP in this scenario"
	if role != "mp":
		return "LP relationships belong to the managing partner"
	if view.get("clock", {}).get("finished", false):
		return "a prospect is declined at a decision barrier"
	if p.get("stage") in PROSPECT_CLOSED:
		return "the prospect's pipeline is already closed"
	if p.get("authorized") != null:
		return "both partners consented to this admission; it can no longer be declined"
	return ""


static func winddown_declared(view: Dictionary) -> bool:
	if view.has("winddown"):
		return view["winddown"] != null  # the declaration day, or null while undeclared
	for p in view.get("packages", []):  # fallback for a server without SessionView.winddown
		if p.get("kind") == "winddown" and p.get("status") == "ELECTED":
			return true
	return view.get("notices", []).any(func(n): return n.get("code") == "winddown_declared")


## Why proposing a winddown is disabled; "" means the server may accept.
static func winddown_reason(view: Dictionary) -> String:
	if not is_campaign(view):
		return "winddown is a campaign mechanic"
	if view.get("clock", {}).get("finished", false):
		return "winddown is declared at a decision barrier before the end"
	if winddown_declared(view):
		return "winddown already declared"
	if has_open(view, "winddown"):
		return "a winddown package already awaits countersignature"
	return _solo_refusal(view, "a winddown")


## Committee-room text for any package kind (both seats see packages).
static func package_text(p: Dictionary) -> String:
	var t: Dictionary = p.get("terms", {})
	match p.get("kind"):
		"gate": return gate_terms_text(t)
		"winddown": return "WINDDOWN declared day %d: no new buying or shorting; liquidate and redeem every unit." % int(t.get("day", 0))
		"admission": return "ADMIT %s: $%s at the day %d dealing close, new series at %s, high-water mark %s." % [
				t.get("series", "?"), units(t.get("amount", "0")), int(t.get("deal_day", 0)), t.get("issue_price", "?"), t.get("hwm", "?")]
	return ", ".join(p.get("orders", []).map(func(o): return "%s %s %s" % [o["side"], o["qty"], o["sym"]]))


## The newest LP-related notices this seat may see (the server already filters private ones by owner).
static func notices(view: Dictionary, limit := 5) -> Array:
	var out: Array = view.get("notices", []).filter(func(n): return n.get("code") in LP_CODES)
	return out.slice(maxi(0, out.size() - limit))
