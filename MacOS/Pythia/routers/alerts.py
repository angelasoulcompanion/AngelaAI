"""
Pythia Router — Alert System
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
import asyncpg
from db import get_conn
from services.alert_service import (
    get_alerts, create_alert, mark_read, mark_all_read,
    delete_alert, get_unread_count, check_and_generate_alerts,
)

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


class CreateAlertRequest(BaseModel):
    alert_type: str = "custom"
    title: str
    message: str = ""
    severity: str = "info"
    asset_id: Optional[UUID] = None
    portfolio_id: Optional[UUID] = None


@router.get("/")
async def list_alerts(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    conn: asyncpg.Connection = Depends(get_conn),
):
    alerts = await get_alerts(conn, unread_only, limit)
    return {
        "alerts": [
            {
                "alert_id": a.alert_id, "alert_type": a.alert_type,
                "title": a.title, "message": a.message,
                "severity": a.severity, "is_read": a.is_read,
                "triggered_at": a.triggered_at, "created_at": a.created_at,
            }
            for a in alerts
        ],
        "count": len(alerts),
    }


@router.get("/unread-count")
async def unread_count(conn: asyncpg.Connection = Depends(get_conn)):
    count = await get_unread_count(conn)
    return {"count": count}


@router.post("/")
async def create_alert_endpoint(
    req: CreateAlertRequest,
    conn: asyncpg.Connection = Depends(get_conn),
):
    aid = await create_alert(conn, req.alert_type, req.title, req.message, req.severity, req.asset_id, req.portfolio_id)
    return {"alert_id": aid, "success": True}


@router.put("/{alert_id}/read")
async def mark_read_endpoint(alert_id: UUID, conn: asyncpg.Connection = Depends(get_conn)):
    ok = await mark_read(conn, alert_id)
    return {"success": ok}


@router.put("/read-all")
async def mark_all_read_endpoint(conn: asyncpg.Connection = Depends(get_conn)):
    count = await mark_all_read(conn)
    return {"marked": count, "success": True}


@router.delete("/{alert_id}")
async def delete_alert_endpoint(alert_id: UUID, conn: asyncpg.Connection = Depends(get_conn)):
    ok = await delete_alert(conn, alert_id)
    return {"success": ok}


@router.post("/check")
async def check_alerts_endpoint(conn: asyncpg.Connection = Depends(get_conn)):
    generated = await check_and_generate_alerts(conn)
    return {"generated": len(generated), "alert_ids": generated}
