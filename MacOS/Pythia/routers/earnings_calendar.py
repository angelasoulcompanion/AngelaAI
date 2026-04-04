"""
Pythia — Earnings Calendar & Economic Events
Fetches upcoming earnings dates + key economic events for watchlist stocks.
"""
from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn
from helpers.financial_utils import get_yahoo_symbol
from services.cache_service import cache, MemoryCache

router = APIRouter(prefix="/api/earnings", tags=["earnings"])


@router.get("/calendar")
async def earnings_calendar(
    watchlist_id: UUID = Query(None, description="Filter by watchlist"),
    days: int = Query(30, ge=1, le=90, description="Days ahead to look"),
    conn=Depends(get_conn),
):
    """Get upcoming earnings dates for watchlist assets."""
    cache_key = f"earnings:{watchlist_id or 'all'}:{days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Get symbols
    if watchlist_id:
        rows = await conn.fetch("""
            SELECT DISTINCT a.symbol, a.name, a.exchange, a.currency
            FROM watchlist_items wi
            JOIN watchlists w ON wi.watchlist_id = w.watchlist_id
            JOIN assets a ON wi.asset_id = a.asset_id
            WHERE w.is_active = true AND w.watchlist_id = $1
              AND a.asset_type = 'stock'
            ORDER BY a.symbol
        """, watchlist_id)
    else:
        rows = await conn.fetch("""
            SELECT DISTINCT a.symbol, a.name, a.exchange, a.currency
            FROM watchlist_items wi
            JOIN watchlists w ON wi.watchlist_id = w.watchlist_id
            JOIN assets a ON wi.asset_id = a.asset_id
            WHERE w.is_active = true AND a.asset_type = 'stock'
            ORDER BY a.symbol
        """)

    if not rows:
        return {"earnings": [], "count": 0}

    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    today = date.today()
    cutoff = today + timedelta(days=days)
    earnings = []

    for row in rows:
        symbol = row["symbol"]
        yahoo_sym = get_yahoo_symbol(symbol, row["exchange"])
        try:
            ticker = yf.Ticker(yahoo_sym)
            cal = ticker.calendar
            if cal is None or cal.empty:
                continue

            # yfinance calendar returns a DataFrame or dict
            if hasattr(cal, 'to_dict'):
                cal_dict = cal.to_dict()
                earnings_date = cal_dict.get("Earnings Date", {})
                # Can be a dict with index 0,1 for date range
                if isinstance(earnings_date, dict):
                    dates = list(earnings_date.values())
                else:
                    dates = [earnings_date] if earnings_date else []
            elif isinstance(cal, dict):
                dates = cal.get("Earnings Date", [])
                if not isinstance(dates, list):
                    dates = [dates]
            else:
                continue

            for d in dates:
                if d is None:
                    continue
                if hasattr(d, 'date'):
                    d = d.date()
                elif isinstance(d, str):
                    try:
                        d = datetime.strptime(d[:10], "%Y-%m-%d").date()
                    except ValueError:
                        continue

                if today <= d <= cutoff:
                    earnings.append({
                        "symbol": symbol,
                        "name": row["name"],
                        "earnings_date": d.isoformat(),
                        "days_until": (d - today).days,
                        "currency": row["currency"] or "",
                    })
                    break  # one date per symbol
        except Exception:
            continue

    # Sort by date
    earnings.sort(key=lambda x: x["earnings_date"])

    result = {
        "earnings": earnings,
        "count": len(earnings),
        "period_days": days,
        "generated_at": datetime.now().isoformat(),
    }

    cache.set(cache_key, result, MemoryCache.EARNINGS_TTL)
    return result


