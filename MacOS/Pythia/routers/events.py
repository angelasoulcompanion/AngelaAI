"""
Pythia Router — Event Impact Analyzer
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
import asyncpg
from db import get_conn
from services.event_service import analyze_event_impact

router = APIRouter(prefix="/api/events", tags=["Event Impact"])


@router.get("/{asset_id}/impact")
async def event_impact_endpoint(
    asset_id: UUID,
    event_type: str = Query("earnings", description="earnings | dividend | economic"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await analyze_event_impact(conn, asset_id, event_type)
    return {
        "asset_id": result.asset_id,
        "symbol": result.symbol,
        "event_type": result.event_type,
        "avg_move_pct": result.avg_move_pct,
        "avg_pre_move": result.avg_pre_move,
        "avg_post_move": result.avg_post_move,
        "positive_rate": result.positive_rate,
        "events_analyzed": result.events_analyzed,
        "upcoming_events": result.upcoming_events,
        "historical_events": result.historical_events,
        "success": result.success,
        "message": result.message,
    }
