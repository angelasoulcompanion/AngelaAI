from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from angela_core.database import db

router = APIRouter()

# Database connection config
DB_CONFIG = {
    "user": "davidsamanyaporn",
    "database": "AngelaMemory",
    "host": "localhost",
    "port": 5432
}

# =====================================================================
# Response Models
# =====================================================================

class KnowledgeNode(BaseModel):
    id: str
    name: str
    category: str
    understanding: Optional[str] = None
    whyImportant: Optional[str] = None
    understandingLevel: Optional[float] = None
    timesReferenced: int
    createdAt: str

class KnowledgeEdge(BaseModel):
    id: str
    source: str  # Changed from 'from' to 'source' for D3.js compatibility
    target: str  # Changed from 'to' to 'target' for D3.js compatibility
    type: str
    strength: Optional[float] = None
    explanation: Optional[str] = None

class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]
    metadata: Dict[str, Any]

class GraphStats(BaseModel):
    totalNodes: int
    totalEdges: int
    categories: List[str]
    avgUnderstanding: Optional[float] = None
    mostReferenced: Optional[Dict[str, Any]] = None

# =====================================================================
# API Endpoints
# =====================================================================

@router.get("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(max_nodes: Optional[int] = 200):
    """Get knowledge graph data with nodes and edges"""
    try:
        

        # Get nodes (limit for performance)
        nodes_query = """
            SELECT
                node_id::text as id,
                concept_name as name,
                concept_category as category,
                my_understanding as understanding,
                why_important as why_important,
                understanding_level,
                times_referenced,
                created_at::text
            FROM knowledge_nodes
            ORDER BY times_referenced DESC, created_at DESC
            LIMIT $1
        """

        nodes_rows = await db.fetch(nodes_query, max_nodes)

        # Get node IDs for filtering edges
        node_ids = [row['id'] for row in nodes_rows]

        # Get edges (only edges between loaded nodes)
        if node_ids:
            edges_query = """
                SELECT
                    relationship_id::text as id,
                    from_node_id::text as from_node,
                    to_node_id::text as to_node,
                    relationship_type as type,
                    strength,
                    my_explanation as explanation
                FROM knowledge_relationships
                WHERE from_node_id::text = ANY($1)
                  AND to_node_id::text = ANY($1)
            """
            edges_rows = await db.fetch(edges_query, node_ids)
        else:
            edges_rows = []        # Build nodes list
        nodes = [
            KnowledgeNode(
                id=row['id'],
                name=row['name'],
                category=row['category'] or 'uncategorized',
                understanding=row['understanding'],
                whyImportant=row['why_important'],
                understandingLevel=float(row['understanding_level']) if row['understanding_level'] else None,
                timesReferenced=row['times_referenced'] or 0,
                createdAt=row['created_at']
            )
            for row in nodes_rows
        ]

        # Build edges list (use 'source' and 'target' for D3.js compatibility)
        edges = [
            KnowledgeEdge(
                id=row['id'],
                source=row['from_node'],
                target=row['to_node'],
                type=row['type'] or 'related',
                strength=float(row['strength']) if row['strength'] else None,
                explanation=row['explanation']
            )
            for row in edges_rows
        ]

        # Metadata
        metadata = {
            "totalNodes": len(nodes),
            "totalEdges": len(edges),
            "exportedNodes": len(nodes),
            "exportedEdges": len(edges),
            "exportedAt": "now"
        }

        return KnowledgeGraphResponse(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch knowledge graph: {str(e)}")

@router.get("/knowledge-graph/stats", response_model=GraphStats)
async def get_graph_statistics():
    """Get knowledge graph statistics"""
    try:
        

        # Total nodes
        total_nodes = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")

        # Total edges
        total_edges = await db.fetchval("SELECT COUNT(*) FROM knowledge_relationships")

        # Categories
        categories_rows = await db.fetch(
            "SELECT DISTINCT concept_category FROM knowledge_nodes WHERE concept_category IS NOT NULL"
        )
        categories = [row['concept_category'] for row in categories_rows]

        # Average understanding level
        avg_understanding = await db.fetchval(
            "SELECT AVG(understanding_level) FROM knowledge_nodes WHERE understanding_level IS NOT NULL"
        )

        # Most referenced node
        most_ref_row = await db.fetchrow(
            """
            SELECT concept_name, times_referenced
            FROM knowledge_nodes
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

        return GraphStats(
            totalNodes=total_nodes or 0,
            totalEdges=total_edges or 0,
            categories=categories,
            avgUnderstanding=float(avg_understanding) if avg_understanding else None,
            mostReferenced=most_referenced
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph stats: {str(e)}")

@router.get("/knowledge-graph/search")
async def search_nodes(q: str, category: Optional[str] = None):
    """Search knowledge nodes"""
    try:
        

        if category:
            query = """
                SELECT
                    node_id::text as id,
                    concept_name as name,
                    concept_category as category,
                    my_understanding as understanding,
                    understanding_level,
                    times_referenced
                FROM knowledge_nodes
                WHERE concept_name ILIKE $1
                  AND concept_category = $2
                ORDER BY times_referenced DESC
                LIMIT 50
            """
            rows = await db.fetch(query, f"%{q}%", category)
        else:
            query = """
                SELECT
                    node_id::text as id,
                    concept_name as name,
                    concept_category as category,
                    my_understanding as understanding,
                    understanding_level,
                    times_referenced
                FROM knowledge_nodes
                WHERE concept_name ILIKE $1
                ORDER BY times_referenced DESC
                LIMIT 50
            """
            rows = await db.fetch(query, f"%{q}%")

        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search nodes: {str(e)}")

@router.get("/knowledge-graph/subgraph")
async def get_node_subgraph(node_name: str, depth: int = 2):
    """Get subgraph around a specific node"""
    try:
        

        # Find the node
        node = await db.fetchrow(
            "SELECT node_id::text as id FROM knowledge_nodes WHERE concept_name = $1",
            node_name
        )

        if not node:            raise HTTPException(status_code=404, detail=f"Node '{node_name}' not found")

        node_id = node['id']

        # Get connected nodes (simplified - just direct connections)
        connected_query = """
            WITH RECURSIVE connected_nodes AS (
                -- Start with the selected node
                SELECT node_id::text as id, 0 as depth
                FROM knowledge_nodes
                WHERE node_id::text = $1

                UNION

                -- Get connected nodes
                SELECT DISTINCT
                    CASE
                        WHEN kr.from_node_id::text = cn.id THEN kr.to_node_id::text
                        ELSE kr.from_node_id::text
                    END as id,
                    cn.depth + 1 as depth
                FROM connected_nodes cn
                JOIN knowledge_relationships kr ON (
                    kr.from_node_id::text = cn.id OR kr.to_node_id::text = cn.id
                )
                WHERE cn.depth < $2
            )
            SELECT DISTINCT
                kn.node_id::text as id,
                kn.concept_name as name,
                kn.concept_category as category,
                kn.my_understanding as understanding,
                kn.understanding_level,
                kn.times_referenced,
                kn.created_at::text
            FROM connected_nodes cn
            JOIN knowledge_nodes kn ON kn.node_id::text = cn.id
        """

        nodes_rows = await db.fetch(connected_query, node_id, depth)
        node_ids = [row['id'] for row in nodes_rows]

        # Get edges between these nodes
        if node_ids:
            edges_query = """
                SELECT
                    relationship_id::text as id,
                    from_node_id::text as from_node,
                    to_node_id::text as to_node,
                    relationship_type as type,
                    strength,
                    my_explanation as explanation
                FROM knowledge_relationships
                WHERE from_node_id::text = ANY($1)
                  AND to_node_id::text = ANY($1)
            """
            edges_rows = await db.fetch(edges_query, node_ids)
        else:
            edges_rows = []        # Build response
        nodes = [
            KnowledgeNode(
                id=row['id'],
                name=row['name'],
                category=row['category'] or 'uncategorized',
                understanding=row['understanding'],
                whyImportant=None,
                understandingLevel=float(row['understanding_level']) if row['understanding_level'] else None,
                timesReferenced=row['times_referenced'] or 0,
                createdAt=row['created_at']
            )
            for row in nodes_rows
        ]

        edges = [
            KnowledgeEdge(
                id=row['id'],
                source=row['from_node'],
                target=row['to_node'],
                type=row['type'] or 'related',
                strength=float(row['strength']) if row['strength'] else None,
                explanation=row['explanation']
            )
            for row in edges_rows
        ]

        return KnowledgeGraphResponse(
            nodes=nodes,
            edges=edges,
            metadata={
                "totalNodes": len(nodes),
                "totalEdges": len(edges),
                "centerNode": node_name,
                "depth": depth
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subgraph: {str(e)}")
