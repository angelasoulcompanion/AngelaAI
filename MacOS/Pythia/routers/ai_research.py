"""
Pythia Router — AI Research RAG
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
import asyncpg
from pydantic import BaseModel

from db import get_conn
from services.ai_rag_service import search_research, store_research, get_research_history

router = APIRouter(prefix="/api/ai/research", tags=["AI Research"])


@router.get("/search")
async def search(
    query: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await search_research(conn, query, limit)
    return {
        "query": result.query,
        "results": result.results,
        "summary": result.summary,
        "sources_count": result.sources_count,
        "success": result.success,
    }


class StoreRequest(BaseModel):
    title: str
    content: str
    source_url: Optional[str] = None
    source_type: str = "manual"
    tags: Optional[list[str]] = None


@router.post("/store")
async def store(
    req: StoreRequest,
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await store_research(conn, req.title, req.content, req.source_url, req.source_type, req.tags)


@router.get("/history")
async def history(
    limit: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await get_research_history(conn, limit)
