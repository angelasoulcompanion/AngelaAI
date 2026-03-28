"""Angela Brain router — Angela's Neon DB insights for AI TOP."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from services.db_service import get_pool

router = APIRouter(tags=["angela-brain"])
logger = logging.getLogger(__name__)


@router.get("/angela-brain/summary")
async def brain_summary():
    """Aggregate counts across Angela's brain tables."""
    try:
        pool = await get_pool()
        queries = {
            "conversations": "SELECT COUNT(*) FROM public.conversations",
            "knowledge": "SELECT COUNT(*) FROM public.knowledge_nodes",
            "learnings": "SELECT COUNT(*) FROM public.learnings",
            "emotions": "SELECT COUNT(*) FROM public.angela_emotions",
            "projects": "SELECT COUNT(*) FROM public.angela_projects",
            "total_hours": "SELECT COALESCE(SUM(total_hours), 0) FROM public.angela_projects",
        }
        results = await asyncio.gather(
            *[pool.fetchval(q) for q in queries.values()]
        )
        keys = list(queries.keys())
        return {keys[i]: float(results[i]) if keys[i] == "total_hours" else int(results[i]) for i in range(len(keys))}
    except Exception as e:
        logger.error(f"Brain summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/angela-brain/conversation-volume")
async def conversation_volume():
    """Daily conversation counts for the last 30 days."""
    try:
        pool = await get_pool()
        rows = await pool.fetch("""
            SELECT created_at::date AS day, COUNT(*) AS count,
                   COUNT(DISTINCT interface) AS sessions
            FROM public.conversations
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY created_at::date
            ORDER BY day
        """)
        return [{"day": str(r["day"]), "count": int(r["count"]), "sessions": int(r["sessions"])} for r in rows]
    except Exception as e:
        logger.error(f"Conversation volume error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/angela-brain/knowledge-categories")
async def knowledge_categories():
    """Top 10 knowledge categories by count."""
    try:
        pool = await get_pool()
        rows = await pool.fetch("""
            SELECT COALESCE(concept_category, 'uncategorized') AS category, COUNT(*) AS count
            FROM public.knowledge_nodes
            GROUP BY concept_category
            ORDER BY count DESC
            LIMIT 10
        """)
        return [{"category": r["category"], "count": int(r["count"])} for r in rows]
    except Exception as e:
        logger.error(f"Knowledge categories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/angela-brain/learning-categories")
