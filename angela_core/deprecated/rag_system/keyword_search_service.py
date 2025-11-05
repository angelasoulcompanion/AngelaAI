#!/usr/bin/env python3
"""
Keyword Search Service for Hybrid RAG
Uses PostgreSQL Full-Text Search with BM25-like ranking

Features:
- Language-agnostic search (works with Thai and English)
- BM25-like ranking using ts_rank_cd
- Phrase queries support
- Fast GIN index lookup

⚠️ DEPRECATION WARNING:
This service is deprecated. Use angela_core.application.services.rag_service.RAGService instead.
"""

import warnings
import asyncpg

warnings.warn(
    "keyword_search_service is deprecated. Use RAGService instead.",
    DeprecationWarning,
    stacklevel=2
)
import logging
from typing import List, Dict, Optional
from uuid import UUID
import re

logger = logging.getLogger(__name__)


class KeywordSearchService:
    """PostgreSQL full-text search for hybrid RAG"""

    @staticmethod
    def _preprocess_query(query: str) -> str:
        """
        Preprocess search query for better results

        Args:
            query: Raw search query

        Returns:
            Preprocessed query string
        """
        # Remove special characters that might break tsquery
        query = re.sub(r'[^\w\s\u0E00-\u0E7F]', ' ', query)

        # Normalize whitespace
        query = ' '.join(query.split())

        # Split into terms
        terms = query.split()

        # Add prefix matching for each term (allows partial matches)
        # This is especially useful for Thai text
        processed_terms = [f"{term}:*" for term in terms if len(term) > 1]

        # Join with OR operator (any term matches)
        # Could also use & for AND operator (all terms must match)
        return ' | '.join(processed_terms) if processed_terms else query

    @staticmethod
    async def keyword_search(
        db: asyncpg.Connection,
        query: str,
        limit: int = 10,
        threshold: float = 0.01,
        document_id: Optional[UUID] = None
    ) -> List[Dict]:
        """
        Perform keyword search using PostgreSQL full-text search

        Args:
            db: Database connection
            query: Search query (Thai or English)
            limit: Maximum results to return
            threshold: Minimum ts_rank score (0-1)
            document_id: Optional document ID filter

        Returns:
            List of matching chunks with scores
        """
        try:
            # Preprocess query
            processed_query = KeywordSearchService._preprocess_query(query)

            if not processed_query:
                logger.warning("Empty query after preprocessing")
                return []

            logger.info(f"🔍 Keyword search: '{query}' -> '{processed_query}'")

            # Build SQL query
            # ts_rank_cd uses document length normalization (similar to BM25)
            # Normalization = 1 means divide rank by document length
            sql_query = """
                SELECT
                    chunk_id,
                    document_id,
                    chunk_index,
                    content,
                    thai_word_count,
                    english_word_count,
                    page_number,
                    section_title,
                    importance_score,
                    -- BM25-like ranking with length normalization
                    ts_rank_cd(content_tsv, query, 1) AS keyword_score,
                    -- Headline for context (shows matching terms)
                    ts_headline('simple', content, query,
                        'MaxWords=50, MinWords=25, ShortWord=3') AS headline
                FROM document_chunks, to_tsquery('simple', $1) query
                WHERE content_tsv @@ query
            """

            params = [processed_query]

            # Add document filter if specified
            if document_id:
                sql_query += " AND document_id = $2"
                params.append(document_id)

            # Order by score and apply threshold
            sql_query += f"""
                AND ts_rank_cd(content_tsv, query, 1) >= ${len(params) + 1}
                ORDER BY keyword_score DESC, chunk_index ASC
                LIMIT ${len(params) + 2}
            """

            params.extend([threshold, limit])

            # Execute query
            results = await db.fetch(sql_query, *params)

            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'chunk_id': str(row['chunk_id']),
                    'document_id': str(row['document_id']),
                    'chunk_index': row['chunk_index'],
                    'content': row['content'],
                    'thai_word_count': row['thai_word_count'],
                    'english_word_count': row['english_word_count'],
                    'page_number': row['page_number'],
                    'section_title': row['section_title'],
                    'importance_score': row['importance_score'],
                    'keyword_score': float(row['keyword_score']),
                    'headline': row['headline']
                })

            logger.info(f"  Found {len(formatted_results)} keyword matches")

            return formatted_results

        except Exception as e:
            logger.error(f"❌ Keyword search error: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    async def phrase_search(
        db: asyncpg.Connection,
        phrase: str,
        limit: int = 10,
        document_id: Optional[UUID] = None
    ) -> List[Dict]:
        """
        Search for exact phrase matches

        Args:
            db: Database connection
            phrase: Exact phrase to search for
            limit: Maximum results
            document_id: Optional document filter

        Returns:
            List of chunks containing the exact phrase
        """
        try:
            # Convert phrase to tsquery phrase format
            # "hello world" -> 'hello <-> world'
            terms = phrase.split()
            phrase_query = ' <-> '.join(terms)

            logger.info(f"📝 Phrase search: '{phrase}'")

            sql_query = """
                SELECT
                    chunk_id,
                    document_id,
                    chunk_index,
                    content,
                    thai_word_count,
                    english_word_count,
                    page_number,
                    section_title,
                    importance_score,
                    ts_rank_cd(content_tsv, query, 1) AS keyword_score
                FROM document_chunks, to_tsquery('simple', $1) query
                WHERE content_tsv @@ query
            """

            params = [phrase_query]

            if document_id:
                sql_query += " AND document_id = $2"
                params.append(document_id)

            sql_query += f"""
                ORDER BY keyword_score DESC, chunk_index ASC
                LIMIT ${len(params) + 1}
            """

            params.append(limit)

            results = await db.fetch(sql_query, *params)

            formatted_results = []
            for row in results:
                formatted_results.append({
                    'chunk_id': str(row['chunk_id']),
                    'document_id': str(row['document_id']),
                    'chunk_index': row['chunk_index'],
                    'content': row['content'],
                    'thai_word_count': row['thai_word_count'],
                    'english_word_count': row['english_word_count'],
                    'page_number': row['page_number'],
                    'section_title': row['section_title'],
                    'importance_score': row['importance_score'],
                    'keyword_score': float(row['keyword_score'])
                })

            logger.info(f"  Found {len(formatted_results)} phrase matches")

            return formatted_results

        except Exception as e:
            logger.error(f"❌ Phrase search error: {e}")
            return []

    @staticmethod
    def normalize_scores(results: List[Dict], score_key: str = 'keyword_score') -> List[Dict]:
        """
        Normalize scores to 0-1 range using min-max normalization

        Args:
            results: List of search results
            score_key: Key containing the score to normalize

        Returns:
            Results with normalized scores
        """
        if not results:
            return results

        scores = [r[score_key] for r in results if score_key in r]

        if not scores:
            return results

        min_score = min(scores)
        max_score = max(scores)

        # Avoid division by zero
        score_range = max_score - min_score if max_score != min_score else 1.0

        for result in results:
            if score_key in result:
                normalized = (result[score_key] - min_score) / score_range
                result[f'{score_key}_normalized'] = normalized

        return results
