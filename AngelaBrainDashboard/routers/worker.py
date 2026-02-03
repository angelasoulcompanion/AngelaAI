"""Background worker metrics endpoint."""
from fastapi import APIRouter, Depends

from db import get_conn, get_pool

router = APIRouter(prefix="/api/worker", tags=["worker"])


@router.get("/metrics")
async def get_background_worker_metrics(conn=Depends(get_conn)):
    """Fetch background worker metrics"""
    row = await conn.fetchrow("""
        SELECT
            tasks_completed,
            queue_size,
            workers_active,
            total_workers,
            avg_processing_ms,
            success_rate,
            tasks_dropped,
            worker_1_utilization,
            worker_2_utilization,
            worker_3_utilization,
            worker_4_utilization,
            recorded_at
        FROM background_worker_metrics
        ORDER BY recorded_at DESC
        LIMIT 1
    """)
    if row:
        return dict(row)
    return None
