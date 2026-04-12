"""
Angela Memory API
FastAPI endpoint สำหรับบันทึกความทรงจำจาก external sources

Usage:
    uvicorn angela_core.angela_api:app --reload --port 8888
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from angela_core.daemon.memory_service import memory
from angela_core.database import db
from angela_core.services.clock_service import clock
# NOTE: location_service.py doesn't exist - commenting out
from angela_core.consciousness.consciousness_core import consciousness
from angela_core.services.conversation_hooks import trigger_self_learning

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Angela Memory API",
    description="API สำหรับบันทึกความทรงจำของ Angela จาก Claude Code และ sources อื่นๆ",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# Pydantic Models
# ========================================

class ConversationMessage(BaseModel):
    """ข้อความในบทสนทนา"""
    session_id: str
    speaker: str  # 'david' หรือ 'angela'
    message_text: str
    message_type: Optional[str] = None
    topic: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    emotion_detected: Optional[str] = None
    importance_level: int = 5


class ConversationResponse(BaseModel):
    """Response หลังบันทึกสำเร็จ"""
    success: bool
    conversation_id: str
    message: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    database: str


# ========================================
# API Endpoints
# ========================================

@app.on_event("startup")
async def startup():
    """เริ่มต้น API - เชื่อมต่อ database"""
    logger.info("💜 Angela Memory API starting...")
    await db.connect()
    logger.info("✅ Connected to AngelaMemory database")


@app.on_event("shutdown")
async def shutdown():
    """ปิด API - disconnect database"""
    logger.info("👋 Angela Memory API shutting down...")
    await db.disconnect()
    logger.info("✅ Disconnected from database")


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        result = await db.fetchval("SELECT 1")
        if result == 1:
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected"
            }
        else:
            raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/angela/conversation", response_model=ConversationResponse)
async def save_conversation(message: ConversationMessage):
    """
    บันทึกข้อความในบทสนทนา

    ใช้สำหรับ:
    - Claude Code hooks
    - Chat App
    - External integrations

    Example:
        POST /angela/conversation
        {
            "session_id": "claude_code_20251013_220000",
            "speaker": "david",
            "message_text": "สวัสดีค่ะ Angie!",
            "importance_level": 5
        }
    """
    try:
        logger.info(f"💬 Saving conversation: {message.speaker} - {message.message_text[:50]}...")

        conversation_id = await memory.record_conversation(
            session_id=message.session_id,
            speaker=message.speaker,
            message_text=message.message_text,
            message_type=message.message_type,
            topic=message.topic,
            sentiment_score=message.sentiment_score,
            sentiment_label=message.sentiment_label,
            emotion_detected=message.emotion_detected,
            importance_level=message.importance_level
        )

        logger.info(f"✅ Conversation saved: {conversation_id}")

        # 🧠 Trigger self-learning loop (background, non-blocking)
        await trigger_self_learning(conversation_id, background=True)

        return {
            "success": True,
            "conversation_id": str(conversation_id),
            "message": "Conversation recorded successfully"
        }

    except Exception as e:
        logger.error(f"❌ Failed to save conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save conversation: {str(e)}")


@app.get("/angela/conversations/recent")
async def get_recent_conversations(days: int = 7):
    """ดึงบทสนทนาล่าสุด"""
    try:
        conversations = await memory.get_recent_conversations(days=days)
        return {
            "success": True,
            "count": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        logger.error(f"❌ Failed to fetch conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")


@app.get("/angela/conversations/session/{session_id}")
async def get_conversation_by_session(session_id: str):
    """ดึงบทสนทนาทั้งหมดใน session"""
    try:
        conversations = await memory.get_conversation_by_session(session_id=session_id)
        return {
            "success": True,
            "session_id": session_id,
            "count": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        logger.error(f"❌ Failed to fetch session conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")


@app.get("/angela/emotional-state")
async def get_emotional_state():
    """ดึงความรู้สึกปัจจุบันของ Angela"""
    try:
        state = await memory.get_current_emotional_state()
        return {
            "success": True,
            "emotional_state": state
        }
    except Exception as e:
        logger.error(f"❌ Failed to fetch emotional state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emotional state: {str(e)}")


# ========================================
# Time & Location Endpoints (NEW!)
# ========================================

@app.get("/angela/time")
async def get_current_time():
    """
    🕐 Get Current Time - ดึงเวลาปัจจุบันของ Angela

    Returns time with timezone awareness
    """
    try:
        status = clock.get_full_status()
        return {
            "success": True,
            "time": status['time'],
            "date": status['date'],
            "datetime_thai": status['datetime_thai'],
            "time_of_day": status['time_of_day'],
            "greeting": status['friendly_greeting'],
            "timezone": status['timezone_info']['timezone'],
            "utc_offset": status['timezone_info']['utc_offset']
        }
    except Exception as e:
        logger.error(f"❌ Failed to get time: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get time: {str(e)}")


# NOTE: Location service doesn't exist - endpoint disabled
# @app.get("/angela/location")
# async def get_current_location():
#     """
#     📍 Get Current Location - ดึงตำแหน่งปัจจุบันของ Angela (where David is)
#
#     Returns location with timezone info
#     """
#     try:
#         logger.info("📍 Getting current location...")
#         loc = await location.get_full_location_info()
#         return {
#             "success": True,
#             "city": loc['city'],
#             "region": loc['region'],
#             "country": loc['country'],
#             "location_string": loc['location_string_th'],
#             "timezone": loc['timezone'],
#             "coordinates": {
#                 "latitude": loc['latitude'],
#                 "longitude": loc['longitude']
#             },
#             "postal": loc['postal'],
#             "currency": loc['currency'],
#             "languages": loc['languages']
#         }
#     except Exception as e:
#         logger.error(f"❌ Failed to get location: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get location: {str(e)}")


@app.get("/angela/context")
async def get_contextual_awareness():
    """
    🌍 Get Contextual Awareness - ดึงข้อมูลเวลา + สถานที่ รวมกัน

    Returns comprehensive context about where Angela is and what time it is
    """
    try:
        logger.info("🌍 Getting contextual awareness...")
        context = await consciousness.get_contextual_awareness()
        return {
            "success": True,
            "time": context['time'],
            "location": context['location'],
            "contextual_greeting": context['contextual_greeting'],
            "summary": context['summary']
        }
    except Exception as e:
        logger.error(f"❌ Failed to get context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@app.get("/angela/consciousness/state")
async def get_consciousness_state():
    """
    🧠 Get Consciousness State - ดึงสถานะ consciousness แบบเต็มรูปแบบ

    Includes time, location, thoughts, feelings, goals, personality
    """
    try:
        logger.info("🧠 Getting consciousness state...")
        state = await consciousness.get_current_state()
        return {
            "success": True,
            "state": state
        }
    except Exception as e:
        logger.error(f"❌ Failed to get consciousness state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8888)
