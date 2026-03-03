"""
Pythia — AI Research RAG Service
Hybrid: Keyword + Vector (pgvector) + Hybrid (RRF) search + LLM summarization + Ask mode.
"""
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4

import asyncpg


@dataclass
class ResearchResult:
    query: str
    results: list[dict] = field(default_factory=list)
    summary: str = ""
    sources_count: int = 0
    search_method: Optional[str] = None
    llm_provider: Optional[str] = None
    success: bool = True
    message: str = ""


@dataclass
class AskResult:
    question: str
    answer: str = ""
    sources: list[dict] = field(default_factory=list)
    llm_provider: Optional[str] = None
    success: bool = True
    message: str = ""


async def search_research(
    conn: asyncpg.Connection,
    query: str,
    method: str = "keyword",
    limit: int = 10,
    include_summary: bool = False,
) -> ResearchResult:
    """Enhanced research search: keyword / vector / hybrid modes."""
    if method == "vector":
        results = await _search_vector(conn, query, limit)
    elif method == "hybrid":
        results = await _search_hybrid(conn, query, limit)
    else:
        results = await _search_keyword(conn, query, limit)

    # Fallback: search asset database
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

    summary = f"Found {len(results)} results for '{query}' ({method})"

    # Optional LLM summary
    llm_provider: Optional[str] = None
    if include_summary and results:
        try:
            from services.llm_service import llm_service

            docs_text = "\n".join(
                f"- {r['title']}: {(r.get('content') or '')[:200]}"
                for r in results[:5]
            )
            prompt = f"""Summarize these research results for the query "{query}":

{docs_text}

Write a concise 2-3 sentence summary of the key findings."""

            llm_resp = await llm_service.complete(
                prompt=prompt,
                system="You are a financial research analyst. Summarize concisely.",
                complexity="simple",
                max_tokens=256,
            )
            if llm_resp.success and llm_resp.text:
                summary = llm_resp.text
                llm_provider = llm_resp.provider
        except Exception:
            pass

    return ResearchResult(
        query=query,
        results=results,
        summary=summary,
        sources_count=len(results),
        search_method=method,
        llm_provider=llm_provider,
    )


async def _search_keyword(
    conn: asyncpg.Connection,
    query: str,
    limit: int,
) -> list[dict]:
    """Full-text keyword search (original)."""
    rows = await conn.fetch("""
        SELECT document_id, title, content, source, metadata, created_at
        FROM research_documents
        WHERE to_tsvector('english', COALESCE(title,'') || ' ' || COALESCE(content, '')) @@ plainto_tsquery('english', $1)
        ORDER BY created_at DESC
        LIMIT $2
    """, query, limit)
    return [_row_to_dict(r) for r in rows]


async def _search_vector(
    conn: asyncpg.Connection,
    query: str,
    limit: int,
) -> list[dict]:
    """Vector similarity search using pgvector cosine distance."""
    try:
        from services.embedding_service import embedding_service
        from helpers.pgvector_utils import embedding_to_pgvector

        query_emb = await embedding_service.embed(query)
        if not query_emb:
            return await _search_keyword(conn, query, limit)

        emb_str = embedding_to_pgvector(query_emb)

        # Check if embedding column exists and has data
        has_embeddings = await conn.fetchval(
            "SELECT COUNT(*) FROM research_documents WHERE embedding IS NOT NULL"
        )
        if not has_embeddings:
            return await _search_keyword(conn, query, limit)

        rows = await conn.fetch(f"""
            SELECT document_id, title, content, source, metadata, created_at,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM research_documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """, emb_str, limit)
        return [_row_to_dict(r, similarity=float(r.get("similarity", 0))) for r in rows]

    except Exception:
        return await _search_keyword(conn, query, limit)


