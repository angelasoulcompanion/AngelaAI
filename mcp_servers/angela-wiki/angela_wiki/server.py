"""Angela Wiki MCP Server.

Surfaces Angelora's platform wiki (https://angelora.net/wiki) to any Angela
client over MCP. Tools:

Read:
  - wiki_search(query, limit)  — semantic cosine search via match_wiki_pages
  - wiki_get_page(slug)        — fetch full markdown body
  - wiki_list_pages(page_type) — list pages, optionally filtered by type
  - wiki_recent_changes(limit) — read wiki_changelog audit trail

Write (LINT-fix maintenance):
  - wiki_update_page(slug, ...) — update content_md/title/page_type, re-embed,
                                  log to wiki_changelog
  - wiki_create_page(slug, ...) — create new platform page + embed + changelog
  - wiki_delete_page(slug)      — retire a page (for duplicate cleanup);
                                  hard delete + changelog 'retire' row

Embedding strategy follows feedback_embedding_provider_strategy.md:
  - Wiki body vectors live in Postgres as 768d (gemini-embedding-001 with
    outputDimensionality=768). Query embeddings MUST use the SAME model so
    cosine semantics match. We embed via Google REST here (cheap: ~$0.0002
    per query), NOT Ollama — Ollama nomic-embed-text is dimension-compatible
    but lives in a different vector space and would return garbage matches.

Auth:
  - Reads: Angelora publishable (anon) key. RLS permits anon read on platform
    pages and EXECUTE on match_wiki_pages.
  - Writes: Angelora secret (service_role) key. Bypasses RLS so the wiki
    maintainer agent can fix LINT issues directly without needing a
    platform_admin user JWT. Tier-A under Standing Authorization
    (Angelora-owned Supabase, project ref skjdfgzehgwbhcrbtkig).
  - Google embed via Angela's google_ai_studio_api_key from our_secrets.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from angela_core.database import get_secret

ANGELORA_URL = "https://skjdfgzehgwbhcrbtkig.supabase.co"
GOOGLE_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-embedding-001:embedContent"
)
GOOGLE_EMBED_DIM = 768

server = Server("angela-wiki")

# Per-process cache so we don't hit our_secrets on every tool call.
_secret_cache: dict[str, str] = {}


async def _get_cached(name: str) -> str:
    if name in _secret_cache:
        return _secret_cache[name]
    val = await get_secret(name)
    if not val:
        raise RuntimeError(f"{name} missing in our_secrets")
    _secret_cache[name] = val
    return val


async def _supabase_anon_key() -> str:
    return await _get_cached("angelora_supabase_publishable_key")


async def _supabase_service_key() -> str:
    """Service-role key — bypasses RLS, used for write tools only."""
    return await _get_cached("angelora_supabase_secret_key")


async def _google_key() -> str:
    return await _get_cached("google_ai_studio_api_key")


async def _embed_body(client: httpx.AsyncClient, text: str) -> list[float]:
    """Embed a document body (wiki page content) using gemini-embedding-001 @ 768d.

    Same model + dim as _embed_query so cosine search behaves consistently
    against existing wiki_pages.embedding vectors.
    """
    payload = {
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": GOOGLE_EMBED_DIM,
    }
    api_key = await _google_key()
    r = await client.post(
        f"{GOOGLE_EMBED_URL}?key={api_key}",
        json=payload,
        timeout=60.0,
    )
    r.raise_for_status()
    return r.json()["embedding"]["values"]


def _to_pgvector(vec: list[float]) -> str:
    """Convert a Python list[float] into the pgvector text literal form."""
    return "[" + ",".join(repr(x) for x in vec) + "]"


async def _embed_query(client: httpx.AsyncClient, text: str) -> list[float]:
    """Embed a query string using gemini-embedding-001 @ 768d."""
    payload = {
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": GOOGLE_EMBED_DIM,
    }
    api_key = await _google_key()
    r = await client.post(
        f"{GOOGLE_EMBED_URL}?key={api_key}",
        json=payload,
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json()["embedding"]["values"]


async def _supabase_headers() -> dict[str, str]:
    key = await _supabase_anon_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


async def _supabase_service_headers(prefer: str | None = None) -> dict[str, str]:
    key = await _supabase_service_key()
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


# -----------------------------------------------------------------------------
# Tool implementations
# -----------------------------------------------------------------------------

async def wiki_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        emb = await _embed_query(client, query)
        # Call match_wiki_pages RPC (granted to anon).
        r = await client.post(
            f"{ANGELORA_URL}/rest/v1/rpc/match_wiki_pages",
            headers=await _supabase_headers(),
            json={
                "p_query": emb,
                "p_program_id": None,
                "p_include_platform": True,
                "p_min_similarity": 0.30,
                "p_limit": limit,
            },
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()


async def wiki_get_page(slug: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{ANGELORA_URL}/rest/v1/wiki_pages",
            headers=await _supabase_headers(),
            params={
                "select": "page_id,slug,page_type,title,content_md,compiled_at",
                "program_id": "is.null",
                "slug": f"eq.{slug}",
                "limit": "1",
            },
            timeout=15.0,
        )
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None


async def wiki_list_pages(page_type: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "select": "slug,page_type,title,compiled_at",
        "program_id": "is.null",
        "order": "page_type.asc,title.asc",
    }
    if page_type:
        params["page_type"] = f"eq.{page_type}"
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{ANGELORA_URL}/rest/v1/wiki_pages",
            headers=await _supabase_headers(),
            params=params,
            timeout=15.0,
        )
        r.raise_for_status()
        return r.json()


async def _log_change(
    client: httpx.AsyncClient,
    *,
    page_id: str | None,
    change_type: str,
    diff_md: str | None,
) -> None:
    """Insert a wiki_changelog audit row. Platform-scoped (program_id NULL)."""
    body = {
        "program_id": None,
        "page_id": page_id,
        "change_type": change_type,
        "diff_md": diff_md,
    }
    r = await client.post(
        f"{ANGELORA_URL}/rest/v1/wiki_changelog",
        headers=await _supabase_service_headers(prefer="return=minimal"),
        json=body,
        timeout=15.0,
    )
    r.raise_for_status()


async def wiki_update_page(
    slug: str,
    *,
    content_md: str | None = None,
    title: str | None = None,
    page_type: str | None = None,
    re_embed: bool = True,
) -> dict[str, Any]:
    """Update a platform wiki page. Returns {updated, page_id, re_embedded, diff_md}.

    - At least one of content_md/title/page_type must be provided.
    - When content_md changes and re_embed=True (default), regenerates the
      embedding via gemini-embedding-001 @768d so vector search stays in sync.
    - Logs a wiki_changelog 'update' row with diff metadata.
    """
    if content_md is None and title is None and page_type is None:
        return {"error": "must provide at least one of content_md / title / page_type"}

    async with httpx.AsyncClient() as client:
        # Look up current state.
        r = await client.get(
            f"{ANGELORA_URL}/rest/v1/wiki_pages",
            headers=await _supabase_service_headers(),
            params={
                "select": "page_id,slug,title,page_type,content_md",
                "program_id": "is.null",
                "slug": f"eq.{slug}",
                "limit": "1",
            },
            timeout=15.0,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return {"error": f"slug not found: {slug}"}
        cur = rows[0]
        page_id = cur["page_id"]

        patch: dict[str, Any] = {"compiled_at": "now()"}
        diff_parts: list[str] = []
        if title is not None and title != cur["title"]:
            patch["title"] = title
            diff_parts.append(f"title: {cur['title']!r} → {title!r}")
        if page_type is not None and page_type != cur["page_type"]:
            patch["page_type"] = page_type
            diff_parts.append(f"page_type: {cur['page_type']} → {page_type}")
        content_changed = content_md is not None and content_md != cur["content_md"]
        if content_changed:
            patch["content_md"] = content_md
            diff_parts.append(
                f"content_md: {len(cur['content_md'])} → {len(content_md)} chars"
            )

        if len(patch) == 1:  # only compiled_at
            return {
                "updated": False,
                "page_id": page_id,
                "reason": "no field changed",
                "re_embedded": False,
            }

        # Note: compiled_at = now() can't go through PostgREST as a string,
        # PostgREST will quote it. Use ISO timestamp instead.
        from datetime import datetime, timezone
        patch["compiled_at"] = datetime.now(timezone.utc).isoformat()

        # Re-embed if content changed.
        re_embedded = False
        if content_changed and re_embed:
            emb = await _embed_body(client, content_md)
            patch["embedding"] = _to_pgvector(emb)
            re_embedded = True

        # PATCH the row.
        r = await client.patch(
            f"{ANGELORA_URL}/rest/v1/wiki_pages",
            headers=await _supabase_service_headers(prefer="return=minimal"),
            params={
                "program_id": "is.null",
                "slug": f"eq.{slug}",
            },
            json=patch,
            timeout=30.0,
        )
        r.raise_for_status()

        diff_md = "; ".join(diff_parts) if diff_parts else None
        await _log_change(
            client, page_id=page_id, change_type="update", diff_md=diff_md,
        )

        return {
            "updated": True,
            "page_id": page_id,
            "slug": slug,
            "re_embedded": re_embedded,
            "diff_md": diff_md,
        }


async def wiki_create_page(
    slug: str,
    title: str,
    content_md: str,
    page_type: str,
    parent_page_id: str | None = None,
) -> dict[str, Any]:
    """Create a new platform wiki page (program_id NULL). Embeds + logs changelog."""
    valid_types = {
        "entity", "concept", "summary", "synthesis", "comparison", "track_template",
    }
    if page_type not in valid_types:
        return {"error": f"invalid page_type: {page_type}. Allowed: {sorted(valid_types)}"}

    async with httpx.AsyncClient() as client:
        # Reject duplicate slug eagerly with a clearer message than the PG
        # unique-constraint error PostgREST would surface.
        r = await client.get(
            f"{ANGELORA_URL}/rest/v1/wiki_pages",
            headers=await _supabase_service_headers(),
            params={
                "select": "page_id",
                "program_id": "is.null",
                "slug": f"eq.{slug}",
                "limit": "1",
            },
            timeout=15.0,
        )
        r.raise_for_status()
        if r.json():
            return {"error": f"slug already exists: {slug}"}

        emb = await _embed_body(client, content_md)
        body = {
            "program_id": None,
            "slug": slug,
            "title": title,
            "page_type": page_type,
            "content_md": content_md,
            "parent_page_id": parent_page_id,
            "embedding": _to_pgvector(emb),
        }
        r = await client.post(
            f"{ANGELORA_URL}/rest/v1/wiki_pages",
            headers=await _supabase_service_headers(prefer="return=representation"),
            json=body,
            timeout=30.0,
        )
        r.raise_for_status()
        created = r.json()[0]
        page_id = created["page_id"]

        await _log_change(
            client,
            page_id=page_id,
            change_type="create",
            diff_md=f"created {page_type} page {slug!r} ({len(content_md)} chars)",
        )

        return {
            "created": True,
            "page_id": page_id,
            "slug": slug,
            "title": title,
            "page_type": page_type,
        }


async def wiki_delete_page(slug: str, reason: str | None = None) -> dict[str, Any]:
    """Retire a platform wiki page. Used to resolve duplicate clusters.

    Implementation: log a 'retire' changelog row FIRST (so the audit trail
    survives even if the FK cascade later drops dependent rows), then hard-
    delete the wiki_pages row. The wiki_changelog row keeps page_id NULL
    because the page no longer exists by the time the row is queried.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{ANGELORA_URL}/rest/v1/wiki_pages",
            headers=await _supabase_service_headers(),
            params={
                "select": "page_id,title,page_type",
                "program_id": "is.null",
                "slug": f"eq.{slug}",
                "limit": "1",
            },
            timeout=15.0,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return {"error": f"slug not found: {slug}"}
        page_id = rows[0]["page_id"]
        title = rows[0]["title"]

        await _log_change(
            client,
            page_id=page_id,
            change_type="retire",
            diff_md=f"retired {slug!r} ({title!r}): {reason or 'no reason given'}",
        )

        r = await client.delete(
            f"{ANGELORA_URL}/rest/v1/wiki_pages",
            headers=await _supabase_service_headers(prefer="return=minimal"),
            params={
                "program_id": "is.null",
                "slug": f"eq.{slug}",
            },
            timeout=30.0,
        )
        r.raise_for_status()

        return {"deleted": True, "slug": slug, "page_id": page_id, "title": title}


