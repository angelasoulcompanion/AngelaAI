"""
Apple Silicon GPU & Neural Engine Monitor.
GPU: reads 'Device Utilization %' from ioreg IOAccelerator (no sudo needed).
ANE: reads from ioreg AppleARMIODevice (best effort).
"""

import re
import subprocess
import time
from typing import Optional


def get_gpu_usage() -> dict:
    """
    Get GPU usage from ioreg IOAccelerator → PerformanceStatistics.
    Returns Device Utilization %, Renderer Utilization %, Tiler Utilization %.
    """
    try:
        result = subprocess.run(
            ["ioreg", "-r", "-d", "1", "-w", "0", "-c", "IOAccelerator"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout

        # Parse PerformanceStatistics dict
        device_util = _extract_value(output, "Device Utilization %")
        renderer_util = _extract_value(output, "Renderer Utilization %")
        tiler_util = _extract_value(output, "Tiler Utilization %")
        in_use_mem = _extract_value(output, "In use system memory")
        alloc_mem = _extract_value(output, "Alloc system memory")

        return {
            "gpu_percent": device_util if device_util >= 0 else 0.0,
            "renderer_percent": renderer_util,
            "tiler_percent": tiler_util,
            "vram_used_bytes": in_use_mem if in_use_mem >= 0 else 0,
            "vram_alloc_bytes": alloc_mem if alloc_mem >= 0 else 0,
        }
    except Exception as e:
        return {
            "gpu_percent": -1,
            "renderer_percent": -1,
            "tiler_percent": -1,
            "vram_used_bytes": 0,
            "vram_alloc_bytes": 0,
        }


def get_ane_power() -> dict:
    """
    Get Neural Engine power consumption (mW) from ioreg.
    ANE usage % is not directly available, but power gives an indication.
    """
    try:
        result = subprocess.run(
            ["ioreg", "-r", "-d", "1", "-w", "0", "-n", "ane0"],
            capture_output=True, text=True, timeout=5
        )
        if "ane-power" in result.stdout:
            power = _extract_value(result.stdout, "ane-power")
            return {"ane_power_mw": power, "ane_active": power > 0}
    except Exception:
        pass
    return {"ane_power_mw": 0, "ane_active": False}


def _extract_value(text: str, key: str) -> int:
    """Extract integer value for a given key from ioreg output."""
    pattern = rf'"{re.escape(key)}"=(\d+)'
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))
    return -1


def get_gpu_ane_usage() -> dict:
    """Combined GPU + ANE usage for dashboard."""
    gpu = get_gpu_usage()
    ane = get_ane_power()
    return {
        "gpu_percent": gpu["gpu_percent"],
        "renderer_percent": gpu["renderer_percent"],
        "tiler_percent": gpu["tiler_percent"],
        "vram_used_bytes": gpu["vram_used_bytes"],
        "vram_alloc_bytes": gpu["vram_alloc_bytes"],
        "ane_power_mw": ane["ane_power_mw"],
        "ane_active": ane["ane_active"],
    }
