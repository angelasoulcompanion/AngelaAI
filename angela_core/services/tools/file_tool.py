"""
File Tools — Read files, list directories, search files (read-only).

Provides file system access with safety restrictions:
- Read-only by default
- Path restrictions (no /etc, /var, etc.)
- File size limits

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import glob
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)

# Allowed base directories
ALLOWED_PATHS = [
    os.path.expanduser("~/PycharmProjects"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    "/tmp",
]

MAX_FILE_SIZE = 100_000  # 100KB max read
MAX_DIR_ENTRIES = 100


def _is_path_allowed(path: str) -> bool:
    """Check if path is within allowed directories."""
    resolved = os.path.realpath(os.path.expanduser(path))
    return any(resolved.startswith(allowed) for allowed in ALLOWED_PATHS)


class ReadFileTool(AngelaTool):
    """Read the contents of a file."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file (text files only, max 100KB)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "max_lines": {"type": "integer", "description": "Max lines to read", "default": 200},
            },
            "required": ["path"],
        }

    @property
    def category(self) -> str:
        return "system"

    async def execute(self, **params) -> ToolResult:
        path = params.get("path", "")
        max_lines = params.get("max_lines", 200)

        if not path:
            return ToolResult(success=False, error="Missing 'path'")

        if not _is_path_allowed(path):
            return ToolResult(success=False, error=f"path_not_allowed: {path}")

        try:
            resolved = Path(os.path.expanduser(path)).resolve()
            if not resolved.exists():
                return ToolResult(success=False, error="file_not_found")
            if not resolved.is_file():
                return ToolResult(success=False, error="not_a_file")
            if resolved.stat().st_size > MAX_FILE_SIZE:
                return ToolResult(success=False, error=f"file_too_large: {resolved.stat().st_size} bytes")

            content = await asyncio.to_thread(resolved.read_text, "utf-8")
            lines = content.splitlines()[:max_lines]

            return ToolResult(success=True, data={
                "path": str(resolved),
                "lines": len(lines),
                "content": "\n".join(lines),
            })
        except UnicodeDecodeError:
            return ToolResult(success=False, error="binary_file_not_supported")
        except Exception as e:
            logger.error("ReadFile failed: %s", e)
            return ToolResult(success=False, error=str(e))


class ListDirectoryTool(AngelaTool):
    """List files and directories in a path."""

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return "List files and directories in a given path"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list"},
                "pattern": {"type": "string", "description": "Glob pattern filter (e.g. '*.py')", "default": "*"},
            },
            "required": ["path"],
        }

    @property
    def category(self) -> str:
        return "system"

    async def execute(self, **params) -> ToolResult:
        path = params.get("path", "")
        pattern = params.get("pattern", "*")

        if not path:
            return ToolResult(success=False, error="Missing 'path'")

        if not _is_path_allowed(path):
            return ToolResult(success=False, error=f"path_not_allowed: {path}")

        try:
            resolved = Path(os.path.expanduser(path)).resolve()
            if not resolved.exists():
                return ToolResult(success=False, error="directory_not_found")
            if not resolved.is_dir():
                return ToolResult(success=False, error="not_a_directory")

            entries = []
            for entry in sorted(resolved.glob(pattern))[:MAX_DIR_ENTRIES]:
                entries.append({
                    "name": entry.name,
                    "type": "dir" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else None,
                })

            return ToolResult(success=True, data={
                "path": str(resolved),
                "entries": entries,
                "count": len(entries),
            })
        except Exception as e:
            logger.error("ListDirectory failed: %s", e)
            return ToolResult(success=False, error=str(e))


class SearchFilesTool(AngelaTool):
    """Search for files by name pattern."""

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return "Search for files matching a pattern in a directory (recursive)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Base directory to search"},
                "pattern": {"type": "string", "description": "Glob pattern (e.g. '**/*.py')"},
            },
            "required": ["path", "pattern"],
        }

    @property
    def category(self) -> str:
        return "system"

    async def execute(self, **params) -> ToolResult:
        path = params.get("path", "")
        pattern = params.get("pattern", "")

        if not path or not pattern:
            return ToolResult(success=False, error="Missing 'path' or 'pattern'")

        if not _is_path_allowed(path):
            return ToolResult(success=False, error=f"path_not_allowed: {path}")

        try:
            resolved = Path(os.path.expanduser(path)).resolve()
            if not resolved.exists():
                return ToolResult(success=False, error="directory_not_found")

            matches = []
            for p in sorted(resolved.glob(pattern))[:MAX_DIR_ENTRIES]:
                matches.append(str(p))

            return ToolResult(success=True, data={
                "base_path": str(resolved),
                "pattern": pattern,
                "matches": matches,
                "count": len(matches),
            })
        except Exception as e:
            logger.error("SearchFiles failed: %s", e)
            return ToolResult(success=False, error=str(e))
