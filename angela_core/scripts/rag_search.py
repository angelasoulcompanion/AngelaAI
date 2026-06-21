#!/usr/bin/env python3
"""
rag_search.py — Semantic retrieval over Angela's domain RAG knowledge bases.

Embeds a query with granite-embedding:278m (768d, via Ollama) — the SAME model
the `rag_*` corpus was built with — and runs a cosine search against one of the
`rag_*` tables on Supabase (Tokyo). Returns the top-k most relevant chunks so
Angela can ground answers in real source material instead of relying on memory.

NOTE: the corpus is granite-space, NOT nomic-space. Embedding a query with the
nomic-pinned `embedding_service` yields near-orthogonal vectors (verified: a
chunk re-embedded with nomic does not even match itself). Always embed with
granite here.

Domains (public schema, Supabase vdvjfivhvvmlpgdhjmga):
    quant  → rag_quant       (~36.8k)  Wilmott · Hull · CQF 2025 · XVA
    ai     → rag_ai          (~22.2k)  Géron · Raschka · AI Engineering · LLM handbook
    bible  → rag_bible       (~16.2k)  KJV + Thai
    wine   → rag_wine        (~4.1k)   1001 Wines · david_wine_prefs
    photo  → rag_photography (~2.7k)   Fuji X-E5 manual · Photography Masterclass

Pass `auto` (or `all`) as the domain to fan out across every corpus at once
and merge the global top-k by similarity — use this when the right domain is
not obvious. `--json` emits machine-readable results for programmatic callers.

Usage:
    python3 angela_core/scripts/rag_search.py quant "how is XVA computed?"
    python3 angela_core/scripts/rag_search.py ai "RAG re-ranking strategies" -k 8
    python3 angela_core/scripts/rag_search.py photo "X-E5 film simulation" --full
    python3 angela_core/scripts/rag_search.py auto "what is a martingale?" -k 6
    python3 angela_core/scripts/rag_search.py auto "Fuji film sim" --json

All retrieval logic stays here; embedding is reused from the SSOT
`embedding_service`. CLI-only — does not require the backend to be running.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow running as a standalone script (python3 angela_core/scripts/rag_search.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import asyncpg  # noqa: E402
import httpx  # noqa: E402

from config import get_supabase_url  # noqa: E402

# The rag_* corpus was embedded with IBM granite-embedding:278m (768d).
# Query embeddings MUST use the same model to share the vector space.
EMBED_MODEL = "granite-embedding:278m"
EMBED_DIMS = 768
OLLAMA_URL = "http://localhost:11434"


async def _granite_embed(text: str) -> list[float]:
    """Embed `text` with granite-embedding:278m via local Ollama."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text, "keep_alive": "3m"},
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Ollama error: {data['error']}")
        emb = data.get("embedding")
        if not emb:
            raise RuntimeError("Ollama returned empty embedding")
        return emb


def _to_pgvector(embedding: list[float]) -> str:
    return "[" + ",".join(map(str, embedding)) + "]"


# domain alias → (table, human label)
DOMAINS: dict[str, tuple[str, str]] = {
    "quant": ("rag_quant", "Quant Finance"),
    "ai": ("rag_ai", "AI / ML"),
    "bible": ("rag_bible", "Bible (KJV + Thai)"),
    "wine": ("rag_wine", "Wine"),
    "photo": ("rag_photography", "Photography"),
    "photography": ("rag_photography", "Photography"),
}

# Aliases that fan out across every corpus at once.
AUTO_KEYS = {"auto", "all"}

# Deduped ordered (table, label) pairs — one entry per physical table.
DOMAIN_TABLES: list[tuple[str, str]] = []
_seen_tables: set[str] = set()
for _t, _l in DOMAINS.values():
    if _t not in _seen_tables:
        _seen_tables.add(_t)
        DOMAIN_TABLES.append((_t, _l))


async def _embed_query(query: str) -> str:
    """Embed `query` with granite (768d) and return a pgvector literal."""
    embedding = await _granite_embed(query)
    if not embedding or len(embedding) != EMBED_DIMS:
        raise RuntimeError(
            f"Embedding failed (got {len(embedding) if embedding else 0} dims, "
            f"expected {EMBED_DIMS}). Is Ollama running with {EMBED_MODEL}?"
        )
    return _to_pgvector(embedding)


