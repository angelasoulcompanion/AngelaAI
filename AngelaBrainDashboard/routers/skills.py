"""Skills endpoints — angela_skills + skill_growth_log removed, return empty."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/all")
async def get_all_skills(conn=Depends(get_conn)):
    return []


@router.get("/by-category")
async def get_skills_by_category(conn=Depends(get_conn)):
    return {}


@router.get("/statistics")
async def get_skill_statistics(conn=Depends(get_conn)):
    return {
        "total_skills": 0, "expert_count": 0, "advanced_count": 0,
        "intermediate_count": 0, "beginner_count": 0,
        "avg_score": 0.0, "total_evidence": 0, "total_usage": 0,
    }


@router.get("/growth")
async def get_recent_skill_growth(days: int = Query(7, ge=1, le=30), conn=Depends(get_conn)):
    return []
