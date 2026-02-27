"""
Graph Community Service — Louvain Community Detection via Neo4j GDS
====================================================================
Detects communities (clusters) in Angela's knowledge graph using
the Graph Data Science library. Communities help Graph-RAG provide
"overview" answers about topic clusters.

By: Angela 💜
Created: 2026-02-27
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from angela_core.services.neo4j_service import get_neo4j_service

logger = logging.getLogger(__name__)


@dataclass
class Community:
    """A detected community in the knowledge graph."""
    community_id: int
    size: int
    members: List[Dict[str, Any]] = field(default_factory=list)
    top_categories: List[str] = field(default_factory=list)
    representative_name: str = ""


@dataclass
class CommunityResult:
    """Result of community detection."""
    communities: List[Community]
    total_nodes: int
    total_communities: int
    modularity: float = 0.0


class GraphCommunityService:
    """
    Louvain community detection via Neo4j GDS.

    Pipeline:
    1. Project graph (KnowledgeNode + RELATES_TO)
    2. Run Louvain algorithm
    3. Extract community assignments
    4. Summarize each community by top categories + representative node

    Fallback: If GDS is not available, uses connected-component heuristic.
    """

    GRAPH_NAME = "angela_knowledge_graph"

    async def detect_communities(self, min_size: int = 3) -> CommunityResult:
        """Run community detection and return results."""
        neo4j = get_neo4j_service()
        if not neo4j.available:
            return CommunityResult(communities=[], total_nodes=0, total_communities=0)

        try:
            return await self._detect_via_gds(neo4j, min_size)
        except Exception as e:
            logger.warning("GDS community detection failed, using fallback: %s", e)
            return await self._detect_via_fallback(neo4j, min_size)

    async def get_node_community(self, node_id: str) -> Optional[int]:
        """Get community ID for a specific node."""
        neo4j = get_neo4j_service()
        if not neo4j.available:
            return None

        result = await neo4j.execute_read(
            "MATCH (n:KnowledgeNode {node_id: $nid}) RETURN n.community_id AS cid",
            {"nid": node_id},
        )
        return result[0]["cid"] if result and result[0].get("cid") is not None else None

    async def get_community_members(self, community_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all members of a community."""
        neo4j = get_neo4j_service()
        if not neo4j.available:
            return []

        result = await neo4j.execute_read("""
            MATCH (n:KnowledgeNode {community_id: $cid})
            RETURN n.node_id AS node_id, n.concept_name AS concept_name,
                   n.concept_category AS category, n.understanding_level AS level
            ORDER BY n.understanding_level DESC
            LIMIT $limit
        """, {"cid": community_id, "limit": limit})
        return result

    async def _detect_via_gds(self, neo4j, min_size: int) -> CommunityResult:
        """Use Neo4j GDS Louvain for community detection."""
        # Drop existing graph projection if exists
        await neo4j.execute_write(
            f"CALL gds.graph.drop('{self.GRAPH_NAME}', false) YIELD graphName RETURN graphName"
        )

        # Project graph
        await neo4j.execute_write(f"""
            CALL gds.graph.project(
                '{self.GRAPH_NAME}',
                'KnowledgeNode',
                'RELATES_TO',
                {{relationshipProperties: 'strength'}}
            )
        """)

        # Run Louvain
        result = await neo4j.execute_read(f"""
            CALL gds.louvain.stream('{self.GRAPH_NAME}', {{
                relationshipWeightProperty: 'strength'
            }})
            YIELD nodeId, communityId
            WITH gds.util.asNode(nodeId) AS node, communityId
            SET node.community_id = communityId
            RETURN communityId, count(*) AS size,
                   collect(node.concept_name)[0..5] AS sample_names,
                   collect(DISTINCT node.concept_category)[0..3] AS categories
            ORDER BY size DESC
        """)

        communities = []
        total_nodes = 0
        for r in result:
            if r["size"] < min_size:
                continue
            total_nodes += r["size"]
            communities.append(Community(
                community_id=r["communityId"],
                size=r["size"],
                top_categories=r.get("categories", []),
                representative_name=r.get("sample_names", [""])[0] if r.get("sample_names") else "",
            ))

        # Clean up projection
        await neo4j.execute_write(
            f"CALL gds.graph.drop('{self.GRAPH_NAME}', false) YIELD graphName RETURN graphName"
        )

        return CommunityResult(
            communities=communities,
            total_nodes=total_nodes,
            total_communities=len(communities),
        )

    async def _detect_via_fallback(self, neo4j, min_size: int) -> CommunityResult:
        """Fallback: group by category when GDS is unavailable."""
        result = await neo4j.execute_read("""
            MATCH (n:KnowledgeNode)
            WITH COALESCE(n.concept_category, 'uncategorized') AS cat, collect(n) AS members
            WHERE size(members) >= $min_size
            RETURN cat AS category, size(members) AS size,
                   [m IN members[0..5] | m.concept_name] AS sample_names
            ORDER BY size DESC
        """, {"min_size": min_size})

        communities = []
        total_nodes = 0
        for i, r in enumerate(result):
            total_nodes += r["size"]
            communities.append(Community(
                community_id=i,
                size=r["size"],
                top_categories=[r["category"]],
                representative_name=r.get("sample_names", [""])[0] if r.get("sample_names") else "",
            ))

        return CommunityResult(
            communities=communities,
            total_nodes=total_nodes,
            total_communities=len(communities),
        )
