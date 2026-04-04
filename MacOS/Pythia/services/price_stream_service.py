"""
Pythia — Live Price WebSocket Broadcaster
Manages WS clients + 30s batch price fetch loop via yfinance.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID

from fastapi import WebSocket

import db
from helpers.financial_utils import get_yahoo_symbol

logger = logging.getLogger("pythia.price_stream")

REFRESH_INTERVAL = 30  # seconds


class PriceStreamService:
    """Manages WebSocket clients and broadcasts live price updates."""

    def __init__(self):
        self._clients: dict[WebSocket, str | None] = {}  # ws → watchlist_id
        self._task: asyncio.Task | None = None

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def connect(self, ws: WebSocket, watchlist_id: str | None = None):
        await ws.accept()
        self._clients[ws] = watchlist_id
        logger.info("Price WS connected (watchlist=%s, total=%d)", watchlist_id, len(self._clients))

        # Start broadcast loop if first client
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._broadcast_loop())

    def disconnect(self, ws: WebSocket):
        self._clients.pop(ws, None)
        logger.info("Price WS disconnected (%d remaining)", len(self._clients))

        # Stop loop if no clients
        if not self._clients and self._task and not self._task.done():
            self._task.cancel()
            self._task = None

    def update_subscription(self, ws: WebSocket, watchlist_id: str | None):
        if ws in self._clients:
            self._clients[ws] = watchlist_id

    async def _broadcast_loop(self):
        """Fetch prices every REFRESH_INTERVAL and broadcast to clients."""
        logger.info("Price broadcast loop started (interval=%ds)", REFRESH_INTERVAL)
        while self._clients:
            try:
                await self._fetch_and_broadcast()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Price broadcast error: %s", e)
            await asyncio.sleep(REFRESH_INTERVAL)
        logger.info("Price broadcast loop stopped (no clients)")

    async def _fetch_and_broadcast(self):
        """Fetch quotes for all subscribed watchlists and send to clients."""
        try:
            import yfinance as yf
        except ImportError:
            return

        # Collect unique watchlist_ids from all clients
        watchlist_ids = set(self._clients.values())

        pool = db.get_pool()
        async with pool.acquire() as conn:
            # Get all symbols across subscriptions
            all_rows = await self._get_symbols(conn, watchlist_ids)
            if not all_rows:
                return

            # Build yahoo symbol mapping
            sym_map: dict[str, dict] = {}
            for row in all_rows:
                yahoo_sym = get_yahoo_symbol(row["symbol"], row["exchange"])
                sym_map[yahoo_sym] = dict(row)

            # Batch download
            yahoo_symbols = list(sym_map.keys())
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
                return

            if data is None or data.empty:
                return

            # Build quotes
            quotes = []
            for yahoo_sym, row in sym_map.items():
                try:
                    if len(yahoo_symbols) == 1:
                        closes = data["Close"].dropna().tolist()
                        volumes = data["Volume"].dropna().tolist()
                    else:
                        ticker_data = data[yahoo_sym]
                        closes = ticker_data["Close"].dropna().tolist()
                        volumes = ticker_data["Volume"].dropna().tolist()

                    curr = closes[-1] if closes else None
                    prev = closes[-2] if len(closes) >= 2 else None
                    if curr is None:
                        continue

                    quotes.append({
                        "symbol": row["symbol"],
                        "name": row["name"],
                        "current_price": round(float(curr), 4),
                        "change": round(float(curr - prev), 4) if prev else None,
                        "change_percent": round(float((curr - prev) / prev * 100), 2) if prev else None,
                        "sparkline": [round(float(c), 2) for c in closes[-5:]],
                        "currency": row.get("currency") or "",
                        "volume": int(volumes[-1]) if volumes else None,
                    })
                except Exception:
                    continue

            if not quotes:
                return

            # Update DB cache
            for q in quotes:
                try:
                    await conn.execute("""
                        UPDATE assets
                        SET metadata = COALESCE(metadata, '{}'::jsonb) || $1::jsonb,
                            updated_at = NOW()
                        WHERE symbol = $2
                    """, json.dumps({
                        "cached_quote": q,
                        "cached_quote_at": datetime.utcnow().isoformat(),
                    }), q["symbol"])
                except Exception:
                    pass

        # Broadcast to clients
        message = json.dumps({
            "type": "price_update",
            "timestamp": datetime.now().isoformat(),
            "quotes": quotes,
        }, ensure_ascii=False, default=str)

        dead: list[WebSocket] = []
        for ws in self._clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.pop(ws, None)

        logger.info("Broadcasted %d quotes to %d clients", len(quotes), len(self._clients))

    async def _get_symbols(self, conn, watchlist_ids: set[str | None]) -> list:
        """Get symbols from DB for given watchlist IDs."""
        if None in watchlist_ids or not watchlist_ids:
            # "all" subscription
            return await conn.fetch("""
                SELECT DISTINCT a.symbol, a.name, a.exchange, a.currency
                FROM watchlist_items wi
                JOIN watchlists w ON wi.watchlist_id = w.watchlist_id
                JOIN assets a ON wi.asset_id = a.asset_id
                WHERE w.is_active = true
                ORDER BY a.symbol
            """)
        else:
            # Specific watchlists
            ids = [UUID(wid) for wid in watchlist_ids if wid]
            return await conn.fetch("""
                SELECT DISTINCT a.symbol, a.name, a.exchange, a.currency
                FROM watchlist_items wi
                JOIN watchlists w ON wi.watchlist_id = w.watchlist_id
                JOIN assets a ON wi.asset_id = a.asset_id
                WHERE w.is_active = true AND w.watchlist_id = ANY($1::uuid[])
                ORDER BY a.symbol
            """, ids)


# Singleton
price_stream = PriceStreamService()
