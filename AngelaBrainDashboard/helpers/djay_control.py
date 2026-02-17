"""AppleScript helper functions for controlling djay Pro app.

Pattern: subprocess.run + osascript (same as things3_helpers.py)
All functions are synchronous — use asyncio.to_thread() in router to avoid blocking.
"""
import subprocess
import logging

logger = logging.getLogger(__name__)


def _run_osascript(script: str, timeout: int = 15) -> tuple[bool, str]:
    """Run an AppleScript and return (success, stdout)."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        logger.warning(f"osascript failed: {result.stderr.strip()}")
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        logger.warning("osascript timed out")
        return False, "timeout"
    except Exception as e:
        logger.warning(f"osascript error: {e}")
        return False, str(e)


def is_djay_running() -> bool:
    """Check if djay Pro is currently running."""
    script = '''
    tell application "System Events"
        set isRunning to (name of processes) contains "djay Pro"
    end tell
    return isRunning as text
    '''
    ok, out = _run_osascript(script)
    return ok and out.lower() == "true"


def launch_djay() -> bool:
    """Launch djay Pro app."""
    script = '''
    tell application "djay Pro"
        activate
    end tell
    delay 2
    return "ok"
    '''
    ok, _ = _run_osascript(script, timeout=20)
    return ok


def search_and_load_song(title: str, artist: str = "", deck: int = 1) -> bool:
    """Search for a song in djay Pro's library and load it.

    Opens Library Search, types the query, waits, then presses Return to load.
    """
    query = f"{title} {artist}".strip()
    safe_query = query.replace("\\", "\\\\").replace('"', '\\"')

    script = f'''
    tell application "djay Pro"
        activate
    end tell
    delay 0.5
    tell application "System Events"
        tell process "djay Pro"
            -- Open search (Cmd+F)
            keystroke "f" using command down
            delay 0.5
            -- Clear existing search
            keystroke "a" using command down
            delay 0.2
            -- Type search query
            keystroke "{safe_query}"
            delay 1.5
            -- Press Return to load first result
            key code 36
            delay 0.5
        end tell
    end tell
    return "ok"
    '''
    ok, _ = _run_osascript(script, timeout=20)
    return ok


def play_pause_deck(deck: int = 1) -> bool:
    """Toggle play/pause on djay Pro."""
    script = '''
    tell application "djay Pro"
        activate
    end tell
    delay 0.3
    tell application "System Events"
        tell process "djay Pro"
            -- Space bar to play/pause
            key code 49
        end tell
    end tell
    return "ok"
    '''
    ok, _ = _run_osascript(script)
    return ok


def load_next_track(deck: int = 1) -> bool:
    """Load the next track in djay Pro."""
    script = '''
    tell application "djay Pro"
        activate
    end tell
    delay 0.3
    tell application "System Events"
        tell process "djay Pro"
            -- Right arrow for next track
            key code 124
        end tell
    end tell
    return "ok"
    '''
    ok, _ = _run_osascript(script)
    return ok


def toggle_automix() -> bool:
    """Toggle Automix mode in djay Pro."""
    script = '''
    tell application "djay Pro"
        activate
    end tell
    delay 0.3
    tell application "System Events"
        tell process "djay Pro"
            -- Cmd+A for automix toggle
            keystroke "a" using {command down, shift down}
        end tell
    end tell
    return "ok"
    '''
    ok, _ = _run_osascript(script)
    return ok
