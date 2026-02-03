"""Executive news endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/news", tags=["news"])


async def _fetch_news_with_categories(conn, summary) -> dict:
    """Shared helper: fetch categories + sources for a news summary row."""
    result = dict(summary)

    categories = await conn.fetch("""
        SELECT category_id::text, summary_id::text, category_name, category_type,
               category_icon, category_color, summary_text, angela_opinion,
               importance_level, display_order,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
        FROM executive_news_categories
        WHERE summary_id = $1::uuid
        ORDER BY display_order ASC
    """, summary['summary_id'])

    result['categories'] = []
    for cat in categories:
        cat_dict = dict(cat)

        sources = await conn.fetch("""
            SELECT source_id::text, category_id::text, title, url, source_name,
                   angela_note,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM executive_news_sources
            WHERE category_id = $1::uuid
            ORDER BY created_at ASC
        """, cat['category_id'])

        cat_dict['sources'] = [dict(s) for s in sources]
        result['categories'].append(cat_dict)

    return result


@router.get("/today")
async def get_today_executive_news(conn=Depends(get_conn)):
    """Fetch today's executive news summary (Bangkok timezone)"""
    summary = await conn.fetchrow("""
        SELECT summary_id::text,
               to_char(summary_date, 'YYYY-MM-DD"T"00:00:00.000"+00:00"') as summary_date,
               overall_summary, angela_mood,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
        FROM executive_news_summaries
        WHERE summary_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        LIMIT 1
    """)

    if not summary:
        return None

    return await _fetch_news_with_categories(conn, summary)


@router.get("/date/{date_str}")
async def get_executive_news_by_date(date_str: str, conn=Depends(get_conn)):
    """Fetch executive news summary for a specific date"""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    summary = await conn.fetchrow("""
        SELECT summary_id::text,
               to_char(summary_date, 'YYYY-MM-DD"T"00:00:00.000"+00:00"') as summary_date,
               overall_summary, angela_mood,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
        FROM executive_news_summaries
        WHERE summary_date = $1
        LIMIT 1
    """, target_date)

    if not summary:
        return None

    return await _fetch_news_with_categories(conn, summary)


@router.get("/list")
async def get_executive_news_list(days: int = Query(30, ge=1, le=90), conn=Depends(get_conn)):
    """Fetch list of recent executive news summaries"""
    rows = await conn.fetch("""
        SELECT summary_id::text,
               to_char(summary_date, 'YYYY-MM-DD"T"00:00:00.000"+00:00"') as summary_date,
               overall_summary, angela_mood,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
        FROM executive_news_summaries
        ORDER BY summary_date DESC
        LIMIT $1
    """, days)
    return [dict(r) for r in rows]


@router.get("/statistics")
async def get_executive_news_statistics(conn=Depends(get_conn)):
    """Fetch executive news statistics"""
    summaries = await conn.fetchval("SELECT COUNT(*) FROM executive_news_summaries") or 0
    categories = await conn.fetchval("SELECT COUNT(*) FROM executive_news_categories") or 0
    sources = await conn.fetchval("SELECT COUNT(*) FROM executive_news_sources") or 0
    return {
        "total_summaries": summaries,
        "total_categories": categories,
        "total_sources": sources
    }
