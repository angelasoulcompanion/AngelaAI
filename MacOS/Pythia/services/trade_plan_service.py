"""
Pythia — Trade Plan Generator Service
AI-powered entry/SL/TP plans with position sizing.
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
class TradePlan:
    plan_id: str = ""
    asset_id: str = ""
    symbol: str = ""
    direction: str = "long"
    current_price: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    take_profit_3: float = 0.0
    position_size_pct: float = 0.0
    risk_reward: float = 0.0
    risk_pct: float = 0.0
    rationale: str = ""
    regime: str = ""
    support_levels: list[float] = field(default_factory=list)
    resistance_levels: list[float] = field(default_factory=list)
    signals_summary: str = ""
    success: bool = True
    message: str = ""


async def generate_trade_plan(
    conn: asyncpg.Connection,
    asset_id: UUID,
    risk_per_trade: float = 0.02,
) -> TradePlan:
    """Generate a complete trade plan for an asset."""
    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return TradePlan(asset_id=str(asset_id), success=False, message="Asset not found")
    symbol = row["symbol"]

    # Ensure fresh prices
    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    prices = await conn.fetch(
        """SELECT date, close_price, volume FROM historical_prices
           WHERE asset_id = $1 AND date >= $2
           ORDER BY date""",
        asset_id, date.today() - timedelta(days=120),
    )

    if len(prices) < 30:
        return TradePlan(asset_id=str(asset_id), symbol=symbol,
                         success=False, message="Insufficient data")

    closes = np.array([float(p["close_price"]) for p in prices])
    volumes = np.array([float(p["volume"] or 0) for p in prices])
    current_price = float(closes[-1])

    # Calculate ATR for stop placement
    daily_ranges = np.abs(np.diff(closes))
    atr_14 = float(np.mean(daily_ranges[-14:])) if len(daily_ranges) >= 14 else float(np.mean(daily_ranges))

    # Find support/resistance
    support, resistance = _find_sr_levels(closes)

    # Get signal direction
    from services.signal_service import generate_signals
    signals = await generate_signals(conn, asset_id, include_ai=False)
    direction = signals.composite_direction if signals.success else "long"
    composite_score = signals.composite_score if signals.success else 0

    # Get regime
    regime = ""
    try:
        from services.regime_service import detect_regime
        regime_result = await detect_regime(conn, symbol, days=200)
        if regime_result.success:
            regime = regime_result.regime
    except Exception:
        pass

    # Calculate entry/SL/TP
    if direction == "long":
        entry = current_price
        sl = max(current_price - 2 * atr_14, support[0] if support else current_price * 0.95)
        tp1 = current_price + 1 * (entry - sl)  # 1R
        tp2 = current_price + 2 * (entry - sl)  # 2R
        tp3 = current_price + 3 * (entry - sl)  # 3R
        if resistance:
            tp1 = min(tp1, resistance[0]) if resistance else tp1
    elif direction == "short":
        entry = current_price
        sl = min(current_price + 2 * atr_14, resistance[0] if resistance else current_price * 1.05)
        tp1 = current_price - 1 * (sl - entry)
        tp2 = current_price - 2 * (sl - entry)
        tp3 = current_price - 3 * (sl - entry)
    else:
        entry = current_price
        sl = current_price - 2 * atr_14
        tp1 = current_price + 2 * atr_14
        tp2 = current_price + 3 * atr_14
        tp3 = current_price + 4 * atr_14

    risk_pct = abs(entry - sl) / entry
    rr = abs(tp2 - entry) / abs(entry - sl) if abs(entry - sl) > 0 else 0
    position_size = min(risk_per_trade / (risk_pct + 1e-10), 0.25)

    signals_summary = f"Composite: {composite_score:+.3f} ({direction})"

    plan = TradePlan(
        asset_id=str(asset_id),
        symbol=symbol,
        direction=direction,
        current_price=round(current_price, 4),
        entry_price=round(entry, 4),
        stop_loss=round(sl, 4),
        take_profit_1=round(tp1, 4),
        take_profit_2=round(tp2, 4),
        take_profit_3=round(tp3, 4),
        position_size_pct=round(position_size, 4),
        risk_reward=round(rr, 2),
        risk_pct=round(risk_pct, 4),
        regime=regime,
        support_levels=[round(s, 4) for s in support[:3]],
        resistance_levels=[round(r, 4) for r in resistance[:3]],
        signals_summary=signals_summary,
    )

    # AI rationale via Claude
    try:
        from services.llm_service import llm_service
        prompt = f"""Generate a trade plan rationale for {symbol}:
Direction: {direction} | Entry: {entry:.4f} | SL: {sl:.4f} | TP1: {tp1:.4f} | TP2: {tp2:.4f}
Risk: {risk_pct*100:.1f}% | R:R = {rr:.1f}:1 | Regime: {regime}
Signals: {signals_summary}
Support: {support[:3]} | Resistance: {resistance[:3]}

Write 3 concise sentences: (1) why this trade, (2) risk factors, (3) key level to watch."""

        resp = await llm_service.complete(
            prompt=prompt,
            system="You are a professional trader writing trade plans. Be specific and actionable.",
            max_tokens=512,
            conn=conn, cache_ttl=PythiaConfig.CACHE_TTL_TRADE_PLAN, feature="trade_plan",
        )
        if resp.success:
            plan.rationale = resp.text
    except Exception:
        pass

    # Store in DB
    try:
        row = await conn.fetchrow(
            """INSERT INTO trade_plans
               (asset_id, direction, entry_price, stop_loss, take_profit_1, take_profit_2, take_profit_3,
                position_size, risk_reward, rationale, signals_used, regime_context, llm_provider)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
               RETURNING plan_id""",
            asset_id, direction, entry, sl, tp1, tp2, tp3,
            position_size, rr, plan.rationale,
            json.dumps({"composite": composite_score}),
            regime, "claude",
        )
        if row:
            plan.plan_id = str(row["plan_id"])
    except Exception:
        pass

    return plan


def _find_sr_levels(closes: np.ndarray, n_levels: int = 3) -> tuple[list[float], list[float]]:
    """Find support and resistance levels from price data."""
    if len(closes) < 10:
        return [], []

    # Find peaks and troughs
    order = max(3, len(closes) // 20)
    peaks = []
    troughs = []

    for i in range(order, len(closes) - order):
        if all(closes[i] >= closes[i - j] for j in range(1, order + 1)) and \
           all(closes[i] >= closes[i + j] for j in range(1, order + 1)):
            peaks.append(float(closes[i]))
        if all(closes[i] <= closes[i - j] for j in range(1, order + 1)) and \
           all(closes[i] <= closes[i + j] for j in range(1, order + 1)):
            troughs.append(float(closes[i]))

    current = float(closes[-1])
    support = sorted([t for t in troughs if t < current], reverse=True)[:n_levels]
    resistance = sorted([p for p in peaks if p > current])[:n_levels]

    return support, resistance


async def list_trade_plans(conn: asyncpg.Connection, status: str = "active") -> list[dict]:
    """List trade plans."""
    rows = await conn.fetch(
        """SELECT plan_id, asset_id, direction, entry_price, stop_loss,
                  take_profit_1, risk_reward, status, created_at
           FROM trade_plans WHERE status = $1
           ORDER BY created_at DESC LIMIT 50""",
        status,
    )

    results = []
    for r in rows:
        symbol_row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", r["asset_id"])
        results.append({
            "plan_id": str(r["plan_id"]),
            "asset_id": str(r["asset_id"]),
            "symbol": symbol_row["symbol"] if symbol_row else "",
            "direction": r["direction"],
            "entry_price": float(r["entry_price"]),
            "stop_loss": float(r["stop_loss"]),
            "take_profit_1": float(r["take_profit_1"] or 0),
            "risk_reward": float(r["risk_reward"] or 0),
            "status": r["status"],
            "created_at": str(r["created_at"]),
        })

    return results