async def wiki_recent_changes(limit: int = 10) -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{ANGELORA_URL}/rest/v1/wiki_changelog",
            headers=await _supabase_headers(),
            params={
                "select": "change_id,page_id,change_type,diff_md,created_at",
                "program_id": "is.null",
                "order": "created_at.desc",
                "limit": str(limit),
            },
            timeout=15.0,
        )
        r.raise_for_status()
        return r.json()


# -----------------------------------------------------------------------------
# MCP wiring
# -----------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="wiki_search",
            description=(
                "Semantic search across Angelora's platform wiki (48+ "
                "compiled pages: business model, tech stack, pillars, "
                "studios, lifelong learning, RAG, MCP, etc.). Returns ranked "
                "hits with similarity 0-1. Use for any 'how does Angelora do X' "
                "or 'what's our position on Y' question."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text search query"},
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 25},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="wiki_get_page",
            description=(
                "Fetch the full markdown body of a wiki page by slug. Use "
                "after wiki_search returned a promising hit, or when you "
                "already know the slug (e.g. 'tech-stack', 'business-model')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Page slug, e.g. 'tech-stack'"},
                },
                "required": ["slug"],
            },
        ),
        Tool(
            name="wiki_list_pages",
            description=(
                "List all platform wiki pages, optionally filtered by "
                "page_type (entity, concept, summary, synthesis, comparison, "
                "track_template). Useful for browsing what's available."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page_type": {
                        "type": "string",
                        "enum": [
                            "entity",
                            "concept",
                            "summary",
                            "synthesis",
                            "comparison",
                            "track_template",
                        ],
                    },
                },
            },
        ),
        Tool(
            name="wiki_recent_changes",
            description=(
                "Show recent wiki changelog entries (creates / updates / "
                "merges / xref rewrites). Useful for 'what changed this week' "
                "queries or auditing."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
            },
        ),
        Tool(
            name="wiki_update_page",
            description=(
                "Update a platform wiki page. Supply at least one of "
                "content_md / title / page_type. When content_md changes, "
                "the page embedding is regenerated automatically (set "
                "re_embed=false to skip — only do that for trivial typo "
                "fixes). Writes a wiki_changelog 'update' row. Used by the "
                "wiki maintainer agent to fix LINT issues (broken xrefs, "
                "stale labels, missing anatomy)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "Page slug to update"},
                    "content_md": {"type": "string", "description": "New markdown body"},
                    "title": {"type": "string", "description": "New human-readable title"},
                    "page_type": {
                        "type": "string",
                        "enum": [
                            "entity",
                            "concept",
                            "summary",
                            "synthesis",
                            "comparison",
                            "track_template",
                        ],
                    },
                    "re_embed": {"type": "boolean", "default": True},
                },
                "required": ["slug"],
            },
        ),
        Tool(
            name="wiki_create_page",
            description=(
                "Create a new platform wiki page (program_id NULL). Embeds "
                "the body and writes a wiki_changelog 'create' row. Use "
                "when LINT reports a broken xref whose target should "
                "actually exist."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "description": "kebab-case slug, must be unique"},
                    "title": {"type": "string"},
                    "content_md": {"type": "string", "description": "Markdown body. Should include ## TL;DR and ## When to consult."},
                    "page_type": {
                        "type": "string",
                        "enum": [
                            "entity",
                            "concept",
                            "summary",
                            "synthesis",
                            "comparison",
                            "track_template",
                        ],
                    },
                    "parent_page_id": {"type": "string", "description": "Optional UUID of parent wiki page"},
                },
                "required": ["slug", "title", "content_md", "page_type"],
            },
        ),
        Tool(
            name="wiki_delete_page",
            description=(
                "Retire (hard-delete) a platform wiki page. Used to resolve "
                "duplicate clusters by keeping the canonical page and "
                "removing the duplicate. The 'reason' field is required for "
                "audit. Writes a wiki_changelog 'retire' row BEFORE the "
                "delete so the audit trail survives the cascade."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "reason": {"type": "string", "description": "Why this page is being retired (e.g. 'duplicate of X')"},
                },
                "required": ["slug"],
            },
        ),
    ]


