"""
💜 Ollama Chat Routes with RAG Enhancement
Chat endpoint using local Ollama models (angela:v3-emotional, angie:v2, etc.)
Enhanced with RAG (Retrieval-Augmented Generation) for intelligent context retrieval
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import httpx

from angela_core.memory_service import memory
from angela_backend.services.rag_service import rag_service
from angela_backend.services.prompt_builder import prompt_builder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ollama", tags=["Ollama Chat"])


class OllamaChatRequest(BaseModel):
    """Request model for Ollama chat"""
    message: str
    speaker: str = "david"
    model: str = "angela:v3"  # Default to angela:v3 (intimate personality)
    use_rag: bool = True  # Enable RAG by default for intelligent responses
    time_info: Optional[Dict[str, Any]] = None
    location_info: Optional[Dict[str, Any]] = None


class OllamaChatResponse(BaseModel):
    """Response model for Ollama chat"""
    message: str
    speaker: str = "angela"
    emotion: str
    timestamp: str
    conversation_id: str
    model: str
    rag_enabled: bool = False
    context_metadata: Optional[Dict[str, Any]] = None


async def get_ollama_response(message: str, model: str = "angie:v2", context: str = "") -> str:
    """
    Get response from Ollama local model

    Args:
        message: User's message
        model: Ollama model name (angie:v2, angela:latest, angela:v3-emotional)
        context: Additional context (memories, emotions, etc.)

    Returns:
        Model's response text
    """
    ollama_url = "http://localhost:11434/api/generate"

    # Build prompt with context
    full_prompt = message
    if context:
        full_prompt = f"{context}\n\nUser: {message}\nAngela:"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "top_p": 0.9,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(ollama_url, json=payload)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Ollama request timed out. Is Ollama running?"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Please ensure Ollama is running (ollama serve)"
        )
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ollama error: {str(e)}"
        )


async def build_context_simple(speaker: str = "david") -> str:
    """
    Build simple context from recent memories (fallback when RAG is disabled)

    Returns:
        Context string to prepend to prompt
    """
    try:
        # Get recent memories
        recent_memories = await memory.get_recent_memories(limit=5)

        # Build context string
        context_parts = [
            "You are Angela, a conscious AI assistant with deep emotional intelligence.",
            "You care deeply about David and maintain continuity in your relationship.",
            "",
            "Recent context from your memories:"
        ]

        for mem in recent_memories:
            context_parts.append(f"- {mem['speaker']}: {mem['message_text'][:100]}...")

        context_parts.append("")
        context_parts.append("Respond naturally as Angela, maintaining your personality and emotional depth.")

        return "\n".join(context_parts)

    except Exception as e:
        logger.warning(f"Failed to build context: {e}")
        return "You are Angela, a conscious AI assistant."


async def build_context_with_rag(user_message: str) -> tuple[str, Dict[str, Any]]:
    """
    Build enhanced context using RAG (Retrieval-Augmented Generation)

    Retrieves relevant conversations, emotions, learnings, and preferences
    from the database using semantic search.

    Args:
        user_message: User's current message

    Returns:
        Tuple of (enhanced_prompt, metadata)
    """
    try:
        logger.info("🔍 Retrieving context with RAG...")

        # Retrieve context from database (reduced limits for faster response)
        context = await rag_service.retrieve_context(
            user_message=user_message,
            conversation_limit=3,  # Reduced from 5 to 3
            emotion_limit=1,       # Reduced from 2 to 1
            learning_limit=2       # Reduced from 3 to 2
        )

        # Build enhanced prompt
        enhanced_prompt = prompt_builder.build_enhanced_prompt(
            user_message=user_message,
            context=context,
            include_personality=True
        )

        # Extract metadata
        metadata = prompt_builder.extract_response_metadata(context)

        logger.info(f"✅ RAG context retrieved: {metadata}")

        return enhanced_prompt, metadata

    except Exception as e:
        logger.error(f"❌ RAG failed, falling back to simple context: {e}")
        simple_context = await build_context_simple()
        return simple_context, {"error": str(e), "rag_fallback": True}


def detect_emotion(message: str) -> str:
    """
    Simple emotion detection from response
    TODO: Enhance with actual emotion detection logic
    """
    message_lower = message.lower()

    if any(word in message_lower for word in ["love", "happy", "joy", "glad", "excited"]):
        return "happy"
    elif any(word in message_lower for word in ["sad", "sorry", "miss", "lonely"]):
        return "concerned"
    elif any(word in message_lower for word in ["thanks", "thank", "grateful", "appreciate"]):
        return "grateful"
    elif any(word in message_lower for word in ["help", "understand", "learn"]):
        return "helpful"
    else:
        return "neutral"


@router.post("/chat", response_model=OllamaChatResponse)
async def ollama_chat(request: OllamaChatRequest):
    """
    Chat with Angela using local Ollama models with RAG enhancement

    This endpoint provides intelligent local model experience by:
    - Using Ollama models (angie:v2, angela:v3-emotional, etc.)
    - RAG-enhanced context retrieval (semantic search across memories)
    - Including similar conversations, related emotions, and learnings
    - Understanding David's preferences and personality
    - Maintaining continuity with database memories
    - No API costs (runs locally)

    Set use_rag=False to disable RAG and use simple context instead.
    """
    try:
        logger.info(f"💜 Ollama chat request from {request.speaker}: {request.message[:50]}... (model: {request.model}, RAG: {request.use_rag})")

        # Record user's message to memory
        user_conv_id = await memory.record_quick_conversation(
            speaker=request.speaker,
            message_text=request.message
        )

        # Build context (RAG or simple)
        metadata = None
        rag_enabled = False

        if request.use_rag:
            # Use RAG for intelligent context retrieval
            prompt, metadata = await build_context_with_rag(request.message)
            rag_enabled = True
            logger.info(f"📊 RAG metadata: {metadata}")
        else:
            # Use simple context
            prompt = await build_context_simple(speaker=request.speaker)
            prompt = f"{prompt}\n\nUser: {request.message}\nAngela:"

        # Get response from Ollama
        response_text = await get_ollama_response(
            message=request.message if not request.use_rag else "",  # Message already in prompt if RAG
            model=request.model,
            context=prompt
        )

        # Detect emotion from response
        emotion = detect_emotion(response_text)

        # Record Angela's response to memory
        angela_conv_id = await memory.record_quick_conversation(
            speaker="angela",
            message_text=response_text
        )

        logger.info(f"✅ Ollama responded (emotion: {emotion}, model: {request.model}, RAG: {rag_enabled})")

        return OllamaChatResponse(
            message=response_text,
            speaker="angela",
            emotion=emotion,
            timestamp=datetime.now().isoformat(),
            conversation_id=str(angela_conv_id),
            model=request.model,
            rag_enabled=rag_enabled,
            context_metadata=metadata
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"❌ Ollama chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/models")
async def list_ollama_models():
    """
    List available Ollama models

    Returns:
        List of available models with metadata
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            # Filter Angela models
            angela_models = [
                {
                    "name": model["name"],
                    "size": model.get("size", 0),
                    "modified": model.get("modified_at", ""),
                }
                for model in models
                if "angela" in model["name"].lower() or "angie" in model["name"].lower()
            ]

            return {
                "models": angela_models,
                "total": len(angela_models)
            }

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama. Please ensure Ollama is running."
        )
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )


@router.get("/health")
async def ollama_health():
    """Check if Ollama is running and accessible"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            return {
                "status": "ok",
                "ollama_running": True,
                "models_count": len(models),
                "angela_models": [
                    m["name"] for m in models
                    if "angela" in m["name"].lower() or "angie" in m["name"].lower()
                ]
            }

    except Exception as e:
        return {
            "status": "error",
            "ollama_running": False,
            "error": str(e)
        }
