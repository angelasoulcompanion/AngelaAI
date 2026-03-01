"""
Pythia — AI Forecasting Service
Moving average + linear regression + trend analysis.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np


@dataclass
class ForecastResult:
    symbol: str
    method: str
    current_price: float
    forecast_days: int
    predictions: list[dict] = field(default_factory=list)
    trend: str = ""
    confidence: float = 0.0
    success: bool = True
    message: str = ""


async def forecast_price(
    conn: asyncpg.Connection,
    asset_id: UUID,
    method: str = "moving_average",
    forecast_days: int = 30,
    lookback_days: int = 365,
) -> ForecastResult:
    """Forecast future prices."""
    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return ForecastResult("", method, 0, forecast_days, success=False, message="Asset not found")
    symbol = row["symbol"]

    prices = await conn.fetch("""
        SELECT date, close_price FROM historical_prices
        WHERE asset_id = $1 AND date >= $2
        ORDER BY date
    """, asset_id, date.today() - timedelta(days=lookback_days))

    if len(prices) < 30:
        return ForecastResult(symbol, method, 0, forecast_days, success=False, message="Insufficient data")

    dates_arr = [p["date"] for p in prices]
    closes = np.array([float(p["close_price"]) for p in prices])
    current = float(closes[-1])

    valid_methods = ["moving_average", "linear_regression", "exponential_smoothing"]
    if method not in valid_methods:
        return ForecastResult(symbol, method, current, forecast_days,
                              success=False, message=f"Unknown method. Valid: {valid_methods}")

    if method == "moving_average":
        predictions = _forecast_ma(closes, forecast_days)
    elif method == "linear_regression":
        predictions = _forecast_lr(closes, forecast_days)
    else:
        predictions = _forecast_ema(closes, forecast_days)

    # Trend detection
    if len(predictions) >= 2:
        first_pred = predictions[0]["price"]
        last_pred = predictions[-1]["price"]
        change = (last_pred - first_pred) / first_pred if first_pred > 0 else 0
        if change > 0.02:
            trend = "upward"
        elif change < -0.02:
            trend = "downward"
        else:
            trend = "sideways"
    else:
        trend = "unknown"

    # Simple confidence based on recent prediction accuracy proxy
    returns = np.diff(closes) / closes[:-1]
    vol = float(np.std(returns[-30:])) if len(returns) >= 30 else float(np.std(returns))
    confidence = max(0.1, min(0.9, 1.0 - vol * 5))

    # Add dates
    last_date = dates_arr[-1]
    for i, pred in enumerate(predictions):
        d = last_date + timedelta(days=i + 1)
        # Skip weekends
        while d.weekday() >= 5:
            d += timedelta(days=1)
        pred["date"] = d.isoformat()

    return ForecastResult(
        symbol=symbol,
        method=method,
        current_price=current,
        forecast_days=forecast_days,
        predictions=predictions,
        trend=trend,
        confidence=round(confidence, 4),
    )


def _forecast_ma(prices: np.ndarray, n_days: int, window: int = 20) -> list[dict]:
    """Moving average forecast."""
    predictions = []
    extended = list(prices)

    for i in range(n_days):
        ma = float(np.mean(extended[-window:]))
        predictions.append({
            "day": i + 1,
            "price": round(ma, 2),
            "lower": round(ma * 0.97, 2),
            "upper": round(ma * 1.03, 2),
        })
        extended.append(ma)

    return predictions


def _forecast_lr(prices: np.ndarray, n_days: int) -> list[dict]:
    """Linear regression forecast."""
    x = np.arange(len(prices))
    coeffs = np.polyfit(x, prices, 1)
    slope, intercept = coeffs[0], coeffs[1]

    # Prediction interval
    residuals = prices - (slope * x + intercept)
    std_err = float(np.std(residuals))

    predictions = []
    for i in range(n_days):
        t = len(prices) + i
        pred = float(slope * t + intercept)
        predictions.append({
            "day": i + 1,
            "price": round(max(0, pred), 2),
            "lower": round(max(0, pred - 1.96 * std_err), 2),
            "upper": round(pred + 1.96 * std_err, 2),
        })

    return predictions


def _forecast_ema(prices: np.ndarray, n_days: int, span: int = 20) -> list[dict]:
    """Exponential smoothing forecast."""
    alpha = 2 / (span + 1)
    ema = float(prices[0])
    for p in prices[1:]:
        ema = alpha * float(p) + (1 - alpha) * ema

    predictions = []
    current_ema = ema
    returns = np.diff(prices) / prices[:-1]
    vol = float(np.std(returns[-30:])) if len(returns) >= 30 else float(np.std(returns))

    for i in range(n_days):
        predictions.append({
            "day": i + 1,
            "price": round(current_ema, 2),
            "lower": round(current_ema * (1 - vol * np.sqrt(i + 1)), 2),
            "upper": round(current_ema * (1 + vol * np.sqrt(i + 1)), 2),
        })
        # EMA converges — slight trend continuation
        current_ema = alpha * current_ema + (1 - alpha) * current_ema

    return predictions
