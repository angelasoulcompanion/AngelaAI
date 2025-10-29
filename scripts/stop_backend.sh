#!/bin/bash
# Stop AngelaNova Backend (port 8000)
# Usage: ./scripts/stop_backend.sh

echo "🛑 Stopping AngelaNova Backend..."

# Check if running
if ! ps aux | grep -v grep | grep -q "angela_backend.main"; then
    echo "⚠️  Backend is not running"
    exit 1
fi

# Kill the process
pkill -f "angela_backend.main"

sleep 1

# Verify stopped
if ps aux | grep -v grep | grep -q "angela_backend.main"; then
    echo "❌ Failed to stop backend (trying force kill...)"
    pkill -9 -f "angela_backend.main"
    sleep 1
fi

if ! ps aux | grep -v grep | grep -q "angela_backend.main"; then
    echo "✅ Backend stopped successfully"
else
    echo "❌ Could not stop backend"
    exit 1
fi
