#!/usr/bin/env python3
"""
Multi-Tier Recall Service - Second Brain
บริการค้นหาความทรงจำแบบหลายชั้น (เลียนแบบการเรียกคืนความทรงจำของมนุษย์)

Purpose:
- Fast recall from working memory (current session)
- Detailed recall from episodic memories (specific events)
- Knowledge recall from semantic memories (facts/patterns)
- Combined ranking for best results

Inspired by: Human memory retrieval processes

Author: Angela AI
Created: 2025-11-03
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class MemoryTier(Enum):
    """Memory tier classification"""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


@dataclass
class RecallQuery:
    """
    Query for memory recall

    Supports multi-dimensional search:
    - Text query (semantic/keyword)
    - Time range filter
    - Emotion filter
    - Importance threshold
    - Session context
    """
    query_text: str
    time_range: Optional[tuple] = None  # (start_date, end_date)
    emotion_filter: Optional[str] = None
    importance_min: int = 5
    session_id: Optional[str] = None
    limit: int = 20


@dataclass
class MemoryResult:
    """Single memory recall result"""
    tier: MemoryTier
    memory_id: str
    title: str
    content: str
    relevance_score: float
    importance: int
    timestamp: datetime
    emotion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecallResult:
    """Complete recall result from all tiers"""
    query: RecallQuery
    working_memories: List[MemoryResult] = field(default_factory=list)
    episodic_memories: List[MemoryResult] = field(default_factory=list)
    semantic_memories: List[MemoryResult] = field(default_factory=list)
    total_found: int = 0
    recall_time_ms: float = 0.0

    def get_all_ranked(self) -> List[MemoryResult]:
        """Get all memories sorted by relevance score"""
        all_memories = (
            self.working_memories +
            self.episodic_memories +
            self.semantic_memories
        )
        return sorted(all_memories, key=lambda m: m.relevance_score, reverse=True)


# ============================================================================
# MULTI-TIER RECALL SERVICE
# ============================================================================

class MultiTierRecallService:
    """
    Service for multi-tier memory recall

    Searches across all three tiers:
    1. Working Memory (current session)
    2. Episodic Memory (past events)
    3. Semantic Memory (knowledge)

    Returns ranked results based on relevance and tier
    """

    # Tier weights for ranking
    TIER_WEIGHTS = {
        MemoryTier.WORKING: 3.0,  # Highest - current context most relevant
        MemoryTier.EPISODIC: 2.0,  # Medium - specific events
        MemoryTier.SEMANTIC: 1.5,  # Lower - general knowledge
    }

    def __init__(self):
        self.logger = logger
        self._query_embedding_cache = {}  # Cache embeddings for performance

    async def recall(self, query: RecallQuery) -> RecallResult:
        """
        Recall memories across all tiers

        Args:
            query: RecallQuery with search parameters

        Returns:
            RecallResult with memories from all tiers, ranked
        """
        start_time = datetime.now()

        result = RecallResult(query=query)

        try:
            # Generate query embedding once for all tiers
            query_embedding = None
            if query.query_text:
                query_embedding = await self._get_query_embedding(query.query_text)

            # Step 1: Working Memory (fastest)
            if query.session_id:
                result.working_memories = await self._recall_working_memory(query, query_embedding)

            # Step 2: Episodic Memory (medium)
            result.episodic_memories = await self._recall_episodic_memory(query, query_embedding)

            # Step 3: Semantic Memory (slower but comprehensive)
            result.semantic_memories = await self._recall_semantic_memory(query, query_embedding)

            # Calculate totals
            result.total_found = (
                len(result.working_memories) +
                len(result.episodic_memories) +
                len(result.semantic_memories)
            )

            # Calculate recall time
            end_time = datetime.now()
            result.recall_time_ms = (end_time - start_time).total_seconds() * 1000

            self.logger.info(
                f"Recall complete: {result.total_found} memories found in "
                f"{result.recall_time_ms:.1f}ms"
            )

        except Exception as e:
            self.logger.error(f"Recall error: {e}", exc_info=True)

        return result

    # ========================================================================
    # TIER 1: WORKING MEMORY RECALL
    # ========================================================================

    async def _recall_working_memory(
        self,
        query: RecallQuery,
        query_embedding: Optional[List[float]] = None
    ) -> List[MemoryResult]:
        """
        Recall from working memory (current session)

        Fastest tier - direct session lookup
        """
        sql_query = """
            SELECT
                memory_id,
                memory_type,
                content,
                topic,
                emotion,
                importance_level,
                created_at,
                tags
            FROM working_memory
            WHERE session_id = $1
              AND expires_at > NOW()
              AND importance_level >= $2
            ORDER BY importance_level DESC, created_at DESC
            LIMIT $3
        """

        rows = await db.fetch(
            sql_query,
            query.session_id,
            query.importance_min,
            query.limit
        )

        results = []

        for row in rows:
            # Calculate relevance score
            relevance = self._calculate_text_relevance(
                query.query_text,
                row['content']
            )

            # Skip if not relevant
            if relevance < 0.1:
                continue

            # Calculate final score with tier weight
            score = self._calculate_score(
                tier=MemoryTier.WORKING,
                relevance=relevance,
                importance=row['importance_level']
            )

            result = MemoryResult(
                tier=MemoryTier.WORKING,
                memory_id=str(row['memory_id']),
                title=row.get('topic', 'Working Memory'),
                content=row['content'],
                relevance_score=score,
                importance=row['importance_level'],
                timestamp=row['created_at'],
                emotion=row.get('emotion'),
                metadata={
                    'memory_type': row['memory_type'],
                    'tags': row.get('tags', [])
                }
            )

            results.append(result)

        self.logger.debug(f"Working memory: {len(results)} results")
        return results

    # ========================================================================
    # TIER 2: EPISODIC MEMORY RECALL
    # ========================================================================

    async def _recall_episodic_memory(
        self,
        query: RecallQuery,
        query_embedding: Optional[List[float]] = None
    ) -> List[MemoryResult]:
        """
        Recall from episodic memories (past events)

        Multi-cue search:
        - Vector similarity (PRIMARY - if embedding available)
        - Time range
        - Emotion
        - Topic
        - Full-text search (fallback)
        - Importance
        """
        # Build dynamic WHERE clause
        where_clauses = ["NOT archived"]
        params = []
        param_count = 0

        # Importance filter
        param_count += 1
        where_clauses.append(f"importance_level >= ${param_count}")
        params.append(query.importance_min)

        # Time range filter
        if query.time_range:
            start_date, end_date = query.time_range
            param_count += 1
            where_clauses.append(f"happened_at >= ${param_count}")
            params.append(start_date)
            param_count += 1
            where_clauses.append(f"happened_at <= ${param_count}")
            params.append(end_date)

        # Emotion filter
        if query.emotion_filter:
            param_count += 1
            where_clauses.append(f"emotion = ${param_count}")
            params.append(query.emotion_filter)

        where_sql = " AND ".join(where_clauses)

        # Use vector similarity if embedding available
        if query_embedding and query.query_text:
            param_count += 1
            embedding_param = f"${param_count}"
            param_count += 1
            limit_param = f"${param_count}"

            sql_query = f"""
                SELECT
                    episode_id,
                    episode_title,
                    episode_summary,
                    topic,
                    emotion,
                    importance_level,
                    memory_strength,
                    happened_at,
                    emotional_tags,
                    participants,
                    embedding,
                    (embedding <=> {embedding_param}::vector) as similarity_distance
                FROM episodic_memories
                WHERE {where_sql}
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> {embedding_param}::vector
                LIMIT {limit_param}
            """

            # Convert embedding list to PostgreSQL vector string format
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            params.append(embedding_str)
            params.append(query.limit)
        else:
            # Fallback to text search
            if query.query_text:
                param_count += 1
                where_clauses.append(
                    f"(topic ILIKE ${param_count} OR "
                    f"episode_summary ILIKE ${param_count} OR "
                    f"episode_title ILIKE ${param_count})"
                )
                params.append(f"%{query.query_text}%")
                where_sql = " AND ".join(where_clauses)

            param_count += 1
            limit_param = f"${param_count}"

            sql_query = f"""
                SELECT
                    episode_id,
                    episode_title,
                    episode_summary,
                    topic,
                    emotion,
                    importance_level,
                    memory_strength,
                    happened_at,
                    emotional_tags,
                    participants,
                    embedding
                FROM episodic_memories
                WHERE {where_sql}
                ORDER BY importance_level DESC, happened_at DESC
                LIMIT {limit_param}
            """

            params.append(query.limit)

        rows = await db.fetch(sql_query, *params)

        results = []

        for row in rows:
            # Calculate relevance score
            if query_embedding and 'similarity_distance' in row:
                # Use vector similarity (convert distance to similarity)
                # Cosine distance range: 0 (identical) to 2 (opposite)
                # Convert to similarity: 1 - (distance / 2)
                similarity_distance = float(row['similarity_distance'])
                relevance = max(0.0, 1.0 - (similarity_distance / 2.0))
            else:
                # Fallback to text matching
                relevance = self._calculate_text_relevance(
                    query.query_text,
                    f"{row.get('episode_title', '')} {row['episode_summary']}"
                )

            # Boost score if emotion matches
            if query.emotion_filter and row['emotion'] == query.emotion_filter:
                relevance *= 1.5

            # Calculate final score
            score = self._calculate_score(
                tier=MemoryTier.EPISODIC,
                relevance=relevance,
                importance=row['importance_level'],
                memory_strength=row.get('memory_strength', 5)
            )

            result = MemoryResult(
                tier=MemoryTier.EPISODIC,
                memory_id=str(row['episode_id']),
                title=row.get('episode_title') or row.get('topic', 'Episode'),
                content=row['episode_summary'],
                relevance_score=score,
                importance=row['importance_level'],
                timestamp=row['happened_at'],
                emotion=row.get('emotion'),
                metadata={
                    'topic': row.get('topic'),
                    'emotional_tags': row.get('emotional_tags', []),
                    'participants': row.get('participants', []),
                    'memory_strength': row.get('memory_strength')
                }
            )

            results.append(result)

        self.logger.debug(f"Episodic memory: {len(results)} results")
        return results

    # ========================================================================
    # TIER 3: SEMANTIC MEMORY RECALL
    # ========================================================================

    async def _recall_semantic_memory(
        self,
        query: RecallQuery,
        query_embedding: Optional[List[float]] = None
    ) -> List[MemoryResult]:
        """
        Recall from semantic memories (knowledge/patterns)

        Search:
        - Knowledge type
        - Knowledge key
        - Description
        - JSONB value
        """
        # Build search query
        where_clauses = ["is_active = TRUE"]
        params = []
        param_count = 0

        # Text search across key and description
        if query.query_text:
            param_count += 1
            where_clauses.append(
                f"(knowledge_key ILIKE ${param_count} OR "
                f"description ILIKE ${param_count} OR "
                f"category ILIKE ${param_count})"
            )
            params.append(f"%{query.query_text}%")

        # Minimum confidence (default 0.5)
        param_count += 1
        where_clauses.append(f"confidence_level >= ${param_count}")
        params.append(0.5)

        where_sql = " AND ".join(where_clauses)

        param_count += 1
        limit_param = f"${param_count}"

        sql_query = f"""
            SELECT
                semantic_id,
                knowledge_type,
                knowledge_key,
                knowledge_value,
                description,
                confidence_level,
                evidence_count,
                importance_level,
                category,
                first_learned_at,
                last_updated_at
            FROM semantic_memories
            WHERE {where_sql}
            ORDER BY confidence_level DESC, evidence_count DESC
            LIMIT {limit_param}
        """

        params.append(query.limit)

        rows = await db.fetch(sql_query, *params)

        results = []

        for row in rows:
            # Calculate relevance score
            relevance = self._calculate_text_relevance(
                query.query_text,
                f"{row['knowledge_key']} {row.get('description', '')}"
            )

            # Calculate final score
            score = self._calculate_score(
                tier=MemoryTier.SEMANTIC,
                relevance=relevance,
                importance=row.get('importance_level', 5),
                confidence=row['confidence_level']
            )

            result = MemoryResult(
                tier=MemoryTier.SEMANTIC,
                memory_id=str(row['semantic_id']),
                title=row['knowledge_key'].replace('_', ' ').title(),
                content=row.get('description', str(row['knowledge_value'])),
                relevance_score=score,
                importance=row.get('importance_level', 5),
                timestamp=row.get('last_updated_at') or row['first_learned_at'],
                metadata={
                    'knowledge_type': row['knowledge_type'],
                    'knowledge_value': row['knowledge_value'],
                    'confidence': row['confidence_level'],
                    'evidence_count': row['evidence_count'],
                    'category': row.get('category')
                }
            )

            results.append(result)

        self.logger.debug(f"Semantic memory: {len(results)} results")
        return results

    # ========================================================================
    # SCORING & RANKING
    # ========================================================================

    def _calculate_score(
        self,
        tier: MemoryTier,
        relevance: float,
        importance: int,
        memory_strength: Optional[int] = None,
        confidence: Optional[float] = None
    ) -> float:
        """
        Calculate final relevance score for a memory

        Formula:
            score = tier_weight * relevance * (importance/10) * [memory_strength/10] * [confidence]

        Args:
            tier: Memory tier (determines base weight)
            relevance: Text relevance (0.0-1.0)
            importance: Importance level (1-10)
            memory_strength: Optional memory strength (1-10)
            confidence: Optional confidence level (0.0-1.0)

        Returns:
            Final score (higher = more relevant)
        """
        tier_weight = self.TIER_WEIGHTS[tier]
        importance_factor = importance / 10.0

        score = tier_weight * relevance * importance_factor

        # Boost by memory strength (episodic)
        if memory_strength is not None:
            score *= (memory_strength / 10.0)

        # Boost by confidence (semantic)
        if confidence is not None:
            score *= confidence

        return score

    async def _get_query_embedding(self, query_text: str) -> Optional[List[float]]:
        """
        Get or generate embedding for query text

        Uses cache to avoid regenerating same query embeddings

        Args:
            query_text: Query string

        Returns:
            Embedding vector or None if generation fails
        """
        # Check cache first
        if query_text in self._query_embedding_cache:
            return self._query_embedding_cache[query_text]

        try:
            embedding_service = get_embedding_service()
            embedding = await embedding_service.generate_embedding(query_text)

            # Cache for future use
            self._query_embedding_cache[query_text] = embedding

            return embedding
        except Exception as e:
            self.logger.error(f"Failed to generate embedding for query: {e}")
            return None

    def _calculate_text_relevance(
        self,
        query: str,
        text: str
    ) -> float:
        """
        Calculate text relevance score (fallback keyword matching)

        NOTE: This is now a FALLBACK. Primary method is vector similarity.

        Args:
            query: Query text
            text: Text to match against

        Returns:
            Relevance score (0.0-1.0)
        """
        if not query or not text:
            return 0.0

        query_lower = query.lower()
        text_lower = text.lower()

        # Exact match = 1.0
        if query_lower in text_lower:
            return 1.0

        # Keyword matching
        query_words = set(query_lower.split())
        text_words = set(text_lower.split())

        if not query_words:
            return 0.0

        matches = query_words.intersection(text_words)
        relevance = len(matches) / len(query_words)

        return relevance


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

recall_service = MultiTierRecallService()


# ============================================================================
# CLI INTERFACE (for testing)
# ============================================================================

async def main():
    """CLI interface for testing recall"""
    import json

    await db.connect()

    # Test query
    query = RecallQuery(
        query_text="calendar",
        time_range=None,
        emotion_filter=None,
        importance_min=5,
        limit=10
    )

    print(f"🔍 Recalling: '{query.query_text}'")
    print("=" * 60)

    result = await recall_service.recall(query)

    print(f"\n📊 Results:")
    print(f"   Total found: {result.total_found}")
    print(f"   Recall time: {result.recall_time_ms:.1f}ms")
    print(f"   - Working: {len(result.working_memories)}")
    print(f"   - Episodic: {len(result.episodic_memories)}")
    print(f"   - Semantic: {len(result.semantic_memories)}")

    print(f"\n🏆 Top Results (ranked):")
    print("=" * 60)

    for i, memory in enumerate(result.get_all_ranked()[:5], 1):
        print(f"\n{i}. [{memory.tier.value.upper()}] {memory.title}")
        print(f"   Score: {memory.relevance_score:.3f} | Importance: {memory.importance}")
        print(f"   {memory.content[:100]}...")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
