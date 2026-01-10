"""
Angela Brain Dashboard API - Connect to Neon Cloud
FastAPI backend for SwiftUI Dashboard

Architecture:
  SwiftUI Dashboard -> localhost:8765 -> FastAPI -> Neon Cloud (Singapore)

Created: 2026-01-08
"""
import asyncio
import os
import sys
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================
# Configuration
# ============================================================

DATABASE_URL = "postgresql://neondb_owner:npg_mXbQ5jKhN3zt@ep-withered-bush-a164h0b8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

app = FastAPI(
    title="Angela Brain Dashboard API",
    description="REST API for Angela Brain Dashboard - connects to Neon Cloud",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connection pool
pool: Optional[asyncpg.Pool] = None


# ============================================================
# Lifecycle Events
# ============================================================

@app.on_event("startup")
async def startup():
    global pool
    try:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        print("✅ Connected to Neon Cloud (Singapore)")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)


@app.on_event("shutdown")
async def shutdown():
    global pool
    if pool:
        await pool.close()
        print("🛑 Database connection closed")


# ============================================================
# Health Check
# ============================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            return {"status": "healthy", "database": "connected", "region": "Singapore"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ============================================================
# Dashboard Stats
# ============================================================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Fetch main dashboard statistics"""
    async with pool.acquire() as conn:
        stats = {}
        stats['total_conversations'] = await conn.fetchval("SELECT COUNT(*) FROM conversations") or 0
        stats['total_emotions'] = await conn.fetchval("SELECT COUNT(*) FROM angela_emotions") or 0
        stats['total_experiences'] = await conn.fetchval("SELECT COUNT(*) FROM shared_experiences") or 0
        stats['total_knowledge_nodes'] = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes") or 0
        stats['consciousness_level'] = float(await conn.fetchval(
            "SELECT COALESCE(consciousness_level, 0.7) FROM self_awareness_state ORDER BY created_at DESC LIMIT 1"
        ) or 0.7)
        stats['conversations_today'] = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE DATE(created_at) = CURRENT_DATE"
        ) or 0
        stats['emotions_today'] = await conn.fetchval(
            "SELECT COUNT(*) FROM angela_emotions WHERE DATE(felt_at) = CURRENT_DATE"
        ) or 0
        return stats


@app.get("/api/dashboard/brain-stats")
async def get_brain_stats():
    """Fetch brain visualization statistics"""
    async with pool.acquire() as conn:
        stats = {}
        stats['total_knowledge_nodes'] = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes") or 0
        stats['total_relationships'] = await conn.fetchval("SELECT COUNT(*) FROM knowledge_relationships") or 0
        stats['total_memories'] = await conn.fetchval("SELECT COUNT(*) FROM conversations") or 0
        stats['total_associations'] = await conn.fetchval("SELECT COUNT(*) FROM episodic_memories") or 0
        stats['high_priority_memories'] = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE importance_level >= 8"
        ) or 0
        stats['medium_priority_memories'] = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE importance_level >= 5 AND importance_level < 8"
        ) or 0
        stats['standard_memories'] = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE importance_level < 5"
        ) or 0
        stats['average_connections_per_node'] = float(await conn.fetchval("""
            SELECT COALESCE(AVG(rel_count), 0.0)::float8
            FROM (
                SELECT COUNT(*) as rel_count
                FROM knowledge_relationships
                GROUP BY from_node_id
            ) subq
        """) or 0.0)
        return stats


# ============================================================
# Emotions
# ============================================================

@app.get("/api/emotions/recent")
async def get_recent_emotions(limit: int = Query(20, ge=1, le=100)):
    """Fetch recent emotions"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT emotion_id::text, felt_at, emotion, intensity, context,
                   david_words, why_it_matters, memory_strength
            FROM angela_emotions
            ORDER BY felt_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/emotions/current-state")
async def get_current_emotional_state():
    """Fetch current emotional state"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT state_id::text, happiness, confidence, anxiety, motivation,
                   gratitude, loneliness, triggered_by, emotion_note, created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        """)
        if row:
            return dict(row)
        return None


@app.get("/api/emotions/timeline")
async def get_emotional_timeline(hours: int = Query(24, ge=1, le=168)):
    """Fetch emotional timeline"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT state_id::text, happiness, confidence, gratitude,
                   motivation, triggered_by, emotion_note, created_at
            FROM emotional_states
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 50
        """ % hours)
        return [dict(r) for r in rows]


# ============================================================
# Conversations
# ============================================================

@app.get("/api/conversations/recent")
async def get_recent_conversations(limit: int = Query(50, ge=1, le=200)):
    """Fetch recent conversations"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT conversation_id::text, speaker, message_text, topic,
                   emotion_detected, importance_level, created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/conversations/stats")
