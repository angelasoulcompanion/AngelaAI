"""
Consciousness RAG — Vector search across Angela's memory for chat context.
Uses nomic-embed-text (768d) matching existing pgvector embeddings in Neon.

Tables searched:
  - conversations (9,400+ records, 768d) — chat history
  - knowledge_nodes (11,400+ records, 768d) — learned concepts
  - core_memories (159 records, 768d) — important memories

Flow: query → nomic-embed-text (768d) → pgvector cosine → top-K context
"""

import logging
import time
from typing import Optional

import aiohttp

from services.db_service import get_pool

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"  # 768d — matches DB vectors exactly


async def _embed_query(text: str) -> Optional[list[float]]:
    """Get 768d embedding from nomic-embed-text via Ollama."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/embed",
                json={"model": EMBED_MODEL, "input": text},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embeddings = data.get("embeddings", [])
                    return embeddings[0] if embeddings else None
    except Exception as e:
        logger.warning("Embedding failed: %s", e)
    return None


async def search_memory(query: str, top_k: int = 5, min_score: float = 0.3) -> list[dict]:
    """
    Search Angela's memory using pgvector cosine similarity.

    Searches 3 tables in parallel, merges by score, returns top-K.
    """
    t0 = time.time()

    embedding = await _embed_query(query)
    if not embedding:
        logger.warning("No embedding for query, falling back to text search")
        return await _text_search_fallback(query, top_k)

    embed_time = time.time() - t0
    emb_str = f"[{','.join(str(float(x)) for x in embedding)}]"

    pool = await get_pool()
    results = []

    # Search 3 tables via UNION — actual column names from schema
    rows = await pool.fetch("""
        (
            SELECT 'conversation' as source,
                   COALESCE(topic, speaker) as title,
                   COALESCE(message_text, '') as content,
                   1 - (embedding <=> $1::vector) as score,
                   created_at
            FROM conversations
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        )
        UNION ALL
        (
            SELECT 'knowledge' as source,
                   COALESCE(concept_name, '') as title,
                   COALESCE(my_understanding, '') as content,
                   1 - (embedding <=> $1::vector) as score,
                   created_at
            FROM knowledge_nodes
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        )
        UNION ALL
        (
            SELECT 'core_memory' as source,
                   COALESCE(title, '') as title,
                   COALESCE(content, '') as content,
                   1 - (embedding <=> $1::vector) as score,
                   created_at
            FROM core_memories
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        )
        ORDER BY score DESC
        LIMIT $2
    """, emb_str, top_k)

    for r in rows:
        score = float(r["score"])
        if score >= min_score:
            results.append({
                "source": r["source"],
                "title": r["title"][:200],
                "content": r["content"][:500],
                "score": round(score, 3),
                "created_at": str(r["created_at"]) if r["created_at"] else None,
            })

    total_time = time.time() - t0
    logger.info(
        "RAG search: %d results (embed %.1fs + search %.1fs = %.1fs)",
        len(results), embed_time, total_time - embed_time, total_time,
    )
    return results


async def _text_search_fallback(query: str, top_k: int = 5) -> list[dict]:
    """Fallback: keyword search when embedding unavailable."""
    pool = await get_pool()
    pattern = f"%{query[:100]}%"

    rows = await pool.fetch("""
        (
            SELECT 'conversation' as source,
                   COALESCE(topic, speaker) as title,
                   COALESCE(message_text, '') as content,
                   0.5 as score,
                   created_at
            FROM conversations
            WHERE message_text ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
        )
        UNION ALL
        (
            SELECT 'knowledge' as source,
                   COALESCE(concept_name, '') as title,
                   COALESCE(my_understanding, '') as content,
                   0.5 as score,
                   created_at
            FROM knowledge_nodes
            WHERE my_understanding ILIKE $1 OR concept_name ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
        )
        ORDER BY created_at DESC
        LIMIT $2
    """, pattern, top_k)

    return [
        {
            "source": r["source"],
            "title": r["title"][:200],
            "content": r["content"][:500],
            "score": 0.5,
        }
        for r in rows
    ]


def format_context_for_prompt(results: list[dict], max_chars: int = 2000) -> str:
    """Format RAG results into a system prompt section."""
    if not results:
        return ""

    lines = ["Relevant context from Angela's memory:"]
    total = 0
    for r in results:
        entry = f"[{r['source']}] {r['title']}: {r['content']}"
        if total + len(entry) > max_chars:
            break
        lines.append(f"- {entry}")
        total += len(entry)

    return "\n".join(lines)
