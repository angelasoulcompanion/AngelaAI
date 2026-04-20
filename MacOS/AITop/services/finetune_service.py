"""
Fine-Tune Service — Multi-method training orchestration for AI TOP.

Supports 5 training methods:
  - MLX_LORA: MLX native LoRA (primary, Apple Silicon optimized)
  - MLX_QLORA: MLX native QLoRA (quantized, less memory)
  - SFT: Supervised Fine-Tuning (via Transformers/Unsloth)
  - DPO: Direct Preference Optimization (via MLX or TRL)
  - ORPO: Odds Ratio Preference Optimization (via TRL)

Engines: MLX (primary), TRANSFORMERS (fallback for SFT/ORPO)
Persistence: Neon DB (primary) + local JSON fallback.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# Enums
# ============================================================

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingMethod(str, Enum):
    MLX_LORA = "mlx_lora"
    MLX_QLORA = "mlx_qlora"
    SFT = "sft"
    DPO = "dpo"
    ORPO = "orpo"


class TrainingEngine(str, Enum):
    MLX = "mlx"
    TRANSFORMERS = "transformers"


class Strategy(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    HIGH_PRECISION = "high_precision"


# ============================================================
# Strategy Presets (legacy compat + quick picks)
# ============================================================

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

# Default advanced config per method
METHOD_DEFAULTS = {
    TrainingMethod.MLX_LORA: {
        "engine": "mlx",
        "epochs": 3, "learning_rate": 1e-4, "lora_rank": 4, "batch_size": 2,
        "num_layers": 8, "lora_alpha": 8, "lora_dropout": 0.05,
        "max_seq_length": 1024, "grad_accumulation": 4,
        "mask_prompt": True, "grad_checkpoint": True,
    },
    TrainingMethod.MLX_QLORA: {
        "engine": "mlx",
        "epochs": 3, "learning_rate": 1e-4, "lora_rank": 8, "batch_size": 2,
        "num_layers": 8, "lora_alpha": 16, "lora_dropout": 0.05,
        "max_seq_length": 1024, "grad_accumulation": 4,
        "mask_prompt": True, "grad_checkpoint": True,
    },
    TrainingMethod.SFT: {
        "engine": "transformers",
        "epochs": 3, "learning_rate": 2e-4, "lora_rank": 16, "batch_size": 4,
        "lora_alpha": 32, "lora_dropout": 0.05,
        "max_seq_length": 2048, "grad_accumulation": 4,
        "warmup_ratio": 0.03, "weight_decay": 0.01,
        "lr_scheduler": "cosine", "grad_checkpoint": True,
    },
    TrainingMethod.DPO: {
        "engine": "mlx",  # Try MLX first, fallback to TRL
        "epochs": 2, "learning_rate": 5e-5, "lora_rank": 16, "batch_size": 1,
        "lora_alpha": 32, "num_layers": 16,
        "max_seq_length": 4096, "beta": 0.1,
        "grad_checkpoint": True,
    },
    TrainingMethod.ORPO: {
        "engine": "transformers",
        "epochs": 3, "learning_rate": 8e-6, "lora_rank": 16, "batch_size": 2,
        "lora_alpha": 32, "lora_dropout": 0.05,
        "max_seq_length": 2048, "grad_accumulation": 4,
        "beta": 0.1, "grad_checkpoint": True,
    },
}


# ============================================================
# Available Libraries Detection
# ============================================================

_available_engines: dict[str, bool] = {}


def _detect_engines():
    """Detect available training libraries on this machine."""
    global _available_engines
    # MLX is always available on Apple Silicon
    try:
        import mlx  # noqa
        _available_engines["mlx"] = True
    except ImportError:
        _available_engines["mlx"] = False

    # Transformers/TRL
    try:
        import transformers  # noqa
        _available_engines["transformers"] = True
    except ImportError:
        _available_engines["transformers"] = False

    # Unsloth (speed boost for Transformers)
    try:
        import unsloth  # noqa
        _available_engines["unsloth"] = True
    except ImportError:
        _available_engines["unsloth"] = False

    logger.info(f"Available engines: {_available_engines}")


_detect_engines()


# ============================================================
# Training Job
# ============================================================

@dataclass
class TrainingJob:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    model: str = ""
    dataset_path: str = ""
    strategy: str = "standard"
    status: str = JobStatus.PENDING
    # Training params
    epochs: int = 3
    learning_rate: float = 2e-4
    lora_rank: int = 8
    batch_size: int = 2
    # Progress
    current_epoch: int = 0
    current_step: int = 0
    total_steps: int = 0
    loss: float = 0.0
    loss_history: list = field(default_factory=list)
    # Timing
    started_at: float = 0
    finished_at: float = 0
    output_dir: str = ""
    error: str = ""
    # --- New Fine-Tune Studio fields ---
    training_method: str = "mlx_lora"
    engine: str = "mlx"
    config: dict = field(default_factory=dict)
    best_loss: float = None
    lr_history: list = field(default_factory=list)
    memory_peak_gb: float = None
    estimated_duration_s: int = None
    estimated_memory_gb: float = None

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
JOBS_FILE = WORKSPACE / "jobs.json"

# Add AngelaAI root to sys.path for angela_core imports
_angela_root = Path(__file__).resolve().parents[2]  # MacOS/AITop -> AngelaAI
if str(_angela_root) not in sys.path:
    sys.path.insert(0, str(_angela_root))


# ============================================================
# Persistence — Neon primary, JSON fallback
# ============================================================

async def _save_to_neon(job: TrainingJob):
    try:
        from services.db_service import save_finetune_job
        await save_finetune_job(job.to_dict())
    except Exception as e:
        logger.warning(f"Neon save failed (job {job.id}): {e}")


def _save_jobs():
    try:
        data = [asdict(j) for j in _jobs.values()]
        JOBS_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to save jobs: {e}")


def _save_jobs_and_neon(job: TrainingJob):
    _save_jobs()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_save_to_neon(job))
        else:
            asyncio.run(_save_to_neon(job))
    except Exception:
        pass


def _load_jobs():
    if not JOBS_FILE.exists():
        return
    try:
        data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
        for d in data:
            job = TrainingJob(**{k: v for k, v in d.items() if k in TrainingJob.__dataclass_fields__})
            if job.status == JobStatus.RUNNING:
                job.status = JobStatus.FAILED
                job.error = "Process lost on restart"
                job.finished_at = job.finished_at or time.time()
            _jobs[job.id] = job
        logger.info(f"Loaded {len(_jobs)} jobs from disk")
    except Exception as e:
        logger.error(f"Failed to load jobs: {e}")


async def sync_from_cloud():
    try:
        from services.db_service import load_finetune_jobs
        cloud_jobs = await load_finetune_jobs()
        for d in cloud_jobs:
            jid = d["id"]
            if jid not in _jobs:
                job = TrainingJob(**{k: v for k, v in d.items() if k in TrainingJob.__dataclass_fields__})
                if job.status == JobStatus.RUNNING:
                    job.status = JobStatus.FAILED
                    job.error = "Process lost on restart"
                    job.finished_at = job.finished_at or time.time()
                _jobs[jid] = job
        logger.info(f"Synced {len(cloud_jobs)} jobs from Supabase (total: {len(_jobs)})")
    except Exception as e:
        logger.warning(f"Supabase sync failed: {e}")


_load_jobs()


# ============================================================
# Public API
# ============================================================

def get_strategies() -> list[dict]:
    """Return available fine-tuning strategy presets."""
    return [{"name": s.value, **STRATEGY_PRESETS[s]} for s in Strategy]


def get_training_methods() -> list[dict]:
    """Return available training methods with engine info."""
    methods = []
    for m in TrainingMethod:
        defaults = METHOD_DEFAULTS[m]
        engine = defaults["engine"]
        available = _available_engines.get(engine, False)
        methods.append({
            "id": m.value,
            "name": m.value.replace("_", " ").upper(),
            "engine": engine,
            "available": available,
            "description": _method_description(m),
            "defaults": {k: v for k, v in defaults.items() if k != "engine"},
        })
    return methods


def _method_description(m: TrainingMethod) -> str:
    descs = {
        TrainingMethod.MLX_LORA: "Apple Silicon native LoRA — fast, efficient, recommended",
        TrainingMethod.MLX_QLORA: "Quantized LoRA — less memory, slightly less quality",
        TrainingMethod.SFT: "Full supervised fine-tuning via Transformers/Unsloth",
        TrainingMethod.DPO: "Direct Preference Optimization — chosen vs rejected",
        TrainingMethod.ORPO: "Odds Ratio Preference Optimization — simpler than DPO",
    }
    return descs.get(m, "")


def create_job(
    model: str,
    dataset_path: str,
    training_method: str = "mlx_lora",
    engine: str = None,
    strategy: str = None,
    config: dict = None,
    # Legacy params (backwards compatible)
    epochs: Optional[int] = None,
    learning_rate: Optional[float] = None,
    lora_rank: Optional[int] = None,
    batch_size: Optional[int] = None,
) -> TrainingJob:
    """Create a new fine-tuning job (does not start it)."""
    method = TrainingMethod(training_method)
    defaults = METHOD_DEFAULTS[method].copy()

    # Apply strategy preset if provided
    if strategy:
        preset = STRATEGY_PRESETS.get(Strategy(strategy), {})
        defaults.update({k: v for k, v in preset.items() if k != "description"})

    # Apply custom config overrides
    if config:
        defaults.update(config)

    # Apply legacy param overrides
    if epochs is not None:
        defaults["epochs"] = epochs
    if learning_rate is not None:
        defaults["learning_rate"] = learning_rate
    if lora_rank is not None:
        defaults["lora_rank"] = lora_rank
    if batch_size is not None:
        defaults["batch_size"] = batch_size

    resolved_engine = engine or defaults.pop("engine", "mlx")

    # Pre-training estimation
    from services.training_estimator import estimate_duration, estimate_memory
    dur = estimate_duration(
        model_name=model,
        num_samples=_count_dataset_lines(dataset_path),
        method=training_method,
        epochs=defaults.get("epochs", 3),
        batch_size=defaults.get("batch_size", 2),
        grad_accumulation=defaults.get("grad_accumulation", 4),
        max_seq_length=defaults.get("max_seq_length", 1024),
    )
    mem = estimate_memory(model_name=model, method=training_method,
                          batch_size=defaults.get("batch_size", 2),
                          max_seq_length=defaults.get("max_seq_length", 1024))

    job = TrainingJob(
        model=model,
        dataset_path=dataset_path,
        strategy=strategy or "custom",
        training_method=training_method,
        engine=resolved_engine,
        config=defaults,
        epochs=defaults.get("epochs", 3),
        learning_rate=defaults.get("learning_rate", 2e-4),
        lora_rank=defaults.get("lora_rank", 8),
        batch_size=defaults.get("batch_size", 2),
        total_steps=dur.get("total_steps", 0),
        estimated_duration_s=dur.get("estimated_seconds"),
        estimated_memory_gb=mem.get("recommended_gb"),
    )
    job.output_dir = str(WORKSPACE / job.id)
    os.makedirs(job.output_dir, exist_ok=True)
    _jobs[job.id] = job
    _save_jobs_and_neon(job)
    return job


async def start_job(job_id: str) -> TrainingJob:
    """Start a fine-tuning job based on its training method."""
    job = _jobs.get(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    if job.status == JobStatus.RUNNING:
        raise ValueError(f"Job {job_id} is already running")

    job.status = JobStatus.RUNNING
    job.started_at = time.time()
    _save_jobs_and_neon(job)

    method = TrainingMethod(job.training_method)

    try:
        if method in (TrainingMethod.MLX_LORA, TrainingMethod.MLX_QLORA):
            _start_mlx_training(job)
        elif method == TrainingMethod.DPO:
            _start_dpo_training(job)
        elif method in (TrainingMethod.SFT, TrainingMethod.ORPO):
            _start_transformers_training(job)
        else:
            raise ValueError(f"Unsupported method: {method}")
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        _save_jobs_and_neon(job)

    return job


# ============================================================
# Training Method Implementations
# ============================================================

def _prepare_mlx_data(dataset_path: str, output_dir: str) -> str:
    """Split single JSONL into train.jsonl + valid.jsonl for MLX (90/10 split)."""
    data_dir = Path(output_dir) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Read all examples
    examples = []
    src = Path(dataset_path)
    with open(src, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                # MLX expects only 'messages' key — strip metadata
                clean = {"messages": row["messages"]} if "messages" in row else row
                examples.append(clean)

    # 90/10 split
    split_idx = int(len(examples) * 0.9)
    train = examples[:split_idx]
    valid = examples[split_idx:]

    # Write files
    with open(data_dir / "train.jsonl", 'w', encoding='utf-8') as f:
        for ex in train:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    with open(data_dir / "valid.jsonl", 'w', encoding='utf-8') as f:
        for ex in valid:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')

    logger.info(f"Prepared MLX data: {len(train)} train, {len(valid)} valid → {data_dir}")
    return str(data_dir)


# Ollama name → HuggingFace MLX model mapping
OLLAMA_TO_HF_MLX = {
    "scb10x/typhoon2.5-qwen3-4b": "typhoon-ai/typhoon2.1-gemma3-4b-mlx-4bit",
    "scb10x/typhoon-ocr1.5-3b": "typhoon-ai/llama3.2-typhoon2-3b-instruct-mlx-4bit",
    "gemma3:12b": "typhoon-ai/typhoon2.1-gemma3-12b-mlx-4bit",
    # NOTE: gemma-3n (E4B/E2B) currently breaks mlx_lm LoRA — altup.prediction_coefs
    # layer gets LoRA-wrapped but model code accesses .weight directly.
    # Map gemma4:e4b to Typhoon Gemma3-4B (Thai-tuned, same ~4B class, stable with LoRA).
    "gemma4:e4b": "typhoon-ai/typhoon2.1-gemma3-4b-mlx-4bit",
    "qwen2.5:7b": "typhoon-ai/typhoon2-qwen2.5-7b-instruct-mlx-4bit",
    "llama3.1:8b": "typhoon-ai/llama3.1-typhoon2-8b-instruct-mlx-4bit",
}


def _resolve_mlx_model(ollama_name: str) -> str:
    """Convert Ollama model name to HuggingFace MLX model ID."""
    # Strip :latest or :tag
    base = ollama_name.split(":")[0] if ":" in ollama_name else ollama_name
    # Check mapping
    for key, hf_id in OLLAMA_TO_HF_MLX.items():
        if key in ollama_name or key in base:
            logger.info(f"Model mapped: {ollama_name} → {hf_id}")
            return hf_id
    # If already a HF model ID (contains no colon), use as-is
    if ":" not in ollama_name:
        return ollama_name
    # Fallback: strip tag
    logger.warning(f"No MLX mapping for {ollama_name}, using base: {base}")
    return base


def _start_mlx_training(job: TrainingJob):
    """Start MLX LoRA/QLoRA training via mlx_lm subprocess."""
    cfg = job.config
    # Note: mlx_lm >=0.20 only supports {lora, dora, full}. QLoRA = LoRA on
    # a pre-quantized base model (e.g. *-4bit). So always pass "lora" here;
    # the quantization is inherited from the model.
    fine_tune_type = "lora"

    # Resolve model name: Ollama → HuggingFace MLX
    hf_model = _resolve_mlx_model(job.model)

    # Prepare data: split into train.jsonl + valid.jsonl
    data_dir = _prepare_mlx_data(job.dataset_path, job.output_dir)

    # Create LoRA config YAML
    lora_rank = cfg.get("lora_rank", job.lora_rank)
    lora_alpha = cfg.get("lora_alpha", lora_rank * 2)
    lora_dropout = cfg.get("lora_dropout", 0.05)
    scale = lora_alpha / lora_rank

    config_dir = Path(job.output_dir)
    config_file = config_dir / "lora_config.yaml"
    config_file.write_text(f"""lora_parameters:
  rank: {lora_rank}
  dropout: {lora_dropout}
  scale: {scale}
