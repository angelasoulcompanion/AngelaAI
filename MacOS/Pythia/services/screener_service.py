"""
Pythia — Smart Screener Service
NL query → structured filters via Claude API, preset screens.
"""
import json
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

import asyncpg

from config import PythiaConfig


@dataclass
class ScreenerResult:
    query: str
    results: list[dict] = field(default_factory=list)
    filters_applied: list[dict] = field(default_factory=list)
    total: int = 0
    success: bool = True
    message: str = ""


PRESET_SCREENS = {
    "oversold_bounce": {
        "name": "Oversold Bounce Candidates",
        "description": "Stocks with RSI < 35 and positive 5-day momentum",
        "sql_filter": "rsi < 35 AND momentum_5d > 0",
    },
    "high_volume_movers": {
        "name": "High Volume Movers",
        "description": "Volume > 2x 20-day average with significant price move",
        "sql_filter": "volume_ratio > 2.0",
    },
    "trend_following": {
        "name": "Trend Following",
        "description": "SMA20 > SMA50 with positive momentum",
        "sql_filter": "sma20_above_sma50 = true AND momentum_20d > 0.03",
    },
    "low_volatility": {
        "name": "Low Volatility Income",
        "description": "Annual volatility < 20% with stable price action",
        "sql_filter": "annual_vol < 0.20",
    },
    "mean_reversion": {
        "name": "Mean Reversion Setup",
        "description": "Price > 10% below 50-day SMA (potential snap-back)",
        "sql_filter": "deviation_from_sma50 < -0.10",
    },
}


async def natural_language_screen(
    conn: asyncpg.Connection,
    query: str,
) -> ScreenerResult:
    """Convert NL query to structured filters via Claude, then scan assets."""
    # Get all active assets
    assets = await conn.fetch(
        "SELECT asset_id, symbol, name, asset_type, sector FROM assets WHERE is_active = true ORDER BY symbol"
    )

    if not assets:
        return ScreenerResult(query=query, success=False, message="No active assets")

    # Use Claude to parse NL query into actionable filters
    from services.llm_service import llm_service
    import numpy as np

    prompt = f"""Parse this stock screening query into structured filters.
Query: "{query}"

Available filter types: rsi, momentum, volume_ratio, sma_cross, volatility, price_change, sector
Respond with JSON only:
{{"filters": [{{"type": "rsi", "operator": "<", "value": 30}}, ...], "sort_by": "composite_score", "direction": "desc"}}"""

    parsed, resp = await llm_service.complete_json(
        prompt=prompt,
        system="You are a stock screener parser. Convert natural language to structured filters. JSON only.",
        max_tokens=256,
        conn=conn, cache_ttl=PythiaConfig.CACHE_TTL_SCREENER, feature="screener_parse",
    )

    filters = parsed.get("filters", []) if parsed else []

    # Scan each asset with signals
    from services.signal_service import generate_signals
    from services.price_fetcher_service import PriceFetcherService

    results = []
    for asset in assets[:PythiaConfig.SCREENER_MAX_RESULTS]:
        asset_id = asset["asset_id"]
        symbol = asset["symbol"]

        try:
            # Get basic price data
            prices = await conn.fetch(
                """SELECT close_price, volume FROM historical_prices
                   WHERE asset_id = $1
                   ORDER BY date DESC LIMIT 60""",
                asset_id,
            )

            if len(prices) < 20:
                continue

            closes = np.array([float(p["close_price"]) for p in reversed(prices)])
            volumes = np.array([float(p["volume"] or 0) for p in reversed(prices)])
            returns = np.diff(np.log(closes))

            # Calculate screening metrics
            metrics = _calc_screen_metrics(closes, volumes, returns)

            # Apply filters
            if _passes_filters(metrics, filters):
                results.append({
                    "asset_id": str(asset_id),
                    "symbol": symbol,
                    "name": asset["name"],
                    "sector": asset["sector"],
                    "price": round(float(closes[-1]), 4),
                    **metrics,
                })
        except Exception:
            continue

    # Sort by composite score
    sort_by = parsed.get("sort_by", "composite_score") if parsed else "composite_score"
    results.sort(key=lambda x: abs(x.get(sort_by, 0)), reverse=True)

    return ScreenerResult(
        query=query,
        results=results[:PythiaConfig.SCREENER_MAX_RESULTS],
        filters_applied=filters,
        total=len(results),
    )


