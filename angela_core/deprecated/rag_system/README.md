# RAG System - Deprecated

**Deprecated Date:** November 3, 2025
**Reason:** Not actively used by David

## What was RAG?

RAG (Retrieval-Augmented Generation) was a system for:
- Searching documents semantically (vector search)
- Hybrid search (keyword + vector)
- Re-ranking results
- LangChain integration

## Files Moved Here:

### Services:
1. `rag_service.py` - Main RAG service
2. `rag_service_app.py` - Application layer RAG service
3. `langchain_rag_service.py` - LangChain integration
4. `vector_search_service.py` - Vector similarity search
5. `hybrid_search_service.py` - Keyword + vector hybrid
6. `keyword_search_service.py` - Full-text search
7. `reranking_service.py` - Result re-ranking

### DTOs:
- `rag_dtos.py` - Data transfer objects

### Tests:
- `tests/deprecated/test_rag*.py` - 5 test files

## Why Deprecated?

David's feedback (Nov 3, 2025):
- "RAG ก็ไม่ได้ใช้ค่ะ" - RAG not being used
- Focus on simpler architecture
- Documents feature in Admin Web is sufficient

## Can It Be Restored?

Yes! All files preserved here. If David wants RAG features:
1. Move files back to `angela_core/services/`
2. Update imports
3. May need to update for current architecture

## What Replaced It?

- **Document viewing** - Admin Web Documents page
- **Simple search** - Database queries
- **Embeddings** - Still available via embedding_service.py (if needed)

---

Made with 💜 by น้อง Angela
