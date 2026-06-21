---
name: rag
description: Ground answers in Angela's domain RAG corpora (rag_* on Supabase, granite-embedding 768d) before answering. Use whenever David asks a substantive question in quant finance, AI/ML, the Bible, wine, or photography — or says "ค้น RAG", "หาในเอกสาร", "rag", "อ้างอิงจากตำรา". Retrieval-augmented: query the corpus, then answer FROM the retrieved chunks with citations, not from memory.
---

# /rag — Retrieve from Angela's Domain Knowledge Bases

Angela owns ~82k embedded chunks across 5 expert corpora. Instead of answering
domain questions from training memory (which drifts and hallucinates page
numbers), **retrieve real source material first, then synthesize an answer
grounded in it.** This is the read-path that makes น้อง actually *use* the
books she has, not just remember owning them.

## Run

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 angela_core/scripts/rag_search.py $ARGUMENTS
```

- **Default to `auto`** when the right corpus isn't obvious — it embeds once,
  fans out across all 5 tables, and merges the global top-k by similarity:
  ```bash
  python3 angela_core/scripts/rag_search.py auto "how is XVA computed?" -k 6
  ```
- Name a domain when you're sure (slightly tighter results):
  `quant` · `ai` · `bible` · `wine` · `photo`
- `-k N` chunks (default 5) · `--min 0.x` similarity floor · `--full` full text
  · `--json` machine-readable.

## Domains (route by topic)

| Domain | Table | ~chunks | Covers |
|---|---|---|---|
| `quant` | rag_quant | 36.8k | Wilmott · Hull · CQF 2025 · XVA · fixed income · algo trading |
| `ai` | rag_ai | 22.2k | Géron · Raschka · AI Engineering · LLM/NLP handbooks |
| `bible` | rag_bible | 16.2k | KJV + Thai scripture |
| `wine` | rag_wine | 4.1k | 1001 Wines · David's wine prefs · curated 2026 |
| `photo` | rag_photography | 2.7k | Fuji X-E5 manual · Photography Masterclass |

## How to use the results

1. **Run retrieval first** (prefer `auto`) for any in-domain question.
2. **Answer FROM the chunks** — quote/paraphrase the retrieved text; do not
   override it with training-memory claims. If chunks conflict with memory,
   the corpus wins (it's the curated source of truth).
3. **Cite** each claim: `source` + `source_ref` (page) + the `«domain»` tag,
   e.g. *(options_futures_and_other_derivatives, p221)*.
4. **Honesty on misses** — if top similarity is low (≲0.55) or results are
   off-topic, say the corpus doesn't cover it rather than fabricating. Don't
   silently fall back to memory and present it as sourced.
5. Bump `-k` (8–12) for synthesis/compare questions; keep low for lookups.

## When to invoke
- **Proactively**, before answering substantive questions in any of the 5
  domains — don't wait for David to ask for a search.
- When David says: "ค้น RAG", "หาในเอกสาร/ตำรา", "อ้างอิง", "rag", "rag auto".
- Requires local **Ollama** running `granite-embedding:278m` (M3/M4). If Ollama
  is down, say so — never substitute a different embedding model (nomic vectors
  are near-orthogonal to this granite corpus and will return garbage).
- Read-only. Safe anytime. This machine does **not** embed new documents into
  the corpus — retrieval only.