""")

    adapter_path = str(config_dir / "adapters")
    os.makedirs(adapter_path, exist_ok=True)

    cmd = [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", hf_model,
        "--train",
        "--data", data_dir,
        "--adapter-path", adapter_path,
        "--fine-tune-type", fine_tune_type,
        "--num-layers", str(cfg.get("num_layers", 8)),
        "--iters", str(job.total_steps or job.epochs * 100),
        "--batch-size", str(job.batch_size),
        "--learning-rate", str(job.learning_rate),
        "--save-every", str(cfg.get("save_every", 200)),
        "--seed", "42",
        "-c", str(config_file),
        "--max-seq-length", str(cfg.get("max_seq_length", 1024)),
    ]

    if cfg.get("grad_checkpoint", True):
        cmd.append("--grad-checkpoint")
    if cfg.get("mask_prompt", True):
        cmd.append("--mask-prompt")
    if cfg.get("grad_accumulation", 1) > 1:
        cmd.extend(["--grad-accumulation-steps", str(cfg["grad_accumulation"])])
    if cfg.get("test_batches"):
        cmd.extend(["--test-batches", str(cfg["test_batches"])])

    logger.info(f"MLX command: {' '.join(cmd)}")
    _launch_subprocess(job, cmd)


def _start_dpo_training(job: TrainingJob):
    """Start DPO training — try MLX first, fallback to TRL."""
    cfg = job.config

    # Use angela_core DPO trainer via subprocess
    cmd = [
        sys.executable, "-m", "angela_core.training.dpo_trainer",
        "--data", job.dataset_path,
        "--output", job.output_dir,
        "--model", job.model,
        "--beta", str(cfg.get("beta", 0.1)),
        "--epochs", str(job.epochs),
        "--batch-size", str(job.batch_size),
        "--learning-rate", str(job.learning_rate),
        "--lora-rank", str(job.lora_rank),
    ]

    # Resume from SFT adapters if specified
    sft_adapters = cfg.get("sft_adapters_path")
    if sft_adapters:
        cmd.extend(["--adapters", sft_adapters])

    logger.info(f"DPO command: {' '.join(cmd)}")
    _launch_subprocess(job, cmd)


def _start_transformers_training(job: TrainingJob):
    """Start SFT/ORPO training via Transformers/Unsloth subprocess."""
    cfg = job.config
    method = job.training_method

    # Build a training script that runs in subprocess
    script = _build_transformers_script(job, method, cfg)
    script_path = Path(job.output_dir) / "train_script.py"
    script_path.write_text(script, encoding="utf-8")

    cmd = [sys.executable, str(script_path)]
    logger.info(f"Transformers command: {' '.join(cmd)}")
    _launch_subprocess(job, cmd)


def _build_transformers_script(job: TrainingJob, method: str, cfg: dict) -> str:
    """Generate a standalone training script for Transformers/TRL."""
    return f'''#!/usr/bin/env python3
"""Auto-generated training script for {method.upper()} — Job {job.id}"""
import sys
import json
import time

# Try Unsloth first (2x faster)
use_unsloth = False
try:
    from unsloth import FastLanguageModel, is_bfloat16_supported
    use_unsloth = True
    print("Using Unsloth (2x speedup)")
except ImportError:
    print("Unsloth not available, using standard Transformers")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

device = "mps" if torch.backends.mps.is_available() else "cpu"
dtype = torch.float16 if device == "mps" else torch.float32
print(f"Device: {{device}}, dtype: {{dtype}}")

# Load model
model_name = "{job.model}"
lora_rank = {cfg.get("lora_rank", 16)}
lora_alpha = {cfg.get("lora_alpha", 32)}

if use_unsloth:
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name, max_seq_length={cfg.get("max_seq_length", 2048)},
        dtype=dtype, load_in_4bit={"True" if method == "qlora" else "False"},
    )
    model = FastLanguageModel.get_peft_model(
        model, r=lora_rank,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=lora_alpha, lora_dropout={cfg.get("lora_dropout", 0.05)},
        bias="none", use_gradient_checkpointing="unsloth",
    )
else:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype)
    if device == "mps":
        model = model.to(device)
    lora_config = LoraConfig(
        r=lora_rank, lora_alpha=lora_alpha, lora_dropout={cfg.get("lora_dropout", 0.05)},
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)

# Load dataset
dataset = load_dataset("json", data_files="{job.dataset_path}", split="train")
print(f"Dataset: {{len(dataset)}} examples")

# Training args
training_args = TrainingArguments(
    output_dir="{job.output_dir}/output",
    num_train_epochs={job.epochs},
    per_device_train_batch_size={job.batch_size},
    gradient_accumulation_steps={cfg.get("grad_accumulation", 4)},
    learning_rate={job.learning_rate},
    warmup_ratio={cfg.get("warmup_ratio", 0.03)},
    weight_decay={cfg.get("weight_decay", 0.01)},
    logging_steps=10,
    save_steps=100,
    fp16=(device == "mps"),
    gradient_checkpointing={cfg.get("grad_checkpoint", True)},
    optim="adamw_torch",
    lr_scheduler_type="{cfg.get("lr_scheduler", "cosine")}",
    report_to="none",
    remove_unused_columns=False,
)

# Train
{"from trl import ORPOTrainer, ORPOConfig" if method == "orpo" else "from trl import SFTTrainer"}

{"trainer = ORPOTrainer(" if method == "orpo" else "trainer = SFTTrainer("}
    model=model, tokenizer=tokenizer, train_dataset=dataset, args=training_args,
    max_seq_length={cfg.get("max_seq_length", 2048)},
)
print("Starting training...")
trainer.train()

# Save
model.save_pretrained("{job.output_dir}/adapters")
tokenizer.save_pretrained("{job.output_dir}/adapters")
print("Training completed!")
'''


# ============================================================
# Subprocess Management
# ============================================================

def _launch_subprocess(job: TrainingJob, cmd: list[str]):
    """Launch training as subprocess and monitor in background."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        _processes[job.id] = proc
        asyncio.get_event_loop().run_in_executor(None, _monitor_job, job.id)
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        _save_jobs_and_neon(job)


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

            # Parse loss values (MLX format: "Iter 100: Train loss 2.345, ...")
            loss_match = re.search(r'(?:Train |train )?loss[:\s]+(\d+\.?\d*)', line, re.IGNORECASE)
            if loss_match:
                try:
                    loss_val = float(loss_match.group(1))
                    job.loss = loss_val
                    if job.best_loss is None or loss_val < job.best_loss:
                        job.best_loss = loss_val
                    job.loss_history.append({
                        "step": job.current_step,
                        "loss": loss_val,
                        "timestamp": time.time(),
                    })
                except ValueError:
                    pass

            # Parse iteration/step
            iter_match = re.search(r'Iter\s+(\d+)', line)
            if iter_match:
                job.current_step = int(iter_match.group(1))

            # Parse learning rate (if logged)
            lr_match = re.search(r'lr[:\s]+(\d+\.?\d*e?-?\d*)', line, re.IGNORECASE)
            if lr_match:
                try:
                    lr_val = float(lr_match.group(1))
                    job.lr_history.append({
                        "step": job.current_step,
                        "lr": lr_val,
                        "timestamp": time.time(),
                    })
                except ValueError:
                    pass

            # Periodic save (every 50 steps)
            if job.current_step > 0 and job.current_step % 50 == 0:
                _save_jobs_and_neon(job)

        proc.wait()
        if proc.returncode == 0:
            job.status = JobStatus.COMPLETED
            # Save trained model to DB
            _save_trained_model_async(job)
        else:
            job.status = JobStatus.FAILED
            job.error = f"Process exited with code {proc.returncode}"
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
    finally:
        job.finished_at = time.time()
        _save_jobs_and_neon(job)


