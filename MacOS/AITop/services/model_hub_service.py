"""
Model Hub Service — HuggingFace integration, local model tracking, Ollama deployment.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODELS_DIR = Path.home() / ".aitop" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Curated popular models for Fine-Tune Studio
POPULAR_MODELS = [
    # MLX 4-bit (Apple Silicon native — recommended)
    {"id": "scb10x/typhoon2.1-gemma3-4b-mlx-4bit", "name": "Typhoon 2.1 4B (MLX 4-bit)", "size_b": 4.0, "engine": "mlx", "recommended": True},
    {"id": "mlx-community/Llama-3.2-3B-Instruct-4bit", "name": "Llama 3.2 3B (MLX 4-bit)", "size_b": 3.0, "engine": "mlx"},
    {"id": "mlx-community/Llama-3.1-8B-Instruct-4bit", "name": "Llama 3.1 8B (MLX 4-bit)", "size_b": 8.0, "engine": "mlx"},
    {"id": "mlx-community/Qwen2.5-7B-Instruct-4bit", "name": "Qwen 2.5 7B (MLX 4-bit)", "size_b": 7.0, "engine": "mlx"},
    {"id": "mlx-community/gemma-2-9b-it-4bit", "name": "Gemma 2 9B (MLX 4-bit)", "size_b": 9.0, "engine": "mlx"},
    {"id": "mlx-community/Phi-3.5-mini-instruct-4bit", "name": "Phi 3.5 Mini (MLX 4-bit)", "size_b": 3.8, "engine": "mlx"},
    {"id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit", "name": "Mistral 7B v0.3 (MLX 4-bit)", "size_b": 7.0, "engine": "mlx"},
    # Unsloth (for Transformers engine)
    {"id": "unsloth/Llama-3.2-1B-Instruct", "name": "Llama 3.2 1B (Unsloth)", "size_b": 1.0, "engine": "transformers"},
    {"id": "unsloth/Llama-3.2-3B-Instruct", "name": "Llama 3.2 3B (Unsloth)", "size_b": 3.0, "engine": "transformers"},
    {"id": "unsloth/Qwen2.5-7B-Instruct", "name": "Qwen 2.5 7B (Unsloth)", "size_b": 7.0, "engine": "transformers"},
]


# ============================================================
# HuggingFace Search
# ============================================================

async def search_huggingface(query: str, limit: int = 20, task: str = "text-generation") -> list[dict]:
    """Search HuggingFace Hub for models."""
    try:
        from huggingface_hub import list_models
        results = await asyncio.to_thread(
            lambda: list(list_models(
                search=query,
                task=task,
                sort="downloads",
                direction=-1,
                limit=limit,
            ))
        )
        return [
            {
                "id": m.id,
                "name": m.id.split("/")[-1],
                "author": m.id.split("/")[0] if "/" in m.id else "",
                "downloads": getattr(m, "downloads", 0),
                "likes": getattr(m, "likes", 0),
                "pipeline_tag": getattr(m, "pipeline_tag", ""),
                "tags": list(getattr(m, "tags", []))[:5],
                "last_modified": str(getattr(m, "last_modified", "")),
            }
            for m in results
        ]
    except ImportError:
        logger.warning("huggingface_hub not installed")
        return []
    except Exception as e:
        logger.error(f"HF search error: {e}")
        return []


async def get_model_info(hf_model_id: str) -> dict:
    """Get detailed info about a HuggingFace model."""
    try:
        from huggingface_hub import model_info
        info = await asyncio.to_thread(lambda: model_info(hf_model_id))
        return {
            "id": info.id,
            "author": getattr(info, "author", ""),
            "downloads": getattr(info, "downloads", 0),
            "likes": getattr(info, "likes", 0),
            "pipeline_tag": getattr(info, "pipeline_tag", ""),
            "tags": list(getattr(info, "tags", [])),
            "gated": getattr(info, "gated", False),
            "library_name": getattr(info, "library_name", ""),
            "siblings": [
                {"rfilename": s.rfilename, "size": getattr(s, "size", 0)}
                for s in (getattr(info, "siblings", []) or [])
                if hasattr(s, "rfilename")
            ][:20],
        }
    except Exception as e:
        logger.error(f"HF model info error: {e}")
        return {"error": str(e)}


# ============================================================
# Model Download
# ============================================================

async def download_model(hf_model_id: str, name: str = None) -> dict:
    """Download a model from HuggingFace to local storage."""
    model_name = name or hf_model_id.split("/")[-1]
    local_path = MODELS_DIR / model_name

    # Get HF token
    hf_token = _get_hf_token()

    try:
        from huggingface_hub import snapshot_download
        result_path = await asyncio.to_thread(
            lambda: snapshot_download(
                repo_id=hf_model_id,
                local_dir=str(local_path),
                token=hf_token,
            )
        )

        # Calculate size
        size_mb = sum(f.stat().st_size for f in Path(result_path).rglob("*") if f.is_file()) / (1024 * 1024)

        # Save to DB
        try:
            from services.db_service import save_local_model
            model_id = await save_local_model({
                "name": model_name,
                "model_type": "base",
                "hf_model_id": hf_model_id,
                "file_path": str(result_path),
                "file_size_mb": round(size_mb, 1),
                "status": "ready",
            })
            return {
                "id": model_id,
                "name": model_name,
                "hf_model_id": hf_model_id,
                "path": str(result_path),
                "size_mb": round(size_mb, 1),
                "status": "ready",
            }
        except Exception as e:
            logger.warning(f"DB save failed: {e}")
            return {"name": model_name, "path": str(result_path), "size_mb": round(size_mb, 1)}

    except Exception as e:
        logger.error(f"Download error: {e}")
        return {"error": str(e)}


# ============================================================
# Ollama Deployment
# ============================================================

async def import_to_ollama(adapter_path: str, base_model: str, ollama_name: str) -> dict:
    """Deploy fine-tuned adapters to Ollama (fuse + GGUF + register)."""
    try:
        # Try using angela_core OllamaDeployer
        from angela_core.training.train_angela import OllamaDeployer
        # This is a complex pipeline, run in thread
        # For now, use simplified approach: create Modelfile pointing to adapters
        pass
    except ImportError:
        pass

    # Simplified Ollama import via Modelfile
    try:
        import subprocess
        adapter_dir = Path(adapter_path)

        # Check if there's a fused model or just adapters
        if (adapter_dir / "model.safetensors").exists():
            # Already fused model — use directly
            model_path = str(adapter_dir)
        else:
            # Just adapters — need to fuse with base model first
            fused_dir = adapter_dir.parent / "fused"
            fused_dir.mkdir(exist_ok=True)

            # Fuse using mlx_lm
            fuse_cmd = [
                "python3", "-m", "mlx_lm", "fuse",
                "--model", base_model,
                "--adapter-path", str(adapter_dir),
                "--save-path", str(fused_dir),
            ]
            result = await asyncio.to_thread(
                lambda: subprocess.run(fuse_cmd, capture_output=True, text=True, timeout=600)
            )
            if result.returncode != 0:
                return {"error": f"Fuse failed: {result.stderr[:200]}"}
            model_path = str(fused_dir)

        # Create Modelfile
        modelfile_path = Path(model_path) / "Modelfile"
        modelfile_path.write_text(f'FROM {model_path}\nPARAMETER temperature 0.7\n')

        # Register with Ollama
        create_cmd = ["ollama", "create", ollama_name, "-f", str(modelfile_path)]
        result = await asyncio.to_thread(
            lambda: subprocess.run(create_cmd, capture_output=True, text=True, timeout=600)
        )
        if result.returncode != 0:
            return {"error": f"Ollama create failed: {result.stderr[:200]}"}

        return {
            "ollama_name": ollama_name,
            "model_path": model_path,
            "status": "deployed",
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Push to HuggingFace
# ============================================================

async def push_to_huggingface(model_path: str, repo_name: str, private: bool = True) -> dict:
    """Push a model to HuggingFace Hub."""
    hf_token = _get_hf_token()
    if not hf_token:
        return {"error": "No HuggingFace token configured"}

    try:
        from huggingface_hub import HfApi
        api = HfApi(token=hf_token)

        # Create repo
        await asyncio.to_thread(
            lambda: api.create_repo(repo_name, private=private, exist_ok=True)
        )

        # Upload
        await asyncio.to_thread(
            lambda: api.upload_folder(
                folder_path=model_path,
                repo_id=repo_name,
            )
        )

        return {
            "repo_name": repo_name,
            "url": f"https://huggingface.co/{repo_name}",
            "status": "pushed",
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Local Models
# ============================================================

async def list_local_models() -> list[dict]:
    """List all locally tracked models (from DB + filesystem)."""
    try:
        from services.db_service import list_local_models as db_list
        return await db_list()
    except Exception as e:
        logger.warning(f"DB list failed: {e}")
        # Fallback: scan filesystem
        models = []
        for d in MODELS_DIR.iterdir():
            if d.is_dir():
                size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / (1024 * 1024)
                models.append({
                    "name": d.name,
                    "model_type": "base",
                    "file_path": str(d),
                    "file_size_mb": round(size_mb, 1),
                    "status": "ready",
                })
        return models


def get_popular_models() -> list[dict]:
    """Get curated list of popular models for fine-tuning."""
    return POPULAR_MODELS


# ============================================================
# Helpers
# ============================================================

def _get_hf_token() -> Optional[str]:
    """Get HuggingFace token from angela_secrets or env."""
    token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
    if token:
        return token
    # Try angela_secrets
    secrets_path = Path.home() / ".angela_secrets"
    if secrets_path.exists():
        for line in secrets_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("HUGGINGFACE_TOKEN="):
                return line.split("=", 1)[1].strip()
    return None
