#!/usr/bin/env python3
"""
Angela Vector Search Service
Adapted from DavidAiReactChat for Angela's schema

Supports multiple similarity methods:
- cosine (default, best for semantic comparison)
- euclidean (L2 distance)
- dot_product (fastest)

⚠️ DEPRECATION WARNING:
This service is deprecated. Use angela_core.application.services.rag_service.RAGService instead.
"""

import warnings
import asyncpg

warnings.warn(
    "vector_search_service is deprecated. Use RAGService instead.",
    DeprecationWarning,
    stacklevel=2
)
from typing import List, Optional, Literal, Dict
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Vector search service for Angela's document chunks"""

    @staticmethod
    async def similarity_search(
        db: asyncpg.Connection,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        document_id: Optional[UUID] = None,
        similarity_method: Literal['cosine', 'euclidean', 'dot_product'] = 'cosine'
    ) -> List[Dict]:
        """
        Perform similarity search on document_chunks using pgvector

        Args:
            db: Database connection
            query_embedding: Query embedding vector (768 dims)
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            document_id: Optional filter by specific document
            similarity_method: 'cosine', 'euclidean', or 'dot_product'

        Returns:
            List of matching chunks with similarity scores
        """
        try:
            # Choose the appropriate distance operator
            if similarity_method == 'cosine':
                # Cosine distance (pgvector <=>)
                distance_op = '<=>'
                similarity_expr = f'1 - (embedding {distance_op} $1::vector)'
                order_by = f'embedding {distance_op} $1::vector'
            elif similarity_method == 'euclidean':
                # L2 distance (pgvector <->)
                distance_op = '<->'
                distance_expr = f'embedding {distance_op} $1::vector'
                similarity_expr = f'1 / (1 + ({distance_expr}))'
                order_by = distance_expr
            elif similarity_method == 'dot_product':
                # Negative inner product (pgvector <#>)
                distance_op = '<#>'
                similarity_expr = f'-(embedding {distance_op} $1::vector)'
                order_by = f'embedding {distance_op} $1::vector'
            else:
                # Default to cosine
                distance_op = '<=>'
                similarity_expr = f'1 - (embedding {distance_op} $1::vector)'
                order_by = f'embedding {distance_op} $1::vector'

            # Build query
            query_parts = []
            params = [str(query_embedding)]  # Convert to string for PostgreSQL vector format
            param_count = 1

            # Base SELECT
            query_sql = f"""
                SELECT
                    chunk_id,
                    document_id,
                    chunk_index,
                    content,
                    page_number,
                    section_title,
                    importance_score,
                    thai_word_count,
                    english_word_count,
                    ({similarity_expr}) as similarity_score
                FROM document_chunks
                WHERE embedding IS NOT NULL
            """

            # Filter by document if specified
            if document_id:
                param_count += 1
                query_sql += f" AND document_id = ${param_count}::uuid"
                params.append(str(document_id))

            # Filter by threshold
            query_sql += f" AND ({similarity_expr}) >= ${param_count + 1}"
            params.append(threshold)
            param_count += 1

            # Order and limit
            query_sql += f" ORDER BY {order_by} LIMIT ${param_count + 1}"
            params.append(limit)

            # Execute query
            rows = await db.fetch(query_sql, *params)

            # Format results
            results = []
            for row in rows:
                # Handle NaN or None similarity scores
                similarity = row['similarity_score']
                if similarity is None or (isinstance(similarity, float) and similarity != similarity):
                    similarity = 0.0

                results.append({
                    'chunk_id': str(row['chunk_id']),
                    'document_id': str(row['document_id']),
                    'chunk_index': row['chunk_index'],
                    'content': row['content'],
                    'page_number': row['page_number'],
                    'section_title': row['section_title'],
                    'importance_score': row['importance_score'],
                    'thai_word_count': row['thai_word_count'],
                    'english_word_count': row['english_word_count'],
                    'similarity_score': float(similarity)
                })

            logger.info(f"Vector search found {len(results)} results (method: {similarity_method})")
            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    @staticmethod
    async def search_by_document(
        db: asyncpg.Connection,
        query_embedding: List[float],
        document_id: UUID,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search within a specific document

        Convenience method for document-specific search
        """
        return await VectorSearchService.similarity_search(
            db=db,
            query_embedding=query_embedding,
            limit=limit,
            threshold=0.5,  # Lower threshold for within-document search
            document_id=document_id,
            similarity_method='cosine'
        )
