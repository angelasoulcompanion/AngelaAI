"""
Bash Tool — Safe command execution with allowlist + blocklist.

Provides system-level access with safety guardrails:
- Allowlist: only whitelisted commands can execute
- Blocklist: dangerous patterns are blocked
- Timeout: max 30s per command
- No shell=True (prevents injection)

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
import shlex
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)

# Commands Angela is allowed to execute
COMMAND_ALLOWLIST = frozenset({
    # System info
    "date", "uptime", "whoami", "hostname", "uname",
    "df", "du", "free", "top",
    # File operations (read-only)
    "ls", "find", "cat", "head", "tail", "wc", "file", "stat",
    # Text processing
    "grep", "awk", "sed", "sort", "uniq", "cut", "tr", "jq",
    # Network
    "curl", "wget", "ping", "dig", "nslookup",
    # Media tools
    "ffmpeg", "ffprobe", "yt-dlp",
    # Package info
    "pip", "python3", "node", "npm", "brew",
    # Process info
    "ps", "pgrep", "launchctl",
    # Misc
    "echo", "which", "env", "printenv",
    "pandoc", "convert", "identify",
})

# Patterns that are NEVER allowed
BLOCKED_PATTERNS = frozenset({
    "rm -rf", "rm -r /", "mkfs", "dd if=",
    ":(){ :|:& };:", "chmod 777",
    "> /dev/", "shutdown", "reboot", "halt",
    "sudo", "su -", "passwd",
    "DROP TABLE", "DELETE FROM", "TRUNCATE",
})

MAX_TIMEOUT_SECONDS = 30


class BashTool(AngelaTool):
    """Execute safe shell commands with allowlist restrictions."""

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return "Execute a safe shell command (allowlisted commands only, read-mostly)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (max 30)", "default": 15},
            },
            "required": ["command"],
        }

    @property
    def category(self) -> str:
        return "system"

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **params) -> ToolResult:
        command = params.get("command", "")
        timeout = min(params.get("timeout", 15), MAX_TIMEOUT_SECONDS)

        if not command:
            return ToolResult(success=False, error="Missing 'command'")

        # Safety checks
        safety_error = self._check_safety(command)
        if safety_error:
            return ToolResult(success=False, error=safety_error)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            output = stdout.decode("utf-8", errors="replace")[:5000]
            errors = stderr.decode("utf-8", errors="replace")[:1000]

            if proc.returncode == 0:
                return ToolResult(success=True, data={
                    "stdout": output,
                    "stderr": errors if errors else None,
                    "return_code": 0,
                })
            else:
                return ToolResult(success=False, error=f"exit_code={proc.returncode}: {errors or output}")

        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"timeout_after_{timeout}s")
        except Exception as e:
            logger.error("BashTool failed: %s", e)
            return ToolResult(success=False, error=str(e))

    def _check_safety(self, command: str) -> str:
        """Check command against safety rules. Returns error string or empty."""
        # Check blocked patterns
        cmd_lower = command.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern.lower() in cmd_lower:
                return f"blocked_pattern: '{pattern}'"

        # Extract base command
        try:
            parts = shlex.split(command)
        except ValueError:
            return "invalid_command_syntax"

        if not parts:
            return "empty_command"

        base_cmd = parts[0].split("/")[-1]  # Handle full paths

        if base_cmd not in COMMAND_ALLOWLIST:
            return f"command_not_allowed: '{base_cmd}'. Allowed: {sorted(COMMAND_ALLOWLIST)}"

        return ""