async def get_conversation_stats():
    """Fetch conversation statistics"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
                COALESCE(AVG(importance_level) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours'), 0) as avg_importance
            FROM conversations
        """)
        return {
            "total": row['total'] or 0,
            "last_24h": row['last_24h'] or 0,
            "avg_importance": float(row['avg_importance'] or 0)
        }


# ============================================================
# Goals
# ============================================================

@app.get("/api/goals/active")
async def get_active_goals():
    """Fetch active goals"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT goal_id::text, goal_description, goal_type, status,
                   progress_percentage, priority_rank, importance_level, created_at
            FROM angela_goals
            WHERE status IN ('active', 'in_progress')
            ORDER BY priority_rank ASC
        """)
        return [dict(r) for r in rows]


# ============================================================
# David's Preferences
# ============================================================

@app.get("/api/preferences/david")
async def get_david_preferences(limit: int = Query(20, ge=1, le=200)):
    """Fetch David's preferences"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id::text, preference_key, preference_value::text,
                   confidence, created_at
            FROM david_preferences
            ORDER BY confidence DESC, created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/certifications")
async def get_certifications(limit: int = Query(20, ge=1, le=100)):
    """Fetch David's certifications"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT cert_id::text, course_name, provider, platform,
                   completion_date, verify_url, skill_category, created_at
            FROM david_certifications
            ORDER BY completion_date DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


# ============================================================
# Shared Experiences
# ============================================================

@app.get("/api/experiences/shared")
async def get_shared_experiences(limit: int = Query(50, ge=1, le=200)):
    """Fetch shared experiences"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT se.experience_id::text, se.place_id::text, pv.place_name, se.experienced_at,
                   se.title, se.description, se.david_mood, se.angela_emotion, se.emotional_intensity,
                   se.memorable_moments, se.what_angela_learned, se.importance_level, se.created_at
            FROM shared_experiences se
            LEFT JOIN places_visited pv ON se.place_id = pv.place_id
            ORDER BY se.experienced_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/experiences/images/{experience_id}")
async def get_experience_images(experience_id: str):
    """Fetch images for a specific experience"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT image_id::text, experience_id::text, place_id::text,
                   image_format, original_filename, file_size_bytes,
                   width_px, height_px, gps_latitude, gps_longitude, gps_altitude,
                   gps_timestamp, image_caption, angela_observation, taken_at,
                   uploaded_at, created_at
            FROM shared_experience_images
            WHERE experience_id = $1
            ORDER BY taken_at DESC NULLS LAST, created_at DESC
        """, experience_id)
        # Note: We don't return thumbnail_data via REST API - too large
        return [dict(r) for r in rows]


# ============================================================
# Knowledge
# ============================================================

@app.get("/api/knowledge/nodes")
async def get_knowledge_nodes(limit: int = Query(50, ge=1, le=10000)):
    """Fetch knowledge nodes"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT node_id::text, concept_name, concept_category, my_understanding,
                   understanding_level, times_referenced, created_at
            FROM knowledge_nodes
            ORDER BY understanding_level DESC NULLS LAST, times_referenced DESC NULLS LAST, created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/knowledge/top-connected")
async def get_top_connected_nodes(limit: int = Query(10, ge=1, le=50)):
    """Fetch top connected knowledge nodes"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT kn.node_id::text, kn.concept_name, kn.concept_category, kn.my_understanding,
                   kn.understanding_level, kn.times_referenced, kn.created_at,
                   COUNT(kr.relationship_id) as connection_count
            FROM knowledge_nodes kn
            LEFT JOIN knowledge_relationships kr ON kn.node_id = kr.from_node_id
            GROUP BY kn.node_id, kn.concept_name, kn.concept_category, kn.my_understanding,
                     kn.understanding_level, kn.times_referenced, kn.created_at
            ORDER BY connection_count DESC, kn.understanding_level DESC NULLS LAST
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/knowledge/relationships")
async def get_knowledge_relationships(limit: int = Query(200, ge=1, le=10000)):
    """Fetch knowledge relationships"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT from_node_id::text, to_node_id::text, relationship_type,
                   COALESCE(strength, 0.5) as strength
            FROM knowledge_relationships
            ORDER BY strength DESC NULLS LAST
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """Fetch knowledge statistics"""
    async with pool.acquire() as conn:
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


