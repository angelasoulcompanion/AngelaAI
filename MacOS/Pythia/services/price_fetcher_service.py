"""
Pythia — Price fetcher service (ported from CQFOracle)
Fetches OHLCV data from Yahoo Finance and stores in historical_prices.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import asyncpg

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

from helpers.financial_utils import get_yahoo_symbol


@dataclass
class FetchResult:
    symbol: str
    records_fetched: int = 0
    records_inserted: int = 0
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    source: str = "yahoo_finance"
    success: bool = True
    error: Optional[str] = None


class PriceFetcherService:
    """Fetch and store historical prices from Yahoo Finance."""

    @staticmethod
    async def fetch_yahoo_prices(
        conn: asyncpg.Connection,
        asset_id: UUID,
        days: int = 365
    ) -> FetchResult:
        """Fetch prices for a single asset and upsert into historical_prices."""
        if not HAS_YFINANCE:
            return FetchResult(symbol="", success=False, error="yfinance not installed")

        # Get asset symbol
        row = await conn.fetchrow(
            "SELECT symbol, exchange FROM assets WHERE asset_id = $1", asset_id
        )
        if not row:
            return FetchResult(symbol="", success=False, error="Asset not found")

        symbol = row["symbol"]
        yahoo_symbol = get_yahoo_symbol(symbol, row["exchange"])

        try:
            ticker = yf.Ticker(yahoo_symbol)
            end = datetime.now()
            start = end - timedelta(days=days)
            hist = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

            if hist.empty:
                return FetchResult(symbol=symbol, success=True)

            inserted = 0
            for date_idx, bar in hist.iterrows():
                try:
                    await conn.execute("""
                        INSERT INTO historical_prices
                            (asset_id, date, open_price, high_price, low_price,
                             close_price, adj_close, volume, dividends, stock_splits)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (asset_id, date) DO UPDATE SET
                            close_price = EXCLUDED.close_price,
                            volume = EXCLUDED.volume,
                            fetched_at = NOW()
                    """,
                        asset_id, date_idx.date(),
                        float(bar.get("Open", 0)), float(bar.get("High", 0)),
                        float(bar.get("Low", 0)), float(bar.get("Close", 0)),
                        float(bar.get("Close", 0)), int(bar.get("Volume", 0)),
                        float(bar.get("Dividends", 0)), float(bar.get("Stock Splits", 1)),
                    )
                    inserted += 1
                except Exception:
                    continue

            return FetchResult(
                symbol=symbol,
                records_fetched=len(hist),
                records_inserted=inserted,
                date_start=hist.index[0].strftime("%Y-%m-%d"),
                date_end=hist.index[-1].strftime("%Y-%m-%d"),
            )

        except Exception as e:
            return FetchResult(symbol=symbol, success=False, error=str(e))

    @staticmethod
    async def fetch_multiple(
        conn: asyncpg.Connection,
        asset_ids: list[UUID],
        days: int = 365
    ) -> list[FetchResult]:
        """Fetch prices for multiple assets."""
        results = []
        for asset_id in asset_ids:
            result = await PriceFetcherService.fetch_yahoo_prices(conn, asset_id, days)
            results.append(result)
        return results

    @staticmethod
    async def ensure_fresh(
        conn: asyncpg.Connection,
        asset_id: UUID,
        min_rows: int = 20,
        max_age_hours: int = 24,
    ) -> bool:
        """Auto-fetch if data is missing or stale. Returns True if data is available."""
        row = await conn.fetchrow("""
            SELECT COUNT(*) AS cnt,
                   MAX(date) AS latest
            FROM historical_prices
            WHERE asset_id = $1
        """, asset_id)

        cnt = row["cnt"] if row else 0
        latest = row["latest"] if row else None

        needs_fetch = False
        if cnt < min_rows:
            needs_fetch = True
        elif latest:
            from datetime import date as date_cls
            age_days = (date_cls.today() - latest).days
            if age_days > (max_age_hours / 24):
                needs_fetch = True

        if needs_fetch:
            result = await PriceFetcherService.fetch_yahoo_prices(conn, asset_id, days=365)
            return result.records_fetched >= min_rows or (cnt + result.records_fetched) >= min_rows

        return cnt >= min_rows

    @staticmethod
    async def update_all_assets(
        conn: asyncpg.Connection,
        days: int = 30
    ) -> dict:
        """Incremental update for all active assets."""
        rows = await conn.fetch(
            "SELECT asset_id FROM assets WHERE is_active = true"
        )
        asset_ids = [row["asset_id"] for row in rows]
        results = await PriceFetcherService.fetch_multiple(conn, asset_ids, days)

        return {
            "total_assets": len(asset_ids),
            "successful": sum(1 for r in results if r.success),
            "total_records": sum(r.records_inserted for r in results),
        }
