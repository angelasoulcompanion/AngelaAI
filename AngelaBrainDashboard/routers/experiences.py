"""Shared experiences endpoints — tables removed, return empty."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/experiences", tags=["experiences"])


@router.get("/shared")
async def get_shared_experiences(limit: int = Query(50, ge=1, le=200), conn=Depends(get_conn)):
    """No shared_experiences table — return empty."""
    return []


@router.get("/images/{experience_id}")
async def get_experience_images(experience_id: str, conn=Depends(get_conn)):
    """No shared_experience_images table — return empty."""
    return []