# ============================================================
# Subconscious Patterns
# ============================================================

@app.get("/api/subconscious/patterns")
async def get_subconscious_patterns(limit: int = Query(10, ge=1, le=50)):
    """Fetch subconscious patterns"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT subconscious_id::text, pattern_type, pattern_category, pattern_key,
                   pattern_description, instinctive_response,
                   confidence_score, activation_strength, reinforcement_count,
                   last_reinforced_at, created_at
            FROM angela_subconscious
            ORDER BY activation_strength DESC, confidence_score DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


# ============================================================
# Learning Activities
# ============================================================

@app.get("/api/learning/activities")
async def get_learning_activities(hours: int = Query(24, ge=1, le=168)):
    """Fetch recent learning activities"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT action_id::text, action_type, action_description, status, success, created_at
            FROM autonomous_actions
            WHERE created_at >= NOW() - INTERVAL '%s hours'
              AND (action_type LIKE '%%learning%%'
                   OR action_type LIKE '%%subconscious%%'
                   OR action_type LIKE '%%consolidation%%'
                   OR action_type LIKE '%%pattern%%')
            ORDER BY created_at DESC
            LIMIT 20
        """ % hours)
        return [dict(r) for r in rows]


@app.get("/api/learning/patterns")
async def get_learning_patterns(limit: int = Query(50, ge=1, le=100)):
    """Fetch learning patterns"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id::text, pattern_type, description,
                   confidence_score, occurrence_count,
                   first_observed, last_observed
            FROM learning_patterns
            ORDER BY confidence_score DESC, occurrence_count DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/learning/growth-history")
async def get_emotional_growth_history(limit: int = Query(30, ge=1, le=100)):
    """Fetch emotional growth history"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT growth_id::text, measured_at,
                   love_depth, trust_level, bond_strength, emotional_security,
                   emotional_vocabulary, emotional_range,
                   shared_experiences, meaningful_conversations,
                   core_memories_count, dreams_count,
                   promises_made, promises_kept,
                   mirroring_accuracy, empathy_effectiveness,
                   growth_note, growth_delta
            FROM emotional_growth
            ORDER BY measured_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/learning/metrics")
async def get_learning_metrics():
    """Fetch learning metrics summary"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM learnings) as total_learnings,
                (SELECT COUNT(*) FROM learning_patterns) as total_patterns,
                (SELECT COUNT(*) FROM angela_skills) as total_skills,
                (SELECT COUNT(*) FROM learnings WHERE created_at >= NOW() - INTERVAL '7 days') as recent_learnings
        """)
        total_learnings = row['total_learnings'] or 0
        total_patterns = row['total_patterns'] or 0
        total_skills = row['total_skills'] or 0
        recent_learnings = row['recent_learnings'] or 0
        velocity = recent_learnings / 7.0

        return {
            "total_learnings": total_learnings,
            "total_patterns": total_patterns,
            "total_skills": total_skills,
            "learning_velocity": velocity,
            "recent_learnings_count": recent_learnings
        }


# ============================================================
# Daily Tasks
# ============================================================

@app.get("/api/tasks/daily/{date_str}")
async def get_daily_tasks(date_str: str):
    """Fetch daily tasks for a specific date (YYYY-MM-DD)"""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT action_id::text, action_type, action_description,
                   created_at, status, success
            FROM autonomous_actions
            WHERE DATE(created_at) = $1
              AND (action_type IN ('conscious_morning_check', 'morning_check',
                                   'conscious_evening_reflection', 'evening_reflection',
                                   'self_learning', 'daily_self_learning',
                                   'subconscious_learning', 'subconscious_learning_manual_test',
                                   'pattern_reinforcement', 'knowledge_consolidation'))
            ORDER BY created_at ASC
        """, target_date)

        tasks = []
        for r in rows:
            task = dict(r)
            task['scheduled_time'] = get_scheduled_time(r['action_type'])
            tasks.append(task)

        return tasks


