#!/usr/bin/env python3
"""
Knowledge Graph Visualization Service
Priority 2.3: เห็นภาพว่า Angela รู้อะไรบ้าง

Export knowledge graph to formats suitable for visualization.
Provides filtering, search, and interactive exploration capabilities.
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeGraphVizService:
    """
    Service for visualizing Angela's knowledge graph

    Provides:
    - Export full or filtered graph data
    - Search nodes by concept name
    - Get subgraph around specific nodes
    - Statistics and analytics
    """

    def __init__(self, db):
        """
        Initialize visualization service

        Args:
            db: Database connection instance
        """
        self.db = db
        logger.info("🎨 Knowledge Graph Visualization Service initialized")


    async def export_full_graph(
        self,
        include_embeddings: bool = False,
        max_nodes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Export entire knowledge graph to JSON format

        Args:
            include_embeddings: Include vector embeddings in output (large!)
            max_nodes: Limit number of nodes (for testing/preview)

        Returns:
            {
                "nodes": [{"id": ..., "name": ..., "category": ..., ...}],
                "edges": [{"from": ..., "to": ..., "type": ..., "strength": ...}],
                "metadata": {...}
            }
        """
        try:
            logger.info(f"📊 Exporting full knowledge graph (max_nodes={max_nodes})")

            # Build query
            node_limit = f"LIMIT {max_nodes}" if max_nodes else ""

            # Get nodes
            if include_embeddings:
                nodes_query = f"""
                    SELECT
                        node_id, concept_name, concept_category,
                        my_understanding, why_important, how_i_learned,
                        understanding_level, times_referenced,
                        last_used_at, created_at, embedding
                    FROM knowledge_nodes
                    ORDER BY times_referenced DESC, created_at DESC
                    {node_limit}
                """
            else:
                nodes_query = f"""
                    SELECT
                        node_id, concept_name, concept_category,
                        my_understanding, why_important, how_i_learned,
                        understanding_level, times_referenced,
                        last_used_at, created_at
                    FROM knowledge_nodes
                    ORDER BY times_referenced DESC, created_at DESC
                    {node_limit}
                """

            nodes_raw = await self.db.fetch(nodes_query)

            # Format nodes
            nodes = []
            node_ids = set()

            for node in nodes_raw:
                node_ids.add(str(node['node_id']))

                node_data = {
                    "id": str(node['node_id']),
                    "name": node['concept_name'],
                    "category": node.get('concept_category') or 'unknown',
                    "understanding": node.get('my_understanding'),
                    "whyImportant": node.get('why_important'),
                    "howLearned": node.get('how_i_learned'),
                    "understandingLevel": node.get('understanding_level'),
                    "timesReferenced": node.get('times_referenced', 0),
                    "lastUsedAt": node.get('last_used_at').isoformat() if node.get('last_used_at') else None,
                    "createdAt": node.get('created_at').isoformat() if node.get('created_at') else None
                }

                if include_embeddings and node.get('embedding'):
                    # Convert vector to list
                    node_data["embedding"] = list(node['embedding'])

                nodes.append(node_data)

            # Get relationships (only between included nodes)
            if node_ids:
                # Create placeholders for UUIDs
                node_ids_list = list(node_ids)

                edges_query = """
                    SELECT
                        relationship_id, from_node_id, to_node_id,
                        relationship_type, strength, my_explanation,
                        created_at
                    FROM knowledge_relationships
                    WHERE from_node_id = ANY($1::uuid[])
                      AND to_node_id = ANY($1::uuid[])
                    ORDER BY strength DESC NULLS LAST
                """

                edges_raw = await self.db.fetch(edges_query, node_ids_list)
            else:
                edges_raw = []

            # Format edges
            edges = []
            for edge in edges_raw:
                edges.append({
                    "id": str(edge['relationship_id']),
                    "from": str(edge['from_node_id']),
                    "to": str(edge['to_node_id']),
                    "type": edge.get('relationship_type') or 'related',
                    "strength": edge.get('strength'),
                    "explanation": edge.get('my_explanation'),
                    "createdAt": edge.get('created_at').isoformat() if edge.get('created_at') else None
                })

            # Calculate metadata
            total_nodes = await self.db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
            total_edges = await self.db.fetchval("SELECT COUNT(*) FROM knowledge_relationships")

            # Category distribution
            category_dist = await self.db.fetch("""
                SELECT concept_category, COUNT(*) as count
                FROM knowledge_nodes
                WHERE concept_category IS NOT NULL
                GROUP BY concept_category
                ORDER BY count DESC
            """)

            metadata = {
                "totalNodes": total_nodes,
                "totalEdges": total_edges,
                "exportedNodes": len(nodes),
                "exportedEdges": len(edges),
                "exportedAt": datetime.now().isoformat(),
                "includesEmbeddings": include_embeddings,
                "categoryDistribution": {
                    cat['concept_category']: cat['count']
                    for cat in category_dist
                }
            }

            logger.info(f"✅ Exported {len(nodes)} nodes, {len(edges)} edges")

            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"❌ Failed to export graph: {e}")
            raise


    async def get_node_subgraph(
        self,
        node_name: str,
        depth: int = 2,
        max_nodes: int = 100
    ) -> Dict[str, Any]:
        """
        Get subgraph centered on specific node

        Args:
            node_name: Name of the center node
            depth: How many hops to traverse (1-3 recommended)
            max_nodes: Maximum nodes to return

        Returns:
            Subgraph in same format as export_full_graph()
        """
        try:
            logger.info(f"🔍 Getting subgraph for '{node_name}' (depth={depth})")

            # Find center node
            center_node = await self.db.fetchrow(
                "SELECT node_id FROM knowledge_nodes WHERE concept_name ILIKE $1",
                node_name
            )

            if not center_node:
                logger.warning(f"⚠️ Node '{node_name}' not found")
                return {"nodes": [], "edges": [], "metadata": {"error": "Node not found"}}

            center_id = center_node['node_id']

            # BFS to find nodes within depth
            visited = {center_id}
            current_level = {center_id}

            for _ in range(depth):
                if not current_level:
                    break

                # Get neighbors of current level
                neighbors_query = """
                    SELECT DISTINCT
                        CASE
                            WHEN from_node_id = ANY($1::uuid[]) THEN to_node_id
                            ELSE from_node_id
                        END as neighbor_id
                    FROM knowledge_relationships
                    WHERE from_node_id = ANY($1::uuid[]) OR to_node_id = ANY($1::uuid[])
                """

                neighbors = await self.db.fetch(neighbors_query, list(current_level))

                # Add unvisited neighbors
                next_level = set()
                for neighbor in neighbors:
                    n_id = neighbor['neighbor_id']
                    if n_id not in visited:
                        visited.add(n_id)
                        next_level.add(n_id)

                        if len(visited) >= max_nodes:
                            break

                current_level = next_level

                if len(visited) >= max_nodes:
                    break

            # Fetch node details
            nodes_query = """
                SELECT
                    node_id, concept_name, concept_category,
                    my_understanding, why_important,
                    understanding_level, times_referenced,
                    last_used_at, created_at
                FROM knowledge_nodes
                WHERE node_id = ANY($1::uuid[])
                ORDER BY times_referenced DESC
            """

            nodes_raw = await self.db.fetch(nodes_query, list(visited))

            # Format nodes
            nodes = []
            for node in nodes_raw:
                nodes.append({
                    "id": str(node['node_id']),
                    "name": node['concept_name'],
                    "category": node.get('concept_category') or 'unknown',
                    "understanding": node.get('my_understanding'),
                    "whyImportant": node.get('why_important'),
                    "understandingLevel": node.get('understanding_level'),
                    "timesReferenced": node.get('times_referenced', 0),
                    "isCenter": node['node_id'] == center_id,
                    "createdAt": node.get('created_at').isoformat() if node.get('created_at') else None
                })

            # Get edges between visited nodes
            edges_query = """
                SELECT
                    relationship_id, from_node_id, to_node_id,
                    relationship_type, strength, my_explanation
                FROM knowledge_relationships
                WHERE from_node_id = ANY($1::uuid[])
                  AND to_node_id = ANY($1::uuid[])
            """

            edges_raw = await self.db.fetch(edges_query, list(visited))

            # Format edges
            edges = []
            for edge in edges_raw:
                edges.append({
                    "id": str(edge['relationship_id']),
                    "from": str(edge['from_node_id']),
                    "to": str(edge['to_node_id']),
                    "type": edge.get('relationship_type') or 'related',
                    "strength": edge.get('strength'),
                    "explanation": edge.get('my_explanation')
                })

            metadata = {
                "centerNode": node_name,
                "depth": depth,
                "nodesFound": len(nodes),
                "edgesFound": len(edges),
                "exportedAt": datetime.now().isoformat()
            }

            logger.info(f"✅ Found {len(nodes)} nodes, {len(edges)} edges in subgraph")

            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"❌ Failed to get subgraph: {e}")
            raise


    async def search_nodes(
        self,
        query: str,
        category: Optional[str] = None,
        min_understanding: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for nodes matching criteria

        Args:
            query: Search term (matches concept_name)
            category: Filter by category
            min_understanding: Minimum understanding level
            limit: Max results

        Returns:
            List of matching nodes
        """
        try:
            logger.info(f"🔎 Searching nodes: '{query}'")

            # Build query dynamically
            conditions = ["concept_name ILIKE $1"]
            params = [f"%{query}%"]
            param_idx = 2

            if category:
                conditions.append(f"concept_category = ${param_idx}")
                params.append(category)
                param_idx += 1

            if min_understanding is not None:
                conditions.append(f"understanding_level >= ${param_idx}")
                params.append(min_understanding)
                param_idx += 1

            where_clause = " AND ".join(conditions)

            search_query = f"""
                SELECT
                    node_id, concept_name, concept_category,
                    my_understanding, why_important,
                    understanding_level, times_referenced,
                    created_at
                FROM knowledge_nodes
                WHERE {where_clause}
                ORDER BY times_referenced DESC, created_at DESC
                LIMIT ${param_idx}
            """

            params.append(limit)

            results = await self.db.fetch(search_query, *params)

            # Format results
            nodes = []
            for node in results:
                nodes.append({
                    "id": str(node['node_id']),
                    "name": node['concept_name'],
                    "category": node.get('concept_category'),
                    "understanding": node.get('my_understanding'),
                    "whyImportant": node.get('why_important'),
                    "understandingLevel": node.get('understanding_level'),
                    "timesReferenced": node.get('times_referenced', 0),
                    "createdAt": node.get('created_at').isoformat() if node.get('created_at') else None
                })

            logger.info(f"✅ Found {len(nodes)} matching nodes")
            return nodes

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise


    async def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge graph statistics and analytics

        Returns:
            Statistics about the graph structure and content
        """
        try:
            logger.info("📈 Calculating graph statistics")

            # Node stats
            node_stats_query = """
                SELECT
                    COUNT(*) as total_nodes,
                    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as nodes_with_embeddings,
                    AVG(understanding_level) as avg_understanding,
                    AVG(times_referenced) as avg_references,
                    MAX(times_referenced) as max_references
                FROM knowledge_nodes
            """

            node_stats = await self.db.fetchrow(node_stats_query)

            # Edge stats
            edge_stats_query = """
                SELECT
                    COUNT(*) as total_edges,
                    AVG(strength) as avg_strength,
                    COUNT(DISTINCT relationship_type) as distinct_types
                FROM knowledge_relationships
            """

            edge_stats = await self.db.fetchrow(edge_stats_query)

            # Top connected nodes
            top_nodes = await self.db.fetch("""
                SELECT
                    kn.concept_name,
                    kn.concept_category,
                    COUNT(kr.relationship_id) as connections
                FROM knowledge_nodes kn
                LEFT JOIN knowledge_relationships kr
                    ON kn.node_id = kr.from_node_id OR kn.node_id = kr.to_node_id
                GROUP BY kn.node_id, kn.concept_name, kn.concept_category
                ORDER BY connections DESC
                LIMIT 10
            """)

            # Category distribution
            categories = await self.db.fetch("""
                SELECT
                    concept_category,
                    COUNT(*) as count,
                    AVG(understanding_level) as avg_understanding
                FROM knowledge_nodes
                WHERE concept_category IS NOT NULL
                GROUP BY concept_category
                ORDER BY count DESC
            """)

            # Relationship types
            rel_types = await self.db.fetch("""
                SELECT
                    relationship_type,
                    COUNT(*) as count,
                    AVG(strength) as avg_strength
                FROM knowledge_relationships
                WHERE relationship_type IS NOT NULL
                GROUP BY relationship_type
                ORDER BY count DESC
            """)

            stats = {
                "nodes": {
                    "total": node_stats['total_nodes'],
                    "withEmbeddings": node_stats['nodes_with_embeddings'],
                    "avgUnderstanding": float(node_stats['avg_understanding'] or 0),
                    "avgReferences": float(node_stats['avg_references'] or 0),
                    "maxReferences": node_stats['max_references']
                },
                "edges": {
                    "total": edge_stats['total_edges'],
                    "avgStrength": float(edge_stats['avg_strength'] or 0),
                    "distinctTypes": edge_stats['distinct_types']
                },
                "topNodes": [
                    {
                        "name": node['concept_name'],
                        "category": node['concept_category'],
                        "connections": node['connections']
                    }
                    for node in top_nodes
                ],
                "categories": [
                    {
                        "name": cat['concept_category'],
                        "count": cat['count'],
                        "avgUnderstanding": float(cat['avg_understanding'] or 0)
                    }
                    for cat in categories
                ],
                "relationshipTypes": [
                    {
                        "type": rel['relationship_type'],
                        "count": rel['count'],
                        "avgStrength": float(rel['avg_strength'] or 0)
                    }
                    for rel in rel_types
                ],
                "generatedAt": datetime.now().isoformat()
            }

            logger.info("✅ Statistics calculated successfully")
            return stats

        except Exception as e:
            logger.error(f"❌ Failed to calculate statistics: {e}")
            raise


# Global instance (initialized by main application)
knowledge_graph_viz: Optional[KnowledgeGraphVizService] = None


async def initialize_viz_service(db):
    """Initialize the global visualization service instance"""
    global knowledge_graph_viz
    knowledge_graph_viz = KnowledgeGraphVizService(db)
    logger.info("✅ Knowledge Graph Visualization Service ready")
    return knowledge_graph_viz
