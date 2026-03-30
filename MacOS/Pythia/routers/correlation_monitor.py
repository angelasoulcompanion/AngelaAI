"""
Pythia Router — Correlation Monitor
Rolling correlation shifts and regime detection.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.correlation_monitor_service import detect_correlation_shifts

router = APIRouter(prefix="/api/correlation-monitor", tags=["Correlation Monitor"])


@router.get("/{portfolio_id}")
async def correlation_monitor_endpoint(
    portfolio_id: UUID,
    window: int = Query(60, ge=20, le=252),
    lookback: int = Query(252, ge=60, le=2520),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await detect_correlation_shifts(conn, portfolio_id, window, lookback)
    return {
        "portfolio_id": result.portfolio_id,
        "correlation_regime": result.correlation_regime,
        "avg_correlation": result.avg_correlation,
        "avg_historical": result.avg_historical,
        "shifts": [
            {
                "asset_1": s.asset_1, "asset_2": s.asset_2,
                "current_corr": s.current_corr, "historical_corr": s.historical_corr,
                "shift": s.shift, "significance": s.significance,
            }
            for s in result.shifts
        ],
        "matrix": result.matrix_current,
        "symbols": result.symbols,
        "success": result.success,
        "message": result.message,
    }
