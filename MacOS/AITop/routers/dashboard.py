"""Dashboard router — hardware stats + Ollama status."""

import logging
import subprocess
import time
import traceback

import psutil
from fastapi import APIRouter, HTTPException

from services.hardware_monitor import get_hardware_stats
from services.ollama_service import check_status, list_running

router = APIRouter(tags=["dashboard"])
logger = logging.getLogger(__name__)


def _get_top_processes(limit: int = 8) -> list[dict]:
    """Top processes by memory usage."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            info = p.info
            if info["memory_percent"] and info["memory_percent"] > 0.1:
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"] or "—",
                    "memory_percent": round(info["memory_percent"], 1),
                    "cpu_percent": round(info["cpu_percent"] or 0, 1),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x["memory_percent"], reverse=True)
    return procs[:limit]


def _get_network_info() -> dict:
    """Network interfaces and IO counters."""
    counters = psutil.net_io_counters()
    # Active interface IP
    addrs = psutil.net_if_addrs()
    active_ip = "—"
    for iface, addr_list in addrs.items():
        if iface in ("lo0", "lo"):
            continue
        for addr in addr_list:
            if addr.family.name == "AF_INET" and not addr.address.startswith("127."):
                active_ip = addr.address
                break
        if active_ip != "—":
            break

    return {
        "ip": active_ip,
        "bytes_sent_gb": round(counters.bytes_sent / (1024**3), 2),
        "bytes_recv_gb": round(counters.bytes_recv / (1024**3), 2),
    }


def _get_battery_info() -> dict | None:
    """Battery info (None if desktop)."""
    bat = psutil.sensors_battery()
    if not bat:
        return None
    return {
        "percent": round(bat.percent, 1),
        "plugged": bat.power_plugged,
        "secs_left": bat.secsleft if bat.secsleft > 0 else None,
    }


def _get_uptime() -> dict:
    """System uptime."""
    boot_time = psutil.boot_time()
    uptime_secs = int(time.time() - boot_time)
    days = uptime_secs // 86400
    hours = (uptime_secs % 86400) // 3600
    mins = (uptime_secs % 3600) // 60
    if days > 0:
        label = f"{days}d {hours}h {mins}m"
    elif hours > 0:
        label = f"{hours}h {mins}m"
    else:
        label = f"{mins}m"
    return {"seconds": uptime_secs, "label": label}


def _get_per_core_cpu() -> list[float]:
    """Per-core CPU usage (non-blocking, uses cached)."""
    return psutil.cpu_percent(percpu=True)


@router.get("/dashboard")
async def get_dashboard():
    """Get full dashboard: hardware stats + Ollama status + running models + extras."""
    try:
        hardware = get_hardware_stats()
        ollama = await check_status()
        running = await list_running()

        return {
            "hardware": hardware,
            "ollama": ollama,
            "running_models": running,
            "top_processes": _get_top_processes(),
            "network": _get_network_info(),
            "battery": _get_battery_info(),
            "uptime": _get_uptime(),
            "per_core_cpu": _get_per_core_cpu(),
        }
    except Exception as e:
        logger.error(f"Dashboard error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/hardware")
async def get_hardware():
    """Hardware stats only (lighter endpoint for polling)."""
    try:
        return get_hardware_stats()
    except Exception as e:
        logger.error(f"Hardware stats error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
