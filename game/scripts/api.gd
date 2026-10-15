extends Node
## Network layer. The server is authoritative for money, time and outcomes; this client only renders
## the as-of view and sends commands. Every command carries one idempotency key, reused on retry.

signal view_changed(view: Dictionary)
signal command_failed(message: String)
## Live presence (cosmetic): the partner's avatar position, or that their last connection closed.
signal partner_moved(role: String, pos: Vector3, location: String)
signal partner_left(role: String)

const POLL_SECONDS := 0.5
const STALE_SECONDS := 2.0

var base_url := "http://127.0.0.1:8000"
var room_id := ""
var token := ""
var view: Dictionary = {}
var view_received_at := 0.0  # Time.get_ticks_msec()/1000 when the last view arrived
var view_etag := ""  # sent as If-None-Match; a 304 keeps the view and its arrival time
var last_poll_success_at := -1.0  # heartbeat time, distinct from the snapshot interpolation baseline
var polling_stale := false
var _joined_at := 0.0
var _join_generation := 0

var _polling := false
var _poll_timer: Timer

# Presence socket. Optional: if it never connects, polling alone runs the game exactly as before.
var presence_live := false
var _ws: WebSocketPeer
var _ws_hello := false
var _ws_attempt := 0
var _ws_retry_at := 0.0
var _ws_opened := false  # a socket reached OPEN since join; until then, handshakes are limited
var _last_sent := Vector3(-1, -1, -1)
var _last_sent_at := 0.0


func _ready() -> void:
	_poll_timer = Timer.new()
	_poll_timer.wait_time = POLL_SECONDS
	_poll_timer.timeout.connect(_poll)
	add_child(_poll_timer)


func join(url: String, room: String, seat_token: String) -> void:
	_join_generation += 1
	_polling = false  # old room reads remain isolated by the captured generation
	view = {}
	view_received_at = 0.0
	last_poll_success_at = -1.0
	polling_stale = false
	_joined_at = Time.get_ticks_msec() / 1000.0
	base_url = url.trim_suffix("/")
	room_id = room
	token = seat_token
	view_etag = ""
	_close_presence()
	_ws_attempt = 0
	_ws_retry_at = 0.0
	_ws_opened = false
	_poll_timer.start()
	_poll()


func new_key() -> String:
	return Crypto.new().generate_random_bytes(16).hex_encode()


## Low-level request. Returns {ok: bool, status: int, data: Variant, network_error: bool, headers}.
func request(method: int, path: String, body: Variant = null, key := "", if_none_match := "") -> Dictionary:
	var http := HTTPRequest.new()
	http.timeout = 10.0
	add_child(http)
	var headers := PackedStringArray(["Content-Type: application/json"])
	if token != "":
		headers.append("Authorization: Bearer " + token)
	if key != "":
		headers.append("Idempotency-Key: " + key)
	if if_none_match != "":
		headers.append("If-None-Match: " + if_none_match)
	var payload := "" if body == null else JSON.stringify(body)
	var err := http.request(base_url + path, headers, method, payload)
	if err != OK:
		http.queue_free()
		return {"ok": false, "status": 0, "data": null, "network_error": true, "headers": PackedStringArray()}
	var res: Array = await http.request_completed
	http.queue_free()
	var status: int = res[1]
	var text: String = (res[3] as PackedByteArray).get_string_from_utf8()
	var data: Variant = JSON.parse_string(text) if text != "" else null
	return {"ok": res[0] == HTTPRequest.RESULT_SUCCESS and status >= 200 and status < 300,
			"status": status, "data": data, "network_error": res[0] != HTTPRequest.RESULT_SUCCESS,
			"headers": res[2]}


func create_room(url: String, pm_name: String, mp_name: String, solo_role := "", scenario := "case1") -> Dictionary:
	base_url = url.trim_suffix("/")
	var body := {"scenario": scenario, "pm_name": pm_name, "mp_name": mp_name}
	if solo_role != "":
		body["solo_role"] = solo_role
	return await request(HTTPClient.METHOD_POST, "/api/rooms", body)


## Send one game command. A network failure is retried once with the SAME key, so the server
## applies it at most once.
func command(cmd: Dictionary) -> Dictionary:
	var key := new_key()
	var path := "/api/rooms/%s/commands" % room_id
	var res := await request(HTTPClient.METHOD_POST, path, cmd, key)
	if res["network_error"]:
		res = await request(HTTPClient.METHOD_POST, path, cmd, key)
	if not res["ok"]:
		var msg := "Request failed (%d)" % res["status"]
		if res["data"] is Dictionary and res["data"].has("detail"):
			msg = str(res["data"]["detail"])
		command_failed.emit(msg)
	_poll()
	return res


## One journal page: the newest entries, or with `after` >= 0 only those following that cursor.
func ledger(entity: String, after := -1) -> Dictionary:
	return await request(HTTPClient.METHOD_GET, WorldRules.ledger_path(room_id, entity, after))


func verify() -> Dictionary:
	return await request(HTTPClient.METHOD_GET, "/api/rooms/%s/verify" % room_id)


