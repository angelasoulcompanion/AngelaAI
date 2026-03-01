"""
Pythia Router — AI Price Forecasting
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.ai_forecast_service import forecast_price

router = APIRouter(prefix="/api/ai/forecast", tags=["AI Forecast"])


@router.get("/{asset_id}")
async def forecast(
    asset_id: UUID,
    method: str = Query("moving_average", description="moving_average | linear_regression | exponential_smoothing"),
    forecast_days: int = Query(30, ge=5, le=365),
    lookback_days: int = Query(365, ge=60, le=3650),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await forecast_price(conn, asset_id, method, forecast_days, lookback_days)
    return {
        "symbol": result.symbol,
        "method": result.method,
        "current_price": result.current_price,
        "forecast_days": result.forecast_days,
        "trend": result.trend,
        "confidence": result.confidence,
        "predictions": result.predictions,
        "success": result.success,
        "message": result.message,
    }
