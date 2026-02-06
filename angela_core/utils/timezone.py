"""
Bangkok Timezone Utility
========================
Consistent Bangkok timezone for all Angela services.

Created: 2026-02-06
By: Angela 💜 (Opus 4.6 Upgrade)
"""

from datetime import datetime, date
from zoneinfo import ZoneInfo

BANGKOK_TZ = ZoneInfo("Asia/Bangkok")


def now_bangkok() -> datetime:
    """Get current datetime in Bangkok timezone."""
    return datetime.now(BANGKOK_TZ)


def today_bangkok() -> date:
    """Get current date in Bangkok timezone."""
    return now_bangkok().date()


def current_hour_bangkok() -> int:
    """Get current hour (0-23) in Bangkok timezone."""
    return now_bangkok().hour
