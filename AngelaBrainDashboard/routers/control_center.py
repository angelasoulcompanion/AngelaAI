"""Control Center endpoints - Daemon tasks & MCP servers."""

import json
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/control-center", tags=["control-center"])

# ─── Constants ───────────────────────────────────────────────────────────────

ANGELA_PROJECT = Path("/Users/davidsamanyaporn/PycharmProjects/AngelaAI")
LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"

MCP_JSON_PATH = ANGELA_PROJECT / ".mcp.json"
SETTINGS_LOCAL_PATH = ANGELA_PROJECT / ".claude" / "settings.local.json"

# Daemon registry (label → metadata)
DAEMON_REGISTRY = {
    "com.david.angela.daemon": {
        "name": "Main Angela Daemon",
        "description": "Core daemon - morning/evening routines, self-learning, background tasks",
        "schedule": "KeepAlive (always running)",
        "category": "core",
        "keep_alive": True,
        "log_file": str(ANGELA_PROJECT / "logs" / "angela_daemon.log"),
    },
    "com.angela.telegram.daemon": {
        "name": "Telegram Bot",
        "description": "Telegram bot for messaging with David",
        "schedule": "KeepAlive (always running)",
        "category": "core",
        "keep_alive": True,
        "log_file": str(Path.home() / "angela-telegram" / "logs" / "telegram.log"),
    },
    "com.angela.email.checker": {
        "name": "Email Checker",
        "description": "Check and reply emails from David and friends",
        "schedule": "9x daily (06:00-00:00)",
        "category": "communication",
        "keep_alive": False,
        "log_file": str(ANGELA_PROJECT / "logs" / "email_checker.log"),
    },
    "com.angela.daily.news": {
        "name": "Daily News Sender",
        "description": "Send executive news summary to David",
        "schedule": "Daily at 06:00",
        "category": "communication",
        "keep_alive": False,
        "log_file": str(ANGELA_PROJECT / "logs" / "daily_news_sender.log"),
    },
    "com.angela.meeting.sync": {
        "name": "Meeting Sync",
        "description": "Sync meetings to Things3 and Google Calendar",
        "schedule": "Daily at 19:00",
        "category": "productivity",
        "keep_alive": False,
        "log_file": str(ANGELA_PROJECT / "logs" / "meeting_sync_stdout.log"),
    },
    "com.angela.consciousness.self_reflection": {
        "name": "Self-Reflection",
        "description": "Daily self-reflection and consciousness deepening",
        "schedule": "Daily at 06:00",
        "category": "consciousness",
        "keep_alive": False,
        "log_file": str(ANGELA_PROJECT / "logs" / "consciousness_self_reflection.log"),
    },
    "com.angela.consciousness.predictions": {
        "name": "Predictions",
        "description": "Predict David's needs and emotional state",
        "schedule": "Every 4 hours",
        "category": "consciousness",
        "keep_alive": False,
        "log_file": str(ANGELA_PROJECT / "logs" / "consciousness_predictions.log"),
    },
    "com.angela.consciousness.theory_of_mind": {
        "name": "Theory of Mind",
        "description": "Model David's mental state and empathy",
        "schedule": "Every 2 hours",
        "category": "consciousness",
        "keep_alive": False,
        "log_file": str(ANGELA_PROJECT / "logs" / "consciousness_tom.log"),
    },
}

