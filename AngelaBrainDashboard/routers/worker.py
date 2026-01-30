"""Background worker metrics endpoint."""
from fastapi import APIRouter

from db import get_pool

router = APIRouter(prefix="/api/worker", tags=["worker"])


@router.get("/metrics")
async def get_background_worker_metrics():
    """Fetch background worker metrics"""
    pool = get_pool()
    async with pool.acquire() as conn:
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