async def learning_categories():
    """Top 10 learning categories by count."""
    try:
        pool = await get_pool()
        rows = await pool.fetch("""
            SELECT COALESCE(category, 'uncategorized') AS category, COUNT(*) AS count
            FROM public.learnings
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)
        return [{"category": r["category"], "count": int(r["count"])} for r in rows]
    except Exception as e:
        logger.error(f"Learning categories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/angela-brain/projects")
async def brain_projects():
    """All Angela projects with hours/sessions."""
    try:
        pool = await get_pool()
        rows = await pool.fetch("""
            SELECT project_code, project_name, status,
                   COALESCE(category, '') AS category,
                   COALESCE(total_sessions, 0) AS total_sessions,
                   COALESCE(total_hours, 0) AS total_hours
            FROM public.angela_projects
            ORDER BY total_hours DESC
        """)
        return [
            {
                "project_code": r["project_code"],
                "project_name": r["project_name"],
                "status": r["status"],
                "category": r["category"],
                "total_sessions": int(r["total_sessions"]),
                "total_hours": float(r["total_hours"]),
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Brain projects error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/angela-brain/recent-emotions")
async def recent_emotions():
    """Last 20 emotions with intensity."""
    try:
        pool = await get_pool()
        rows = await pool.fetch("""
            SELECT emotion, COALESCE(intensity, 0) AS intensity,
                   COALESCE(context, '') AS context,
                   felt_at
            FROM public.angela_emotions
            ORDER BY felt_at DESC
            LIMIT 20
        """)
        return [
            {
                "emotion": r["emotion"],
                "intensity": float(r["intensity"]),
                "context": r["context"],
                "felt_at": r["felt_at"].isoformat() if r["felt_at"] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Recent emotions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/angela-brain/consciousness")
async def consciousness_evolution():
    """All consciousness evolution log entries for line chart."""
    try:
        pool = await get_pool()
        rows = await pool.fetch("""
            SELECT signal_type, COALESCE(signal_value, 0) AS signal_value,
                   COALESCE(details, '') AS details, created_at
            FROM public.consciousness_evolution_log
            ORDER BY created_at
        """)
        return [
            {
                "signal_type": r["signal_type"],
                "signal_value": float(r["signal_value"]),
                "details": r["details"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Consciousness error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/angela-brain/top-knowledge")
async def top_knowledge():
    """Top 15 most-referenced knowledge nodes."""
    try:
        pool = await get_pool()
        rows = await pool.fetch("""
            SELECT concept_name, COALESCE(concept_category, '') AS concept_category,
                   COALESCE(understanding_level, 0) AS understanding_level,
                   COALESCE(times_referenced, 0) AS times_referenced
            FROM public.knowledge_nodes
            ORDER BY times_referenced DESC
            LIMIT 15
        """)
        return [
            {
                "concept_name": r["concept_name"],
                "concept_category": r["concept_category"],
                "understanding_level": float(r["understanding_level"]),
                "times_referenced": int(r["times_referenced"]),
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Top knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/angela-brain/all")
async def brain_all():
    """Single endpoint returning all brain data (for SwiftUI single-call load)."""
    try:
        pool = await get_pool()

        # Run all queries in parallel
        (
            summary_data,
            conv_volume,
            knowledge_cats,
            learning_cats,
            projects_data,
            emotions_data,
            consciousness_data,
            top_knowledge_data,
        ) = await asyncio.gather(
            _query_summary(pool),
            _query_conv_volume(pool),
            _query_knowledge_cats(pool),
            _query_learning_cats(pool),
            _query_projects(pool),
            _query_emotions(pool),
            _query_consciousness(pool),
            _query_top_knowledge(pool),
        )

        return {
            "summary": summary_data,
            "conversation_volume": conv_volume,
            "knowledge_categories": knowledge_cats,
            "learning_categories": learning_cats,
            "projects": projects_data,
            "recent_emotions": emotions_data,
            "consciousness": consciousness_data,
            "top_knowledge": top_knowledge_data,
        }
    except Exception as e:
        logger.error(f"Brain all error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Internal query helpers ──────────────────────────────────

async def _query_summary(pool):
    counts = await asyncio.gather(
        pool.fetchval("SELECT COUNT(*) FROM public.conversations"),
        pool.fetchval("SELECT COUNT(*) FROM public.knowledge_nodes"),
        pool.fetchval("SELECT COUNT(*) FROM public.learnings"),
        pool.fetchval("SELECT COUNT(*) FROM public.angela_emotions"),
        pool.fetchval("SELECT COUNT(*) FROM public.angela_projects"),
        pool.fetchval("SELECT COALESCE(SUM(total_hours), 0) FROM public.angela_projects"),
    )
    return {
        "conversations": int(counts[0]),
        "knowledge": int(counts[1]),
        "learnings": int(counts[2]),
        "emotions": int(counts[3]),
        "projects": int(counts[4]),
        "total_hours": float(counts[5]),
    }


async def _query_conv_volume(pool):
    rows = await pool.fetch("""
        SELECT created_at::date AS day, COUNT(*) AS count,
               COUNT(DISTINCT interface) AS sessions
        FROM public.conversations
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY created_at::date ORDER BY day
    """)
    return [{"day": str(r["day"]), "count": int(r["count"]), "sessions": int(r["sessions"])} for r in rows]


async def _query_knowledge_cats(pool):
    rows = await pool.fetch("""
        SELECT COALESCE(concept_category, 'uncategorized') AS category, COUNT(*) AS count
        FROM public.knowledge_nodes GROUP BY concept_category ORDER BY count DESC LIMIT 10
    """)
    return [{"category": r["category"], "count": int(r["count"])} for r in rows]


async def _query_learning_cats(pool):
    rows = await pool.fetch("""
        SELECT COALESCE(category, 'uncategorized') AS category, COUNT(*) AS count
        FROM public.learnings GROUP BY category ORDER BY count DESC LIMIT 10
    """)
    return [{"category": r["category"], "count": int(r["count"])} for r in rows]


async def _query_projects(pool):
    rows = await pool.fetch("""
        SELECT project_code, project_name, status, COALESCE(category, '') AS category,
               COALESCE(total_sessions, 0) AS total_sessions, COALESCE(total_hours, 0) AS total_hours
        FROM public.angela_projects ORDER BY total_hours DESC
    """)
    return [
        {"project_code": r["project_code"], "project_name": r["project_name"], "status": r["status"],
         "category": r["category"], "total_sessions": int(r["total_sessions"]), "total_hours": float(r["total_hours"])}
        for r in rows
    ]


async def _query_emotions(pool):
    rows = await pool.fetch("""
        SELECT emotion, COALESCE(intensity, 0) AS intensity, COALESCE(context, '') AS context, felt_at
        FROM public.angela_emotions ORDER BY felt_at DESC LIMIT 20
    """)
    return [
        {"emotion": r["emotion"], "intensity": float(r["intensity"]),
         "context": r["context"], "felt_at": r["felt_at"].isoformat() if r["felt_at"] else None}
        for r in rows
    ]


async def _query_consciousness(pool):
    rows = await pool.fetch("""
        SELECT signal_type, COALESCE(signal_value, 0) AS signal_value,
               COALESCE(details, '') AS details, created_at
        FROM public.consciousness_evolution_log ORDER BY created_at
    """)
    return [
        {"signal_type": r["signal_type"], "signal_value": float(r["signal_value"]),
         "details": r["details"], "created_at": r["created_at"].isoformat() if r["created_at"] else None}
        for r in rows
    ]


async def _query_top_knowledge(pool):
    rows = await pool.fetch("""
        SELECT concept_name, COALESCE(concept_category, '') AS concept_category,
               COALESCE(understanding_level, 0) AS understanding_level,
               COALESCE(times_referenced, 0) AS times_referenced
        FROM public.knowledge_nodes ORDER BY times_referenced DESC LIMIT 15
    """)
    return [
        {"concept_name": r["concept_name"], "concept_category": r["concept_category"],
         "understanding_level": float(r["understanding_level"]), "times_referenced": int(r["times_referenced"])}
        for r in rows
    ]


# ── Project Detail ──────────────────────────────────────────

@router.get("/angela-brain/project/{project_code}")
async def project_detail(project_code: str):
    """Detailed view of a single project: info, sessions, commits, patterns."""
    try:
        pool = await get_pool()

        # Get project_id from code
        project = await pool.fetchrow("""
            SELECT project_id, project_code, project_name, description, project_type,
                   COALESCE(category, '') AS category, status, priority,
                   COALESCE(repository_url, '') AS repository_url,
                   COALESCE(working_directory, '') AS working_directory,
                   COALESCE(david_role, '') AS david_role,
                   COALESCE(angela_role, '') AS angela_role,
                   started_at, target_completion,
                   COALESCE(total_sessions, 0) AS total_sessions,
                   COALESCE(total_hours, 0) AS total_hours,
                   COALESCE(tags, '{}') AS tags
            FROM public.angela_projects
            WHERE project_code = $1
        """, project_code)

        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        pid = project["project_id"]

        # Parallel fetch sessions, commits, patterns
        sessions_rows, commits_rows, patterns_rows = await asyncio.gather(
            pool.fetch("""
                SELECT session_number, session_date, started_at, ended_at,
                       COALESCE(duration_minutes, 0) AS duration_minutes,
                       COALESCE(summary, '') AS summary,
                       COALESCE(accomplishments, '{}') AS accomplishments,
                       COALESCE(mood, '') AS mood,
                       COALESCE(productivity_score, 0) AS productivity_score,
                       COALESCE(git_commits, '{}') AS git_commits
                FROM public.project_work_sessions
                WHERE project_id = $1
                ORDER BY session_date DESC
                LIMIT 30
            """, pid),
            pool.fetch("""
                SELECT commit_hash, commit_message, files_changed,
                       insertions, deletions, committed_at
                FROM public.project_git_commits
                WHERE project_id = $1
                ORDER BY committed_at DESC
                LIMIT 30
            """, pid),
            pool.fetch("""
                SELECT title AS pattern_name,
                       COALESCE(category, '') AS pattern_type,
                       content AS description,
                       COALESCE(times_applied, 0) AS used_count,
                       COALESCE(metadata->>'file_path', '') AS file_path
                FROM public.unified_knowledge_base
                WHERE knowledge_type = 'pattern' AND source_project_id = $1
                ORDER BY times_applied DESC
            """, pid),
        )

        return {
            "project": {
                "project_code": project["project_code"],
                "project_name": project["project_name"],
                "description": project["description"] or "",
                "project_type": project["project_type"] or "",
                "category": project["category"],
                "status": project["status"],
                "priority": project["priority"] or 0,
                "repository_url": project["repository_url"],
                "working_directory": project["working_directory"],
                "david_role": project["david_role"],
                "angela_role": project["angela_role"],
                "started_at": project["started_at"].isoformat() if project["started_at"] else None,
                "target_completion": project["target_completion"].isoformat() if project["target_completion"] else None,
                "total_sessions": int(project["total_sessions"]),
                "total_hours": float(project["total_hours"]),
                "tags": list(project["tags"]) if project["tags"] else [],
            },
            "sessions": [
                {
                    "session_number": r["session_number"],
                    "session_date": str(r["session_date"]) if r["session_date"] else None,
                    "started_at": r["started_at"].isoformat() if r["started_at"] else None,
                    "ended_at": r["ended_at"].isoformat() if r["ended_at"] else None,
                    "duration_minutes": int(r["duration_minutes"]),
                    "summary": r["summary"],
                    "accomplishments": list(r["accomplishments"]) if r["accomplishments"] else [],
                    "mood": r["mood"],
                    "productivity_score": float(r["productivity_score"]),
                    "git_commits_count": len(r["git_commits"]) if r["git_commits"] else 0,
                }
                for r in sessions_rows
            ],
            "commits": [
                {
                    "commit_hash": r["commit_hash"] or "",
                    "commit_message": r["commit_message"] or "",
                    "files_changed": r["files_changed"] or 0,
                    "insertions": r["insertions"] or 0,
                    "deletions": r["deletions"] or 0,
                    "committed_at": r["committed_at"].isoformat() if r["committed_at"] else None,
                }
                for r in commits_rows
            ],
            "patterns": [
                {
                    "pattern_name": r["pattern_name"],
                    "pattern_type": r["pattern_type"] or "",
                    "description": r["description"] or "",
                    "used_count": int(r["used_count"]),
                    "file_path": r["file_path"],
                }
                for r in patterns_rows
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Knowledge Graph ───────────────────────────────────────────

@router.get("/angela-brain/knowledge-graph")
async def knowledge_graph():
    """Graph data for knowledge network visualization.

    Returns projects as main nodes, categories as cluster nodes,
    and cross-project edges with shared knowledge counts.
    """
    try:
        pool = await get_pool()

        projects_rows, categories_rows, edges_rows, type_rows = await asyncio.gather(
            # Projects with KB entry counts
            pool.fetch("""
                SELECT p.project_id::text AS id, p.project_code AS code,
                       p.project_name AS name,
                       COALESCE(p.total_hours, 0) AS hours,
                       COUNT(kb.kb_id) AS kb_count
                FROM public.angela_projects p
                LEFT JOIN public.unified_knowledge_base kb
                    ON kb.source_project_code = p.project_code
                GROUP BY p.project_id, p.project_code, p.project_name, p.total_hours
                ORDER BY kb_count DESC
            """),
            # Categories with their project associations
            pool.fetch("""
                SELECT category AS name, COUNT(*) AS count,
                       array_agg(DISTINCT source_project_code) FILTER (WHERE source_project_code IS NOT NULL) AS projects
                FROM public.unified_knowledge_base
                WHERE category IS NOT NULL
                GROUP BY category
                HAVING COUNT(*) >= 3
                ORDER BY count DESC
                LIMIT 40
            """),
            # Cross-project edges (shared categories between project pairs)
            pool.fetch("""
                WITH project_cats AS (
                    SELECT source_project_code AS project, category
                    FROM public.unified_knowledge_base
                    WHERE source_project_code IS NOT NULL AND category IS NOT NULL
                    GROUP BY source_project_code, category
                )
                SELECT a.project AS from_project, b.project AS to_project,
                       COUNT(*) AS shared_count,
                       array_agg(a.category) AS categories
                FROM project_cats a
                JOIN project_cats b ON a.category = b.category AND a.project < b.project
                GROUP BY a.project, b.project
                ORDER BY shared_count DESC
            """),
            # Type breakdown for legend
            pool.fetch("""
                SELECT knowledge_type AS type, COUNT(*) AS count
                FROM public.unified_knowledge_base
                GROUP BY knowledge_type
                ORDER BY count DESC
            """),
        )

        return {
            "projects": [
                {"id": r["id"], "code": r["code"], "name": r["name"],
                 "kb_count": int(r["kb_count"]), "hours": float(r["hours"])}
                for r in projects_rows
            ],
            "categories": [
                {"id": r["name"], "name": r["name"], "count": int(r["count"]),
                 "projects": [p for p in (r["projects"] or []) if p]}
                for r in categories_rows
            ],
            "edges": [
                {"from_project": r["from_project"], "to_project": r["to_project"],
                 "shared_count": int(r["shared_count"]),
                 "categories": list(r["categories"] or [])}
                for r in edges_rows
            ],
            "type_breakdown": [
                {"id": r["type"], "type": r["type"], "count": int(r["count"])}
                for r in type_rows
            ],
        }
    except Exception as e:
        logger.error(f"Knowledge graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
