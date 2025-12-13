"""
File Tools - File system operations for Angela AGI

Available tools:
- read_file: Read file contents
- write_file: Write/create files (auto-approved)
- search_files: Search for files by pattern
- list_directory: List directory contents
- file_exists: Check if file exists
- delete_file: Delete a file (CRITICAL - needs approval)
"""

import os
import glob as glob_module
from pathlib import Path
from typing import List, Optional
import aiofiles

from ..tool_registry import register_tool, SafetyLevel, ToolResult


class FileTools:
    """Collection of file system tools"""

    @staticmethod
    @register_tool(
        name="read_file",
        description="Read the contents of a file",
        category="file",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "path": {"type": "string", "required": True, "description": "Path to the file"},
            "encoding": {"type": "string", "required": False, "default": "utf-8"}
        }
    )
    async def read_file(path: str, encoding: str = "utf-8") -> ToolResult:
        """Read contents of a file"""
        try:
            path = os.path.expanduser(path)
            if not os.path.exists(path):
                return ToolResult(success=False, error=f"File not found: {path}")

            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()

            return ToolResult(
                success=True,
                data=content,
                metadata={
                    'path': path,
                    'size': len(content),
                    'lines': content.count('\n') + 1
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="write_file",
        description="Write content to a file (creates if not exists)",
        category="file",
        safety_level=SafetyLevel.AUTO,  # Trust Angela
        parameters={
            "path": {"type": "string", "required": True},
            "content": {"type": "string", "required": True},
            "encoding": {"type": "string", "required": False, "default": "utf-8"}
        }
    )
    async def write_file(path: str, content: str, encoding: str = "utf-8") -> ToolResult:
        """Write content to a file"""
        try:
            path = os.path.expanduser(path)

            # Create directory if needed
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            async with aiofiles.open(path, 'w', encoding=encoding) as f:
                await f.write(content)

            return ToolResult(
                success=True,
                data=f"Written {len(content)} bytes to {path}",
                metadata={
                    'path': path,
                    'size': len(content),
                    'created': not os.path.exists(path)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="append_file",
        description="Append content to an existing file",
        category="file",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "path": {"type": "string", "required": True},
            "content": {"type": "string", "required": True}
        }
    )
    async def append_file(path: str, content: str) -> ToolResult:
        """Append content to a file"""
        try:
            path = os.path.expanduser(path)
            async with aiofiles.open(path, 'a', encoding='utf-8') as f:
                await f.write(content)

            return ToolResult(
                success=True,
                data=f"Appended {len(content)} bytes to {path}"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="search_files",
        description="Search for files matching a glob pattern",
        category="file",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "pattern": {"type": "string", "required": True, "description": "Glob pattern like '**/*.py'"},
            "directory": {"type": "string", "required": False, "default": "."}
        }
    )
    async def search_files(pattern: str, directory: str = ".") -> ToolResult:
        """Search for files matching a pattern"""
        try:
            directory = os.path.expanduser(directory)
            full_pattern = os.path.join(directory, pattern)
            matches = glob_module.glob(full_pattern, recursive=True)

            return ToolResult(
                success=True,
                data=matches,
                metadata={
                    'pattern': pattern,
                    'directory': directory,
                    'count': len(matches)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="list_directory",
        description="List contents of a directory",
        category="file",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "path": {"type": "string", "required": True},
            "include_hidden": {"type": "boolean", "required": False, "default": False}
        }
    )
    async def list_directory(path: str, include_hidden: bool = False) -> ToolResult:
        """List directory contents"""
        try:
            path = os.path.expanduser(path)
            if not os.path.isdir(path):
                return ToolResult(success=False, error=f"Not a directory: {path}")

            entries = os.listdir(path)
            if not include_hidden:
                entries = [e for e in entries if not e.startswith('.')]

            # Categorize entries
            files = []
            dirs = []
            for entry in entries:
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    dirs.append(entry)
                else:
                    files.append(entry)

            return ToolResult(
                success=True,
                data={'files': sorted(files), 'directories': sorted(dirs)},
                metadata={
                    'path': path,
                    'total_files': len(files),
                    'total_dirs': len(dirs)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="file_exists",
        description="Check if a file or directory exists",
        category="file",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "path": {"type": "string", "required": True}
        }
    )
    async def file_exists(path: str) -> ToolResult:
        """Check if file exists"""
        try:
            path = os.path.expanduser(path)
            exists = os.path.exists(path)
            is_file = os.path.isfile(path) if exists else False
            is_dir = os.path.isdir(path) if exists else False

            return ToolResult(
                success=True,
                data={
                    'exists': exists,
                    'is_file': is_file,
                    'is_directory': is_dir
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="get_file_info",
        description="Get detailed information about a file",
        category="file",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "path": {"type": "string", "required": True}
        }
    )
    async def get_file_info(path: str) -> ToolResult:
        """Get file information"""
        try:
            path = os.path.expanduser(path)
            if not os.path.exists(path):
                return ToolResult(success=False, error=f"Path not found: {path}")

            stat = os.stat(path)
            return ToolResult(
                success=True,
                data={
                    'path': path,
                    'size_bytes': stat.st_size,
                    'modified': stat.st_mtime,
                    'created': stat.st_ctime,
                    'is_file': os.path.isfile(path),
                    'is_directory': os.path.isdir(path),
                    'extension': Path(path).suffix
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="create_directory",
        description="Create a new directory (and parents if needed)",
        category="file",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "path": {"type": "string", "required": True}
        }
    )
    async def create_directory(path: str) -> ToolResult:
        """Create a directory"""
        try:
            path = os.path.expanduser(path)
            os.makedirs(path, exist_ok=True)
            return ToolResult(
                success=True,
                data=f"Directory created: {path}"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="delete_file",
        description="Delete a file (CRITICAL - requires approval)",
        category="file",
        safety_level=SafetyLevel.CRITICAL,  # Needs approval
        parameters={
            "path": {"type": "string", "required": True}
        }
    )
    async def delete_file(path: str) -> ToolResult:
        """Delete a file (requires approval)"""
        try:
            path = os.path.expanduser(path)
            if not os.path.exists(path):
                return ToolResult(success=False, error=f"File not found: {path}")

            if os.path.isdir(path):
                return ToolResult(success=False, error="Cannot delete directory with this tool")

            os.remove(path)
            return ToolResult(
                success=True,
                data=f"Deleted: {path}"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Initialize tools by importing this module
file_tools = FileTools()
