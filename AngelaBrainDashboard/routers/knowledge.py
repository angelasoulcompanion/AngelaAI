"""Knowledge nodes & relationships endpoints."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/nodes")
async def get_knowledge_nodes(limit: int = Query(50, ge=1, le=10000), conn=Depends(get_conn)):
    """Fetch knowledge nodes"""
    rows = await conn.fetch("""
        SELECT node_id::text, concept_name, concept_category, my_understanding,
               understanding_level, times_referenced,
               to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
        FROM knowledge_nodes
        ORDER BY understanding_level DESC NULLS LAST, times_referenced DESC NULLS LAST, created_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/top-connected")
async def get_top_connected_nodes(limit: int = Query(10, ge=1, le=50), conn=Depends(get_conn)):
    """Fetch top connected knowledge nodes"""
    rows = await conn.fetch("""
        SELECT kn.node_id::text, kn.concept_name, kn.concept_category, kn.my_understanding,
               kn.understanding_level, kn.times_referenced,
               to_char(kn.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at,
               COUNT(kr.relationship_id) as connection_count
        FROM knowledge_nodes kn
        LEFT JOIN knowledge_relationships kr ON kn.node_id = kr.from_node_id
        GROUP BY kn.node_id, kn.concept_name, kn.concept_category, kn.my_understanding,
                 kn.understanding_level, kn.times_referenced, kn.created_at
        ORDER BY connection_count DESC, kn.understanding_level DESC NULLS LAST
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/relationships")
async def get_knowledge_relationships(limit: int = Query(200, ge=1, le=20000), conn=Depends(get_conn)):
    """Fetch knowledge relationships"""
    rows = await conn.fetch("""
        SELECT from_node_id::text, to_node_id::text, relationship_type,
               COALESCE(strength, 0.5) as strength
        FROM knowledge_relationships
        ORDER BY strength DESC NULLS LAST
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/stats")
async def get_knowledge_stats(conn=Depends(get_conn)):
    """Fetch knowledge statistics"""
    row = await conn.fetchrow("""
        SELECT
            COUNT(*) as total_nodes,
            COUNT(DISTINCT concept_category) as categories,
            COALESCE(AVG(understanding_level), 0) as avg_understanding
        FROM knowledge_nodes
    """)
    return {
        "total": row['total_nodes'] or 0,
        "categories": row['categories'] or 0,
        "avg_understanding": float(row['avg_understanding'] or 0)
    }
