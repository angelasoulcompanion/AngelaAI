"""
Pythia Router — Modern Portfolio Theory (MPT)
Optimization, Efficient Frontier, Correlation Matrix.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.optimization_service import (
    optimize_portfolio,
    generate_efficient_frontier,
    calculate_correlation_matrix,
)

router = APIRouter(prefix="/api/mpt", tags=["MPT"])


@router.get("/{portfolio_id}/optimize")
async def optimize(
    portfolio_id: UUID,
    optimization_type: str = Query("max_sharpe", description="max_sharpe | min_volatility | target_return"),
    risk_free_rate: float = Query(0.0225, ge=0, le=0.5),
    target_return: Optional[float] = Query(None, description="Required if optimization_type=target_return"),
    days: int = Query(365, ge=30, le=3650),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await optimize_portfolio(
        conn, portfolio_id, optimization_type, risk_free_rate, target_return, days
    )
    return {
        "portfolio_id": str(portfolio_id),
        "optimization_type": result.optimization_type,
        "success": result.success,
        "message": result.message,
        "weights": result.weights,
        "expected_return": result.expected_return,
        "volatility": result.volatility,
        "sharpe_ratio": result.sharpe_ratio,
    }


@router.get("/{portfolio_id}/efficient-frontier")
async def efficient_frontier(
    portfolio_id: UUID,
    n_points: int = Query(50, ge=10, le=200),
    risk_free_rate: float = Query(0.0225, ge=0, le=0.5),
    days: int = Query(365, ge=30, le=3650),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await generate_efficient_frontier(conn, portfolio_id, n_points, risk_free_rate, days)
    return result


@router.get("/{portfolio_id}/correlation")
async def correlation_matrix(
    portfolio_id: UUID,
    days: int = Query(365, ge=30, le=3650),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await calculate_correlation_matrix(conn, portfolio_id, days)
    return result
