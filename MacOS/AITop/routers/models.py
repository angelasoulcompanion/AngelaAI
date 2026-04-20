"""Models router — Ollama model management + HuggingFace search."""

import logging
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from angela_core.services.thaillm_service import THAILLM_MODELS
from services.ollama_service import list_models, pull_model, delete_model, show_model

router = APIRouter(tags=["models"])
logger = logging.getLogger(__name__)


class PullRequest(BaseModel):
    name: str


class DeleteRequest(BaseModel):
    name: str


def _thaillm_as_model_entries() -> list[dict]:
    """Expose ThaiLLM variants in the same shape as OllamaModel so the Chat picker can list them."""
    entries = []
    for key, m in THAILLM_MODELS.items():
        display = f"thaillm:{key}"
        entries.append({
            "name": display,
            "model": display,
            "size_bytes": 0,
            "size_gb": 0.0,
            "modified_at": "",
            "digest": "",
            "family": m.provider,         # AIEAT / NECTEC / SCB 10X / KBTG
            "parameter_size": "8B",
            "quantization": "API",
        })
    return entries


@router.get("/models")
async def get_models():
    """List local Ollama models + remote ThaiLLM variants."""
    try:
        models = await list_models()
    except Exception as e:
        logger.warning(f"Ollama unavailable, returning ThaiLLM only: {e}")
        models = []

    models.extend(_thaillm_as_model_entries())
    return {"models": models, "count": len(models)}


@router.get("/models/{model_name:path}/details")
async def get_model_details(model_name: str):
    """Get details for a specific model."""
    try:
        details = await show_model(model_name)
        return details
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/models/pull")
async def pull_model_endpoint(req: PullRequest):
    """Pull a model from Ollama registry (streaming progress)."""
    async def stream():
        import json
        try:
            async for progress in pull_model(req.name):
                yield json.dumps(progress) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.delete("/models")
async def delete_model_endpoint(req: DeleteRequest):
    """Delete a local model."""
    try:
        success = await delete_model(req.name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Model {req.name} not found")
        return {"deleted": req.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete model error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/search/hf")
async def search_huggingface(query: str = "", task: str = "text-generation", limit: int = 20):
    """Search HuggingFace Hub for models."""
    import httpx
    try:
        params = {
            "search": query,
            "filter": task,
            "sort": "downloads",
            "direction": "-1",
            "limit": limit,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get("https://huggingface.co/api/models", params=params)
            resp.raise_for_status()
            models = resp.json()
            return {
                "models": [
                    {
                        "id": m.get("modelId", ""),
                        "author": m.get("modelId", "").split("/")[0] if "/" in m.get("modelId", "") else "",
                        "downloads": m.get("downloads", 0),
                        "likes": m.get("likes", 0),
                        "tags": m.get("tags", [])[:5],
                        "pipeline_tag": m.get("pipeline_tag", ""),
                        "last_modified": m.get("lastModified", ""),
                    }
                    for m in models
                ],
                "count": len(models),
            }
    except Exception as e:
        logger.error(f"HuggingFace search error: {traceback.format_exc()}")
        raise HTTPException(status_code=502, detail=f"HuggingFace API error: {e}")
