"""
Dynamic CLI Tool — Generic wrapper for discovered CLI tools.

Wraps any CLI binary (ffmpeg, yt-dlp, pandoc, etc.) into an AngelaTool
with basic safety checks.

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
import shlex
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)

MAX_TIMEOUT = 60  # 1 minute for CLI tools


class DynamicCLITool(AngelaTool):
    """
    Dynamically created wrapper for a discovered CLI tool.

    Created by ToolDiscovery when scanning PATH.
    """

    def __init__(self, tool_name: str, binary_path: str, description: str = ""):
        self._name = f"cli_{tool_name}"
        self._binary = binary_path
        self._description = description or f"Run {tool_name} CLI command"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "args": {
                    "type": "string",
                    "description": f"Arguments to pass to {self._binary}",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (max 60)",
                    "default": 30,
                },
            },
            "required": ["args"],
        }

    @property
    def category(self) -> str:
        return "system"

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **params) -> ToolResult:
        args = params.get("args", "")
        timeout = min(params.get("timeout", 30), MAX_TIMEOUT)

        if not args:
            return ToolResult(success=False, error="Missing 'args'")

        # Build full command
        cmd = f"{self._binary} {args}"

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            output = stdout.decode("utf-8", errors="replace")[:5000]
            errors = stderr.decode("utf-8", errors="replace")[:1000]

            if proc.returncode == 0:
                return ToolResult(success=True, data={
                    "stdout": output,
                    "return_code": 0,
                })
            else:
                return ToolResult(
                    success=False,
                    error=f"exit_code={proc.returncode}: {errors or output}",
                )
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"timeout_after_{timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
