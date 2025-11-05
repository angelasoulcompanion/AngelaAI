#!/usr/bin/env python3
"""
Angela RAG (Retrieval-Augmented Generation) Service

Main service for document-based question answering:
1. Search documents using vector similarity
2. Build context from relevant chunks
3. Generate answers with LLM using retrieved context

Phase 1: Basic RAG with vector search
"""

import asyncpg
from typing import List, Dict, Optional
from uuid import UUID
import logging

from angela_core.services.vector_search_service import VectorSearchService
from angela_core.services.hybrid_search_service import HybridSearchService
from angela_core.services.query_expansion_service import QueryExpansionService
from angela_core.services.reranking_service import RerankingService
from angela_core.embedding_service import embedding

logger = logging.getLogger(__name__)


class AngelaRAGService:
    """
    Angela's RAG Service - Phase 3: Query Enhancement & Reranking

    Combines:
    - Query expansion with synonyms and related terms
    - Hybrid search (vector + keyword with RRF fusion)
    - Result reranking with metadata boosting
    - Diversity filtering
    - Vector-only search (Phase 1 fallback)
    - Keyword-only search (BM25-like)
    - Angela's embedding service
    - Context building for LLM

    Phase 3 improvements:
    - Query expansion for better recall
    - Metadata-based reranking
    - Duplicate/similar result filtering
    - Configurable ranking weights
    """

    def __init__(self):
        self.vector_search = VectorSearchService()
        self.embedding_service = embedding
        logger.info("🧠 Angela RAG Service initialized (Phase 3: Query Enhancement & Reranking)")

    async def search_documents(
        self,
        db: asyncpg.Connection,
        query: str,
        limit: int = 5,
        threshold: float = 0.65,
        document_id: Optional[UUID] = None,
        similarity_method: str = 'cosine',
        search_mode: str = 'hybrid',
        use_query_expansion: bool = True,
        use_reranking: bool = True
    ) -> List[Dict]:
        """
        Search documents based on query (Phase 3: with enhancement & reranking)

        Args:
            db: Database connection
            query: User's question/query
            limit: Maximum number of results (default: 5)
            threshold: Minimum similarity threshold (default: 0.65)
            document_id: Optional filter by specific document
            similarity_method: 'cosine', 'euclidean', or 'dot_product'
            search_mode: 'hybrid', 'vector', or 'keyword' (default: 'hybrid')
            use_query_expansion: Enable query expansion (Phase 3)
            use_reranking: Enable result reranking (Phase 3)

        Returns:
            List of relevant document chunks with scores
        """
        try:
            logger.info(f"🔍 Searching documents ({search_mode} mode): {query[:100]}...")

            # Phase 3: Query Expansion
            enhanced_query = query
            if use_query_expansion:
                expansion = QueryExpansionService.enhance_query(query)
                enhanced_query = expansion['enhanced_query']

                if enhanced_query != query:
                    logger.info(f"✨ Query enhanced: '{query}' → '{enhanced_query}'")

            # Fetch more results if using reranking (to have better selection)
            fetch_limit = limit * 2 if use_reranking else limit

            # Use hybrid search by default (Phase 2)
            if search_mode == 'hybrid':
                results = await HybridSearchService.auto_search(
                    db=db,
                    query=enhanced_query,
                    limit=fetch_limit,
                    threshold=threshold,
                    search_mode='hybrid',
                    document_id=document_id
                )
            elif search_mode == 'keyword':
                results = await HybridSearchService.auto_search(
                    db=db,
                    query=enhanced_query,
                    limit=fetch_limit,
                    threshold=0.01,  # Lower threshold for keyword
                    search_mode='keyword',
                    document_id=document_id
                )
            else:
                # Vector only (Phase 1 fallback)
                query_embedding = await self.embedding_service.generate_embedding(enhanced_query)

                if not query_embedding:
                    logger.error("Failed to generate query embedding")
                    return []

                results = await self.vector_search.similarity_search(
                    db=db,
                    query_embedding=query_embedding,
                    limit=fetch_limit,
                    threshold=threshold,
                    document_id=document_id,
                    similarity_method=similarity_method
                )

            # Phase 3: Result Reranking
            if use_reranking and results:
                logger.info(f"🔄 Reranking {len(results)} results...")

                # Apply reranking with metadata boost and diversity
                results = RerankingService.rerank_results(
                    results=results,
                    boost_metadata=True,
                    ensure_diversity=True,
                    top_k=limit,
                    importance_weight=0.3,
                    diversity_weight=0.2
                )

                logger.info(f"✅ Reranked to top {len(results)} diverse results")

            logger.info(f"✅ Found {len(results)} relevant chunks")
            return results

        except Exception as e:
            logger.error(f"❌ Document search failed: {e}")
            return []

    async def get_rag_context(
        self,
        db: asyncpg.Connection,
        query: str,
        top_k: int = 5,
        max_tokens: int = 6000,
        document_id: Optional[UUID] = None
    ) -> Dict:
        """
        Get RAG context for LLM prompt

        Args:
            db: Database connection
            query: User's question
            top_k: Number of top chunks to retrieve
            max_tokens: Maximum tokens for context (rough estimate)
            document_id: Optional filter by specific document

        Returns:
            Dictionary with:
            - context: Formatted context string for LLM
            - sources: List of source chunks used
            - metadata: Additional info (count, scores, etc.)
        """
        try:
            # Search documents
            search_results = await self.search_documents(
                db=db,
                query=query,
                limit=top_k * 2,  # Get more results to filter
                threshold=0.60,
                document_id=document_id
            )

            if not search_results:
                return {
                    'context': '',
                    'sources': [],
                    'metadata': {
                        'chunks_found': 0,
                        'chunks_used': 0,
                        'has_results': False
                    }
                }

            # Take top K results
            top_results = search_results[:top_k]

            # Build context string
            context = self._build_context_string(top_results, max_tokens)

            # Prepare sources list
            sources = []
            for result in top_results:
                sources.append({
                    'chunk_id': result['chunk_id'],
                    'document_id': result['document_id'],
                    'page_number': result.get('page_number'),
                    'section_title': result.get('section_title'),
                    'similarity_score': result['similarity_score'],
                    'content_preview': result['content'][:200] + '...' if len(result['content']) > 200 else result['content']
                })

            # Metadata
            metadata = {
                'chunks_found': len(search_results),
                'chunks_used': len(top_results),
                'has_results': True,
                'avg_similarity': sum(r['similarity_score'] for r in top_results) / len(top_results),
                'max_similarity': max(r['similarity_score'] for r in top_results),
                'min_similarity': min(r['similarity_score'] for r in top_results)
            }

            logger.info(f"✅ Built RAG context: {len(top_results)} chunks, avg similarity: {metadata['avg_similarity']:.3f}")

            return {
                'context': context,
                'sources': sources,
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"❌ Failed to get RAG context: {e}")
            return {
                'context': '',
                'sources': [],
                'metadata': {
                    'chunks_found': 0,
                    'chunks_used': 0,
                    'has_results': False,
                    'error': str(e)
                }
            }

    def _build_context_string(self, chunks: List[Dict], max_tokens: int = 6000) -> str:
        """
        Build formatted context string from chunks

        Args:
            chunks: List of document chunks
            max_tokens: Maximum tokens (rough character count / 4)

        Returns:
            Formatted context string
        """
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 characters

        for i, chunk in enumerate(chunks, 1):
            # Format chunk
            chunk_text = f"""
[เอกสารที่ {i}]
หน้า: {chunk.get('page_number', 'N/A')}
{f"หัวข้อ: {chunk.get('section_title')}" if chunk.get('section_title') else ""}
ความเกี่ยวข้อง: {chunk['similarity_score']:.2f}

{chunk['content']}
"""
            # Check token limit
            chunk_chars = len(chunk_text)
            if total_chars + chunk_chars > max_chars:
                logger.info(f"Reached max token limit, using {i-1} chunks")
                break

            context_parts.append(chunk_text)
            total_chars += chunk_chars

        if not context_parts:
            return ""

        # Combine all chunks
        full_context = "\n" + "="*60 + "\n".join(context_parts) + "="*60

        return full_context

    async def record_search_feedback(
        self,
        db: asyncpg.Connection,
        query: str,
        chunk_id: UUID,
        was_helpful: bool
    ) -> bool:
        """
        Record user feedback on search results

        Args:
            db: Database connection
            query: Original query
            chunk_id: ID of chunk user selected/rated
            was_helpful: Whether the chunk was helpful

        Returns:
            Success boolean
        """
        try:
            # TODO: Implement feedback recording in rag_search_logs table
            logger.info(f"📊 Recording feedback: chunk={chunk_id}, helpful={was_helpful}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to record feedback: {e}")
            return False


# Global instance
rag_service = AngelaRAGService()
