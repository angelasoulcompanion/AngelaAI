"""
Pythia — Market data from Yahoo Finance
"""
import json
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn
from helpers.financial_utils import get_yahoo_symbol

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/quote/{symbol}")
async def get_quote(symbol: str, conn=Depends(get_conn)):
    """Get real-time quote for a symbol. Caches in DB for 5 minutes."""
    # Check cache first
    cached = await conn.fetchrow("""
        SELECT metadata FROM assets
        WHERE symbol = $1 AND metadata->>'last_quote_at' IS NOT NULL
          AND (metadata->>'last_quote_at')::timestamptz > NOW() - INTERVAL '5 minutes'
    """, symbol.upper())

    if cached and cached["metadata"]:
        meta = json.loads(cached["metadata"]) if isinstance(cached["metadata"], str) else cached["metadata"]
        if "quote" in meta:
            return meta["quote"]

    # Fetch from Yahoo Finance
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    yahoo_symbol = get_yahoo_symbol(symbol)
    ticker = yf.Ticker(yahoo_symbol)
    info = ticker.info

    if not info or "regularMarketPrice" not in info:
        raise HTTPException(status_code=404, detail=f"No quote data for {symbol}")

    quote = {
        "symbol": symbol.upper(),
        "name": info.get("longName") or info.get("shortName", symbol),
        "current_price": info.get("regularMarketPrice"),
        "previous_close": info.get("previousClose"),
        "open_price": info.get("open"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "dividend_yield": info.get("dividendYield"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
        "beta": info.get("beta"),
        "exchange": info.get("exchange"),
        "currency": info.get("currency"),
    }

    # Calculate change
    prev = info.get("previousClose")
    curr = info.get("regularMarketPrice")
    if prev and curr:
        quote["change"] = round(curr - prev, 4)
        quote["change_percent"] = round((curr - prev) / prev * 100, 2)

    # Cache the quote
    await conn.execute("""
        UPDATE assets SET metadata = metadata || $1::jsonb, updated_at = NOW()
        WHERE symbol = $2
    """, json.dumps({"quote": quote, "last_quote_at": datetime.utcnow().isoformat()}),
        symbol.upper())

    return quote


@router.get("/history/{symbol}")
async def get_history(
    symbol: str,
    period: str = Query("1y", description="1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query("1d", description="1d, 1wk, 1mo"),
    conn=Depends(get_conn)
):
    """Get historical OHLCV data from Yahoo Finance."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    yahoo_symbol = get_yahoo_symbol(symbol)
    ticker = yf.Ticker(yahoo_symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        raise HTTPException(status_code=404, detail=f"No history for {symbol}")

    data = []
    for date_idx, row in hist.iterrows():
        data.append({
            "date": date_idx.strftime("%Y-%m-%d"),
            "open": round(row.get("Open", 0), 4),
            "high": round(row.get("High", 0), 4),
            "low": round(row.get("Low", 0), 4),
            "close": round(row.get("Close", 0), 4),
            "volume": int(row.get("Volume", 0)),
        })
    return {"symbol": symbol.upper(), "period": period, "interval": interval, "data": data}


@router.get("/fetch-prices/{asset_id}")
async def fetch_and_store_prices(
    asset_id: UUID,
    days: int = Query(365, ge=1, le=3650),
    conn=Depends(get_conn)
):
    """Fetch prices from Yahoo Finance and store in historical_prices table."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    # Get asset symbol
    asset = await conn.fetchrow(
        "SELECT symbol, exchange FROM assets WHERE asset_id = $1", asset_id
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    yahoo_symbol = get_yahoo_symbol(asset["symbol"], asset["exchange"])
    ticker = yf.Ticker(yahoo_symbol)
    end = datetime.now()
    start = end - timedelta(days=days)
    hist = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

    if hist.empty:
        return {"symbol": asset["symbol"], "records_fetched": 0, "records_inserted": 0}

    inserted = 0
    for date_idx, row in hist.iterrows():
        try:
            await conn.execute("""
                INSERT INTO historical_prices (asset_id, date, open_price, high_price,
                    low_price, close_price, adj_close, volume, dividends, stock_splits)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (asset_id, date) DO UPDATE SET
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    fetched_at = NOW()
            """,
                asset_id, date_idx.date(),
                float(row.get("Open", 0)), float(row.get("High", 0)),
                float(row.get("Low", 0)), float(row.get("Close", 0)),
                float(row.get("Close", 0)), int(row.get("Volume", 0)),
                float(row.get("Dividends", 0)), float(row.get("Stock Splits", 1)),
            )
            inserted += 1
        except Exception:
            continue

    return {
        "symbol": asset["symbol"],
        "records_fetched": len(hist),
        "records_inserted": inserted,
        "date_range": {
            "start": hist.index[0].strftime("%Y-%m-%d"),
            "end": hist.index[-1].strftime("%Y-%m-%d"),
        }
    }


@router.get("/search")
async def search_market(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=30)):
    """Search for symbols via Yahoo Finance."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    # Try direct ticker lookup
    results = []
    symbols_to_try = [q.upper(), f"{q.upper()}.BK"]

    for sym in symbols_to_try:
        try:
            ticker = yf.Ticker(sym)
            info = ticker.info
            if info and "symbol" in info:
                results.append({
                    "symbol": info.get("symbol", sym),
                    "name": info.get("longName") or info.get("shortName", ""),
                    "exchange": info.get("exchange", ""),
                    "type": info.get("quoteType", ""),
                    "currency": info.get("currency", ""),
                })
        except Exception:
            continue

    return results[:limit]
