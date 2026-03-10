"""Fine-Tune router — MLX LoRA training jobs."""

import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services.finetune_service import (
    create_job, start_job, cancel_job, get_job, list_jobs, get_strategies, WORKSPACE
)

router = APIRouter(tags=["finetune"])

DATASETS_DIR = WORKSPACE / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)


class CreateJobRequest(BaseModel):
    model: str
    dataset_path: str
    strategy: str = "standard"
    epochs: Optional[int] = None
    learning_rate: Optional[float] = None
    lora_rank: Optional[int] = None
    batch_size: Optional[int] = None


@router.get("/finetune/strategies")
async def get_strategy_presets():
    """Get available fine-tuning strategies with presets."""
    return {"strategies": get_strategies()}


@router.get("/finetune/jobs")
async def get_jobs():
    """List all fine-tuning jobs."""
    jobs = list_jobs()
    return {"jobs": jobs, "count": len(jobs)}


@router.get("/finetune/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.post("/finetune/jobs")
async def create_finetune_job(req: CreateJobRequest):
    """Create a new fine-tuning job."""
    job = create_job(
        model=req.model,
        dataset_path=req.dataset_path,
        strategy=req.strategy,
        epochs=req.epochs,
        learning_rate=req.learning_rate,
        lora_rank=req.lora_rank,
        batch_size=req.batch_size,
    )
    return job.to_dict()


@router.post("/finetune/jobs/{job_id}/start")
async def start_finetune_job(job_id: str):
    """Start a pending fine-tuning job."""
    try:
        job = await start_job(job_id)
        return job.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/finetune/jobs/{job_id}/cancel")
async def cancel_finetune_job(job_id: str):
    """Cancel a running fine-tuning job."""
    success = cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or not running")
    return {"cancelled": job_id}


@router.post("/finetune/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a dataset file (JSONL format)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")

    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in (".jsonl", ".json", ".txt", ".csv"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    dest = DATASETS_DIR / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    # Count lines for JSONL
    line_count = 0
    if ext == ".jsonl":
        line_count = content.decode("utf-8", errors="ignore").count("\n")

    return {
        "filename": file.filename,
        "path": str(dest),
        "size_bytes": len(content),
        "lines": line_count,
    }


@router.get("/finetune/datasets")
async def list_datasets():
    """List available datasets."""
    datasets = []
    for f in DATASETS_DIR.iterdir():
        if f.is_file():
            datasets.append({
                "filename": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
            })
    return {"datasets": datasets}