async def preset_screen(
    conn: asyncpg.Connection,
    preset_name: str,
) -> ScreenerResult:
    """Run a preset screen."""
    if preset_name not in PRESET_SCREENS:
        return ScreenerResult(query=preset_name, success=False, message=f"Preset '{preset_name}' not found")

    preset = PRESET_SCREENS[preset_name]

    # Get all assets and scan
    assets = await conn.fetch(
        "SELECT asset_id, symbol, name, sector FROM assets WHERE is_active = true ORDER BY symbol"
    )

    import numpy as np

    results = []
    for asset in assets[:PythiaConfig.SCREENER_MAX_RESULTS]:
        try:
            prices = await conn.fetch(
                """SELECT close_price, volume FROM historical_prices
                   WHERE asset_id = $1
                   ORDER BY date DESC LIMIT 60""",
                asset["asset_id"],
            )
            if len(prices) < 20:
                continue

            closes = np.array([float(p["close_price"]) for p in reversed(prices)])
            volumes = np.array([float(p["volume"] or 0) for p in reversed(prices)])
            returns = np.diff(np.log(closes))
            metrics = _calc_screen_metrics(closes, volumes, returns)

            if _passes_preset(metrics, preset_name):
                results.append({
                    "asset_id": str(asset["asset_id"]),
                    "symbol": asset["symbol"],
                    "name": asset["name"],
                    "sector": asset["sector"],
                    "price": round(float(closes[-1]), 4),
                    **metrics,
                })
        except Exception:
            continue

    results.sort(key=lambda x: abs(x.get("composite_score", 0)), reverse=True)

    return ScreenerResult(
        query=preset["name"],
        results=results,
        total=len(results),
    )


def _calc_screen_metrics(closes, volumes, returns) -> dict:
    """Calculate screening metrics for an asset."""
    import numpy as np

    # RSI
    if len(returns) >= 14:
        gains = np.where(returns[-14:] > 0, returns[-14:], 0)
        losses = np.where(returns[-14:] < 0, -returns[-14:], 0)
        rs = np.mean(gains) / (np.mean(losses) + 1e-10)
        rsi = 100 - 100 / (1 + rs)
    else:
        rsi = 50

    # Momentum
    momentum_5d = float(np.sum(returns[-5:])) if len(returns) >= 5 else 0
    momentum_20d = float(np.sum(returns[-20:])) if len(returns) >= 20 else 0

    # Volume ratio
    if len(volumes) >= 20 and np.mean(volumes[-20:]) > 0:
        volume_ratio = float(np.mean(volumes[-5:]) / np.mean(volumes[-20:]))
    else:
        volume_ratio = 1.0

    # SMA cross
    sma20_above_sma50 = False
    if len(closes) >= 50:
        sma20_above_sma50 = float(np.mean(closes[-20:])) > float(np.mean(closes[-50:]))

    # Volatility
    annual_vol = float(np.std(returns[-20:]) * np.sqrt(252)) if len(returns) >= 20 else 0

    # Deviation from SMA50
    if len(closes) >= 50:
        sma50 = float(np.mean(closes[-50:]))
        deviation = (float(closes[-1]) - sma50) / sma50
    else:
        deviation = 0

    # Composite score
    composite = 0.0
    if rsi < 30: composite += 0.3
    elif rsi > 70: composite -= 0.3
    if momentum_20d > 0.05: composite += 0.2
    elif momentum_20d < -0.05: composite -= 0.2
    if sma20_above_sma50: composite += 0.15
    if volume_ratio > 1.5: composite += 0.1

    return {
        "rsi": round(float(rsi), 1),
        "momentum_5d": round(momentum_5d, 4),
        "momentum_20d": round(momentum_20d, 4),
        "volume_ratio": round(volume_ratio, 2),
        "sma20_above_sma50": sma20_above_sma50,
        "annual_vol": round(annual_vol, 4),
        "deviation_from_sma50": round(deviation, 4),
        "composite_score": round(composite, 3),
    }


def _passes_filters(metrics: dict, filters: list[dict]) -> bool:
    """Check if metrics pass all filters."""
    if not filters:
        return True

    for f in filters:
        ftype = f.get("type", "")
        op = f.get("operator", "")
        value = f.get("value")

        if ftype not in metrics or value is None:
            continue

        actual = metrics[ftype]
        if isinstance(actual, bool):
            if op == "=" and actual != value:
                return False
        else:
            if op == "<" and actual >= value:
                return False
            if op == ">" and actual <= value:
                return False
            if op == "<=" and actual > value:
                return False
            if op == ">=" and actual < value:
                return False

    return True


def _passes_preset(metrics: dict, preset_name: str) -> bool:
    """Check if metrics pass preset screen."""
    if preset_name == "oversold_bounce":
        return metrics["rsi"] < 35 and metrics["momentum_5d"] > 0
    elif preset_name == "high_volume_movers":
        return metrics["volume_ratio"] > 2.0
    elif preset_name == "trend_following":
        return metrics["sma20_above_sma50"] and metrics["momentum_20d"] > 0.03
    elif preset_name == "low_volatility":
        return metrics["annual_vol"] < 0.20 and metrics["annual_vol"] > 0
    elif preset_name == "mean_reversion":
        return metrics["deviation_from_sma50"] < -0.10
    return True
