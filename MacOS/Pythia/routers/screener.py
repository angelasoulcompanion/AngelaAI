"""
Pythia Router — Smart Screener
NL query + preset screens for asset filtering.
"""
from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.screener_service import natural_language_screen, preset_screen, PRESET_SCREENS

router = APIRouter(prefix="/api/screener", tags=["Smart Screener"])


@router.get("/search")
async def search_endpoint(
    query: str = Query(..., description="Natural language screening query"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await natural_language_screen(conn, query)
    return {
        "query": result.query,
        "results": result.results,
        "filters_applied": result.filters_applied,
        "total": result.total,
        "success": result.success,
        "message": result.message,
    }


@router.get("/preset/{preset_name}")
async def preset_endpoint(
    preset_name: str,
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await preset_screen(conn, preset_name)
    return {
        "query": result.query,
        "results": result.results,
        "total": result.total,
        "success": result.success,
        "message": result.message,
    }


@router.get("/presets")
async def list_presets():
    return {
        "presets": [
            {"key": k, "name": v["name"], "description": v["description"]}
            for k, v in PRESET_SCREENS.items()
        ]
    }
