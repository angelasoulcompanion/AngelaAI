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
    method: str = Query("prophet", description="prophet | moving_average | linear_regression | growth_rate"),
    forecast_days: int = Query(30, ge=5, le=365),
    lookback_days: int = Query(365, ge=60, le=3650),
    include_interpretation: bool = Query(False, description="Include LLM interpretation + risk factors"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await forecast_price(conn, asset_id, method, forecast_days, lookback_days, include_interpretation)
    return {
        "symbol": result.symbol,
        "method": result.method,
        "current_price": result.current_price,
        "forecast_days": result.forecast_days,
        "trend": result.trend,
        "confidence": result.confidence,
        "confidence_level": result.confidence_level,
        "predictions": result.predictions,
        "historical_prices": result.historical_prices,
        # Enhanced fields
        "interpretation": result.interpretation,
        "risk_factors": result.risk_factors,
        "llm_provider": result.llm_provider,
        "success": result.success,
        "message": result.message,
    }
