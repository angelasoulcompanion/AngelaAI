"""RAG router — read-only dashboard over Angela's domain knowledge bases.

This machine no longer embeds documents into tables. The page is now a
dashboard that surfaces the state of Angela's `rag_*` corpora on Supabase
(Tokyo), all built with IBM granite-embedding:278m (768d).
"""

import logging

from fastapi import APIRouter, HTTPException

from services.db_service import get_pool

router = APIRouter(tags=["rag"])
logger = logging.getLogger(__name__)

# The rag_* corpus was embedded with IBM granite-embedding:278m (768d).
EMBED_MODEL = "granite-embedding:278m"
EMBED_DIMS = 768

# domain key → (table, human label)
DOMAINS: list[tuple[str, str, str]] = [
    ("quant", "rag_quant", "Quant Finance"),
    ("ai", "rag_ai", "AI / ML"),
    ("bible", "rag_bible", "Bible (KJV + Thai)"),
    ("wine", "rag_wine", "Wine"),
    ("photography", "rag_photography", "Photography"),
]


async def _domain_stats(conn, key: str, table: str, label: str) -> dict:
    """Read-only aggregate for one rag_* table."""
    agg = await conn.fetchrow(
        f"""
        SELECT COUNT(*)                AS chunks,
               COUNT(embedding)        AS embedded,
               COUNT(DISTINCT source)  AS sources,
               COALESCE(SUM(token_count), 0) AS tokens,
               MAX(created_at)         AS updated_at
        FROM {table}
        """
    )
    langs = await conn.fetch(
        f"SELECT language, COUNT(*) AS n FROM {table} "
        f"GROUP BY language ORDER BY n DESC"
    )
    top = await conn.fetch(
        f"SELECT source, COUNT(*) AS n FROM {table} "
        f"GROUP BY source ORDER BY n DESC LIMIT 3"
    )
    return {
        "key": key,
        "table": table,
        "label": label,
        "chunks": agg["chunks"],
        "embedded": agg["embedded"],
        "sources": agg["sources"],
        "tokens": int(agg["tokens"]),
        "updatedAt": agg["updated_at"].isoformat() if agg["updated_at"] else None,
        "languages": [{"language": r["language"] or "?", "count": r["n"]} for r in langs],
        "topSources": [{"source": r["source"] or "?", "count": r["n"]} for r in top],
    }


@router.get("/rag/angela-stats")
async def angela_rag_stats():
    """Dashboard payload: per-domain corpus stats + summary roll-up."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            domains = [
                await _domain_stats(conn, key, table, label)
                for key, table, label in DOMAINS
            ]
    except Exception as e:  # noqa: BLE001 — surface the real error to the client
        logger.error("angela_rag_stats failed: %s", e)
        raise HTTPException(status_code=503, detail=f"RAG stats unavailable: {e}")

    total_chunks = sum(d["chunks"] for d in domains)
    total_sources = sum(d["sources"] for d in domains)
    total_tokens = sum(d["tokens"] for d in domains)
    total_embedded = sum(d["embedded"] for d in domains)
    last_updated = max(
        (d["updatedAt"] for d in domains if d["updatedAt"]), default=None
    )

    return {
        "embedModel": EMBED_MODEL,
        "embedDims": EMBED_DIMS,
        "totalChunks": total_chunks,
        "totalDomains": len(domains),
        "totalSources": total_sources,
        "totalTokens": total_tokens,
        "totalEmbedded": total_embedded,
        "lastUpdated": last_updated,
        "domains": domains,
    }
