#!/usr/bin/env python3
"""
Hybrid Search Service - Combines Vector + Keyword Search
Uses Reciprocal Rank Fusion (RRF) for result merging

RRF Algorithm:
- Combines rankings from multiple retrieval systems
- score = sum(1 / (k + rank)) for each system
- k = 60 (standard constant from research)
- Robust and works well in practice

⚠️ DEPRECATION WARNING:
This service is deprecated. Use angela_core.application.services.rag_service.RAGService instead.
"""

import warnings
import asyncpg

warnings.warn(
    "hybrid_search_service is deprecated. Use RAGService instead.",
    DeprecationWarning,
    stacklevel=2
)
import logging
from typing import List, Dict, Optional, Literal
from uuid import UUID

from angela_core.services.vector_search_service import VectorSearchService
from angela_core.services.keyword_search_service import KeywordSearchService
from angela_core.embedding_service import embedding

logger = logging.getLogger(__name__)


class HybridSearchService:
    """Hybrid search combining vector similarity and keyword matching"""

    # RRF constant (from research papers)
    RRF_K = 60

    @staticmethod
    def reciprocal_rank_fusion(
        rankings: List[List[Dict]],
        k: int = RRF_K
    ) -> List[Dict]:
        """
        Merge multiple rankings using Reciprocal Rank Fusion

        Args:
            rankings: List of ranked result lists (each with chunk_id)
            k: RRF constant (default: 60)

        Returns:
            Merged and re-ranked results
        """
        # Track RRF scores for each chunk
        chunk_scores = {}
        chunk_data = {}

        # Process each ranking
        for ranking in rankings:
            for rank, result in enumerate(ranking, start=1):
                chunk_id = result.get('chunk_id')

                if not chunk_id:
                    continue

                # RRF formula: 1 / (k + rank)
                rrf_score = 1.0 / (k + rank)

                # Accumulate RRF scores
                if chunk_id in chunk_scores:
                    chunk_scores[chunk_id] += rrf_score
                else:
                    chunk_scores[chunk_id] = rrf_score
                    # Store full chunk data (from first appearance)
                    chunk_data[chunk_id] = result

        # Sort by RRF score (descending)
        sorted_chunks = sorted(
            chunk_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Build final ranked list
        merged_results = []
        for chunk_id, rrf_score in sorted_chunks:
            chunk = chunk_data[chunk_id].copy()
            chunk['rrf_score'] = rrf_score
            chunk['combined_score'] = rrf_score  # Alias for compatibility
            merged_results.append(chunk)

        return merged_results

    @staticmethod
    async def hybrid_search(
        db: asyncpg.Connection,
        query: str,
        limit: int = 10,
        vector_weight: float = 0.5,
        keyword_weight: float = 0.5,
        vector_threshold: float = 0.7,
        keyword_threshold: float = 0.01,
        document_id: Optional[UUID] = None
    ) -> List[Dict]:
        """
        Perform hybrid search combining vector and keyword search

        Args:
            db: Database connection
            query: Search query
            limit: Number of results to return
            vector_weight: Weight for vector search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            vector_threshold: Minimum similarity score for vector search
            keyword_threshold: Minimum ts_rank for keyword search
            document_id: Optional document filter

        Returns:
            Hybrid search results with RRF scores
        """
        try:
            logger.info(f"🔄 Hybrid search: '{query}' (v:{vector_weight}, k:{keyword_weight})")

            # Fetch more results from each system for better fusion
            fetch_limit = limit * 3

            # 1. Vector Search
            query_embedding = await embedding.generate_embedding(query)
            vector_results = await VectorSearchService.similarity_search(
                db=db,
                query_embedding=query_embedding,
                limit=fetch_limit,
                threshold=vector_threshold,
                document_id=document_id,
                similarity_method='cosine'
            )

            logger.info(f"  Vector: {len(vector_results)} results")

            # 2. Keyword Search
            keyword_results = await KeywordSearchService.keyword_search(
                db=db,
                query=query,
                limit=fetch_limit,
                threshold=keyword_threshold,
                document_id=document_id
            )

            logger.info(f"  Keyword: {len(keyword_results)} results")

            # 3. Reciprocal Rank Fusion
            if not vector_results and not keyword_results:
                logger.warning("  No results from either search method")
                return []

            # Apply weights by duplicating rankings
            # Higher weight = more influence in fusion
            rankings = []

            if vector_weight > 0 and vector_results:
                # Add vector ranking (possibly multiple times based on weight)
                vector_influence = max(1, round(vector_weight * 10))
                for _ in range(vector_influence):
                    rankings.append(vector_results)

            if keyword_weight > 0 and keyword_results:
                # Add keyword ranking
                keyword_influence = max(1, round(keyword_weight * 10))
                for _ in range(keyword_influence):
                    rankings.append(keyword_results)

            # Fuse results
            merged_results = HybridSearchService.reciprocal_rank_fusion(rankings)

            # Keep top results
            final_results = merged_results[:limit]

            logger.info(f"  ✅ Hybrid: {len(final_results)} merged results")

            # Add original scores to final results
            chunk_id_to_scores = {}

            for result in vector_results:
                chunk_id = result['chunk_id']
                chunk_id_to_scores[chunk_id] = {
                    'similarity_score': result.get('similarity_score', 0.0),
                    'keyword_score': 0.0
                }

            for result in keyword_results:
                chunk_id = result['chunk_id']
                if chunk_id in chunk_id_to_scores:
                    chunk_id_to_scores[chunk_id]['keyword_score'] = result.get('keyword_score', 0.0)
                else:
                    chunk_id_to_scores[chunk_id] = {
                        'similarity_score': 0.0,
                        'keyword_score': result.get('keyword_score', 0.0)
                    }

            # Augment final results with individual scores
            for result in final_results:
                chunk_id = result['chunk_id']
                if chunk_id in chunk_id_to_scores:
                    result.update(chunk_id_to_scores[chunk_id])

            return final_results

        except Exception as e:
            logger.error(f"❌ Hybrid search error: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    async def auto_search(
        db: asyncpg.Connection,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        search_mode: Literal['hybrid', 'vector', 'keyword'] = 'hybrid',
        document_id: Optional[UUID] = None
    ) -> List[Dict]:
        """
        Automatic search with mode selection

        Args:
            db: Database connection
            query: Search query
            limit: Results limit
            threshold: Similarity/ranking threshold
            search_mode: 'hybrid', 'vector', or 'keyword'
            document_id: Optional document filter

        Returns:
            Search results based on selected mode
        """
        try:
            if search_mode == 'vector':
                # Vector only
                query_embedding = await embedding.generate_embedding(query)
                return await VectorSearchService.similarity_search(
                    db=db,
                    query_embedding=query_embedding,
                    limit=limit,
                    threshold=threshold,
                    document_id=document_id
                )

            elif search_mode == 'keyword':
                # Keyword only
                return await KeywordSearchService.keyword_search(
                    db=db,
                    query=query,
                    limit=limit,
                    threshold=threshold,
                    document_id=document_id
                )

            else:
                # Hybrid (default)
                return await HybridSearchService.hybrid_search(
                    db=db,
                    query=query,
                    limit=limit,
                    vector_weight=0.5,
                    keyword_weight=0.5,
                    vector_threshold=threshold,
                    keyword_threshold=0.01,
                    document_id=document_id
                )

        except Exception as e:
            logger.error(f"❌ Auto search error: {e}")
            return []
