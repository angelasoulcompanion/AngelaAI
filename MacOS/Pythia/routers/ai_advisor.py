"""
Pythia Router — AI Portfolio Advisor
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
import asyncpg

from db import get_conn
from services.ai_advisor_service import generate_ai_advice, chat_with_advisor, get_conversation_history

router = APIRouter(prefix="/api/ai/advisor", tags=["AI Advisor"])


@router.get("/{portfolio_id}/analyze")
async def analyze(
    portfolio_id: UUID,
    question: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await generate_ai_advice(conn, portfolio_id, question, session_id)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/{portfolio_id}/chat")
async def chat(
    portfolio_id: UUID,
    req: ChatRequest,
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await chat_with_advisor(conn, portfolio_id, req.message, req.session_id)


@router.get("/{portfolio_id}/history")
async def history(
    portfolio_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await get_conversation_history(conn, portfolio_id, limit)
