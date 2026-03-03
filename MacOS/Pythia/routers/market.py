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


async def _get_watchlist_symbols(conn, watchlist_id: UUID = None) -> list:
    """Get unique symbols from watchlists."""
    if watchlist_id is not None:
        return await conn.fetch("""
            SELECT DISTINCT a.symbol, a.name, a.asset_type::text, a.exchange, a.currency
            FROM watchlist_items wi
            JOIN watchlists w ON wi.watchlist_id = w.watchlist_id
            JOIN assets a ON wi.asset_id = a.asset_id
            WHERE w.is_active = true AND w.watchlist_id = $1
            ORDER BY a.symbol
        """, watchlist_id)
    else:
        return await conn.fetch("""
            SELECT DISTINCT a.symbol, a.name, a.asset_type::text, a.exchange, a.currency
            FROM watchlist_items wi
            JOIN watchlists w ON wi.watchlist_id = w.watchlist_id
            JOIN assets a ON wi.asset_id = a.asset_id
            WHERE w.is_active = true
            ORDER BY a.symbol
        """)


@router.get("/watchlist-quotes-cached")
async def get_watchlist_quotes_cached(
    watchlist_id: UUID = Query(None, description="Filter by watchlist ID"),
    conn=Depends(get_conn),
):
    """Return watchlist quotes from DB cache only — no Yahoo calls. Always instant."""
    rows = await _get_watchlist_symbols(conn, watchlist_id)
    if not rows:
        return []

    symbols = [r["symbol"] for r in rows]
    cached = await conn.fetch("""
        SELECT symbol, metadata->'cached_quote' AS cq
        FROM assets
        WHERE symbol = ANY($1::text[])
          AND metadata->'cached_quote' IS NOT NULL
    """, symbols)

    cache_map = {}
    for c in cached:
        cq = c["cq"]
        if cq:
            cache_map[c["symbol"]] = json.loads(cq) if isinstance(cq, str) else cq

    results = []
    for row in rows:
        sym = row["symbol"]
        if sym in cache_map:
            results.append(cache_map[sym])
        else:
            # No cache — return skeleton with DB name
            results.append({
                "symbol": sym,
                "name": row["name"],
                "current_price": None,
                "change": None,
                "change_percent": None,
                "sparkline": [],
                "currency": row["currency"] or "",
                "volume": None,
            })
    return results


@router.get("/watchlist-quotes")
async def get_watchlist_quotes(
    watchlist_id: UUID = Query(None, description="Filter by watchlist ID"),
    conn=Depends(get_conn),
):
    """Get quotes for watchlist assets using batch yf.download (fast for large lists)."""
    try:
        import yfinance as yf
        import numpy as np
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    rows = await _get_watchlist_symbols(conn, watchlist_id)
    if not rows:
        return []

    # Build yahoo symbol mapping
    sym_map = {}  # yahoo_sym -> row
    for row in rows:
        yahoo_sym = get_yahoo_symbol(row["symbol"], row["exchange"])
        sym_map[yahoo_sym] = row

    yahoo_symbols = list(sym_map.keys())

    # Batch download — single HTTP batch for ALL symbols (5-10s for 173 vs 5+ min)
    try:
        data = yf.download(
            yahoo_symbols,
            period="5d",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False,
        )
    except Exception:
        data = None

    results = []
    for yahoo_sym, row in sym_map.items():
        symbol = row["symbol"]
        try:
            if data is None or data.empty:
                raise ValueError("no data")

            if len(yahoo_symbols) == 1:
                # Single ticker — columns are flat (Open, High, Low, Close, Volume)
                closes = data["Close"].dropna().tolist()
                volumes = data["Volume"].dropna().tolist()
            else:
                # Multi ticker — columns are (ticker, field)
                ticker_data = data[yahoo_sym]
                closes = ticker_data["Close"].dropna().tolist()
                volumes = ticker_data["Volume"].dropna().tolist()

            curr = closes[-1] if closes else None
            prev = closes[-2] if len(closes) >= 2 else None
            change = round(curr - prev, 4) if curr and prev else None
            change_pct = round((curr - prev) / prev * 100, 2) if curr and prev else None
            sparkline = [round(float(c), 2) for c in closes[-5:]]
            volume = int(volumes[-1]) if volumes else None

            quote = {
                "symbol": symbol,
                "name": row["name"],
                "current_price": round(float(curr), 4) if curr else None,
                "change": change,
                "change_percent": change_pct,
                "sparkline": sparkline,
                "currency": row["currency"] or "",
                "volume": volume,
            }
        except Exception:
            quote = {
                "symbol": symbol,
                "name": row["name"],
                "current_price": None,
                "change": None,
                "change_percent": None,
                "sparkline": [],
                "currency": row["currency"] or "",
                "volume": None,
            }

        results.append(quote)

        # Update DB cache
        try:
            await conn.execute("""
                UPDATE assets
                SET metadata = COALESCE(metadata, '{}'::jsonb) || $1::jsonb,
                    updated_at = NOW()
                WHERE symbol = $2
            """, json.dumps({"cached_quote": quote, "cached_quote_at": datetime.utcnow().isoformat()}),
                symbol)
        except Exception:
            pass

    return results


