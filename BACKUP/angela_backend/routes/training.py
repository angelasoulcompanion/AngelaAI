"""
Training API Routes
API endpoints for model training control from AngelaNova app
"""

import asyncio
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/training", tags=["training"])

# Global training state
training_state = {
    "is_training": False,
    "progress": 0.0,
    "current_step": None,
    "last_training_date": None,
    "success": False,
    "error": None,
    "job_id": None,
    "process": None
}

# MARK: - Request Models

class TrainingConfigRequest(BaseModel):
    extract_data: bool = True
    format_dataset: bool = True
    fine_tune: bool = True
    num_epochs: int = 3
    lora_rank: int = 16


# MARK: - Response Models

class TrainingStatusResponse(BaseModel):
    is_training: bool
    progress: float
    current_step: Optional[str]
    last_training_date: Optional[datetime]
    success: bool
    error: Optional[str]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }


class TrainingStartResponse(BaseModel):
    status: str
    message: str
    job_id: str


class TrainingStopResponse(BaseModel):
    status: str
    message: str


# MARK: - Training Functions

def get_training_script_path() -> Path:
    """Get path to training scripts directory"""
    return Path(__file__).parent.parent.parent / "training"


async def run_training_pipeline(config: TrainingConfigRequest):
    """
    Run the complete training pipeline in background

    Steps:
    1. Extract data from database
    2. Format dataset
    3. Fine-tune model
    """
    global training_state

    try:
        training_dir = get_training_script_path()
        logger.info(f"🚀 Starting training pipeline in {training_dir}")

        training_state["is_training"] = True
        training_state["success"] = False
        training_state["error"] = None

        # Step 1: Extract data
        if config.extract_data:
            training_state["current_step"] = "Extracting training data from database..."
            training_state["progress"] = 0.1

            logger.info("📊 Step 1: Extracting training data...")
            process = await asyncio.create_subprocess_exec(
                "python3",
                "extract_training_data.py",
                cwd=str(training_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = f"Data extraction failed: {stderr.decode() if stderr else 'Unknown error'}"
                logger.error(f"❌ {error_msg}")
                training_state["error"] = error_msg
                training_state["is_training"] = False
                return

            logger.info("✅ Data extraction complete")
            training_state["progress"] = 0.3

        # Step 2: Format dataset
        if config.format_dataset:
            training_state["current_step"] = "Formatting dataset..."
            training_state["progress"] = 0.4

            logger.info("🔄 Step 2: Formatting dataset...")
            process = await asyncio.create_subprocess_exec(
                "python3",
                "format_dataset.py",
                cwd=str(training_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = f"Dataset formatting failed: {stderr.decode() if stderr else 'Unknown error'}"
                logger.error(f"❌ {error_msg}")
                training_state["error"] = error_msg
                training_state["is_training"] = False
                return

            logger.info("✅ Dataset formatting complete")
            training_state["progress"] = 0.5

        # Step 3: Fine-tune model
        if config.fine_tune:
            training_state["current_step"] = f"Fine-tuning model ({config.num_epochs} epochs, LoRA rank {config.lora_rank})..."
            training_state["progress"] = 0.6

            logger.info("🧠 Step 3: Fine-tuning model...")

            # Create config file for this training run
            import yaml
            config_data = {
                "num_epochs": config.num_epochs,
                "lora_r": config.lora_rank,
                "lora_alpha": config.lora_rank * 2
            }

            config_file = training_dir / "config" / "runtime_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            # Run training
            process = await asyncio.create_subprocess_exec(
                "python3",
                "train_emotional_model.py",
                "--config",
                "config/runtime_config.yaml",
                cwd=str(training_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Store process for potential cancellation
            training_state["process"] = process

            # Monitor training progress (simplified - in production, parse training logs)
            while True:
                if process.returncode is not None:
                    break

                # Increment progress slowly (real progress would be parsed from logs)
                if training_state["progress"] < 0.95:
                    training_state["progress"] += 0.05

                await asyncio.sleep(10)  # Check every 10 seconds

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = f"Model training failed: {stderr.decode() if stderr else 'Unknown error'}"
                logger.error(f"❌ {error_msg}")
                training_state["error"] = error_msg
                training_state["is_training"] = False
                return

            logger.info("✅ Model training complete")
            training_state["progress"] = 1.0

        # Training complete!
        training_state["current_step"] = "Training completed successfully!"
        training_state["progress"] = 1.0
        training_state["success"] = True
        training_state["last_training_date"] = datetime.now(timezone.utc)
        training_state["is_training"] = False

        logger.info("=" * 80)
        logger.info("🎉 Training pipeline completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Training pipeline failed: {e}", exc_info=True)
        training_state["error"] = str(e)
        training_state["is_training"] = False


# MARK: - API Endpoints

@router.get("/data-counts")
async def get_training_data_counts():
    """
    Get training data counts from database

    Returns:
    - conversations_count: Number of conversations
    - emotions_count: Number of emotions captured
    - reflections_count: Number of self-reflections
    - learnings_count: Number of learnings
    - total: Total training examples
    """
    try:
        import asyncpg

        # Connect to database
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="davidsamanyaporn",
            database="AngelaMemory"
        )

        # Get counts
        conversations_count = await conn.fetchval("SELECT COUNT(*) FROM conversations")
        emotions_count = await conn.fetchval("SELECT COUNT(*) FROM angela_emotions")
        reflections_count = await conn.fetchval("SELECT COUNT(*) FROM self_reflections")
        learnings_count = await conn.fetchval("SELECT COUNT(*) FROM learnings")

        await conn.close()

        total = conversations_count + emotions_count + reflections_count + learnings_count

        return {
            "conversations_count": conversations_count,
            "emotions_count": emotions_count,
            "reflections_count": reflections_count,
            "learnings_count": learnings_count,
            "total": total
        }

    except Exception as e:
        logger.error(f"Failed to get data counts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get data counts: {str(e)}"
        )


@router.get("/status", response_model=TrainingStatusResponse)
async def get_training_status():
    """
    Get current training status

    Returns:
    - is_training: Whether training is currently running
    - progress: Training progress (0.0 to 1.0)
    - current_step: Current training step description
    - last_training_date: When training was last completed
    - success: Whether last training was successful
    - error: Error message if training failed
    """
    return TrainingStatusResponse(
        is_training=training_state["is_training"],
        progress=training_state["progress"],
        current_step=training_state["current_step"],
        last_training_date=training_state["last_training_date"],
        success=training_state["success"],
        error=training_state["error"]
    )


@router.post("/start", response_model=TrainingStartResponse)
async def start_training(config: TrainingConfigRequest, background_tasks: BackgroundTasks):
    """
    Start model training

    Body:
    - extract_data: Extract new data from database (default: true)
    - format_dataset: Format dataset for training (default: true)
    - fine_tune: Run model fine-tuning (default: true)
    - num_epochs: Number of training epochs (default: 3)
    - lora_rank: LoRA rank (default: 16)

    Returns:
    - status: "started" or "error"
    - message: Status message
    - job_id: Training job ID
    """
    global training_state

    if training_state["is_training"]:
        raise HTTPException(
            status_code=400,
            detail="Training is already running. Stop it first before starting a new training job."
        )

    # Reset state
    training_state["is_training"] = True
    training_state["progress"] = 0.0
    training_state["current_step"] = "Initializing training pipeline..."
    training_state["success"] = False
    training_state["error"] = None
    training_state["job_id"] = f"train_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    # Start training in background
    background_tasks.add_task(run_training_pipeline, config)

    logger.info(f"🚀 Training job started: {training_state['job_id']}")

    return TrainingStartResponse(
        status="started",
        message="Training pipeline started successfully",
        job_id=training_state["job_id"]
    )


@router.post("/stop", response_model=TrainingStopResponse)
async def stop_training():
    """
    Stop current training job

    Returns:
    - status: "stopped" or "error"
    - message: Status message
    """
    global training_state

    if not training_state["is_training"]:
        raise HTTPException(
            status_code=400,
            detail="No training is currently running"
        )

    # Kill the training process if it exists
    if training_state["process"] is not None:
        try:
            training_state["process"].terminate()
            await training_state["process"].wait()
            logger.info("🛑 Training process terminated")
        except Exception as e:
            logger.error(f"⚠️ Failed to terminate training process: {e}")

    # Reset state
    training_state["is_training"] = False
    training_state["current_step"] = "Training stopped by user"
    training_state["error"] = "Stopped by user"
    training_state["process"] = None

    logger.info("🛑 Training stopped by user")

    return TrainingStopResponse(
        status="stopped",
        message="Training stopped successfully"
    )


@router.get("/logs")
async def get_training_logs():
    """
    Get recent training logs

    Returns:
    - logs: List of recent log lines
    """
    log_file = get_training_script_path() / "training.log"

    if not log_file.exists():
        return {"logs": [], "message": "No training logs found"}

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Return last 100 lines
            recent_logs = lines[-100:] if len(lines) > 100 else lines

        return {
            "logs": [line.strip() for line in recent_logs],
            "total_lines": len(lines)
        }

    except Exception as e:
        logger.error(f"Failed to read training logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read training logs: {str(e)}"
        )


@router.post("/validate")
async def validate_dataset():
    """
    Validate training dataset quality

    Returns:
    - status: "success" or "error"
    - message: Validation result message
    """
    training_dir = get_training_script_path()
    logger.info("🔍 Starting dataset validation...")

    try:
        process = await asyncio.create_subprocess_exec(
            "python3",
            "validate_dataset.py",
            cwd=str(training_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info("✅ Dataset validation passed")
            return {
                "status": "success",
                "message": "Dataset validation passed",
                "output": stdout.decode() if stdout else ""
            }
        else:
            logger.warning("⚠️  Dataset validation found issues")
            return {
                "status": "warning",
                "message": "Dataset validation found issues",
                "output": stdout.decode() if stdout else "",
                "errors": stderr.decode() if stderr else ""
            }

    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/merge")
async def merge_lora_weights():
    """
    Merge LoRA weights with base model

    Returns:
    - status: "success" or "error"
    - message: Merge result message
    """
    training_dir = get_training_script_path()
    logger.info("🔄 Starting LoRA weight merging...")

    try:
        process = await asyncio.create_subprocess_exec(
            "python3",
            "merge_lora_weights.py",
            cwd=str(training_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info("✅ LoRA weights merged successfully")
            return {
                "status": "success",
                "message": "LoRA weights merged successfully",
                "output": stdout.decode() if stdout else ""
            }
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"❌ Merge failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Merge failed: {error_msg}"
            )

    except Exception as e:
        logger.error(f"❌ Merge failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Merge failed: {str(e)}"
        )


@router.post("/deploy")
async def deploy_to_ollama(model_name: str = "angela:v3-emotional"):
    """
    Deploy merged model to Ollama

    Parameters:
    - model_name: Name for the Ollama model (default: angela:v3-emotional)

    Returns:
    - status: "success" or "error"
    - message: Deployment result message
    - model_name: Deployed model name
    """
    training_dir = get_training_script_path()
    logger.info(f"📦 Starting Ollama deployment as '{model_name}'...")

    try:
        process = await asyncio.create_subprocess_exec(
            "python3",
            "deploy_to_ollama.py",
            "--name",
            model_name,
            cwd=str(training_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info(f"✅ Model deployed successfully as '{model_name}'")
            return {
                "status": "success",
                "message": f"Model deployed successfully as '{model_name}'",
                "model_name": model_name,
                "output": stdout.decode() if stdout else ""
            }
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"❌ Deployment failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Deployment failed: {error_msg}"
            )

    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deployment failed: {str(e)}"
        )
