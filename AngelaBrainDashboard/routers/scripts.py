"""Python script browser endpoints."""
import pathlib
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from schemas import ScriptContentUpdate

router = APIRouter(prefix="/api/python-scripts", tags=["scripts"])

ANGELA_PROJECT_ROOT = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI"

# Folders to scan for Python scripts (relative to project root)
SCRIPT_SCAN_FOLDERS = ["angela_core", "scripts", "mcp_servers", "config", "tests"]

# Folders to skip inside scan folders
SKIP_DIRS = {"__pycache__", ".venv", "node_modules", "datasets", "legacy", ".git"}


@router.get("/")
async def list_python_scripts(folder: Optional[str] = None):
    """List Python scripts from AngelaAI project for the script picker"""
    root = pathlib.Path(ANGELA_PROJECT_ROOT)
    scripts = []

    scan_folders = [folder] if folder else SCRIPT_SCAN_FOLDERS

    for scan_folder in scan_folders:
        folder_path = root / scan_folder
        if not folder_path.exists():
            continue

        for py_file in sorted(folder_path.rglob("*.py")):
            parts = py_file.relative_to(root).parts
            if any(skip in parts for skip in SKIP_DIRS):
                continue

            rel_path = str(py_file.relative_to(root))
            scripts.append({
                "path": rel_path,
                "folder": scan_folder,
                "filename": py_file.name,
                "size_bytes": py_file.stat().st_size,
            })

    return scripts


@router.get("/content")
async def get_python_script_content(path: str):
    """Read content of a Python script file"""
    root = pathlib.Path(ANGELA_PROJECT_ROOT)
    full_path = root / path

    try:
        resolved = full_path.resolve()
        if not str(resolved).startswith(str(root.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: path outside project root")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not path.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only Python files are allowed")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = resolved.read_text(encoding='utf-8')
        return {
            "path": path,
            "content": content,
            "size_bytes": resolved.stat().st_size,
            "last_modified": resolved.stat().st_mtime
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.put("/content")
async def update_python_script_content(body: ScriptContentUpdate):
    """Write content to a Python script file"""
    root = pathlib.Path(ANGELA_PROJECT_ROOT)
    full_path = root / body.path

    try:
        resolved = full_path.resolve()
        if not str(resolved).startswith(str(root.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: path outside project root")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    if not body.path.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only Python files are allowed")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        backup_content = resolved.read_text(encoding='utf-8')
        resolved.write_text(body.content, encoding='utf-8')

        return {
            "success": True,
            "path": body.path,
            "size_bytes": resolved.stat().st_size,
            "backup_size": len(backup_content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")