async def _query_table(
    conn, table: str, label: str, vec: str, k: int, min_similarity: float
) -> list[dict]:
    """Top-k cosine matches in one rag_* table. `<=>` is cosine distance."""
    rows = await conn.fetch(
        f"""
        SELECT source, source_ref, topic, content,
               1 - (embedding <=> $1::vector) AS similarity
        FROM {table}
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector
        LIMIT $2
        """,
        vec,
        k,
    )
    out = []
    for r in rows:
        if r["similarity"] is None or r["similarity"] < min_similarity:
            continue
        d = dict(r)
        d["domain"] = label
        out.append(d)
    return out


async def rag_search(
    domain: str,
    query: str,
    k: int = 5,
    min_similarity: float = 0.0,
) -> list[dict]:
    """Embed `query` and return the top-k nearest chunks.

    `domain` is a key in DOMAINS, or 'auto'/'all' to fan out across every
    corpus and merge the global top-k by similarity. Each result dict is
    {source, source_ref, topic, content, similarity, domain}.
    """
    is_auto = domain in AUTO_KEYS
    if not is_auto and domain not in DOMAINS:
        raise ValueError(
            f"Unknown domain '{domain}'. Choose one of: "
            f"{', '.join(sorted(set(DOMAINS)))}, auto"
        )

    vec = await _embed_query(query)
    dsn = get_supabase_url().split("?")[0]  # asyncpg takes ssl= kwarg, not sslmode in DSN
    conn = await asyncpg.connect(dsn, ssl="require", statement_cache_size=0)
    try:
        if is_auto:
            merged: list[dict] = []
            for table, label in DOMAIN_TABLES:
                merged += await _query_table(conn, table, label, vec, k, min_similarity)
            merged.sort(key=lambda r: r["similarity"], reverse=True)
            return merged[:k]
        table, label = DOMAINS[domain]
        return await _query_table(conn, table, label, vec, k, min_similarity)
    finally:
        await conn.close()


def _header_label(domain: str) -> str:
    return "All domains" if domain in AUTO_KEYS else DOMAINS[domain][1]


def _print_results(domain: str, query: str, results: list[dict], full: bool) -> None:
    label = _header_label(domain)
    print(f"\n🔎 RAG · {label}  |  query: {query!r}  |  {len(results)} hits\n" + "─" * 72)
    if not results:
        print("  (no results — try a different domain or lower --min)")
        return
    for i, r in enumerate(results, 1):
        sim = r["similarity"]
        src = r.get("source") or "?"
        ref = r.get("source_ref")
        topic = r.get("topic")
        head = f"[{i}] sim={sim:.3f}  {src}"
        # In auto mode, tag each hit with the corpus it came from.
        if domain in AUTO_KEYS and r.get("domain"):
            head += f"  «{r['domain']}»"
        if ref:
            head += f"  ({ref})"
        if topic:
            head += f"  · {topic}"
        print(head)
        content = (r.get("content") or "").strip()
        if not full and len(content) > 600:
            content = content[:600].rstrip() + " …"
        print("    " + content.replace("\n", "\n    "))
        print("─" * 72)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Semantic search over Angela's domain RAG knowledge bases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Domains: " + ", ".join(sorted(set(DOMAINS))) + ", auto (all)",
    )
    p.add_argument("domain", help="quant | ai | bible | wine | photo | auto")
    p.add_argument("query", help="natural-language query")
    p.add_argument("-k", type=int, default=5, help="number of chunks (default 5)")
    p.add_argument(
        "--min", type=float, default=0.0, dest="min_similarity",
        help="minimum cosine similarity 0..1 (default 0)",
    )
    p.add_argument("--full", action="store_true", help="print full chunk content")
    p.add_argument("--json", action="store_true", help="emit results as JSON")
    args = p.parse_args()

    try:
        results = asyncio.run(
            rag_search(args.domain, args.query, k=args.k, min_similarity=args.min_similarity)
        )
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 — surface the real error to the operator
        print(f"❌ rag_search failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        import json
        payload = {
            "domain": args.domain,
            "query": args.query,
            "count": len(results),
            "results": [
                {k: v for k, v in r.items() if k != "embedding"} for r in results
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        _print_results(args.domain, args.query, results, args.full)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
