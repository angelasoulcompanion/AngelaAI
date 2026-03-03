"""
Pythia — AI Forecasting Service
Techniques aligned with SECustomerAnalysis ForecastingEngine.
Methods: Prophet (AI), Moving Average, Linear Regression, Growth Rate + LLM interpretation.
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
    historical_prices: list[dict] = field(default_factory=list)  # SE pattern: actual data for chart
    trend: str = ""
    confidence: float = 0.0
    confidence_level: str = ""  # High / Medium / Low
    # Enhanced fields
    interpretation: Optional[str] = None
    risk_factors: Optional[list[str]] = None
    llm_provider: Optional[str] = None
    success: bool = True
    message: str = ""


async def forecast_price(
    conn: asyncpg.Connection,
    asset_id: UUID,
    method: str = "prophet",
    forecast_days: int = 30,
    lookback_days: int = 365,
    include_interpretation: bool = False,
) -> ForecastResult:
    """Enhanced forecast aligned with SECustomerAnalysis ForecastingEngine."""
    # Auto-fetch prices if stale or missing
    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return ForecastResult("", method, 0, forecast_days, success=False, message="Asset not found")
    symbol = row["symbol"]

    prices = await conn.fetch("""
        SELECT date, close_price FROM historical_prices
        WHERE asset_id = $1 AND date >= $2
        ORDER BY date
    """, asset_id, date.today() - timedelta(days=lookback_days))

    if len(prices) < 20:
        return ForecastResult(symbol, method, 0, forecast_days, success=False, message="Insufficient data")

    dates_arr = [p["date"] for p in prices]
    closes = np.array([float(p["close_price"]) for p in prices])
    current = float(closes[-1])

    valid_methods = ["prophet", "moving_average", "linear_regression", "growth_rate"]
    if method not in valid_methods:
        return ForecastResult(symbol, method, current, forecast_days,
                              success=False, message=f"Unknown method. Valid: {valid_methods}")

    if method == "prophet":
        predictions, conf = _forecast_prophet(dates_arr, closes, forecast_days)
    elif method == "moving_average":
        predictions, conf = _forecast_ma(closes, forecast_days)
    elif method == "linear_regression":
        predictions, conf = _forecast_lr(closes, forecast_days)
    else:  # growth_rate
        predictions, conf = _forecast_growth_rate(closes, forecast_days)

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

    # Confidence level (SECustomerAnalysis pattern)
    n_data = len(closes)
    if n_data > 200:
        conf_level = "High"
    elif n_data > 60:
        conf_level = "Medium"
    else:
        conf_level = "Low"

    # Add dates to predictions
    last_date = dates_arr[-1]
    for i, pred in enumerate(predictions):
        d = last_date + timedelta(days=i + 1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
        pred["date"] = d.isoformat()

    # Historical prices for chart (last N trading days, matching forecast horizon)
    hist_count = min(len(dates_arr), max(90, forecast_days * 3))
    historical = [
        {"date": dates_arr[i].isoformat(), "price": round(float(closes[i]), 2)}
        for i in range(len(dates_arr) - hist_count, len(dates_arr))
    ]

    result = ForecastResult(
        symbol=symbol,
        method=method,
        current_price=current,
        forecast_days=forecast_days,
        predictions=predictions,
        historical_prices=historical,
        trend=trend,
        confidence=round(conf, 4),
        confidence_level=conf_level,
    )

    # LLM interpretation + risk factors
    if include_interpretation:
        try:
            from services.llm_service import llm_service

            last_pred = predictions[-1] if predictions else {}
            forecast_price_val = last_pred.get("price", current)
            change_pct = ((forecast_price_val - current) / current * 100) if current > 0 else 0
            vol = float(np.std(np.diff(closes) / closes[:-1])) * np.sqrt(252) if len(closes) > 1 else 0

            prompt = f"""Interpret this price forecast for {symbol}:
- Current Price: {current:.2f}
- Method: {method}
- Forecast ({forecast_days}d): {forecast_price_val:.2f} ({change_pct:+.1f}%)
- Trend: {trend}
- Confidence: {conf:.1%} ({conf_level})
- Annualized Volatility: {vol*100:.1f}%

