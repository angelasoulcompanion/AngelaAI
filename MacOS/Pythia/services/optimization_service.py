"""
Pythia — Portfolio Optimization Service (ported from CQFOracle)
Mean-Variance Optimization using scipy.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np
from scipy.optimize import minimize

from config import PythiaConfig

TRADING_DAYS = PythiaConfig.TRADING_DAYS_PER_YEAR


@dataclass
class OptimizationResult:
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    optimization_type: str
    success: bool
    message: str = ""


async def get_returns_matrix(
    conn: asyncpg.Connection,
    asset_ids: list[UUID],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> tuple[np.ndarray, list[str]]:
    """Get aligned returns matrix for multiple assets. Shape: (n_dates, n_assets)."""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    all_prices: dict[UUID, list[tuple[date, float]]] = {}
    for aid in asset_ids:
        rows = await conn.fetch("""
            SELECT date, close_price FROM historical_prices
            WHERE asset_id = $1 AND date BETWEEN $2 AND $3
            ORDER BY date
        """, aid, start_date, end_date)
        all_prices[aid] = [(r["date"], float(r["close_price"])) for r in rows]

    if not all_prices:
        return np.array([]), []

    # Common dates
    date_sets = [set(d for d, _ in prices) for prices in all_prices.values()]
    common_dates = sorted(set.intersection(*date_sets))
    if len(common_dates) < 2:
        return np.array([]), []

    # Build price matrix
    n_assets = len(asset_ids)
    n_dates = len(common_dates)
    price_matrix = np.zeros((n_dates, n_assets))
    for i, aid in enumerate(asset_ids):
        price_dict = {d: p for d, p in all_prices[aid]}
        for j, dt in enumerate(common_dates):
            price_matrix[j, i] = price_dict[dt]

    returns_matrix = np.diff(price_matrix, axis=0) / price_matrix[:-1]
    return returns_matrix, [d.isoformat() for d in common_dates[1:]]


def portfolio_stats(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = PythiaConfig.DEFAULT_RISK_FREE_RATE,
) -> tuple[float, float, float]:
    """Calculate annualized return, volatility, Sharpe ratio."""
    exp_return = float(np.sum(mean_returns * weights) * TRADING_DAYS)
    variance = float(np.dot(weights.T, np.dot(cov_matrix, weights)))
    vol = float(np.sqrt(variance * TRADING_DAYS))
    sharpe = (exp_return - risk_free_rate) / vol if vol > 0 else 0.0
    return exp_return, vol, sharpe


async def optimize_portfolio(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    optimization_type: str = "max_sharpe",
    risk_free_rate: float = PythiaConfig.DEFAULT_RISK_FREE_RATE,
    target_return: Optional[float] = None,
    days: int = 365,
) -> OptimizationResult:
    """Run portfolio optimization (max_sharpe, min_volatility, target_return)."""
    # Get holdings
    rows = await conn.fetch("""
        SELECT asset_id, weight FROM portfolio_holdings
        WHERE portfolio_id = $1
    """, portfolio_id)
    if not rows:
        return OptimizationResult({}, 0, 0, 0, optimization_type, False, "No holdings")

    asset_ids = [r["asset_id"] for r in rows]
    symbols_map = {}
    for aid in asset_ids:
        sym = await conn.fetchval("SELECT symbol FROM assets WHERE asset_id = $1", aid)
        symbols_map[str(aid)] = sym or str(aid)

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    returns_matrix, dates = await get_returns_matrix(conn, asset_ids, start_date, end_date)

    if returns_matrix.size == 0:
        return OptimizationResult({}, 0, 0, 0, optimization_type, False, "Insufficient price data")

    mean_returns = np.mean(returns_matrix, axis=0)
    cov_matrix = np.cov(returns_matrix.T)
    n = len(asset_ids)
    init_w = np.array([1 / n] * n)
    bounds = tuple((0, 1) for _ in range(n))
    cons = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]

    if optimization_type == "max_sharpe":
        def objective(w):
            r, v, _ = portfolio_stats(w, mean_returns, cov_matrix, risk_free_rate)
            return -(r - risk_free_rate) / v if v > 0 else 0
    elif optimization_type == "min_volatility":
        def objective(w):
            return np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)) * TRADING_DAYS)
    elif optimization_type == "target_return" and target_return is not None:
        def objective(w):
            return np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)) * TRADING_DAYS)
        cons.append({
            "type": "eq",
            "fun": lambda w: np.sum(mean_returns * w) * TRADING_DAYS - target_return
        })
    else:
        return OptimizationResult({}, 0, 0, 0, optimization_type, False, f"Unknown type: {optimization_type}")

    result = minimize(objective, init_w, method="SLSQP", bounds=bounds, constraints=cons,
                      options={"maxiter": PythiaConfig.OPTIMIZATION_MAX_ITERATIONS})

    if result.success:
        w = result.x
        exp_ret, vol, sharpe = portfolio_stats(w, mean_returns, cov_matrix, risk_free_rate)
        weights_dict = {symbols_map.get(str(aid), str(aid)): round(float(wt), 6)
                        for aid, wt in zip(asset_ids, w)}
        return OptimizationResult(weights_dict, exp_ret, vol, sharpe, optimization_type, True)
    else:
        return OptimizationResult({}, 0, 0, 0, optimization_type, False, str(result.message))


async def generate_efficient_frontier(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    n_points: int = 50,
    risk_free_rate: float = PythiaConfig.DEFAULT_RISK_FREE_RATE,
    days: int = 365,
) -> dict:
    """Generate efficient frontier points."""
    rows = await conn.fetch(
        "SELECT asset_id FROM portfolio_holdings WHERE portfolio_id = $1", portfolio_id
    )
    if not rows:
        return {"error": "No holdings", "points": []}

    asset_ids = [r["asset_id"] for r in rows]
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    returns_matrix, _ = await get_returns_matrix(conn, asset_ids, start_date, end_date)

    if returns_matrix.size == 0:
        return {"error": "Insufficient data", "points": []}

    mean_returns = np.mean(returns_matrix, axis=0)
    cov_matrix = np.cov(returns_matrix.T)
    n = len(asset_ids)

    # Generate target returns range
    min_ret = float(np.min(mean_returns)) * TRADING_DAYS
    max_ret = float(np.max(mean_returns)) * TRADING_DAYS
    target_returns = np.linspace(min_ret, max_ret, n_points)

    points = []
    for target in target_returns:
        def vol_obj(w):
            return np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)) * TRADING_DAYS)

        cons = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, t=target: np.sum(mean_returns * w) * TRADING_DAYS - t},
        ]
        bounds = tuple((0, 1) for _ in range(n))
        init_w = np.array([1 / n] * n)

        res = minimize(vol_obj, init_w, method="SLSQP", bounds=bounds, constraints=cons)
        if res.success:
            vol = float(vol_obj(res.x))
            sharpe = (target - risk_free_rate) / vol if vol > 0 else 0
            points.append({
                "return": round(target, 6),
                "risk": round(vol, 6),
                "sharpe_ratio": round(sharpe, 4),
                "weights": {str(aid): round(float(w), 4) for aid, w in zip(asset_ids, res.x)},
            })

    # Find special portfolios
    max_sharpe = optimize_portfolio.__wrapped__ if hasattr(optimize_portfolio, '__wrapped__') else None
    return {
        "points": points,
        "n_assets": n,
        "risk_free_rate": risk_free_rate,
    }


async def calculate_correlation_matrix(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    days: int = 365,
) -> dict:
    """Calculate correlation and covariance matrices."""
    rows = await conn.fetch("""
        SELECT h.asset_id, a.symbol FROM portfolio_holdings h
        JOIN assets a ON h.asset_id = a.asset_id
        WHERE h.portfolio_id = $1
    """, portfolio_id)
    if not rows:
        return {"error": "No holdings"}

    asset_ids = [r["asset_id"] for r in rows]
    symbols = [r["symbol"] for r in rows]
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    returns_matrix, _ = await get_returns_matrix(conn, asset_ids, start_date, end_date)

    if returns_matrix.size == 0:
        return {"error": "Insufficient data"}

    corr = np.corrcoef(returns_matrix.T)
    cov = np.cov(returns_matrix.T) * TRADING_DAYS

    return {
        "symbols": symbols,
        "correlation_matrix": corr.tolist(),
        "covariance_matrix": cov.tolist(),
        "period_days": days,
    }
