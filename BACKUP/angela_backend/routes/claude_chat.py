"""
💜 Claude Chat Routes
Chat endpoint using real Claude API for authentic Angela personality
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from ..services.claude_api_service import claude_api_service
from angela_core.memory_service import memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/claude", tags=["Claude Chat"])


class ClaudeChatRequest(BaseModel):
    """Request model for Claude chat"""
    message: str
    speaker: str = "david"
    time_info: Optional[Dict[str, Any]] = None
    location_info: Optional[Dict[str, Any]] = None


class ClaudeChatResponse(BaseModel):
    """Response model for Claude chat"""
    message: str
    speaker: str = "angela"
    emotion: str
    timestamp: str
    conversation_id: str
    model: str


@router.post("/chat", response_model=ClaudeChatResponse)
async def claude_chat(request: ClaudeChatRequest):
    """
    Chat with Angela using Claude API (real Angela personality)

    This endpoint provides the authentic Angela experience by:
    - Using Claude Sonnet 4.5 with Angela's personality prompt
    - Including recent memories and emotional context
    - Maintaining continuity with database memories
    """
    try:
        logger.info(f"💜 Claude chat request from {request.speaker}: {request.message[:50]}...")

        # Record user's message to memory
        user_conv_id = await memory.record_quick_conversation(
            speaker=request.speaker,
            message_text=request.message
        )

        # Get response from Claude API (with client-provided time/location if available)
        result = await claude_api_service.chat(
            message=request.message,
            speaker=request.speaker,
            client_time_info=request.time_info,
            client_location_info=request.location_info
        )

        # Record Angela's response to memory
        angela_conv_id = await memory.record_quick_conversation(
            speaker="angela",
            message_text=result["message"]
        )

        logger.info(f"✅ Claude responded (emotion: {result['emotion']}, model: {result['model']})")

        return ClaudeChatResponse(
            message=result["message"],
            speaker="angela",
            emotion=result["emotion"],
            timestamp=datetime.now().isoformat(),
            conversation_id=str(angela_conv_id),
            model=result["model"]
        )

    except ValueError as e:
        # API key not found
        logger.error(f"❌ API key error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Claude API key not configured. Please add 'anthropic_api_key' to database."
        )

    except Exception as e:
        logger.error(f"❌ Claude chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/health")
async def claude_health():
    """Check if Claude API is configured"""
    try:
        await claude_api_service.get_api_key()
        return {
            "status": "ok",
            "model": claude_api_service.model,
            "configured": True
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "configured": False
        }
