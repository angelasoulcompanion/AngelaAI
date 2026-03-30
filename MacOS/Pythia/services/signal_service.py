"""
Pythia — Multi-Factor Signal Generation Engine
Combines technical, sentiment, and quantitative signals into composite scores.
"""
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from config import PythiaConfig


@dataclass
class Signal:
    signal_type: str       # technical, sentiment, quant, fundamental
    signal_name: str       # e.g. "RSI Oversold", "Momentum Z-Score"
    direction: str         # long, short, neutral
    strength: float        # 0.0 to 1.0
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class SignalResult:
    asset_id: str
    symbol: str
    composite_score: float      # -1.0 to 1.0
    composite_direction: str    # long, short, neutral
    signals: list[Signal] = field(default_factory=list)
    technical_score: float = 0.0
    sentiment_score: float = 0.0
    quant_score: float = 0.0
    ai_insight: str = ""
    success: bool = True
    message: str = ""


@dataclass
class SignalSummary:
    asset_id: str
    symbol: str
    composite_score: float
    direction: str
    top_signal: str
    regime: str = ""


async def generate_signals(
    conn: asyncpg.Connection,
    asset_id: UUID,
    include_ai: bool = True,
) -> SignalResult:
    """Generate multi-factor signals for a single asset."""
    # Get asset info
    row = await conn.fetchrow(
        "SELECT symbol, asset_type FROM assets WHERE asset_id = $1", asset_id
    )
    if not row:
        return SignalResult(
            asset_id=str(asset_id), symbol="", composite_score=0,
            composite_direction="neutral",
            success=False, message="Asset not found",
        )
    symbol = row["symbol"]

    # Ensure fresh prices
    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    # Fetch price data
    prices = await conn.fetch(
        """SELECT date, close_price, volume FROM historical_prices
           WHERE asset_id = $1 AND date >= $2
           ORDER BY date""",
        asset_id, date.today() - timedelta(days=365),
    )

    if len(prices) < 30:
        return SignalResult(
            asset_id=str(asset_id), symbol=symbol, composite_score=0,
            composite_direction="neutral",
            success=False, message=f"Insufficient data ({len(prices)} points)",
        )

    closes = np.array([float(p["close_price"]) for p in prices])
    volumes = np.array([float(p["volume"] or 0) for p in prices])
    returns = np.diff(np.log(closes))

    all_signals: list[Signal] = []

    # ── Technical Signals ─────────────────────────────────
    tech_signals, tech_score = _technical_signals(closes, volumes, returns)
    all_signals.extend(tech_signals)

    # ── Quantitative Signals ──────────────────────────────
    quant_signals, quant_score = _quant_signals(closes, returns, volumes)
    all_signals.extend(quant_signals)

    # ── Sentiment Score (from existing service) ───────────
    sentiment_score = 0.0
    try:
        from services.ai_sentiment_service import _analyze_technical
        sent_result = await _analyze_technical(conn, asset_id, days=30)
        if sent_result.success:
            sentiment_score = sent_result.score
            all_signals.append(Signal(
                signal_type="sentiment",
                signal_name="Technical Sentiment",
                direction="long" if sent_result.score > 0.2 else "short" if sent_result.score < -0.2 else "neutral",
                strength=abs(sent_result.score),
                confidence=0.7,
                metadata={"sentiment": sent_result.sentiment, "signals_count": len(sent_result.signals)},
            ))
    except Exception:
        pass

    # ── Composite Score ───────────────────────────────────
    weights = PythiaConfig.SIGNAL_COMPOSITE_WEIGHTS
    composite = (
        weights["technical"] * tech_score
        + weights["quant"] * quant_score
        + weights["sentiment"] * sentiment_score
        + weights["fundamental"] * 0  # placeholder for future
    )
    composite = max(-1.0, min(1.0, composite))

    if composite > 0.15:
        direction = "long"
    elif composite < -0.15:
        direction = "short"
    else:
        direction = "neutral"

    result = SignalResult(
        asset_id=str(asset_id),
        symbol=symbol,
        composite_score=round(composite, 4),
        composite_direction=direction,
        signals=all_signals,
        technical_score=round(tech_score, 4),
        sentiment_score=round(sentiment_score, 4),
        quant_score=round(quant_score, 4),
    )

    # ── AI Insight (Claude) ───────────────────────────────
    if include_ai:
        try:
            from services.llm_service import llm_service

            signal_summary = ", ".join(
                f"{s.signal_name}={s.direction}({s.strength:.2f})"
                for s in all_signals[:8]
            )
            prompt = f"""Asset: {symbol}
Composite Score: {composite:.3f} ({direction})
Technical: {tech_score:.3f} | Quant: {quant_score:.3f} | Sentiment: {sentiment_score:.3f}
Signals: {signal_summary}

Write a 2-sentence actionable trading insight. Be specific about levels and timing."""

            resp = await llm_service.complete(
                prompt=prompt,
                system="You are a quantitative trader. Give brief, precise trading insights.",
                max_tokens=256,
                conn=conn,
                cache_ttl=PythiaConfig.CACHE_TTL_SIGNALS,
                feature="signal_insight",
            )
            if resp.success:
                result.ai_insight = resp.text
        except Exception:
            pass

    # Store signals in DB
    try:
        for sig in all_signals:
            await conn.execute(
                """INSERT INTO trading_signals
                   (asset_id, signal_type, signal_name, direction, strength, confidence, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                asset_id, sig.signal_type, sig.signal_name,
                sig.direction, sig.strength, sig.confidence,
                json.dumps(sig.metadata),
            )
    except Exception:
        pass

    return result


def _technical_signals(
    closes: np.ndarray, volumes: np.ndarray, returns: np.ndarray
) -> tuple[list[Signal], float]:
    """Generate technical analysis signals."""
    signals = []
    score = 0.0

    # 1. RSI (14-period)
    if len(returns) >= 14:
        gains = np.where(returns[-14:] > 0, returns[-14:], 0)
        losses = np.where(returns[-14:] < 0, -returns[-14:], 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses) + 1e-10
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))

        if rsi > 70:
            signals.append(Signal("technical", "RSI Overbought", "short", 0.7,
                                  metadata={"rsi": round(float(rsi), 1)}))
            score -= 0.3
        elif rsi < 30:
            signals.append(Signal("technical", "RSI Oversold", "long", 0.7,
                                  metadata={"rsi": round(float(rsi), 1)}))
            score += 0.3
        else:
            signals.append(Signal("technical", "RSI Neutral", "neutral", 0.3,
                                  metadata={"rsi": round(float(rsi), 1)}))

    # 2. MACD (12, 26, 9)
    if len(closes) >= 35:
        ema12 = _ema(closes, 12)
        ema26 = _ema(closes, 26)
        macd_line = ema12[-len(ema26):] - ema26
        signal_line = _ema(macd_line, 9) if len(macd_line) >= 9 else macd_line

        if len(macd_line) >= 2 and len(signal_line) >= 2:
            macd_val = float(macd_line[-1])
            sig_val = float(signal_line[-1])
            prev_macd = float(macd_line[-2])
            prev_sig = float(signal_line[-2])

            if prev_macd <= prev_sig and macd_val > sig_val:
                signals.append(Signal("technical", "MACD Bullish Cross", "long", 0.8,
                                      metadata={"macd": round(macd_val, 4)}))
                score += 0.25
            elif prev_macd >= prev_sig and macd_val < sig_val:
                signals.append(Signal("technical", "MACD Bearish Cross", "short", 0.8,
                                      metadata={"macd": round(macd_val, 4)}))
                score -= 0.25

    # 3. Bollinger Band position
    if len(closes) >= 20:
        sma20 = np.mean(closes[-20:])
        std20 = np.std(closes[-20:])
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20
        current = float(closes[-1])

        bb_pct = (current - lower) / (upper - lower + 1e-10)
        if bb_pct > 0.95:
            signals.append(Signal("technical", "Above Upper Bollinger", "short", 0.6,
                                  metadata={"bb_pct": round(bb_pct, 3)}))
            score -= 0.15
        elif bb_pct < 0.05:
            signals.append(Signal("technical", "Below Lower Bollinger", "long", 0.6,
                                  metadata={"bb_pct": round(bb_pct, 3)}))
            score += 0.15

    # 4. SMA Cross (20/50)
    if len(closes) >= 50:
        sma20 = np.mean(closes[-20:])
        sma50 = np.mean(closes[-50:])
        if sma20 > sma50 * 1.01:
            signals.append(Signal("technical", "SMA20 > SMA50", "long", 0.5))
            score += 0.15
        elif sma20 < sma50 * 0.99:
            signals.append(Signal("technical", "SMA20 < SMA50", "short", 0.5))
            score -= 0.15

    # 5. Volume confirmation
    if len(volumes) >= 20 and np.mean(volumes[-20:]) > 0:
        vol_ratio = float(np.mean(volumes[-5:]) / np.mean(volumes[-20:]))
        price_direction = "long" if returns[-1] > 0 else "short"
        if vol_ratio > 1.5:
            signals.append(Signal("technical", "Volume Surge", price_direction, 0.6,
                                  metadata={"vol_ratio": round(vol_ratio, 2)}))
            score += 0.1 if price_direction == "long" else -0.1

    score = max(-1.0, min(1.0, score))
    return signals, score


def _quant_signals(
    closes: np.ndarray, returns: np.ndarray, volumes: np.ndarray
) -> tuple[list[Signal], float]:
    """Generate quantitative signals."""
    signals = []
    score = 0.0

    # 1. Momentum Z-Score (20d return vs 252d distribution)
    if len(returns) >= 252:
        ret_20d = float(np.sum(returns[-20:]))
        mu = float(np.mean([np.sum(returns[i:i+20]) for i in range(len(returns) - 20)]))
        sigma = float(np.std([np.sum(returns[i:i+20]) for i in range(len(returns) - 20)])) + 1e-10
        z_score = (ret_20d - mu) / sigma

        if z_score > 1.5:
            signals.append(Signal("quant", "Momentum Z-Score High", "long", min(0.9, abs(z_score)/3),
                                  metadata={"z_score": round(z_score, 2)}))
            score += 0.3
        elif z_score < -1.5:
            signals.append(Signal("quant", "Momentum Z-Score Low", "short", min(0.9, abs(z_score)/3),
                                  metadata={"z_score": round(z_score, 2)}))
            score -= 0.3
    elif len(returns) >= 60:
        ret_20d = float(np.sum(returns[-20:]))
        mu = float(np.mean(returns)) * 20
        sigma = float(np.std(returns)) * np.sqrt(20) + 1e-10
        z_score = (ret_20d - mu) / sigma
        if abs(z_score) > 1.5:
            direction = "long" if z_score > 0 else "short"
            signals.append(Signal("quant", "Momentum Z-Score", direction, min(0.7, abs(z_score)/3),
                                  metadata={"z_score": round(z_score, 2)}))
            score += 0.2 if z_score > 0 else -0.2

    # 2. Mean Reversion (distance from 50d SMA)
    if len(closes) >= 50:
        sma50 = np.mean(closes[-50:])
        deviation = (float(closes[-1]) - sma50) / sma50
        if deviation > 0.10:  # >10% above SMA50
            signals.append(Signal("quant", "Extended Above SMA50", "short", 0.5,
                                  metadata={"deviation_pct": round(deviation * 100, 1)}))
            score -= 0.15
        elif deviation < -0.10:  # >10% below SMA50
            signals.append(Signal("quant", "Extended Below SMA50", "long", 0.5,
                                  metadata={"deviation_pct": round(deviation * 100, 1)}))
            score += 0.15

    # 3. Volatility Regime
    if len(returns) >= 60:
        recent_vol = float(np.std(returns[-20:])) * np.sqrt(252)
        hist_vol = float(np.std(returns[-60:])) * np.sqrt(252)
        vol_ratio = recent_vol / (hist_vol + 1e-10)

        if vol_ratio > 1.5:
            signals.append(Signal("quant", "Volatility Expansion", "neutral", 0.6,
                                  metadata={"vol_ratio": round(vol_ratio, 2),
                                           "annual_vol": round(recent_vol, 4)}))
            score -= 0.1  # Higher vol = more cautious
        elif vol_ratio < 0.6:
            signals.append(Signal("quant", "Volatility Compression", "neutral", 0.4,
                                  metadata={"vol_ratio": round(vol_ratio, 2)}))

    # 4. Volume-Price Divergence
    if len(volumes) >= 20 and len(returns) >= 20:
        price_trend = float(np.mean(returns[-10:]))
        vol_trend = float(np.mean(volumes[-5:]) / (np.mean(volumes[-20:]) + 1e-10))
        if price_trend > 0.002 and vol_trend < 0.8:
            signals.append(Signal("quant", "Price Up / Volume Down Divergence", "short", 0.5,
                                  metadata={"price_trend": round(price_trend, 4),
                                           "vol_trend": round(vol_trend, 2)}))
            score -= 0.1
        elif price_trend < -0.002 and vol_trend > 1.3:
            signals.append(Signal("quant", "Capitulation Volume", "long", 0.6,
                                  metadata={"price_trend": round(price_trend, 4),
                                           "vol_trend": round(vol_trend, 2)}))
            score += 0.15

    # 5. Drawdown from High
    if len(closes) >= 252:
        max_high = float(np.max(closes[-252:]))
        current = float(closes[-1])
        drawdown = (current - max_high) / max_high
        if drawdown < -0.20:
            signals.append(Signal("quant", "Deep Drawdown (>20%)", "long", 0.5,
                                  metadata={"drawdown_pct": round(drawdown * 100, 1)}))
            score += 0.1

    score = max(-1.0, min(1.0, score))
    return signals, score


def _ema(data: np.ndarray, span: int) -> np.ndarray:
    """Calculate exponential moving average."""
    alpha = 2 / (span + 1)
    ema = np.zeros_like(data, dtype=float)
    ema[0] = data[0]
    for i in range(1, len(data)):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
    return ema


async def scan_universe(
    conn: asyncpg.Connection,
    asset_ids: list[UUID],
    min_score: float = 0.0,
    include_ai: bool = False,
) -> list[SignalSummary]:
    """Batch scan multiple assets for signals."""
    results = []
    for aid in asset_ids:
        try:
            result = await generate_signals(conn, aid, include_ai=include_ai)
            if result.success and abs(result.composite_score) >= min_score:
                top_signal = result.signals[0].signal_name if result.signals else "None"
                results.append(SignalSummary(
                    asset_id=str(aid),
                    symbol=result.symbol,
                    composite_score=result.composite_score,
                    direction=result.composite_direction,
                    top_signal=top_signal,
                ))
        except Exception:
            continue

    # Sort by absolute score (strongest signals first)
    results.sort(key=lambda x: abs(x.composite_score), reverse=True)
    return results


async def get_signal_history(
    conn: asyncpg.Connection,
    asset_id: UUID,
    days: int = 30,
) -> list[dict]:
    """Get recent signal history for an asset."""
    rows = await conn.fetch(
        """SELECT signal_type, signal_name, direction, strength, confidence, metadata, created_at
           FROM trading_signals
           WHERE asset_id = $1 AND created_at >= NOW() - INTERVAL '%s days'
           ORDER BY created_at DESC
           LIMIT 100""" % days,
        asset_id,
    )
    return [
        {
            "signal_type": r["signal_type"],
            "signal_name": r["signal_name"],
            "direction": r["direction"],
            "strength": float(r["strength"]),
            "confidence": float(r["confidence"] or 0),
            "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]
