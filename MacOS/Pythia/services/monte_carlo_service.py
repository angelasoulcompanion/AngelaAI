"""
Pythia — Monte Carlo Simulation Service
Geometric Brownian Motion (GBM) price simulation.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from config import PythiaConfig

TRADING_DAYS = PythiaConfig.TRADING_DAYS_PER_YEAR


@dataclass
class MonteCarloResult:
    symbol: str
    current_price: float
    n_simulations: int
    time_steps: int
    # Statistics
    mean_final_price: float
    median_final_price: float
    std_final_price: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    prob_above_current: float
    # Distribution
    expected_return: float
    volatility: float
    # Sample paths (for visualization)
    sample_paths: list[list[float]] = field(default_factory=list)
    percentile_bands: list[dict] = field(default_factory=list)
    final_distribution: list[float] = field(default_factory=list)
    success: bool = True
    message: str = ""


async def run_monte_carlo(
    conn: asyncpg.Connection,
    asset_id: UUID,
    n_simulations: int = 10000,
    time_steps: int = 252,
    lookback_days: int = 365,
    n_sample_paths: int = 100,
) -> MonteCarloResult:
    """Run Monte Carlo simulation using GBM."""
    # Get current info
    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return MonteCarloResult("", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                success=False, message="Asset not found")
    symbol = row["symbol"]

    # Get historical prices
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)
    prices = await conn.fetch("""
        SELECT close_price FROM historical_prices
        WHERE asset_id = $1 AND date BETWEEN $2 AND $3
        ORDER BY date
    """, asset_id, start_date, end_date)

    if len(prices) < 20:
        return MonteCarloResult(symbol, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                success=False, message="Insufficient data")

    price_array = np.array([float(p["close_price"]) for p in prices])
    returns = np.diff(price_array) / price_array[:-1]

    S0 = float(price_array[-1])  # Current price
    mu = float(np.mean(returns))
    sigma = float(np.std(returns))

    # GBM simulation
    dt = 1.0  # daily
    np.random.seed(None)  # Random seed for each run

    # Generate all paths at once
    Z = np.random.standard_normal((n_simulations, time_steps))
    drift = (mu - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt) * Z

    log_returns = drift + diffusion
    log_price_paths = np.cumsum(log_returns, axis=1)
    price_paths = S0 * np.exp(log_price_paths)

    final_prices = price_paths[:, -1]

    # Percentile bands (for fan chart)
    percentile_bands = []
    for t in range(0, time_steps, max(1, time_steps // 50)):
        col = price_paths[:, t]
        percentile_bands.append({
            "step": t,
            "p5": round(float(np.percentile(col, 5)), 2),
            "p25": round(float(np.percentile(col, 25)), 2),
            "p50": round(float(np.percentile(col, 50)), 2),
            "p75": round(float(np.percentile(col, 75)), 2),
            "p95": round(float(np.percentile(col, 95)), 2),
        })

    # Sample paths for visualization
    sample_indices = np.random.choice(n_simulations, min(n_sample_paths, n_simulations), replace=False)
    sample_paths = []
    step = max(1, time_steps // 50)
    for idx in sample_indices:
        path = [round(float(price_paths[idx, t]), 2) for t in range(0, time_steps, step)]
        sample_paths.append(path)

    # Final distribution histogram (100 bins)
    hist_values = sorted([round(float(p), 2) for p in np.random.choice(final_prices, min(500, n_simulations), replace=False)])

    return MonteCarloResult(
        symbol=symbol,
        current_price=round(S0, 2),
        n_simulations=n_simulations,
        time_steps=time_steps,
        mean_final_price=round(float(np.mean(final_prices)), 2),
        median_final_price=round(float(np.median(final_prices)), 2),
        std_final_price=round(float(np.std(final_prices)), 2),
        percentile_5=round(float(np.percentile(final_prices, 5)), 2),
        percentile_25=round(float(np.percentile(final_prices, 25)), 2),
        percentile_75=round(float(np.percentile(final_prices, 75)), 2),
        percentile_95=round(float(np.percentile(final_prices, 95)), 2),
        prob_above_current=round(float(np.mean(final_prices > S0)), 4),
        expected_return=round(mu * TRADING_DAYS, 6),
        volatility=round(sigma * np.sqrt(TRADING_DAYS), 6),
        sample_paths=sample_paths,
        percentile_bands=percentile_bands,
        final_distribution=hist_values,
    )
