#!/bin/sh
# Brings the production stack up on https://localhost (Caddy's internal CA) and checks the deploy contract:
# TLS routing, /metrics hidden publicly, no published database port, non-root app processes, a real
# two-seat game through the proxy that replays to a verified journal, and a verified startup backup.
#   deploy/smoke.sh [extra `compose up` flags, e.g. --no-build]
# Leaves the stack running on failure for inspection; `docker compose -f deploy/compose.prod.yaml down -v` cleans up.
set -eu
cd "$(dirname "$0")/.."
env_file=$(mktemp)
printf 'FUNDFORGE_DOMAIN=localhost\nPOSTGRES_PASSWORD=%s\nBACKUP_ON_START=1\nFUNDFORGE_CLOCK=0\n' "$(od -An -tx1 -N16 /dev/urandom | tr -d ' \n')" > "$env_file"
compose="docker compose -f deploy/compose.prod.yaml --env-file $env_file"
curl="curl -sk --noproxy localhost,127.0.0.1"
fail() { echo "deploy smoke FAILED: $*" >&2; $compose ps >&2; exit 1; }

$compose up -d --wait "$@"
for _ in $(seq 60); do [ "$($curl https://localhost/api/health 2>/dev/null)" = '{"ok":true}' ] && break; sleep 1; done
[ "$($curl https://localhost/api/health)" = '{"ok":true}' ] || fail "API health through Caddy"
[ "$($curl -o /dev/null -w '%{http_code}' https://localhost/)" = 200 ] || fail "web desk through Caddy"
[ "$($curl -o /dev/null -w '%{http_code}' https://localhost/metrics)" = 404 ] || fail "/metrics is public"
$curl http://127.0.0.1:${METRICS_PORT:-9464}/metrics | grep -q '^fundforge_' || fail "host-local /metrics"
[ -z "$(docker port "$($compose ps -q db)")" ] || fail "database port is published"
for s in api web backup; do
    [ "$($compose exec -T "$s" id -u)" != 0 ] || fail "$s runs as root"
done
python3 - <<'EOF' || fail "two-seat game through Caddy"
import json, ssl
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener
http = build_opener(ProxyHandler({}), HTTPSHandler(context=ssl._create_unverified_context()))
def call(path, token=None, body=None, key=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    data = json.dumps(body).encode() if body is not None else None
    return json.load(http.open(Request("https://localhost" + path, headers=headers, data=data)))
room = call("/api/rooms", body={"pm_name": "Smoke PM", "mp_name": "Smoke MP"})
prefix, pm, mp = "/api/rooms/" + room["room_id"], room["tokens"]["pm"], room["tokens"]["mp"]
cover = {"order_id": "smoke-cover", "sym": "BRIN", "side": "COVER", "qty": 1250}
package = call(prefix + "/commands", pm, {"type": "propose", "package_id": "smoke", "orders": [cover]}, "propose")
call(prefix + "/commands", mp, {"type": "sign", "package_id": "smoke", "digest": package["digest"]}, "sign")
for i in range(30):
    if call(prefix + "/view", pm).get("outcome") is not None:
        break
    for role, token in (("pm", pm), ("mp", mp)):
        version = call(prefix + "/view", token)["version"]
        call(prefix + "/commands", token, {"type": "ready", "version": version, "skip": True}, f"ready-{i}-{role}")
outcome, verified = call(prefix + "/view", pm)["outcome"], call(prefix + "/verify", pm)
assert outcome is not None and verified["ok"], verified
print(f"game: {outcome['label']} in {i} rounds, version {verified['version']} verified")
EOF
# Live presence is a WebSocket: Caddy must pass the upgrade through (the server then waits for a hello).
upgrade=$($curl --http1.1 -o /dev/null -w '%{http_code}' --max-time 3 -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
    -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
    https://localhost/api/rooms/none/presence || true)
[ "$upgrade" = 101 ] || fail "presence WebSocket upgrade through Caddy (got $upgrade)"
backup=$($compose ps -q backup)
for _ in $(seq 60); do docker logs "$backup" 2>&1 | grep -q '^backup: verified' && break; sleep 1; done
docker logs "$backup" 2>&1 | grep -q '^backup: verified' || fail "startup backup was not restored and verified"
rm -f "$env_file"
echo "deploy smoke passed"
