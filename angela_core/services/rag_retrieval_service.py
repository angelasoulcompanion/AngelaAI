"""
RAG Retrieval Service
Handles semantic search, hybrid search, and context retrieval for Angela
"""

import asyncio
import asyncpg
import httpx
from typing import List, Dict, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import json
import logging
from collections import Counter

from .thai_text_processor import ThaiTextProcessor

# Import centralized embedding service
from angela_core.embedding_service import embedding as embedding_service

logger = logging.getLogger(__name__)


class RAGRetrievalService:
    """ระบบ RAG สำหรับค้นหาและดึง context จากเอกสาร"""

    def __init__(self, db_connection, ollama_base_url: str = "http://localhost:11434"):
        """Initialize RAG retrieval service"""
        self.db = db_connection
        self.ollama_url = ollama_base_url
        self.thai_processor = ThaiTextProcessor()
        self.embedding_model = "nomic-embed-text"

        logger.info("✅ RAGRetrievalService initialized")

    async def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""

        try:
            # Normalize text
            embedding_text = await self.thai_processor.normalize_for_embedding(text)

            # Use centralized embedding service
            return await embedding_service.generate_embedding(embedding_text)

        except Exception as e:
            logger.error(f"❌ Embedding error: {e}")
            return None

    async def vector_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        threshold: float = 0.5
    ) -> List[Dict]:
        """Vector similarity search"""

        try:
            # Using PostgreSQL pgvector for cosine similarity search
            search_query = """
                SELECT
                    chunk_id, document_id, content,
                    1 - (embedding <=> $1::vector) as similarity_score,
                    page_number, section_title, importance_score
                FROM document_chunks
                WHERE 1 - (embedding <=> $1::vector) > $2
                ORDER BY similarity_score DESC
                LIMIT $3
            """

            # Convert embedding list to string format for pgvector
            embedding_str = str(query_embedding) if isinstance(query_embedding, list) else query_embedding

            results = await self.db.fetch(
                search_query,
                embedding_str,
                threshold,
                top_k
            )

            logger.info(f"✅ Vector search found {len(results)} results")

            return [dict(r) for r in results]

        except Exception as e:
            logger.error(f"❌ Vector search error: {e}")
            return []

    async def keyword_search(
        self,
        keywords: List[str],
        top_k: int = 10
    ) -> List[Dict]:
        """Keyword-based search using Thai text search"""

        try:
            # Build search query with multiple keywords
            if not keywords:
                return []

            # Use PostgreSQL full-text search
            search_query = """
                SELECT
                    chunk_id, document_id, content,
                    COUNT(*) as keyword_matches,
                    ts_rank(to_tsvector('simple', content_normalized),
                            plainto_tsquery('simple', $1::text)) as rank
                FROM document_chunks
                WHERE to_tsvector('simple', content_normalized) @@
                      plainto_tsquery('simple', $1::text)
                GROUP BY chunk_id, document_id, content
                ORDER BY rank DESC, keyword_matches DESC
                LIMIT $2
            """

            keywords_str = ' '.join(keywords)

            results = await self.db.fetch(search_query, keywords_str, top_k)

            logger.info(f"✅ Keyword search found {len(results)} results")

            return [dict(r) for r in results]

        except Exception as e:
            logger.error(f"❌ Keyword search error: {e}")
            return []

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        vector_weight: float = 0.5,
        keyword_weight: float = 0.5,
        threshold: float = 0.6
    ) -> List[Dict]:
        """Hybrid search combining vector and keyword search"""

        try:
            logger.info(f"🔍 Hybrid search for: {query}")

            # Detect language and preprocess
            language = self.thai_processor.detect_language(query)
            processed_query = await self.thai_processor.preprocess_thai_text(query)

            # 1. Generate query embedding
            query_embedding = await self.embed_text(processed_query)

            if not query_embedding:
                logger.warning("⚠️ Could not generate query embedding, using keyword search only")
                keywords = await self.thai_processor.extract_keywords_thai(query)
                return await self.keyword_search(keywords, top_k)

            # 2. Vector search (retrieve more candidates for better ranking)
            vector_results = await self.vector_search(
                query_embedding,
                top_k=top_k * 3,
                threshold=threshold
            )

            # 3. Keyword search (retrieve more candidates)
            # Use fewer keywords for queries (top 10 most important)
            keywords = await self.thai_processor.extract_keywords_thai(query, top_k=10)
            keyword_results = await self.keyword_search(keywords, top_k=top_k * 3)

            # 4. Hybrid ranking
            final_results = await self._hybrid_rank(
                vector_results,
                keyword_results,
                alpha=vector_weight
            )

            # Take top k
            final_results = final_results[:top_k]

            logger.info(f"✅ Hybrid search complete: {len(final_results)} results")

            return final_results

        except Exception as e:
            logger.error(f"❌ Hybrid search error: {e}")
            return []

    async def _hybrid_rank(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        alpha: float = 0.7
    ) -> List[Dict]:
        """Combine and rank results from vector and keyword search"""

        try:
            # Normalize scores to 0-1 range
            combined = {}

            # Add vector search results
            for i, result in enumerate(vector_results):
                chunk_id = str(result['chunk_id'])
                score = result.get('similarity_score', 0)

                if chunk_id not in combined:
                    combined[chunk_id] = {
                        'chunk_id': result['chunk_id'],
                        'document_id': result['document_id'],
                        'content': result['content'],
                        'vector_score': score,
                        'keyword_score': 0,
                        'position': i
                    }
                else:
                    combined[chunk_id]['vector_score'] = score

            # Add keyword search results
            for i, result in enumerate(keyword_results):
                chunk_id = str(result['chunk_id'])
                score = result.get('rank', 0)

                if chunk_id not in combined:
                    combined[chunk_id] = {
                        'chunk_id': result['chunk_id'],
                        'document_id': result['document_id'],
                        'content': result['content'],
                        'vector_score': 0,
                        'keyword_score': min(score / 10, 1.0),  # Normalize
                        'position': i
                    }
                else:
                    combined[chunk_id]['keyword_score'] = min(score / 10, 1.0)

            # Calculate combined score
            for chunk_id, data in combined.items():
                combined_score = (
                    alpha * data['vector_score'] +
                    (1 - alpha) * data['keyword_score']
                )
                data['combined_score'] = combined_score

            # Sort by combined score
            results = sorted(
                combined.values(),
                key=lambda x: x['combined_score'],
                reverse=True
            )

            return results

        except Exception as e:
            logger.error(f"❌ Ranking error: {e}")
            return vector_results

    async def get_rag_context(
        self,
        query: str,
        top_k: int = 5,
        search_mode: str = 'hybrid'
    ) -> Dict:
        """Get RAG context for a query"""

        try:
            logger.info(f"📚 Retrieving RAG context for query: {query[:50]}...")

            # Perform search
            if search_mode == 'vector':
                query_embedding = await self.embed_text(query)
                if not query_embedding:
                    return {'error': 'Could not generate embedding'}
                results = await self.vector_search(query_embedding, top_k)

            elif search_mode == 'keyword':
                keywords = await self.thai_processor.extract_keywords_thai(query)
                results = await self.keyword_search(keywords, top_k)

            else:  # hybrid
                results = await self.hybrid_search(query, top_k)

            if not results:
                logger.warning("⚠️ No results found for query")
                return {'results': [], 'context': "", 'source_count': 0, 'sources': []}

            # Format context
            context_text = self._format_context(results)

            # Get source information
            sources = await self._get_source_info([r['document_id'] for r in results])

            # Log search
            await self._log_search(query, results, search_mode)

            return {
                'results': results,
                'context': context_text,
                'source_count': len(sources),
                'sources': sources
            }

        except Exception as e:
            logger.error(f"❌ Error getting RAG context: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return {'error': str(e), 'results': [], 'context': "", 'source_count': 0, 'sources': []}

    def _format_context(self, results: List[Dict]) -> str:
        """Format search results into context string"""

        context_parts = []

        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[ข้อมูลที่ {i}]:\n{result.get('content', '')}"
            )

        return "\n\n".join(context_parts)

    async def _get_source_info(self, document_ids: List[UUID]) -> List[Dict]:
        """Get source document information"""

        try:
            if not document_ids:
                return []

            # Remove duplicates
            document_ids = list(set(document_ids))

            query = """
                SELECT document_id, title, category, created_at
                FROM document_library
                WHERE document_id = ANY($1)
            """

            sources = await self.db.fetch(query, document_ids)

            return [dict(s) for s in sources]

        except Exception as e:
            logger.error(f"❌ Error getting source info: {e}")
            return []

    async def _log_search(
        self,
        query: str,
        results: List[Dict],
        search_mode: str
    ) -> None:
        """Log search query and results"""

        try:
            query_embedding = await self.embed_text(query)

            if not query_embedding:
                return

            search_id = uuid4()

            # Extract keywords
            keywords = await self.thai_processor.extract_keywords_thai(query)

            # Get relevance scores
            relevance_scores = [r.get('combined_score', r.get('similarity_score', 0)) for r in results]
            returned_chunks = [r['chunk_id'] for r in results]

            log_query = """
                INSERT INTO rag_search_logs
                (search_id, query_text, query_language, query_tokens,
                 query_embedding, search_mode, returned_chunks,
                 relevance_scores, top_result_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """

            language = self.thai_processor.detect_language(query)

            # Convert embedding list to pgvector format string
            embedding_str = str(query_embedding) if query_embedding else None

            await self.db.execute(
                log_query,
                search_id,
                query,
                language,
                keywords,
                embedding_str,
                search_mode,
                [str(cid) for cid in returned_chunks],
                relevance_scores,
                relevance_scores[0] if relevance_scores else 0
            )

            logger.info(f"✅ Search logged: {search_id}")

        except Exception as e:
            logger.error(f"⚠️ Error logging search: {e}")

    async def record_search_feedback(
        self,
        search_id: UUID,
        was_helpful: bool,
        rating: Optional[int] = None,
        feedback_text: Optional[str] = None
    ) -> Dict:
        """Record user feedback on search results"""

        try:
            update_query = """
                UPDATE rag_search_logs
                SET was_helpful = $1, user_rating = $2, feedback_text = $3
                WHERE search_id = $4
            """

            await self.db.execute(
                update_query,
                was_helpful,
                rating,
                feedback_text,
                search_id
            )

            logger.info(f"✅ Feedback recorded for search: {search_id}")

            return {'success': True}

        except Exception as e:
            logger.error(f"❌ Error recording feedback: {e}")
            return {'success': False, 'error': str(e)}

    async def get_analytics(self, days: int = 7) -> Dict:
        """Get RAG analytics for the past N days"""

        try:
            query = """
                SELECT
                    COUNT(*) as total_queries,
                    COUNT(DISTINCT query_language) as languages_used,
                    AVG(array_length(returned_chunks, 1)) as avg_chunks_retrieved,
                    AVG(top_result_score) as avg_relevance,
                    SUM(CASE WHEN was_helpful = true THEN 1 ELSE 0 END)::float /
                        NULLIF(COUNT(CASE WHEN was_helpful IS NOT NULL THEN 1 END), 0) * 100
                        as helpful_percentage
                FROM rag_search_logs
                WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 day' * $1
            """

            result = await self.db.fetchrow(query, days)

            if result:
                return dict(result)
            else:
                return {
                    'total_queries': 0,
                    'languages_used': 0,
                    'avg_chunks_retrieved': 0,
                    'avg_relevance': 0,
                    'helpful_percentage': 0
                }

        except Exception as e:
            logger.error(f"❌ Error getting analytics: {e}")
            return {}