@router.get("/outlook/{symbol}")
async def get_financial_outlook(symbol: str):
    """Get financial outlook: analyst recs, target price, earnings, margins."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    yahoo_symbol = get_yahoo_symbol(symbol)
    ticker = yf.Ticker(yahoo_symbol)
    info = ticker.info

    if not info:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    def safe_round(val, n=2):
        return round(val, n) if val is not None else None

    def safe_pct(val):
        return round(val * 100, 2) if val is not None else None

    outlook = {
        "symbol": symbol.upper(),
        "name": info.get("longName") or info.get("shortName", symbol),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        # Analyst recommendations
        "recommendation": info.get("recommendationKey"),
        "recommendation_mean": safe_round(info.get("recommendationMean")),
        "number_of_analysts": info.get("numberOfAnalystOpinions"),
        "target_high": safe_round(info.get("targetHighPrice")),
        "target_low": safe_round(info.get("targetLowPrice")),
        "target_mean": safe_round(info.get("targetMeanPrice")),
        "target_median": safe_round(info.get("targetMedianPrice")),
        # Valuation
        "pe_trailing": safe_round(info.get("trailingPE")),
        "pe_forward": safe_round(info.get("forwardPE")),
        "peg_ratio": safe_round(info.get("pegRatio")),
        "price_to_book": safe_round(info.get("priceToBook")),
        "price_to_sales": safe_round(info.get("priceToSalesTrailing12Months")),
        "ev_to_ebitda": safe_round(info.get("enterpriseToEbitda")),
        # Profitability
        "profit_margin": safe_pct(info.get("profitMargins")),
        "operating_margin": safe_pct(info.get("operatingMargins")),
        "gross_margin": safe_pct(info.get("grossMargins")),
        "return_on_equity": safe_pct(info.get("returnOnEquity")),
        "return_on_assets": safe_pct(info.get("returnOnAssets")),
        # Growth
        "revenue_growth": safe_pct(info.get("revenueGrowth")),
        "earnings_growth": safe_pct(info.get("earningsGrowth")),
        "earnings_quarterly_growth": safe_pct(info.get("earningsQuarterlyGrowth")),
        # Financials
        "total_revenue": info.get("totalRevenue"),
        "ebitda": info.get("ebitda"),
        "total_debt": info.get("totalDebt"),
        "total_cash": info.get("totalCash"),
        "debt_to_equity": safe_round(info.get("debtToEquity")),
        "current_ratio": safe_round(info.get("currentRatio")),
        # Dividends
        "dividend_rate": safe_round(info.get("dividendRate")),
        "dividend_yield": safe_round(info.get("dividendYield")),  # Yahoo returns % already (e.g. 5.41 = 5.41%)
        "payout_ratio": safe_pct(info.get("payoutRatio")),
        "currency": info.get("currency"),
    }

    return outlook


@router.get("/financials/{symbol}")
async def get_financial_statements(symbol: str, period: str = Query("annual", regex="^(annual|quarterly)$")):
    """Get financial statements: Income Statement, Balance Sheet, Cash Flow."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    yahoo_symbol = get_yahoo_symbol(symbol)
    ticker = yf.Ticker(yahoo_symbol)

    def df_to_dict(df):
        """Convert yfinance DataFrame to serializable dict."""
        if df is None or df.empty:
            return {"periods": [], "items": []}
        # Sort columns (dates) descending — most recent first
        df = df[sorted(df.columns, reverse=True)]
        # Columns = dates, Rows = line items
        periods = [col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col) for col in df.columns]
        items = []
        for label, row in df.iterrows():
            values = []
            for v in row:
                if v is None or (hasattr(v, "__float__") and str(v) == "nan"):
                    values.append(None)
                else:
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        values.append(None)
            items.append({"label": str(label), "values": values})
        return {"periods": periods, "items": items}

    try:
        if period == "annual":
            income = df_to_dict(ticker.financials)
            balance = df_to_dict(ticker.balance_sheet)
            cashflow = df_to_dict(ticker.cashflow)
        else:
            income = df_to_dict(ticker.quarterly_financials)
            balance = df_to_dict(ticker.quarterly_balance_sheet)
            cashflow = df_to_dict(ticker.quarterly_cashflow)
    except Exception:
        income = {"periods": [], "items": []}
        balance = {"periods": [], "items": []}
        cashflow = {"periods": [], "items": []}

    return {
        "symbol": symbol.upper(),
        "period": period,
        "income_statement": income,
        "balance_sheet": balance,
        "cash_flow": cashflow,
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
