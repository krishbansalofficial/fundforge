#!/usr/bin/env bash
# Host-local release, supplied by the manual release workflow. No source checkout is changed.
set -euo pipefail
release_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
usage() { echo 'usage: release.sh ENV_FILE API_DIGEST WEB_DIGEST BACKUP_DIGEST [--allow-incompatible] [--dry-run]' >&2; exit 2; }
[[ $# -ge 4 ]] || usage
env_file=$1
export FUNDFORGE_API_IMAGE=$2 FUNDFORGE_WEB_IMAGE=$3 FUNDFORGE_BACKUP_IMAGE=$4
shift 4
allow_incompatible=0
dry_run=0
while [[ $# -gt 0 ]]; do
    case $1 in --allow-incompatible) allow_incompatible=1 ;; --dry-run) dry_run=1 ;; *) usage ;; esac
    shift
done
[[ -f "$env_file" ]] || { echo 'Missing host environment file' >&2; exit 2; }
for ref in "$FUNDFORGE_API_IMAGE" "$FUNDFORGE_WEB_IMAGE" "$FUNDFORGE_BACKUP_IMAGE"; do
    [[ $ref =~ ^ghcr\.io/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$ ]] || { echo 'Image references must be GHCR sha256 digests' >&2; exit 2; }
done
compose=(docker compose --project-name fundforge --env-file "$env_file" -f "$release_dir/deploy/compose.prod.yaml" -f "$release_dir/deploy/compose.images.yaml")
# Quiet rendering validates interpolation without logging passwords or full environment values.
"${compose[@]}" config --quiet
if (( dry_run )); then
    echo 'Release configuration valid; no pull, database operation or container change performed.'
    exit 0
fi
"${compose[@]}" pull api web backup
"${compose[@]}" up -d --wait --wait-timeout 120 db
old_api=$("${compose[@]}" ps -q api)
old_web=$("${compose[@]}" ps -q web)
old_backup=$("${compose[@]}" ps -q backup)
upgrade_started=0
restart_old() {
    status=$?
    if (( status != 0 && upgrade_started == 0 )); then
        [[ -z "$old_api" ]] || docker start "$old_api" >/dev/null || true
        [[ -z "$old_web" ]] || docker start "$old_web" >/dev/null || true
    fi
    exit "$status"
}
trap restart_old EXIT
if [[ -n "$old_api" ]]; then
    [[ -n "$old_backup" ]] || { echo 'Existing API needs its running backup container for a verified pre-upgrade archive' >&2; exit 1; }
    # Quiesce ingress and the server clock so no commands can appear after the snapshot.
    docker stop "$old_web" "$old_api" >/dev/null 2>&1 || {
        # API-only deployments have no web container.
        [[ -n "$old_web" ]] && exit 1
        docker stop "$old_api" >/dev/null
    }
    archive="/backups/pre-release-$(date -u +%Y%m%dT%H%M%SZ)-$$.dump"
    "${compose[@]}" exec -T backup python -m fundforge.backup dump "$archive"
    "${compose[@]}" exec -T backup python -m fundforge.backup check "$archive"
    # Candidate code restores the same archive into scratch and verifies room compatibility.
    # A successful CLI check alone may report incompatible rooms, so inspect the typed report.
    "${compose[@]}" run --rm --no-deps --entrypoint python backup -c '
import json, os, sys
from pathlib import Path
from fundforge.backup import check
report = check(os.environ["DATABASE_URL"], Path(sys.argv[1]))
bad = [rid for rid, value in report["rooms"].items() if value["status"] != "verified"]
print(json.dumps({"rooms": len(report["rooms"]), "incompatible_rooms": bad}, sort_keys=True))
if bad and sys.argv[2] != "1":
    raise SystemExit("Candidate cannot replay all pinned rooms; keep the prior release or explicitly acknowledge incompatibility")
' "$archive" "$allow_incompatible"
    echo "Pre-upgrade archive retained: $archive (plus manifest)"
else
    # Never treat a populated database with missing application containers as a fresh install.
    tables=$("${compose[@]}" exec -T db psql -U fundforge -d fundforge -Atc "select count(*) from information_schema.tables where table_schema='public'")
    [[ $tables == 0 ]] || { echo 'Existing database without running old API: restore the prior stack before releasing' >&2; exit 1; }
    echo 'Fresh database; no pre-existing rooms to archive.'
fi
upgrade_started=1
"${compose[@]}" up -d --no-build --wait --wait-timeout 180 api web backup caddy
# Verify same-origin routing from the private Docker network; TLS/Internet checks stay host-specific.
"${compose[@]}" exec -T web node -e '
Promise.all([fetch("http://api:8000/api/ready"), fetch("http://127.0.0.1:3000/")]).then(rs => {
  if (rs.some(r => !r.ok)) process.exit(1);
}).catch(() => process.exit(1));'
# Record only successful release image identity; secrets remain in the separate host env file.
printf '%s\n' "$FUNDFORGE_API_IMAGE" "$FUNDFORGE_WEB_IMAGE" "$FUNDFORGE_BACKUP_IMAGE" > "$release_dir/images.deployed.txt"
echo 'Release ready. Confirm public TLS and preserve the pre-upgrade archive off-host.'
