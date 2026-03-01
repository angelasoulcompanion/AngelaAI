"""
Pythia Router — Risk Management
VaR, Stress Tests, Risk Decomposition.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.var_service import calculate_var, calculate_component_var
from services.stress_test_service import (
    run_stress_test,
    run_custom_scenario,
    run_all_scenarios,
    sensitivity_analysis,
    PREDEFINED_SCENARIOS,
)

router = APIRouter(prefix="/api/risk", tags=["Risk"])


# ── VaR ──────────────────────────────────────────────────

@router.get("/{portfolio_id}/var")
async def var_endpoint(
    portfolio_id: UUID,
    method: str = Query("historical", description="historical | parametric | monte_carlo"),
    confidence: float = Query(0.95, ge=0.9, le=0.999),
    holding_period: int = Query(1, ge=1, le=30),
    lookback_days: int = Query(252, ge=30, le=2520),
    n_simulations: int = Query(10000, ge=1000, le=100000),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await calculate_var(
        conn, portfolio_id, method, confidence, holding_period, lookback_days, n_simulations
    )
    return {
        "portfolio_id": str(portfolio_id),
        "method": result.method,
        "confidence_level": result.confidence_level,
        "holding_period": result.holding_period,
        "portfolio_value": result.portfolio_value,
        "var_value": result.var_value,
        "var_percent": result.var_percent,
        "cvar_value": result.cvar_value,
        "cvar_percent": result.cvar_percent,
        "success": result.success,
        "message": result.message,
    }


@router.get("/{portfolio_id}/component-var")
async def component_var_endpoint(
    portfolio_id: UUID,
    confidence: float = Query(0.95, ge=0.9, le=0.999),
    days: int = Query(252, ge=30, le=2520),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await calculate_component_var(conn, portfolio_id, confidence, days)
    return result


# ── Stress Tests ─────────────────────────────────────────

@router.get("/scenarios")
async def list_scenarios():
    """List all predefined stress scenarios."""
    return {
        "scenarios": [
            {"key": k, "name": v["name"], "description": v["description"], "default_shock": v["default_shock"]}
            for k, v in PREDEFINED_SCENARIOS.items()
        ]
    }


@router.get("/{portfolio_id}/stress-test/{scenario_name}")
async def stress_test(
    portfolio_id: UUID,
    scenario_name: str,
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await run_stress_test(conn, portfolio_id, scenario_name)
    return {
        "scenario_name": result.scenario_name,
        "description": result.description,
        "portfolio_value_before": result.portfolio_value_before,
        "portfolio_value_after": result.portfolio_value_after,
        "portfolio_pnl": result.portfolio_pnl,
        "portfolio_pnl_pct": result.portfolio_pnl_pct,
        "asset_impacts": result.asset_impacts,
        "worst_asset": result.worst_asset,
        "best_asset": result.best_asset,
        "success": result.success,
        "message": result.message,
    }


@router.get("/{portfolio_id}/stress-test-all")
async def stress_test_all(
    portfolio_id: UUID,
    conn: asyncpg.Connection = Depends(get_conn),
):
    results = await run_all_scenarios(conn, portfolio_id)
    return {
        "portfolio_id": str(portfolio_id),
        "scenarios": [
            {
                "scenario_name": r.scenario_name,
                "portfolio_pnl": r.portfolio_pnl,
                "portfolio_pnl_pct": r.portfolio_pnl_pct,
                "worst_asset": r.worst_asset,
            }
            for r in results
        ],
    }


@router.get("/{portfolio_id}/sensitivity")
async def sensitivity(
    portfolio_id: UUID,
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await sensitivity_analysis(conn, portfolio_id)
    return result
