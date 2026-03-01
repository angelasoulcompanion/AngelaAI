"""
Pythia — Portfolio CRUD + Holdings + Transactions
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn
from schemas import (
    HoldingCreate,
    HoldingUpdate,
    PortfolioCreate,
    PortfolioUpdate,
    TransactionCreate,
)
from helpers import DynamicUpdate

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


# ============================================================
# PORTFOLIO CRUD
# ============================================================

@router.get("/")
async def list_portfolios(conn=Depends(get_conn)):
    """List all active portfolios with holding count and total value."""
    rows = await conn.fetch("""
        SELECT p.portfolio_id::text, p.name, p.description, p.base_currency,
               p.benchmark_symbol, p.risk_free_rate, p.initial_capital,
               p.inception_date, p.is_active, p.created_at, p.updated_at,
               COUNT(h.holding_id) AS holding_count,
               COALESCE(SUM(h.market_value), 0) AS total_value
        FROM portfolios p
        LEFT JOIN portfolio_holdings h ON p.portfolio_id = h.portfolio_id
        WHERE p.is_active = true
        GROUP BY p.portfolio_id
        ORDER BY p.created_at DESC
    """)
    return [dict(r) for r in rows]


@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: UUID, conn=Depends(get_conn)):
    """Get portfolio with holdings."""
    row = await conn.fetchrow("""
        SELECT portfolio_id::text, name, description, base_currency,
               benchmark_symbol, risk_free_rate, initial_capital,
               inception_date, is_active, created_at, updated_at
        FROM portfolios WHERE portfolio_id = $1
    """, portfolio_id)
    if not row:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    holdings = await conn.fetch("""
        SELECT h.holding_id::text, h.asset_id::text, a.symbol, a.name AS asset_name,
               a.asset_type::text, h.weight, h.quantity, h.average_cost,
               h.market_value, h.target_weight, h.min_weight, h.max_weight,
               h.created_at, h.updated_at
        FROM portfolio_holdings h
        JOIN assets a ON h.asset_id = a.asset_id
        WHERE h.portfolio_id = $1
        ORDER BY h.weight DESC
    """, portfolio_id)

    result = dict(row)
    result["holdings"] = [dict(h) for h in holdings]
    result["total_value"] = sum(float(h["market_value"] or 0) for h in holdings)
    return result


@router.post("/", status_code=201)
async def create_portfolio(body: PortfolioCreate, conn=Depends(get_conn)):
    """Create a new portfolio."""
    row = await conn.fetchrow("""
        INSERT INTO portfolios (name, description, base_currency, benchmark_symbol,
                                risk_free_rate, initial_capital, inception_date)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING portfolio_id::text, name, created_at
    """, body.name, body.description, body.base_currency, body.benchmark_symbol,
        body.risk_free_rate, body.initial_capital, body.inception_date)
    return dict(row)


@router.put("/{portfolio_id}")
async def update_portfolio(portfolio_id: UUID, body: PortfolioUpdate, conn=Depends(get_conn)):
    """Update portfolio fields."""
    builder = DynamicUpdate()
    builder.add("name", body.name)
    builder.add("description", body.description)
    builder.add("benchmark_symbol", body.benchmark_symbol)
    builder.add("risk_free_rate", body.risk_free_rate)
    builder.add("is_active", body.is_active)

    if not builder.has_updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    sql, values = builder.build("portfolios", "portfolio_id", portfolio_id)
    await conn.execute(sql, *values)
    return {"status": "updated", "portfolio_id": str(portfolio_id)}


@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: UUID, conn=Depends(get_conn)):
    """Soft delete portfolio."""
    await conn.execute("""
        UPDATE portfolios SET is_active = false, updated_at = NOW()
        WHERE portfolio_id = $1
    """, portfolio_id)
    return {"status": "deleted", "portfolio_id": str(portfolio_id)}


# ============================================================
# HOLDINGS
# ============================================================

@router.get("/{portfolio_id}/holdings")
async def list_holdings(portfolio_id: UUID, conn=Depends(get_conn)):
    """List holdings for a portfolio."""
    rows = await conn.fetch("""
        SELECT h.holding_id::text, h.asset_id::text, a.symbol, a.name AS asset_name,
               a.asset_type::text, a.sector, h.weight, h.quantity, h.average_cost,
               h.market_value, h.target_weight, h.min_weight, h.max_weight,
               h.created_at, h.updated_at
        FROM portfolio_holdings h
        JOIN assets a ON h.asset_id = a.asset_id
        WHERE h.portfolio_id = $1
        ORDER BY h.weight DESC
    """, portfolio_id)
    return [dict(r) for r in rows]


@router.post("/{portfolio_id}/holdings", status_code=201)
async def add_holding(portfolio_id: UUID, body: HoldingCreate, conn=Depends(get_conn)):
    """Add or update a holding (upsert on portfolio+asset)."""
    row = await conn.fetchrow("""
        INSERT INTO portfolio_holdings (portfolio_id, asset_id, weight, quantity, average_cost)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (portfolio_id, asset_id)
        DO UPDATE SET weight = EXCLUDED.weight,
                      quantity = COALESCE(EXCLUDED.quantity, portfolio_holdings.quantity),
                      average_cost = COALESCE(EXCLUDED.average_cost, portfolio_holdings.average_cost),
                      updated_at = NOW()
        RETURNING holding_id::text, asset_id::text, weight
    """, portfolio_id, body.asset_id, body.weight, body.quantity, body.average_cost)
    return dict(row)


@router.put("/{portfolio_id}/holdings/{asset_id}")
async def update_holding(portfolio_id: UUID, asset_id: UUID, body: HoldingUpdate, conn=Depends(get_conn)):
    """Update a single holding."""
    builder = DynamicUpdate()
    builder.add("weight", body.weight)
    builder.add("quantity", body.quantity)
    builder.add("average_cost", body.average_cost)
    builder.add("target_weight", body.target_weight)

    if not builder.has_updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Build WHERE with two conditions
    idx = builder._idx
    sets_sql = ", ".join(builder._sets)
    sql = f"UPDATE portfolio_holdings SET {sets_sql}, updated_at = NOW() WHERE portfolio_id = ${idx+1} AND asset_id = ${idx+2}"
    values = builder._values + [portfolio_id, asset_id]
    await conn.execute(sql, *values)
    return {"status": "updated"}


@router.delete("/{portfolio_id}/holdings/{asset_id}")
async def remove_holding(portfolio_id: UUID, asset_id: UUID, conn=Depends(get_conn)):
    """Remove a holding from portfolio."""
    await conn.execute("""
        DELETE FROM portfolio_holdings WHERE portfolio_id = $1 AND asset_id = $2
    """, portfolio_id, asset_id)
    return {"status": "removed"}


# ============================================================
# TRANSACTIONS
# ============================================================

@router.get("/{portfolio_id}/transactions")
async def list_transactions(
    portfolio_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    conn=Depends(get_conn)
):
    """List transactions for a portfolio."""
    rows = await conn.fetch("""
        SELECT t.transaction_id::text, t.asset_id::text, a.symbol, a.name AS asset_name,
               t.transaction_type::text, t.quantity, t.price, t.fees, t.taxes,
               t.total_amount, t.transaction_date, t.settlement_date, t.notes,
               t.created_at
        FROM transactions t
        JOIN assets a ON t.asset_id = a.asset_id
        WHERE t.portfolio_id = $1
        ORDER BY t.transaction_date DESC
        LIMIT $2
    """, portfolio_id, limit)
    return [dict(r) for r in rows]


@router.post("/{portfolio_id}/transactions", status_code=201)
async def add_transaction(portfolio_id: UUID, body: TransactionCreate, conn=Depends(get_conn)):
    """Record a new transaction."""
    row = await conn.fetchrow("""
        INSERT INTO transactions (portfolio_id, asset_id, transaction_type, quantity,
                                  price, fees, taxes, total_amount, transaction_date,
                                  settlement_date, notes)
        VALUES ($1, $2, $3::transaction_type, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING transaction_id::text, transaction_type::text, total_amount, created_at
    """, portfolio_id, body.asset_id, body.transaction_type, body.quantity,
        body.price, body.fees, body.taxes, body.total_amount,
        body.transaction_date, body.settlement_date, body.notes)
    return dict(row)
