"""
Pythia — Stress Test Service (ported from CQFOracle)
Scenario analysis: predefined + custom + sensitivity.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from config import PythiaConfig

TRADING_DAYS = PythiaConfig.TRADING_DAYS_PER_YEAR

# Predefined stress scenarios
PREDEFINED_SCENARIOS: dict[str, dict] = {
    "market_crash": {
        "name": "Market Crash (2008-style)",
        "description": "Broad market decline of 30%",
        "default_shock": -0.30,
        "sector_shocks": {
            "Financials": -0.45,
            "Real Estate": -0.40,
            "Technology": -0.35,
            "Consumer Discretionary": -0.35,
            "Industrials": -0.30,
            "Energy": -0.25,
            "Consumer Staples": -0.15,
            "Health Care": -0.15,
            "Utilities": -0.10,
        },
    },
    "tech_selloff": {
        "name": "Tech Sector Selloff",
        "description": "Technology sector drops 35%, others mildly affected",
        "default_shock": -0.10,
        "sector_shocks": {
            "Technology": -0.35,
            "Communication Services": -0.25,
            "Consumer Discretionary": -0.15,
        },
    },
    "interest_rate_shock": {
        "name": "Interest Rate Shock (+300bps)",
        "description": "Rapid rate increase hurts growth/RE, helps financials",
        "default_shock": -0.10,
        "sector_shocks": {
            "Real Estate": -0.25,
            "Utilities": -0.20,
            "Technology": -0.15,
            "Financials": 0.05,
        },
    },
    "currency_crisis": {
        "name": "Currency Crisis",
        "description": "THB depreciation 20%, hurts importers, helps exporters",
        "default_shock": -0.15,
        "sector_shocks": {
            "Consumer Staples": -0.20,
            "Energy": -0.10,
            "Industrials": 0.05,
        },
    },
    "pandemic": {
        "name": "Pandemic Shock (COVID-style)",
        "description": "Severe market selloff with sector rotation",
        "default_shock": -0.35,
        "sector_shocks": {
            "Energy": -0.50,
            "Industrials": -0.40,
            "Consumer Discretionary": -0.40,
            "Real Estate": -0.30,
            "Financials": -0.30,
            "Technology": -0.15,
            "Health Care": 0.05,
            "Consumer Staples": -0.10,
        },
    },
    "mild_correction": {
        "name": "Mild Correction (-10%)",
        "description": "Orderly market pullback",
        "default_shock": -0.10,
        "sector_shocks": {},
    },
}


@dataclass
class StressTestResult:
    scenario_name: str
    description: str
    portfolio_value_before: float
    portfolio_value_after: float
    portfolio_pnl: float
    portfolio_pnl_pct: float
    asset_impacts: list[dict]
    worst_asset: Optional[dict] = None
    best_asset: Optional[dict] = None
    success: bool = True
    message: str = ""


async def _get_holdings_with_sector(
    conn: asyncpg.Connection, portfolio_id: UUID
) -> list[dict]:
    """Get holdings with sector info."""
    rows = await conn.fetch("""
        SELECT h.asset_id, a.symbol, a.name, a.sector,
               h.weight, h.market_value
        FROM portfolio_holdings h
        JOIN assets a ON h.asset_id = a.asset_id
        WHERE h.portfolio_id = $1
    """, portfolio_id)
    return [dict(r) for r in rows]


async def run_stress_test(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    scenario_name: str,
) -> StressTestResult:
    """Run a predefined stress scenario."""
    if scenario_name not in PREDEFINED_SCENARIOS:
        return StressTestResult(
            scenario_name=scenario_name, description="",
            portfolio_value_before=0, portfolio_value_after=0,
            portfolio_pnl=0, portfolio_pnl_pct=0,
            asset_impacts=[], success=False,
            message=f"Unknown scenario: {scenario_name}. Available: {list(PREDEFINED_SCENARIOS.keys())}",
        )

    scenario = PREDEFINED_SCENARIOS[scenario_name]
    holdings = await _get_holdings_with_sector(conn, portfolio_id)
    if not holdings:
        return StressTestResult(
            scenario_name=scenario_name, description=scenario["description"],
            portfolio_value_before=0, portfolio_value_after=0,
            portfolio_pnl=0, portfolio_pnl_pct=0,
            asset_impacts=[], success=False, message="No holdings",
        )

    return _apply_shocks(holdings, scenario_name, scenario["description"],
                         scenario["default_shock"], scenario["sector_shocks"])


async def run_custom_scenario(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    name: str,
    default_shock: float,
    asset_shocks: Optional[dict[str, float]] = None,
    sector_shocks: Optional[dict[str, float]] = None,
) -> StressTestResult:
    """Run a custom stress scenario."""
    holdings = await _get_holdings_with_sector(conn, portfolio_id)
    if not holdings:
        return StressTestResult(
            scenario_name=name, description="Custom scenario",
            portfolio_value_before=0, portfolio_value_after=0,
            portfolio_pnl=0, portfolio_pnl_pct=0,
            asset_impacts=[], success=False, message="No holdings",
        )

    return _apply_shocks(
        holdings, name, "Custom scenario",
        default_shock, sector_shocks or {},
        asset_shocks or {},
    )


async def run_all_scenarios(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
) -> list[StressTestResult]:
    """Run all predefined scenarios."""
    results = []
    for scenario_name in PREDEFINED_SCENARIOS:
        result = await run_stress_test(conn, portfolio_id, scenario_name)
        results.append(result)
    return results


async def sensitivity_analysis(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    shock_range: Optional[list[float]] = None,
) -> dict:
    """Run sensitivity analysis across a range of shocks."""
    if shock_range is None:
        shock_range = [-0.30, -0.25, -0.20, -0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15]

    holdings = await _get_holdings_with_sector(conn, portfolio_id)
    if not holdings:
        return {"error": "No holdings"}

    portfolio_value = sum(float(h.get("market_value") or 0) for h in holdings)
    if portfolio_value == 0:
        portfolio_value = 1_000_000

    points = []
    for shock in shock_range:
        pnl = portfolio_value * shock
        points.append({
            "shock_pct": round(shock, 4),
            "portfolio_value": round(portfolio_value + pnl, 2),
            "pnl": round(pnl, 2),
        })

    return {
        "portfolio_value": round(portfolio_value, 2),
        "shock_range": shock_range,
        "results": points,
    }


def _apply_shocks(
    holdings: list[dict],
    scenario_name: str,
    description: str,
    default_shock: float,
    sector_shocks: dict[str, float],
    asset_shocks: Optional[dict[str, float]] = None,
) -> StressTestResult:
    """Apply shock values to holdings and compute P&L."""
    if asset_shocks is None:
        asset_shocks = {}

    portfolio_value = sum(float(h.get("market_value") or 0) for h in holdings)
    if portfolio_value == 0:
        portfolio_value = 1_000_000
        for h in holdings:
            w = float(h.get("weight") or 0)
            h["market_value"] = portfolio_value * w

    impacts = []
    total_pnl = 0.0

    for h in holdings:
        symbol = h["symbol"]
        sector = h.get("sector") or ""
        mv = float(h.get("market_value") or 0)

        # Priority: asset-specific > sector > default
        if symbol in asset_shocks:
            shock = asset_shocks[symbol]
        elif sector in sector_shocks:
            shock = sector_shocks[sector]
        else:
            shock = default_shock

        pnl = mv * shock
        total_pnl += pnl

        impacts.append({
            "symbol": symbol,
            "name": h.get("name", ""),
            "sector": sector,
            "market_value": round(mv, 2),
            "shock_pct": round(shock, 4),
            "pnl": round(pnl, 2),
            "value_after": round(mv + pnl, 2),
        })

    # Sort by PnL to find worst/best
    impacts.sort(key=lambda x: x["pnl"])
    worst = impacts[0] if impacts else None
    best = impacts[-1] if impacts else None

    port_after = portfolio_value + total_pnl
    port_pnl_pct = total_pnl / portfolio_value if portfolio_value > 0 else 0

    return StressTestResult(
        scenario_name=scenario_name,
        description=description,
        portfolio_value_before=round(portfolio_value, 2),
        portfolio_value_after=round(port_after, 2),
        portfolio_pnl=round(total_pnl, 2),
        portfolio_pnl_pct=round(port_pnl_pct, 6),
        asset_impacts=impacts,
        worst_asset=worst,
        best_asset=best,
    )
