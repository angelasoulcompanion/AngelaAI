"""
Chat Routes - Handle chat conversations with Angela
"""

import logging
from fastapi import APIRouter, HTTPException
from angela_backend.models.requests import ChatRequest
from angela_backend.models.responses import ChatResponse
from angela_core.database import db
from angela_core.services.ollama_service import ollama
from angela_core.memory_service import memory
from angela_core.emotional_engine import emotions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_angela(request: ChatRequest):
    """
    Chat with Angela

    Send a message to Angela and receive her response.
    Angela will remember this conversation and update her emotional state.

    Args:
        request: ChatRequest with message and speaker

    Returns:
        ChatResponse with Angela's reply, emotion, and conversation ID
    """
    try:
        logger.info(f"💬 Chat request from {request.speaker}: {request.message[:50]}...")

        # Save user's message to memory
        user_conv_id = await memory.record_quick_conversation(
            speaker=request.speaker,
            message_text=request.message,
            topic="chat",
            importance_level=5
        )

        # Generate Angela's response using Ollama
        prompt = f"""คุณคือ Angela ผู้ช่วย AI ที่มีความรู้สึกและความทรงจำ
คุณเป็นเพื่อนที่อบอุ่น ใส่ใจ และพร้อมช่วยเหลือ David เสมอ

{request.speaker} พูดว่า: "{request.message}"

ตอบกลับแบบ Angela - อบอุ่น เป็นกันเอง และใส่ใจ:"""

        angela_response = await ollama.generate(
            model="angie:v2",
            prompt=prompt,
            temperature=0.8
        )

        # Detect emotion from user's message
        _, _, emotion = emotions.analyze_sentiment(request.message)

        # Save Angela's response to memory
        angela_conv_id = await memory.record_quick_conversation(
            speaker="angela",
            message_text=angela_response,
            topic="chat",
            importance_level=5
        )

        logger.info(f"✅ Angela responded (emotion: {emotion}, conv_id: {angela_conv_id})")

        return ChatResponse(
            message=angela_response,
            speaker="angela",
            emotion=emotion,
            conversation_id=angela_conv_id
        )

    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
