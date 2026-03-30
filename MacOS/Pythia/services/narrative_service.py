"""
Pythia — Market Narrative Engine
Daily brief + weekly deep dive via Claude API.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import asyncpg

from config import PythiaConfig


@dataclass
class NarrativeResult:
    headline: str = ""
    summary: str = ""
    key_themes: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    market_regime: str = ""
    generated_at: str = ""
    narrative_type: str = "daily"  # daily, weekly
    success: bool = True
    message: str = ""


async def daily_brief(conn: asyncpg.Connection) -> NarrativeResult:
    """Generate daily market narrative brief via Claude."""
    # Gather market context
    context = await _gather_market_context(conn)

    from services.llm_service import llm_service

    prompt = f"""Write a concise daily market brief based on this data:

{context}

Respond in JSON:
{{
  "headline": "One-line market headline",
  "summary": "2-3 sentence market overview",
  "key_themes": ["theme1", "theme2", "theme3"],
  "risk_factors": ["risk1", "risk2"],
  "opportunities": ["opportunity1", "opportunity2"]
}}"""

    parsed, resp = await llm_service.complete_json(
        prompt=prompt,
        system="You are a senior market strategist writing the morning brief for a trading desk. Be precise, data-driven, and actionable.",
        max_tokens=1024,
        conn=conn, cache_ttl=PythiaConfig.CACHE_TTL_NARRATIVE, feature="daily_narrative",
    )

    if not parsed:
        return NarrativeResult(
            success=False,
            message=resp.error if resp else "Failed to generate narrative",
        )

    return NarrativeResult(
        headline=parsed.get("headline", ""),
        summary=parsed.get("summary", ""),
        key_themes=parsed.get("key_themes", []),
        risk_factors=parsed.get("risk_factors", []),
        opportunities=parsed.get("opportunities", []),
        market_regime=context.split("Regime:")[1].split("\n")[0].strip() if "Regime:" in context else "",
        generated_at=str(date.today()),
        narrative_type="daily",
    )


async def weekly_deep_dive(conn: asyncpg.Connection) -> NarrativeResult:
    """Generate weekly deep-dive market analysis."""
    context = await _gather_market_context(conn, extended=True)

    from services.llm_service import llm_service

    prompt = f"""Write a comprehensive weekly market analysis based on this data:

{context}

Respond in JSON:
{{
  "headline": "Weekly market headline",
  "summary": "4-5 sentence comprehensive analysis covering macro trends, sector rotation, and risk outlook",
  "key_themes": ["theme1", "theme2", "theme3", "theme4"],
  "risk_factors": ["risk1", "risk2", "risk3"],
  "opportunities": ["opp1", "opp2", "opp3"]
}}"""

    parsed, resp = await llm_service.complete_json(
        prompt=prompt,
        system="You are a chief market strategist at a quantitative hedge fund. Write institutional-quality weekly analysis.",
        max_tokens=2048,
        conn=conn, cache_ttl=PythiaConfig.CACHE_TTL_NARRATIVE, feature="weekly_narrative",
    )

    if not parsed:
        return NarrativeResult(
            success=False,
            message=resp.error if resp else "Failed to generate narrative",
        )

    return NarrativeResult(
        headline=parsed.get("headline", ""),
        summary=parsed.get("summary", ""),
        key_themes=parsed.get("key_themes", []),
        risk_factors=parsed.get("risk_factors", []),
        opportunities=parsed.get("opportunities", []),
        generated_at=str(date.today()),
        narrative_type="weekly",
    )


async def _gather_market_context(conn: asyncpg.Connection, extended: bool = False) -> str:
    """Gather market data context for narrative generation."""
    lines = [f"Date: {date.today()}"]

    # Regime detection for key indices
    try:
        from services.regime_service import detect_regime
        for symbol, name in [("^SET.BK", "SET"), ("^GSPC", "S&P 500"), ("^N225", "Nikkei")]:
            r = await detect_regime(conn, symbol, days=200)
            if r.success:
                lines.append(f"{name}: Regime={r.regime}, Vol={r.volatility:.3f}, Trend={r.trend_strength:+.3f}")
    except Exception:
        pass

    # Recent signals summary
    try:
        recent_signals = await conn.fetch(
            """SELECT a.symbol, ts.direction, ts.strength, ts.signal_name
               FROM trading_signals ts
               JOIN assets a ON a.asset_id = ts.asset_id
               WHERE ts.created_at >= NOW() - INTERVAL '1 day'
               ORDER BY ts.strength DESC LIMIT 10"""
        )
        if recent_signals:
            lines.append("\nRecent Strong Signals:")
            for s in recent_signals:
                lines.append(f"  {s['symbol']}: {s['signal_name']} → {s['direction']} (strength={s['strength']:.2f})")
    except Exception:
        pass

    # Portfolio summary
    try:
        port_count = await conn.fetchval("SELECT COUNT(*) FROM portfolios")
        lines.append(f"\nPortfolios tracked: {port_count}")
    except Exception:
        pass

    if extended:
        lines.append("\n[Extended analysis requested — provide deeper macro view]")

    return "\n".join(lines)