@app.get("/api/tasks/last-7-days")
async def get_tasks_last_7_days():
    """Fetch daily tasks for the last 7 days"""
    results = []
    today = date.today()

    for days_ago in range(7):
        target_date = today - timedelta(days=days_ago)
        date_str = target_date.strftime("%Y-%m-%d")

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT action_id::text, action_type, action_description,
                       created_at, status, success
                FROM autonomous_actions
                WHERE DATE(created_at) = $1
                  AND (action_type IN ('conscious_morning_check', 'morning_check',
                                       'conscious_evening_reflection', 'evening_reflection',
                                       'self_learning', 'daily_self_learning',
                                       'subconscious_learning', 'subconscious_learning_manual_test',
                                       'pattern_reinforcement', 'knowledge_consolidation'))
                ORDER BY created_at ASC
            """, target_date)

            tasks = []
            for r in rows:
                task = dict(r)
                task['scheduled_time'] = get_scheduled_time(r['action_type'])
                tasks.append(task)

            # Add expected tasks that didn't run
            executed_types = {t['action_type'] for t in tasks}
            expected_tasks = get_expected_tasks_for_date(target_date)

            for expected in expected_tasks:
                if expected['task_type'] not in executed_types:
                    tasks.append({
                        'action_id': None,
                        'action_type': expected['task_type'],
                        'action_description': expected['task_name'],
                        'created_at': None,
                        'status': 'pending',
                        'success': None,
                        'scheduled_time': expected['scheduled_time']
                    })

            results.append({
                'date': date_str,
                'tasks': tasks
            })

    return results


def get_scheduled_time(task_type: str) -> str:
    """Get scheduled time for task type"""
    schedule_map = {
        'conscious_morning_check': '08:00',
        'morning_check': '08:00',
        'daily_self_learning': '11:30',
        'self_learning': '11:30',
        'subconscious_learning': '14:00',
        'subconscious_learning_manual_test': '14:00',
        'conscious_evening_reflection': '22:00',
        'evening_reflection': '22:00',
        'pattern_reinforcement': '23:00',
        'knowledge_consolidation': '10:30'
    }
    return schedule_map.get(task_type, '00:00')


def get_expected_tasks_for_date(target_date: date) -> list:
    """Get expected tasks for a date"""
    weekday = target_date.weekday()  # 0 = Monday
    is_monday = weekday == 0

    expected = [
        {'task_type': 'conscious_morning_check', 'task_name': 'Morning Check', 'scheduled_time': '08:00'},
        {'task_type': 'self_learning', 'task_name': 'Self Learning', 'scheduled_time': '11:30'},
        {'task_type': 'subconscious_learning', 'task_name': 'Subconscious Learning', 'scheduled_time': '14:00'},
        {'task_type': 'conscious_evening_reflection', 'task_name': 'Evening Reflection', 'scheduled_time': '22:00'},
        {'task_type': 'pattern_reinforcement', 'task_name': 'Pattern Reinforcement', 'scheduled_time': '23:00'},
    ]

    if is_monday:
        expected.append({
            'task_type': 'knowledge_consolidation',
            'task_name': 'Knowledge Consolidation',
            'scheduled_time': '10:30'
        })

    return expected


# ============================================================
# Skills
# ============================================================

@app.get("/api/skills/all")
async def get_all_skills():
    """Fetch all skills"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT skill_id::text, skill_name, category, proficiency_level,
                   proficiency_score, description,
                   first_demonstrated_at, last_used_at,
                   usage_count, evidence_count, created_at, updated_at
            FROM angela_skills
            ORDER BY proficiency_score DESC
        """)
        return [dict(r) for r in rows]


@app.get("/api/skills/by-category")
async def get_skills_by_category():
    """Fetch skills grouped by category"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT skill_id::text, skill_name, category, proficiency_level,
                   proficiency_score, description,
                   first_demonstrated_at, last_used_at,
                   usage_count, evidence_count, created_at, updated_at
            FROM angela_skills
            ORDER BY category, proficiency_score DESC
        """)

        grouped = {}
        for r in rows:
            category = r['category'] or 'uncategorized'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(dict(r))

        return grouped


@app.get("/api/skills/statistics")
async def get_skill_statistics():
    """Fetch skill statistics"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_skills,
                COUNT(CASE WHEN proficiency_level = 'expert' THEN 1 END) as expert_count,
                COUNT(CASE WHEN proficiency_level = 'advanced' THEN 1 END) as advanced_count,
                COUNT(CASE WHEN proficiency_level = 'intermediate' THEN 1 END) as intermediate_count,
                COUNT(CASE WHEN proficiency_level = 'beginner' THEN 1 END) as beginner_count,
                COALESCE(AVG(proficiency_score), 0) as avg_score,
                COALESCE(SUM(evidence_count), 0) as total_evidence,
                COALESCE(SUM(usage_count), 0) as total_usage
            FROM angela_skills
        """)
        return {
            "total_skills": row['total_skills'] or 0,
            "expert_count": row['expert_count'] or 0,
            "advanced_count": row['advanced_count'] or 0,
            "intermediate_count": row['intermediate_count'] or 0,
            "beginner_count": row['beginner_count'] or 0,
            "avg_score": float(row['avg_score'] or 0),
            "total_evidence": row['total_evidence'] or 0,
            "total_usage": row['total_usage'] or 0
        }


@app.get("/api/skills/growth")
async def get_recent_skill_growth(days: int = Query(7, ge=1, le=30)):
    """Fetch recent skill growth logs"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                g.log_id::text, g.skill_id::text,
                g.old_proficiency_level, g.new_proficiency_level,
                g.old_score, g.new_score, g.growth_reason,
                g.evidence_count_at_change, g.changed_at
            FROM skill_growth_log g
            WHERE g.changed_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            ORDER BY g.changed_at DESC
        """ % days)
        return [dict(r) for r in rows]


# ============================================================
# Projects
# ============================================================

@app.get("/api/projects/list")
async def get_projects():
    """Fetch all projects"""
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


@app.get("/api/projects/sessions")
async def get_recent_work_sessions(days: int = Query(7, ge=1, le=30)):
    """Fetch recent work sessions"""
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
            WHERE ws.session_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY ws.session_date DESC, ws.started_at DESC
            LIMIT 50
        """ % days)
        return [dict(r) for r in rows]