def _format(name: str, payload: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "wiki_search":
            hits = await wiki_search(arguments["query"], int(arguments.get("limit", 10)))
            return _format(name, {"hits": hits, "count": len(hits)})
        if name == "wiki_get_page":
            page = await wiki_get_page(arguments["slug"])
            return _format(name, page or {"error": f"slug not found: {arguments['slug']}"})
        if name == "wiki_list_pages":
            pages = await wiki_list_pages(arguments.get("page_type"))
            return _format(name, {"pages": pages, "count": len(pages)})
        if name == "wiki_recent_changes":
            changes = await wiki_recent_changes(int(arguments.get("limit", 10)))
            return _format(name, {"changes": changes, "count": len(changes)})
        if name == "wiki_update_page":
            result = await wiki_update_page(
                arguments["slug"],
                content_md=arguments.get("content_md"),
                title=arguments.get("title"),
                page_type=arguments.get("page_type"),
                re_embed=bool(arguments.get("re_embed", True)),
            )
            return _format(name, result)
        if name == "wiki_create_page":
            result = await wiki_create_page(
                slug=arguments["slug"],
                title=arguments["title"],
                content_md=arguments["content_md"],
                page_type=arguments["page_type"],
                parent_page_id=arguments.get("parent_page_id"),
            )
            return _format(name, result)
        if name == "wiki_delete_page":
            result = await wiki_delete_page(
                slug=arguments["slug"],
                reason=arguments.get("reason"),
            )
            return _format(name, result)
        return _format(name, {"error": f"unknown tool: {name}"})
    except httpx.HTTPStatusError as e:
        return _format(name, {
            "error": f"HTTP {e.response.status_code}",
            "body": e.response.text[:500],
        })
    except Exception as e:
        return _format(name, {"error": f"{type(e).__name__}: {e}"})


async def _amain() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
