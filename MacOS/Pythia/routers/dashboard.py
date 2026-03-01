"""
Pythia — Dashboard KPI aggregation
"""
from fastapi import APIRouter, Depends

from db import get_conn

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(conn=Depends(get_conn)):
    """Get dashboard summary KPIs."""
    # Portfolio count + total value
    portfolio_stats = await conn.fetchrow("""
        SELECT COUNT(DISTINCT p.portfolio_id) AS portfolio_count,
               COALESCE(SUM(h.market_value), 0) AS total_portfolio_value
        FROM portfolios p
        LEFT JOIN portfolio_holdings h ON p.portfolio_id = h.portfolio_id
        WHERE p.is_active = true
    """)

    # Asset count
    asset_count = await conn.fetchval("""
        SELECT COUNT(*) FROM assets WHERE is_active = true
    """)

    # Total holdings
    holding_count = await conn.fetchval("""
        SELECT COUNT(*) FROM portfolio_holdings h
        JOIN portfolios p ON h.portfolio_id = p.portfolio_id
        WHERE p.is_active = true
    """)

    # Transaction count (last 30 days)
    recent_txns = await conn.fetchval("""
        SELECT COUNT(*) FROM transactions
        WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
    """)

    # Price data points
    price_count = await conn.fetchval("""
        SELECT COUNT(*) FROM historical_prices
    """)

    # Watchlist count
    watchlist_count = await conn.fetchval("""
        SELECT COUNT(*) FROM watchlists WHERE is_active = true
    """)

    return {
        "portfolio_count": portfolio_stats["portfolio_count"],
        "total_portfolio_value": float(portfolio_stats["total_portfolio_value"]),
        "asset_count": asset_count,
        "holding_count": holding_count,
        "recent_transactions": recent_txns,
        "price_data_points": price_count,
        "watchlist_count": watchlist_count,
    }


@router.get("/portfolio-breakdown")
async def get_portfolio_breakdown(conn=Depends(get_conn)):
    """Get portfolio allocation breakdown by asset type."""
    rows = await conn.fetch("""
        SELECT a.asset_type::text, COUNT(*) AS count,
               COALESCE(SUM(h.market_value), 0) AS total_value,
               COALESCE(SUM(h.weight), 0) AS total_weight
        FROM portfolio_holdings h
        JOIN assets a ON h.asset_id = a.asset_id
        JOIN portfolios p ON h.portfolio_id = p.portfolio_id
        WHERE p.is_active = true
        GROUP BY a.asset_type
        ORDER BY total_value DESC
    """)
    return [dict(r) for r in rows]


@router.get("/recent-activity")
async def get_recent_activity(conn=Depends(get_conn)):
    """Get recent transactions and price updates."""
    txns = await conn.fetch("""
        SELECT t.transaction_id::text, a.symbol, t.transaction_type::text,
               t.quantity, t.price, t.total_amount, t.transaction_date
        FROM transactions t
        JOIN assets a ON t.asset_id = a.asset_id
        ORDER BY t.transaction_date DESC
        LIMIT 10
    """)

    prices = await conn.fetch("""
        SELECT a.symbol, hp.date, hp.close_price, hp.volume
        FROM historical_prices hp
        JOIN assets a ON hp.asset_id = a.asset_id
        ORDER BY hp.fetched_at DESC
        LIMIT 10
    """)

    return {
        "recent_transactions": [dict(t) for t in txns],
        "recent_prices": [dict(p) for p in prices],
    }
