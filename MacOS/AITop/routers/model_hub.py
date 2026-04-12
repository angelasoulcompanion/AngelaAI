"""Model Hub router — HuggingFace integration, local models, Ollama deployment."""

import logging
import traceback
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.model_hub_service import (
    search_huggingface, get_model_info, download_model,
    import_to_ollama, push_to_huggingface,
    list_local_models, get_popular_models,
)

router = APIRouter(tags=["model_hub"])
logger = logging.getLogger(__name__)


class DownloadRequest(BaseModel):
    hf_model_id: str
    name: Optional[str] = None


class ImportOllamaRequest(BaseModel):
    adapter_path: str
    base_model: str
    ollama_name: str


class PushHFRequest(BaseModel):
    model_path: str
    repo_name: str
    private: bool = True


@router.get("/models/hub/search")
async def search_models(
    query: str = Query(..., min_length=1),
    task: str = Query(default="text-generation"),
    limit: int = Query(default=20, le=50),
):
    """Search HuggingFace Hub for models."""
    results = await search_huggingface(query, limit, task)
    return {"models": results, "count": len(results)}


@router.get("/models/hub/popular")
async def popular_models():
    """Get curated list of popular fine-tuning models."""
    return {"models": get_popular_models()}


@router.get("/models/hub/info/{model_id:path}")
async def model_info(model_id: str):
    """Get detailed info about a HuggingFace model."""
    info = await get_model_info(model_id)
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    return info


@router.post("/models/hub/download")
async def download_hub_model(req: DownloadRequest):
    """Download a model from HuggingFace."""
    result = await download_model(req.hf_model_id, req.name)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/models/hub/import-ollama")
async def import_ollama(req: ImportOllamaRequest):
    """Deploy fine-tuned model to Ollama."""
    result = await import_to_ollama(req.adapter_path, req.base_model, req.ollama_name)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/models/hub/push")
async def push_to_hf(req: PushHFRequest):
    """Push a model to HuggingFace Hub."""
    result = await push_to_huggingface(req.model_path, req.repo_name, req.private)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/models/local")
async def local_models():
    """List all locally tracked models."""
    try:
        models = await list_local_models()
        return {"models": models, "count": len(models)}
    except Exception as e:
        logger.error(f"List local models error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
