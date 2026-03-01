"""
Pythia — AI Research RAG Service
Simple keyword-based research from stored documents + web search.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID, uuid4

import asyncpg


@dataclass
class ResearchResult:
    query: str
    results: list[dict] = field(default_factory=list)
    summary: str = ""
    sources_count: int = 0
    success: bool = True
    message: str = ""


async def search_research(
    conn: asyncpg.Connection,
    query: str,
    limit: int = 10,
) -> ResearchResult:
    """Search stored research documents."""
    # Search in research_documents table
    rows = await conn.fetch("""
        SELECT document_id, title, content, source_url, source_type, created_at
        FROM research_documents
        WHERE to_tsvector('english', title || ' ' || COALESCE(content, '')) @@ plainto_tsquery('english', $1)
        ORDER BY created_at DESC
        LIMIT $2
    """, query, limit)

    results = [
        {
            "document_id": str(r["document_id"]),
            "title": r["title"],
            "content": (r["content"] or "")[:500],
            "source_url": r["source_url"],
            "source_type": r["source_type"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]

    # Fallback: search asset notes
    if not results:
        asset_rows = await conn.fetch("""
            SELECT symbol, name, sector, industry
            FROM assets
            WHERE to_tsvector('english', symbol || ' ' || name || ' ' || COALESCE(sector, '') || ' ' || COALESCE(industry, ''))
                  @@ plainto_tsquery('english', $1)
            LIMIT $2
        """, query, limit)
        for r in asset_rows:
            results.append({
                "title": f"{r['symbol']} — {r['name']}",
                "content": f"Sector: {r['sector']}, Industry: {r['industry']}",
                "source_type": "asset_database",
            })

    summary = f"Found {len(results)} results for '{query}'" if results else f"No results found for '{query}'"

    return ResearchResult(
        query=query,
        results=results,
        summary=summary,
        sources_count=len(results),
    )


async def store_research(
    conn: asyncpg.Connection,
    title: str,
    content: str,
    source_url: Optional[str] = None,
    source_type: str = "manual",
    tags: Optional[list[str]] = None,
) -> dict:
    """Store a research document."""
    doc_id = uuid4()
    await conn.execute("""
        INSERT INTO research_documents (document_id, title, content, source_url, source_type, tags)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, doc_id, title, content, source_url, source_type, tags or [])

    return {"document_id": str(doc_id), "title": title, "success": True}


async def get_research_history(
    conn: asyncpg.Connection,
    limit: int = 20,
) -> list[dict]:
    """Get recent research documents."""
    rows = await conn.fetch("""
        SELECT document_id, title, source_type, tags, created_at
        FROM research_documents
        ORDER BY created_at DESC
        LIMIT $1
    """, limit)
    return [
        {
            "document_id": str(r["document_id"]),
            "title": r["title"],
            "source_type": r["source_type"],
            "tags": r["tags"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]
