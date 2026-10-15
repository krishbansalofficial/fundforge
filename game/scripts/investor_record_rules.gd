class_name InvestorRecordRules
extends RefCounted
## Completed-only LP record text. Decimal strings are displayed exactly as served.

const REVIEW := [["drawdown", "Drawdown"], ["response_lag", "Response lag"], ["contact", "Contact"], ["clamp", "Clamp"]]
const CHAPTER := [["performance", "Performance"], ["breaches", "Breaches"], ["report", "Report"],
	["meeting", "Meeting"], ["gate", "Gate"], ["herding", "Herding"], ["overdue", "Overdue"], ["clamp", "Clamp"]]


static func lines(record: Variant) -> PackedStringArray:
	var out := PackedStringArray()
	if not record is Dictionary:
		return out
	if record.get("policy") != null:
		out.append("Relationship policy: %s" % record["policy"])
	var final: Dictionary = record.get("final", {})
	for lp in final:
		var result: Dictionary = final[lp]
		out.append("%s / final confidence %s / %s" % [lp, result.get("confidence", "unavailable"), str(result.get("band", "unavailable")).replace("_", " ")])
	var carried: Dictionary = record.get("carried_units", {})
	for lp in carried:
		out.append("%s / carried redemption units: %s (remain invested)" % [lp, carried[lp]])
	var checkpoints: Array = record.get("checkpoints", [])
	if checkpoints.is_empty():
		out.append("No relationship checkpoints were reached in this run.")
	for checkpoint in checkpoints:
		var chapter: bool = checkpoint.get("kind") == "chapter_close"
		out.append("Day %s / %s / %s / confidence %s to %s / %s" % [checkpoint.get("day", "?"),
			checkpoint.get("lp", "?"), "Chapter close" if chapter else "Interim review",
			checkpoint.get("start", "unavailable"), checkpoint.get("end", "unavailable"),
			str(checkpoint.get("band", "unavailable")).replace("_", " ")])
		var drivers := PackedStringArray()
		for driver in CHAPTER if chapter else REVIEW:
			if checkpoint.get(driver[0]) != null:
				drivers.append("%s: %s" % [driver[1], checkpoint[driver[0]]])
		if not drivers.is_empty():
			out.append("Confidence drivers / " + "; ".join(drivers))
		var facts := PackedStringArray()
		if checkpoint.get("drawdown_pp") != null:
			facts.append("Drawdown percentage points: %s" % checkpoint["drawdown_pp"])
		if checkpoint.get("open_alerts") != null:
			facts.append("Open alerts: %s" % checkpoint["open_alerts"])
		if checkpoint.get("policy_version") != null:
			facts.append("Policy: %s" % checkpoint["policy_version"])
		if not facts.is_empty():
			out.append("; ".join(facts))
	return out
