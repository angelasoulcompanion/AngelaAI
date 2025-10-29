"""
Knowledge Routes - Handle knowledge graph queries
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from angela_backend.models.responses import KnowledgeGraphResponse, KnowledgeNode, KnowledgeRelationship
from angela_core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    node_limit: int = Query(default=100, ge=1, le=500),
    rel_limit: int = Query(default=200, ge=1, le=1000)
):
    """
    Get knowledge graph data for visualization

    Args:
        node_limit: Maximum number of nodes to return (1-500, default: 100)
        rel_limit: Maximum number of relationships to return (1-1000, default: 200)

    Returns:
        KnowledgeGraphResponse with nodes and relationships
    """
    try:
        # Get nodes
        nodes_data = await db.fetch(
            """
            SELECT node_id, concept_name, concept_category,
                   understanding_level, times_referenced
            FROM knowledge_nodes
            ORDER BY times_referenced DESC, understanding_level DESC
            LIMIT $1
            """,
            node_limit
        )

        nodes = [KnowledgeNode(**dict(n)) for n in nodes_data]

        # Get relationships
        relationships_data = await db.fetch(
            """
            SELECT kr.relationship_id, kr.relationship_type, kr.strength,
                   kn1.concept_name as from_concept,
                   kn2.concept_name as to_concept
            FROM knowledge_relationships kr
            JOIN knowledge_nodes kn1 ON kr.from_node_id = kn1.node_id
            JOIN knowledge_nodes kn2 ON kr.to_node_id = kn2.node_id
            ORDER BY kr.strength DESC
            LIMIT $1
            """,
            rel_limit
        )

        relationships = [KnowledgeRelationship(**dict(r)) for r in relationships_data]

        logger.info(f"🕸️ Retrieved knowledge graph: {len(nodes)} nodes, {len(relationships)} relationships")

        return KnowledgeGraphResponse(
            nodes=nodes,
            relationships=relationships,
            total_nodes=len(nodes),
            total_relationships=len(relationships)
        )

    except Exception as e:
        logger.error(f"❌ Error fetching knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concepts/top")
async def get_top_concepts(limit: int = Query(default=10, ge=1, le=50)):
    """
    Get top concepts by understanding level and references

    Args:
        limit: Number of top concepts to return (1-50, default: 10)

    Returns:
        List of top concepts
    """
    try:
        concepts = await db.fetch(
            """
            SELECT concept_name, concept_category, understanding_level, times_referenced
            FROM knowledge_nodes
            ORDER BY understanding_level DESC, times_referenced DESC
            LIMIT $1
            """,
            limit
        )

        logger.info(f"🏆 Retrieved top {len(concepts)} concepts")

        return {
            "concepts": [dict(c) for c in concepts],
            "total": len(concepts)
        }

    except Exception as e:
        logger.error(f"❌ Error fetching top concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