@router.get("/upcoming/{symbol}")
async def upcoming_earnings(symbol: str):
    """Get earnings details for a specific symbol."""
    cache_key = f"earnings_detail:{symbol.upper()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    yahoo_sym = get_yahoo_symbol(symbol)
    ticker = yf.Ticker(yahoo_sym)
    info = ticker.info or {}

    result = {
        "symbol": symbol.upper(),
        "name": info.get("longName") or info.get("shortName", symbol),
        "earnings_date": None,
        "revenue_estimate": None,
        "eps_estimate": None,
        "last_eps_actual": info.get("trailingEps"),
        "last_revenue": info.get("totalRevenue"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
    }

    # Get calendar
    try:
        cal = ticker.calendar
        if cal is not None:
            if hasattr(cal, 'to_dict'):
                cal_dict = cal.to_dict()
                dates = cal_dict.get("Earnings Date", {})
                if isinstance(dates, dict):
                    vals = list(dates.values())
                    if vals:
                        d = vals[0]
                        result["earnings_date"] = d.isoformat() if hasattr(d, 'isoformat') else str(d)
                revenue = cal_dict.get("Revenue Avg", {})
                if isinstance(revenue, dict) and revenue:
                    result["revenue_estimate"] = list(revenue.values())[0]
                eps = cal_dict.get("Earnings Avg", {})
                if isinstance(eps, dict) and eps:
                    result["eps_estimate"] = list(eps.values())[0]
    except Exception:
        pass

    cache.set(cache_key, result, MemoryCache.EARNINGS_TTL)
    return result


@router.get("/economic-events")
async def economic_events(
    days: int = Query(7, ge=1, le=30, description="Days ahead"),
):
    """Get major upcoming economic events (FOMC, CPI, NFP, etc.)."""
    cache_key = f"econ_events:{days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Static calendar of recurring major US economic events
    # In production, this would come from an API like Trading Economics
    today = date.today()
    cutoff = today + timedelta(days=days)

    # Generate recurring events for the period
    events = _generate_economic_events(today, cutoff)

    result = {
        "events": events,
        "count": len(events),
        "period_days": days,
    }

    cache.set(cache_key, result, 3600)
    return result


def _generate_economic_events(start: date, end: date) -> list[dict]:
    """Generate known recurring economic events in date range."""
    events = []

    # Major recurring events (approximate typical dates)
    # FOMC meetings 2026 (8 per year)
    fomc_dates = [
        date(2026, 1, 28), date(2026, 3, 18), date(2026, 5, 6),
        date(2026, 6, 17), date(2026, 7, 29), date(2026, 9, 16),
        date(2026, 11, 4), date(2026, 12, 16),
    ]
    for d in fomc_dates:
        if start <= d <= end:
            events.append({
                "date": d.isoformat(),
                "event": "FOMC Rate Decision",
                "impact": "high",
                "country": "US",
                "category": "central_bank",
            })

    # Monthly events (approximate — first Friday = NFP, ~10th = CPI)
    import calendar
    for month in range(start.month, min(end.month + 2, 13)):
        year = start.year
        # NFP — first Friday
        cal = calendar.monthcalendar(year, month)
        first_friday = None
        for week in cal:
            if week[calendar.FRIDAY] != 0:
                first_friday = date(year, month, week[calendar.FRIDAY])
                break
        if first_friday and start <= first_friday <= end:
            events.append({
                "date": first_friday.isoformat(),
                "event": "Non-Farm Payrolls (NFP)",
                "impact": "high",
                "country": "US",
                "category": "employment",
            })

        # CPI — ~10th-15th of month
        cpi_day = date(year, month, 12)
        if start <= cpi_day <= end:
            events.append({
                "date": cpi_day.isoformat(),
                "event": "CPI (Consumer Price Index)",
                "impact": "high",
                "country": "US",
                "category": "inflation",
            })

        # BOT (Bank of Thailand) — quarterly
        if month in (2, 4, 6, 8, 10, 12):
            bot_day = date(year, month, 20)
            if start <= bot_day <= end:
                events.append({
                    "date": bot_day.isoformat(),
                    "event": "BOT Rate Decision",
                    "impact": "high",
                    "country": "TH",
                    "category": "central_bank",
                })

    events.sort(key=lambda x: x["date"])
    return events
