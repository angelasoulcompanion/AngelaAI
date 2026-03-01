"""
Pythia Router — Backtesting
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.backtest_service import run_sma_backtest

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])


@router.get("/{asset_id}/sma")
async def sma_backtest(
    asset_id: UUID,
    short_window: int = Query(20, ge=5, le=100),
    long_window: int = Query(50, ge=10, le=300),
    initial_capital: float = Query(1_000_000, ge=10000),
    days: int = Query(730, ge=60, le=3650),
    conn: asyncpg.Connection = Depends(get_conn),
):
    end_date = date.today()
    start_date = date.today()
    from datetime import timedelta
    start_date = end_date - timedelta(days=days)

    result = await run_sma_backtest(
        conn, asset_id, short_window, long_window, initial_capital, start_date, end_date
    )
    return {
        "strategy_name": result.strategy_name,
        "symbol": result.symbol,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "initial_capital": result.initial_capital,
        "final_value": result.final_value,
        "total_return": result.total_return,
        "annualized_return": result.annualized_return,
        "max_drawdown": result.max_drawdown,
        "sharpe_ratio": result.sharpe_ratio,
        "n_trades": result.n_trades,
        "win_rate": result.win_rate,
        "benchmark_return": result.benchmark_return,
        "excess_return": result.excess_return,
        "equity_curve": result.equity_curve,
        "trades": result.trades,
        "success": result.success,
        "message": result.message,
    }
