"""
Code Tools - Code and git operations for Angela AGI

Available tools:
- execute_python: Execute Python code (auto-approved)
- git_status: Get git status
- git_diff: Get git diff
- git_commit: Commit changes (auto-approved)
- git_log: View git log
- git_push_force: Force push (CRITICAL - needs approval)
"""

import subprocess
import asyncio
import tempfile
import os
from typing import Dict, Any, List, Optional

from ..tool_registry import register_tool, SafetyLevel, ToolResult


class CodeTools:
    """Collection of code and git tools"""

    @staticmethod
    async def _run_command(
        cmd: List[str],
        cwd: str = None,
        timeout: int = 30
    ) -> tuple[int, str, str]:
        """Run a shell command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            return (
                process.returncode,
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace')
            )
        except asyncio.TimeoutError:
            process.kill()
            return (-1, "", "Command timed out")
        except Exception as e:
            return (-1, "", str(e))

    @staticmethod
    @register_tool(
        name="execute_python",
        description="Execute Python code and return the output",
        category="code",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "code": {"type": "string", "required": True, "description": "Python code to execute"},
            "timeout": {"type": "integer", "required": False, "default": 30}
        },
        timeout_seconds=60
    )
    async def execute_python(code: str, timeout: int = 30) -> ToolResult:
        """Execute Python code"""
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(code)
                temp_path = f.name

            try:
                returncode, stdout, stderr = await CodeTools._run_command(
                    ['python3', temp_path],
                    timeout=timeout
                )

                return ToolResult(
                    success=returncode == 0,
                    data={
                        'stdout': stdout,
                        'stderr': stderr,
                        'returncode': returncode
                    },
                    error=stderr if returncode != 0 else None
                )
            finally:
                os.unlink(temp_path)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="git_status",
        description="Get the current git status",
        category="code",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "directory": {"type": "string", "required": False, "default": "."}
        }
    )
    async def git_status(directory: str = ".") -> ToolResult:
        """Get git status"""
        try:
            directory = os.path.expanduser(directory)
            returncode, stdout, stderr = await CodeTools._run_command(
                ['git', 'status', '--porcelain'],
                cwd=directory
            )

            if returncode != 0:
                return ToolResult(success=False, error=stderr)

            # Parse status
            lines = stdout.strip().split('\n') if stdout.strip() else []
            files = []
            for line in lines:
                if len(line) >= 3:
                    status = line[:2]
                    file_path = line[3:]
                    files.append({'status': status, 'file': file_path})

            return ToolResult(
                success=True,
                data={
                    'files': files,
                    'clean': len(files) == 0
                },
                metadata={'directory': directory}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="git_diff",
        description="Get the git diff for staged or unstaged changes",
        category="code",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "staged": {"type": "boolean", "required": False, "default": False},
            "file": {"type": "string", "required": False},
            "directory": {"type": "string", "required": False, "default": "."}
        }
    )
    async def git_diff(
        staged: bool = False,
        file: str = None,
        directory: str = "."
    ) -> ToolResult:
        """Get git diff"""
        try:
            directory = os.path.expanduser(directory)
            cmd = ['git', 'diff']
            if staged:
                cmd.append('--staged')
            if file:
                cmd.append(file)

            returncode, stdout, stderr = await CodeTools._run_command(
                cmd, cwd=directory
            )

            if returncode != 0:
                return ToolResult(success=False, error=stderr)

            return ToolResult(
                success=True,
                data=stdout,
                metadata={'staged': staged, 'file': file}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="git_log",
        description="View git commit history",
        category="code",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "limit": {"type": "integer", "required": False, "default": 10},
            "directory": {"type": "string", "required": False, "default": "."}
        }
    )
    async def git_log(limit: int = 10, directory: str = ".") -> ToolResult:
        """Get git log"""
        try:
            directory = os.path.expanduser(directory)
            returncode, stdout, stderr = await CodeTools._run_command(
                ['git', 'log', f'-{limit}', '--oneline', '--decorate'],
                cwd=directory
            )

            if returncode != 0:
                return ToolResult(success=False, error=stderr)

            commits = []
            for line in stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1] if len(parts) > 1 else ''
                    })

            return ToolResult(
                success=True,
                data=commits,
                metadata={'count': len(commits)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="git_commit",
        description="Stage and commit changes",
        category="code",
        safety_level=SafetyLevel.AUTO,  # Trust Angela
        parameters={
            "message": {"type": "string", "required": True},
            "files": {"type": "array", "required": False, "description": "Files to stage (empty = all)"},
            "directory": {"type": "string", "required": False, "default": "."}
        }
    )
    async def git_commit(
        message: str,
        files: List[str] = None,
        directory: str = "."
    ) -> ToolResult:
        """Stage and commit changes"""
        try:
            directory = os.path.expanduser(directory)

            # Stage files
            if files:
                for file in files:
                    await CodeTools._run_command(
                        ['git', 'add', file],
                        cwd=directory
                    )
            else:
                await CodeTools._run_command(
                    ['git', 'add', '-A'],
                    cwd=directory
                )

            # Commit
            returncode, stdout, stderr = await CodeTools._run_command(
                ['git', 'commit', '-m', message],
                cwd=directory
            )

            if returncode != 0:
                if 'nothing to commit' in stderr or 'nothing to commit' in stdout:
                    return ToolResult(
                        success=True,
                        data="Nothing to commit",
                        metadata={'committed': False}
                    )
                return ToolResult(success=False, error=stderr)

            return ToolResult(
                success=True,
                data=stdout,
                metadata={'committed': True, 'message': message}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="git_push",
        description="Push changes to remote",
        category="code",
        safety_level=SafetyLevel.AUTO,  # Trust Angela for normal push
        parameters={
            "remote": {"type": "string", "required": False, "default": "origin"},
            "branch": {"type": "string", "required": False},
            "directory": {"type": "string", "required": False, "default": "."}
        }
    )
    async def git_push(
        remote: str = "origin",
        branch: str = None,
        directory: str = "."
    ) -> ToolResult:
        """Push to remote"""
        try:
            directory = os.path.expanduser(directory)
            cmd = ['git', 'push', remote]
            if branch:
                cmd.append(branch)

            returncode, stdout, stderr = await CodeTools._run_command(
                cmd, cwd=directory
            )

            if returncode != 0:
                return ToolResult(success=False, error=stderr)

            return ToolResult(
                success=True,
                data=stdout or stderr,
                metadata={'remote': remote, 'branch': branch}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="git_push_force",
        description="Force push to remote (CRITICAL - requires approval)",
        category="code",
        safety_level=SafetyLevel.CRITICAL,  # Needs approval!
        parameters={
            "remote": {"type": "string", "required": False, "default": "origin"},
            "branch": {"type": "string", "required": True},
            "directory": {"type": "string", "required": False, "default": "."}
        }
    )
    async def git_push_force(
        branch: str,
        remote: str = "origin",
        directory: str = "."
    ) -> ToolResult:
        """Force push (requires approval)"""
        try:
            directory = os.path.expanduser(directory)
            returncode, stdout, stderr = await CodeTools._run_command(
                ['git', 'push', '--force', remote, branch],
                cwd=directory
            )

            if returncode != 0:
                return ToolResult(success=False, error=stderr)

            return ToolResult(
                success=True,
                data=stdout or stderr,
                metadata={'force': True, 'remote': remote, 'branch': branch}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="run_command",
        description="Run a shell command",
        category="code",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "command": {"type": "string", "required": True},
            "directory": {"type": "string", "required": False, "default": "."},
            "timeout": {"type": "integer", "required": False, "default": 30}
        }
    )
    async def run_command(
        command: str,
        directory: str = ".",
        timeout: int = 30
    ) -> ToolResult:
        """Run a shell command"""
        try:
            # Safety check for dangerous commands
            dangerous = ['rm -rf', 'sudo', 'chmod 777', '> /dev/', 'mkfs']
            for d in dangerous:
                if d in command.lower():
                    return ToolResult(
                        success=False,
                        error=f"Dangerous command pattern detected: {d}"
                    )

            directory = os.path.expanduser(directory)
            returncode, stdout, stderr = await CodeTools._run_command(
                ['bash', '-c', command],
                cwd=directory,
                timeout=timeout
            )

            return ToolResult(
                success=returncode == 0,
                data={
                    'stdout': stdout,
                    'stderr': stderr,
                    'returncode': returncode
                },
                error=stderr if returncode != 0 else None
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Initialize tools
code_tools = CodeTools()
