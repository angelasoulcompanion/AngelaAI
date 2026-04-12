"""
Apple Silicon GPU & Neural Engine Monitor.
GPU: reads 'Device Utilization %' from ioreg IOAccelerator (no sudo needed).
ANE: reads power-gates from ioreg ane device + detects CoreML processes.
"""

import re
import subprocess
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
    except Exception:
        return {
            "gpu_percent": -1,
            "renderer_percent": -1,
            "tiler_percent": -1,
            "vram_used_bytes": 0,
            "vram_alloc_bytes": 0,
        }


def get_ane_status() -> dict:
    """
    Get Neural Engine status from ioreg power-gates + CoreML process detection.
    macOS does not expose ANE utilization % without sudo/powermetrics.
    We use two heuristics:
    1. power-gates bytes from ioreg ane device (non-zero = powered on)
    2. Check for coremlcompiler/ANECompilerService processes
    """
    ane_active = False
    power_gate_value = 0

    # Method 1: Check power-gates from ioreg
    try:
        result = subprocess.run(
            ["ioreg", "-r", "-n", "ane", "-d", "1", "-w", "0"],
            capture_output=True, text=True, timeout=3
        )
        if "power-gates" in result.stdout:
            # Parse power-gates = <b4000000a4010000>
            match = re.search(r'"power-gates"\s*=\s*<([0-9a-f]+)>', result.stdout)
            if match:
                hex_str = match.group(1)
                power_gate_value = int(hex_str, 16)
                ane_active = power_gate_value > 0
    except Exception:
        pass

    # Method 2: Check if CoreML/ANE processes are running
    try:
        result = subprocess.run(
            ["pgrep", "-fl", "coreml|ANECompiler|espresso|aned"],
            capture_output=True, text=True, timeout=3
        )
        if result.stdout.strip():
            ane_active = True
    except Exception:
        pass

    return {
        "ane_active": ane_active,
        "ane_power_mw": 0,  # Not available without sudo
    }


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
    ane = get_ane_status()
    return {
        "gpu_percent": gpu["gpu_percent"],
        "renderer_percent": gpu["renderer_percent"],
        "tiler_percent": gpu["tiler_percent"],
        "vram_used_bytes": gpu["vram_used_bytes"],
        "vram_alloc_bytes": gpu["vram_alloc_bytes"],
        "ane_power_mw": ane["ane_power_mw"],
        "ane_active": ane["ane_active"],
    }
