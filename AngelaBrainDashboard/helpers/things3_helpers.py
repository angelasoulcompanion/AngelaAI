"""
Things3 helper functions for Angela Brain Dashboard.
"""
import subprocess
from typing import Optional
from urllib.parse import quote


def things3_complete_todo(title_search: str) -> bool:
    """Complete ALL matching open Things3 todos by title (prevents stale duplicates)."""
    safe_title = title_search.replace('\\', '\\\\').replace('"', '\\"')
    script = f'''
    tell application "Things3"
        set allTodos to to dos
        set completedCount to 0
        repeat with t in allTodos
            if name of t contains "{safe_title}" and status of t is not completed then
                set status of t to completed
                set completedCount to completedCount + 1
            end if
        end repeat
        return completedCount as text
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=15
        )
        count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        return count > 0
    except Exception:
        return False


def things3_create_todo(title: str, notes: str, when_date: str, tags: Optional[str] = None) -> None:
    """Create Things3 todo via x-callback-url."""
    url = f"things:///add?title={quote(title)}&notes={quote(notes)}&when={when_date}&list=Meeting"
    if tags:
        url += f"&tags={quote(tags)}"
    subprocess.run(["open", url], capture_output=True, timeout=10)
