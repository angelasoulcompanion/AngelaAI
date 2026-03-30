"""
Pythia — Portfolio Rebalancing Service
Target weight, threshold drift, calendar-based rebalancing.
"""
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from config import PythiaConfig


@dataclass
class RebalanceTrade:
    asset_id: str
    symbol: str
    current_weight: float
    target_weight: float
    drift: float
    action: str  # buy, sell, hold
    trade_value: float = 0.0


@dataclass
class RebalancePlan:
    portfolio_id: str
    plan_type: str
    total_value: float = 0.0
    trades: list[RebalanceTrade] = field(default_factory=list)
    max_drift: float = 0.0
    estimated_cost: float = 0.0
    needs_rebalance: bool = False
    success: bool = True
    message: str = ""


async def generate_rebalance_plan(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    method: str = "equal_weight",
    threshold: float = 0.05,
) -> RebalancePlan:
    """Generate rebalance plan comparing current vs target weights."""
    # Get current holdings with values
    holdings = await conn.fetch(
        """SELECT h.asset_id, h.quantity, a.symbol,
                  (SELECT close_price FROM historical_prices
                   WHERE asset_id = h.asset_id ORDER BY date DESC LIMIT 1) as price
           FROM portfolio_holdings h
           JOIN assets a ON a.asset_id = h.asset_id
           WHERE h.portfolio_id = $1""",
        portfolio_id,
    )

    if not holdings:
        return RebalancePlan(
            portfolio_id=str(portfolio_id), plan_type=method,
            success=False, message="No holdings found",
        )

    # Calculate current weights
    values = {}
    symbols = {}
    for h in holdings:
        aid = str(h["asset_id"])
        price = float(h["price"] or 0)
        qty = float(h["quantity"] or 0)
        values[aid] = price * qty
        symbols[aid] = h["symbol"]

    total_value = sum(values.values())
    if total_value <= 0:
        return RebalancePlan(
            portfolio_id=str(portfolio_id), plan_type=method,
            success=False, message="Portfolio value is zero",
        )

    current_weights = {aid: v / total_value for aid, v in values.items()}

    # Calculate target weights
    if method == "equal_weight":
        n = len(current_weights)
        target_weights = {aid: 1.0 / n for aid in current_weights}
    elif method == "risk_parity":
        from services.position_sizing_service import risk_parity_weights
        asset_ids = [UUID(aid) for aid in current_weights.keys()]
        rp = await risk_parity_weights(conn, asset_ids)
        if rp.success:
            target_weights = rp.weights
        else:
            target_weights = {aid: 1.0 / len(current_weights) for aid in current_weights}
    elif method == "market_cap":
        # Use current weights as proxy (already market-cap-ish)
        target_weights = current_weights.copy()
    else:
        target_weights = {aid: 1.0 / len(current_weights) for aid in current_weights}

    # Calculate trades
    trades = []
    max_drift = 0.0
    total_trade_value = 0.0

    for aid in current_weights:
        cw = current_weights.get(aid, 0)
        tw = target_weights.get(aid, 0)
        drift = cw - tw

        if abs(drift) > 0.001:
            trade_value = abs(drift) * total_value
            action = "sell" if drift > 0 else "buy"
        else:
            trade_value = 0
            action = "hold"

        trades.append(RebalanceTrade(
            asset_id=aid,
            symbol=symbols.get(aid, ""),
            current_weight=round(cw, 4),
            target_weight=round(tw, 4),
            drift=round(drift, 4),
            action=action,
            trade_value=round(trade_value, 2),
        ))

        max_drift = max(max_drift, abs(drift))
        total_trade_value += trade_value

    # Estimated transaction cost
    cost_bps = PythiaConfig.DEFAULT_TRANSACTION_COST_BPS
    estimated_cost = total_trade_value * cost_bps / 10000

    needs_rebalance = max_drift > threshold

    # Sort by absolute drift
    trades.sort(key=lambda t: abs(t.drift), reverse=True)

    plan = RebalancePlan(
        portfolio_id=str(portfolio_id),
        plan_type=method,
        total_value=round(total_value, 2),
        trades=trades,
        max_drift=round(max_drift, 4),
        estimated_cost=round(estimated_cost, 2),
        needs_rebalance=needs_rebalance,
    )

    # Store plan in DB
    try:
        await conn.execute(
            """INSERT INTO rebalance_plans
               (portfolio_id, plan_type, current_weights, target_weights, trades_needed, estimated_cost)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            portfolio_id, method,
            json.dumps(current_weights),
            json.dumps(target_weights),
            json.dumps([{"asset_id": t.asset_id, "action": t.action, "value": t.trade_value} for t in trades]),
            estimated_cost,
        )
    except Exception:
        pass

    return plan


async def get_drift(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
) -> dict:
    """Get current portfolio drift from equal-weight target."""
    plan = await generate_rebalance_plan(conn, portfolio_id, method="equal_weight")
    return {
        "portfolio_id": str(portfolio_id),
        "max_drift": plan.max_drift,
        "needs_rebalance": plan.needs_rebalance,
        "threshold": PythiaConfig.REBALANCE_DRIFT_THRESHOLD,
        "holdings": len(plan.trades),
    }
