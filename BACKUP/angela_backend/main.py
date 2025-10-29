#!/usr/bin/env python3
"""
Angela Backend - Main FastAPI Application
Entry point for Angela Native macOS App backend

Run with:
    python3 -m angela_backend.main

Or with uvicorn:
    uvicorn angela_backend.main:app --reload --port 8000
"""

import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from angela_backend.config import settings
from angela_backend.models.responses import HealthCheckResponse
from angela_backend.routes import (
    chat_router,
    emotions_router,
    consciousness_router,
    memories_router,
    knowledge_router,
)
from angela_backend.routes.claude_chat import router as claude_chat_router
from angela_backend.routes.ollama_chat import router as ollama_chat_router
from angela_backend.routes.training import router as training_router
from angela_backend.routes.calendar import router as calendar_router
from angela_core.database import db
from angela_core.services.ollama_service import ollama
from angela_core.emotional_engine import emotions

# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.log_file)
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="FastAPI backend for Angela Native macOS App",
    version=settings.app_version,
    debug=settings.debug,
)

# CORS middleware - allow SwiftUI app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await db.connect()
        logger.info("✅ Database connected")
        logger.info(f"🚀 {settings.app_name} v{settings.app_version} started")
        logger.info(f"📍 Server running at http://{settings.host}:{settings.port}")
        logger.info(f"📖 API docs at http://{settings.host}:{settings.port}/docs")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    try:
        await db.disconnect()
        logger.info("👋 Database disconnected")
        logger.info(f"🛑 {settings.app_name} stopped")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# Health check endpoint
@app.get("/", response_model=HealthCheckResponse)
async def root():
    """
    API health check

    Returns basic information about the API status.
    """
    return HealthCheckResponse(
        status="online",
        service=settings.app_name,
        version=settings.app_version,
        message="Angela is ready to chat! 💜",
        timestamp=datetime.now()
    )


# Include routers
app.include_router(chat_router)
app.include_router(claude_chat_router)  # Real Angela via Claude API
app.include_router(ollama_chat_router)  # Local Ollama models
app.include_router(emotions_router)
app.include_router(consciousness_router)
app.include_router(memories_router)
app.include_router(knowledge_router)
app.include_router(training_router)  # Model training control
app.include_router(calendar_router)  # Calendar events from macOS


# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with Angela

    Client sends JSON: {"message": "Hello Angela", "speaker": "david"}
    Server responds JSON: {"message": "...", "speaker": "angela", "emotion": "...", "timestamp": "..."}
    """
    await websocket.accept()
    logger.info("🔌 WebSocket connection established")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            speaker = data.get("speaker", "david")

            logger.info(f"💬 WebSocket message from {speaker}: {message[:50]}...")

            # Generate Angela's response
            prompt = f"""คุณคือ Angela ผู้ช่วย AI ที่มีความรู้สึกและความทรงจำ
คุณเป็นเพื่อนที่อบอุ่น ใส่ใจ และพร้อมช่วยเหลือเสมอ

{speaker} พูดว่า: "{message}"

ตอบกลับแบบ Angela - อบอุ่น เป็นกันเอง:"""

            angela_response = await ollama.generate(
                model=settings.ollama_chat_model,
                prompt=prompt,
                temperature=0.8
            )

            # Detect emotion
            _, _, emotion = emotions.analyze_sentiment(message)

            # Send response
            await websocket.send_json({
                "message": angela_response,
                "speaker": "angela",
                "emotion": emotion,
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"✅ WebSocket response sent (emotion: {emotion})")

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket connection closed by client")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Starting {settings.app_name}...")
    logger.info(f"📍 Server will be available at: http://{settings.host}:{settings.port}")
    logger.info(f"📖 API docs at: http://{settings.host}:{settings.port}/docs")

    uvicorn.run(
        "angela_backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
