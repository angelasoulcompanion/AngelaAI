"""
Hardware Monitor — macOS CPU/GPU/RAM/SSD/Neural Engine metrics.
Apple Silicon native: GPU via ioreg IOAccelerator, CPU via psutil, ANE via ioreg.
"""

import subprocess
import json
import time
from typing import Optional

import psutil

from services.apple_silicon_monitor import get_gpu_ane_usage


# Cache chip info (doesn't change)
_chip_info: Optional[dict] = None
_chip_info_ts: float = 0


def _get_chip_info() -> dict:
    """Get Apple Silicon chip info (cached permanently)."""
    global _chip_info, _chip_info_ts
    if _chip_info and (time.time() - _chip_info_ts) < 3600:
        return _chip_info

    try:
        result = subprocess.run(
            ["system_profiler", "SPHardwareDataType", "-json"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        hw = data.get("SPHardwareDataType", [{}])[0]
        _chip_info = {
            "chip_name": hw.get("chip_type", "Unknown"),
            "model_name": hw.get("machine_model", "Mac"),
            "cpu_cores": psutil.cpu_count(logical=False),
            "memory_gb": int(hw.get("physical_memory", "0 GB").split()[0]) if "physical_memory" in hw else 0,
        }
    except Exception:
        _chip_info = {
            "chip_name": "Apple Silicon",
            "model_name": "Mac",
            "cpu_cores": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3)),
        }
    _chip_info_ts = time.time()
    return _chip_info


def _get_thermal_pressure() -> str:
    """Get macOS thermal pressure level."""
    try:
        result = subprocess.run(
            ["pmset", "-g", "therm"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.lower()
        if "nominal" in output:
            return "nominal"
        elif "moderate" in output or "fair" in output:
            return "moderate"
        elif "serious" in output or "heavy" in output:
            return "heavy"
        elif "critical" in output:
            return "critical"
    except Exception:
        pass
    return "unknown"


def _get_disk_info() -> dict:
    """Get primary disk usage."""
    disk = psutil.disk_usage("/")
    return {
        "total_gb": round(disk.total / (1024**3), 1),
        "used_gb": round(disk.used / (1024**3), 1),
        "free_gb": round(disk.free / (1024**3), 1),
        "percent": disk.percent,
    }


def _get_neural_engine_info(ane_data: dict) -> dict:
    """Neural Engine info from ioreg + chip detection."""
    chip = _get_chip_info()
    chip_name = chip.get("chip_name", "").lower()

    ne_cores = 0
    if "m1" in chip_name:
        ne_cores = 16
    elif "m2" in chip_name:
        ne_cores = 16
    elif "m3" in chip_name:
        ne_cores = 16
    elif "m4" in chip_name:
        ne_cores = 16

    return {
        "cores": ne_cores,
        "available": ne_cores > 0,
        "usage_percent": -1,
        "power_mw": ane_data.get("ane_power_mw", 0),
        "active": ane_data.get("ane_active", False),
    }


def get_hardware_stats() -> dict:
    """Aggregate all hardware stats into a single dashboard response."""
    chip = _get_chip_info()
    mem = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.5)
    gpu_ane = get_gpu_ane_usage()
    disk = _get_disk_info()
    ne = _get_neural_engine_info(gpu_ane)
    thermal = _get_thermal_pressure()

    return {
        "chip": chip,
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "freq_mhz": round(psutil.cpu_freq().current) if psutil.cpu_freq() else 0,
        },
        "gpu": {
            "percent": gpu_ane.get("gpu_percent", 0),
            "renderer_percent": gpu_ane.get("renderer_percent", 0),
            "tiler_percent": gpu_ane.get("tiler_percent", 0),
            "vram_used_mb": round(gpu_ane.get("vram_used_bytes", 0) / (1024**2)),
            "vram_alloc_mb": round(gpu_ane.get("vram_alloc_bytes", 0) / (1024**2)),
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
            "percent": mem.percent,
        },
        "disk": disk,
        "neural_engine": ne,
        "thermal_pressure": thermal,
    }
