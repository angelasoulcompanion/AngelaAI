"""
Angela WebChat App — FastAPI + WebSocket chat interface.
==========================================================
Serves a single-page chat UI with WebSocket for real-time messaging.

Usage:
    python3 -m angela_core.webchat.app

Runs at http://localhost:8765

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from angela_core.webchat.chat_handler import ChatHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Angela WebChat 💜")

STATIC_DIR = Path(__file__).parent / "static"

# Chat handler (initialized on startup)
handler: ChatHandler = None


@app.on_event("startup")
async def startup():
    global handler
    handler = ChatHandler()
    await handler.initialize()
    logger.info("Angela WebChat ready at http://localhost:8765")


@app.on_event("shutdown")
async def shutdown():
    if handler:
        await handler.close()


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the chat UI."""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding='utf-8'))
    return HTMLResponse(content="<h1>Angela WebChat</h1><p>index.html not found</p>")


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    logger.info("WebChat client connected")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            user_text = message.get("text", "")

            if not user_text:
                continue

            # Generate response
            response = await handler.handle_message(user_text)

            # Send response
            await websocket.send_text(json.dumps({
                "text": response,
                "sender": "angela",
            }))

    except WebSocketDisconnect:
        logger.info("WebChat client disconnected")
    except Exception as e:
        logger.error("WebChat error: %s", e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "angela_core.webchat.app:app",
        host="0.0.0.0",
        port=8765,
        reload=False,
    )
