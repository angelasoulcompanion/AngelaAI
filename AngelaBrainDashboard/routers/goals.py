"""Goals endpoints."""
from fastapi import APIRouter, Depends

from db import get_conn, get_pool

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("/active")
async def get_active_goals(conn=Depends(get_conn)):
    """Fetch active goals"""
    rows = await conn.fetch("""
        SELECT goal_id::text, goal_description, goal_type, status,
               progress_percentage, priority_rank, importance_level, created_at
        FROM angela_goals
        WHERE status IN ('active', 'in_progress')
        ORDER BY priority_rank ASC
    """)
    return [dict(r) for r in rows]
