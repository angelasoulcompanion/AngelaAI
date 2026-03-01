"""
Pythia — Value at Risk Service (ported from CQFOracle)
Historical, Parametric, and Monte Carlo VaR + CVaR.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np
from scipy.stats import norm

from config import PythiaConfig
from services.optimization_service import get_returns_matrix

TRADING_DAYS = PythiaConfig.TRADING_DAYS_PER_YEAR


@dataclass
class VaRResult:
    method: str
    confidence_level: float
    holding_period: int
    portfolio_value: float
    var_value: float
    var_percent: float
    cvar_value: float
    cvar_percent: float
    success: bool
    message: str = ""


async def calculate_var(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    method: str = "historical",
    confidence_level: float = 0.95,
    holding_period: int = 1,
    lookback_days: int = 252,
    n_simulations: int = 10000,
) -> VaRResult:
    """Calculate VaR and CVaR for a portfolio."""
    # Get holdings
    rows = await conn.fetch("""
        SELECT h.asset_id, h.weight, h.market_value
        FROM portfolio_holdings h
        WHERE h.portfolio_id = $1
    """, portfolio_id)
    if not rows:
        return VaRResult(method, confidence_level, holding_period, 0, 0, 0, 0, 0, False, "No holdings")

    asset_ids = [r["asset_id"] for r in rows]
    weights = np.array([float(r["weight"]) for r in rows])
    portfolio_value = sum(float(r["market_value"] or 0) for r in rows)
    if portfolio_value == 0:
        portfolio_value = 1_000_000  # Default 1M if no market values

    # Normalize weights
    w_sum = weights.sum()
    if w_sum > 0:
        weights = weights / w_sum

    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)
    returns_matrix, _ = await get_returns_matrix(conn, asset_ids, start_date, end_date)

    if returns_matrix.size == 0:
        return VaRResult(method, confidence_level, holding_period, portfolio_value, 0, 0, 0, 0, False, "Insufficient data")

    # Portfolio returns
    port_returns = returns_matrix @ weights

    if method == "historical":
        var_pct, cvar_pct = _historical_var(port_returns, confidence_level, holding_period)
    elif method == "parametric":
        var_pct, cvar_pct = _parametric_var(port_returns, confidence_level, holding_period)
    elif method == "monte_carlo":
        var_pct, cvar_pct = _monte_carlo_var(port_returns, confidence_level, holding_period, n_simulations)
    else:
        return VaRResult(method, confidence_level, holding_period, portfolio_value, 0, 0, 0, 0, False, f"Unknown method: {method}")

    var_value = portfolio_value * abs(var_pct)
    cvar_value = portfolio_value * abs(cvar_pct)

    return VaRResult(
        method=method,
        confidence_level=confidence_level,
        holding_period=holding_period,
        portfolio_value=portfolio_value,
        var_value=round(var_value, 2),
        var_percent=round(var_pct, 6),
        cvar_value=round(cvar_value, 2),
        cvar_percent=round(cvar_pct, 6),
        success=True,
    )


def _historical_var(returns: np.ndarray, confidence: float, holding_period: int) -> tuple[float, float]:
    """Historical simulation VaR."""
    if holding_period > 1:
        # Multi-day returns via rolling window
        multi_day = np.array([
            np.sum(returns[i:i + holding_period])
            for i in range(len(returns) - holding_period + 1)
        ])
    else:
        multi_day = returns

    sorted_returns = np.sort(multi_day)
    index = int((1 - confidence) * len(sorted_returns))
    var_pct = float(sorted_returns[max(index, 0)])
    cvar_pct = float(np.mean(sorted_returns[:max(index, 1)]))
    return var_pct, cvar_pct


def _parametric_var(returns: np.ndarray, confidence: float, holding_period: int) -> tuple[float, float]:
    """Variance-Covariance (parametric) VaR assuming normal distribution."""
    mu = float(np.mean(returns))
    sigma = float(np.std(returns))
    z = norm.ppf(1 - confidence)

    # Scale for holding period
    var_pct = mu * holding_period + z * sigma * np.sqrt(holding_period)

    # CVaR for normal distribution
    pdf_z = norm.pdf(z)
    cvar_pct = mu * holding_period - sigma * np.sqrt(holding_period) * pdf_z / (1 - confidence)
    return float(var_pct), float(cvar_pct)


def _monte_carlo_var(
    returns: np.ndarray, confidence: float, holding_period: int, n_sims: int
) -> tuple[float, float]:
    """Monte Carlo simulation VaR using GBM."""
    mu = float(np.mean(returns))
    sigma = float(np.std(returns))

    # Simulate paths
    np.random.seed(42)
    simulated = np.random.normal(mu, sigma, (n_sims, holding_period))
    cumulative = np.sum(simulated, axis=1)

    sorted_sims = np.sort(cumulative)
    index = int((1 - confidence) * n_sims)
    var_pct = float(sorted_sims[max(index, 0)])
    cvar_pct = float(np.mean(sorted_sims[:max(index, 1)]))
    return var_pct, cvar_pct


async def calculate_component_var(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    confidence_level: float = 0.95,
    days: int = 252,
) -> dict:
    """Calculate component VaR — VaR contribution per asset."""
    rows = await conn.fetch("""
        SELECT h.asset_id, a.symbol, h.weight
        FROM portfolio_holdings h
        JOIN assets a ON h.asset_id = a.asset_id
        WHERE h.portfolio_id = $1
    """, portfolio_id)
    if not rows:
        return {"error": "No holdings"}

    asset_ids = [r["asset_id"] for r in rows]
    symbols = [r["symbol"] for r in rows]
    weights = np.array([float(r["weight"]) for r in rows])
    w_sum = weights.sum()
    if w_sum > 0:
        weights = weights / w_sum

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    returns_matrix, _ = await get_returns_matrix(conn, asset_ids, start_date, end_date)

    if returns_matrix.size == 0:
        return {"error": "Insufficient data"}

    cov_matrix = np.cov(returns_matrix.T)
    port_vol = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)) * TRADING_DAYS))
    z = abs(norm.ppf(1 - confidence_level))

    # Marginal VaR = z * (Cov * w) / port_vol
    marginal_var = z * (cov_matrix @ weights * np.sqrt(TRADING_DAYS)) / port_vol if port_vol > 0 else np.zeros(len(weights))
    # Component VaR = w * marginal_var
    component_var = weights * marginal_var

    components = []
    for i, sym in enumerate(symbols):
        components.append({
            "symbol": sym,
            "weight": round(float(weights[i]), 4),
            "marginal_var": round(float(marginal_var[i]), 6),
            "component_var": round(float(component_var[i]), 6),
            "pct_contribution": round(float(component_var[i] / sum(component_var) * 100) if sum(component_var) > 0 else 0, 2),
        })

    return {
        "portfolio_var_pct": round(port_vol * z, 6),
        "components": components,
    }
