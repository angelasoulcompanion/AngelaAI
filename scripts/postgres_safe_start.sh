#!/bin/bash
# PostgreSQL Safe Start Script
# Cleans up stale lock files before starting PostgreSQL
# Prevents "lock file already exists" errors after Mac restart

PGDATA="/opt/homebrew/var/postgresql@14"
PIDFILE="$PGDATA/postmaster.pid"
LOGFILE="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/postgres_startup.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

log "=== PostgreSQL Safe Start ==="

# Check if lock file exists
if [ -f "$PIDFILE" ]; then
    PID=$(head -1 "$PIDFILE" 2>/dev/null)

    if [ -n "$PID" ]; then
        log "Found PID file with PID: $PID"

        # Check if process exists and is actually postgres
        if ps -p "$PID" > /dev/null 2>&1; then
            # Process exists - check if it's postgres
            if ps -p "$PID" | grep -q postgres; then
                log "✅ PostgreSQL already running (PID: $PID)"
                exit 0
            else
                PROCESS_NAME=$(ps -p "$PID" -o comm= 2>/dev/null)
                log "⚠️  Stale lock file detected! PID $PID is '$PROCESS_NAME', not postgres"
                log "🧹 Removing stale lock file: $PIDFILE"
                rm -f "$PIDFILE"
            fi
        else
            log "⚠️  Process $PID not running - stale lock file"
            log "🧹 Removing stale lock file: $PIDFILE"
            rm -f "$PIDFILE"
        fi
    else
        log "⚠️  Empty PID file found"
        log "🧹 Removing empty lock file: $PIDFILE"
        rm -f "$PIDFILE"
    fi
else
    log "✓ No lock file found - clean start"
fi

# Start PostgreSQL
log "🚀 Starting PostgreSQL..."
exec /opt/homebrew/opt/postgresql@14/bin/postgres -D "$PGDATA"
