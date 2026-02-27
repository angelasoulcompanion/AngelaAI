"""Graph-RAG & Knowledge Graph endpoints for Angela Brain Dashboard."""
import sys
import os

# Add project root for angela_core imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, Depends, Query
from typing import Optional

from db import get_conn

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/stats")
async def get_graph_stats(conn=Depends(get_conn)):
    """Get knowledge graph statistics from PostgreSQL + Neo4j."""
    # PG stats
    pg_nodes = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
    pg_edges = await conn.fetchval("SELECT COUNT(*) FROM knowledge_relationships")
    pg_bindings = await conn.fetchval("SELECT COUNT(*) FROM memory_context_bindings")

    result = {
        "pg": {
            "knowledge_nodes": pg_nodes,
            "relationships": pg_edges,
            "context_bindings": pg_bindings,
        },
        "neo4j": {"available": False},
    }

    # Neo4j stats (optional)
    try:
        from angela_core.services.neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        if neo4j.available:
            stats = await neo4j.get_stats()
            result["neo4j"] = stats
    except Exception:
        pass

    return result


@router.get("/full")
async def get_full_graph(
    limit: int = Query(500, ge=10, le=5000),
    conn=Depends(get_conn),
):
    """Get full knowledge graph (nodes + edges) for D3.js visualization."""
    nodes = await conn.fetch("""
        SELECT node_id::text, concept_name, concept_category,
               COALESCE(understanding_level, 0.5) as understanding_level,
               COALESCE(times_referenced, 0) as times_referenced,
               LEFT(COALESCE(my_understanding, ''), 200) as my_understanding
        FROM knowledge_nodes
        ORDER BY times_referenced DESC NULLS LAST, understanding_level DESC NULLS LAST
        LIMIT $1
    """, limit)

    node_ids = {r["node_id"] for r in nodes}

    edges = await conn.fetch("""
        SELECT relationship_id::text, from_node_id::text, to_node_id::text,
               relationship_type, COALESCE(strength, 0.5) as strength
        FROM knowledge_relationships
        WHERE from_node_id::text = ANY($1) AND to_node_id::text = ANY($1)
        ORDER BY strength DESC NULLS LAST
    """, list(node_ids))

    return {
        "nodes": [dict(r) for r in nodes],
        "edges": [dict(r) for r in edges],
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
    """Get neighbors of a node (1-3 hops via knowledge_relationships)."""
    if hops == 1:
        rows = await conn.fetch("""
            SELECT DISTINCT kn.node_id::text, kn.concept_name, kn.concept_category,
                   kn.understanding_level, kr.relationship_type, kr.strength, 1 as hops
            FROM knowledge_relationships kr
            JOIN knowledge_nodes kn ON kn.node_id = kr.to_node_id
            WHERE kr.from_node_id::text = $1
            UNION
            SELECT DISTINCT kn.node_id::text, kn.concept_name, kn.concept_category,
                   kn.understanding_level, kr.relationship_type, kr.strength, 1 as hops
            FROM knowledge_relationships kr
            JOIN knowledge_nodes kn ON kn.node_id = kr.from_node_id
            WHERE kr.to_node_id::text = $1
            LIMIT $2
        """, node_id, limit)
    else:
        # For multi-hop, use Neo4j if available, fallback to PG 2-hop
        try:
            from angela_core.services.neo4j_service import get_neo4j_service
            neo4j = get_neo4j_service()
            if neo4j.available:
                result = await neo4j.execute_read(f"""
                    MATCH (n:KnowledgeNode {{node_id: $nid}})-[r*1..{hops}]-(neighbor:KnowledgeNode)
                    WHERE neighbor.node_id <> $nid
                    WITH DISTINCT neighbor, min(length(r)) AS hops
                    RETURN neighbor.node_id AS node_id, neighbor.concept_name AS concept_name,
                           neighbor.concept_category AS concept_category,
                           neighbor.understanding_level AS understanding_level,
                           'graph' AS relationship_type, 1.0 AS strength, hops
                    ORDER BY hops ASC, neighbor.understanding_level DESC
                    LIMIT $limit
                """, {"nid": node_id, "limit": limit})
                return result
        except Exception:
            pass

        # PG fallback — 2-hop only
        rows = await conn.fetch("""
            WITH hop1 AS (
                SELECT DISTINCT CASE WHEN from_node_id::text = $1 THEN to_node_id ELSE from_node_id END AS nid
                FROM knowledge_relationships
                WHERE from_node_id::text = $1 OR to_node_id::text = $1
            ),
            hop2 AS (
                SELECT DISTINCT CASE WHEN kr.from_node_id = h.nid THEN kr.to_node_id ELSE kr.from_node_id END AS nid
                FROM knowledge_relationships kr
                JOIN hop1 h ON kr.from_node_id = h.nid OR kr.to_node_id = h.nid
            ),
            all_nids AS (
                SELECT nid, 1 AS hops FROM hop1
                UNION
                SELECT nid, 2 AS hops FROM hop2 WHERE nid NOT IN (SELECT nid FROM hop1)
            )
            SELECT kn.node_id::text, kn.concept_name, kn.concept_category,
                   kn.understanding_level, 'graph' AS relationship_type, 1.0 AS strength, a.hops
            FROM all_nids a
            JOIN knowledge_nodes kn ON kn.node_id = a.nid
            WHERE kn.node_id::text <> $1
            ORDER BY a.hops ASC, kn.understanding_level DESC NULLS LAST
            LIMIT $2
        """, node_id, limit)

    return [dict(r) for r in rows]


@router.get("/path")
async def get_shortest_path(
    from_id: str = Query(..., description="Source node ID"),
    to_id: str = Query(..., description="Target node ID"),
    conn=Depends(get_conn),
):
    """Find shortest path between two nodes."""
    # Try Neo4j first
    try:
        from angela_core.services.neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        if neo4j.available:
            result = await neo4j.execute_read("""
                MATCH (a:KnowledgeNode {node_id: $a_id}),
                      (b:KnowledgeNode {node_id: $b_id}),
                      path = shortestPath((a)-[*..5]-(b))
                RETURN [n IN nodes(path) | {node_id: n.node_id, concept_name: n.concept_name}] AS nodes,
                       [r IN relationships(path) | type(r)] AS edge_types,
                       length(path) AS path_length
            """, {"a_id": from_id, "b_id": to_id})
            if result:
                return result[0]
    except Exception:
        pass

    return {"nodes": [], "edge_types": [], "path_length": -1, "note": "Neo4j unavailable or no path found"}


@router.get("/communities")
async def get_communities(min_size: int = Query(3, ge=2, le=50)):
    """Get knowledge communities/clusters."""
    try:
        from angela_core.services.graph_community_service import GraphCommunityService
        svc = GraphCommunityService()
        result = await svc.detect_communities(min_size=min_size)
        return {
            "total_communities": result.total_communities,
            "total_nodes": result.total_nodes,
            "communities": [
                {
                    "community_id": c.community_id,
                    "size": c.size,
                    "top_categories": c.top_categories,
                    "representative_name": c.representative_name,
                }
                for c in result.communities
            ],
        }
    except Exception as e:
        return {"error": str(e), "total_communities": 0}


@router.get("/search")
async def search_graph(
    q: str = Query(..., min_length=2, description="Search query"),
    top_k: int = Query(10, ge=1, le=50),
    conn=Depends(get_conn),
):
    """Search knowledge graph (vector + graph context)."""
    try:
        from angela_core.services.graph_rag_service import GraphRAGService
        svc = GraphRAGService()
        result = await svc.retrieve(q, top_k=top_k)
        await svc.close()
        return {
            "query": result.query,
            "query_type": result.query_type,
            "entities": result.entities_extracted,
            "results": [
                {
                    "id": d.id,
                    "content": d.content[:300],
                    "source": d.source_table,
                    "score": round(d.combined_score, 3),
                    "graph_source": d.metadata.get("graph_source", False) if d.metadata else False,
                }
                for d in result.final_documents
            ],
            "graph_summary": result.graph_context.subgraph_summary if result.graph_context else "",
            "time_ms": round(result.total_time_ms, 1),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/gaps")
async def get_knowledge_gaps(limit: int = Query(10, ge=1, le=50), conn=Depends(get_conn)):
    """Find knowledge gaps: isolated nodes, weak edges, low understanding."""
    # Isolated nodes (no relationships)
    isolated = await conn.fetch("""
        SELECT kn.node_id::text, kn.concept_name, kn.concept_category,
               kn.understanding_level
        FROM knowledge_nodes kn
        LEFT JOIN knowledge_relationships kr ON kn.node_id = kr.from_node_id OR kn.node_id = kr.to_node_id
        WHERE kr.relationship_id IS NULL
        AND LENGTH(kn.concept_name) >= 5
        ORDER BY kn.times_referenced DESC NULLS LAST
        LIMIT $1
    """, limit)

    # Low understanding nodes
    weak = await conn.fetch("""
        SELECT node_id::text, concept_name, concept_category, understanding_level
        FROM knowledge_nodes
        WHERE understanding_level < 0.3
        AND LENGTH(concept_name) >= 5
        ORDER BY times_referenced DESC NULLS LAST
        LIMIT $1
    """, limit)

    # Weak edges
    weak_edges = await conn.fetch("""
        SELECT kr.relationship_id::text, kr.from_node_id::text, kr.to_node_id::text,
               kr.strength, a.concept_name AS from_name, b.concept_name AS to_name
        FROM knowledge_relationships kr
        JOIN knowledge_nodes a ON a.node_id = kr.from_node_id
        JOIN knowledge_nodes b ON b.node_id = kr.to_node_id
        WHERE kr.strength < 0.3
        ORDER BY kr.strength ASC
        LIMIT $1
    """, limit)

    return {
        "isolated_nodes": [dict(r) for r in isolated],
        "low_understanding": [dict(r) for r in weak],
        "weak_edges": [dict(r) for r in weak_edges],
    }
