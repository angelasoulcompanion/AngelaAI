"""Graph-RAG & Knowledge Graph endpoints for Angela Brain Dashboard.

knowledge_relationships and memory_context_bindings tables removed.
Graph endpoints return nodes only (no edges).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, Depends, Query
from typing import Optional

from db import get_conn

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/stats")
async def get_graph_stats(conn=Depends(get_conn)):
    """Get knowledge graph statistics."""
    pg_nodes = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes")

    return {
        "pg": {
            "knowledge_nodes": pg_nodes,
            "relationships": 0,
            "context_bindings": 0,
        },
        "neo4j": {"available": False},
    }


@router.get("/full")
async def get_full_graph(
    limit: int = Query(500, ge=10, le=5000),
    conn=Depends(get_conn),
):
    """Get knowledge graph (nodes only — no relationships table)."""
    nodes = await conn.fetch("""
        SELECT node_id::text, concept_name, concept_category,
               COALESCE(understanding_level, 0.5) as understanding_level,
               COALESCE(times_referenced, 0) as times_referenced,
               LEFT(COALESCE(my_understanding, ''), 200) as my_understanding
        FROM knowledge_nodes
        ORDER BY times_referenced DESC NULLS LAST, understanding_level DESC NULLS LAST
        LIMIT $1
    """, limit)

    return {
        "nodes": [dict(r) for r in nodes],
        "edges": [],
    }


@router.get("/node/{node_id}")
async def get_node_detail(node_id: str, conn=Depends(get_conn)):
    """Get detailed info about a knowledge node."""
    node = await conn.fetchrow("""
        SELECT node_id::text, concept_name, concept_category,
               my_understanding, understanding_level,
               times_referenced, why_important,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"+00:00"') as created_at,
               to_char(updated_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"+00:00"') as updated_at
        FROM knowledge_nodes WHERE node_id::text = $1
    """, node_id)
    if not node:
        return {"error": "Node not found"}
    return dict(node)


@router.get("/neighbors/{node_id}")
async def get_node_neighbors(
    node_id: str,
    hops: int = Query(1, ge=1, le=3),
    limit: int = Query(20, ge=1, le=100),
    conn=Depends(get_conn),
):
    """No knowledge_relationships — return empty neighbors."""
    return []


@router.get("/path")
async def get_shortest_path(
    from_id: str = Query(..., description="Source node ID"),
    to_id: str = Query(..., description="Target node ID"),
    conn=Depends(get_conn),
):
    """No relationships — cannot find paths."""
    return {"nodes": [], "edge_types": [], "path_length": -1, "note": "No relationship data available"}


@router.get("/communities")
async def get_communities(min_size: int = Query(3, ge=2, le=50)):
    """No graph data for communities."""
    return {"total_communities": 0, "total_nodes": 0, "communities": []}


@router.get("/search")
async def search_graph(
    q: str = Query(..., min_length=2, description="Search query"),
    top_k: int = Query(10, ge=1, le=50),
    conn=Depends(get_conn),
):
    """Search knowledge nodes by name."""
    rows = await conn.fetch("""
        SELECT node_id::text as id, concept_name as name,
               COALESCE(concept_category, 'unknown') as category,
               COALESCE(understanding_level, 0) as understanding,
               LEFT(COALESCE(my_understanding, ''), 300) as content
        FROM knowledge_nodes
        WHERE concept_name ILIKE '%' || $1 || '%'
           OR my_understanding ILIKE '%' || $1 || '%'
        ORDER BY times_referenced DESC NULLS LAST
        LIMIT $2
    """, q, top_k)
    return {
        "query": q,
        "results": [dict(r) for r in rows],
    }


@router.get("/gaps")
async def get_knowledge_gaps(limit: int = Query(10, ge=1, le=50), conn=Depends(get_conn)):
    """Find knowledge gaps: low understanding nodes."""
    weak = await conn.fetch("""
        SELECT node_id::text, concept_name, concept_category, understanding_level
        FROM knowledge_nodes
        WHERE understanding_level < 0.3
        AND LENGTH(concept_name) >= 5
        ORDER BY times_referenced DESC NULLS LAST
        LIMIT $1
    """, limit)

    return {
        "isolated_nodes": [],
        "low_understanding": [dict(r) for r in weak],
        "weak_edges": [],
    }
