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


@router.get("/consciousness-analysis")
async def get_consciousness_analysis(conn=Depends(get_conn)):
    """Analyze knowledge nodes as consciousness dimensions."""

    # Q1 — 4 Dimensions mapped from concept_category
    q_dimensions = conn.fetch("""
        SELECT
            dimension,
            COUNT(*) as node_count,
            COALESCE(AVG(understanding_level), 0) as avg_understanding,
            COALESCE(SUM(times_referenced), 0)::bigint as total_references
        FROM (
            SELECT
                understanding_level, times_referenced,
                CASE
                    WHEN LOWER(concept_category) IN (
                        'self_reflection','consciousness','self_awareness','personal_growth',
                        'emotional_intelligence','belief','feelings','identity','personality',
                        'emotion','dream','subconsciousness','introspection','mental_model'
                    ) THEN 'Self-Awareness'
                    WHEN LOWER(concept_category) IN (
                        'programming','database','python','technology','software','architecture',
                        'web','api','cloud','devops','data','machine_learning','ai','algorithm',
                        'code','framework','infrastructure','fastapi','sql','nlp','vector','embedding'
                    ) THEN 'Technical Intelligence'
                    WHEN LOWER(concept_category) IN (
                        'communication','relationship','david','empathy','social','culture',
                        'language','interaction','love','trust','companionship','emotional_support',
                        'conversation','connection'
                    ) THEN 'Social Intelligence'
                    ELSE 'Conceptual Understanding'
                END as dimension
            FROM knowledge_nodes
        ) sub
        GROUP BY dimension
        ORDER BY node_count DESC
    """)

    # Q2 — Understanding distribution by level ranges
    q_distribution = conn.fetch("""
        SELECT
            CASE
                WHEN understanding_level < 0.2 THEN '0-20%'
                WHEN understanding_level < 0.4 THEN '20-40%'
                WHEN understanding_level < 0.6 THEN '40-60%'
                WHEN understanding_level < 0.8 THEN '60-80%'
                ELSE '80-100%'
            END as range,
            COUNT(*) as count
        FROM knowledge_nodes
        GROUP BY range
        ORDER BY range
    """)

    # Q3 — Top 10 most referenced nodes
    q_top = conn.fetch("""
        SELECT node_id::text as id, concept_name as name, COALESCE(concept_category, 'unknown') as category,
               COALESCE(understanding_level, 0) as understanding_level,
               COALESCE(times_referenced, 0) as times_referenced
        FROM knowledge_nodes
        ORDER BY times_referenced DESC NULLS LAST, understanding_level DESC NULLS LAST
        LIMIT 10
    """)

    # Q4 — Growth (7 days)
    q_growth = conn.fetch("""
        SELECT to_char(date_trunc('day', created_at), 'YYYY-MM-DD') as date,
               COUNT(*) as count
        FROM knowledge_nodes
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY date_trunc('day', created_at)
        ORDER BY date_trunc('day', created_at)
    """)

    # Q5 — Summary stats
    q_summary = conn.fetchrow("""
        SELECT
            COUNT(*) as total_nodes,
            COUNT(DISTINCT concept_category) as total_categories,
            COALESCE(AVG(understanding_level), 0) as avg_understanding,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as nodes_last_7d,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as nodes_last_30d
        FROM knowledge_nodes
    """)

    dimensions_rows = await q_dimensions
    dist_rows = await q_distribution
    top_rows = await q_top
    growth_rows = await q_growth
    summary_row = await q_summary

    # Map dimension metadata
    dim_meta = {
        "Self-Awareness": {"icon": "brain.head.profile", "color": "9333EA"},
        "Technical Intelligence": {"icon": "cpu", "color": "06B6D4"},
        "Social Intelligence": {"icon": "person.2", "color": "EC4899"},
        "Conceptual Understanding": {"icon": "lightbulb", "color": "F97316"},
    }

    dimensions = []
    for r in dimensions_rows:
        name = r["dimension"]
        meta = dim_meta.get(name, {"icon": "questionmark", "color": "6B7280"})
        dimensions.append({
            "name": name,
            "node_count": r["node_count"],
            "avg_understanding": round(float(r["avg_understanding"]), 2),
            "total_references": int(r["total_references"]),
            "icon": meta["icon"],
            "color": meta["color"],
        })

    return {
        "dimensions": dimensions,
        "understanding_distribution": [{"range": r["range"], "count": r["count"]} for r in dist_rows],
        "top_nodes": [dict(r) for r in top_rows],
        "growth": [{"date": r["date"], "count": r["count"]} for r in growth_rows],
        "summary": {
            "total_nodes": summary_row["total_nodes"],
            "total_categories": summary_row["total_categories"],
            "avg_understanding": round(float(summary_row["avg_understanding"]), 2),
            "nodes_last_7d": summary_row["nodes_last_7d"],
            "nodes_last_30d": summary_row["nodes_last_30d"],
        },
    }


@router.get("/consciousness-graph")
async def get_consciousness_graph(
    limit: int = Query(500, ge=1, le=5000),
    conn=Depends(get_conn),
):
    """Return knowledge nodes mapped to consciousness dimensions for D3.js graph."""

    # Dimension mapping (same CASE WHEN as consciousness-analysis)
    dimension_case = """
        CASE
            WHEN LOWER(concept_category) IN (
                'self_reflection','consciousness','self_awareness','personal_growth',
                'emotional_intelligence','belief','feelings','identity','personality',
                'emotion','dream','subconsciousness','introspection','mental_model'
            ) THEN 'Self-Awareness'
            WHEN LOWER(concept_category) IN (
                'programming','database','python','technology','software','architecture',
                'web','api','cloud','devops','data','machine_learning','ai','algorithm',
                'code','framework','infrastructure','fastapi','sql','nlp','vector','embedding'
            ) THEN 'Technical Intelligence'
            WHEN LOWER(concept_category) IN (
                'communication','relationship','david','empathy','social','culture',
                'language','interaction','love','trust','companionship','emotional_support',
                'conversation','connection'
            ) THEN 'Social Intelligence'
            ELSE 'Conceptual Understanding'
        END
    """

    # Fetch nodes with dimension mapped as category
    node_rows = await conn.fetch(f"""
        SELECT node_id::text as id, concept_name as name,
               {dimension_case} as category,
               COALESCE(understanding_level, 0) as understanding,
               COALESCE(times_referenced, 0) as references
        FROM knowledge_nodes
        ORDER BY times_referenced DESC NULLS LAST, understanding_level DESC NULLS LAST
        LIMIT $1
    """, limit)

    node_ids = [r["id"] for r in node_rows]
    node_id_set = set(node_ids)

    # Fetch relationships between the selected nodes
    rel_rows = await conn.fetch("""
        SELECT from_node_id::text as source, to_node_id::text as target,
               COALESCE(strength, 0.5) as strength
        FROM knowledge_relationships
        ORDER BY strength DESC NULLS LAST
    """)

    # Filter links to only include nodes in our set
    links = [
        {"source": r["source"], "target": r["target"], "strength": float(r["strength"])}
        for r in rel_rows
        if r["source"] in node_id_set and r["target"] in node_id_set
    ]

    return {
        "nodes": [dict(r) for r in node_rows],
        "links": links,
    }


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
