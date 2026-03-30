"""
Pythia Router — Strategy Builder
CRUD + evaluation for composable trading strategies.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
import asyncpg

from db import get_conn
from services.strategy_service import (
    create_strategy, list_strategies, get_strategy,
    update_strategy, delete_strategy, evaluate_strategy,
    PRESET_STRATEGIES,
)

router = APIRouter(prefix="/api/strategies", tags=["Strategy Builder"])


class StrategyCreateRequest(BaseModel):
    name: str
    strategy_type: str = "custom"
    description: str = ""
    entry_rules: list[dict] = []
    exit_rules: list[dict] = []
    filters: list[dict] = []
    position_sizing: dict = {"method": "fixed", "size_pct": 0.10}
    transaction_cost_bps: int = 10


class EvaluateRequest(BaseModel):
    asset_id: UUID
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    initial_capital: float = 100000


@router.get("/")
async def list_strategies_endpoint(conn: asyncpg.Connection = Depends(get_conn)):
    strategies = await list_strategies(conn)
    return {"strategies": strategies, "count": len(strategies)}


@router.get("/presets")
async def list_presets_endpoint():
    return {
        "presets": [
            {"key": k, "name": v["name"], "type": v["strategy_type"], "description": v["description"]}
            for k, v in PRESET_STRATEGIES.items()
        ]
    }


@router.post("/from-preset/{preset_key}")
async def create_from_preset(
    preset_key: str,
    conn: asyncpg.Connection = Depends(get_conn),
):
    if preset_key not in PRESET_STRATEGIES:
        return {"success": False, "message": f"Preset '{preset_key}' not found"}
    config = PRESET_STRATEGIES[preset_key].copy()
    sid = await create_strategy(conn, config)
    return {"strategy_id": sid, "name": config["name"], "success": True}


@router.post("/")
async def create_strategy_endpoint(
    req: StrategyCreateRequest,
    conn: asyncpg.Connection = Depends(get_conn),
):
    config = req.dict()
    sid = await create_strategy(conn, config)
    return {"strategy_id": sid, "success": True}


@router.get("/{strategy_id}")
async def get_strategy_endpoint(
    strategy_id: UUID,
    conn: asyncpg.Connection = Depends(get_conn),
):
    strategy = await get_strategy(conn, strategy_id)
    if not strategy:
        return {"success": False, "message": "Strategy not found"}
    return {**strategy, "success": True}


@router.put("/{strategy_id}")
async def update_strategy_endpoint(
    strategy_id: UUID,
    req: StrategyCreateRequest,
    conn: asyncpg.Connection = Depends(get_conn),
):
    ok = await update_strategy(conn, strategy_id, req.dict())
    return {"success": ok}


@router.delete("/{strategy_id}")
async def delete_strategy_endpoint(
    strategy_id: UUID,
    conn: asyncpg.Connection = Depends(get_conn),
):
    ok = await delete_strategy(conn, strategy_id)
    return {"success": ok}


@router.post("/{strategy_id}/evaluate")
async def evaluate_strategy_endpoint(
    strategy_id: UUID,
    req: EvaluateRequest,
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await evaluate_strategy(
        conn, strategy_id, req.asset_id,
        req.start_date, req.end_date, req.initial_capital,
    )
    return {
        "strategy_id": result.strategy_id,
        "strategy_name": result.strategy_name,
        "total_return": result.total_return,
        "annualized_return": result.annualized_return,
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown": result.max_drawdown,
        "win_rate": result.win_rate,
        "profit_factor": result.profit_factor,
        "total_trades": result.total_trades,
        "avg_holding_days": result.avg_holding_days,
        "trades": [
            {
                "entry_date": t.entry_date, "exit_date": t.exit_date,
                "direction": t.direction, "entry_price": t.entry_price,
                "exit_price": t.exit_price, "pnl_pct": t.pnl_pct,
                "pnl_value": t.pnl_value, "holding_days": t.holding_days,
                "exit_reason": t.exit_reason,
            }
            for t in result.trades
        ],
        "equity_curve": result.equity_curve,
        "success": result.success,
        "message": result.message,
    }