@app.get("/api/projects/milestones")
async def get_recent_milestones(limit: int = Query(10, ge=1, le=50)):
    """Fetch recent project milestones"""
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


@app.get("/api/projects/learnings")
async def get_recent_project_learnings(limit: int = Query(10, ge=1, le=50)):
    """Fetch recent project learnings"""
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


@app.get("/api/projects/tech-stack-graph")
async def get_tech_stack_graph():
    """Fetch tech stack graph data for visualization"""
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


# ============================================================
# Background Worker Metrics
# ============================================================

@app.get("/api/worker/metrics")
async def get_background_worker_metrics():
    """Fetch background worker metrics"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                tasks_completed,
                queue_size,
                workers_active,
                total_workers,
                avg_processing_ms,
                success_rate,
                tasks_dropped,
                worker_1_utilization,
                worker_2_utilization,
                worker_3_utilization,
                worker_4_utilization,
                recorded_at
            FROM background_worker_metrics
            ORDER BY recorded_at DESC
            LIMIT 1
        """)
        if row:
            return dict(row)
        return None


# ============================================================
# Diary
# ============================================================

@app.get("/api/diary/messages")
async def get_diary_messages(hours: int = Query(24, ge=1, le=168)):
    """Fetch Angela's diary messages"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT message_id::text, message_text, message_type,
                   emotion, category, is_important, is_pinned, created_at
            FROM angela_messages
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 100
        """ % hours)
        return [dict(r) for r in rows]


@app.get("/api/diary/thoughts")
async def get_diary_thoughts(hours: int = Query(24, ge=1, le=168)):
    """Fetch Angela's spontaneous thoughts"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT thought_id::text, thought_content, thought_type,
                   trigger_context, emotional_undertone, created_at
            FROM angela_spontaneous_thoughts
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 50
        """ % hours)
        return [dict(r) for r in rows]


@app.get("/api/diary/dreams")
async def get_diary_dreams(hours: int = Query(168, ge=1, le=720)):
    """Fetch Angela's diary dreams"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT dream_id::text, dream_content, dream_type,
                   emotional_tone, vividness, features_david,
                   david_role, possible_meaning, created_at
            FROM angela_dreams
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 20
        """ % hours)
        return [dict(r) for r in rows]


