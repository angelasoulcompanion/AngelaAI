"""Scheduled tasks (CRUD + Execute) endpoints.

dashboard_scheduled_tasks + dashboard_scheduled_task_logs tables removed.
All endpoints return empty/null.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn, get_pool
from schemas import ScheduledTaskCreate, ScheduledTaskUpdate

router = APIRouter(prefix="/api/scheduled-tasks", tags=["scheduled-tasks"])


@router.get("/next")
async def get_next_scheduled_task(conn=Depends(get_conn)):
    return None


@router.get("/")
async def list_scheduled_tasks(conn=Depends(get_conn)):
    return []


@router.post("/")
async def create_scheduled_task(body: ScheduledTaskCreate, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Scheduled tasks table not available")


@router.put("/{task_id}")
async def update_scheduled_task(task_id: str, body: ScheduledTaskUpdate, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Scheduled tasks table not available")


@router.delete("/{task_id}")
async def delete_scheduled_task(task_id: str, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Scheduled tasks table not available")


@router.post("/{task_id}/execute")
async def execute_scheduled_task(task_id: str, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Scheduled tasks table not available")


@router.get("/{task_id}/logs")
async def get_scheduled_task_logs(task_id: str, limit: int = Query(20, ge=1, le=100), conn=Depends(get_conn)):
    return []
