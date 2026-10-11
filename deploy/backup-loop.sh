#!/bin/sh
# Nightly logical backup with restore-and-verify, for the `backup` service in compose.prod.yaml.
#   BACKUP_AT          UTC time of day, HH:MM (default 03:17)
#   BACKUP_KEEP_DAYS   verified archives older than this are deleted (default 14)
#   BACKUP_ON_START=1  also take one backup immediately (used to check a fresh deployment)
# An archive is kept only beside a `.verified` marker written after `fundforge.backup check` restored it
# into a scratch database and replay reproduced every room's digest and chain head. A failed check
# leaves `<archive>.FAILED` with the error and is never pruned. Archives contain seat-token hashes.
set -u
dir=/backups
at=${BACKUP_AT:-03:17}
keep=${BACKUP_KEEP_DAYS:-14}

run() {
    archive="$dir/fundforge-$(date -u +%Y%m%dT%H%M%SZ).dump"
    echo "backup: dumping to $archive"
    if python -m fundforge.backup dump "$archive" && python -m fundforge.backup check "$archive" > "$archive.verified.tmp" 2>&1; then
        mv "$archive.verified.tmp" "$archive.verified"
        echo "backup: verified $archive"
        find "$dir" -maxdepth 1 -name 'fundforge-*.dump*' ! -name '*.FAILED' -mtime +"$keep" -delete
    else
        [ -f "$archive.verified.tmp" ] && mv "$archive.verified.tmp" "$archive.FAILED" || echo "dump failed" > "$archive.FAILED"
        echo "backup: FAILED for $archive" >&2
        cat "$archive.FAILED" >&2
    fi
}

[ "${BACKUP_ON_START:-0}" = "1" ] && run
while true; do
    now=$(date -u +%s)
    next=$(date -u -d "today $at" +%s)
    [ "$next" -le "$now" ] && next=$((next + 86400))
    echo "backup: next run in $((next - now)) s"
    sleep $((next - now))
    run
done
