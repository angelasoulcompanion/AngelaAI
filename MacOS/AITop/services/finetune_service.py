"""
Fine-Tune Service — MLX LoRA training orchestration.
Manages training jobs as background subprocess with progress tracking.
"""

import asyncio
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Strategy(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    HIGH_PRECISION = "high_precision"


# Strategy presets
STRATEGY_PRESETS = {
    Strategy.FAST: {
        "epochs": 1,
        "learning_rate": 5e-4,
        "lora_rank": 4,
        "batch_size": 4,
        "description": "Quick training, lower quality. ~30min for 7B model.",
    },
    Strategy.STANDARD: {
        "epochs": 3,
        "learning_rate": 2e-4,
        "lora_rank": 8,
        "batch_size": 2,
        "description": "Balanced quality and speed. ~2h for 7B model.",
    },
    Strategy.HIGH_PRECISION: {
        "epochs": 5,
        "learning_rate": 1e-4,
        "lora_rank": 16,
        "batch_size": 1,
        "description": "Best quality, slowest. ~5h for 7B model.",
    },
}


@dataclass
class TrainingJob:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    model: str = ""
    dataset_path: str = ""
    strategy: str = "standard"
    status: str = JobStatus.PENDING
    epochs: int = 3
    learning_rate: float = 2e-4
    lora_rank: int = 8
    batch_size: int = 2
    current_epoch: int = 0
    current_step: int = 0
    total_steps: int = 0
    loss: float = 0.0
    loss_history: list = field(default_factory=list)
    started_at: float = 0
    finished_at: float = 0
    output_dir: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.started_at > 0:
            elapsed = (self.finished_at or time.time()) - self.started_at
            d["elapsed_seconds"] = round(elapsed, 1)
            if self.total_steps > 0 and self.current_step > 0:
                eta = elapsed / self.current_step * (self.total_steps - self.current_step)
                d["eta_seconds"] = round(eta, 1)
        return d


# In-memory job store
_jobs: dict[str, TrainingJob] = {}
_processes: dict[str, subprocess.Popen] = {}

WORKSPACE = Path.home() / ".aitop" / "finetune"
WORKSPACE.mkdir(parents=True, exist_ok=True)


def get_strategies() -> list[dict]:
    """Return available fine-tuning strategies."""
    return [
        {"name": s.value, **STRATEGY_PRESETS[s]}
        for s in Strategy
    ]


def create_job(
    model: str,
    dataset_path: str,
    strategy: str = "standard",
    epochs: Optional[int] = None,
    learning_rate: Optional[float] = None,
    lora_rank: Optional[int] = None,
    batch_size: Optional[int] = None,
) -> TrainingJob:
    """Create a new fine-tuning job (does not start it)."""
    preset = STRATEGY_PRESETS.get(Strategy(strategy), STRATEGY_PRESETS[Strategy.STANDARD])

    job = TrainingJob(
        model=model,
        dataset_path=dataset_path,
        strategy=strategy,
        epochs=epochs or preset["epochs"],
        learning_rate=learning_rate or preset["learning_rate"],
        lora_rank=lora_rank or preset["lora_rank"],
        batch_size=batch_size or preset["batch_size"],
    )
    job.output_dir = str(WORKSPACE / job.id)
    os.makedirs(job.output_dir, exist_ok=True)
    _jobs[job.id] = job
    return job


async def start_job(job_id: str) -> TrainingJob:
    """Start a fine-tuning job as a subprocess using mlx_lm.lora."""
    job = _jobs.get(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    if job.status == JobStatus.RUNNING:
        raise ValueError(f"Job {job_id} is already running")

    job.status = JobStatus.RUNNING
    job.started_at = time.time()

    # Build mlx_lm.lora command
    cmd = [
        "python3", "-m", "mlx_lm.lora",
        "--model", job.model,
        "--data", job.dataset_path,
        "--train",
        "--iters", str(job.epochs * 100),  # approximate
        "--batch-size", str(job.batch_size),
        "--lora-layers", str(job.lora_rank),
        "--learning-rate", str(job.learning_rate),
        "--adapter-path", os.path.join(job.output_dir, "adapters"),
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        _processes[job_id] = proc

        # Monitor in background
        asyncio.get_event_loop().run_in_executor(None, _monitor_job, job_id)
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)

    return job


def _monitor_job(job_id: str):
    """Monitor training process output and update job progress."""
    job = _jobs.get(job_id)
    proc = _processes.get(job_id)
    if not job or not proc:
        return

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            # Parse mlx_lm output for loss values
            # Typical format: "Iter 10: Train loss 2.345, Learning Rate 0.0002"
            if "Train loss" in line or "train loss" in line.lower():
                try:
                    parts = line.split("Train loss")[-1].strip()
                    loss_val = float(parts.split(",")[0].strip())
                    job.loss = loss_val
                    job.loss_history.append({
                        "step": job.current_step,
                        "loss": loss_val,
                        "timestamp": time.time(),
                    })
                except (ValueError, IndexError):
                    pass

            if "Iter" in line or "iter" in line:
                try:
                    iter_part = line.split("Iter")[-1].strip()
                    iter_num = int(iter_part.split(":")[0].strip())
                    job.current_step = iter_num
                except (ValueError, IndexError):
                    pass

        proc.wait()
        if proc.returncode == 0:
            job.status = JobStatus.COMPLETED
        else:
            job.status = JobStatus.FAILED
            job.error = f"Process exited with code {proc.returncode}"
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
    finally:
        job.finished_at = time.time()


def cancel_job(job_id: str) -> bool:
    """Cancel a running job."""
    proc = _processes.get(job_id)
    job = _jobs.get(job_id)
    if proc and job:
        proc.terminate()
        job.status = JobStatus.CANCELLED
        job.finished_at = time.time()
        return True
    return False


def get_job(job_id: str) -> Optional[dict]:
    """Get job status."""
    job = _jobs.get(job_id)
    return job.to_dict() if job else None


def list_jobs() -> list[dict]:
    """List all jobs."""
    return [j.to_dict() for j in _jobs.values()]
