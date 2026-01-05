#!/bin/bash
# Angela Telegram Daemon Startup Script
# Waits for PostgreSQL and starts the Telegram auto-reply service

export PATH="/opt/homebrew/bin:/opt/anaconda3/bin:$PATH"
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI

# Wait for PostgreSQL to be ready (max 60 seconds)
echo "[$(date)] Waiting for PostgreSQL..."
for i in {1..12}; do
    if /opt/homebrew/bin/pg_isready -h localhost -p 5432 -U davidsamanyaporn > /dev/null 2>&1; then
        echo "[$(date)] PostgreSQL is ready!"
        break
    fi
    echo "[$(date)] PostgreSQL not ready, waiting... ($i/12)"
    sleep 5
done

# Start the Telegram daemon
echo "[$(date)] Starting Angela Telegram Daemon..."
exec /opt/anaconda3/bin/python3 -u angela_core/daemon/telegram_daemon.py
