"""Background worker metrics endpoint — table removed."""
from fastapi import APIRouter, Depends

from db import get_conn, get_pool

router = APIRouter(prefix="/api/worker", tags=["worker"])


@router.get("/metrics")
async def get_background_worker_metrics(conn=Depends(get_conn)):
    """No background_worker_metrics table — return None."""
    return None
