"""
Training Estimator — Duration & memory estimation for Fine-Tune Studio.
Ported from AiFineTune with Apple Silicon calibration.
"""

import logging
import psutil
from typing import Optional

logger = logging.getLogger(__name__)


# ==================== Model Size Inference ====================

# Known model sizes (billions of parameters)
MODEL_SIZES: dict[str, float] = {
    # Typhoon (Thai LLM)
    "typhoon": 4.0,
    "typhoon2": 4.0,
    "typhoon2.1": 4.0,
    # Llama
    "llama-3.2-1b": 1.0,
    "llama-3.2-3b": 3.0,
    "llama-3.1-8b": 8.0,
    "llama-3.3-70b": 70.0,
    # Qwen
    "qwen2.5-0.5b": 0.5,
    "qwen2.5-1.5b": 1.5,
    "qwen2.5-3b": 3.0,
    "qwen2.5-7b": 7.0,
    "qwen2.5-14b": 14.0,
    "qwen2.5-32b": 32.0,
    # Gemma
    "gemma-2-2b": 2.0,
    "gemma-2-9b": 9.0,
    "gemma-2-27b": 27.0,
    "gemma3-4b": 4.0,
    # Phi
    "phi-3.5-mini": 3.8,
    "phi-4": 14.0,
    # Mistral
    "mistral-7b": 7.0,
    "mixtral-8x7b": 47.0,
}


def estimate_model_size(model_name: str) -> float:
    """Estimate model size in billions from model name."""
    name_lower = model_name.lower()
    # Try known models
    for key, size in MODEL_SIZES.items():
        if key in name_lower:
            return size
    # Try extracting from name patterns like "7b", "13b", "70b"
    import re
    match = re.search(r'(\d+(?:\.\d+)?)b', name_lower)
    if match:
        return float(match.group(1))
    # Default to 7B
    return 7.0


# ==================== Duration Estimation ====================

def estimate_duration(
    model_name: str,
    num_samples: int,
    method: str = "mlx_lora",
    epochs: int = 3,
    batch_size: int = 2,
    grad_accumulation: int = 4,
    max_seq_length: int = 1024,
) -> dict:
    """
    Estimate training duration on Apple Silicon (MPS).

    Returns dict with estimated_seconds, formatted, confidence, basis.
    """
    model_size = estimate_model_size(model_name)

    # Calculate total steps
    effective_batch = batch_size * grad_accumulation
    steps_per_epoch = max(1, num_samples // effective_batch)
    total_steps = steps_per_epoch * epochs

    # Base: 0.8s per step for 7B LoRA on A100 CUDA
    base_time = 0.8

    # Device: Apple Silicon MPS ~3x slower than CUDA
    device_mult = 3.0

    # Method multipliers
    method_mults = {
        "mlx_lora": 0.8,    # MLX is faster than Transformers on Apple Silicon
        "mlx_qlora": 0.7,   # QLoRA even faster
        "sft": 1.2,
        "lora": 1.0,
        "qlora": 0.9,
        "dpo": 1.5,
        "orpo": 1.3,
    }
    method_mult = method_mults.get(method, 1.0)

    # Model size multiplier (baseline 7B)
    size_mult = model_size / 7.0

    # Sequence length multiplier (baseline 2048)
    seq_mult = max_seq_length / 2048.0

    time_per_step = base_time * device_mult * method_mult * size_mult * seq_mult
    estimated_seconds = total_steps * time_per_step + 180  # 3min overhead

    hours = estimated_seconds / 3600
    minutes = estimated_seconds / 60

    if hours >= 1:
        formatted = f"{hours:.1f}h"
    elif minutes >= 1:
        formatted = f"{minutes:.0f}min"
    else:
        formatted = f"{estimated_seconds:.0f}s"

    # MLX methods have higher confidence on Apple Silicon
    confidence = "high" if method.startswith("mlx") else "medium"

    return {
        "estimated_seconds": round(estimated_seconds),
        "estimated_minutes": round(minutes, 1),
        "estimated_hours": round(hours, 2),
        "formatted": formatted,
        "confidence": confidence,
        "total_steps": total_steps,
        "model_size_b": model_size,
        "basis": f"{total_steps} steps, MPS, {method.upper()}, ~{model_size}B params",
    }


# ==================== Memory Estimation ====================

def estimate_memory(
    model_name: str,
    method: str = "mlx_lora",
    batch_size: int = 2,
    max_seq_length: int = 1024,
) -> dict:
    """
    Estimate memory required for training on Apple Silicon unified memory.

    Returns dict with minimum_gb, recommended_gb, notes, fits_current_machine.
    """
    model_size = estimate_model_size(model_name)

    # Base model memory
    # MLX 4-bit models: ~0.5 bytes per param
    # MLX fp16 models: ~2 bytes per param
    is_quantized = any(q in model_name.lower() for q in ["4bit", "4-bit", "int4", "q4"])
    bytes_per_param = 0.5 if is_quantized else 2.0
    model_mem_gb = model_size * bytes_per_param

    # Method multipliers for training overhead
    method_mults = {
        "mlx_lora": 1.3,    # MLX LoRA very efficient
        "mlx_qlora": 1.2,   # Even more efficient
        "sft": 4.0,
        "lora": 1.5,
        "qlora": 0.5,
        "dpo": 3.0,         # Needs reference model
        "orpo": 2.0,
    }
    method_mult = method_mults.get(method, 1.5)

    # Activation memory
    activation_mem = batch_size * max_seq_length * model_size * 0.001

    min_mem = model_mem_gb * method_mult + activation_mem
    recommended = min_mem * 1.3

    # Check current machine
    total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    fits = recommended <= total_ram_gb * 0.8  # 80% threshold

    # Apple Silicon notes
    if is_quantized and model_size <= 4:
        notes = f"4-bit {model_size}B fits easily on {total_ram_gb:.0f}GB unified memory"
    elif is_quantized and model_size <= 13:
        notes = f"4-bit {model_size}B needs ~{min_mem:.0f}GB — {'OK' if fits else 'tight'} on {total_ram_gb:.0f}GB"
    elif method in ("dpo", "orpo") and model_size > 7:
        notes = "Preference training on large models — consider QLoRA"
    elif method == "sft":
        notes = "Full SFT needs significant memory — consider LoRA/QLoRA"
    else:
        notes = f"~{min_mem:.0f}GB needed for {method} on {model_size}B model"

    return {
        "minimum_gb": round(min_mem, 1),
        "recommended_gb": round(recommended, 1),
        "model_memory_gb": round(model_mem_gb, 1),
        "total_ram_gb": round(total_ram_gb, 1),
        "fits_current_machine": fits,
        "method": method,
        "model_size_b": model_size,
        "is_quantized": is_quantized,
        "notes": notes,
    }
