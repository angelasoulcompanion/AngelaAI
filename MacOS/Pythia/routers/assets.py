"""
Pythia — Asset management + Yahoo Finance integration
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn
from schemas import AssetCreate, AssetUpdate
from helpers import DynamicUpdate

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("/")
async def list_assets(
    asset_type: str | None = None,
    search: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    conn=Depends(get_conn)
):
    """List assets with optional filtering."""
    if search:
        rows = await conn.fetch("""
            SELECT asset_id::text, symbol, name, asset_type::text, exchange,
                   currency, sector, industry, country, is_active,
                   metadata, created_at, updated_at
            FROM assets
            WHERE is_active = true
              AND (symbol ILIKE $1 OR name ILIKE $1)
            ORDER BY symbol
            LIMIT $2
        """, f"%{search}%", limit)
    elif asset_type:
        rows = await conn.fetch("""
            SELECT asset_id::text, symbol, name, asset_type::text, exchange,
                   currency, sector, industry, country, is_active,
                   metadata, created_at, updated_at
            FROM assets
            WHERE is_active = true AND asset_type = $1::asset_type
            ORDER BY symbol
            LIMIT $2
        """, asset_type, limit)
    else:
        rows = await conn.fetch("""
            SELECT asset_id::text, symbol, name, asset_type::text, exchange,
                   currency, sector, industry, country, is_active,
                   metadata, created_at, updated_at
            FROM assets
            WHERE is_active = true
            ORDER BY symbol
            LIMIT $1
        """, limit)
    return [dict(r) for r in rows]


@router.get("/{asset_id}")
async def get_asset(asset_id: UUID, conn=Depends(get_conn)):
    """Get asset by ID."""
    row = await conn.fetchrow("""
        SELECT asset_id::text, symbol, name, asset_type::text, exchange,
               currency, sector, industry, country, is_active,
               metadata, created_at, updated_at
        FROM assets WHERE asset_id = $1
    """, asset_id)
    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")
    return dict(row)


@router.post("/", status_code=201)
async def create_asset(body: AssetCreate, conn=Depends(get_conn)):
    """Create a new asset."""
    # Check for duplicate
    existing = await conn.fetchrow("""
        SELECT asset_id FROM assets WHERE symbol = $1 AND exchange = $2
    """, body.symbol, body.exchange)
    if existing:
        raise HTTPException(status_code=409, detail=f"Asset {body.symbol} already exists on {body.exchange}")

    row = await conn.fetchrow("""
        INSERT INTO assets (symbol, name, asset_type, exchange, currency, sector, industry, country)
        VALUES ($1, $2, $3::asset_type, $4, $5, $6, $7, $8)
        RETURNING asset_id::text, symbol, name, created_at
    """, body.symbol, body.name, body.asset_type, body.exchange,
        body.currency, body.sector, body.industry, body.country)
    return dict(row)


@router.post("/from-yahoo", status_code=201)
async def create_asset_from_yahoo(symbol: str, conn=Depends(get_conn)):
    """Create asset by fetching info from Yahoo Finance."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(status_code=503, detail="yfinance not installed")

    # Check existing
    existing = await conn.fetchrow(
        "SELECT asset_id::text, symbol FROM assets WHERE symbol = $1", symbol.upper()
    )
    if existing:
        return {"status": "exists", **dict(existing)}

    ticker = yf.Ticker(symbol)
    info = ticker.info
    if not info or "symbol" not in info:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found on Yahoo Finance")

    # Detect asset type
    quote_type = info.get("quoteType", "").lower()
    exchange_name = info.get("exchange", "")
    asset_type_map = {
        "equity": "thai_stock" if ".BK" in symbol.upper() else "us_stock",
        "etf": "etf",
        "mutualfund": "mutual_fund",
        "cryptocurrency": "crypto",
        "index": "index",
    }
    detected_type = asset_type_map.get(quote_type, "other")

    row = await conn.fetchrow("""
        INSERT INTO assets (symbol, name, asset_type, exchange, currency, sector, industry, country, metadata)
        VALUES ($1, $2, $3::asset_type, $4, $5, $6, $7, $8, $9::jsonb)
        RETURNING asset_id::text, symbol, name, asset_type::text, created_at
    """,
        info.get("symbol", symbol).upper(),
        info.get("longName") or info.get("shortName", symbol),
        detected_type,
        exchange_name,
        info.get("currency", "THB"),
        info.get("sector"),
        info.get("industry"),
        info.get("country", "Thailand"),
        str({
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
        }).replace("'", '"').replace("None", "null"),
    )
    return dict(row)


@router.put("/{asset_id}")
async def update_asset(asset_id: UUID, body: AssetUpdate, conn=Depends(get_conn)):
    """Update asset fields."""
    builder = DynamicUpdate()
    builder.add("name", body.name)
    builder.add("sector", body.sector)
    builder.add("industry", body.industry)
    builder.add("is_active", body.is_active)

    if not builder.has_updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    sql, values = builder.build("assets", "asset_id", asset_id)
    await conn.execute(sql, *values)
    return {"status": "updated", "asset_id": str(asset_id)}


@router.get("/{asset_id}/prices")
async def get_asset_prices(
    asset_id: UUID,
    days: int = Query(365, ge=1, le=3650),
    conn=Depends(get_conn)
):
    """Get historical prices for an asset."""
    rows = await conn.fetch("""
        SELECT price_id::text, date, open_price, high_price, low_price,
               close_price, adj_close, volume, dividends, stock_splits
        FROM historical_prices
        WHERE asset_id = $1
        ORDER BY date DESC
        LIMIT $2
    """, asset_id, days)
    return [dict(r) for r in rows]
