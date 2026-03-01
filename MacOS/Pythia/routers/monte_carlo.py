"""
Pythia Router — Monte Carlo Simulation
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.monte_carlo_service import run_monte_carlo

router = APIRouter(prefix="/api/monte-carlo", tags=["Monte Carlo"])


@router.get("/{asset_id}/simulate")
async def simulate(
    asset_id: UUID,
    n_simulations: int = Query(10000, ge=100, le=100000),
    time_steps: int = Query(252, ge=10, le=756),
    lookback_days: int = Query(365, ge=60, le=3650),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await run_monte_carlo(conn, asset_id, n_simulations, time_steps, lookback_days)
    return {
        "symbol": result.symbol,
        "current_price": result.current_price,
        "n_simulations": result.n_simulations,
        "time_steps": result.time_steps,
        "statistics": {
            "mean_final_price": result.mean_final_price,
            "median_final_price": result.median_final_price,
            "std_final_price": result.std_final_price,
            "percentile_5": result.percentile_5,
            "percentile_25": result.percentile_25,
            "percentile_75": result.percentile_75,
            "percentile_95": result.percentile_95,
            "prob_above_current": result.prob_above_current,
        },
        "parameters": {
            "expected_return": result.expected_return,
            "volatility": result.volatility,
        },
        "sample_paths": result.sample_paths,
        "percentile_bands": result.percentile_bands,
        "final_distribution": result.final_distribution,
        "success": result.success,
        "message": result.message,
    }
