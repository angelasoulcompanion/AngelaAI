"""
Pythia — Technical Analysis Router
Computes MACD, RSI, SMA, EMA, Bollinger Bands from Yahoo Finance data.
"""
import math
from typing import Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from helpers.financial_utils import get_yahoo_symbol

router = APIRouter(prefix="/api/technical", tags=["technical"])


def _sma(data: list[float], period: int) -> list[Optional[float]]:
    result: list[Optional[float]] = [None] * len(data)
    for i in range(period - 1, len(data)):
        result[i] = sum(data[i - period + 1 : i + 1]) / period
    return result


def _ema(data: list[float], period: int) -> list[Optional[float]]:
    result: list[Optional[float]] = [None] * len(data)
    k = 2.0 / (period + 1)
    # Seed with SMA
    if len(data) < period:
        return result
    result[period - 1] = sum(data[:period]) / period
    for i in range(period, len(data)):
        result[i] = data[i] * k + result[i - 1] * (1 - k)
    return result


def _macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict:
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    n = len(closes)

    macd_line: list[Optional[float]] = [None] * n
    for i in range(n):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]

    # Signal line = EMA of MACD line
    macd_values = [v for v in macd_line if v is not None]
    if len(macd_values) < signal:
        signal_line: list[Optional[float]] = [None] * n
        histogram: list[Optional[float]] = [None] * n
    else:
        signal_ema = _ema(macd_values, signal)
        # Map back to full length
        signal_line = [None] * n
        histogram = [None] * n
        start_idx = next(i for i in range(n) if macd_line[i] is not None)
        for j, val in enumerate(signal_ema):
            idx = start_idx + j
            if idx < n:
                signal_line[idx] = val
                if val is not None and macd_line[idx] is not None:
                    histogram[idx] = macd_line[idx] - val

    return {
        "macd": [round(v, 6) if v is not None else None for v in macd_line],
        "signal": [round(v, 6) if v is not None else None for v in signal_line],
        "histogram": [round(v, 6) if v is not None else None for v in histogram],
    }


def _rsi(closes: list[float], period: int = 14) -> list[Optional[float]]:
    n = len(closes)
    result: list[Optional[float]] = [None] * n
    if n < period + 1:
        return result

    gains = []
    losses = []
    for i in range(1, n):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    # Initial average
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = round(100 - (100 / (1 + rs)), 4)

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            result[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i + 1] = round(100 - (100 / (1 + rs)), 4)

    return result


def _bollinger(closes: list[float], period: int = 20, std_dev: float = 2.0) -> dict:
    n = len(closes)
    upper: list[Optional[float]] = [None] * n
    middle: list[Optional[float]] = [None] * n
    lower: list[Optional[float]] = [None] * n

    for i in range(period - 1, n):
        window = closes[i - period + 1 : i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)
        middle[i] = round(mean, 4)
        upper[i] = round(mean + std_dev * std, 4)
        lower[i] = round(mean - std_dev * std, 4)

    return {"upper": upper, "middle": middle, "lower": lower}


@router.get("/{symbol}")
async def get_technical_analysis(
    symbol: str,
    period: str = Query("6mo", description="1mo, 3mo, 6mo, 1y, 2y, 5y"),
    interval: str = Query("1d", description="1d, 1wk"),
    macd_fast: int = Query(12, ge=2, le=50, description="MACD fast EMA period"),
    macd_slow: int = Query(26, ge=5, le=100, description="MACD slow EMA period"),
    macd_signal: int = Query(9, ge=2, le=50, description="MACD signal line period"),
    rsi_period: int = Query(14, ge=2, le=50, description="RSI period"),
    sma_periods: str = Query("20,50", description="Comma-separated SMA periods"),
    ema_periods: str = Query("12,26", description="Comma-separated EMA periods"),
    bb_period: int = Query(20, ge=5, le=50, description="Bollinger Bands period"),
    bb_std: float = Query(2.0, ge=0.5, le=4.0, description="Bollinger Bands std dev"),
):
    """Compute technical indicators for a symbol."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    yahoo_symbol = get_yahoo_symbol(symbol)
    ticker = yf.Ticker(yahoo_symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    dates = [idx.strftime("%Y-%m-%d") for idx in hist.index]
    opens = [round(float(r.get("Open", 0)), 4) for _, r in hist.iterrows()]
    highs = [round(float(r.get("High", 0)), 4) for _, r in hist.iterrows()]
    lows = [round(float(r.get("Low", 0)), 4) for _, r in hist.iterrows()]
    closes = [round(float(r.get("Close", 0)), 4) for _, r in hist.iterrows()]
    volumes = [int(r.get("Volume", 0)) for _, r in hist.iterrows()]

    # Parse SMA/EMA period lists
    try:
        sma_period_list = [int(x.strip()) for x in sma_periods.split(",") if x.strip()]
    except ValueError:
        sma_period_list = [20, 50]
    try:
        ema_period_list = [int(x.strip()) for x in ema_periods.split(",") if x.strip()]
    except ValueError:
        ema_period_list = [12, 26]

    # Compute indicators
    macd_data = _macd(closes, macd_fast, macd_slow, macd_signal)
    rsi_data = _rsi(closes, rsi_period)
    bb_data = _bollinger(closes, bb_period, bb_std)

    sma_data = {}
    for p in sma_period_list:
        sma_data[str(p)] = _sma(closes, p)

    ema_data = {}
    for p in ema_period_list:
        ema_data[str(p)] = _ema(closes, p)
    # Round EMA values
    for key in ema_data:
        ema_data[key] = [round(v, 4) if v is not None else None for v in ema_data[key]]

    return {
        "symbol": symbol.upper(),
        "period": period,
        "interval": interval,
        "dates": dates,
        "ohlcv": {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        },
        "macd": {
            "params": {"fast": macd_fast, "slow": macd_slow, "signal": macd_signal},
            **macd_data,
        },
        "rsi": {
            "params": {"period": rsi_period},
            "values": rsi_data,
        },
        "bollinger": {
            "params": {"period": bb_period, "std_dev": bb_std},
            **bb_data,
        },
        "sma": {k: [round(v, 4) if v is not None else None for v in vals] for k, vals in sma_data.items()},
        "ema": ema_data,
    }
