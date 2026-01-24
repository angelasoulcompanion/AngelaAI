"""
Dev Tools - Code Search and File Operations
Tools สำหรับ Dev Agent

Safe file operations only - no destructive commands.

Author: Angela AI 💜
Created: 2025-01-25
"""

import asyncio
import subprocess
import os
from pathlib import Path
from typing import Any, Optional, Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class CodeSearchInput(BaseModel):
    """Input schema for code search tool"""
    pattern: str = Field(..., description="Regex pattern to search for")
    file_type: Optional[str] = Field(default=None, description="File extension (py, ts, js)")
    path: Optional[str] = Field(default=None, description="Directory to search in")


class CodeSearchTool(BaseTool):
    """
    Tool for searching code patterns in the codebase.
    Uses ripgrep for fast searching.
    """
    name: str = "code_search"
    description: str = """ค้นหา code patterns ใน codebase
    ใช้เมื่อต้องการหา function, class, หรือ code patterns
    Input: pattern (regex), file_type (py/ts/js), path (directory)"""
    args_schema: Type[BaseModel] = CodeSearchInput

    def _run(
        self,
        pattern: str,
        file_type: Optional[str] = None,
        path: Optional[str] = None
    ) -> str:
        """Search code patterns using ripgrep"""
        try:
            # Default to AngelaAI project
            search_path = path or "/Users/davidsamanyaporn/PycharmProjects/AngelaAI"

            # Build rg command
            cmd = ["rg", "--max-count=20", "--line-number"]

            if file_type:
                cmd.extend(["--type", file_type])

            cmd.extend([pattern, search_path])

            # Run ripgrep
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                output = f"🔍 Code Search Results for: {pattern}\n\n"
                lines = result.stdout.strip().split("\n")[:20]  # Limit output

                for line in lines:
                    # Clean up the path for readability
                    line = line.replace(search_path + "/", "")
                    output += f"  {line}\n"

                return output
            else:
                return f"ไม่พบ code ที่ตรงกับ pattern: {pattern}"

        except subprocess.TimeoutExpired:
            return "❌ Search timed out"
        except Exception as e:
            return f"Error searching code: {str(e)}"


class FileReadInput(BaseModel):
    """Input schema for file read tool"""
    file_path: str = Field(..., description="Path to the file to read")
    start_line: int = Field(default=1, description="Starting line number")
    num_lines: int = Field(default=50, description="Number of lines to read")


class FileReadTool(BaseTool):
    """
    Tool for reading file contents safely.
    Limited to reasonable file sizes.
    """
    name: str = "file_read"
    description: str = """อ่านเนื้อหาไฟล์
    ใช้เมื่อต้องการดูเนื้อหาของไฟล์ใด ๆ
    Input: file_path (path), start_line (default 1), num_lines (default 50)"""
    args_schema: Type[BaseModel] = FileReadInput

    def _run(
        self,
        file_path: str,
        start_line: int = 1,
        num_lines: int = 50
    ) -> str:
        """Read file contents"""
        try:
            path = Path(file_path)

            if not path.exists():
                return f"❌ File not found: {file_path}"

            if not path.is_file():
                return f"❌ Not a file: {file_path}"

            # Check file size (limit to 1MB)
            if path.stat().st_size > 1024 * 1024:
                return f"❌ File too large: {path.stat().st_size} bytes"

            # Read file
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Slice the requested lines
            total_lines = len(lines)
            end_line = min(start_line + num_lines - 1, total_lines)
            selected_lines = lines[start_line - 1:end_line]

            # Format output
            output = f"📄 {file_path}\n"
            output += f"   Lines {start_line}-{end_line} of {total_lines}\n\n"

            for i, line in enumerate(selected_lines, start=start_line):
                output += f"{i:4d}| {line.rstrip()}\n"

            return output

        except UnicodeDecodeError:
            return f"❌ Cannot read binary file: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


class RunTestsInput(BaseModel):
    """Input schema for run tests tool"""
    test_path: Optional[str] = Field(default=None, description="Specific test file or directory")
    verbose: bool = Field(default=False, description="Show verbose output")


class RunTestsTool(BaseTool):
    """
    Tool for running pytest tests safely.
    Only runs tests, no modifications.
    """
    name: str = "run_tests"
    description: str = """รัน pytest tests
    ใช้เมื่อต้องการรัน tests เพื่อตรวจสอบ code
    Input: test_path (optional specific path), verbose (bool)"""
    args_schema: Type[BaseModel] = RunTestsInput

    def _run(
        self,
        test_path: Optional[str] = None,
        verbose: bool = False
    ) -> str:
        """Run pytest tests"""
        try:
            cmd = ["python3", "-m", "pytest"]

            if verbose:
                cmd.append("-v")

            if test_path:
                cmd.append(test_path)
            else:
                # Default to tests directory
                cmd.append("/Users/davidsamanyaporn/PycharmProjects/AngelaAI/tests")

            cmd.extend(["--timeout=60", "-x"])  # Stop on first failure

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd="/Users/davidsamanyaporn/PycharmProjects/AngelaAI"
            )

            output = f"🧪 Test Results\n\n"
            output += result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout

            if result.returncode != 0:
                output += f"\n\n❌ Tests failed (exit code: {result.returncode})"
                if result.stderr:
                    output += f"\nErrors:\n{result.stderr[-500:]}"
            else:
                output += "\n\n✅ All tests passed!"

            return output

        except subprocess.TimeoutExpired:
            return "❌ Tests timed out after 120 seconds"
        except Exception as e:
            return f"Error running tests: {str(e)}"