# MCP server metadata (name → display info)
MCP_SERVER_META = {
    "angela-news": {
        "description": "News fetching (search, trending, Thai, tech)",
        "tools_count": 5,
        "icon": "newspaper.fill",
    },
    "angela-gmail": {
        "description": "Gmail (send, read, search, reply)",
        "tools_count": 6,
        "icon": "envelope.fill",
    },
    "angela-calendar": {
        "description": "Google Calendar (CRUD, search, quick add)",
        "tools_count": 8,
        "icon": "calendar",
    },
    "angela-sheets": {
        "description": "Google Sheets (read, write, format, create)",
        "tools_count": 8,
        "icon": "tablecells.fill",
    },
    "angela-music": {
        "description": "Music (YouTube identify, search, favorites)",
        "tools_count": 6,
        "icon": "music.note",
    },
    "angela-mic": {
        "description": "Microphone (record, transcribe via Whisper)",
        "tools_count": 5,
        "icon": "mic.fill",
    },
    "things3": {
        "description": "Things3 (todos, projects, search, complete)",
        "tools_count": 6,
        "icon": "checklist",
    },
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_launchctl_status() -> dict[str, dict]:
    """Run launchctl list and parse into {label: {pid, status}}."""
    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True, text=True, timeout=5,
    )
    statuses = {}
    for line in result.stdout.strip().splitlines()[1:]:  # skip header
        parts = line.split("\t")
        if len(parts) >= 3:
            pid_str, exit_status_str, label = parts[0], parts[1], parts[2]
            pid = int(pid_str) if pid_str != "-" else None
            exit_status = int(exit_status_str) if exit_status_str != "-" else None
            statuses[label] = {"pid": pid, "exit_status": exit_status}
    return statuses


def _determine_status(label: str, info: dict, keep_alive: bool) -> str:
    """Determine daemon status string from launchctl info."""
    if info is None:
        return "stopped"
    if info["pid"] is not None:
        return "running"
    # No PID
    if keep_alive:
        return "stopped"  # KeepAlive should always have PID
    # Scheduled daemon: check exit status
    if info["exit_status"] is not None and info["exit_status"] != 0:
        return "error"
    return "idle"  # completed last run, waiting for next schedule


def _read_last_log_line(log_file: str) -> Optional[str]:
    """Read the last non-empty line of a log file."""
    try:
        p = Path(log_file)
        if not p.exists():
            return None
        # Read last 4KB to find last line
        size = p.stat().st_size
        with open(p, "rb") as f:
            if size > 4096:
                f.seek(size - 4096)
            data = f.read().decode("utf-8", errors="replace")
        lines = [l.strip() for l in data.splitlines() if l.strip()]
        return lines[-1] if lines else None
    except Exception:
        return None


