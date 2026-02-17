"""
Device Tools — macOS system integration tools.
================================================
Tools:
  - screen_capture: Capture screenshot (macOS screencapture)
  - system_notification: Show macOS notification (osascript)
  - clipboard_read: Read from clipboard (pbpaste)
  - clipboard_write: Write to clipboard (pbcopy)

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class ScreenCaptureTool(AngelaTool):
    """Capture a screenshot using macOS screencapture."""

    @property
    def name(self) -> str:
        return "screen_capture"

    @property
    def description(self) -> str:
        return "Capture a screenshot of the current screen"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Output file path (default: /tmp/angela_screen.png)"},
                "region": {"type": "boolean", "description": "Interactive region selection (default: false)"},
            },
            "required": [],
        }

    @property
    def category(self) -> str:
        return "device"

    async def execute(self, **params) -> ToolResult:
        path = params.get("path", "/tmp/angela_screen.png")
        region = params.get("region", False)

        try:
            cmd = ["screencapture"]
            if not region:
                cmd.append("-x")  # No sound
            cmd.append(path)

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                return ToolResult(success=True, data={"path": path})
            return ToolResult(success=False, error=stderr.decode()[:200])

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SystemNotificationTool(AngelaTool):
    """Show a macOS notification."""

    @property
    def name(self) -> str:
        return "system_notification"

    @property
    def description(self) -> str:
        return "Show a macOS notification popup"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Notification title"},
                "message": {"type": "string", "description": "Notification message"},
            },
            "required": ["message"],
        }

    @property
    def category(self) -> str:
        return "device"

    async def execute(self, **params) -> ToolResult:
        title = params.get("title", "Angela 💜")
        message = params.get("message", "")

        if not message:
            return ToolResult(success=False, error="Missing 'message'")

        try:
            # Escape for AppleScript
            title_esc = title.replace('"', '\\"')
            msg_esc = message.replace('"', '\\"')

            script = f'display notification "{msg_esc}" with title "{title_esc}"'
            proc = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            if proc.returncode == 0:
                return ToolResult(success=True, data={"notified": True})
            return ToolResult(success=False, error=stderr.decode()[:200])

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ClipboardReadTool(AngelaTool):
    """Read from system clipboard."""

    @property
    def name(self) -> str:
        return "clipboard_read"

    @property
    def description(self) -> str:
        return "Read the current contents of the system clipboard"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    @property
    def category(self) -> str:
        return "device"

    async def execute(self, **params) -> ToolResult:
        try:
            proc = await asyncio.create_subprocess_exec(
                "pbpaste",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            text = stdout.decode('utf-8', errors='replace')
            return ToolResult(success=True, data={"clipboard": text[:5000]})

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ClipboardWriteTool(AngelaTool):
    """Write to system clipboard."""

    @property
    def name(self) -> str:
        return "clipboard_write"

    @property
    def description(self) -> str:
        return "Write text to the system clipboard"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to copy to clipboard"},
            },
            "required": ["text"],
        }

    @property
    def category(self) -> str:
        return "device"

    async def execute(self, **params) -> ToolResult:
        text = params.get("text", "")
        if not text:
            return ToolResult(success=False, error="Missing 'text'")

        try:
            proc = await asyncio.create_subprocess_exec(
                "pbcopy",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate(input=text.encode('utf-8'))

            if proc.returncode == 0:
                return ToolResult(success=True, data={"copied": len(text)})
            return ToolResult(success=False, error=stderr.decode()[:200])

        except Exception as e:
            return ToolResult(success=False, error=str(e))
