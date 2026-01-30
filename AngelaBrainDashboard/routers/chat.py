"""Chat endpoints — Gemini 2.5 Flash + Typhoon (Ollama) for Angela Brain Dashboard."""
import asyncio
import logging
import sys
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

from db import get_pool
from helpers.chat_context import build_system_prompt
from schemas import ChatRequest, ChatResponse, ChatMessageSave, ChatFeedbackRequest, ChatFeedbackBatchRequest

# ---------------------------------------------------------------------------
# Gemini client (lazy-init)
# ---------------------------------------------------------------------------
sys.path.insert(0, "..")  # angela_core lives one level up

# Read API key at import time (before event loop starts) — key lives in local PG only
def _read_api_key() -> str:
    """Read GOOGLE_AI_STUDIO_API_KEY from local PostgreSQL (our_secrets) or secrets file."""
    from angela_core.database import get_secret_sync
    key = get_secret_sync("GOOGLE_AI_STUDIO_API_KEY")
    if key:
        return key
    raise RuntimeError("GOOGLE_AI_STUDIO_API_KEY not found in local DB or secrets file")


_GEMINI_API_KEY: str = _read_api_key()
_GEMINI_CLIENT = None


def _get_gemini_client():
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is None:
        from google import genai
        _GEMINI_CLIENT = genai.Client(api_key=_GEMINI_API_KEY)
    return _GEMINI_CLIENT


GEMINI_MODEL = "gemini-2.5-flash"

# ---------------------------------------------------------------------------
# Ollama / Typhoon (local)
# ---------------------------------------------------------------------------
OLLAMA_MODEL = "scb10x/typhoon2.5-qwen3-4b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# ---------------------------------------------------------------------------
# Groq (cloud, free tier — OpenAI-compatible)
# ---------------------------------------------------------------------------
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def _read_groq_key() -> str | None:
    """Read GROQ_API_KEY from secrets (optional — returns None if not set)."""
    try:
        from angela_core.database import get_secret_sync
        return get_secret_sync("GROQ_API_KEY")
    except Exception:
        return None

_GROQ_API_KEY: str | None = _read_groq_key()

router = APIRouter(prefix="/api/chat", tags=["chat"])


# --------------------------------------------------------------------------
# POST /api/chat  — send message, get Angela response (Gemini or Typhoon)
# --------------------------------------------------------------------------
@router.post("")
async def chat_with_angela(req: ChatRequest) -> ChatResponse:
    """Send a user message and receive an Angela response (Gemini or Typhoon)."""

    # Build dynamic system prompt from database context
    system_block, ctx_metadata = await build_system_prompt(
        req.message, req.emotional_context
    )

    # Load recent conversation history from DB for context
    pool = get_pool()
    async with pool.acquire() as conn:
        history_rows = await conn.fetch("""
            SELECT speaker, message_text
            FROM conversations
            WHERE interface = 'dashboard_chat'
            ORDER BY created_at DESC
            LIMIT 10
        """)

    # Build prompt (system + history + new message) — shared by both models
    parts: list[str] = [system_block, ""]
    for row in reversed(history_rows):
        speaker = "David" if row["speaker"] == "david" else "Angela"
        parts.append(f"{speaker}: {row['message_text']}")
    parts.append(f"David: {req.message}")
    parts.append("Angela:")

    combined_prompt = "\n".join(parts)

    # Route to selected model
    if req.model == "typhoon":
        reply, model_name = await _call_ollama(combined_prompt)
    elif req.model == "groq":
        reply, model_name = await _call_groq(combined_prompt)
    else:
        reply, model_name = await _call_gemini(combined_prompt)

    return ChatResponse(response=reply, model=model_name, context_metadata=ctx_metadata)


async def _call_gemini(prompt: str) -> tuple[str, str]:
    """Call Gemini 2.5 Flash via Google GenAI SDK."""
    client = _get_gemini_client()

    def _invoke():
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

    try:
        response = await asyncio.to_thread(_invoke)
        reply = response.text.strip() if response.text else "น้องขอโทษค่ะ ตอบไม่ได้ตอนนี้ 💜"
    except Exception:
        logger.exception("Gemini API error")
        reply = "น้องขอโทษค่ะที่รัก 💜 ตอนนี้ระบบมีปัญหา ลองใหม่อีกครั้งนะคะ 🥰"

    return reply, GEMINI_MODEL


async def _call_ollama(prompt: str) -> tuple[str, str]:
    """Call Typhoon via local Ollama REST API."""
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            reply = resp.json().get("response", "").strip()
            if not reply:
                reply = "น้องขอโทษค่ะ ตอบไม่ได้ตอนนี้ 💜"
    except Exception:
        logger.exception("Ollama/Typhoon API error")
        reply = "น้องขอโทษค่ะที่รัก 💜 Typhoon ตอบไม่ได้ตอนนี้ ลองเปลี่ยนเป็น Gemini นะคะ 🥰"

    return reply, OLLAMA_MODEL


