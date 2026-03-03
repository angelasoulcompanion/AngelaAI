"""
Pythia Router — AI Sentiment Analysis
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
import asyncpg

from db import get_conn
from services.ai_sentiment_service import analyze_sentiment

router = APIRouter(prefix="/api/ai/sentiment", tags=["AI Sentiment"])


@router.get("/{asset_id}")
async def sentiment(
    asset_id: UUID,
    days: int = Query(30, ge=7, le=365),
    include_news: bool = Query(False, description="Include yfinance news sentiment"),
    include_narrative: bool = Query(False, description="Include LLM narrative commentary"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    result = await analyze_sentiment(conn, asset_id, days, include_news, include_narrative)
    return {
        "symbol": result.symbol,
        "sentiment": result.sentiment,
        "score": result.score,
        "signals": result.signals,
        "price_momentum": result.price_momentum,
        "volume_trend": result.volume_trend,
        "volatility_regime": result.volatility_regime,
        # Enhanced fields
        "narrative": result.narrative,
        "news_headlines": result.news_headlines,
        "technical_score": result.technical_score,
        "news_score": result.news_score,
        "combined_score": result.combined_score,
        "llm_provider": result.llm_provider,
        "success": result.success,
        "message": result.message,
    }
