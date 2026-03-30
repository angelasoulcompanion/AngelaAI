"""
Pythia Router — Trading Signals
Multi-factor signal generation and universe scanning.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
import asyncpg

from db import get_conn
from services.signal_service import generate_signals, scan_universe, get_signal_history

router = APIRouter(prefix="/api/signals", tags=["Trading Signals"])


class ScanRequest(BaseModel):
    asset_ids: list[UUID]
    min_score: float = 0.0
    include_ai: bool = False


@router.get("/{asset_id}")
async def signals_endpoint(
    asset_id: UUID,
    include_ai: bool = Query(True, description="Include AI insight"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Generate multi-factor signals for a single asset."""
    result = await generate_signals(conn, asset_id, include_ai=include_ai)
    return {
        "asset_id": result.asset_id,
        "symbol": result.symbol,
        "composite_score": result.composite_score,
        "composite_direction": result.composite_direction,
        "technical_score": result.technical_score,
        "sentiment_score": result.sentiment_score,
        "quant_score": result.quant_score,
        "ai_insight": result.ai_insight,
        "signals": [
            {
                "signal_type": s.signal_type,
                "signal_name": s.signal_name,
                "direction": s.direction,
                "strength": s.strength,
                "confidence": s.confidence,
                "metadata": s.metadata,
            }
            for s in result.signals
        ],
        "success": result.success,
        "message": result.message,
    }


@router.get("/{asset_id}/history")
async def signal_history_endpoint(
    asset_id: UUID,
    days: int = Query(30, ge=1, le=365),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Get signal history for an asset."""
    history = await get_signal_history(conn, asset_id, days)
    return {
        "asset_id": str(asset_id),
        "days": days,
        "signals": history,
        "count": len(history),
    }


@router.post("/scan")
async def scan_endpoint(
    req: ScanRequest,
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Batch scan multiple assets for signals."""
    results = await scan_universe(
        conn, req.asset_ids, min_score=req.min_score, include_ai=req.include_ai,
    )
    return {
        "results": [
            {
                "asset_id": r.asset_id,
                "symbol": r.symbol,
                "composite_score": r.composite_score,
                "direction": r.direction,
                "top_signal": r.top_signal,
                "regime": r.regime,
            }
            for r in results
        ],
        "count": len(results),
        "scanned": len(req.asset_ids),
    }
