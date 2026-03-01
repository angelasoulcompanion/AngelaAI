"""
Pythia — Returns calculation service (ported from CQFOracle)
Calculates returns, basic statistics, and technical indicators.
"""
from datetime import date
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np


class ReturnsService:
    """Calculate returns and basic statistics from historical prices."""

    @staticmethod
    async def get_returns(
        conn: asyncpg.Connection,
        asset_id: UUID,
        period_days: int = 252,
        return_type: str = "log"
    ) -> dict:
        """Calculate returns from historical prices."""
        rows = await conn.fetch("""
            SELECT date, close_price
            FROM historical_prices
            WHERE asset_id = $1
            ORDER BY date DESC
            LIMIT $2
        """, asset_id, period_days + 1)

        if len(rows) < 2:
            return {"error": "Insufficient data", "data_points": len(rows)}

        prices = np.array([float(r["close_price"]) for r in reversed(rows)])
        dates = [r["date"] for r in reversed(rows)]

        if return_type == "log":
            returns = np.diff(np.log(prices))
        else:
            returns = np.diff(prices) / prices[:-1]

        return {
            "asset_id": str(asset_id),
            "data_points": len(returns),
            "return_type": return_type,
            "dates": [d.isoformat() for d in dates[1:]],
            "returns": returns.tolist(),
            "statistics": {
                "mean": float(np.mean(returns)),
                "std": float(np.std(returns)),
                "annualized_return": float(np.mean(returns) * 252),
                "annualized_volatility": float(np.std(returns) * np.sqrt(252)),
                "skewness": float(_skewness(returns)),
                "kurtosis": float(_kurtosis(returns)),
                "min": float(np.min(returns)),
                "max": float(np.max(returns)),
            }
        }

    @staticmethod
    async def get_cumulative_returns(
        conn: asyncpg.Connection,
        asset_id: UUID,
        period_days: int = 252
    ) -> dict:
        """Calculate cumulative returns."""
        rows = await conn.fetch("""
            SELECT date, close_price
            FROM historical_prices
            WHERE asset_id = $1
            ORDER BY date ASC
            LIMIT $2
        """, asset_id, period_days)

        if len(rows) < 2:
            return {"error": "Insufficient data"}

        prices = np.array([float(r["close_price"]) for r in rows])
        initial = prices[0]
        cumulative = (prices / initial - 1) * 100

        return {
            "asset_id": str(asset_id),
            "dates": [r["date"].isoformat() for r in rows],
            "cumulative_returns": cumulative.tolist(),
            "total_return": float(cumulative[-1]),
        }


def _skewness(data: np.ndarray) -> float:
    """Calculate skewness."""
    n = len(data)
    if n < 3:
        return 0.0
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    return float(n / ((n - 1) * (n - 2)) * np.sum(((data - mean) / std) ** 3))


def _kurtosis(data: np.ndarray) -> float:
    """Calculate excess kurtosis."""
    n = len(data)
    if n < 4:
        return 0.0
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    k4 = np.mean(((data - mean) / std) ** 4)
    return float(k4 - 3)