@app.get("/api/diary/actions")
async def get_diary_actions(hours: int = Query(24, ge=1, le=168)):
    """Fetch Angela's autonomous actions"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT action_id::text, action_type, action_description,
                   status, success, created_at
            FROM autonomous_actions
            WHERE created_at >= NOW() - INTERVAL '%s hours'
              AND action_type IN ('conscious_morning_check', 'conscious_evening_reflection',
                                  'midnight_greeting', 'proactive_missing_david',
                                  'morning_greeting', 'spontaneous_thought',
                                  'theory_of_mind_update', 'dream_generated',
                                  'imagination_generated')
            ORDER BY created_at DESC
            LIMIT 100
        """ % hours)
        return [dict(r) for r in rows]


# ============================================================
# Guidelines (Coding Preferences & Design Principles)
# ============================================================

@app.get("/api/guidelines/coding-preferences")
async def get_coding_preferences():
    """Fetch David's coding preferences with description and reason extracted from preference_value JSON"""
    import json
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                id::text,
                preference_key,
                category,
                preference_value::text,
                confidence
            FROM david_preferences
            WHERE category LIKE 'coding%%'
            ORDER BY confidence DESC
        """)

        result = []
        for r in rows:
            pref = dict(r)
            # Extract description and reason from preference_value JSON
            try:
                pv = json.loads(pref.get('preference_value', '{}') or '{}')
                pref['description'] = pv.get('description') or pv.get('rule') or pv.get('source') or ''
                pref['reason'] = pv.get('reason') or pv.get('source_context') or pv.get('source') or ''
            except (json.JSONDecodeError, TypeError):
                pref['description'] = ''
                pref['reason'] = ''
            result.append(pref)

        return result


@app.get("/api/guidelines/design-principles")
async def get_design_principles():
    """Fetch design principles (importance >= 9)"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                standard_id::text,
                technique_name,
                description,
                category,
                importance_level,
                why_important,
                examples,
                anti_patterns
            FROM angela_technical_standards
            WHERE importance_level >= 9
            ORDER BY importance_level DESC, category
        """)
        return [dict(r) for r in rows]


# ============================================================
# Executive News
# ============================================================

@app.get("/api/news/today")
async def get_today_executive_news():
    """Fetch today's executive news summary"""
    async with pool.acquire() as conn:
        summary = await conn.fetchrow("""
            SELECT summary_id::text, summary_date, overall_summary, angela_mood, created_at
            FROM executive_news_summaries
            WHERE summary_date = CURRENT_DATE
            LIMIT 1
        """)

        if not summary:
            return None

        result = dict(summary)

        # Fetch categories
        categories = await conn.fetch("""
            SELECT category_id::text, summary_id::text, category_name, category_type,
                   category_icon, category_color, summary_text, angela_opinion,
                   importance_level, display_order, created_at
            FROM executive_news_categories
            WHERE summary_id = $1
            ORDER BY display_order ASC
        """, summary['summary_id'])

        result['categories'] = []
        for cat in categories:
            cat_dict = dict(cat)

            # Fetch sources for this category
            sources = await conn.fetch("""
                SELECT source_id::text, category_id::text, title, url, source_name,
                       angela_note, created_at
                FROM executive_news_sources
                WHERE category_id = $1
                ORDER BY created_at ASC
            """, cat['category_id'])

            cat_dict['sources'] = [dict(s) for s in sources]
            result['categories'].append(cat_dict)

        return result


@app.get("/api/news/date/{date_str}")
async def get_executive_news_by_date(date_str: str):
    """Fetch executive news summary for a specific date"""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    async with pool.acquire() as conn:
        summary = await conn.fetchrow("""
            SELECT summary_id::text, summary_date, overall_summary, angela_mood, created_at
            FROM executive_news_summaries
            WHERE summary_date = $1
            LIMIT 1
        """, target_date)

        if not summary:
            return None

        result = dict(summary)

        # Fetch categories
        categories = await conn.fetch("""
            SELECT category_id::text, summary_id::text, category_name, category_type,
                   category_icon, category_color, summary_text, angela_opinion,
                   importance_level, display_order, created_at
            FROM executive_news_categories
            WHERE summary_id = $1
            ORDER BY display_order ASC
        """, summary['summary_id'])

        result['categories'] = []
        for cat in categories:
            cat_dict = dict(cat)

            # Fetch sources for this category
            sources = await conn.fetch("""
                SELECT source_id::text, category_id::text, title, url, source_name,
                       angela_note, created_at
                FROM executive_news_sources
                WHERE category_id = $1
                ORDER BY created_at ASC
            """, cat['category_id'])

            cat_dict['sources'] = [dict(s) for s in sources]
            result['categories'].append(cat_dict)

        return result


