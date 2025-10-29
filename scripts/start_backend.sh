#!/bin/bash
# Start AngelaNova Backend (port 8000)
# Usage: ./scripts/start_backend.sh

cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI

echo "🚀 Starting AngelaNova Backend..."

# Check if already running
if ps aux | grep -v grep | grep -q "angela_backend.main"; then
    echo "⚠️  Backend is already running!"
    ps aux | grep -v grep | grep "angela_backend.main"
    exit 1
fi

# Start backend in background
python3 -m angela_backend.main > logs/angela_backend.log 2>&1 &

sleep 2

# Check if started successfully
if ps aux | grep -v grep | grep -q "angela_backend.main"; then
    echo "✅ Backend started successfully!"
    echo "📍 Running on http://0.0.0.0:8000"
    echo "📖 API docs at http://0.0.0.0:8000/docs"
    echo "📝 Logs: tail -f logs/angela_backend.log"
else
    echo "❌ Failed to start backend"
    echo "Check logs: cat logs/angela_backend.log"
    exit 1
fi
