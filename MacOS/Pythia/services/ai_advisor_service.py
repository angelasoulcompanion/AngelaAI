"""
Pythia — AI Portfolio Advisor Service
Uses Claude API for intelligent portfolio analysis and recommendations.
"""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID, uuid4

import asyncpg

from config import PythiaConfig


async def get_portfolio_context(conn: asyncpg.Connection, portfolio_id: UUID) -> dict:
    """Build context dict for AI analysis."""
    portfolio = await conn.fetchrow(
        "SELECT name, base_currency, risk_free_rate FROM portfolios WHERE portfolio_id = $1",
        portfolio_id,
    )
    if not portfolio:
        return {"error": "Portfolio not found"}

    holdings = await conn.fetch("""
        SELECT a.symbol, a.name, a.sector, h.weight, h.market_value
        FROM portfolio_holdings h
        JOIN assets a ON h.asset_id = a.asset_id
        WHERE h.portfolio_id = $1
        ORDER BY h.weight DESC
    """, portfolio_id)

    return {
        "portfolio_name": portfolio["name"],
        "currency": portfolio["base_currency"],
        "risk_free_rate": float(portfolio["risk_free_rate"]),
        "holdings": [
            {
                "symbol": h["symbol"],
                "name": h["name"],
                "sector": h["sector"],
                "weight": round(float(h["weight"]), 4),
                "market_value": round(float(h["market_value"] or 0), 2),
            }
            for h in holdings
        ],
    }


async def generate_ai_advice(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    question: Optional[str] = None,
) -> dict:
    """Generate AI-powered portfolio advice."""
    context = await get_portfolio_context(conn, portfolio_id)
    if "error" in context:
        return context

    holdings = context["holdings"]
    if not holdings:
        return {"advice": "No holdings found. Add assets to your portfolio first.", "success": True}

    # Build analysis without external LLM (rule-based for now, can upgrade to Claude API)
    analysis = []
    total_value = sum(h["market_value"] for h in holdings)

    # Concentration risk
    max_weight = max(h["weight"] for h in holdings)
    if max_weight > 0.3:
        top = next(h for h in holdings if h["weight"] == max_weight)
        analysis.append(f"Concentration Risk: {top['symbol']} has {max_weight*100:.1f}% weight. Consider diversifying below 30%.")

    # Sector analysis
    sectors: dict[str, float] = {}
    for h in holdings:
        s = h["sector"] or "Unknown"
        sectors[s] = sectors.get(s, 0) + h["weight"]
    for sector, weight in sorted(sectors.items(), key=lambda x: -x[1]):
        if weight > 0.4:
            analysis.append(f"Sector Overweight: {sector} at {weight*100:.1f}%. Sector concentration above 40%.")

    # Diversification score
    n_assets = len(holdings)
    n_sectors = len(sectors)
    div_score = min(1.0, (n_assets / 10) * 0.5 + (n_sectors / 5) * 0.5)
    analysis.append(f"Diversification Score: {div_score*100:.0f}% ({n_assets} assets across {n_sectors} sectors)")

    # Save conversation
    conv_id = uuid4()
    await conn.execute("""
        INSERT INTO ai_conversations (conversation_id, portfolio_id, message_type, content)
        VALUES ($1, $2, 'assistant', $3)
    """, conv_id, portfolio_id, "\n".join(analysis))

    return {
        "portfolio": context["portfolio_name"],
        "analysis": analysis,
        "holdings_count": n_assets,
        "sectors_count": n_sectors,
        "diversification_score": round(div_score, 2),
        "question": question,
        "conversation_id": str(conv_id),
        "success": True,
    }


async def get_conversation_history(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    limit: int = 20,
) -> list[dict]:
    """Get AI conversation history."""
    rows = await conn.fetch("""
        SELECT conversation_id, message_type, content, created_at
        FROM ai_conversations
        WHERE portfolio_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    """, portfolio_id, limit)
    return [
        {
            "conversation_id": str(r["conversation_id"]),
            "type": r["message_type"],
            "content": r["content"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]
