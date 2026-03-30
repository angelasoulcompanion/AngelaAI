"""
Pythia — Event Impact Analyzer Service
Event study methodology for earnings, dividends, economic releases.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np


@dataclass
class EventImpactResult:
    asset_id: str
    symbol: str
    event_type: str
    avg_move_pct: float = 0.0
    avg_pre_move: float = 0.0
    avg_post_move: float = 0.0
    positive_rate: float = 0.0
    events_analyzed: int = 0
    upcoming_events: list[dict] = field(default_factory=list)
    historical_events: list[dict] = field(default_factory=list)
    success: bool = True
    message: str = ""


async def analyze_event_impact(
    conn: asyncpg.Connection,
    asset_id: UUID,
    event_type: str = "earnings",
) -> EventImpactResult:
    """Analyze historical event impact using event study methodology."""
    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return EventImpactResult(asset_id=str(asset_id), symbol="", event_type=event_type,
                                 success=False, message="Asset not found")
    symbol = row["symbol"]

    # Get price data
    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    prices = await conn.fetch(
        """SELECT date, close_price FROM historical_prices
           WHERE asset_id = $1 AND date >= $2
           ORDER BY date""",
        asset_id, date.today() - timedelta(days=730),
    )

    if len(prices) < 60:
        return EventImpactResult(asset_id=str(asset_id), symbol=symbol, event_type=event_type,
                                 success=False, message="Insufficient price data")

    closes = np.array([float(p["close_price"]) for p in prices])
    dates = [p["date"] for p in prices]
    returns = np.diff(np.log(closes))

    # Find significant moves as proxy for events
    # (In production, would use actual earnings dates from yfinance calendar)
    event_indices = _detect_event_dates(returns, event_type)

    if not event_indices:
        # Try yfinance calendar
        upcoming = await _get_upcoming_events(symbol)
        return EventImpactResult(
            asset_id=str(asset_id), symbol=symbol, event_type=event_type,
            upcoming_events=upcoming,
            message="No historical events detected, showing upcoming only",
        )

    # Event study: measure [-5, +5] day window around each event
    window = 5
    historical = []
    pre_moves = []
    post_moves = []
    all_moves = []

    for idx in event_indices:
        if idx < window or idx + window >= len(returns):
            continue

        pre = float(np.sum(returns[idx - window:idx]))
        post = float(np.sum(returns[idx:idx + window]))
        event_ret = float(returns[idx])

        pre_moves.append(pre)
        post_moves.append(post)
        all_moves.append(event_ret)

        historical.append({
            "date": str(dates[idx + 1]) if idx + 1 < len(dates) else "",
            "event_return": round(event_ret * 100, 2),
            "pre_5d": round(pre * 100, 2),
            "post_5d": round(post * 100, 2),
        })

    avg_move = float(np.mean(all_moves)) if all_moves else 0
    avg_pre = float(np.mean(pre_moves)) if pre_moves else 0
    avg_post = float(np.mean(post_moves)) if post_moves else 0
    positive_rate = len([m for m in all_moves if m > 0]) / max(len(all_moves), 1)

    upcoming = await _get_upcoming_events(symbol)

    return EventImpactResult(
        asset_id=str(asset_id),
        symbol=symbol,
        event_type=event_type,
        avg_move_pct=round(avg_move * 100, 2),
        avg_pre_move=round(avg_pre * 100, 2),
        avg_post_move=round(avg_post * 100, 2),
        positive_rate=round(positive_rate, 4),
        events_analyzed=len(historical),
        upcoming_events=upcoming,
        historical_events=historical[-10:],
    )


def _detect_event_dates(returns: np.ndarray, event_type: str) -> list[int]:
    """Detect significant events from price action."""
    vol = np.std(returns)
    threshold = 2.0 * vol  # 2-sigma moves

    if event_type == "earnings":
        # Look for large single-day moves (proxy for earnings)
        indices = [i for i in range(len(returns)) if abs(returns[i]) > threshold]
    elif event_type == "dividend":
        # Look for negative gaps (ex-dividend)
        indices = [i for i in range(len(returns)) if returns[i] < -threshold * 0.5]
    else:
        indices = [i for i in range(len(returns)) if abs(returns[i]) > threshold]

    # Deduplicate (keep at least 20 days apart)
    filtered = []
    for idx in indices:
        if not filtered or idx - filtered[-1] >= 20:
            filtered.append(idx)

    return filtered


async def _get_upcoming_events(symbol: str) -> list[dict]:
    """Get upcoming events from yfinance."""
    events = []
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)

        # Earnings dates
        if hasattr(ticker, 'calendar') and ticker.calendar is not None:
            cal = ticker.calendar
            if isinstance(cal, dict):
                for key, val in cal.items():
                    events.append({"type": "calendar", "event": str(key), "value": str(val)})

        # Dividends
        if hasattr(ticker, 'dividends') and not ticker.dividends.empty:
            last_div = ticker.dividends.iloc[-1]
            events.append({"type": "dividend", "event": "Last Dividend", "value": f"{last_div:.4f}"})

    except Exception:
        pass

    return events