Respond with JSON:
{{
  "interpretation": "<2-3 sentence interpretation of this forecast>",
  "risk_factors": ["<risk 1>", "<risk 2>", "<risk 3>"]
}}"""

            parsed, llm_resp = await llm_service.complete_json(
                prompt=prompt,
                system="You are a quantitative analyst. Be specific and data-driven. List concrete risks.",
                complexity="simple",
                max_tokens=512,
            )
            if parsed:
                result.interpretation = parsed.get("interpretation")
                result.risk_factors = parsed.get("risk_factors", [])
                result.llm_provider = llm_resp.provider
        except Exception:
            pass

    return result


# ── Forecast Methods (aligned with SECustomerAnalysis ForecastingEngine) ──────


def _forecast_ma(prices: np.ndarray, n_days: int) -> tuple[list[dict], float]:
    """Moving Average: 3-period window + trend adjustment.
    SECustomerAnalysis pattern: base = avg(last 3), trend from halves, confidence ±20%.
    """
    window = min(3, len(prices))
    confidence_margin = 0.20

    base = float(np.mean(prices[-window:]))

    # Trend: first half vs second half
    mid = len(prices) // 2
    first_half_avg = float(np.mean(prices[:mid])) if mid > 0 else base
    second_half_avg = float(np.mean(prices[mid:])) if mid > 0 else base
    trend = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
    trend = max(-0.3, min(0.3, trend))  # Cap at ±30%

    predictions = []
    for i in range(n_days):
        projected = base * (1 + trend * (i + 1) / n_days)
        projected = max(0, projected)
        predictions.append({
            "day": i + 1,
            "price": round(projected, 2),
            "lower": round(max(0, projected * (1 - confidence_margin)), 2),
            "upper": round(projected * (1 + confidence_margin), 2),
        })

    confidence = max(0.1, min(0.9, 1.0 - abs(trend)))
    return predictions, confidence


def _forecast_lr(prices: np.ndarray, n_days: int) -> tuple[list[dict], float]:
    """Linear Regression with R²-based dynamic confidence.
    SECustomerAnalysis pattern: R² > 0.7 → ±15%, R² > 0.5 → ±25%, else ±35%.
    """
    x = np.arange(len(prices), dtype=float)
    x_mean = np.mean(x)
    y_mean = np.mean(prices)

    # Least squares
    numerator = np.sum((x - x_mean) * (prices - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean

    # R² for confidence
    y_pred = slope * x + intercept
    ss_res = np.sum((prices - y_pred) ** 2)
    ss_tot = np.sum((prices - y_mean) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Dynamic confidence margin based on R²
    if r_squared > 0.7:
        confidence_margin = 0.15
    elif r_squared > 0.5:
        confidence_margin = 0.25
    else:
        confidence_margin = 0.35

    predictions = []
    for i in range(n_days):
        t = len(prices) + i
        projected = float(slope * t + intercept)
        projected = max(0, projected)
        predictions.append({
            "day": i + 1,
            "price": round(projected, 2),
            "lower": round(max(0, projected * (1 - confidence_margin)), 2),
            "upper": round(projected * (1 + confidence_margin), 2),
        })

    confidence = max(0.1, min(0.9, r_squared))
    return predictions, confidence


def _forecast_growth_rate(prices: np.ndarray, n_days: int) -> tuple[list[dict], float]:
    """Growth Rate: compound MoM growth extrapolation.
    SECustomerAnalysis pattern: avg growth capped at ±10%, compound projection.
    """
    max_daily_growth = 0.005  # ±0.5% per day cap
    confidence_margin = 0.15

    # Calculate day-over-day growth rates
    returns = np.diff(prices) / prices[:-1]
    returns = returns[np.isfinite(returns)]

    if len(returns) < 5:
        # Fallback: use simple last price
        return _forecast_ma(prices, n_days)

    avg_growth = float(np.mean(returns))
    avg_growth = max(-max_daily_growth, min(max_daily_growth, avg_growth))

    base = float(prices[-1])
    predictions = []
    for i in range(n_days):
        projected = base * (1 + avg_growth) ** (i + 1)
        projected = max(0, projected)
        predictions.append({
            "day": i + 1,
            "price": round(projected, 2),
            "lower": round(max(0, projected * (1 - confidence_margin)), 2),
            "upper": round(projected * (1 + confidence_margin), 2),
        })

    # Confidence based on growth stability
    growth_std = float(np.std(returns))
    confidence = max(0.1, min(0.9, 1.0 - growth_std * 10))
    return predictions, confidence


def _forecast_prophet(dates: list, prices: np.ndarray, n_days: int) -> tuple[list[dict], float]:
    """Prophet: AI-powered with seasonality detection.
    SECustomerAnalysis pattern: multiplicative seasonality, 80% interval, changepoint_prior_scale=0.05.
    Falls back to moving_average if Prophet unavailable.
    """
    try:
        from prophet import Prophet
        import pandas as pd

        df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": prices})
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            seasonality_mode="multiplicative",
            interval_width=0.80,
            changepoint_prior_scale=0.05,
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=n_days, freq="B")
        forecast = model.predict(future)
        forecast_tail = forecast.tail(n_days)

        predictions = []
        for i, (_, row) in enumerate(forecast_tail.iterrows()):
            predictions.append({
                "day": i + 1,
                "price": round(max(0, float(row["yhat"])), 2),
                "lower": round(max(0, float(row["yhat_lower"])), 2),
                "upper": round(float(row["yhat_upper"]), 2),
            })

        # Prophet's own confidence
        confidence = 0.80
        return predictions, confidence

    except ImportError:
        return _forecast_ma(prices, n_days)
