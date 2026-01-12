#!/usr/bin/env python3
"""
Knowledge Repository - PostgreSQL Implementation

Handles all data access for KnowledgeNode entity.
Manages Angela's knowledge graph with concept understanding and relationships.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.domain import KnowledgeNode, KnowledgeCategory
from angela_core.domain.interfaces.repositories import IKnowledgeRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.utils import parse_enum, validate_embedding


class KnowledgeRepository(BaseRepository[KnowledgeNode], IKnowledgeRepository):
    """
    PostgreSQL repository for KnowledgeNode entity.

    Table: knowledge_nodes
    Columns:
    - node_id (UUID, PK)
    - concept_name (VARCHAR, unique)
    - concept_category (VARCHAR)
    - my_understanding (TEXT)
    - why_important (TEXT)
    - how_i_learned (TEXT)
    - understanding_level (DOUBLE PRECISION)
    - last_used_at (TIMESTAMP, nullable)
    - times_referenced (INTEGER)
    - embedding (VECTOR(768), nullable)
    - created_at (TIMESTAMP)

    Note: Some entity fields (confidence, source_file, topic, # content_json)  # REMOVED: Migration 010
    are not in the database schema. These will use default values.
    """

    def __init__(self, db):
        """Initialize repository."""
        super().__init__(
            db=db,
            table_name="knowledge_nodes",
            primary_key_column="node_id"
        )

    # ========================================================================
    # ROW TO ENTITY CONVERSION
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> KnowledgeNode:
        """Convert database row to KnowledgeNode entity."""
        # Parse enum with DRY utility
        category = parse_enum(row.get('concept_category'), KnowledgeCategory, KnowledgeCategory.GENERAL)

        # Parse embedding with DRY utility
        embedding = validate_embedding(row.get('embedding'))

        return KnowledgeNode(
            concept_name=row['concept_name'],
            id=row['node_id'],
            concept_category=category,
            my_understanding=row.get('my_understanding', 'Learning this concept'),
            why_important=row.get('why_important', 'This helps me understand and serve better'),
            how_i_learned=row.get('how_i_learned', 'From conversations and experiences'),
            understanding_level=row.get('understanding_level', 0.5),
            confidence=0.8,  # Default, not in DB
            times_referenced=row.get('times_referenced', 0),
            last_used_at=row.get('last_used_at'),
            source_file=None,  # Not in DB
            topic=None,  # Not in DB
            # content_json={},  # Not in DB  # REMOVED: Migration 010
            embedding=embedding,
            created_at=row['created_at']
        )

    def _entity_to_dict(self, entity: KnowledgeNode) -> Dict[str, Any]:
        """
        Convert KnowledgeNode entity to database row dict.

        Args:
            entity: KnowledgeNode entity

        Returns:
            Dictionary for database insert/update
        """
        return {
            'node_id': entity.id,
            'concept_name': entity.concept_name,
            'concept_category': entity.concept_category.value,
            'my_understanding': entity.my_understanding,
            'why_important': entity.why_important,
            'how_i_learned': entity.how_i_learned,
            'understanding_level': entity.understanding_level,
            'times_referenced': entity.times_referenced,
            'last_used_at': entity.last_used_at,
            'embedding': entity.embedding,
            'created_at': entity.created_at
        }

    # ========================================================================
    # KNOWLEDGE-SPECIFIC QUERIES
    # ========================================================================

    async def search_by_vector(
        self,
        embedding: List[float],
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[tuple[KnowledgeNode, float]]:
        """
        Vector similarity search for knowledge.

        Args:
            embedding: Query embedding vector (768 dimensions)
            top_k: Number of top results to return
            category: Optional category filter

        Returns:
            List of (KnowledgeNode, similarity_score) tuples
        """
        if category:
            query = f"""
                SELECT *, (embedding <=> $1::vector) as distance
                FROM {self.table_name}
                WHERE concept_category = $2 AND embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT $3
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, embedding, category, top_k)
        else:
            query = f"""
                SELECT *, (embedding <=> $1::vector) as distance
                FROM {self.table_name}
                WHERE embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT $2
            """
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, embedding, top_k)

        # Convert distance to similarity score (1 - distance for cosine)
        results = []
        for row in rows:
            knowledge = self._row_to_entity(row)
            similarity = 1.0 - float(row['distance'])
            results.append((knowledge, similarity))

        return results

    async def get_by_concept_name(
        self,
        concept_name: str
    ) -> Optional[KnowledgeNode]:
        """
        Get knowledge node by concept name.

        Args:
            concept_name: Concept name (unique)

        Returns:
            KnowledgeNode if found, None otherwise
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE concept_name = $1
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, concept_name)

        return self._row_to_entity(row) if row else None

    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """
        Get knowledge by category.

        Args:
            category: Knowledge category
            limit: Maximum results

        Returns:
            List of knowledge nodes in category
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE concept_category = $1
            ORDER BY understanding_level DESC, created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, category, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_well_understood(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """
        Get well-understood concepts (understanding_level >= threshold).

        Args:
            threshold: Understanding threshold (0.0-1.0)
            limit: Maximum results

        Returns:
            List of well-understood knowledge nodes
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE understanding_level >= $1
            ORDER BY understanding_level DESC, times_referenced DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_expert_level(
        self,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """
        Get expert-level concepts (understanding_level >= 0.9).

        Args:
            limit: Maximum results

        Returns:
            List of expert-level knowledge nodes
        """
        return await self.get_well_understood(0.9, limit)

    async def get_about_david(
        self,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """
        Get knowledge about David.

        Args:
            limit: Maximum results

        Returns:
            List of knowledge nodes about David
        """
        return await self.get_by_category('david', limit)

    async def get_frequently_used(
        self,
        threshold: int = 10,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """
        Get frequently referenced concepts (times_referenced >= threshold).

        Args:
            threshold: Reference count threshold
            limit: Maximum results

        Returns:
            List of frequently used knowledge nodes
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE times_referenced >= $1
            ORDER BY times_referenced DESC, understanding_level DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, threshold, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_recently_used(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """
        Get recently used concepts (last_used_at within last N days).

        Args:
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of recently used knowledge nodes
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE last_used_at >= $1
            ORDER BY last_used_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, cutoff_date, limit)

        return [self._row_to_entity(row) for row in rows]

    async def search_by_concept(
        self,
        query: str,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """
        Search knowledge by concept name.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching knowledge nodes
        """
        search_query = f"""
            SELECT * FROM {self.table_name}
            WHERE concept_name ILIKE $1
               OR my_understanding ILIKE $1
            ORDER BY understanding_level DESC, times_referenced DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(search_query, f"%{query}%", limit)

        return [self._row_to_entity(row) for row in rows]

    async def count_by_category(self, category: str) -> int:
        """
        Count knowledge nodes by category.

        Args:
            category: Knowledge category

        Returns:
            Count of knowledge nodes in category
        """
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE concept_category = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, category)

        return result or 0

    async def get_related_knowledge(
        self,
        knowledge_id: UUID,
        max_depth: int = 2
    ) -> List[KnowledgeNode]:
        """
        Get related knowledge via graph traversal.

        Uses knowledge_relationships table to find connected concepts.

        Args:
            knowledge_id: Starting knowledge node ID
            max_depth: Maximum traversal depth (default: 2)

        Returns:
            List of related knowledge nodes
        """
        # Recursive CTE for graph traversal
        query = f"""
            WITH RECURSIVE related_nodes AS (
                -- Base case: direct relationships
                SELECT to_node_id, 1 as depth
                FROM knowledge_relationships
                WHERE from_node_id = $1

                UNION

                -- Recursive case: traverse deeper
                SELECT kr.to_node_id, rn.depth + 1
                FROM knowledge_relationships kr
                INNER JOIN related_nodes rn ON kr.from_node_id = rn.to_node_id
                WHERE rn.depth < $2
            )
            SELECT DISTINCT kn.*
            FROM {self.table_name} kn
            INNER JOIN related_nodes rn ON kn.node_id = rn.to_node_id
            ORDER BY kn.understanding_level DESC, kn.times_referenced DESC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, knowledge_id, max_depth)

        return [self._row_to_entity(row) for row in rows]

    # =========================================================================
    # Dashboard-Specific Methods (Added for Batch-22 Repository Enhancement)
    # =========================================================================

    async def count_nodes(self) -> int:
        """
        Count total knowledge nodes.

        Returns:
            Total number of knowledge nodes

        Example:
            >>> total = await repo.count_nodes()
            >>> print(f"Knowledge nodes: {total}")
            Knowledge nodes: 6734
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)

        return result or 0

    async def count_relationships(self) -> int:
        """
        Count total knowledge relationships.

        Returns:
            Total number of knowledge relationships (edges in graph)

        Example:
            >>> total = await repo.count_relationships()
            >>> print(f"Knowledge connections: {total}")
            Knowledge connections: 4851
        """
        query = "SELECT COUNT(*) FROM knowledge_relationships"

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)

        return result or 0

    async def count_categories(self) -> int:
        """
        Count distinct knowledge categories.

        Returns:
            Number of unique concept categories

        Example:
            >>> total = await repo.count_categories()
            >>> print(f"Knowledge categories: {total}")
            Knowledge categories: 30
        """
        query = f"""
            SELECT COUNT(DISTINCT concept_category)
            FROM {self.table_name}
            WHERE concept_category IS NOT NULL
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query)

        return result or 0

    # ========================================================================
    # KNOWLEDGE GRAPH METHODS (Added for Batch-25)
    # ========================================================================

    async def get_graph_with_edges(
        self,
        max_nodes: int = 200
    ) -> Dict[str, Any]:
        """
        Get knowledge graph with nodes and edges for visualization.

        Returns nodes with their relationships, suitable for graph visualization
        tools like D3.js.

        Args:
            max_nodes: Maximum number of nodes to return (default: 200)

        Returns:
            Dictionary with 'nodes' and 'edges' lists

        Example:
            >>> graph = await repo.get_graph_with_edges(max_nodes=100)
            >>> print(f"Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")
            Nodes: 100, Edges: 234
        """
        # Get nodes (limit for performance)
        nodes_query = f"""
            SELECT
                node_id,
                concept_name,
                concept_category,
                my_understanding,
                why_important,
                understanding_level,
                times_referenced,
                created_at
            FROM {self.table_name}
            ORDER BY times_referenced DESC, created_at DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            nodes_rows = await conn.fetch(nodes_query, max_nodes)

            # Get node IDs for filtering edges
            node_ids = [str(row['node_id']) for row in nodes_rows]

            # Get edges (only edges between loaded nodes)
            edges_rows = []
            if node_ids:
                edges_query = """
                    SELECT
                        relationship_id,
                        from_node_id,
                        to_node_id,
                        relationship_type,
                        strength,
                        my_explanation
                    FROM knowledge_relationships
                    WHERE from_node_id::text = ANY($1)
                      AND to_node_id::text = ANY($1)
                """
                edges_rows = await conn.fetch(edges_query, node_ids)

        # Convert rows to dictionaries
        nodes = [dict(row) for row in nodes_rows]
        edges = [dict(row) for row in edges_rows]

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive knowledge graph statistics.

        Returns:
            Dictionary with graph statistics including node count, edge count,
            categories, average understanding, and most referenced node

        Example:
            >>> stats = await repo.get_graph_statistics()
            >>> print(f"Total nodes: {stats['total_nodes']}")
            Total nodes: 482
        """
        async with self.db.acquire() as conn:
            # Total nodes
            total_nodes = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self.table_name}"
            )

            # Total edges
            total_edges = await conn.fetchval(
                "SELECT COUNT(*) FROM knowledge_relationships"
            )

            # Categories
            categories_rows = await conn.fetch(
                f"""
                SELECT DISTINCT concept_category
                FROM {self.table_name}
                WHERE concept_category IS NOT NULL
                ORDER BY concept_category
                """
            )
            categories = [row['concept_category'] for row in categories_rows]

            # Average understanding level
            avg_understanding = await conn.fetchval(
                f"""
                SELECT AVG(understanding_level)
                FROM {self.table_name}
                WHERE understanding_level IS NOT NULL
                """
            )

            # Most referenced node
            most_ref_row = await conn.fetchrow(
                f"""
                SELECT concept_name, times_referenced
                FROM {self.table_name}
                ORDER BY times_referenced DESC
                LIMIT 1
                """
            )

        most_referenced = None
        if most_ref_row:
            most_referenced = {
                "name": most_ref_row['concept_name'],
                "references": most_ref_row['times_referenced']
            }

        return {
            "total_nodes": total_nodes or 0,
            "total_edges": total_edges or 0,
            "categories": categories,
            "avg_understanding": float(avg_understanding) if avg_understanding else None,
            "most_referenced": most_referenced
        }

    async def search_nodes(
        self,
        query_text: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge nodes by concept name.

        Performs case-insensitive text search on concept names, with optional
        category filtering.

        Args:
            query_text: Search query (will use ILIKE %query%)
            category: Optional category filter
            limit: Maximum number of results (default: 50)

        Returns:
            List of matching node dictionaries

        Example:
            >>> nodes = await repo.search_nodes("python", category="programming")
            >>> print(f"Found {len(nodes)} Python concepts")
            Found 15 Python concepts
        """
        if category:
            query = f"""
                SELECT
                    node_id,
                    concept_name,
                    concept_category,
                    my_understanding,
                    understanding_level,
                    times_referenced,
                    created_at
                FROM {self.table_name}
                WHERE concept_name ILIKE $1
                  AND concept_category = $2
                ORDER BY times_referenced DESC
                LIMIT $3
            """
            params = [f"%{query_text}%", category, limit]
        else:
            query = f"""
                SELECT
                    node_id,
                    concept_name,
                    concept_category,
                    my_understanding,
                    understanding_level,
                    times_referenced,
                    created_at
                FROM {self.table_name}
                WHERE concept_name ILIKE $1
                ORDER BY times_referenced DESC
                LIMIT $2
            """
            params = [f"%{query_text}%", limit]

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def get_subgraph(
        self,
        node_name: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get subgraph around a specific node.

        Retrieves a node and its connected neighbors up to the specified depth,
        useful for visualizing knowledge relationships around a concept.

        Args:
            node_name: Name of the central node
            depth: How many relationship levels to include (default: 2)

        Returns:
            Dictionary with 'center_node', 'nodes', and 'edges'

        Example:
            >>> subgraph = await repo.get_subgraph("Machine Learning", depth=2)
            >>> print(f"Center: {subgraph['center_node']['concept_name']}")
            Center: Machine Learning
        """
        async with self.db.acquire() as conn:
            # Find the center node
            center_node_row = await conn.fetchrow(
                f"""
                SELECT
                    node_id,
                    concept_name,
                    concept_category,
                    my_understanding,
                    why_important,
                    understanding_level,
                    times_referenced,
                    created_at
                FROM {self.table_name}
                WHERE concept_name = $1
                """,
                node_name
            )

            if not center_node_row:
                # Return empty subgraph if node not found
                return {
                    "center_node": None,
                    "nodes": [],
                    "edges": []
                }

            center_node_id = str(center_node_row['node_id'])

            # Get connected nodes (depth 1 - direct neighbors)
            # This gets both outgoing and incoming relationships
            connected_query = """
                SELECT DISTINCT node_id, concept_name, concept_category,
                       my_understanding, understanding_level, times_referenced,
                       created_at
                FROM knowledge_nodes
                WHERE node_id IN (
                    SELECT to_node_id FROM knowledge_relationships WHERE from_node_id = $1
                    UNION
                    SELECT from_node_id FROM knowledge_relationships WHERE to_node_id = $1
                )
            """
            connected_rows = await conn.fetch(connected_query, center_node_row['node_id'])

            # Get all relevant node IDs
            all_node_ids = [center_node_id] + [str(row['node_id']) for row in connected_rows]

            # Get edges between these nodes
            edges_query = """
                SELECT
                    relationship_id,
                    from_node_id,
                    to_node_id,
                    relationship_type,
                    strength,
                    my_explanation
                FROM knowledge_relationships
                WHERE from_node_id::text = ANY($1)
                   OR to_node_id::text = ANY($1)
            """
            edges_rows = await conn.fetch(edges_query, all_node_ids)

        # Build result
        nodes = [dict(center_node_row)] + [dict(row) for row in connected_rows]
        edges = [dict(row) for row in edges_rows]

        return {
            "center_node": dict(center_node_row),
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "depth": depth
            }
        }
