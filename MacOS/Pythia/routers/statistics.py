"""
Pythia Router — Statistical Analysis
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.statistical_service import analyze_distribution

router = APIRouter(prefix="/api/statistics", tags=["Statistics"])


@router.get("/{asset_id}/distribution")
async def distribution_analysis(
    asset_id: UUID,
    days: int = Query(365, ge=30, le=3650),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await analyze_distribution(conn, asset_id, days)
    return {
        "symbol": result.symbol,
        "n_observations": result.n_observations,
        "descriptive": {
            "mean": result.mean,
            "std": result.std,
            "median": result.median,
            "skewness": result.skewness,
            "kurtosis": result.kurtosis,
            "min": result.min_return,
            "max": result.max_return,
        },
        "percentiles": {
            "p1": result.percentile_1,
            "p5": result.percentile_5,
            "p95": result.percentile_95,
            "p99": result.percentile_99,
        },
        "tests": result.tests,
        "histogram": result.histogram,
        "success": result.success,
        "message": result.message,
    }
