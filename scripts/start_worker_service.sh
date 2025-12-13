#!/bin/bash
# Start Angela Background Worker Service
# This service processes conversations in background with intelligent queue

PROJECT_DIR="/Users/davidsamanyaporn/PycharmProjects/AngelaAI"
LOG_FILE="$PROJECT_DIR/logs/worker_service.log"

echo "🚀 Starting Angela Background Worker Service..."

cd "$PROJECT_DIR"

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Start worker service
python3 angela_core/services/background_worker_service.py >> "$LOG_FILE" 2>&1 &

WORKER_PID=$!
echo "$WORKER_PID" > /tmp/angela_worker_service.pid

echo "✅ Worker Service started with PID: $WORKER_PID"
echo "📄 Logs: $LOG_FILE"
echo ""
echo "To stop: kill \$(cat /tmp/angela_worker_service.pid)"
