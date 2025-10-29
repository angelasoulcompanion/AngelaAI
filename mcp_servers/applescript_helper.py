#!/usr/bin/env python3
"""
Shared AppleScript utilities for MCP servers
Provides safe execution of AppleScript commands
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def run_applescript(script: str, timeout: int = 10) -> str:
    """
    Execute AppleScript and return result

    Args:
        script: AppleScript code to execute
        timeout: Maximum execution time in seconds (default: 10)

    Returns:
        Script output as string

    Raises:
        Exception: If script execution fails
    """
    try:
        process = await asyncio.create_subprocess_exec(
            'osascript', '-e', script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise Exception(f"AppleScript execution timed out after {timeout}s")

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise Exception(f"AppleScript error: {error_msg}")

        result = stdout.decode().strip()
        logger.debug(f"AppleScript executed successfully: {result[:100]}")
        return result

    except Exception as e:
        logger.error(f"AppleScript execution failed: {e}")
        raise


async def check_permission(app_name: str) -> bool:
    """
    Check if we have permission to access the specified app

    Args:
        app_name: Name of macOS app (e.g., "Calendar", "Music")

    Returns:
        True if permission granted, False otherwise
    """
    script = f"""
    tell application "{app_name}"
        try
            get name
            return "granted"
        on error
            return "denied"
        end try
    end tell
    """

    try:
        result = await run_applescript(script, timeout=5)
        return result == "granted"
    except:
        return False


async def check_app_running(app_name: str) -> bool:
    """
    Check if specified app is currently running

    Args:
        app_name: Name of macOS app

    Returns:
        True if app is running
    """
    script = f"""
    tell application "System Events"
        return (name of processes) contains "{app_name}"
    end tell
    """

    try:
        result = await run_applescript(script, timeout=5)
        return result.lower() == "true"
    except:
        return False


def format_applescript_date(date_str: str) -> str:
    """
    Format Python date string to AppleScript date format

    Args:
        date_str: Date in ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)

    Returns:
        AppleScript date format string
    """
    from datetime import datetime

    try:
        # Try parsing with time
        dt = datetime.fromisoformat(date_str)
    except:
        # Try parsing date only
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except:
            raise ValueError(f"Invalid date format: {date_str}")

    # AppleScript date format: "January 1, 2025 at 2:00:00 PM"
    return dt.strftime("%B %d, %Y at %I:%M:%S %p")


def escape_applescript_string(text: str) -> str:
    """
    Escape special characters in strings for AppleScript

    Args:
        text: String to escape

    Returns:
        Escaped string safe for AppleScript
    """
    # Escape quotes and backslashes
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    return text
