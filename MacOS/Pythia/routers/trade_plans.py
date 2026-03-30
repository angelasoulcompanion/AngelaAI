"""
Pythia Router — Trade Plan Generator
AI-powered trade plans with entry/SL/TP levels.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.trade_plan_service import generate_trade_plan, list_trade_plans

router = APIRouter(prefix="/api/trade-plans", tags=["Trade Plans"])


@router.post("/{asset_id}")
async def generate_plan_endpoint(
    asset_id: UUID,
    risk_per_trade: float = Query(0.02, ge=0.005, le=0.10),
    conn: asyncpg.Connection = Depends(get_conn),
):
    plan = await generate_trade_plan(conn, asset_id, risk_per_trade)
    return {
        "plan_id": plan.plan_id,
        "asset_id": plan.asset_id,
        "symbol": plan.symbol,
        "direction": plan.direction,
        "current_price": plan.current_price,
        "entry_price": plan.entry_price,
        "stop_loss": plan.stop_loss,
        "take_profit_1": plan.take_profit_1,
        "take_profit_2": plan.take_profit_2,
        "take_profit_3": plan.take_profit_3,
        "position_size_pct": plan.position_size_pct,
        "risk_reward": plan.risk_reward,
        "risk_pct": plan.risk_pct,
        "rationale": plan.rationale,
        "regime": plan.regime,
        "support_levels": plan.support_levels,
        "resistance_levels": plan.resistance_levels,
        "signals_summary": plan.signals_summary,
        "success": plan.success,
        "message": plan.message,
    }


@router.get("/")
async def list_plans_endpoint(
    status: str = Query("active"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    plans = await list_trade_plans(conn, status)
    return {"plans": plans, "count": len(plans)}
