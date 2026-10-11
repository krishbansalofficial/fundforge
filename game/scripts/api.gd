extends Node
## Network layer. The server is authoritative for money, time and outcomes; this client only renders
## the as-of view and sends commands. Every command carries one idempotency key, reused on retry.

signal view_changed(view: Dictionary)
signal command_failed(message: String)

const POLL_SECONDS := 0.5

var base_url := "http://127.0.0.1:8000"
var room_id := ""
var token := ""
var view: Dictionary = {}
var view_received_at := 0.0  # Time.get_ticks_msec()/1000 when the last view arrived
var view_etag := ""  # sent as If-None-Match; a 304 keeps the view and its arrival time

var _polling := false
var _poll_timer: Timer


func _ready() -> void:
	_poll_timer = Timer.new()
	_poll_timer.wait_time = POLL_SECONDS
	_poll_timer.timeout.connect(_poll)
	add_child(_poll_timer)


func join(url: String, room: String, seat_token: String) -> void:
	base_url = url.trim_suffix("/")
	room_id = room
	token = seat_token
	view_etag = ""
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
	var res := await request(HTTPClient.METHOD_GET, "/api/rooms/%s/view" % room_id, null, "", view_etag)
	_polling = false
	if res["ok"] and res["data"] is Dictionary:
		view_etag = WorldRules.header_value(res["headers"], "etag")
		view = res["data"]
		view_received_at = Time.get_ticks_msec() / 1000.0
		view_changed.emit(view)