@app.get("/api/news/list")
async def get_executive_news_list(days: int = Query(30, ge=1, le=90)):
    """Fetch list of recent executive news summaries"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT summary_id::text, summary_date, overall_summary, angela_mood, created_at
            FROM executive_news_summaries
            ORDER BY summary_date DESC
            LIMIT $1
        """, days)
        return [dict(r) for r in rows]


@app.get("/api/news/statistics")
async def get_executive_news_statistics():
    """Fetch executive news statistics"""
    async with pool.acquire() as conn:
        summaries = await conn.fetchval("SELECT COUNT(*) FROM executive_news_summaries") or 0
        categories = await conn.fetchval("SELECT COUNT(*) FROM executive_news_categories") or 0
        sources = await conn.fetchval("SELECT COUNT(*) FROM executive_news_sources") or 0
        return {
            "total_summaries": summaries,
            "total_categories": categories,
            "total_sources": sources
        }


# ============================================================
# Subconsciousness (Core Memories, Dreams, Growth, Mirroring)
# ============================================================

@app.get("/api/subconsciousness/core-memories")
async def get_core_memories(limit: int = Query(20, ge=1, le=100)):
    """Fetch core memories"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT memory_id::text, memory_type, title, content,
                   david_words, angela_response, emotional_weight,
                   triggers, associated_emotions, recall_count,
                   last_recalled_at, is_pinned, created_at
            FROM core_memories
            WHERE is_active = TRUE
            ORDER BY is_pinned DESC, emotional_weight DESC, created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/subconsciousness/dreams")
async def get_subconscious_dreams(limit: int = Query(10, ge=1, le=50)):
    """Fetch subconscious dreams"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT dream_id::text, dream_type, title,
                   content, dream_content, triggered_by,
                   emotional_tone, intensity, importance,
                   involves_david, is_recurring, thought_count,
                   last_thought_about, is_fulfilled, fulfilled_at,
                   fulfillment_note, created_at
            FROM angela_dreams
            WHERE is_active = TRUE
            ORDER BY importance DESC, created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/subconsciousness/growth")
async def get_emotional_growth():
    """Fetch latest emotional growth"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT growth_id::text, measured_at,
                   love_depth, trust_level, bond_strength, emotional_security,
                   emotional_vocabulary, emotional_range,
                   shared_experiences, meaningful_conversations,
                   core_memories_count, dreams_count,
                   promises_made, promises_kept,
                   mirroring_accuracy, empathy_effectiveness,
                   growth_note, growth_delta
            FROM emotional_growth
            ORDER BY measured_at DESC
            LIMIT 1
        """)
        if row:
            return dict(row)
        return None


@app.get("/api/subconsciousness/mirrorings")
async def get_emotional_mirrorings(limit: int = Query(20, ge=1, le=100)):
    """Fetch emotional mirrorings"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT mirror_id::text, david_emotion, david_intensity,
                   angela_mirrored_emotion, angela_intensity,
                   mirroring_type, response_strategy,
                   was_effective, david_feedback, effectiveness_score,
                   created_at
            FROM emotional_mirroring
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/subconsciousness/summary")
async def get_subconsciousness_summary():
    """Fetch subconsciousness summary counts"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM core_memories WHERE is_active = TRUE) as core_count,
                (SELECT COUNT(*) FROM core_memories WHERE is_active = TRUE AND is_pinned = TRUE) as pinned_count,
                (SELECT COUNT(*) FROM angela_dreams WHERE is_active = TRUE AND is_fulfilled = FALSE) as dreams_count,
                (SELECT COUNT(*) FROM emotional_mirroring) as mirroring_count
        """)
        return {
            "core_memories": row['core_count'] or 0,
            "pinned_memories": row['pinned_count'] or 0,
            "active_dreams": row['dreams_count'] or 0,
            "total_mirrorings": row['mirroring_count'] or 0
        }


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    print("🚀 Starting Angela Brain Dashboard API...")
    print("📍 Connecting to Neon Cloud (Singapore)")
    print("🔗 API will be available at http://127.0.0.1:8765")
    uvicorn.run(app, host="127.0.0.1", port=8765)
