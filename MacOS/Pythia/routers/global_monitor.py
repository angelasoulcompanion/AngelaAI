"""
Pythia — Global Monitor Router
GET /api/global-monitor → command-center payload with 15 world indices
"""
from fastapi import APIRouter

from services.global_monitor_service import fetch_global_monitor

router = APIRouter(prefix="/api/global-monitor", tags=["global_monitor"])


@router.get("/")
async def get_global_monitor():
    """Fetch global market monitor data (15 indices, market status, heatmap)."""
    return fetch_global_monitor()
