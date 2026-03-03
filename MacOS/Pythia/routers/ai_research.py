"""
Pythia Router — AI Research RAG
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
import asyncpg
from pydantic import BaseModel

from db import get_conn
from services.ai_rag_service import search_research, store_research, get_research_history, ask_research

router = APIRouter(prefix="/api/ai/research", tags=["AI Research"])


@router.get("/search")
async def search(
    query: str = Query(..., min_length=2),
    method: str = Query("keyword", description="keyword | vector | hybrid"),
    limit: int = Query(10, ge=1, le=50),
    include_summary: bool = Query(False, description="Include LLM summary"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await search_research(conn, query, method, limit, include_summary)
    return {
        "query": result.query,
        "results": result.results,
        "summary": result.summary,
        "sources_count": result.sources_count,
        "search_method": result.search_method,
        "llm_provider": result.llm_provider,
        "success": result.success,
    }


@router.get("/ask")
async def ask(
    question: str = Query(..., min_length=2),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await ask_research(conn, question)
    return {
        "question": result.question,
        "answer": result.answer,
        "sources": result.sources,
        "llm_provider": result.llm_provider,
        "success": result.success,
        "message": result.message,
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
