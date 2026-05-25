#!/bin/bash
# stash-filemonitor.sh — host-level file watcher for Stash on Unraid
# Watches library/download paths and triggers Stash scan on new video files
#
# DEPLOYED TO:  /boot/config/scripts/stash-filemonitor.sh  (on Unraid)
# STARTED BY:   /boot/config/go (runs on every Unraid boot)
# LOG:          /var/log/stash-filemonitor.log
# DEPLOYED:     2026-05-13 by Claude Cowork
#
# WHY THIS EXISTS:
#   The Stash "FileMonitor" plugin explicitly refuses to run inside Docker.
#   This script runs on the Unraid host directly, using inotifywait to watch
#   the same paths Stash has configured as libraries. When a new video file
#   arrives (via torrent/usenet download or direct copy), it fires a Stash
#   GraphQL metadataScan — which is step 3 in the automated pipeline.
#
# RESTART:
#   nohup bash /boot/config/scripts/stash-filemonitor.sh </dev/null >> /var/log/stash-filemonitor.log 2>&1 &
#
# CHECK STATUS:
#   pgrep -a inotifywait | grep -v changes.txt
#   tail -20 /var/log/stash-filemonitor.log

STASH_URL="http://192.168.1.147:9999"
STASH_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJyb290Iiwic3ViIjoiQVBJS2V5IiwiaWF0IjoxNzcyNzU0MTc3fQ.10aU5TzoxuG6GJ-ECsaRQi28SR8xWsn3q5uIBeGebjc"
LOGFILE="/var/log/stash-filemonitor.log"

# Host-side paths (container /data → /mnt/user/adult, /downloads → /mnt/user/torrents)
WATCH_PATHS=(
    "/mnt/user/adult/movies"
    "/mnt/user/adult/scenes"
    "/mnt/user/torrents/Complete/xxx"
    "/mnt/user/torrents/usenet/_complete/xxx"
)

SCAN_MUTATION='{"query":"mutation { metadataScan(input: {scanGeneratePreviews: false, scanGenerateCovers: true, scanGenerateImagePreviews: false}) }"}'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"
}

trigger_scan() {
    local file="$1"
    log "New file: $file — triggering Stash scan"
    result=$(curl -s -X POST "$STASH_URL/graphql" \
        -H "Content-Type: application/json" \
        -H "ApiKey: $STASH_API_KEY" \
        -d "$SCAN_MUTATION" 2>&1)
    log "Stash response: $result"
}

log "=== Stash file monitor starting ==="
log "Watching: ${WATCH_PATHS[*]}"

ACTIVE_PATHS=()
for path in "${WATCH_PATHS[@]}"; do
    if [ -d "$path" ]; then
        ACTIVE_PATHS+=("$path")
        log "Watching: $path"
    else
        log "SKIP (not found): $path"
    fi
done

if [ ${#ACTIVE_PATHS[@]} -eq 0 ]; then
    log "ERROR: No valid watch paths found — exiting"
    exit 1
fi

LAST_SCAN=0

inotifywait -m -r -q \
    -e close_write,moved_to \
    "${ACTIVE_PATHS[@]}" \
    --format '%w%f' 2>/dev/null | \
while IFS= read -r FILE; do
    case "${FILE,,}" in
        *.mp4|*.mkv|*.avi|*.wmv|*.mov|*.m4v|*.flv|*.ts|*.strm)
            NOW=$(date +%s)
            if (( NOW - LAST_SCAN >= 30 )); then
                trigger_scan "$FILE"
                LAST_SCAN=$NOW
            else
                log "Debounced (scan pending): $FILE"
            fi
            ;;
    esac
done
