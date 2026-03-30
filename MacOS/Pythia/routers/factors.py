"""
Pythia Router — Factor Models (Fama-French)
FF3/FF5 factor exposure analysis.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.factor_service import calculate_factor_exposures, calculate_asset_factor_exposure

router = APIRouter(prefix="/api/factors", tags=["Factor Models"])


@router.get("/{portfolio_id}")
async def portfolio_factors_endpoint(
    portfolio_id: UUID,
    model: str = Query("ff3", description="ff3 or ff5"),
    days: int = Query(365, ge=60, le=2520),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Calculate Fama-French factor exposures for a portfolio."""
    result = await calculate_factor_exposures(conn, portfolio_id, model, days)
    return {
        "portfolio_id": result.portfolio_id,
        "model": result.model,
        "alpha": result.alpha,
        "alpha_t_stat": result.alpha_t_stat,
        "alpha_p_value": result.alpha_p_value,
        "r_squared": result.r_squared,
        "adj_r_squared": result.adj_r_squared,
        "exposures": [
            {"factor_name": e.factor_name, "beta": e.beta, "t_stat": e.t_stat, "p_value": e.p_value}
            for e in result.exposures
        ],
        "period_days": result.period_days,
        "ai_interpretation": result.ai_interpretation,
        "success": result.success,
        "message": result.message,
    }


@router.get("/asset/{asset_id}")
async def asset_factors_endpoint(
    asset_id: UUID,
    model: str = Query("ff3", description="ff3 or ff5"),
    days: int = Query(365, ge=60, le=2520),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Calculate factor exposures for a single asset."""
    result = await calculate_asset_factor_exposure(conn, asset_id, model, days)
    return {
        "asset_id": result.asset_id,
        "symbol": result.symbol,
        "model": result.model,
        "alpha": result.alpha,
        "alpha_t_stat": result.alpha_t_stat,
        "r_squared": result.r_squared,
        "exposures": [
            {"factor_name": e.factor_name, "beta": e.beta, "t_stat": e.t_stat, "p_value": e.p_value}
            for e in result.exposures
        ],
        "success": result.success,
        "message": result.message,
    }
