"""
Pythia — AI Portfolio Advisor Service
Hybrid: Rule-based analysis + LLM insights + multi-turn chat.
"""
import json
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
    session_id: Optional[str] = None,
) -> dict:
    """Generate AI-powered portfolio advice with optional LLM analysis."""
    context = await get_portfolio_context(conn, portfolio_id)
    if "error" in context:
        return context

    holdings = context["holdings"]
    if not holdings:
        return {"advice": "No holdings found. Add assets to your portfolio first.", "success": True}

    # Step 1: Always run rule-based analysis
    analysis = _generate_rule_based(holdings)

    # Step 2: LLM analysis (if available)
    llm_analysis: Optional[str] = None
    llm_provider: Optional[str] = None

    try:
        from services.llm_service import llm_service

        # Determine complexity: simple portfolio overview → Ollama, complex question → Claude
        complexity = "complex" if question else "simple"

        holdings_text = "\n".join(
            f"- {h['symbol']} ({h['name']}): {h['weight']*100:.1f}% weight, sector={h['sector']}"
            for h in holdings[:15]
        )

        # Build conversation context if session exists
        conv_context = ""
        if session_id:
            history = await _get_session_history(conn, portfolio_id, session_id, limit=5)
            if history:
                conv_context = "\n\nPrevious conversation:\n" + "\n".join(
                    f"{msg['type'].upper()}: {msg['content']}" for msg in history
                )

        prompt = f"""Portfolio: {context['portfolio_name']} ({context['currency']})
Holdings:
{holdings_text}

Rule-based analysis:
{chr(10).join('- ' + a for a in analysis)}
{conv_context}
{f"User question: {question}" if question else "Provide a brief overall assessment and top recommendation."}

Give a concise, actionable analysis (3-5 sentences). Reference specific holdings and percentages."""

        llm_resp = await llm_service.complete(
            prompt=prompt,
            system="You are a CFA-certified portfolio advisor. Give specific, actionable advice based on the data. No generic disclaimers.",
            complexity=complexity,
            max_tokens=512,
        )
        if llm_resp.success and llm_resp.text:
            llm_analysis = llm_resp.text
            llm_provider = llm_resp.provider
    except Exception:
        pass

    # Generate or use existing session_id
    sid = session_id or str(uuid4())

    # Save conversation turns
    if question:
        await _save_conversation(conn, portfolio_id, "user", question, sid)
    response_content = llm_analysis or "\n".join(analysis)
    await _save_conversation(conn, portfolio_id, "assistant", response_content, sid, llm_provider)

    # Diversification metrics
    total_value = sum(h["market_value"] for h in holdings)
    sectors: dict[str, float] = {}
    for h in holdings:
        s = h["sector"] or "Unknown"
        sectors[s] = sectors.get(s, 0) + h["weight"]
    n_assets = len(holdings)
    n_sectors = len(sectors)
    div_score = min(1.0, (n_assets / 10) * 0.5 + (n_sectors / 5) * 0.5)

    return {
        "portfolio": context["portfolio_name"],
        "analysis": analysis,
        "holdings_count": n_assets,
        "sectors_count": n_sectors,
        "diversification_score": round(div_score, 2),
        "question": question,
        "session_id": sid,
        "conversation_id": sid,
        # Enhanced fields
        "llm_analysis": llm_analysis,
        "llm_provider": llm_provider,
        "success": True,
    }


def _generate_rule_based(holdings: list[dict]) -> list[str]:
    """Original rule-based portfolio analysis."""
    analysis = []

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

    return analysis


async def chat_with_advisor(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    message: str,
    session_id: Optional[str] = None,
) -> dict:
    """Multi-turn chat endpoint for advisor."""
    return await generate_ai_advice(conn, portfolio_id, question=message, session_id=session_id)


async def _save_conversation(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    msg_type: str,
    content: str,
    session_id: str,
    llm_provider: Optional[str] = None,
) -> None:
    """Save a conversation turn to the database."""
    try:
        await conn.execute("""
            INSERT INTO ai_conversations (conversation_id, portfolio_id, message_type, content, session_id, llm_provider)
            VALUES ($1, $2, $3, $4, $5::uuid, $6)
        """, uuid4(), portfolio_id, msg_type, content, session_id, llm_provider)
    except Exception:
        # Fallback without session_id cast if column doesn't support UUID yet
        try:
            await conn.execute("""
                INSERT INTO ai_conversations (conversation_id, portfolio_id, message_type, content)
                VALUES ($1, $2, $3, $4)
            """, uuid4(), portfolio_id, msg_type, content)
        except Exception:
            pass


async def _get_session_history(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    session_id: str,
    limit: int = 10,
) -> list[dict]:
    """Get conversation history for a specific session."""
    try:
        rows = await conn.fetch("""
            SELECT message_type, content, created_at
            FROM ai_conversations
            WHERE portfolio_id = $1 AND session_id = $2::uuid
            ORDER BY created_at ASC
            LIMIT $3
        """, portfolio_id, session_id, limit)
        return [{"type": r["message_type"], "content": r["content"]} for r in rows]
    except Exception:
        return []


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
