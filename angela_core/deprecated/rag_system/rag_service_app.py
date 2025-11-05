#!/usr/bin/env python3
"""
Unified RAG Service - Clean Architecture Implementation

Consolidates all RAG functionality:
- Vector search (semantic similarity)
- Keyword search (BM25-like fulltext)
- Hybrid search (RRF fusion)
- Query expansion
- Result reranking
- Answer generation

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import logging
from typing import List, Dict, Optional, Any
from uuid import UUID
import time
import re

from angela_core.application.services.base_service import BaseService
from angela_core.application.dto.rag_dtos import (
    RAGRequest, RAGResponse, DocumentChunkResult,
    SearchStrategy, QueryExpansion, RerankingResult, SearchMetrics
)
from angela_core.domain import DocumentChunk
from angela_core.domain.interfaces.repositories import (
    IDocumentRepository,
    IEmbeddingRepository
)
from angela_core.shared.exceptions import InvalidInputError, NotFoundError

logger = logging.getLogger(__name__)


class RAGService(BaseService):
    """
    Unified Retrieval-Augmented Generation Service.

    Clean Architecture implementation that consolidates:
    - langchain_rag_service.py (LangChain RAG)
    - hybrid_search_service.py (Vector + Keyword fusion)
    - keyword_search_service.py (BM25-like search)
    - vector_search_service.py (Pure vector search)

    Features:
    - Multiple search strategies (vector, keyword, hybrid)
    - Query expansion for better recall
    - Result reranking with metadata boosting
    - Diversity filtering
    - Optional answer generation
    - Comprehensive metrics
    """

    def __init__(
        self,
        document_repo: IDocumentRepository,
        embedding_repo: IEmbeddingRepository
    ):
        """
        Initialize RAG service.

        Args:
            document_repo: Document repository for chunk access
            embedding_repo: Embedding repository for vector search
        """
        super().__init__()
        self.document_repo = document_repo
        self.embedding_repo = embedding_repo

        logger.info("🧠 Unified RAG Service initialized (Clean Architecture)")

    # ========================================================================
    # MAIN RAG QUERY
    # ========================================================================

    async def query(self, request: RAGRequest) -> RAGResponse:
        """
        Execute RAG query with specified strategy.

        Args:
            request: RAG request with query and configuration

        Returns:
            RAG response with retrieved chunks and optional answer
        """
        start_time = time.time()

        try:
            # Validate request
            if not request.query or not request.query.strip():
                raise InvalidInputError("Query cannot be empty")

            logger.info(f"🔍 RAG Query ({request.search_strategy}): {request.query[:100]}...")

            # Step 1: Query expansion (if enabled)
            enhanced_query = request.query
            if request.use_query_expansion:
                expansion = await self._expand_query(request.query)
                enhanced_query = expansion.enhanced_query
                logger.info(f"✨ Query expanded: '{request.query}' → '{enhanced_query}'")

            # Step 2: Generate embedding
            embedding_start = time.time()
            embedding = await self.embedding_repo.generate_embedding(enhanced_query)
            embedding_time_ms = int((time.time() - embedding_start) * 1000)

            # Step 3: Search documents
            search_start = time.time()
            chunks: List[DocumentChunkResult] = []

            if request.search_strategy == SearchStrategy.VECTOR:
                chunks = await self._vector_search(request, embedding)
            elif request.search_strategy == SearchStrategy.KEYWORD:
                chunks = await self._keyword_search(request)
            else:  # HYBRID
                chunks = await self._hybrid_search(request, embedding)

            search_time_ms = int((time.time() - search_start) * 1000)

            # Step 4: Reranking (if enabled)
            rerank_time_ms = None
            if request.use_reranking and len(chunks) > 1:
                rerank_start = time.time()
                reranking_result = await self._rerank_results(chunks)
                chunks = reranking_result.chunks
                rerank_time_ms = int((time.time() - rerank_start) * 1000)
                logger.info(f"♻️ Reranked {len(chunks)} chunks (removed {reranking_result.removed_duplicates} duplicates)")

            # Step 5: Calculate scores
            avg_similarity = sum(c.final_score for c in chunks) / len(chunks) if chunks else 0.0
            max_similarity = max((c.final_score for c in chunks), default=0.0)
            confidence_score = self._calculate_confidence(chunks)

            # Step 6: Generate answer (if requested)
            answer = None
            answer_metadata = {}
            if request.generate_answer and chunks:
                # TODO: Implement answer generation with LLM
                # This would integrate with OllamaService or AnthropicService
                pass

            total_time_ms = int((time.time() - start_time) * 1000)

            # Build response
            response = RAGResponse(
                query=request.query,
                enhanced_query=enhanced_query if request.use_query_expansion else None,
                search_strategy=request.search_strategy,
                chunks=chunks[:request.top_k],  # Limit to requested top_k
                total_chunks_found=len(chunks),
                avg_similarity=round(avg_similarity, 3),
                max_similarity=round(max_similarity, 3),
                confidence_score=round(confidence_score, 3),
                answer=answer,
                answer_metadata=answer_metadata,
                search_time_ms=search_time_ms,
                total_time_ms=total_time_ms,
                success=True
            )

            logger.info(f"✅ RAG completed: {len(chunks)} chunks, confidence={confidence_score:.2f}, {total_time_ms}ms")
            return response

        except Exception as e:
            logger.error(f"❌ RAG query failed: {e}")
            return RAGResponse(
                query=request.query,
                search_strategy=request.search_strategy,
                success=False,
                error_message=str(e)
            )

    # ========================================================================
    # SEARCH STRATEGIES
    # ========================================================================

    async def _vector_search(
        self,
        request: RAGRequest,
        embedding: List[float]
    ) -> List[DocumentChunkResult]:
        """
        Pure vector similarity search.

        Args:
            request: RAG request
            embedding: Query embedding

        Returns:
            List of document chunk results
        """
        # Build filters
        filters = {}
        if request.document_id:
            filters['document_id'] = request.document_id
        if request.category:
            filters['category'] = request.category

        # Search using embedding repository
        results = await self.embedding_repo.search_documents(
            embedding=embedding,
            top_k=request.top_k * 2,  # Fetch more for reranking
            filters=filters if filters else None
        )

        # Convert to DocumentChunkResult
        chunks = []
        for chunk_entity, score in results:
            if score >= request.similarity_threshold:
                chunks.append(self._entity_to_result(chunk_entity, score))

        return chunks

    async def _keyword_search(
        self,
        request: RAGRequest
    ) -> List[DocumentChunkResult]:
        """
        Pure keyword/fulltext search.

        Args:
            request: RAG request

        Returns:
            List of document chunk results
        """
        # TODO: Implement keyword search using PostgreSQL fulltext search
        # This would use tsvector and tsquery for BM25-like ranking
        # For now, return empty list as placeholder
        logger.warning("⚠️ Keyword search not yet implemented - using vector search fallback")

        # Fallback to vector search
        embedding = await self.embedding_repo.generate_embedding(request.query)
        return await self._vector_search(request, embedding)

    async def _hybrid_search(
        self,
        request: RAGRequest,
        embedding: List[float]
    ) -> List[DocumentChunkResult]:
        """
        Hybrid search combining vector and keyword with RRF fusion.

        Reciprocal Rank Fusion (RRF):
        RRF_score = sum(1 / (rank + k)) where k=60 (default)

        Args:
            request: RAG request
            embedding: Query embedding

        Returns:
            List of document chunk results (fused and sorted)
        """
        # Get vector search results
        vector_chunks = await self._vector_search(request, embedding)

        # Get keyword search results
        keyword_chunks = await self._keyword_search(request)

        # Apply RRF fusion
        fused_chunks = self._rrf_fusion(
            vector_chunks,
            keyword_chunks,
            k=60  # RRF constant
        )

        return fused_chunks[:request.top_k * 2]  # Return top results

    def _rrf_fusion(
        self,
        vector_chunks: List[DocumentChunkResult],
        keyword_chunks: List[DocumentChunkResult],
        k: int = 60
    ) -> List[DocumentChunkResult]:
        """
        Reciprocal Rank Fusion algorithm.

        Combines rankings from multiple search strategies.

        Args:
            vector_chunks: Results from vector search
            keyword_chunks: Results from keyword search
            k: RRF constant (default 60)

        Returns:
            Fused and re-ranked results
        """
        # Build RRF scores
        rrf_scores: Dict[UUID, float] = {}
        chunk_map: Dict[UUID, DocumentChunkResult] = {}

        # Add vector search rankings
        for rank, chunk in enumerate(vector_chunks, start=1):
            chunk_id = chunk.chunk_id
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (rank + k))
            chunk_map[chunk_id] = chunk

        # Add keyword search rankings
        for rank, chunk in enumerate(keyword_chunks, start=1):
            chunk_id = chunk.chunk_id
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (rank + k))
            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = chunk

        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Build result list with updated final_score
        fused_chunks = []
        for chunk_id in sorted_ids:
            chunk = chunk_map[chunk_id]
            chunk.final_score = rrf_scores[chunk_id]
            fused_chunks.append(chunk)

        return fused_chunks

    # ========================================================================
    # QUERY ENHANCEMENT
    # ========================================================================

    async def _expand_query(self, query: str) -> QueryExpansion:
        """
        Expand query with synonyms and related terms.

        Simple implementation - can be enhanced with:
        - WordNet/Thai dictionary lookups
        - Embedding-based similar terms
        - Query logs analysis

        Args:
            query: Original query

        Returns:
            Query expansion result
        """
        # Simple expansion: add variations
        original = query.strip()
        terms = original.lower().split()

        # Common Thai/English synonyms (very basic)
        synonyms_map = {
            'how': ['วิธี', 'อย่างไร'],
            'what': ['อะไร', 'คืออะไร'],
            'where': ['ที่ไหน', 'ตรงไหน'],
            'when': ['เมื่อไหร่', 'เวลาไหน'],
            'why': ['ทำไม', 'เพราะอะไร'],
        }

        added_terms = []
        for term in terms:
            if term in synonyms_map:
                added_terms.extend(synonyms_map[term])

        # Build enhanced query
        if added_terms:
            enhanced = f"{original} {' '.join(added_terms)}"
        else:
            enhanced = original

        return QueryExpansion(
            original_query=original,
            enhanced_query=enhanced,
            added_terms=added_terms
        )

    # ========================================================================
    # RERANKING
    # ========================================================================

    async def _rerank_results(
        self,
        chunks: List[DocumentChunkResult]
    ) -> RerankingResult:
        """
        Rerank results with metadata boosting and diversity filtering.

        Boosting factors:
        - Recency: Newer documents rank higher
        - Importance: Manually marked important chunks
        - Category match: Specific categories get boost

        Args:
            chunks: Initial search results

        Returns:
            Reranked results
        """
        if not chunks:
            return RerankingResult(chunks=[], reranking_method="none")

        reranked = []
        seen_texts = set()
        removed_count = 0

        for chunk in chunks:
            # Diversity filtering: remove near-duplicates
            chunk_text_lower = chunk.chunk_text.lower()[:200]  # First 200 chars

            # Check similarity with seen chunks
            is_duplicate = False
            for seen_text in seen_texts:
                similarity = self._text_similarity(chunk_text_lower, seen_text)
                if similarity > 0.85:  # 85% similar
                    is_duplicate = True
                    removed_count += 1
                    break

            if not is_duplicate:
                # Calculate rerank score with boosting
                base_score = chunk.final_score
                boost = 1.0

                # Recency boost (if metadata available)
                if chunk.created_at:
                    days_old = (time.time() - chunk.created_at.timestamp()) / 86400
                    if days_old < 30:
                        boost += 0.1  # Recent boost
                    elif days_old > 365:
                        boost -= 0.1  # Penalty for old docs

                # Importance boost (from chunk_metadata)
                if chunk.chunk_metadata.get('importance_level', 0) >= 8:
                    boost += 0.15

                # Category boost (if specific categories prioritized)
                # This could be customized based on query type

                chunk.rerank_score = base_score * boost
                chunk.final_score = chunk.rerank_score

                reranked.append(chunk)
                seen_texts.add(chunk_text_lower)

        # Sort by final score
        reranked.sort(key=lambda x: x.final_score, reverse=True)

        return RerankingResult(
            chunks=reranked,
            reranking_method="metadata_boost_diversity",
            boost_factors={"recency": 0.1, "importance": 0.15},
            diversity_threshold=0.85,
            removed_duplicates=removed_count
        )

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity (Jaccard).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score 0.0-1.0
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _entity_to_result(
        self,
        chunk: DocumentChunk,
        score: float
    ) -> DocumentChunkResult:
        """
        Convert DocumentChunk entity to DocumentChunkResult DTO.

        Args:
            chunk: Document chunk entity
            score: Similarity/relevance score

        Returns:
            Document chunk result DTO
        """
        return DocumentChunkResult(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            chunk_text=chunk.chunk_text,
            chunk_index=chunk.chunk_index,
            document_title=None,  # TODO: Fetch from document if needed
            document_category=None,
            chunk_metadata={
                'importance_level': chunk.importance_level,
                'token_count': chunk.token_count
            },
            similarity_score=round(score, 3),
            final_score=round(score, 3),
            created_at=chunk.created_at
        )

    def _calculate_confidence(
        self,
        chunks: List[DocumentChunkResult]
    ) -> float:
        """
        Calculate overall confidence in results.

        Factors:
        - Number of results
        - Average similarity score
        - Score distribution

        Args:
            chunks: Retrieved chunks

        Returns:
            Confidence score 0.0-1.0
        """
        if not chunks:
            return 0.0

        # Factor 1: Result count (more is better, up to a point)
        count_score = min(len(chunks) / 5.0, 1.0)  # Optimal: 5+ results

        # Factor 2: Average similarity
        avg_score = sum(c.final_score for c in chunks) / len(chunks)

        # Factor 3: Top result quality
        top_score = chunks[0].final_score if chunks else 0.0

        # Weighted average
        confidence = (
            count_score * 0.2 +
            avg_score * 0.4 +
            top_score * 0.4
        )

        return min(confidence, 1.0)
