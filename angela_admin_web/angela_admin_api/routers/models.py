"""
💜 Fine-tuned Models API Router
Endpoints for managing Angela's fine-tuned models
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import shutil
from pathlib import Path

from ..services.model_service import ModelService, TEMP_DIR

router = APIRouter(prefix="/api/models", tags=["models"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ModelUploadRequest(BaseModel):
    """Model upload request"""
    model_name: str
    display_name: str
    description: Optional[str] = None
    base_model: str
    model_type: str  # qwen, llama, mistral
    model_size: Optional[str] = None
    training_examples: Optional[int] = None
    training_epochs: Optional[int] = None
    final_loss: Optional[float] = None
    evaluation_score: Optional[float] = None
    version: str = "v1.0"


class ModelResponse(BaseModel):
    """Model response"""
    model_id: str
    model_name: str
    display_name: str
    description: Optional[str]
    base_model: str
    model_type: str
    model_size: Optional[str]
    status: str
    is_active: bool
    is_imported_to_ollama: bool
    ollama_model_name: Optional[str]
    file_size_mb: Optional[float]
    training_date: datetime
    training_examples: Optional[int]
    training_epochs: Optional[int]
    final_loss: Optional[float]
    quality_rating: Optional[float]
    total_uses: int
    created_at: datetime
    version: str


class ImportToOllamaRequest(BaseModel):
    """Import to Ollama request"""
    ollama_model_name: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/upload", response_model=dict)
async def upload_model(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model_name: str = Form(...),
    display_name: str = Form(...),
    description: Optional[str] = Form(None),
    base_model: str = Form(...),
    model_type: str = Form(...),
    model_size: Optional[str] = Form(None),
    training_examples: Optional[int] = Form(None),
    training_epochs: Optional[int] = Form(None),
    final_loss: Optional[float] = Form(None),
    evaluation_score: Optional[float] = Form(None),
    version: str = Form("v1.0")
):
    """
    Upload a fine-tuned model ZIP file

    The ZIP file should contain:
    - Model files (GGUF or safetensors)
    - Adapter config (if using LoRA)
    - Tokenizer files
    """
    try:
        # Validate file type
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")

        # Save uploaded file to temp directory
        temp_file_path = TEMP_DIR / file.filename
        with open(temp_file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Prepare training info
        training_info = {
            "training_date": datetime.now(),
            "training_examples": training_examples,
            "training_epochs": training_epochs,
            "final_loss": final_loss,
            "evaluation_score": evaluation_score,
            "version": version
        }

        # Upload and extract model
        result = await ModelService.upload_model(
            file_path=str(temp_file_path),
            model_name=model_name,
            display_name=display_name,
            description=description or "",
            base_model=base_model,
            model_type=model_type,
            training_info=training_info
        )

        # Clean up temp file
        temp_file_path.unlink()

        return {
            "success": True,
            "message": f"Model '{model_name}' uploaded successfully",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=List[dict])
async def list_models(status: Optional[str] = None):
    """
    List all fine-tuned models

    Optional filter by status: uploaded, importing, ready, active, archived, failed
    """
    try:
        models = await ModelService.list_models(status=status)

        # Convert datetime/UUID to strings for JSON serialization
        for model in models:
            for key, value in model.items():
                if isinstance(value, datetime):
                    model[key] = value.isoformat()
                elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                    model[key] = str(value)

        return models

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=dict)
async def get_active_model():
    """Get currently active model"""
    try:
        model = await ModelService.get_active_model()

        if not model:
            return {"message": "No active model"}

        # Convert datetime/UUID to strings
        for key, value in model.items():
            if isinstance(value, datetime):
                model[key] = value.isoformat()
            elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                model[key] = str(value)

        return model

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", response_model=dict)
async def get_model(model_id: str):
    """Get model by ID"""
    try:
        model = await ModelService.get_model(model_id)

        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        # Convert datetime/UUID to strings
        for key, value in model.items():
            if isinstance(value, datetime):
                model[key] = value.isoformat()
            elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                model[key] = str(value)

        return model

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/import-to-ollama", response_model=dict)
async def import_to_ollama(
    model_id: str,
    request: ImportToOllamaRequest
):
    """
    Import model to Ollama

    This process may take several minutes for large models.
    """
    try:
        result = await ModelService.import_to_ollama(
            model_id=model_id,
            ollama_model_name=request.ollama_model_name
        )

        return {
            "success": True,
            "message": f"Model imported to Ollama as '{result['ollama_model_name']}'",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/{model_id}/activate", response_model=dict)
async def activate_model(model_id: str):
    """
    Activate a model (deactivates all others)

    The model must be imported to Ollama first.
    """
    try:
        result = await ModelService.activate_model(model_id)

        return {
            "success": True,
            "message": f"Model '{result['model_name']}' is now active",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}", response_model=dict)
async def delete_model(
    model_id: str,
    remove_from_ollama: bool = True
):
    """
    Delete a model

    Args:
        model_id: Model ID to delete
        remove_from_ollama: Also remove from Ollama (default: true)
    """
    try:
        result = await ModelService.delete_model(
            model_id=model_id,
            remove_from_ollama=remove_from_ollama
        )

        return {
            "success": True,
            "message": f"Model '{result['model_name']}' deleted successfully",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", response_model=dict)
async def get_models_stats():
    """Get summary statistics for all models"""
    try:
        all_models = await ModelService.list_models()

        stats = {
            "total_models": len(all_models),
            "by_status": {},
            "by_type": {},
            "active_model": None,
            "total_size_mb": 0,
            "average_quality": 0
        }

        # Count by status and type
        quality_ratings = []
        for model in all_models:
            # Status
            status = model.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

            # Type
            model_type = model.get('model_type', 'unknown')
            stats['by_type'][model_type] = stats['by_type'].get(model_type, 0) + 1

            # Active model
            if model.get('is_active'):
                stats['active_model'] = {
                    "model_id": str(model['model_id']),
                    "model_name": model['model_name'],
                    "display_name": model['display_name']
                }

            # Size
            if model.get('file_size_mb'):
                stats['total_size_mb'] += model['file_size_mb']

            # Quality
            if model.get('quality_rating'):
                quality_ratings.append(model['quality_rating'])

        # Average quality
        if quality_ratings:
            stats['average_quality'] = round(sum(quality_ratings) / len(quality_ratings), 2)

        stats['total_size_mb'] = round(stats['total_size_mb'], 2)

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
