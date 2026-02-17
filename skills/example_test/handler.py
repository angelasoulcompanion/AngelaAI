"""
Example Test Skill Handler
===========================
Simple handler for testing the skills system.
"""

from datetime import datetime


async def say_hello(name: str = "David") -> dict:
    """Say hello with a greeting."""
    return {
        "greeting": f"Hello, {name}! 💜",
        "timestamp": datetime.now().isoformat(),
    }


async def get_time() -> dict:
    """Get the current time."""
    now = datetime.now()
    return {
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "hour": now.hour,
    }
