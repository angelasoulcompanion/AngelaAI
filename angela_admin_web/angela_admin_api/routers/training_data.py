"""
💜 Training Data Export API Router
Endpoints for preparing and exporting training data
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import subprocess
import os
import json
from datetime import datetime
from pathlib import Path

router = APIRouter(prefix="/api/training-data", tags=["training-data"])

# Path to FineTuninng_coursera folder
FINETUNING_DIR = Path("/Users/davidsamanyaporn/PycharmProjects/AngelaAI/FineTuninng_coursera")
SCRIPT_PATH = FINETUNING_DIR / "prepare_angela_training_data.py"


class PrepareTrainingDataRequest(BaseModel):
    """Request model for preparing training data"""
    min_importance: int = 7
    max_per_topic: int = 150
    test_split: float = 0.1
    min_length: int = 10
    time_window: int = 5


class PrepareTrainingDataResponse(BaseModel):
    """Response model for prepared training data"""
    success: bool
    message: str
    stats: dict
    files: dict


@router.post("/prepare", response_model=PrepareTrainingDataResponse)
async def prepare_training_data(request: PrepareTrainingDataRequest):
    """
    Prepare training data from AngelaMemory database

    This endpoint runs the data preparation script with specified parameters
    and returns statistics about the generated dataset.
    """
    try:
        # Build command
        cmd = [
            "python3",
            str(SCRIPT_PATH),
            "--min-importance", str(request.min_importance),
            "--max-per-topic", str(request.max_per_topic),
            "--test-split", str(request.test_split),
            "--min-length", str(request.min_length),
            "--time-window", str(request.time_window)
        ]

        # Run script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(FINETUNING_DIR),
            timeout=120  # 2 minutes timeout
        )

        if result.returncode != 0:
            raise Exception(f"Script failed: {result.stderr}")

        # Read statistics
        stats_file = FINETUNING_DIR / "data_statistics.json"
        if not stats_file.exists():
            raise Exception("Statistics file not generated")

        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)

        # Check if files exist
        train_file = FINETUNING_DIR / "angela_training_data.jsonl"
        test_file = FINETUNING_DIR / "angela_test_data.jsonl"
        quality_file = FINETUNING_DIR / "data_quality_report.txt"

        files = {
            "training": str(train_file) if train_file.exists() else None,
            "test": str(test_file) if test_file.exists() else None,
            "statistics": str(stats_file),
            "quality_report": str(quality_file) if quality_file.exists() else None
        }

        # Get file sizes
        file_sizes = {}
        for name, path in files.items():
            if path and os.path.exists(path):
                size_mb = os.path.getsize(path) / (1024 * 1024)
                file_sizes[name] = round(size_mb, 2)

        return {
            "success": True,
            "message": f"✅ Generated {stats['total_examples']} examples",
            "stats": {
                **stats,
                "file_sizes_mb": file_sizes
            },
            "files": files
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Data preparation timed out (>2 minutes)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare data: {str(e)}"
        )


@router.get("/download/{file_type}")
async def download_file(file_type: str):
    """
    Download a training data file

    file_type: 'training', 'test', 'statistics', or 'quality_report'
    """
    file_map = {
        "training": FINETUNING_DIR / "angela_training_data.jsonl",
        "test": FINETUNING_DIR / "angela_test_data.jsonl",
        "statistics": FINETUNING_DIR / "data_statistics.json",
        "quality_report": FINETUNING_DIR / "data_quality_report.txt"
    }

    if file_type not in file_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Must be one of: {list(file_map.keys())}"
        )

    file_path = file_map[file_type]

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_path.name}. Run preparation first."
        )

    # Determine media type
    media_types = {
        "training": "application/x-ndjson",
        "test": "application/x-ndjson",
        "statistics": "application/json",
        "quality_report": "text/plain"
    }

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type=media_types[file_type]
    )


@router.get("/status")
async def get_preparation_status():
    """
    Check if training data files exist and get their metadata
    """
    files = {
        "training": FINETUNING_DIR / "angela_training_data.jsonl",
        "test": FINETUNING_DIR / "angela_test_data.jsonl",
        "statistics": FINETUNING_DIR / "data_statistics.json",
        "quality_report": FINETUNING_DIR / "data_quality_report.txt"
    }

    status = {}

    for name, path in files.items():
        if path.exists():
            stat = os.stat(path)
            size_mb = stat.st_size / (1024 * 1024)
            modified = datetime.fromtimestamp(stat.st_mtime)

            status[name] = {
                "exists": True,
                "size_mb": round(size_mb, 2),
                "modified": modified.isoformat(),
                "path": str(path)
            }
        else:
            status[name] = {
                "exists": False,
                "size_mb": 0,
                "modified": None,
                "path": str(path)
            }

    # If statistics file exists, read it
    stats = None
    if files["statistics"].exists():
        try:
            with open(files["statistics"], 'r', encoding='utf-8') as f:
                stats = json.load(f)
        except:
            pass

    return {
        "files": status,
        "statistics": stats,
        "has_data": all(f["exists"] for f in [status["training"], status["test"]])
    }


@router.delete("/clear")
async def clear_training_data():
    """
    Delete all generated training data files
    """
    files = [
        FINETUNING_DIR / "angela_training_data.jsonl",
        FINETUNING_DIR / "angela_test_data.jsonl",
        FINETUNING_DIR / "data_statistics.json",
        FINETUNING_DIR / "data_quality_report.txt"
    ]

    deleted = []
    for file_path in files:
        if file_path.exists():
            file_path.unlink()
            deleted.append(file_path.name)

    return {
        "success": True,
        "message": f"Deleted {len(deleted)} files",
        "deleted": deleted
    }
