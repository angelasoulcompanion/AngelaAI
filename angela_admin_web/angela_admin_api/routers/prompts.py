#
#  prompts.py
#  Angela Admin API - Prompt Management Router
#
#  Created by Angela AI on 2025-11-06.
#  API endpoints for managing and viewing optimized system prompts
#

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from angela_core.services.prompt_optimization_service import PromptOptimizationService
from angela_core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


# Request/Response Models
class GeneratePromptRequest(BaseModel):
    """Request model for generating optimized prompt"""
    context: Optional[str] = None
    include_goals: bool = True
    include_preferences: bool = True
    include_emotions: bool = True
    max_length: int = 3000  # Increased to allow full prompts


class PromptVersionResponse(BaseModel):
    """Response model for prompt version"""
    version_id: str
    version: str
    preview: str
    components: List[str]
    metadata: Dict[str, Any]
    notes: Optional[str]
    created_at: str


class ActivatePromptRequest(BaseModel):
    """Request model for activating a prompt version"""
    version_id: str
    notes: Optional[str] = None


# Endpoints

@router.get("/current")
async def get_current_prompt() -> Dict[str, Any]:
    """
    Get currently active prompt

    Returns:
        Current active prompt with full details
    """
    try:
        # Query current active prompt
        query = """
        SELECT version_id, version, prompt_text, components, metadata,
               notes, model_target, created_at, created_by
        FROM prompt_versions
        WHERE is_active = true
        ORDER BY created_at DESC
        LIMIT 1
        """

        async with db.acquire() as conn:
            row = await conn.fetchrow(query)

        if not row:
            # No active prompt - generate default one
            prompt_service = PromptOptimizationService(db)
            default_prompt = await prompt_service.generate_optimized_prompt()

            return {
                "message": "No active prompt found - generated default",
                "prompt": default_prompt,
                "is_default": True
            }

        import json

        return {
            "version_id": str(row['version_id']),
            "version": row['version'],
            "prompt_text": row['prompt_text'],
            "components": json.loads(row['components']) if row['components'] else [],
            "metadata": json.loads(row['metadata']) if row['metadata'] else {},
            "notes": row['notes'],
            "model_target": row['model_target'],
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "created_by": row['created_by'],
            "is_active": True
        }

    except Exception as e:
        logger.error(f"❌ Error getting current prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_prompt(params: GeneratePromptRequest) -> Dict[str, Any]:
    """
    Generate optimized system prompt based on current database state

    Request body:
        - context: Optional context string
        - include_goals: Include Angela's goals (default: true)
        - include_preferences: Include David's preferences (default: true)
        - include_emotions: Include emotional context (default: true)
        - max_length: Maximum prompt length (default: 2000)

    Returns:
        Generated prompt with metadata
    """
    try:
        prompt_service = PromptOptimizationService(db)

        # Generate optimized prompt
        result = await prompt_service.generate_optimized_prompt(
            context=params.context,
            include_goals=params.include_goals,
            include_preferences=params.include_preferences,
            include_emotions=params.include_emotions,
            max_length=params.max_length
        )

        logger.info(f"✅ Generated prompt: {result['length']} chars")

        return result

    except Exception as e:
        logger.error(f"❌ Error generating prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_prompt_version(prompt_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Save generated prompt as a new version

    Request body:
        - prompt: Full prompt text
        - version: Version string (e.g., "1.0.0")
        - components: List of components included
        - metadata: Dict of metadata
        - notes: Optional notes about this version

    Returns:
        version_id of saved prompt
    """
    try:
        prompt_service = PromptOptimizationService(db)

        # Save version
        version_id = await prompt_service.save_prompt_version(
            prompt_data=prompt_data,
            notes=prompt_data.get('notes')
        )

        if not version_id:
            raise HTTPException(status_code=500, detail="Failed to save prompt version")

        logger.info(f"✅ Saved prompt version: {version_id}")

        return {
            "version_id": version_id,
            "message": "Prompt version saved successfully"
        }

    except Exception as e:
        logger.error(f"❌ Error saving prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions")
async def get_prompt_versions(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent prompt versions

    Query params:
        - limit: Maximum number of versions to return (default: 10)

    Returns:
        List of prompt versions with metadata
    """
    try:
        prompt_service = PromptOptimizationService(db)

        # Get versions
        versions = await prompt_service.get_prompt_versions(limit=limit)

        logger.info(f"✅ Retrieved {len(versions)} prompt versions")

        return versions

    except Exception as e:
        logger.error(f"❌ Error getting versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activate")
async def activate_prompt_version(params: ActivatePromptRequest) -> Dict[str, str]:
    """
    Activate a specific prompt version for production use

    Request body:
        - version_id: UUID of version to activate
        - notes: Optional notes about why activating

    Returns:
        Success message
    """
    try:
        # Deactivate all prompts first
        deactivate_query = """
        UPDATE prompt_versions
        SET is_active = false
        WHERE is_active = true
        """

        # Activate selected prompt
        activate_query = """
        UPDATE prompt_versions
        SET is_active = true
        WHERE version_id = $1
        RETURNING version_id, version
        """

        async with db.acquire() as conn:
            # Deactivate all
            await conn.execute(deactivate_query)

            # Activate selected
            row = await conn.fetchrow(activate_query, params.version_id)

            if not row:
                raise HTTPException(status_code=404, detail="Prompt version not found")

        logger.info(f"✅ Activated prompt version: {params.version_id} (v{row['version']})")

        return {
            "version_id": str(row['version_id']),
            "version": row['version'],
            "message": f"Prompt version {row['version']} activated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error activating prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_prompt_stats() -> Dict[str, Any]:
    """
    Get statistics about prompt versions

    Returns:
        Stats including total versions, active version, average length, etc.
    """
    try:
        query = """
        SELECT
            COUNT(*) as total_versions,
            AVG(LENGTH(prompt_text)) as avg_length,
            MAX(LENGTH(prompt_text)) as max_length,
            MIN(LENGTH(prompt_text)) as min_length
        FROM prompt_versions
        """

        active_query = """
        SELECT version, created_at
        FROM prompt_versions
        WHERE is_active = true
        LIMIT 1
        """

        async with db.acquire() as conn:
            stats_row = await conn.fetchrow(query)
            active_row = await conn.fetchrow(active_query)

        stats = {
            "total_versions": stats_row['total_versions'] if stats_row else 0,
            "avg_length": int(stats_row['avg_length']) if stats_row and stats_row['avg_length'] else 0,
            "max_length": stats_row['max_length'] if stats_row else 0,
            "min_length": stats_row['min_length'] if stats_row else 0,
            "active_version": active_row['version'] if active_row else None,
            "active_since": active_row['created_at'].isoformat() if active_row and active_row['created_at'] else None
        }

        logger.info(f"✅ Retrieved prompt stats: {stats['total_versions']} versions")

        return stats

    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