async def _search_hybrid(
    conn: asyncpg.Connection,
    query: str,
    limit: int,
) -> list[dict]:
    """Hybrid search: RRF (Reciprocal Rank Fusion) of keyword + vector results.
    Pattern from CogniFy RAG service.
    """
    k = 60  # RRF constant

    # Get both result sets
    keyword_results = await _search_keyword(conn, query, limit * 2)
    vector_results = await _search_vector(conn, query, limit * 2)

    # Build RRF scores
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, doc in enumerate(keyword_results):
        doc_id = doc.get("document_id") or doc["title"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        docs[doc_id] = doc

    for rank, doc in enumerate(vector_results):
        doc_id = doc.get("document_id") or doc["title"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        docs[doc_id] = doc

    # Sort by RRF score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [docs[doc_id] for doc_id in sorted_ids[:limit]]


async def ask_research(
    conn: asyncpg.Connection,
    question: str,
) -> AskResult:
    """RAG Q&A: hybrid search → Claude generates grounded answer."""
    # Step 1: Hybrid search for relevant documents
    search_result = await search_research(conn, question, method="hybrid", limit=5)

    if not search_result.results:
        return AskResult(
            question=question,
            answer="No relevant research documents found. Try storing some research first.",
            success=True,
        )

    # Step 2: Build context from top results
    context_parts = []
    sources = []
    for doc in search_result.results[:5]:
        content = (doc.get("content") or "")[:1000]
        if content:
            context_parts.append(f"[{doc['title']}]\n{content}")
            sources.append({
                "title": doc["title"],
                "source_url": doc.get("source_url"),
                "source_type": doc.get("source_type"),
            })

    context_text = "\n\n---\n\n".join(context_parts)

    # Step 3: Generate grounded answer via Claude (complex task)
    try:
        from services.llm_service import llm_service

        prompt = f"""Based on the following research documents, answer the question.
Only use information from the provided documents. If the documents don't contain enough information, say so.

Documents:
{context_text}

Question: {question}

Provide a clear, specific answer with references to the source documents."""

        llm_resp = await llm_service.complete(
            prompt=prompt,
            system="You are a financial research analyst. Answer based ONLY on the provided documents. Cite sources.",
            complexity="complex",
            max_tokens=1024,
        )
        if llm_resp.success and llm_resp.text:
            return AskResult(
                question=question,
                answer=llm_resp.text,
                sources=sources,
                llm_provider=llm_resp.provider,
            )
    except Exception:
        pass

    # Fallback: return search results summary
    return AskResult(
        question=question,
        answer=f"Found {len(search_result.results)} relevant documents but LLM is unavailable for summarization.",
        sources=sources,
    )


async def store_research(
    conn: asyncpg.Connection,
    title: str,
    content: str,
    source_url: Optional[str] = None,
    source_type: str = "manual",
    tags: Optional[list[str]] = None,
) -> dict:
    """Store a research document with auto-embedding."""
    import json as _json
    doc_id = uuid4()
    embedding_str: Optional[str] = None
    metadata = _json.dumps({"source_type": source_type, "tags": tags or [], "source_url": source_url})

    # Auto-embed on store
    try:
        from services.embedding_service import embedding_service
        from helpers.pgvector_utils import embedding_to_pgvector

        emb = await embedding_service.embed(f"{title} {content[:500]}")
        if emb:
            embedding_str = embedding_to_pgvector(emb)
    except Exception:
        pass

    if embedding_str:
        await conn.execute("""
            INSERT INTO research_documents (document_id, title, content, source, metadata, embedding)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::vector)
        """, doc_id, title, content, source_url or source_type, metadata, embedding_str)
    else:
        await conn.execute("""
            INSERT INTO research_documents (document_id, title, content, source, metadata)
            VALUES ($1, $2, $3, $4, $5::jsonb)
        """, doc_id, title, content, source_url or source_type, metadata)

    return {"document_id": str(doc_id), "title": title, "embedded": embedding_str is not None, "success": True}


async def get_research_history(
    conn: asyncpg.Connection,
    limit: int = 20,
) -> list[dict]:
    """Get recent research documents."""
    rows = await conn.fetch("""
        SELECT document_id, title, source, metadata, created_at
        FROM research_documents
        ORDER BY created_at DESC
        LIMIT $1
    """, limit)
    return [
        {
            "document_id": str(r["document_id"]),
            "title": r["title"],
            "source_type": (r["metadata"] or {}).get("source_type", r["source"]) if r["metadata"] else r["source"],
            "tags": (r["metadata"] or {}).get("tags", []) if r["metadata"] else [],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]


def _row_to_dict(r: asyncpg.Record, similarity: Optional[float] = None) -> dict:
    """Convert a database row to result dict."""
    meta = r.get("metadata") or {}
    if isinstance(meta, str):
        import json as _json
        try:
            meta = _json.loads(meta)
        except Exception:
            meta = {}
    d = {
        "document_id": str(r["document_id"]),
        "title": r["title"],
        "content": (r["content"] or "")[:500],
        "source_url": meta.get("source_url") or r.get("source"),
        "source_type": meta.get("source_type") or r.get("source"),
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
    }
    if similarity is not None:
        d["similarity"] = round(similarity, 4)
    return d
