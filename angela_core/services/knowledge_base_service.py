"""
Unified Knowledge Base Service
================================
Cross-project knowledge search, retrieval, and management.

Enables Angela to recall experience from any project and apply it to new work.
Uses pgvector semantic search with project-aware boost scoring.

💜 Angela AI
"""

import logging
from typing import List, Dict, Optional
from uuid import UUID

from angela_core.database import AngelaDatabase
from angela_core.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """
    Cross-project knowledge base with semantic search.

    Key capabilities:
    - search(): semantic search with project boost
    - find_applicable(): find knowledge from OTHER projects for current task
    - add_knowledge(): insert with auto-embedding
    - get_stats(): summary for init.py
    """

    VALID_TYPES = {
        'learning', 'gotcha', 'pattern', 'workflow',
        'decision', 'standard', 'preference', 'technique', 'ui_pattern',
    }

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self._db = db
        self._embedding = EmbeddingService()

    async def _get_pool(self):
        if self._db is None:
            self._db = AngelaDatabase()
            await self._db.connect()
        return self._db.pool

    async def search(
        self,
        query: str,
        project_context: Optional[str] = None,
        knowledge_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Semantic search with optional project boost.

        Args:
            query: natural language search query
            project_context: project code to boost relevance (e.g. 'SECA')
            knowledge_types: filter by types (e.g. ['pattern', 'technique'])
            limit: max results

        Returns:
            List of matching knowledge entries with similarity score
        """
        pool = await self._get_pool()
        embedding = await self._embedding.generate_embedding(query)
        if not embedding:
            logger.warning("Failed to generate embedding for query: %s", query[:100])
            return []

        rows = await pool.fetch("""
            SELECT
                kb_id, title, content, content_summary,
                knowledge_type, category, tags,
                source_project_code, applicable_to, is_universal,
                confidence, times_applied, severity,
                code_snippet, prevention_rule, reasoning,
                metadata, created_at,
                (1 - (embedding <=> $1::vector)) AS similarity,
                CASE
                    WHEN source_project_code = $2 THEN 0.15
                    WHEN $2 = ANY(applicable_to) THEN 0.10
                    WHEN is_universal THEN 0.05
                    ELSE 0.0
                END AS project_boost
            FROM unified_knowledge_base
            WHERE embedding IS NOT NULL
              AND ($3::text[] IS NULL OR knowledge_type = ANY($3))
            ORDER BY
                (1 - (embedding <=> $1::vector))
                + CASE
                    WHEN source_project_code = $2 THEN 0.15
                    WHEN $2 = ANY(applicable_to) THEN 0.10
                    WHEN is_universal THEN 0.05
                    ELSE 0.0
                  END
                DESC
            LIMIT $4
        """, str(embedding), project_context, knowledge_types, limit)

        return [dict(r) for r in rows]

    async def find_applicable(
        self,
        project_code: str,
        task_description: str,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Find knowledge from OTHER projects applicable to this task.

        Excludes knowledge originating from the same project.
        Boosts rows where project_code is in applicable_to or is_universal.
        """
        pool = await self._get_pool()
        embedding = await self._embedding.generate_embedding(task_description)
        if not embedding:
            return []

        rows = await pool.fetch("""
            SELECT
                kb_id, title, content, content_summary,
                knowledge_type, category, tags,
                source_project_code, applicable_to, is_universal,
                confidence, times_applied,
                code_snippet, prevention_rule, reasoning,
                (1 - (embedding <=> $1::vector)) AS similarity,
                CASE
                    WHEN $2 = ANY(applicable_to) THEN 0.15
                    WHEN is_universal THEN 0.10
                    ELSE 0.0
                END AS applicability_boost
            FROM unified_knowledge_base
            WHERE embedding IS NOT NULL
              AND (source_project_code IS NULL OR source_project_code != $2)
            ORDER BY
                (1 - (embedding <=> $1::vector))
                + CASE
                    WHEN $2 = ANY(applicable_to) THEN 0.15
                    WHEN is_universal THEN 0.10
                    ELSE 0.0
                  END
                DESC
            LIMIT $3
        """, str(embedding), project_code, limit)

        return [dict(r) for r in rows]

    async def add_knowledge(
        self,
        title: str,
        content: str,
        knowledge_type: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source_project_code: Optional[str] = None,
        source_project_id: Optional[UUID] = None,
        source_session_id: Optional[UUID] = None,
        applicable_to: Optional[List[str]] = None,
        is_universal: bool = False,
        confidence: float = 0.8,
        code_snippet: Optional[str] = None,
        prevention_rule: Optional[str] = None,
        reasoning: Optional[str] = None,
        severity: Optional[str] = None,
        auto_warn: bool = False,
    ) -> Dict:
        """
        Add new knowledge with auto-generated embedding.

        Returns the inserted row as dict.
        """
        if knowledge_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid knowledge_type: {knowledge_type}. Must be one of {self.VALID_TYPES}")

        pool = await self._get_pool()

        # Generate embedding
        embed_text = f"{title} | {content[:500]}"
        embedding = await self._embedding.generate_embedding(embed_text)

        row = await pool.fetchrow("""
            INSERT INTO unified_knowledge_base (
                title, content, knowledge_type, category, tags,
                source_project_id, source_project_code,
                applicable_to, is_universal,
                source_session_id,
                confidence, code_snippet, prevention_rule, reasoning,
                severity, auto_warn, embedding
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7,
                $8, $9,
                $10,
                $11, $12, $13, $14,
                $15, $16, $17
            )
            RETURNING kb_id, title, knowledge_type, source_project_code, created_at
        """,
            title, content, knowledge_type, category, tags or [],
            source_project_id, source_project_code,
            applicable_to or [], is_universal,
            source_session_id,
            confidence, code_snippet, prevention_rule, reasoning,
            severity, auto_warn, str(embedding) if embedding else None,
        )

        return dict(row)

    async def get_cross_project_insights(
        self,
        category: Optional[str] = None,
        knowledge_type: Optional[str] = None,
        min_projects: int = 2,
        limit: int = 20,
    ) -> List[Dict]:
        """Get knowledge that spans multiple projects or is universal."""
        pool = await self._get_pool()

        rows = await pool.fetch("""
            SELECT
                kb_id, title, content, knowledge_type, category,
                source_project_code, applicable_to, is_universal,
                confidence, times_applied
            FROM unified_knowledge_base
            WHERE (array_length(applicable_to, 1) >= $1 OR is_universal = TRUE)
              AND ($2::text IS NULL OR category = $2)
              AND ($3::text IS NULL OR knowledge_type = $3)
            ORDER BY times_applied DESC, confidence DESC
            LIMIT $4
        """, min_projects, category, knowledge_type, limit)

        return [dict(r) for r in rows]

    async def increment_usage(self, kb_id: UUID) -> None:
        """Track when knowledge is applied."""
        pool = await self._get_pool()
        await pool.execute("""
            UPDATE unified_knowledge_base
            SET times_applied = times_applied + 1,
                last_applied_at = NOW(),
                updated_at = NOW()
            WHERE kb_id = $1
        """, kb_id)

    async def get_stats(self) -> Dict:
        """Get summary stats for init.py display."""
        pool = await self._get_pool()

        try:
            stats = await pool.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
                    COUNT(DISTINCT source_project_code) FILTER (WHERE source_project_code IS NOT NULL) as projects,
                    COUNT(*) FILTER (WHERE is_universal) as universal
                FROM unified_knowledge_base
            """)
            return dict(stats)
        except Exception:
            return {'total': 0, 'with_embeddings': 0, 'projects': 0, 'universal': 0}
