"""Fine-Tune router — Multi-method training jobs + dataset management."""

import logging
import traceback
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel

from services.finetune_service import (
    create_job, start_job, cancel_job, get_job, list_jobs,
    get_strategies, get_training_methods, WORKSPACE
)

router = APIRouter(tags=["finetune"])
logger = logging.getLogger(__name__)

DATASETS_DIR = WORKSPACE / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Request Models
# ============================================================

class CreateJobRequest(BaseModel):
    model: str
    dataset_path: str
    training_method: str = "mlx_lora"
    engine: Optional[str] = None
    strategy: Optional[str] = None
    config: Optional[dict] = None
    # Legacy params (backwards compatible)
    epochs: Optional[int] = None
    learning_rate: Optional[float] = None
    lora_rank: Optional[int] = None
    batch_size: Optional[int] = None


class EstimateRequest(BaseModel):
    model: str
    dataset_path: str
    training_method: str = "mlx_lora"
    epochs: int = 3
    batch_size: int = 2
    grad_accumulation: int = 4
    max_seq_length: int = 1024


# ============================================================
# Training Methods & Strategies
# ============================================================

@router.get("/finetune/methods")
async def get_methods():
    """Get available training methods with engine info."""
    return {"methods": get_training_methods()}


@router.get("/finetune/strategies")
async def get_strategy_presets():
    """Get available fine-tuning strategies with presets."""
    return {"strategies": get_strategies()}


# ============================================================
# Estimation
# ============================================================

@router.post("/finetune/estimate")
async def estimate_training(req: EstimateRequest):
    """Estimate training duration and memory before starting."""
    try:
        from services.training_estimator import estimate_duration, estimate_memory
        dur = estimate_duration(
            model_name=req.model,
            num_samples=_count_lines(req.dataset_path),
            method=req.training_method,
            epochs=req.epochs,
            batch_size=req.batch_size,
            grad_accumulation=req.grad_accumulation,
            max_seq_length=req.max_seq_length,
        )
        mem = estimate_memory(
            model_name=req.model,
            method=req.training_method,
            batch_size=req.batch_size,
            max_seq_length=req.max_seq_length,
        )
        return {"duration": dur, "memory": mem}
    except Exception as e:
        logger.error(f"Estimate error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Jobs CRUD
# ============================================================

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
    try:
        job = create_job(
            model=req.model,
            dataset_path=req.dataset_path,
            training_method=req.training_method,
            engine=req.engine,
            strategy=req.strategy,
            config=req.config,
            epochs=req.epochs,
            learning_rate=req.learning_rate,
            lora_rank=req.lora_rank,
            batch_size=req.batch_size,
        )
        return job.to_dict()
    except Exception as e:
        logger.error(f"Create job error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finetune/jobs/{job_id}/start")
async def start_finetune_job(job_id: str):
    """Start a pending fine-tuning job."""
    try:
        job = await start_job(job_id)
        return job.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Start job error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finetune/jobs/{job_id}/cancel")
async def cancel_finetune_job(job_id: str):
    """Cancel a running fine-tuning job."""
    success = cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or not running")
    return {"cancelled": job_id}


# ============================================================
# Datasets
# ============================================================

@router.post("/finetune/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    dataset_type: str = "sft",
):
    """Upload a dataset file (JSONL, JSON, CSV, Parquet)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".jsonl", ".json", ".txt", ".csv", ".parquet"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    try:
        dest = DATASETS_DIR / file.filename
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)

        line_count = 0
        if ext == ".jsonl":
            line_count = content.decode("utf-8", errors="ignore").count("\n")
        elif ext == ".csv":
            line_count = max(0, content.decode("utf-8", errors="ignore").count("\n") - 1)

        # Save to Neon
        dataset_id = ""
        try:
            from services.db_service import save_dataset
            dataset_id = await save_dataset(
                file.filename, str(dest), len(content), line_count,
                ext.lstrip("."), name or file.filename, dataset_type
            )
        except Exception as e:
            logger.warning(f"Neon dataset save failed: {e}")

        return {
            "id": dataset_id,
            "filename": file.filename,
            "path": str(dest),
            "size_bytes": len(content),
            "lines": line_count,
            "dataset_type": dataset_type,
        }
    except Exception as e:
        logger.error(f"Upload dataset error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finetune/datasets")
async def list_datasets_endpoint():
    """List available datasets (uploaded only — exports are in batch history)."""
    try:
        datasets = []
        for f in DATASETS_DIR.iterdir():
            if f.is_file():
                lines = _count_lines(str(f))
                datasets.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                    "lines": lines,
                    "datasetType": "uploaded",
                })
        return {"datasets": datasets}
    except Exception as e:
        logger.error(f"List datasets error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finetune/datasets/export/preview")
async def preview_exported_file(path: str = Query(...), offset: int = Query(default=0), limit: int = Query(default=20, le=100)):
    """Preview an exported JSONL file with pagination."""
    import json as _json
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    try:
        rows = []
        total = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total += 1
                if i < offset:
                    continue
                if len(rows) >= limit:
                    continue  # still counting total
                line = line.strip()
                if line:
                    rows.append(_json.loads(line))
        return {"rows": rows, "total": total, "offset": offset, "limit": limit, "showing": len(rows)}
    except Exception as e:
        logger.error(f"Preview export error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finetune/datasets/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, limit: int = Query(default=10, le=50)):
    """Preview first N rows of a dataset."""
    try:
        from services.dataset_service import preview_dataset as _preview
        result = await _preview(dataset_id, limit)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Preview dataset error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finetune/datasets/{dataset_id}/validate")
async def validate_dataset(dataset_id: str):
    """Validate a dataset for training."""
    try:
        from services.dataset_service import validate_dataset as _validate
        result = await _validate(dataset_id)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Validate dataset error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finetune/datasets/{dataset_id}/stats")
async def get_dataset_stats(dataset_id: str):
    """Get detailed statistics for a dataset."""
    try:
        from services.dataset_service import get_statistics
        result = await get_statistics(dataset_id)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Dataset stats error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Dataset Export (Quality-Filtered from Neon DB)
# ============================================================

class ExportRequest(BaseModel):
    days: int = 730
    min_quality: float = 6.0
    min_importance: int = 1
    max_examples: int = 10000
    include_knowledge: bool = True
    include_core_memories: bool = True


@router.post("/finetune/datasets/export")
async def export_dataset(req: ExportRequest):
    """Export quality-filtered SFT dataset from Angela's conversation history."""
    try:
        from services.dataset_export_service import export_sft_dataset
        result = await export_sft_dataset(
            days=req.days,
            min_quality=req.min_quality,
            min_importance=req.min_importance,
            max_examples=req.max_examples,
            include_knowledge=req.include_knowledge,
            include_core_memories=req.include_core_memories,
        )
        return result
    except Exception as e:
        logger.error(f"Export dataset error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finetune/batches")
async def list_batches():
    """List all export batch history."""
    try:
        from services.db_service import list_export_batches
        batches = await list_export_batches()
        return {"batches": batches, "count": len(batches)}
    except Exception as e:
        logger.error(f"List batches error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Helpers
# ============================================================

def _count_lines(path: str) -> int:
    """Count lines in a file."""
    try:
        p = Path(path)
        if not p.exists():
            return 100
        with open(p) as f:
            return sum(1 for _ in f)
    except Exception:
        return 100