func liquidity(assumptions: Dictionary) -> Dictionary:
	return await request(HTTPClient.METHOD_POST, "/api/rooms/%s/liquidity" % room_id, assumptions)


func debrief(options: Dictionary) -> Dictionary:
	return await request(HTTPClient.METHOD_POST, "/api/rooms/%s/debrief" % room_id, options)


func terminal() -> Dictionary:
	return await request(HTTPClient.METHOD_GET, "/api/rooms/%s/terminal" % room_id)


func _poll() -> void:
	if _polling or room_id == "":
		return
	_polling = true
	var generation := _join_generation
	var res := await request(HTTPClient.METHOD_GET, "/api/rooms/%s/view" % room_id, null, "", view_etag)
	if generation != _join_generation:
		return
	_polling = false
	var now := Time.get_ticks_msec() / 1000.0
	if res.get("status") == 304 and not res.get("network_error", false) and not view.is_empty():
		last_poll_success_at = now
		polling_stale = false
		view.erase("_client_frozen_hour")
		return
	if res["ok"] and res["data"] is Dictionary:
		if int(res["data"].get("version", -1)) < int(view.get("version", -1)):
			_mark_stale(now)
			return
		view_etag = WorldRules.header_value(res["headers"], "etag")
		view = res["data"].duplicate(true)
		view.erase("_client_frozen_hour")
		view_received_at = Time.get_ticks_msec() / 1000.0
		last_poll_success_at = now
		polling_stale = false
		view_changed.emit(view)
	else:
		_mark_stale(now)


func _mark_stale(now: float) -> void:
	if not polling_stale and not view.is_empty():
		view["_client_frozen_hour"] = WorldRules.clock_hour(view, maxf(0.0, now - view_received_at))
	polling_stale = true


func poll_state(now := -1.0) -> Dictionary:
	if now < 0:
		now = Time.get_ticks_msec() / 1000.0
	var age := maxf(0.0, now - (last_poll_success_at if last_poll_success_at >= 0.0 else _joined_at))
	if room_id != "" and age >= STALE_SECONDS:
		_mark_stale(now)
	return {"stale": polling_stale, "age_seconds": age, "has_view": not view.is_empty()}


# ---------------- live presence ----------------

func _process(_delta: float) -> void:
	poll_state()
	if room_id == "" or token == "":
		return
	var now := Time.get_ticks_msec() / 1000.0
	if _ws == null:
		if now >= _ws_retry_at and WorldRules.presence_retry(_ws_attempt, _ws_opened):
			_ws = WebSocketPeer.new()
			_ws_hello = false
			if _ws.connect_to_url(WorldRules.presence_url(base_url, room_id)) != OK:
				_presence_closed(now)
		return
	_ws.poll()
	match _ws.get_ready_state():
		WebSocketPeer.STATE_OPEN:
			if not _ws_hello:
				_ws_hello = true
				_ws_opened = true
				_ws.send_text(JSON.stringify({"type": "hello", "token": token}))
			while _ws.get_available_packet_count() > 0:
				var msg: Variant = JSON.parse_string(_ws.get_packet().get_string_from_utf8())
				if msg is Dictionary:
					handle_presence(msg)
		WebSocketPeer.STATE_CLOSED:
			_presence_closed(now)


## Applies one server frame. Public so headless tests can drive it without a socket.
func handle_presence(msg: Dictionary) -> void:
	match str(msg.get("type", "")):
		"welcome":
			presence_live = true
			_ws_attempt = 0
			var partners: Dictionary = msg.get("partners", {}) if msg.get("partners") is Dictionary else {}
			for r in partners:
				_emit_move(str(r), partners[r])
		"presence":
			_emit_move(str(msg.get("role", "")), msg)
		"left":
			partner_left.emit(str(msg.get("role", "")))
		"version":  # the room changed: fetch the view now instead of at the next poll tick
			if int(msg.get("version", -1)) != int(view.get("version", -1)):
				_poll()


func _emit_move(role: String, p: Variant) -> void:
	if p is Dictionary:
		partner_moved.emit(role, Vector3(float(p.get("x", 0.0)), 0.0, float(p.get("z", 0.0))), str(p.get("location", "")))


## Called every frame with the local avatar; sends only real steps, at most every PRESENCE_SEND_SECONDS.
func send_move(pos: Vector3, location: String) -> void:
	var now := Time.get_ticks_msec() / 1000.0
	if not presence_live or not WorldRules.should_send_move(_last_sent, pos, now - _last_sent_at):
		return
	_last_sent = pos
	_last_sent_at = now
	_ws.send_text(JSON.stringify(WorldRules.move_frame(pos, location)))


func _presence_closed(now: float) -> void:
	var was_live := presence_live
	presence_live = false
	_ws = null
	_ws_attempt += 1
	_ws_retry_at = now + WorldRules.reconnect_delay(_ws_attempt)
	if was_live:  # the partner may still be there; fall back to the view's last-decision placement
		partner_left.emit("")


func _close_presence() -> void:
	if _ws:
		_ws.close()
	_ws = null
	presence_live = false
