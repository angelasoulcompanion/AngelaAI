#!/bin/bash
# Stop Angela Web Chat Services

echo "🛑 Stopping Angela Web Chat Services..."

# Stop Backend API
pkill -f "uvicorn main:app" && echo "   ✅ API stopped" || echo "   ℹ️  API not running"

# Stop Frontend Web
pkill -f "vite" && echo "   ✅ Web stopped" || echo "   ℹ️  Web not running"

echo ""
echo "✅ Angela Web Chat services stopped"
