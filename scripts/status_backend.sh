#!/bin/bash
# Check AngelaNova Backend status
# Usage: ./scripts/status_backend.sh

echo "🔍 Checking AngelaNova Backend status..."
echo ""

# Check if process is running
if ps aux | grep -v grep | grep -q "angela_backend.main"; then
    echo "✅ Backend is RUNNING"
    echo ""
    echo "Process info:"
    ps aux | grep -v grep | grep "angela_backend.main"
    echo ""

    # Check port
    if lsof -i :8000 > /dev/null 2>&1; then
        echo "✅ Port 8000 is OPEN"
        lsof -i :8000
    else
        echo "❌ Port 8000 is CLOSED"
    fi
    echo ""

    # Test API
    echo "Testing API endpoint..."
    if curl -s http://127.0.0.1:8000 > /dev/null 2>&1; then
        echo "✅ API is RESPONDING"
        curl -s http://127.0.0.1:8000 | head -5
    else
        echo "❌ API is NOT responding"
    fi
else
    echo "❌ Backend is NOT RUNNING"
    echo ""
    echo "To start: ./scripts/start_backend.sh"
fi
