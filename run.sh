#!/bin/bash
# Chief of Staff hourly runner
# Invoked by cron every hour Mon-Fri 7am-6pm CDT (12:00-23:00 UTC)

set -euo pipefail

LOCK_FILE="/tmp/chiefofstaff.lock"
LOG_FILE="/home/user/chiefofstaff/cos.log"
CLAUDE_CMD="/opt/node22/bin/claude"
PROJECT_DIR="/home/user/chiefofstaff"

# Rotate log if over 5MB
if [ -f "$LOG_FILE" ] && [ "$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)" -gt 5242880 ]; then
    mv "$LOG_FILE" "${LOG_FILE}.prev"
fi

log() {
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $*" >> "$LOG_FILE"
}

# Prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -c%Y "$LOCK_FILE" 2>/dev/null || echo 0) ))
    if [ "$LOCK_AGE" -lt 3600 ]; then
        log "SKIP: previous run still in progress (lock age: ${LOCK_AGE}s)"
        exit 0
    else
        log "WARN: stale lock file found (age: ${LOCK_AGE}s), removing"
        rm -f "$LOCK_FILE"
    fi
fi

touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"; log "Run ended"' EXIT

log "Run started"

cd "$PROJECT_DIR"

"$CLAUDE_CMD" \
    --print \
    --max-turns 80 \
    --model claude-sonnet-4-6 \
    -p "Run your hourly Chief of Staff check now." \
    >> "$LOG_FILE" 2>&1

log "Run completed successfully"
