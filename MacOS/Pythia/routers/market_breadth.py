"""
Pythia — Market Breadth Router
Endpoints for breadth indicators computed from constituent prices.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn
from services.market_breadth_service import (
    UNIVERSES,
    compute_breadth,
    _cache_key,
    _get_cached,
    _set_cached,
)

router = APIRouter(prefix="/api/breadth", tags=["breadth"])


@router.get("/universes")
async def list_universes(conn=Depends(get_conn)):
    """List predefined universes + user watchlists."""
    result = []

    # Predefined
    for key, info in UNIVERSES.items():
        result.append({
            "id": key,
            "name": info["name"],
            "type": info["type"],
            "size": len(info["symbols"]),
        })

    # User watchlists
    rows = await conn.fetch(
        """SELECT w.watchlist_id::text, w.name, COUNT(wi.item_id) AS cnt
           FROM watchlists w
           JOIN watchlist_items wi ON wi.watchlist_id = w.watchlist_id
           WHERE w.is_active = true
           GROUP BY w.watchlist_id, w.name
           HAVING COUNT(wi.item_id) >= 5
           ORDER BY w.name"""
    )
    for r in rows:
        result.append({
            "id": r["watchlist_id"],
            "name": f"📋 {r['name']}",
            "type": "watchlist",
            "size": r["cnt"],
        })

    return result


@router.get("/{universe}")
async def get_breadth(
    universe: str,
    period: str = Query("1y", description="Period: 3mo, 6mo, 1y, 2y"),
    conn=Depends(get_conn),
):
    """Compute all breadth indicators for a universe."""
    # Check cache
    key = _cache_key(universe, period)
    cached = _get_cached(key)
    if cached:
        return cached

    # Resolve symbols
    if universe.upper() in UNIVERSES:
        symbols = UNIVERSES[universe.upper()]["symbols"]
        universe_name = UNIVERSES[universe.upper()]["name"]
    else:
        # Try as watchlist UUID
        rows = await conn.fetch(
            """SELECT a.symbol, a.exchange
               FROM watchlist_items wi
               JOIN assets a ON a.asset_id = wi.asset_id
               WHERE wi.watchlist_id = $1::uuid""",
            universe,
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Universe '{universe}' not found")

        symbols = []
        for r in rows:
            sym = r["symbol"]
            if r["exchange"] and r["exchange"].upper() in ("SET", "MAI"):
                sym = f"{sym}.BK" if not sym.endswith(".BK") else sym
            symbols.append(sym)

        wl = await conn.fetchrow(
            "SELECT name FROM watchlists WHERE watchlist_id = $1::uuid", universe
        )
        universe_name = wl["name"] if wl else universe

    if len(symbols) < 5:
        raise HTTPException(status_code=400, detail="Universe must have at least 5 symbols")

    # Compute
    result = compute_breadth(symbols, period)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Computation failed"))

    result["universe"] = universe_name
    result["period"] = period

    _set_cached(key, result)
    return result