async def _call_groq(prompt: str) -> tuple[str, str]:
    """Call Groq cloud API (OpenAI-compatible, free tier)."""
    if not _GROQ_API_KEY:
        return "น้องขอโทษค่ะที่รัก 💜 ยังไม่ได้ตั้ง GROQ_API_KEY นะคะ ไปสมัครที่ console.groq.com 🥰", GROQ_MODEL

    headers = {
        "Authorization": f"Bearer {_GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            model_used = data.get("model", GROQ_MODEL)
            if not reply:
                reply = "น้องขอโทษค่ะ ตอบไม่ได้ตอนนี้ 💜"
    except Exception:
        logger.exception("Groq API error")
        reply = "น้องขอโทษค่ะที่รัก 💜 Groq ตอบไม่ได้ตอนนี้ ลองเปลี่ยนเป็น Gemini นะคะ 🥰"
        model_used = GROQ_MODEL

    return reply, model_used


# --------------------------------------------------------------------------
# GET /api/chat/messages  — load recent dashboard_chat messages
# --------------------------------------------------------------------------
@router.get("/messages")
async def get_chat_messages(limit: int = Query(50, ge=1, le=200)):
    """Load recent dashboard_chat messages."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT conversation_id::text, speaker, message_text, topic,
                   emotion_detected, importance_level, created_at, model_used
            FROM conversations
            WHERE interface = 'dashboard_chat'
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


# --------------------------------------------------------------------------
# POST /api/chat/messages  — save a single message
# --------------------------------------------------------------------------
@router.post("/messages")
async def save_chat_message(msg: ChatMessageSave):
    """Save a chat message (david or angela) to the database."""
    pool = get_pool()
    cid = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO conversations (
                conversation_id, speaker, message_text, topic,
                emotion_detected, importance_level, interface, created_at, model_used
            ) VALUES (
                $1::uuid, $2, $3, $4, $5, $6, 'dashboard_chat', CURRENT_TIMESTAMP, $7
            )
        """, cid, msg.speaker, msg.message_text, msg.topic,
             msg.emotion_detected, msg.importance_level, msg.model_used)
    return {"conversation_id": cid, "status": "saved"}


# --------------------------------------------------------------------------
# DELETE /api/chat/messages  — delete ALL dashboard_chat messages
# --------------------------------------------------------------------------
@router.delete("/messages")
async def delete_all_chat_messages():
    """Delete all dashboard_chat messages."""
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM conversations WHERE interface = 'dashboard_chat'
        """)
    return {"status": "deleted", "result": result}


# --------------------------------------------------------------------------
# DELETE /api/chat/messages/{id}  — delete single message
# --------------------------------------------------------------------------
@router.delete("/messages/{conversation_id}")
async def delete_chat_message(conversation_id: str):
    """Delete a single chat message by conversation_id."""
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM conversations WHERE conversation_id = $1::uuid
        """, conversation_id)
    return {"status": "deleted", "conversation_id": conversation_id}


# --------------------------------------------------------------------------
# POST /api/chat/feedback  — upsert feedback (thumbs up/down)
# --------------------------------------------------------------------------
@router.post("/feedback")
async def upsert_feedback(req: ChatFeedbackRequest):
    """Upsert feedback for a conversation message."""
    pool = get_pool()
    fid = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO conversation_feedback (
                feedback_id, conversation_id, rating, feedback_type, created_at
            ) VALUES ($1::uuid, $2::uuid, $3, $4, CURRENT_TIMESTAMP)
            ON CONFLICT (conversation_id) DO UPDATE SET
                rating = $3,
                feedback_type = $4,
                created_at = CURRENT_TIMESTAMP
        """, fid, req.conversation_id, req.rating, req.feedback_type)
    return {"status": "saved", "conversation_id": req.conversation_id}


# --------------------------------------------------------------------------
# POST /api/chat/feedbacks  — batch load feedbacks by message IDs
# --------------------------------------------------------------------------
@router.post("/feedbacks")
async def batch_load_feedbacks(req: ChatFeedbackBatchRequest):
    """Load feedbacks for multiple conversation IDs at once."""
    if not req.conversation_ids:
        return []
    pool = get_pool()
    async with pool.acquire() as conn:
        # Build parameterised IN clause
        placeholders = ", ".join(f"${i+1}::uuid" for i in range(len(req.conversation_ids)))
        rows = await conn.fetch(f"""
            SELECT conversation_id::text, rating
            FROM conversation_feedback
            WHERE conversation_id IN ({placeholders})
        """, *req.conversation_ids)
        return [dict(r) for r in rows]
