"""
Pythia Router — Market Regime Detection
HMM-based regime classification: bull, bear, sideways, crisis
"""
from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.regime_service import detect_regime, get_regime_history, get_market_state

router = APIRouter(prefix="/api/regime", tags=["Regime Detection"])


@router.get("/{symbol}")
async def regime_endpoint(
    symbol: str,
    days: int = Query(500, ge=60, le=2000, description="Lookback days for HMM fitting"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Detect current market regime for a symbol."""
    result = await detect_regime(conn, symbol, days)
    return {
        "symbol": result.symbol,
        "regime": result.regime,
        "probability": result.probability,
        "all_probabilities": result.all_probabilities,
        "volatility": result.volatility,
        "trend_strength": result.trend_strength,
        "detected_at": result.detected_at,
        "success": result.success,
        "message": result.message,
    }


@router.get("/{symbol}/history")
async def regime_history_endpoint(
    symbol: str,
    days: int = Query(365, ge=60, le=2000),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Get regime classification history for charting."""
    history = await get_regime_history(conn, symbol, days)
    return {
        "symbol": symbol,
        "history": [
            {
                "date": h.date,
                "regime": h.regime,
                "probability": h.probability,
                "volatility": h.volatility,
            }
            for h in history
        ],
        "count": len(history),
    }


@router.get("/market-state/overview")
async def market_state_endpoint(
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Aggregate regime across major global indices."""
    result = await get_market_state(conn)
    return {
        "overall_regime": result.overall_regime,
        "risk_level": result.risk_level,
        "components": result.components,
        "success": result.success,
        "message": result.message,
    }
