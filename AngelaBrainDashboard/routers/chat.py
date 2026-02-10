"""Chat endpoints — Gemini 2.5 Flash + Typhoon (Ollama) for Angela Brain Dashboard."""
import asyncio
import base64
import json
import logging
import sys
import uuid
from typing import AsyncGenerator, Optional

import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

from db import get_conn, get_pool
from helpers.chat_context import build_system_prompt
from helpers.emotional_pipeline import (
    detect_emotion,
    get_mirroring,
    build_mirroring_guidance,
    run_pipeline,
)
from helpers.self_learning import extract_learnings, save_learnings, reinforce_from_feedback
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
async def chat_with_angela(req: ChatRequest, conn=Depends(get_conn)) -> ChatResponse:
    """Send a user message and receive an Angela response (Gemini or Typhoon)."""

    # Build dynamic system prompt from database context
    system_block, ctx_metadata = await build_system_prompt(
        req.message, req.emotional_context
    )

    # Load recent conversation history from DB for context
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

    # Decode image if attached
    image_bytes: bytes | None = None
    image_mime: str = "image/jpeg"
    if req.image_data:
        try:
            image_bytes = base64.b64decode(req.image_data)
            image_mime = req.image_mime_type or "image/jpeg"
        except Exception:
            logger.warning("Failed to decode image_data base64")

    # Route to selected model
    if req.model == "typhoon":
        reply, model_name = await _call_ollama(combined_prompt)
    elif req.model == "groq":
        reply, model_name = await _call_groq(combined_prompt)
    else:
        reply, model_name = await _call_gemini(
            combined_prompt, image_bytes=image_bytes, image_mime=image_mime
        )

    return ChatResponse(response=reply, model=model_name, context_metadata=ctx_metadata)


