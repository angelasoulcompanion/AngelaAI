"""
Pythia Router — Market Narrative Engine
Daily brief + weekly deep dive.
"""
from fastapi import APIRouter, Depends
import asyncpg

from db import get_conn
from services.narrative_service import daily_brief, weekly_deep_dive

router = APIRouter(prefix="/api/narrative", tags=["Market Narrative"])


@router.get("/daily")
async def daily_endpoint(conn: asyncpg.Connection = Depends(get_conn)):
    result = await daily_brief(conn)
    return {
        "headline": result.headline,
        "summary": result.summary,
        "key_themes": result.key_themes,
        "risk_factors": result.risk_factors,
        "opportunities": result.opportunities,
        "market_regime": result.market_regime,
        "generated_at": result.generated_at,
        "type": result.narrative_type,
        "success": result.success,
        "message": result.message,
    }


@router.get("/weekly")
async def weekly_endpoint(conn: asyncpg.Connection = Depends(get_conn)):
    result = await weekly_deep_dive(conn)
    return {
        "headline": result.headline,
        "summary": result.summary,
        "key_themes": result.key_themes,
        "risk_factors": result.risk_factors,
        "opportunities": result.opportunities,
        "generated_at": result.generated_at,
        "type": result.narrative_type,
        "success": result.success,
        "message": result.message,
    }
