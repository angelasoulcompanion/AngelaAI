"""Chat router — Ollama chat completions."""

from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.ollama_service import chat, chat_stream

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    model: str
    messages: list[dict]
    system: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Chat with an Ollama model."""
    if req.stream:
        async def stream():
            async for token in chat_stream(
                model=req.model,
                messages=req.messages,
                system=req.system,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            ):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")

    result = await chat(
        model=req.model,
        messages=req.messages,
        system=req.system,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    return result
