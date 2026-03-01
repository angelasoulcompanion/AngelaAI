"""
Pythia Router — AI Portfolio Advisor
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.ai_advisor_service import generate_ai_advice, get_conversation_history

router = APIRouter(prefix="/api/ai/advisor", tags=["AI Advisor"])


@router.get("/{portfolio_id}/analyze")
async def analyze(
    portfolio_id: UUID,
    question: Optional[str] = Query(None),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await generate_ai_advice(conn, portfolio_id, question)


@router.get("/{portfolio_id}/history")
async def history(
    portfolio_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await get_conversation_history(conn, portfolio_id, limit)
