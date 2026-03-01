"""
Pythia — Watchlist CRUD
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from db import get_conn
from schemas import WatchlistCreate, WatchlistItemAdd

router = APIRouter(prefix="/api/watchlists", tags=["watchlist"])


@router.get("/")
async def list_watchlists(conn=Depends(get_conn)):
    """List all active watchlists."""
    rows = await conn.fetch("""
        SELECT w.watchlist_id::text, w.name, w.description,
               COUNT(wi.item_id) AS item_count,
               w.created_at, w.updated_at
        FROM watchlists w
        LEFT JOIN watchlist_items wi ON w.watchlist_id = wi.watchlist_id
        WHERE w.is_active = true
        GROUP BY w.watchlist_id
        ORDER BY w.created_at DESC
    """)
    return [dict(r) for r in rows]


@router.get("/{watchlist_id}")
async def get_watchlist(watchlist_id: UUID, conn=Depends(get_conn)):
    """Get watchlist with items."""
    wl = await conn.fetchrow("""
        SELECT watchlist_id::text, name, description, created_at
        FROM watchlists WHERE watchlist_id = $1 AND is_active = true
    """, watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    items = await conn.fetch("""
        SELECT wi.item_id::text, wi.asset_id::text, a.symbol, a.name AS asset_name,
               a.asset_type::text, a.sector, wi.notes, wi.added_at
        FROM watchlist_items wi
        JOIN assets a ON wi.asset_id = a.asset_id
        WHERE wi.watchlist_id = $1
        ORDER BY wi.added_at DESC
    """, watchlist_id)

    result = dict(wl)
    result["items"] = [dict(i) for i in items]
    return result


@router.post("/", status_code=201)
async def create_watchlist(body: WatchlistCreate, conn=Depends(get_conn)):
    """Create a new watchlist."""
    row = await conn.fetchrow("""
        INSERT INTO watchlists (name, description)
        VALUES ($1, $2)
        RETURNING watchlist_id::text, name, created_at
    """, body.name, body.description)
    return dict(row)


@router.post("/{watchlist_id}/items", status_code=201)
async def add_watchlist_item(watchlist_id: UUID, body: WatchlistItemAdd, conn=Depends(get_conn)):
    """Add an asset to a watchlist."""
    row = await conn.fetchrow("""
        INSERT INTO watchlist_items (watchlist_id, asset_id, notes)
        VALUES ($1, $2, $3)
        ON CONFLICT (watchlist_id, asset_id) DO NOTHING
        RETURNING item_id::text, asset_id::text
    """, watchlist_id, body.asset_id, body.notes)
    if not row:
        return {"status": "already_exists"}
    return dict(row)


@router.delete("/{watchlist_id}/items/{asset_id}")
async def remove_watchlist_item(watchlist_id: UUID, asset_id: UUID, conn=Depends(get_conn)):
    """Remove an asset from a watchlist."""
    await conn.execute("""
        DELETE FROM watchlist_items WHERE watchlist_id = $1 AND asset_id = $2
    """, watchlist_id, asset_id)
    return {"status": "removed"}


@router.delete("/{watchlist_id}")
async def delete_watchlist(watchlist_id: UUID, conn=Depends(get_conn)):
    """Soft delete a watchlist."""
    await conn.execute("""
        UPDATE watchlists SET is_active = false, updated_at = NOW()
        WHERE watchlist_id = $1
    """, watchlist_id)
    return {"status": "deleted"}
