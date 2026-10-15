class_name CertificationRules
extends RefCounted
## The view status applies to the latest dealing close, never the current intraday mark.

static func summary(view: Dictionary) -> String:
	match view.get("certification", "pending"):
		"certified":
			return "Latest dealing-close: Certified\nNot a new check of current NAV."
		"broken":
			return "Latest dealing-close: Broken\nLatest dealing was withheld; inspect RISK.\nNot a new check of current NAV."
		_:
			return "Latest dealing-close: Pending\nNo dealing-close certificate yet.\nNot a new check of current NAV."
