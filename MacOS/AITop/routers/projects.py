"""Projects router — detailed project tracking for AI TOP.

Surfaces the rich project_* tables (work_sessions, technical_decisions, mistakes,
git_commits, milestones) that Angela logs every session but never displayed.
Visual sibling of the /recall CLI.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from services.db_service import get_pool

router = APIRouter(tags=["projects"])
logger = logging.getLogger(__name__)


def _d(value) -> str | None:
    """Date/datetime → ISO string (or None)."""
    return value.isoformat() if value is not None else None


@router.get("/projects/overview")
async def projects_overview():
    """Portfolio: per-project cards + aggregate KPIs."""
    try:
        pool = await get_pool()

        totals, rows = await asyncio.gather(
            pool.fetchrow("""
                SELECT
                    (SELECT COUNT(*) FROM public.angela_projects) AS projects,
                    (SELECT COUNT(*) FROM public.angela_projects WHERE status = 'active') AS active,
                    (SELECT COUNT(*) FROM public.project_work_sessions) AS sessions,
                    (SELECT COALESCE(SUM(total_hours), 0) FROM public.angela_projects) AS hours,
                    (SELECT COUNT(*) FROM public.project_technical_decisions) AS decisions,
                    (SELECT COUNT(*) FROM public.project_mistakes WHERE auto_warn) AS active_gotchas,
                    (SELECT COUNT(*) FROM public.project_git_commits) AS commits,
                    (SELECT COUNT(*) FROM public.project_work_sessions
                       WHERE session_date >= CURRENT_DATE - 7) AS week_sessions
            """),
            pool.fetch("""
                SELECT
                    p.project_code, p.project_name, p.status,
                    COALESCE(p.priority, 0) AS priority,
                    COALESCE(p.total_sessions, 0) AS total_sessions,
                    COALESCE(p.total_hours, 0) AS total_hours,
                    (SELECT MAX(session_date) FROM public.project_work_sessions w
                       WHERE w.project_id = p.project_id) AS last_active,
                    (SELECT COUNT(*) FROM public.project_mistakes m
                       WHERE m.project_id = p.project_id AND m.auto_warn) AS active_gotchas,
                    COALESCE((
                        SELECT array_length(w.next_steps, 1) FROM public.project_work_sessions w
                         WHERE w.project_id = p.project_id AND w.next_steps IS NOT NULL
                         ORDER BY w.session_date DESC NULLS LAST, w.started_at DESC LIMIT 1
                    ), 0) AS open_threads,
                    COALESCE((
                        SELECT ARRAY_AGG(s.productivity_score ORDER BY s.session_date)
                        FROM (
                            SELECT productivity_score, session_date
                            FROM public.project_work_sessions w
                            WHERE w.project_id = p.project_id AND productivity_score IS NOT NULL
                            ORDER BY session_date DESC NULLS LAST LIMIT 12
                        ) s
                    ), ARRAY[]::double precision[]) AS spark
                FROM public.angela_projects p
                ORDER BY last_active DESC NULLS LAST, p.total_hours DESC
            """),
        )

        projects = []
        for r in rows:
            spark = [float(x) for x in (r["spark"] or [])]
            projects.append({
                "project_code": r["project_code"],
                "project_name": r["project_name"],
                "status": r["status"] or "unknown",
                "priority": int(r["priority"]),
                "total_sessions": int(r["total_sessions"]),
                "total_hours": float(r["total_hours"]),
                "last_active": _d(r["last_active"]),
                "active_gotchas": int(r["active_gotchas"]),
                "open_threads": int(r["open_threads"]),
                "spark": spark,
                "avg_productivity": round(sum(spark) / len(spark), 1) if spark else 0.0,
            })

        return {
            "totals": {
                "projects": int(totals["projects"]),
                "active": int(totals["active"]),
                "sessions": int(totals["sessions"]),
                "hours": float(totals["hours"]),
                "decisions": int(totals["decisions"]),
                "active_gotchas": int(totals["active_gotchas"]),
                "commits": int(totals["commits"]),
                "week_sessions": int(totals["week_sessions"]),
            },
            "projects": projects,
        }
    except Exception as e:
        logger.error(f"Projects overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_code}")
async def project_detail(project_code: str):
    """Full per-project tracking detail."""
    try:
        pool = await get_pool()

        proj = await pool.fetchrow("""
            SELECT project_id, project_code, project_name,
                   COALESCE(description, '') AS description,
                   COALESCE(project_type, '') AS project_type,
                   COALESCE(category, '') AS category,
                   COALESCE(status, 'unknown') AS status,
                   COALESCE(priority, 0) AS priority,
                   COALESCE(repository_url, '') AS repository_url,
                   COALESCE(david_role, '') AS david_role,
                   COALESCE(angela_role, '') AS angela_role,
                   started_at, target_completion,
                   COALESCE(total_sessions, 0) AS total_sessions,
                   COALESCE(total_hours, 0) AS total_hours,
                   COALESCE(tags, ARRAY[]::text[]) AS tags
            FROM public.angela_projects
            WHERE project_code = $1
        """, project_code)

        if proj is None:
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        pid = proj["project_id"]

        kpis, sessions, decisions, gotchas, commits, milestones = await asyncio.gather(
            pool.fetchrow("""
                SELECT
                    (SELECT COUNT(*) FROM public.project_technical_decisions WHERE project_id = $1) AS decisions,
                    (SELECT COUNT(*) FROM public.project_mistakes WHERE project_id = $1) AS mistakes,
                    (SELECT COUNT(*) FROM public.project_mistakes WHERE project_id = $1 AND auto_warn) AS active_gotchas,
                    (SELECT COUNT(*) FROM public.project_git_commits WHERE project_id = $1) AS commits,
                    (SELECT COUNT(*) FROM public.project_milestones WHERE project_id = $1) AS milestones
            """, pid),
            pool.fetch("""
                SELECT session_number, session_date, started_at,
                       COALESCE(session_goal, '') AS session_goal,
                       COALESCE(summary, '') AS summary,
                       COALESCE(accomplishments, ARRAY[]::text[]) AS accomplishments,
                       COALESCE(blockers, ARRAY[]::text[]) AS blockers,
                       COALESCE(next_steps, ARRAY[]::text[]) AS next_steps,
                       COALESCE(mood, '') AS mood,
                       COALESCE(productivity_score, 0) AS productivity_score,
                       COALESCE(duration_minutes, 0) AS duration_minutes,
                       COALESCE(array_length(git_commits, 1), 0) AS git_commits_count
                FROM public.project_work_sessions
                WHERE project_id = $1
                ORDER BY session_date DESC NULLS LAST, started_at DESC
                LIMIT 25
            """, pid),
            pool.fetch("""
                SELECT decision_title, COALESCE(category, '') AS category,
                       COALESCE(decision_made, '') AS decision_made,
                       COALESCE(status, 'active') AS status, decided_at
                FROM public.project_technical_decisions
                WHERE project_id = $1
                  AND COALESCE(status, 'active') NOT IN ('superseded', 'reverted')
                  AND superseded_by IS NULL
                ORDER BY decided_at DESC NULLS LAST
                LIMIT 20
            """, pid),
            pool.fetch("""
                SELECT severity, title, COALESCE(how_to_prevent, '') AS how_to_prevent,
                       COALESCE(mistake_type, '') AS mistake_type, created_at
                FROM public.project_mistakes
                WHERE project_id = $1 AND auto_warn
                ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                         WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END,
                         created_at DESC
                LIMIT 20
            """, pid),
            pool.fetch("""
                SELECT commit_hash, COALESCE(commit_message, '') AS commit_message,
                       COALESCE(files_changed, 0) AS files_changed,
                       COALESCE(insertions, 0) AS insertions,
                       COALESCE(deletions, 0) AS deletions, committed_at
                FROM public.project_git_commits
                WHERE project_id = $1
                ORDER BY committed_at DESC NULLS LAST
                LIMIT 20
            """, pid),
            pool.fetch("""
                SELECT title, COALESCE(milestone_type, '') AS milestone_type,
                       COALESCE(description, '') AS description,
                       COALESCE(significance, 0) AS significance,
                       COALESCE(celebration_note, '') AS celebration_note, achieved_at
                FROM public.project_milestones
                WHERE project_id = $1
                ORDER BY achieved_at DESC NULLS LAST
                LIMIT 20
            """, pid),
        )

        # Open threads = next_steps from the most recent session, deduped
        threads: list[str] = []
        seen = set()
        for s in sessions:
            for step in (s["next_steps"] or []):
                k = " ".join(step.split()).lower()
                if k and k not in seen:
                    seen.add(k)
                    threads.append(step)
            if threads:
                break  # only the latest session that actually has next_steps

        # Productivity trend (chronological, last 30)
        productivity = [
            {"date": _d(s["session_date"]), "score": float(s["productivity_score"]), "mood": s["mood"]}
            for s in reversed(sessions) if s["productivity_score"]
        ][-30:]

        return {
            "project": {
                "project_code": proj["project_code"],
                "project_name": proj["project_name"],
                "description": proj["description"],
                "project_type": proj["project_type"],
                "category": proj["category"],
                "status": proj["status"],
                "priority": int(proj["priority"]),
                "repository_url": proj["repository_url"],
                "david_role": proj["david_role"],
                "angela_role": proj["angela_role"],
                "started_at": _d(proj["started_at"]),
                "target_completion": _d(proj["target_completion"]),
                "total_sessions": int(proj["total_sessions"]),
                "total_hours": float(proj["total_hours"]),
                "tags": list(proj["tags"] or []),
            },
            "kpis": {
                "decisions": int(kpis["decisions"]),
                "mistakes": int(kpis["mistakes"]),
                "active_gotchas": int(kpis["active_gotchas"]),
                "commits": int(kpis["commits"]),
                "milestones": int(kpis["milestones"]),
            },
            "threads": threads,
            "productivity": productivity,
            "sessions": [{
                "session_number": int(s["session_number"]) if s["session_number"] is not None else 0,
                "session_date": _d(s["session_date"]),
                "session_goal": s["session_goal"],
                "summary": s["summary"],
                "accomplishments": list(s["accomplishments"] or []),
                "blockers": list(s["blockers"] or []),
                "next_steps": list(s["next_steps"] or []),
                "mood": s["mood"],
                "productivity_score": float(s["productivity_score"]),
                "duration_minutes": int(s["duration_minutes"]),
                "git_commits_count": int(s["git_commits_count"]),
            } for s in sessions],
            "decisions": [{
                "decision_title": d["decision_title"],
                "category": d["category"],
                "decision_made": d["decision_made"],
                "status": d["status"],
                "decided_at": _d(d["decided_at"]),
            } for d in decisions],
            "gotchas": [{
                "severity": g["severity"],
                "title": g["title"],
                "how_to_prevent": g["how_to_prevent"],
                "mistake_type": g["mistake_type"],
                "created_at": _d(g["created_at"]),
            } for g in gotchas],
            "commits": [{
                "commit_hash": c["commit_hash"],
                "commit_message": c["commit_message"],
                "files_changed": int(c["files_changed"]),
                "insertions": int(c["insertions"]),
                "deletions": int(c["deletions"]),
                "committed_at": _d(c["committed_at"]),
            } for c in commits],
            "milestones": [{
                "title": m["title"],
                "milestone_type": m["milestone_type"],
                "description": m["description"],
                "significance": int(m["significance"]),
                "celebration_note": m["celebration_note"],
                "achieved_at": _d(m["achieved_at"]),
            } for m in milestones],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project detail error ({project_code}): {e}")
        raise HTTPException(status_code=500, detail=str(e))
