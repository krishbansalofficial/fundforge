class_name CardRules
## Pure text for the outcome screen and the shareable ending card. Every value is a server-response field;
## nothing here computes money, score or rank.

const SIZE := Vector2i(1200, 630)
const LABELS := {"WIN": "Win", "SURVIVAL": "Survival", "DISTRESS": "Distress"}


## Optional server-derived facts for the completed-run screen; absent fields stay absent.
static func facts(outcome: Dictionary) -> PackedStringArray:
	var out := PackedStringArray()
	if outcome.has("scenario"):
		out.append("Scenario: %s" % outcome["scenario"])
	if outcome.has("max_drawdown"):
		out.append("Maximum drawdown: %s%% of NAV per unit, measured at business-day closes" % percent(outcome["max_drawdown"]))
	if outcome.get("generated_days") != null and outcome.get("stressed_days") != null:
		out.append("Generated market: %d stressed days out of %d generated days" % [int(outcome["stressed_days"]), int(outcome["generated_days"])])
	if outcome.get("seed_commitment") != null:
		out.append("Seed SHA-256: %s" % outcome["seed_commitment"])
		var local := seed_hash(outcome.get("variant"))
		if local != "" and local != str(outcome["seed_commitment"]):
			out.append("WARNING: the revealed seed hashes to %s, not the served commitment" % local)
	return out


## What the run's market was, from the outcome's revealed `variant`. Case 1 variants are authored
## (fixtures/case1.json); generated rooms reveal their seed as `seed:<text>`.
static func market_text(variant: Variant, scenario: Variant = null) -> String:
	var v := "base" if variant == null else str(variant)
	if scenario != null and not str(scenario).begins_with("case1"):  # Case 1's day 16 text would be wrong here
		return "The %s run's hidden variant was \"%s\"." % [scenario, v]
	if v == "base":
		return "The day 16 market was a sell-off and short squeeze. You couldn't know which in advance."
	if v == "rally":
		return "The day 16 market was a broad rally. You couldn't know which in advance."
	if v.begins_with("seed:"):
		return "A generated market: Case 1's crisis calendar on a seeded price path. Seed revealed: %s" % v.substr(5)
	return "The market was the hidden \"%s\" variant." % v


## SHA-256 of a revealed seed, so anyone can check it against the commitment and regenerate the tape.
static func seed_hash(variant: Variant) -> String:
	var v := str(variant)
	return v.substr(5).sha256_text() if v.begins_with("seed:") else ""


## A Decimal string as dollars with thousands separators. String-only, so no float rounding:
## every fractional digit the server sent is kept (at least cents).
static func money(s: Variant) -> String:
	var t := str(s).strip_edges()
	var neg := t.begins_with("-")
	var parts := t.trim_prefix("-").split(".")
	var whole: String = parts[0]
	var frac: String = parts[1] if parts.size() > 1 else ""
	while frac.length() < 2:
		frac += "0"
	var out := ""
	while whole.length() > 3:
		out = "," + whole.substr(whole.length() - 3) + out
		whole = whole.substr(0, whole.length() - 3)
	return ("-$" if neg else "$") + whole + out + "." + frac


## A Decimal fraction string as a percentage by moving the point two places: "0.123456" -> "12.3456".
## String-only, so every digit the server sent is kept and nothing is rounded.
static func percent(s: Variant) -> String:
	var t := str(s).strip_edges()
	var neg := t.begins_with("-")
	var parts := t.trim_prefix("-").split(".")
	var frac: String = parts[1] if parts.size() > 1 else ""
	while frac.length() < 2:
		frac += "0"
	var whole := (parts[0] + frac.substr(0, 2)).lstrip("0")
	var rest := frac.substr(2)
	return ("-" if neg else "") + (whole if whole != "" else "0") + ("." + rest if rest != "" else "")


static func signed(s: Variant) -> String:
	var t := str(s)
	return t if t.begins_with("-") else "+" + t


## Card rows [label, value] from the outcome, the view's partner names, the debrief's research block
## and the verify response. Optional sources may be empty; their rows are left out, never guessed.
static func rows(outcome: Dictionary, names: Dictionary, research: Dictionary, verify: Dictionary) -> Array:
	var out: Array = []
	out.append(["Partners", "%s (PM) and %s (MP)" % [names.get("pm", "?"), names.get("mp", "?")]])
	var standing := "Score %s bps" % signed(outcome.get("score", "?"))
	if outcome.get("rank") != null and outcome.get("funds") != null:
		standing = "#%d of %d funds  /  " % [int(outcome["rank"]), int(outcome["funds"])] + standing
	out.append(["Result", standing])
	out.append(["vs benchmark", "fund %s bps vs passive book %s bps" % [
			signed(outcome.get("fund_return_bps", "?")), signed(outcome.get("benchmark_return_bps", "?"))]])
	out.append(["Final NAV", money(outcome.get("nav", "0"))])
	var forced: Array = outcome.get("forced", [])
	out.append(["Forced actions", str(forced.size())])
	var seats: Dictionary = research.get("seats", {})
	var brier := PackedStringArray()
	for role in ["pm", "mp"]:
		var seat: Dictionary = seats.get(role, {})
		if int(seat.get("theses", 0)) > 0 and seat.get("mean_brier") != null:
			brier.append("%s %s (%d)" % [role.to_upper(), seat["mean_brier"], int(seat["theses"])])
	if not brier.is_empty():
		out.append(["Mean Brier", "  ".join(brier)])
	if outcome.get("max_drawdown") != null:
		out.append(["Max drawdown", "%s%% (NAV per unit, at closes)" % percent(outcome["max_drawdown"])])
	if outcome.get("scenario") != null:
		out.append(["Scenario", str(outcome["scenario"])])
	if outcome.get("generated_days") != null and outcome.get("stressed_days") != null:
		out.append(["Stressed days", "%d of %d generated" % [int(outcome["stressed_days"]), int(outcome["generated_days"])]])
	var variant: Variant = outcome.get("variant", "base")
	if str(variant).begins_with("seed:"):
		out.append(["Seed", str(variant).substr(5)])
		# Prefer the server's commitment; the client hash of the revealed seed must match it.
		var served: Variant = outcome.get("seed_commitment")
		var local := seed_hash(variant)
		if served == null:
			out.append(["Seed SHA-256", local])
		elif str(served) == local:
			out.append(["Seed SHA-256", str(served)])
		else:
			out.append(["Seed SHA-256", "%s (does NOT match the revealed seed: %s)" % [served, local]])
	else:
		out.append(["Variant", str(variant)])
	if verify.get("rules_version") != null:
		out.append(["Rules", str(verify["rules_version"])])
	if verify.get("chain_head") != null:
		out.append(["Chain head", str(verify["chain_head"])])
	out.append(["Journal", str(outcome.get("journal_digest", "?"))])
	return out
