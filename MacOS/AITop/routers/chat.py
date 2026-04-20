"""Chat router — Ollama chat with consciousness RAG (vector search pre-chat + async learning post-chat)."""

import asyncio
import logging
import traceback
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from angela_core.services.thaillm_service import THAILLM_MODELS, ThaiLLMService
from services.ollama_service import chat, chat_stream
from services.consciousness_rag import search_memory, format_context_for_prompt

THAILLM_PREFIX = "thaillm:"
_thaillm_service = ThaiLLMService()

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

# Clean fallback — AITop Chat is for model evaluation, not Angela persona usage.
# If the Swift client doesn't send a system prompt, use plain Thai language rules only.
DEFAULT_TEST_SYSTEM_PROMPT = (
    "กฎสำคัญ: ตอบเป็นภาษาไทยเท่านั้น ห้ามแปลเป็นภาษาอังกฤษ ห้ามตอบ 2 ภาษา\n"
    "ตอบกระชับ ตรงประเด็น คิดเป็นขั้นตอน"
)


class ChatRequest(BaseModel):
    model: str
    messages: list[dict]
    system: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    rag_enabled: bool = False  # Default OFF — this Chat UI is for model testing, not Angela conversations


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Chat with consciousness: RAG pre-chat → Gemma 3 12B → async learning post-chat."""
    try:
        system_prompt = req.system or DEFAULT_TEST_SYSTEM_PROMPT

        # ① PRE-CHAT: Vector search for relevant context
        rag_context = ""
        if req.rag_enabled and req.messages:
            last_user_msg = next(
                (m["content"] for m in reversed(req.messages) if m.get("role") == "user"),
                None,
            )
            if last_user_msg:
                try:
                    results = await search_memory(last_user_msg, top_k=5, min_score=0.3)
                    rag_context = format_context_for_prompt(results, max_chars=2000)
                    if rag_context:
                        logger.info(f"RAG injected {len(results)} memories into context")
                except Exception as e:
                    logger.warning(f"RAG search failed (non-blocking): {e}")

        # Inject RAG context into system prompt
        enriched_system = system_prompt
        if rag_context:
            enriched_system = f"{system_prompt}\n\n{rag_context}"

        # ② CHAT: Route to ThaiLLM (remote) or Ollama (local)
        is_thaillm = req.model.startswith(THAILLM_PREFIX)

        if is_thaillm:
            model_key = req.model[len(THAILLM_PREFIX):]
            if model_key not in THAILLM_MODELS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown ThaiLLM model '{model_key}'. "
                           f"Valid: {list(THAILLM_MODELS.keys())}",
                )
            # ThaiLLM only supports single-user prompt per call; collapse history into last user msg.
            last_user = next(
                (m["content"] for m in reversed(req.messages) if m.get("role") == "user"),
                "",
            )
            tl_result = await _thaillm_service.chat(
                prompt=last_user,
                model_key=model_key,
                system=enriched_system,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )
            eval_ms = tl_result.latency_ms
            tps = (tl_result.completion_tokens / (eval_ms / 1000.0)) if eval_ms > 0 else 0.0
            result = {
                "content": tl_result.content,
                "model": req.model,
                "total_duration_ms": round(eval_ms, 1),
                "eval_count": tl_result.completion_tokens,
                "eval_duration_ms": round(eval_ms, 1),
                "tokens_per_second": round(tps, 1),
            }
        elif req.stream:
            async def stream():
                try:
                    async for token in chat_stream(
                        model=req.model,
                        messages=req.messages,
                        system=enriched_system,
                        temperature=req.temperature,
                        max_tokens=req.max_tokens,
                    ):
                        yield f"data: {token}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: {{\"error\": \"{e}\"}}\n\n"

            return StreamingResponse(stream(), media_type="text/event-stream")
        else:
            result = await chat(
                model=req.model,
                messages=req.messages,
                system=enriched_system,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )

        # ③ POST-CHAT: Async learning (non-blocking)
        if req.messages:
            last_user = next(
                (m["content"] for m in reversed(req.messages) if m.get("role") == "user"),
                "",
            )
            asyncio.create_task(_async_learn(last_user, result.get("content", "")))

        # Add RAG metadata to response
        result["rag_context_used"] = bool(rag_context)

        return result

    except Exception as e:
        logger.error(f"Chat error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


async def _async_learn(user_msg: str, assistant_resp: str):
    """Queue conversation for background learning (fire-and-forget)."""
    try:
        from services.consciousness_rag import search_memory  # noqa: already imported
        # Log for now — full learning worker integration comes next
        logger.info(f"📚 Learning queued: user={user_msg[:50]}... → resp={assistant_resp[:50]}...")
    except Exception as e:
        logger.warning(f"Async learning failed (non-critical): {e}")
