"""
Pythia — Position Sizing Service
Kelly Criterion, Risk Parity, Volatility Targeting
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from config import PythiaConfig


@dataclass
class PositionSizeResult:
    asset_id: str
    symbol: str
    method: str
    position_size_pct: float     # % of portfolio
    position_size_value: float   # absolute value
    portfolio_value: float
    risk_per_trade: float
    details: dict = field(default_factory=dict)
    success: bool = True
    message: str = ""


@dataclass
class RiskParityResult:
    weights: dict[str, float]    # asset_id -> weight
    symbols: dict[str, str]      # asset_id -> symbol
    volatilities: dict[str, float]
    success: bool = True
    message: str = ""


def kelly_criterion(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    fraction: float = 0.5,
) -> float:
    """Half-Kelly position sizing.

    f* = (p * b - q) / b
    where p = win_rate, q = 1-p, b = avg_win/avg_loss
    """
    if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0

    b = avg_win / avg_loss  # win/loss ratio
    q = 1 - win_rate
    kelly = (win_rate * b - q) / b

    # Apply fraction (half-Kelly default) and cap
    sized = max(0.0, kelly * fraction)
    return min(sized, 0.25)  # cap at 25% of portfolio


async def calculate_position_size(
    conn: asyncpg.Connection,
    asset_id: UUID,
    portfolio_id: UUID,
    method: str = "kelly",
    risk_per_trade: float = 0.02,
) -> PositionSizeResult:
    """Calculate position size using specified method."""
    # Get asset info
    row = await conn.fetchrow(
        "SELECT symbol FROM assets WHERE asset_id = $1", asset_id
    )
    if not row:
        return PositionSizeResult(
            asset_id=str(asset_id), symbol="", method=method,
            position_size_pct=0, position_size_value=0, portfolio_value=0,
            risk_per_trade=risk_per_trade,
            success=False, message="Asset not found",
        )
    symbol = row["symbol"]

    # Get portfolio value
    port_row = await conn.fetchrow(
        """SELECT COALESCE(SUM(h.quantity * hp.close_price), 0) as total_value
           FROM portfolio_holdings h
           JOIN LATERAL (
               SELECT close_price FROM historical_prices
               WHERE asset_id = h.asset_id ORDER BY date DESC LIMIT 1
           ) hp ON true
           WHERE h.portfolio_id = $1""",
        portfolio_id,
    )
    portfolio_value = float(port_row["total_value"]) if port_row else 0

    if portfolio_value <= 0:
        # Use initial capital as fallback
        cap_row = await conn.fetchrow(
            "SELECT initial_capital FROM portfolios WHERE portfolio_id = $1",
            portfolio_id,
        )
        portfolio_value = float(cap_row["initial_capital"] or 100000) if cap_row else 100000

    # Get price history for calculations
    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    prices = await conn.fetch(
        """SELECT close_price FROM historical_prices
           WHERE asset_id = $1 AND date >= $2
           ORDER BY date""",
        asset_id, date.today() - timedelta(days=365),
    )

    if len(prices) < 30:
        return PositionSizeResult(
            asset_id=str(asset_id), symbol=symbol, method=method,
            position_size_pct=0, position_size_value=0,
            portfolio_value=portfolio_value,
            risk_per_trade=risk_per_trade,
            success=False, message="Insufficient price data",
        )

    closes = np.array([float(p["close_price"]) for p in prices])
    returns = np.diff(np.log(closes))

    if method == "kelly":
        size_pct, details = _kelly_size(returns, risk_per_trade)
    elif method == "volatility_target":
        size_pct, details = _vol_target_size(returns, risk_per_trade)
    elif method == "atr_stop":
        size_pct, details = _atr_stop_size(closes, risk_per_trade, portfolio_value)
    else:
        size_pct = risk_per_trade
        details = {"method": "fixed_risk", "note": "Using fixed risk per trade"}

    size_value = portfolio_value * size_pct

    return PositionSizeResult(
        asset_id=str(asset_id),
        symbol=symbol,
        method=method,
        position_size_pct=round(size_pct, 4),
        position_size_value=round(size_value, 2),
        portfolio_value=round(portfolio_value, 2),
        risk_per_trade=risk_per_trade,
        details=details,
    )


def _kelly_size(returns: np.ndarray, risk_per_trade: float) -> tuple[float, dict]:
    """Kelly Criterion sizing from historical returns."""
    wins = returns[returns > 0]
    losses = returns[returns < 0]

    if len(wins) == 0 or len(losses) == 0:
        return risk_per_trade, {"note": "Not enough win/loss data, using fixed risk"}

    win_rate = len(wins) / len(returns)
    avg_win = float(np.mean(wins))
    avg_loss = float(np.mean(np.abs(losses)))

    kelly_full = kelly_criterion(win_rate, avg_win, avg_loss, fraction=1.0)
    kelly_half = kelly_criterion(win_rate, avg_win, avg_loss, fraction=PythiaConfig.KELLY_FRACTION)

    return kelly_half, {
        "win_rate": round(win_rate, 4),
        "avg_win": round(avg_win, 6),
        "avg_loss": round(avg_loss, 6),
        "win_loss_ratio": round(avg_win / avg_loss, 4),
        "kelly_full": round(kelly_full, 4),
        "kelly_half": round(kelly_half, 4),
        "fraction": PythiaConfig.KELLY_FRACTION,
    }


def _vol_target_size(returns: np.ndarray, target_vol: float) -> tuple[float, dict]:
    """Size position to target portfolio volatility."""
    annual_vol = float(np.std(returns[-60:]) * np.sqrt(252))
    if annual_vol <= 0:
        return target_vol, {"note": "Zero volatility"}

    # Scale factor: target_vol / asset_vol
    size = target_vol / annual_vol
    size = min(size, 0.30)  # cap at 30%

    return size, {
        "asset_annual_vol": round(annual_vol, 4),
        "target_vol": target_vol,
        "scale_factor": round(size, 4),
    }


def _atr_stop_size(
    closes: np.ndarray, risk_per_trade: float, portfolio_value: float
) -> tuple[float, dict]:
    """Size based on ATR (Average True Range) stop distance."""
    if len(closes) < 15:
        return risk_per_trade, {"note": "Not enough data for ATR"}

    # Simplified ATR (using close-to-close)
    daily_ranges = np.abs(np.diff(closes))
    atr_14 = float(np.mean(daily_ranges[-14:]))
    current_price = float(closes[-1])

    if current_price <= 0:
        return risk_per_trade, {"note": "Invalid price"}

    # Stop distance = 2 * ATR
    stop_distance = 2 * atr_14
    stop_pct = stop_distance / current_price

    # Risk amount = portfolio * risk_per_trade
    risk_amount = portfolio_value * risk_per_trade

    # Position size = risk_amount / stop_distance
    if stop_distance > 0:
        shares = risk_amount / stop_distance
        position_value = shares * current_price
        size_pct = position_value / portfolio_value
    else:
        size_pct = risk_per_trade

    size_pct = min(size_pct, 0.25)

    return size_pct, {
        "atr_14": round(atr_14, 4),
        "current_price": round(current_price, 4),
        "stop_distance": round(stop_distance, 4),
        "stop_pct": round(stop_pct, 4),
        "risk_amount": round(risk_amount, 2),
    }


async def risk_parity_weights(
    conn: asyncpg.Connection,
    asset_ids: list[UUID],
    days: int = 252,
) -> RiskParityResult:
    """Calculate risk parity (inverse volatility) weights."""
    from services.optimization_service import get_returns_matrix

    start_date = date.today() - timedelta(days=days + 50)
    returns_matrix, symbols = await get_returns_matrix(conn, asset_ids, start_date)

    if returns_matrix.size == 0:
        return RiskParityResult(
            weights={}, symbols={}, volatilities={},
            success=False, message="Insufficient data",
        )

    # Annual volatility per asset
    vols = np.std(returns_matrix, axis=0) * np.sqrt(252)
    inv_vols = 1.0 / (vols + 1e-10)
    weights = inv_vols / inv_vols.sum()

    weight_dict = {}
    symbol_dict = {}
    vol_dict = {}
    for i, aid in enumerate(asset_ids):
        if i < len(symbols):
            aid_str = str(aid)
            weight_dict[aid_str] = round(float(weights[i]), 4)
            symbol_dict[aid_str] = symbols[i]
            vol_dict[aid_str] = round(float(vols[i]), 4)

    return RiskParityResult(
        weights=weight_dict,
        symbols=symbol_dict,
        volatilities=vol_dict,
    )
