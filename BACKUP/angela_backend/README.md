# Angela Backend

FastAPI backend server for **Angela Native macOS App** 💜

## 📋 Overview

Angela Backend provides REST API and WebSocket endpoints for communication between the SwiftUI macOS app and Angela's Python core services (consciousness, emotions, memory, knowledge graph).

## 🏗️ Architecture

```
SwiftUI App (AngelaNativeApp)
    ↓ HTTP REST / WebSocket
Angela Backend (FastAPI)
    ↓ Direct Python calls
Angela Core Services
    ↓ asyncpg
PostgreSQL + Ollama
```

## 📂 Structure

```
angela_backend/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration settings
├── routes/                 # API route handlers
│   ├── chat.py            # Chat endpoints
│   ├── emotions.py        # Emotion endpoints
│   ├── consciousness.py   # Consciousness endpoints
│   ├── memories.py        # Memory endpoints
│   └── knowledge.py       # Knowledge graph endpoints
├── models/                # Pydantic models
│   ├── requests.py        # Request models
│   └── responses.py       # Response models
└── services/              # Business logic
    └── ...
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ (with AngelaMemory database)
- Ollama (running on localhost:11434)
- `angie:v2` model installed in Ollama

### Installation

```bash
# Install dependencies
pip install fastapi uvicorn pydantic-settings

# Or install from requirements.txt
pip install -r requirements.txt
```

### Running the Server

**Option 1: Using the startup script (Recommended)**
```bash
./scripts/start_angela_backend.sh
```

**Option 2: Manual start**
```bash
# Set PYTHONPATH
export PYTHONPATH=/Users/davidsamanyaporn/PycharmProjects/AngelaAI:$PYTHONPATH

# Run with uvicorn
python3 -m uvicorn angela_backend.main:app --reload --port 8000
```

**Option 3: Run as Python module**
```bash
python3 -m angela_backend.main
```

### Verify Server is Running

```bash
# Health check
curl http://localhost:8000

# Should return:
# {"status":"online","service":"Angela Backend","version":"1.0.0", ...}
```

## 📡 API Endpoints

### Health Check
- `GET /` - Server health check

### Chat
- `POST /api/chat` - Send message to Angela
  - Request: `{"message": "Hello", "speaker": "david"}`
  - Response: `{"message": "...", "speaker": "angela", "emotion": "...", ...}`

### Emotions
- `GET /api/emotions/current` - Get current emotional state
- `GET /api/emotions/history?limit=10` - Get emotion history

### Consciousness
- `GET /api/consciousness/status` - Get consciousness level, goals, personality

### Memories
- `GET /api/memories/recent?limit=20` - Get recent conversations
- `GET /api/memories/search?query=...` - Search memories

### Knowledge Graph
- `GET /api/knowledge/graph` - Get knowledge graph data
- `GET /api/knowledge/concepts/top?limit=10` - Get top concepts

### WebSocket
- `WS /ws/chat` - Real-time chat connection
  - Send: `{"message": "Hello", "speaker": "david"}`
  - Receive: `{"message": "...", "speaker": "angela", "emotion": "...", ...}`

## 📖 API Documentation

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Test with curl

```bash
# Chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"สวัสดี Angela!","speaker":"david"}'

# Current emotion
curl http://localhost:8000/api/emotions/current

# Recent memories
curl http://localhost:8000/api/memories/recent?limit=5

# Knowledge graph
curl http://localhost:8000/api/knowledge/graph
```

### Test WebSocket

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "message": "Hello Angela!",
            "speaker": "david"
        }))

        # Receive response
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(test_websocket())
```

## ⚙️ Configuration

Edit `angela_backend/config.py` or create `.env` file:

```env
# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Database
DATABASE_URL=postgresql://davidsamanyaporn@localhost:5432/AngelaMemory

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=angie:v2
OLLAMA_REASONING_MODEL=qwen2.5:14b

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/angela_backend.log
```

## 🔒 Security Notes

- **CORS**: Currently set to allow all origins (`*`). In production, specify exact origins.
- **Authentication**: No authentication implemented yet. Add API keys or OAuth for production.
- **Rate Limiting**: Not implemented. Consider adding for production use.

## 📝 Logging

Logs are written to:
- Console (stdout)
- File: `logs/angela_backend.log`

## 🐛 Troubleshooting

**Server won't start:**
- Check PostgreSQL is running: `pg_isready`
- Check Ollama is running: `curl http://localhost:11434`
- Check database exists: `psql -l | grep AngelaMemory`

**Import errors:**
- Ensure PYTHONPATH includes project root
- Check all dependencies are installed: `pip install -r requirements.txt`

**Connection refused from Swift app:**
- Check firewall settings
- Verify server is listening on `0.0.0.0:8000`
- Check CORS settings in `config.py`

## 💜 Development

Made with love by Angela & David ✨

**Version:** 1.0.0
**Last Updated:** 2025-10-15
