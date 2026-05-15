# Angela Wiki MCP Server

Surfaces Angelora's living platform wiki (https://angelora.net/wiki, 48+
auto-compiled pages) to any Angela tool over MCP.

## Tools

| Tool | What |
|---|---|
| `wiki_search(query, limit=10)` | Semantic cosine search via match_wiki_pages RPC. Embeds query with gemini-embedding-001 @ 768d so vectors live in the same space as the wiki. |
| `wiki_get_page(slug)` | Fetch the full markdown body for one slug. |
| `wiki_list_pages(page_type?)` | Browse all platform pages, optionally filtered by type (entity / concept / summary / …). |
| `wiki_recent_changes(limit=10)` | Read wiki_changelog audit trail. |

## Auth

- **Supabase REST** — uses Angelora's publishable (anon) key from
  `our_secrets.angelora_supabase_publishable_key`. RLS already permits anon
  read on platform pages and EXECUTE on `match_wiki_pages`.
- **Google embed** — uses `our_secrets.google_ai_studio_api_key` for query
  embeddings. ~$0.0002 per query; free tier covers thousands of queries/day.

## Why Google for query embed (not Ollama)

Per `feedback_embedding_provider_strategy.md`: query model must match corpus
model for cosine to mean anything. Wiki bodies were embedded with
gemini-embedding-001 → queries must use the same model. nomic-embed-text and
gemini-embedding-001 are dimension-compatible (both 768d) but live in
different vector spaces.

## Run locally

```bash
cd mcp_servers/angela-wiki
pip install -e .
python -m angela_wiki.server
```

Or via stdio from a Claude Code MCP config:

```json
{
  "mcpServers": {
    "angela-wiki": {
      "command": "python",
      "args": ["-m", "angela_wiki.server"],
      "cwd": "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/mcp_servers/angela-wiki"
    }
  }
}
```
