"""
Pythia Router — Performance Metrics
Comprehensive risk/return metrics, drawdown analysis, rolling metrics.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.risk_metrics_service import (
    calculate_portfolio_metrics,
    calculate_portfolio_metrics_with_benchmark,
    get_drawdown_analysis,
    calculate_rolling_metrics,
)

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("/{portfolio_id}")
async def portfolio_metrics(
    portfolio_id: UUID,
    days: int = Query(365, ge=30, le=3650),
    risk_free_rate: Optional[float] = Query(None),
    conn: asyncpg.Connection = Depends(get_conn),
):
    metrics = await calculate_portfolio_metrics(conn, portfolio_id, days, risk_free_rate)
    return {
        "portfolio_id": str(portfolio_id),
        "success": metrics.success,
        "message": metrics.message,
        "returns": {
            "total_return": metrics.total_return,
            "annualized_return": metrics.annualized_return,
        },
        "risk": {
            "volatility": metrics.volatility,
            "downside_deviation": metrics.downside_deviation,
            "max_drawdown": metrics.max_drawdown,
            "max_drawdown_duration": metrics.max_drawdown_duration,
            "var_95": metrics.var_95,
            "var_99": metrics.var_99,
            "cvar_95": metrics.cvar_95,
        },
        "ratios": {
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "calmar_ratio": metrics.calmar_ratio,
            "treynor_ratio": metrics.treynor_ratio,
            "information_ratio": metrics.information_ratio,
        },
        "distribution": {
            "skewness": metrics.skewness,
            "excess_kurtosis": metrics.excess_kurtosis,
        },
        "market": {
            "beta": metrics.beta,
            "alpha": metrics.alpha,
            "r_squared": metrics.r_squared,
            "tracking_error": metrics.tracking_error,
        },
        "meta": {
            "n_observations": metrics.n_observations,
            "period_days": metrics.period_days,
        },
    }


@router.get("/{portfolio_id}/benchmark")
async def benchmark_comparison(
    portfolio_id: UUID,
    benchmark_asset_id: UUID = Query(..., description="Asset ID of the benchmark"),
    days: int = Query(365, ge=30, le=3650),
    risk_free_rate: Optional[float] = Query(None),
    conn: asyncpg.Connection = Depends(get_conn),
):
    metrics = await calculate_portfolio_metrics_with_benchmark(
        conn, portfolio_id, benchmark_asset_id, days, risk_free_rate
    )
    return {
        "portfolio_id": str(portfolio_id),
        "benchmark_asset_id": str(benchmark_asset_id),
        "success": metrics.success,
        "message": metrics.message,
        "annualized_return": metrics.annualized_return,
        "volatility": metrics.volatility,
        "sharpe_ratio": metrics.sharpe_ratio,
        "sortino_ratio": metrics.sortino_ratio,
        "beta": metrics.beta,
        "alpha": metrics.alpha,
        "r_squared": metrics.r_squared,
        "tracking_error": metrics.tracking_error,
        "information_ratio": metrics.information_ratio,
        "treynor_ratio": metrics.treynor_ratio,
        "max_drawdown": metrics.max_drawdown,
    }


@router.get("/{portfolio_id}/drawdown")
async def drawdown_analysis(
    portfolio_id: UUID,
    days: int = Query(365, ge=30, le=3650),
    top_n: int = Query(5, ge=1, le=20),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await get_drawdown_analysis(conn, portfolio_id, days, top_n)
    return result


@router.get("/{portfolio_id}/rolling")
async def rolling_metrics(
    portfolio_id: UUID,
    window: int = Query(60, ge=20, le=252),
    days: int = Query(365, ge=60, le=3650),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await calculate_rolling_metrics(conn, portfolio_id, window, days)
    return result
