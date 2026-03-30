"""
Pythia Router — Portfolio Rebalancing + Alpha + Risk Budget
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
import asyncpg
from db import get_conn
from services.rebalance_service import generate_rebalance_plan, get_drift
from services.alpha_service import generate_alpha_signals
from services.risk_budget_service import allocate_risk_budget

router = APIRouter(tags=["Rebalance & Risk"])


# ── Alpha Signals ─────────────────────────────────────────
@router.get("/api/signals/{asset_id}/alpha")
async def alpha_endpoint(
    asset_id: UUID,
    days: int = Query(500, ge=120, le=2000),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await generate_alpha_signals(conn, asset_id, days)
    return {
        "asset_id": result.asset_id,
        "symbol": result.symbol,
        "predicted_direction": result.predicted_direction,
        "probability": result.probability,
        "feature_importance": result.feature_importance,
        "model_accuracy": result.model_accuracy,
        "training_samples": result.training_samples,
        "success": result.success,
        "message": result.message,
    }


# ── Rebalancing ───────────────────────────────────────────
@router.get("/api/rebalance/{portfolio_id}/plan")
async def rebalance_plan_endpoint(
    portfolio_id: UUID,
    method: str = Query("equal_weight", description="equal_weight | risk_parity"),
    threshold: float = Query(0.05, ge=0.01, le=0.20),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await generate_rebalance_plan(conn, portfolio_id, method, threshold)
    return {
        "portfolio_id": result.portfolio_id,
        "plan_type": result.plan_type,
        "total_value": result.total_value,
        "trades": [
            {
                "asset_id": t.asset_id, "symbol": t.symbol,
                "current_weight": t.current_weight, "target_weight": t.target_weight,
                "drift": t.drift, "action": t.action, "trade_value": t.trade_value,
            }
            for t in result.trades
        ],
        "max_drift": result.max_drift,
        "estimated_cost": result.estimated_cost,
        "needs_rebalance": result.needs_rebalance,
        "success": result.success,
        "message": result.message,
    }


@router.get("/api/rebalance/{portfolio_id}/drift")
async def drift_endpoint(
    portfolio_id: UUID,
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await get_drift(conn, portfolio_id)


# ── Risk Budget ───────────────────────────────────────────
@router.get("/api/risk/{portfolio_id}/budget")
async def risk_budget_endpoint(
    portfolio_id: UUID,
    total_budget: float = Query(0.02, ge=0.005, le=0.10),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await allocate_risk_budget(conn, portfolio_id, total_budget)
    return {
        "portfolio_id": result.portfolio_id,
        "total_budget": result.total_budget,
        "allocations": result.allocations,
        "utilization": result.utilization,
        "regime": result.regime,
        "ai_advice": result.ai_advice,
        "success": result.success,
        "message": result.message,
    }
