"""Models router — Ollama model management + HuggingFace search."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.ollama_service import list_models, pull_model, delete_model, show_model

router = APIRouter(tags=["models"])


class PullRequest(BaseModel):
    name: str


class DeleteRequest(BaseModel):
    name: str


@router.get("/models")
async def get_models():
    """List all local Ollama models."""
    models = await list_models()
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
        async for progress in pull_model(req.name):
            yield json.dumps(progress) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.delete("/models")
async def delete_model_endpoint(req: DeleteRequest):
    """Delete a local model."""
    success = await delete_model(req.name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Model {req.name} not found")
    return {"deleted": req.name}


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
        raise HTTPException(status_code=502, detail=f"HuggingFace API error: {e}")
