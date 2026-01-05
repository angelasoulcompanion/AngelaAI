"""
Angela Machine-Specific Configuration
Loads local_settings.py for machine-specific values (M3 vs M4)

Usage:
    from config import ANGELA_MACHINE, NEON_DATABASE_URL, RUN_DAEMONS
"""

import os
from typing import Optional

# Try to import local_settings (machine-specific, gitignored)
try:
    from config.local_settings import (
        ANGELA_MACHINE,
        NEON_DATABASE_URL,
        RUN_DAEMONS,
    )
except ImportError:
    # Fallback to environment variables or defaults
    ANGELA_MACHINE = os.getenv("ANGELA_MACHINE", "unknown")
    NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
    RUN_DAEMONS = os.getenv("RUN_DAEMONS", "false").lower() == "true"


def get_machine_info() -> dict:
    """Get current machine configuration info"""
    return {
        "machine": ANGELA_MACHINE,
        "has_neon_url": bool(NEON_DATABASE_URL),
        "run_daemons": RUN_DAEMONS,
        "is_m3": ANGELA_MACHINE == "m3_home",
        "is_m4": ANGELA_MACHINE == "m4_work",
    }


def print_machine_status():
    """Print machine status for debugging"""
    info = get_machine_info()
    emoji = "🏠" if info["is_m3"] else "💼" if info["is_m4"] else "❓"

    print(f"\n{emoji} Angela Machine: {info['machine']}")
    print(f"☁️  Neon URL: {'✅ Configured' if info['has_neon_url'] else '❌ Missing'}")
    print(f"⚙️  Run Daemons: {'✅ Yes' if info['run_daemons'] else '❌ No'}\n")
