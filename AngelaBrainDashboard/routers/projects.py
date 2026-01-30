"""Projects endpoints."""
from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/list")
async def get_projects():
    """Fetch all projects"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                p.project_id::text, p.project_code, p.project_name, p.description,
                p.project_type, p.category, p.status, p.priority,
                p.repository_url, p.working_directory, p.client_name,
                p.david_role, p.angela_role, p.started_at, p.target_completion,
                p.completed_at, p.total_sessions, p.total_hours, p.tags,
                p.created_at, p.updated_at,
                (SELECT MAX(session_date) FROM project_work_sessions WHERE project_id = p.project_id) as last_session_date
            FROM angela_projects p
            ORDER BY
                (SELECT MAX(session_date) FROM project_work_sessions WHERE project_id = p.project_id) DESC NULLS LAST
        """)
        return [dict(r) for r in rows]


@router.get("/sessions")
async def get_recent_work_sessions(days: int = Query(7, ge=1, le=30)):
    """Fetch recent work sessions"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                ws.session_id::text, ws.project_id::text, ws.session_number,
                ws.session_date, ws.started_at, ws.ended_at, ws.duration_minutes,
                ws.session_goal, ws.david_requests, ws.summary,
                ws.accomplishments, ws.blockers, ws.next_steps, ws.mood,
                ws.productivity_score, p.project_name
            FROM project_work_sessions ws
            JOIN angela_projects p ON ws.project_id = p.project_id
            WHERE ws.session_date >= CURRENT_DATE - make_interval(days => $1)
            ORDER BY ws.session_date DESC, ws.started_at DESC
            LIMIT 50
        """, days)
        return [dict(r) for r in rows]


@router.get("/milestones")
async def get_recent_milestones(limit: int = Query(10, ge=1, le=50)):
    """Fetch recent project milestones"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                milestone_id::text, project_id::text, session_id::text,
                milestone_type, title, description, significance,
                achieved_at, celebration_note, created_at
            FROM project_milestones
            ORDER BY achieved_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@router.get("/learnings")
async def get_recent_project_learnings(limit: int = Query(10, ge=1, le=50)):
    """Fetch recent project learnings"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                learning_id::text, project_id::text, session_id::text,
                learning_type, category, title, insight, context,
                applicable_to, confidence, learned_at
            FROM project_learnings
            ORDER BY learned_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@router.get("/tech-stack-graph")
async def get_tech_stack_graph():
    """Fetch tech stack graph data for visualization"""
    pool = get_pool()
    async with pool.acquire() as conn:
        # Get all unique techs with their project counts
        tech_rows = await conn.fetch("""
            SELECT
                ts.tech_type,
                ts.tech_name,
                ts.version,
                ts.purpose,
                COUNT(DISTINCT ts.project_id) as project_count,
                ARRAY_AGG(DISTINCT p.project_name) as project_names
            FROM project_tech_stack ts
            JOIN angela_projects p ON ts.project_id = p.project_id
            GROUP BY ts.tech_type, ts.tech_name, ts.version, ts.purpose
            ORDER BY project_count DESC, ts.tech_name
        """)

        # Get all projects with their tech counts
        project_rows = await conn.fetch("""
            SELECT
                p.project_id::text,
                p.project_name,
                p.status,
                p.project_type,
                COUNT(ts.stack_id) as tech_count
            FROM angela_projects p
            LEFT JOIN project_tech_stack ts ON p.project_id = ts.project_id
            GROUP BY p.project_id, p.project_name, p.status, p.project_type
            HAVING COUNT(ts.stack_id) > 0
            ORDER BY tech_count DESC
        """)

        # Get all project-tech relationships for links
        link_rows = await conn.fetch("""
            SELECT
                p.project_id::text,
                ts.tech_name,
                ts.tech_type
            FROM project_tech_stack ts
            JOIN angela_projects p ON ts.project_id = p.project_id
        """)

        nodes = []
        links = []
        tech_name_to_id = {}

        # Create tech nodes
        for r in tech_rows:
            tech_name = r['tech_name']
            tech_id = f"tech-{tech_name.lower().replace(' ', '-')}"
            tech_name_to_id[tech_name] = tech_id

            nodes.append({
                'id': tech_id,
                'name': tech_name,
                'node_type': 'tech',
                'tech_type': r['tech_type'],
                'version': r['version'],
                'purpose': r['purpose'],
                'project_count': r['project_count'],
                'projects': list(r['project_names']) if r['project_names'] else []
            })

        # Create project nodes
        project_id_to_node_id = {}
        for r in project_rows:
            project_id = r['project_id']
            node_id = f"proj-{project_id}"
            project_id_to_node_id[project_id] = node_id

            nodes.append({
                'id': node_id,
                'name': r['project_name'],
                'node_type': 'project',
                'status': r['status'],
                'project_type': r['project_type'],
                'tech_count': r['tech_count']
            })

        # Create links
        for r in link_rows:
            project_id = r['project_id']
            tech_name = r['tech_name']

            if project_id in project_id_to_node_id and tech_name in tech_name_to_id:
                links.append({
                    'source': project_id_to_node_id[project_id],
                    'target': tech_name_to_id[tech_name],
                    'strength': 0.7,
                    'tech_type': r['tech_type']
                })

        return {'nodes': nodes, 'links': links}
