"""
Pythia Router — Chart Pattern Recognition
Detects classical chart patterns with breakout/target levels.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
import asyncpg

from db import get_conn
from services.pattern_service import detect_patterns, scan_patterns

router = APIRouter(prefix="/api/patterns", tags=["Pattern Recognition"])


class PatternScanRequest(BaseModel):
    asset_ids: list[UUID]


@router.get("/{asset_id}")
async def patterns_endpoint(
    asset_id: UUID,
    days: int = Query(120, ge=30, le=500),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Detect chart patterns for a single asset."""
    result = await detect_patterns(conn, asset_id, days)
    return {
        "asset_id": result.asset_id,
        "symbol": result.symbol,
        "current_price": result.current_price,
        "patterns": [
            {
                "pattern_type": p.pattern_type,
                "direction": p.direction,
                "confidence": p.confidence,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "breakout_price": p.breakout_price,
                "target_price": p.target_price,
                "description": p.description,
                "key_levels": p.key_levels,
            }
            for p in result.patterns
        ],
        "count": len(result.patterns),
        "success": result.success,
        "message": result.message,
    }


@router.post("/scan")
async def scan_patterns_endpoint(
    req: PatternScanRequest,
    conn: asyncpg.Connection = Depends(get_conn),
):
    """Batch scan multiple assets for patterns."""
    results = await scan_patterns(conn, req.asset_ids)
    return {
        "results": [
            {
                "asset_id": r.asset_id,
                "symbol": r.symbol,
                "current_price": r.current_price,
                "patterns": [
                    {
                        "pattern_type": p.pattern_type,
                        "direction": p.direction,
                        "confidence": p.confidence,
                        "description": p.description,
                    }
                    for p in r.patterns
                ],
                "count": len(r.patterns),
            }
            for r in results
        ],
        "scanned": len(req.asset_ids),
    }