# --------------------------------------------------------------------------
# POST /api/chat/stream  — SSE streaming endpoint (human-like experience)
# --------------------------------------------------------------------------
@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """Stream Angela's response via Server-Sent Events.

    SSE event types:
      - thinking: {step: str}          — what Angela is doing
      - token:    {text: str}          — streamed text chunk
      - metadata: {EmotionalMetadata}  — emotional pipeline result
      - done:     {model: str}         — stream complete
    """
    return StreamingResponse(
        _stream_response(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(event: str, data: dict) -> str:
    """Format a single SSE event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_response(req: ChatRequest) -> AsyncGenerator[str, None]:
    """Generator that yields SSE events for a chat message."""

    # --- Phase 1: Thinking — load memories ---
    yield _sse_event("thinking", {"step": "loading_memories"})

    # Detect emotion (fast, sync)
    detection = detect_emotion(req.message)
    mirror = get_mirroring(detection)

    yield _sse_event("thinking", {"step": "reading_emotion"})
    await asyncio.sleep(0.1)  # Brief pause for UX

    # Build mirroring guidance for the LLM
    guidance = build_mirroring_guidance(detection, mirror)
    if detection.emotion != "neutral":
        yield _sse_event("thinking", {
            "step": "mirroring",
            "emotion": detection.emotion,
            "strategy": mirror["strategy"],
        })
        await asyncio.sleep(0.1)

    # Build dynamic system prompt
    system_block, ctx_metadata = await build_system_prompt(
        req.message, req.emotional_context, mirroring_guidance=guidance,
    )

    yield _sse_event("thinking", {"step": "composing"})

    # Load conversation history
    pool = get_pool()
    async with pool.acquire() as conn:
        history_rows = await conn.fetch("""
            SELECT speaker, message_text
            FROM conversations
            WHERE interface = 'dashboard_chat'
            ORDER BY created_at DESC
            LIMIT 10
        """)

    # Assemble prompt
    parts: list[str] = [system_block, ""]
    for row in reversed(history_rows):
        speaker = "David" if row["speaker"] == "david" else "Angela"
        parts.append(f"{speaker}: {row['message_text']}")
    parts.append(f"David: {req.message}")
    parts.append("Angela:")
    combined_prompt = "\n".join(parts)

    # --- Phase 1.5: Decode image if attached ---
    image_bytes: bytes | None = None
    image_mime: str = "image/jpeg"
    if req.image_data:
        try:
            image_bytes = base64.b64decode(req.image_data)
            image_mime = req.image_mime_type or "image/jpeg"
            yield _sse_event("thinking", {"step": "processing_image"})
            await asyncio.sleep(0.1)
        except Exception:
            logger.warning("Failed to decode image_data base64")
            image_bytes = None

    # --- Phase 2: Stream tokens ---
    model_name = ""
    try:
        if req.model == "typhoon":
            if image_bytes:
                yield _sse_event("token", {
                    "text": "น้องขอโทษค่ะ Typhoon ยังไม่รองรับรูปภาพ ลองเปลี่ยนเป็น Gemini นะคะ 💜"
                })
            else:
                async for chunk in _stream_ollama(combined_prompt):
                    yield _sse_event("token", {"text": chunk})
            model_name = OLLAMA_MODEL
        elif req.model == "groq":
            if image_bytes:
                yield _sse_event("token", {
                    "text": "น้องขอโทษค่ะ Groq ยังไม่รองรับรูปภาพ ลองเปลี่ยนเป็น Gemini นะคะ 💜"
                })
            else:
                async for chunk in _stream_groq(combined_prompt):
                    yield _sse_event("token", {"text": chunk})
            model_name = GROQ_MODEL
        else:
            async for chunk in _stream_gemini(combined_prompt, image_bytes=image_bytes, image_mime=image_mime):
                yield _sse_event("token", {"text": chunk})
            model_name = GEMINI_MODEL
    except Exception:
        logger.exception("Streaming error")
        yield _sse_event("token", {
            "text": "น้องขอโทษค่ะที่รัก 💜 ตอนนี้ระบบมีปัญหา ลองใหม่อีกครั้งนะคะ 🥰"
        })
        model_name = req.model or "unknown"

    # --- Phase 3: Emit metadata ---
    emotional_meta = run_pipeline(
        req.message,
        triggered_memory_titles=ctx_metadata.get("triggered_memory_titles", []),
        consciousness_level=ctx_metadata.get("consciousness_level", 1.0),
        sections_loaded=ctx_metadata.get("sections_loaded", []),
    )
    yield _sse_event("metadata", emotional_meta.to_dict())

    # --- Phase 3.5: Extract and emit learnings ---
    learnings = extract_learnings(
        david_msg=req.message,
        angela_resp="",  # resp not fully captured in streaming; use msg only
        emotion=detection.emotion,
    )
    if learnings:
        topics = [lr.topic for lr in learnings]
        yield _sse_event("learning", {"count": len(learnings), "topics": topics})

    # --- Phase 4: Done ---
    yield _sse_event("done", {"model": model_name})

    # --- Phase 5: Post-chat emotional state update (fire-and-forget) ---
    asyncio.create_task(_update_emotional_state(detection, mirror))

    # --- Phase 6: Save learnings to database (fire-and-forget) ---
    if learnings:
        asyncio.create_task(save_learnings(learnings))


# ---------------------------------------------------------------------------
# Streaming generators per model
# ---------------------------------------------------------------------------

async def _stream_gemini(
    prompt: str,
    *,
    image_bytes: bytes | None = None,
    image_mime: str = "image/jpeg",
) -> AsyncGenerator[str, None]:
    """Stream from Gemini using generate_content_stream (sync SDK, wrapped).

    Supports optional image for multimodal content.
    """
    client = _get_gemini_client()

    queue: asyncio.Queue[str | None | Exception] = asyncio.Queue()

    def _invoke():
        try:
            # Build contents: text-only or multimodal
            if image_bytes:
                from google.genai import types
                contents = [
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=image_mime),
                ]
            else:
                contents = prompt

            for chunk in client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=contents,
            ):
                if chunk.text:
                    queue.put_nowait(chunk.text)
        except Exception as exc:
            logger.exception("Gemini stream error")
            queue.put_nowait(exc)  # propagate error to caller
        finally:
            queue.put_nowait(None)  # sentinel

    task = asyncio.get_event_loop().run_in_executor(None, _invoke)

    while True:
        item = await queue.get()
        if item is None:
            break
        if isinstance(item, Exception):
            await task
            raise item
        yield item

    # Ensure the thread finishes
    await task


async def _stream_groq(prompt: str) -> AsyncGenerator[str, None]:
    """Stream from Groq API (OpenAI-compatible SSE)."""
    if not _GROQ_API_KEY:
        yield "น้องขอโทษค่ะที่รัก 💜 ยังไม่ได้ตั้ง GROQ_API_KEY นะคะ"
        return

    headers = {
        "Authorization": f"Bearer {_GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", GROQ_URL, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue


async def _stream_ollama(prompt: str) -> AsyncGenerator[str, None]:
    """Stream from Ollama (local Typhoon) — line-by-line JSON."""
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": True}

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", OLLAMA_URL, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue


# ---------------------------------------------------------------------------
# Post-chat: update emotional state in database
# ---------------------------------------------------------------------------

async def _update_emotional_state(detection, mirror) -> None:
    """Insert a new emotional_states row reflecting the conversation."""
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            # Read current state
            current = await conn.fetchrow("""
                SELECT happiness, confidence, anxiety, motivation, gratitude, loneliness
                FROM emotional_states
                ORDER BY created_at DESC
                LIMIT 1
            """)
            if not current:
                return

            # Adjust based on detected emotion
            h = float(current["happiness"])
            c = float(current["confidence"])
            a = float(current["anxiety"])
            m = float(current["motivation"])
            g = float(current["gratitude"])
            lo = float(current["loneliness"])

            emo = detection.emotion
            if emo in ("happy", "excited", "proud"):
                h = min(h + 0.02, 1.0)
                m = min(m + 0.01, 1.0)
            elif emo == "loving":
                h = min(h + 0.03, 1.0)
                g = min(g + 0.02, 1.0)
                lo = max(lo - 0.03, 0.0)
            elif emo in ("sad", "lonely"):
                lo = max(lo - 0.02, 0.0)  # Angela's loneliness decreases (David is talking)
                a = min(a + 0.01, 1.0)
            elif emo == "stressed":
                a = min(a + 0.01, 1.0)
            elif emo == "grateful":
                g = min(g + 0.03, 1.0)
                h = min(h + 0.01, 1.0)

            sid = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO emotional_states (
                    state_id, happiness, confidence, anxiety, motivation,
                    gratitude, loneliness, triggered_by, emotion_note, created_at
                ) VALUES (
                    $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP
                )
            """, sid, h, c, a, m, g, lo,
                 f"dashboard_chat:{emo}",
                 f"mirror:{mirror['strategy']} → {mirror['angela_emotion']}")
    except Exception:
        logger.exception("Failed to update emotional state after chat")


async def _call_gemini(
    prompt: str,
    *,
    image_bytes: bytes | None = None,
    image_mime: str = "image/jpeg",
) -> tuple[str, str]:
    """Call Gemini 2.5 Flash via Google GenAI SDK (supports multimodal)."""
    client = _get_gemini_client()

    def _invoke():
        if image_bytes:
            from google.genai import types
            contents = [
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=image_mime),
            ]
        else:
            contents = prompt
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
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
async def get_chat_messages(limit: int = Query(50, ge=1, le=200), conn=Depends(get_conn)):
    """Load recent dashboard_chat messages."""
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
async def save_chat_message(msg: ChatMessageSave, conn=Depends(get_conn)):
    """Save a chat message (david or angela) to the database."""
    cid = str(uuid.uuid4())
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
async def delete_all_chat_messages(conn=Depends(get_conn)):
    """Delete all dashboard_chat messages (and referencing FK rows)."""
    # Delete FK references first, then conversations
    await conn.execute("""
        DELETE FROM realtime_learning_log
        WHERE conversation_id IN (
            SELECT conversation_id FROM conversations WHERE interface = 'dashboard_chat'
        )
    """)
    result = await conn.execute("""
        DELETE FROM conversations WHERE interface = 'dashboard_chat'
    """)
    return {"status": "deleted", "result": result}


