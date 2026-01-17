#!/bin/bash
# Angela Daemon Delayed Start Script
# Waits for PostgreSQL to be fully ready before starting daemon

LOGFILE="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_daemon_startup.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

log "=== Angela Daemon Delayed Start ==="

# Wait 10 seconds to allow PostgreSQL to start
log "⏳ Waiting 10 seconds for PostgreSQL to be ready..."
sleep 10

# Check if PostgreSQL is responding
log "🔍 Checking PostgreSQL availability..."
for i in {1..5}; do
    if psql -d AngelaMemory -U davidsamanyaporn -c "SELECT 1" > /dev/null 2>&1; then
        log "✅ PostgreSQL is ready!"
        break
    else
        if [ $i -lt 5 ]; then
            log "⏳ PostgreSQL not ready yet, waiting... (attempt $i/5)"
            sleep 2
        else
            log "⚠️  PostgreSQL not responding after 5 attempts, starting daemon anyway (has retry logic)"
        fi
    fi
done

# Start Angela daemon
log "🚀 Starting Angela daemon..."
exec /Users/davidsamanyaporn/PycharmProjects/AngelaAI/.venv/bin/python3 /Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/angela_daemon.py
