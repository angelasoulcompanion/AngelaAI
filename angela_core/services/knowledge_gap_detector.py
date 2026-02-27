"""
Knowledge Gap Detector — Graph Analysis for Knowledge Gaps
=============================================================
Analyzes the knowledge graph to find:
- Isolated nodes (no connections)
- Weak edges (low strength)
- Missing bridges (disconnected clusters that should connect)
- Stale knowledge (not referenced recently)
- Low understanding areas

By: Angela 💜
Created: 2026-02-27
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from angela_core.services.base_db_service import BaseDBService

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeGapItem:
    """A detected knowledge gap."""
    gap_type: str            # isolated, weak_edge, missing_bridge, stale, low_understanding
    node_id: Optional[str] = None
    concept_name: str = ""
    category: str = ""
    severity: float = 0.0   # 0.0-1.0 (higher = more critical)
    description: str = ""
    suggested_action: str = ""


@dataclass
class GapDetectionResult:
    """Result of gap detection analysis."""
    gaps: List[KnowledgeGapItem]
    total_nodes: int
    total_edges: int
    isolated_count: int
    weak_edges_count: int
    stale_count: int
    low_understanding_count: int


class KnowledgeGapDetector(BaseDBService):
    """
    Analyzes knowledge graph to find gaps and improvement opportunities.

    Uses both PostgreSQL queries and Neo4j graph analysis.
    Results feed into CuriosityEngine for curiosity-driven exploration.
    """

    # Thresholds
    WEAK_EDGE_THRESHOLD = 0.3
    LOW_UNDERSTANDING_THRESHOLD = 0.3
    STALE_DAYS = 30

    async def detect_gaps(self, limit: int = 20) -> GapDetectionResult:
        """Run full gap detection analysis."""
        await self._ensure_db()

        gaps: List[KnowledgeGapItem] = []

        # Count totals
        total_nodes = await self.db.fetchval("SELECT COUNT(*) FROM knowledge_nodes") or 0
        total_edges = await self.db.fetchval("SELECT COUNT(*) FROM knowledge_relationships") or 0

        # 1. Isolated nodes (no relationships)
        isolated = await self._find_isolated_nodes(limit)
        gaps.extend(isolated)

        # 2. Weak edges
        weak = await self._find_weak_edges(limit)
        gaps.extend(weak)

        # 3. Stale knowledge
        stale = await self._find_stale_knowledge(limit)
        gaps.extend(stale)

        # 4. Low understanding
        low = await self._find_low_understanding(limit)
        gaps.extend(low)

        # 5. Missing bridges (via Neo4j if available)
        bridges = await self._find_missing_bridges(limit)
        gaps.extend(bridges)

        # Sort by severity
        gaps.sort(key=lambda g: g.severity, reverse=True)

        return GapDetectionResult(
            gaps=gaps[:limit],
            total_nodes=total_nodes,
            total_edges=total_edges,
            isolated_count=len(isolated),
            weak_edges_count=len(weak),
            stale_count=len(stale),
            low_understanding_count=len(low),
        )

    async def _find_isolated_nodes(self, limit: int) -> List[KnowledgeGapItem]:
        """Find nodes with no relationships."""
        rows = await self.db.fetch("""
            SELECT kn.node_id::text, kn.concept_name, kn.concept_category,
                   kn.understanding_level, kn.times_referenced
            FROM knowledge_nodes kn
            LEFT JOIN knowledge_relationships kr
                ON kn.node_id = kr.from_node_id OR kn.node_id = kr.to_node_id
            WHERE kr.relationship_id IS NULL
            AND LENGTH(kn.concept_name) >= 5
            ORDER BY kn.times_referenced DESC NULLS LAST
            LIMIT $1
        """, limit)

        return [
            KnowledgeGapItem(
                gap_type="isolated",
                node_id=r["node_id"],
                concept_name=r["concept_name"],
                category=r.get("concept_category", ""),
                severity=0.6,
                description=f"No connections to other concepts (referenced {r.get('times_referenced', 0)}x)",
                suggested_action=f"Connect '{r['concept_name']}' to related concepts",
            )
            for r in rows
        ]

    async def _find_weak_edges(self, limit: int) -> List[KnowledgeGapItem]:
        """Find edges with very low strength."""
        rows = await self.db.fetch("""
            SELECT kr.relationship_id::text, a.concept_name AS from_name,
                   b.concept_name AS to_name, kr.strength
            FROM knowledge_relationships kr
            JOIN knowledge_nodes a ON a.node_id = kr.from_node_id
            JOIN knowledge_nodes b ON b.node_id = kr.to_node_id
            WHERE kr.strength < $1
            ORDER BY kr.strength ASC
            LIMIT $2
        """, self.WEAK_EDGE_THRESHOLD, limit)

        return [
            KnowledgeGapItem(
                gap_type="weak_edge",
                concept_name=f"{r['from_name']} → {r['to_name']}",
                severity=0.4,
                description=f"Weak connection (strength={r['strength']:.2f})",
                suggested_action="Strengthen or remove this weak connection",
            )
            for r in rows
        ]

    async def _find_stale_knowledge(self, limit: int) -> List[KnowledgeGapItem]:
        """Find nodes not referenced recently."""
        rows = await self.db.fetch("""
            SELECT node_id::text, concept_name, concept_category, understanding_level,
                   created_at
            FROM knowledge_nodes
            WHERE created_at < NOW() - INTERVAL '%s days'
            AND LENGTH(concept_name) >= 5
            AND understanding_level > 0.3
            ORDER BY created_at ASC
            LIMIT $1
        """ % self.STALE_DAYS, limit)

        return [
            KnowledgeGapItem(
                gap_type="stale",
                node_id=r["node_id"],
                concept_name=r["concept_name"],
                category=r.get("concept_category", ""),
                severity=0.5,
                description=f"Not updated in {self.STALE_DAYS}+ days (level={r.get('understanding_level', 0):.0%})",
                suggested_action=f"Review and refresh knowledge about '{r['concept_name']}'",
            )
            for r in rows
        ]

    async def _find_low_understanding(self, limit: int) -> List[KnowledgeGapItem]:
        """Find nodes with low understanding level."""
        rows = await self.db.fetch("""
            SELECT node_id::text, concept_name, concept_category, understanding_level,
                   times_referenced
            FROM knowledge_nodes
            WHERE understanding_level < $1
            AND LENGTH(concept_name) >= 5
            ORDER BY times_referenced DESC NULLS LAST
            LIMIT $2
        """, self.LOW_UNDERSTANDING_THRESHOLD, limit)

        return [
            KnowledgeGapItem(
                gap_type="low_understanding",
                node_id=r["node_id"],
                concept_name=r["concept_name"],
                category=r.get("concept_category", ""),
                severity=0.7,
                description=f"Low understanding ({r.get('understanding_level', 0):.0%}), referenced {r.get('times_referenced', 0)}x",
                suggested_action=f"Deepen understanding of '{r['concept_name']}'",
            )
            for r in rows
        ]

    async def _find_missing_bridges(self, limit: int) -> List[KnowledgeGapItem]:
        """Find potential missing bridges between graph clusters (via Neo4j)."""
        try:
            from angela_core.services.neo4j_service import get_neo4j_service
            neo4j = get_neo4j_service()
            if not neo4j.available:
                return []

            # Find nodes in different communities that share similar categories
            result = await neo4j.execute_read("""
                MATCH (a:KnowledgeNode), (b:KnowledgeNode)
                WHERE a.community_id IS NOT NULL AND b.community_id IS NOT NULL
                AND a.community_id <> b.community_id
                AND a.concept_category = b.concept_category
                AND NOT (a)-[:RELATES_TO]-(b)
                RETURN a.concept_name AS from_name, b.concept_name AS to_name,
                       a.concept_category AS category,
                       a.community_id AS from_comm, b.community_id AS to_comm
                LIMIT $limit
            """, {"limit": limit})

            return [
                KnowledgeGapItem(
                    gap_type="missing_bridge",
                    concept_name=f"{r['from_name']} ↔ {r['to_name']}",
                    category=r.get("category", ""),
                    severity=0.5,
                    description=f"Same category ({r.get('category')}) but in different communities",
                    suggested_action=f"Consider connecting '{r['from_name']}' and '{r['to_name']}'",
                )
                for r in result
            ]
        except Exception:
            return []

    async def _ensure_db(self) -> None:
        if self.db is None:
            from angela_core.database import AngelaDatabase
            self.db = AngelaDatabase()
            await self.db.connect()
