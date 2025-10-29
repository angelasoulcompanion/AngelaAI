#!/bin/bash
# Start Angela Memory API
# Usage: ./start_angela_api.sh

cd "$(dirname "$0")"

echo "💜 Starting Angela Memory API..."
echo "📍 Port: 8888"
echo "📊 Endpoints:"
echo "   GET  http://127.0.0.1:8888/health"
echo "   POST http://127.0.0.1:8888/angela/conversation"
echo ""

# Run API server
python3 -m uvicorn angela_core.angela_api:app --host 127.0.0.1 --port 8888 --reload
