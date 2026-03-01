"""
Pythia — AI Sentiment Analysis Service
Rule-based sentiment from price action + volume.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np


@dataclass
class SentimentResult:
    symbol: str
    sentiment: str  # bullish, bearish, neutral
    score: float  # -1.0 to 1.0
    signals: list[dict]
    price_momentum: float
    volume_trend: float
    volatility_regime: str
    success: bool = True
    message: str = ""


async def analyze_sentiment(
    conn: asyncpg.Connection,
    asset_id: UUID,
    days: int = 30,
) -> SentimentResult:
    """Analyze market sentiment from price & volume data."""
    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return SentimentResult("", "neutral", 0, [], 0, 0, "unknown",
                               success=False, message="Asset not found")
    symbol = row["symbol"]

    prices = await conn.fetch("""
        SELECT date, close_price, volume FROM historical_prices
        WHERE asset_id = $1 AND date >= $2
        ORDER BY date
    """, asset_id, date.today() - timedelta(days=days + 50))

    if len(prices) < 20:
        return SentimentResult(symbol, "neutral", 0, [], 0, 0, "unknown",
                               success=False, message="Insufficient data")

    closes = np.array([float(p["close_price"]) for p in prices])
    volumes = np.array([float(p["volume"] or 0) for p in prices])
    returns = np.diff(closes) / closes[:-1]

    signals = []
    score = 0.0

    # 1. Price momentum (last N days)
    recent_ret = float(np.sum(returns[-days:])) if len(returns) >= days else float(np.sum(returns))
    if recent_ret > 0.05:
        signals.append({"signal": "Strong upward momentum", "impact": "bullish", "value": round(recent_ret, 4)})
        score += 0.3
    elif recent_ret < -0.05:
        signals.append({"signal": "Strong downward momentum", "impact": "bearish", "value": round(recent_ret, 4)})
        score -= 0.3
    else:
        signals.append({"signal": "Neutral momentum", "impact": "neutral", "value": round(recent_ret, 4)})

    # 2. SMA crossover (20 vs 50)
    if len(closes) >= 50:
        sma20 = np.mean(closes[-20:])
        sma50 = np.mean(closes[-50:])
        if sma20 > sma50:
            signals.append({"signal": "SMA20 above SMA50 (Golden Cross area)", "impact": "bullish"})
            score += 0.2
        else:
            signals.append({"signal": "SMA20 below SMA50 (Death Cross area)", "impact": "bearish"})
            score -= 0.2

    # 3. Volume trend
    if len(volumes) >= 20 and np.mean(volumes[-20:]) > 0:
        vol_ratio = float(np.mean(volumes[-5:]) / np.mean(volumes[-20:]))
        if vol_ratio > 1.5:
            signals.append({"signal": "Volume surge (5d/20d ratio)", "impact": "bullish" if recent_ret > 0 else "bearish", "value": round(vol_ratio, 2)})
            score += 0.15 if recent_ret > 0 else -0.15
        elif vol_ratio < 0.7:
            signals.append({"signal": "Volume declining", "impact": "neutral", "value": round(vol_ratio, 2)})

    # 4. Volatility regime
    recent_vol = float(np.std(returns[-20:])) * np.sqrt(252) if len(returns) >= 20 else 0
    if recent_vol > 0.4:
        vol_regime = "high"
        signals.append({"signal": "High volatility regime", "impact": "cautious", "value": round(recent_vol, 4)})
    elif recent_vol < 0.15:
        vol_regime = "low"
        signals.append({"signal": "Low volatility regime", "impact": "neutral", "value": round(recent_vol, 4)})
    else:
        vol_regime = "normal"

    # 5. RSI approximation
    if len(returns) >= 14:
        gains = returns[-14:]
        avg_gain = float(np.mean(gains[gains > 0])) if np.any(gains > 0) else 0
        avg_loss = float(np.mean(np.abs(gains[gains < 0]))) if np.any(gains < 0) else 0.001
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))
        if rsi > 70:
            signals.append({"signal": "RSI overbought", "impact": "bearish", "value": round(rsi, 1)})
            score -= 0.15
        elif rsi < 30:
            signals.append({"signal": "RSI oversold", "impact": "bullish", "value": round(rsi, 1)})
            score += 0.15
        else:
            signals.append({"signal": "RSI neutral", "impact": "neutral", "value": round(rsi, 1)})

    # Final sentiment
    score = max(-1.0, min(1.0, score))
    if score > 0.2:
        sentiment = "bullish"
    elif score < -0.2:
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    vol_ratio_val = float(np.mean(volumes[-5:]) / np.mean(volumes[-20:])) if len(volumes) >= 20 and np.mean(volumes[-20:]) > 0 else 1.0

    return SentimentResult(
        symbol=symbol,
        sentiment=sentiment,
        score=round(score, 4),
        signals=signals,
        price_momentum=round(recent_ret, 6),
        volume_trend=round(vol_ratio_val, 4),
        volatility_regime=vol_regime,
    )
