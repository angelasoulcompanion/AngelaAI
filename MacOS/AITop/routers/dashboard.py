"""Dashboard router — hardware stats + Ollama status."""

from fastapi import APIRouter

from services.hardware_monitor import get_hardware_stats
from services.ollama_service import check_status, list_running

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard():
    """Get full dashboard: hardware stats + Ollama status + running models."""
    hardware = get_hardware_stats()
    ollama = await check_status()
    running = await list_running()

    return {
        "hardware": hardware,
        "ollama": ollama,
        "running_models": running,
    }


@router.get("/dashboard/hardware")
async def get_hardware():
    """Hardware stats only (lighter endpoint for polling)."""
    return get_hardware_stats()