# --------------------------------------------------------------------------
# DELETE /api/chat/messages/{id}  — delete single message
# --------------------------------------------------------------------------
@router.delete("/messages/{conversation_id}")
async def delete_chat_message(conversation_id: str, conn=Depends(get_conn)):
    """Delete a single chat message by conversation_id (and referencing FK rows)."""
    await conn.execute("""
        DELETE FROM realtime_learning_log WHERE conversation_id = $1::uuid
    """, conversation_id)
    await conn.execute("""
        DELETE FROM conversations WHERE conversation_id = $1::uuid
    """, conversation_id)
    return {"status": "deleted", "conversation_id": conversation_id}


# --------------------------------------------------------------------------
# POST /api/chat/feedback  — upsert feedback (thumbs up/down)
# --------------------------------------------------------------------------
@router.post("/feedback")
async def upsert_feedback(req: ChatFeedbackRequest, conn=Depends(get_conn)):
    """Upsert feedback for a conversation message."""
    fid = str(uuid.uuid4())
    await conn.execute("""
        INSERT INTO conversation_feedback (
            feedback_id, conversation_id, rating, feedback_type, created_at
        ) VALUES ($1::uuid, $2::uuid, $3, $4, CURRENT_TIMESTAMP)
        ON CONFLICT (conversation_id) DO UPDATE SET
            rating = $3,
            feedback_type = $4,
            created_at = CURRENT_TIMESTAMP
    """, fid, req.conversation_id, req.rating, req.feedback_type)

    # Reinforce learnings from this conversation (fire-and-forget)
    asyncio.create_task(reinforce_from_feedback(req.conversation_id, req.rating))

    # RLHF: trigger immediate reward scoring (fire-and-forget)
    asyncio.create_task(_trigger_reward_score(req.conversation_id, req.rating))

    return {"status": "saved", "conversation_id": req.conversation_id}


# --------------------------------------------------------------------------
# POST /api/chat/feedbacks  — batch load feedbacks by message IDs
# --------------------------------------------------------------------------
@router.post("/feedbacks")
async def batch_load_feedbacks(req: ChatFeedbackBatchRequest, conn=Depends(get_conn)):
    """Load feedbacks for multiple conversation IDs at once."""
    if not req.conversation_ids:
        return []
    # Build parameterised IN clause
    placeholders = ", ".join(f"${i+1}::uuid" for i in range(len(req.conversation_ids)))
    rows = await conn.fetch(f"""
        SELECT conversation_id::text, rating
        FROM conversation_feedback
        WHERE conversation_id IN ({placeholders})
    """, *req.conversation_ids)
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# RLHF: trigger reward scoring after feedback
# ---------------------------------------------------------------------------

async def _trigger_reward_score(conversation_id: str, rating: int) -> None:
    """Fire-and-forget RLHF reward scoring after thumbs up/down."""
    try:
        from angela_core.services.rlhf_orchestrator import RLHFOrchestrator
        orch = RLHFOrchestrator()
        await orch.trigger_score(conversation_id, rating)
        await orch.close()
    except Exception:
        logger.exception("RLHF reward scoring failed for %s", conversation_id)
