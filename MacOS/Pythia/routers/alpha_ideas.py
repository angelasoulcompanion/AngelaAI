"""
Pythia — Alpha Ideas Router
Scan Thai or US stocks and rank by 7 academic alpha factors.
"""
from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.alpha_ideas_service import scan_alpha_ideas, seed_us_universe

router = APIRouter(prefix="/api/alpha-ideas", tags=["Alpha Ideas"])


@router.get("/scan")
async def scan_endpoint(
    top_n: int = Query(10, ge=5, le=30, description="Top N stocks per idea"),
    market: str = Query("TH", description="Market: TH or US"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Scan stocks and rank by 7 alpha factor ideas."""
    result = await scan_alpha_ideas(conn, top_n, market=market)
    return {
        "ideas": [
            {
                "idea_id": idea.idea_id,
                "name": idea.name,
                "description": idea.description,
                "long_rationale": idea.long_rationale,
                "short_rationale": idea.short_rationale,
                "long_candidates": idea.long_candidates,
                "short_candidates": idea.short_candidates,
            }
            for idea in result.ideas
        ],
        "composite_ranking": result.composite_ranking,
        "total_stocks_scanned": result.total_stocks_scanned,
        "scan_time_seconds": result.scan_time_seconds,
        "success": result.success,
        "message": result.message,
    }


@router.post("/seed-us-universe")
async def seed_us_endpoint(
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Seed US stock universe table with S&P 500 core tickers."""
    count = await seed_us_universe(conn)
    return {"inserted": count, "success": True, "message": f"Seeded {count} US tickers"}