def cancel_job(job_id: str) -> bool:
    """Cancel a running job."""
    proc = _processes.get(job_id)
    job = _jobs.get(job_id)
    if proc and job:
        proc.terminate()
        job.status = JobStatus.CANCELLED
        job.finished_at = time.time()
        _save_jobs_and_neon(job)
        return True
    return False


def get_job(job_id: str) -> Optional[dict]:
    """Get job status."""
    job = _jobs.get(job_id)
    return job.to_dict() if job else None


def list_jobs() -> list[dict]:
    """List all jobs."""
    return [j.to_dict() for j in _jobs.values()]


# ============================================================
# Helpers
# ============================================================

def _save_trained_model_async(job: TrainingJob):
    """Save trained model record to DB after successful training."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_save_trained_model(job))
    except Exception:
        pass


async def _save_trained_model(job: TrainingJob):
    """Save trained model to local_models table + link to job."""
    try:
        from services.db_service import save_trained_model, link_job_to_model
        duration_s = int(job.finished_at - job.started_at) if job.finished_at and job.started_at else None

        model_id = await save_trained_model({
            "name": f"{job.model}-{job.training_method}-{job.id}",
            "model_type": "lora",
            "hf_model_id": job.model,
            "file_path": os.path.join(job.output_dir, "adapters"),
            "file_size_mb": _dir_size_mb(os.path.join(job.output_dir, "adapters")),
            "status": "ready",
            "training_job_id": job.id,
            "training_config": job.config,
            "best_loss": job.best_loss,
            "training_duration_s": duration_s,
        })

        if model_id:
            await link_job_to_model(job.id, model_id)
            logger.info(f"Trained model saved: {model_id} (job {job.id})")
    except Exception as e:
        logger.warning(f"Failed to save trained model: {e}")


def _dir_size_mb(path: str) -> float:
    """Get directory size in MB."""
    try:
        p = Path(path)
        if not p.exists():
            return 0.0
        total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return round(total / (1024 * 1024), 1)
    except Exception:
        return 0.0


def _count_dataset_lines(path: str) -> int:
    """Count lines in dataset file (for estimation)."""
    try:
        p = Path(path)
        if not p.exists():
            return 100  # Default estimate
        if p.suffix in (".jsonl", ".json"):
            with open(p) as f:
                return sum(1 for _ in f)
        elif p.suffix == ".csv":
            with open(p) as f:
                return sum(1 for _ in f) - 1  # Minus header
        return 100
    except Exception:
        return 100
