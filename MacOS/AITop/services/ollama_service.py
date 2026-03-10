"""
Ollama Service — wrapper for Ollama REST API (localhost:11434).
Handles model listing, pulling, deleting, chatting, and status checks.
"""

import httpx
from typing import Optional, AsyncIterator

OLLAMA_BASE = "http://localhost:11434"
TIMEOUT = httpx.Timeout(30.0, read=120.0)


async def check_status() -> dict:
    """Check if Ollama is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                return {
                    "running": True,
                    "model_count": len(models),
                }
    except Exception:
        pass
    return {"running": False, "model_count": 0}


async def list_models() -> list[dict]:
    """List all local Ollama models."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{OLLAMA_BASE}/api/tags")
        resp.raise_for_status()
        data = resp.json()
        models = []
        for m in data.get("models", []):
            models.append({
                "name": m.get("name", ""),
                "model": m.get("model", ""),
                "size_bytes": m.get("size", 0),
                "size_gb": round(m.get("size", 0) / (1024**3), 2),
                "modified_at": m.get("modified_at", ""),
                "digest": m.get("digest", "")[:12],
                "family": m.get("details", {}).get("family", ""),
                "parameter_size": m.get("details", {}).get("parameter_size", ""),
                "quantization": m.get("details", {}).get("quantization_level", ""),
            })
        return models


async def pull_model(model_name: str) -> AsyncIterator[dict]:
    """Pull a model from Ollama registry. Yields progress dicts."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE}/api/pull",
            json={"name": model_name},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.strip():
                    import json
                    yield json.loads(line)


async def delete_model(model_name: str) -> bool:
    """Delete a local Ollama model."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.delete(
            f"{OLLAMA_BASE}/api/delete",
            json={"name": model_name}
        )
        return resp.status_code == 200


async def chat(
    model: str,
    messages: list[dict],
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    """Send chat completion (non-streaming)."""
    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + messages

    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as client:
        resp = await client.post(f"{OLLAMA_BASE}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {
            "content": data.get("message", {}).get("content", ""),
            "model": data.get("model", model),
            "total_duration_ms": round(data.get("total_duration", 0) / 1e6, 1),
            "eval_count": data.get("eval_count", 0),
            "eval_duration_ms": round(data.get("eval_duration", 0) / 1e6, 1),
            "tokens_per_second": round(
                data.get("eval_count", 0) / max(data.get("eval_duration", 1) / 1e9, 0.001), 1
            ),
        }


async def chat_stream(
    model: str,
    messages: list[dict],
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AsyncIterator[str]:
    """Stream chat completion tokens."""
    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + messages

    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as client:
        async with client.stream("POST", f"{OLLAMA_BASE}/api/chat", json=payload) as resp:
            resp.raise_for_status()
            import json
            async for line in resp.aiter_lines():
                if line.strip():
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token


async def show_model(model_name: str) -> dict:
    """Get model details."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{OLLAMA_BASE}/api/show",
            json={"name": model_name}
        )
        resp.raise_for_status()
        return resp.json()


async def list_running() -> list[dict]:
    """List currently loaded/running models."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/ps")
            resp.raise_for_status()
            return resp.json().get("models", [])
    except Exception:
        return []
