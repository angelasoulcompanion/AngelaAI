"""
Pythia Router — Position Sizing
Kelly Criterion, Volatility Target, ATR-based sizing.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.position_sizing_service import calculate_position_size, risk_parity_weights

router = APIRouter(prefix="/api/position-size", tags=["Position Sizing"])


@router.get("/{portfolio_id}/{asset_id}")
async def position_size_endpoint(
    portfolio_id: UUID,
    asset_id: UUID,
    method: str = Query("kelly", description="kelly | volatility_target | atr_stop"),
    risk_per_trade: float = Query(0.02, ge=0.001, le=0.10),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Calculate position size for a trade."""
    result = await calculate_position_size(conn, asset_id, portfolio_id, method, risk_per_trade)
    return {
        "asset_id": result.asset_id,
        "symbol": result.symbol,
        "method": result.method,
        "position_size_pct": result.position_size_pct,
        "position_size_value": result.position_size_value,
        "portfolio_value": result.portfolio_value,
        "risk_per_trade": result.risk_per_trade,
        "details": result.details,
        "success": result.success,
        "message": result.message,
    }


@router.get("/{portfolio_id}/risk-parity")
async def risk_parity_endpoint(
    portfolio_id: UUID,
    days: int = Query(252, ge=60, le=2520),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Calculate risk parity weights for portfolio holdings."""
    # Get portfolio's asset IDs
    rows = await conn.fetch(
        "SELECT asset_id FROM portfolio_holdings WHERE portfolio_id = $1",
        portfolio_id,
    )
    if not rows:
        return {"success": False, "message": "No holdings found"}

    asset_ids = [r["asset_id"] for r in rows]
    result = await risk_parity_weights(conn, asset_ids, days)
    return {
        "portfolio_id": str(portfolio_id),
        "weights": result.weights,
        "symbols": result.symbols,
        "volatilities": result.volatilities,
        "success": result.success,
        "message": result.message,
    }
