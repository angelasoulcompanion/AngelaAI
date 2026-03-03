"""
Pythia — AI Sentiment Analysis Service
Hybrid: Rule-based technical + yfinance news + LLM narrative commentary.
"""
import json
from dataclasses import dataclass, field
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
    # Enhanced fields
    narrative: Optional[str] = None
    news_headlines: Optional[list[dict]] = None
    technical_score: Optional[float] = None
    news_score: Optional[float] = None
    combined_score: Optional[float] = None
    llm_provider: Optional[str] = None
    success: bool = True
    message: str = ""


async def analyze_sentiment(
    conn: asyncpg.Connection,
    asset_id: UUID,
    days: int = 30,
    include_news: bool = False,
    include_narrative: bool = False,
) -> SentimentResult:
    """Enhanced sentiment: technical + news + LLM narrative."""
    # Step 0: Auto-fetch prices if stale or missing
    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    # Step 1: Always run technical analysis
    result = await _analyze_technical(conn, asset_id, days)
    if not result.success:
        return result

    technical_score = result.score
    result.technical_score = technical_score

    # Step 2: News sentiment (optional)
    if include_news:
        news_data = await _analyze_news(result.symbol)
        result.news_headlines = news_data["headlines"]
        result.news_score = news_data["score"]

        # Combined score: 60% technical + 40% news
        if result.news_score is not None:
            result.combined_score = round(0.6 * technical_score + 0.4 * result.news_score, 4)
            result.score = result.combined_score
            # Recalculate sentiment from combined
            if result.combined_score > 0.2:
                result.sentiment = "bullish"
            elif result.combined_score < -0.2:
                result.sentiment = "bearish"
            else:
                result.sentiment = "neutral"
        else:
            result.combined_score = technical_score

    # Step 3: LLM narrative commentary (optional)
    if include_narrative:
        try:
            from services.llm_service import llm_service

            prompt = f"""Analyze the market sentiment for {result.symbol}:
- Technical Score: {technical_score:.4f} ({result.sentiment})
- Price Momentum: {result.price_momentum:.4f}
- Volume Trend: {result.volume_trend:.2f}x
- Volatility: {result.volatility_regime}
- Signals: {json.dumps(result.signals[:5])}
{"- News Score: " + str(result.news_score) if result.news_score is not None else ""}

Write a concise 2-3 sentence market commentary. Be specific about price action and what traders should watch for. No disclaimers."""

            llm_resp = await llm_service.complete(
                prompt=prompt,
                system="You are a senior market analyst at a quantitative hedge fund. Write brief, actionable commentary.",
                complexity="simple",
                max_tokens=256,
            )
            if llm_resp.success and llm_resp.text:
                result.narrative = llm_resp.text
                result.llm_provider = llm_resp.provider
        except Exception:
            pass  # Narrative is optional enhancement

    return result


async def _analyze_technical(
    conn: asyncpg.Connection,
    asset_id: UUID,
    days: int = 30,
) -> SentimentResult:
    """Technical analysis from price action + volume (original rule-based logic)."""
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

    # 1. Price momentum
    recent_ret = float(np.sum(returns[-days:])) if len(returns) >= days else float(np.sum(returns))
    if recent_ret > 0.05:
        signals.append({"signal": "Strong upward momentum", "impact": "bullish", "value": round(recent_ret, 4)})
        score += 0.3
    elif recent_ret < -0.05:
        signals.append({"signal": "Strong downward momentum", "impact": "bearish", "value": round(recent_ret, 4)})
        score -= 0.3
    else:
        signals.append({"signal": "Neutral momentum", "impact": "neutral", "value": round(recent_ret, 4)})

    # 2. SMA crossover
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


async def _analyze_news(symbol: str) -> dict:
    """Fetch news headlines from yfinance and score sentiment via LLM."""
    headlines: list[dict] = []
    news_score: Optional[float] = None

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        for item in news[:10]:
            headlines.append({
                "title": item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "link": item.get("link", ""),
            })
    except Exception:
        return {"headlines": headlines, "score": None}

    if not headlines:
        return {"headlines": headlines, "score": None}

    # Score headlines via LLM
    try:
        from services.llm_service import llm_service

        titles = "\n".join(f"- {h['title']}" for h in headlines if h["title"])
        prompt = f"""Score the overall sentiment of these news headlines for {symbol} on a scale from -1.0 (very bearish) to 1.0 (very bullish).

Headlines:
{titles}

Respond with ONLY a JSON object: {{"score": <float>, "reasoning": "<one sentence>"}}"""

        parsed, llm_resp = await llm_service.complete_json(
            prompt=prompt,
            complexity="simple",
            max_tokens=128,
        )
        if parsed and "score" in parsed:
            news_score = max(-1.0, min(1.0, float(parsed["score"])))
    except Exception:
        pass

    return {"headlines": headlines, "score": news_score}