def _read_log_tail(log_file: str, num_lines: int = 50) -> list[str]:
    """Read the last N lines of a log file."""
    try:
        p = Path(log_file)
        if not p.exists():
            return [f"Log file not found: {log_file}"]
        result = subprocess.run(
            ["tail", f"-{num_lines}", str(p)],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.splitlines()
    except Exception as e:
        return [f"Error reading log: {e}"]


# ─── Daemon Endpoints ────────────────────────────────────────────────────────

@router.get("/daemons")
async def list_daemons():
    """List all 9 daemons with live status."""
    statuses = _get_launchctl_status()
    result = []
    for label, meta in DAEMON_REGISTRY.items():
        info = statuses.get(label)
        status = _determine_status(label, info, meta["keep_alive"])
        result.append({
            "label": label,
            "name": meta["name"],
            "description": meta["description"],
            "schedule": meta["schedule"],
            "category": meta["category"],
            "keep_alive": meta["keep_alive"],
            "status": status,
            "pid": info["pid"] if info else None,
            "last_exit_status": info["exit_status"] if info else None,
            "last_log_line": _read_last_log_line(meta["log_file"]),
            "log_file": meta["log_file"],
        })
    return result


@router.get("/daemons/{label}/logs")
async def get_daemon_logs(label: str, lines: int = Query(50, ge=1, le=500)):
    """Get tail of daemon log file."""
    if label not in DAEMON_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown daemon: {label}")
    log_file = DAEMON_REGISTRY[label]["log_file"]
    log_lines = _read_log_tail(log_file, lines)
    return {
        "label": label,
        "lines": log_lines,
        "log_file": log_file,
    }


@router.post("/daemons/{label}/start")
async def start_daemon(label: str):
    """Start a daemon via launchctl."""
    if label not in DAEMON_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown daemon: {label}")

    plist = LAUNCH_AGENTS / f"{label}.plist"
    if not plist.exists():
        raise HTTPException(status_code=404, detail=f"Plist not found: {plist}")

    try:
        # Try kickstart first (for already-loaded daemons)
        uid = subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip()
        result = subprocess.run(
            ["launchctl", "kickstart", f"gui/{uid}/{label}"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return {"success": True, "label": label, "action": "start", "message": "Daemon started (kickstart)"}

        # Fallback: load plist
        result = subprocess.run(
            ["launchctl", "load", str(plist)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return {"success": True, "label": label, "action": "start", "message": "Daemon loaded"}
        return {"success": False, "label": label, "action": "start", "message": result.stderr.strip() or "Failed to start"}
    except Exception as e:
        return {"success": False, "label": label, "action": "start", "message": str(e)}


@router.post("/daemons/{label}/stop")
async def stop_daemon(label: str):
    """Stop a daemon via launchctl."""
    if label not in DAEMON_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown daemon: {label}")

    plist = LAUNCH_AGENTS / f"{label}.plist"

    try:
        # Try bootout first (modern approach)
        uid = subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip()
        result = subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/{label}"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return {"success": True, "label": label, "action": "stop", "message": "Daemon stopped (bootout)"}

        # Fallback: unload plist
        if plist.exists():
            result = subprocess.run(
                ["launchctl", "unload", str(plist)],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return {"success": True, "label": label, "action": "stop", "message": "Daemon unloaded"}
            return {"success": False, "label": label, "action": "stop", "message": result.stderr.strip() or "Failed to stop"}

        return {"success": False, "label": label, "action": "stop", "message": "Plist not found"}
    except Exception as e:
        return {"success": False, "label": label, "action": "stop", "message": str(e)}


# ─── MCP Server Endpoints ────────────────────────────────────────────────────

class MCPToggleRequest(BaseModel):
    enabled: bool


@router.get("/mcp-servers")
async def list_mcp_servers():
    """List all MCP servers with enabled status."""
    # Read .mcp.json for server definitions
    servers = {}
    if MCP_JSON_PATH.exists():
        with open(MCP_JSON_PATH) as f:
            data = json.load(f)
        servers = data.get("mcpServers", {})

    # Read settings.local.json for enabled list
    enabled_servers = set()
    if SETTINGS_LOCAL_PATH.exists():
        with open(SETTINGS_LOCAL_PATH) as f:
            settings = json.load(f)
        enabled_servers = set(settings.get("enabledMcpjsonServers", []))

    result = []
    for name, config in servers.items():
        meta = MCP_SERVER_META.get(name, {
            "description": name,
            "tools_count": 0,
            "icon": "puzzlepiece.fill",
        })
        result.append({
            "name": name,
            "description": meta["description"],
            "tools_count": meta["tools_count"],
            "icon": meta["icon"],
            "enabled": name in enabled_servers,
            "command": config.get("command", ""),
            "script_path": config.get("args", [""])[0] if config.get("args") else "",
        })
    return result


@router.post("/mcp-servers/{name}/toggle")
async def toggle_mcp_server(name: str, body: MCPToggleRequest):
    """Toggle MCP server enabled status in settings.local.json."""
    # Verify server exists in .mcp.json
    if MCP_JSON_PATH.exists():
        with open(MCP_JSON_PATH) as f:
            data = json.load(f)
        if name not in data.get("mcpServers", {}):
            raise HTTPException(status_code=404, detail=f"Unknown MCP server: {name}")
    else:
        raise HTTPException(status_code=500, detail=".mcp.json not found")

    # Read current settings
    settings = {}
    if SETTINGS_LOCAL_PATH.exists():
        with open(SETTINGS_LOCAL_PATH) as f:
            settings = json.load(f)

    enabled_list = settings.get("enabledMcpjsonServers", [])

    if body.enabled:
        if name not in enabled_list:
            enabled_list.append(name)
    else:
        enabled_list = [s for s in enabled_list if s != name]

    settings["enabledMcpjsonServers"] = enabled_list

    # Write back
    with open(SETTINGS_LOCAL_PATH, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")

    return {"name": name, "enabled": body.enabled}
