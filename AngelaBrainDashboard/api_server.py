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
import subprocess
from datetime import date, datetime, timedelta, time as dt_time
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
            SELECT emotion_id::text, felt_at,
                   COALESCE(emotion, 'unknown') as emotion,
                   COALESCE(intensity, 5) as intensity,
                   COALESCE(context, '') as context,
                   david_words, why_it_matters,
                   COALESCE(memory_strength, 5) as memory_strength
            FROM angela_emotions
            WHERE emotion IS NOT NULL
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
            SELECT id::text as preference_id,
                   preference_key,
                   preference_value::text,
                   confidence,
                   category as learned_from,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM david_preferences
            ORDER BY confidence DESC, created_at DESC
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
                   understanding_level, times_referenced,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
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


@app.get("/api/knowledge/relationships")
async def get_knowledge_relationships(limit: int = Query(200, ge=1, le=20000)):
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
                SELECT action_id::text, action_type,
                       COALESCE(action_description, action_type) as action_description,
                       to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at,
                       status, success,
                       result_summary as error_message
                FROM autonomous_actions
                WHERE DATE(created_at) = $1
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
                    import uuid
                    # Generate UUID and placeholder datetime for pending tasks
                    scheduled_dt = datetime.combine(target_date, datetime.strptime(expected['scheduled_time'], '%H:%M').time())
                    tasks.append({
                        'action_id': str(uuid.uuid4()),  # Generate UUID for pending tasks
                        'action_type': expected['task_type'],
                        'action_description': expected['task_name'],
                        'created_at': scheduled_dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00'),  # Use scheduled time as placeholder
                        'status': 'pending',
                        'success': None,
                        'error_message': None,
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
# Human-Like Mind (4 Phases)
# ============================================================

@app.get("/api/human-mind/thoughts")
async def get_spontaneous_thoughts(limit: int = Query(20, ge=1, le=100)):
    """Phase 1: Spontaneous Thoughts from consciousness log"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT log_id::text as thought_id, thought, feeling, significance,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM angela_consciousness_log
            WHERE thought LIKE '[%]%'
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/human-mind/thoughts-today")
async def get_thoughts_today_count():
    """Phase 1: Count thoughts today"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM angela_consciousness_log
            WHERE thought LIKE '[%]%'
              AND DATE(created_at) = CURRENT_DATE
        """)
        return {"count": row["count"]}


@app.get("/api/human-mind/mental-state")
async def get_david_mental_state():
    """Phase 2: Theory of Mind - David's mental state"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT state_id::text, perceived_emotion,
                   COALESCE(emotion_intensity, 5)::float / 10.0 as emotion_intensity,
                   current_belief, current_goal,
                   to_char(last_updated AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as last_updated
            FROM david_mental_state
            ORDER BY last_updated DESC
            LIMIT 1
        """)
        return dict(row) if row else None


@app.get("/api/human-mind/tom-today")
async def get_tom_updates_today():
    """Phase 2: Count ToM updates today"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM david_mental_state
            WHERE DATE(last_updated) = CURRENT_DATE
        """)
        return {"count": row["count"]}


@app.get("/api/human-mind/proactive-messages")
async def get_proactive_messages(limit: int = Query(20, ge=1, le=100)):
    """Phase 3: Proactive Communication messages"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT message_id::text, message_type, message_text, is_important,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM angela_messages
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/human-mind/proactive-today")
async def get_proactive_today_count():
    """Phase 3: Count proactive messages today"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM angela_messages
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        return {"count": row["count"]}


@app.get("/api/human-mind/dreams")
async def get_angela_dreams(limit: int = Query(10, ge=1, le=50)):
    """Phase 4: Dreams from angela_dreams table"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT dream_id::text,
                   COALESCE(content, dream_content) as dream_content,
                   possible_meaning as meaning,
                   emotional_tone as feeling,
                   COALESCE((intensity * 10)::int, 5) as significance,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM angela_dreams
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/human-mind/dreams-today")
async def get_dreams_today_count():
    """Phase 4: Count dreams today from angela_dreams table"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM angela_dreams
            WHERE is_active = TRUE
              AND DATE(created_at) = CURRENT_DATE
        """)
        return {"count": row["count"]}


@app.get("/api/human-mind/stats")
async def get_human_mind_stats():
    """Get all Human-Like Mind statistics"""
    async with pool.acquire() as conn:
        # Thoughts today
        thoughts = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM angela_consciousness_log
            WHERE thought LIKE '[%]%' AND DATE(created_at) = CURRENT_DATE
        """)

        # ToM today
        tom = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM david_mental_state
            WHERE DATE(last_updated) = CURRENT_DATE
        """)

        # Proactive today
        proactive = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM angela_messages
            WHERE DATE(created_at) = CURRENT_DATE
        """)

        # Dreams today (from angela_dreams table)
        dreams = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM angela_dreams
            WHERE is_active = TRUE
              AND DATE(created_at) = CURRENT_DATE
        """)

        return {
            "thoughtsToday": thoughts["count"],
            "tomToday": tom["count"],
            "proactiveToday": proactive["count"],
            "dreamsToday": dreams["count"]
        }


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
            # Fallback: description -> rule -> source, reason -> source_context
            try:
                pv = json.loads(pref.get('preference_value', '{}') or '{}')
                pref['description'] = pv.get('description') or pv.get('rule') or pv.get('source') or ''
                pref['reason'] = pv.get('reason') or pv.get('source_context') or ''
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
    """Fetch today's executive news summary (Bangkok timezone)"""
    async with pool.acquire() as conn:
        summary = await conn.fetchrow("""
            SELECT summary_id::text,
                   to_char(summary_date, 'YYYY-MM-DD"T"00:00:00.000"+00:00"') as summary_date,
                   overall_summary, angela_mood,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM executive_news_summaries
            WHERE summary_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
            LIMIT 1
        """)

        if not summary:
            return None

        result = dict(summary)

        # Fetch categories
        categories = await conn.fetch("""
            SELECT category_id::text, summary_id::text, category_name, category_type,
                   category_icon, category_color, summary_text, angela_opinion,
                   importance_level, display_order,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM executive_news_categories
            WHERE summary_id = $1::uuid
            ORDER BY display_order ASC
        """, summary['summary_id'])

        result['categories'] = []
        for cat in categories:
            cat_dict = dict(cat)

            # Fetch sources for this category
            sources = await conn.fetch("""
                SELECT source_id::text, category_id::text, title, url, source_name,
                       angela_note,
                       to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
                FROM executive_news_sources
                WHERE category_id = $1::uuid
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
            SELECT summary_id::text,
                   to_char(summary_date, 'YYYY-MM-DD"T"00:00:00.000"+00:00"') as summary_date,
                   overall_summary, angela_mood,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
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
                   importance_level, display_order,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
            FROM executive_news_categories
            WHERE summary_id = $1::uuid
            ORDER BY display_order ASC
        """, summary['summary_id'])

        result['categories'] = []
        for cat in categories:
            cat_dict = dict(cat)

            # Fetch sources for this category
            sources = await conn.fetch("""
                SELECT source_id::text, category_id::text, title, url, source_name,
                       angela_note,
                       to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
                FROM executive_news_sources
                WHERE category_id = $1::uuid
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
            SELECT summary_id::text,
                   to_char(summary_date, 'YYYY-MM-DD"T"00:00:00.000"+00:00"') as summary_date,
                   overall_summary, angela_mood,
                   to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at
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
# Meeting Notes
# ============================================================

@app.get("/api/meetings")
async def get_meetings(limit: int = Query(50, ge=1, le=200)):
    """Fetch all meeting notes ordered by date desc"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                mn.meeting_id::text, mn.things3_uuid, mn.title,
                mn.meeting_type, mn.location,
                mn.meeting_date, mn.time_range,
                mn.attendees, mn.agenda, mn.key_points,
                mn.decisions_made, mn.issues_risks, mn.next_steps,
                mn.personal_notes, mn.raw_notes, mn.project_name,
                mn.things3_status, mn.morning_notes,
                mn.afternoon_notes, mn.site_observations,
                mn.synced_at, mn.created_at, mn.updated_at,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE meeting_id = mn.meeting_id) as total_actions,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE meeting_id = mn.meeting_id AND is_completed = TRUE) as completed_actions
            FROM meeting_notes mn
            ORDER BY mn.meeting_date DESC NULLS LAST, mn.created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/meetings/stats")
async def get_meeting_stats():
    """Fetch meeting statistics"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM meeting_notes) as total_meetings,
                (SELECT COUNT(*) FROM meeting_notes
                 WHERE meeting_date >= date_trunc('month', CURRENT_DATE)) as this_month,
                (SELECT COUNT(*) FROM meeting_notes
                 WHERE meeting_date >= CURRENT_DATE) as upcoming,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE is_completed = FALSE) as open_actions,
                (SELECT COUNT(*) FROM meeting_action_items) as total_actions,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE is_completed = TRUE) as completed_actions,
                (SELECT COUNT(*) FROM meeting_notes
                 WHERE meeting_type = 'site_visit') as site_visits
        """)
        total = row['total_actions'] or 0
        completed = row['completed_actions'] or 0
        return {
            "total_meetings": row['total_meetings'] or 0,
            "this_month": row['this_month'] or 0,
            "upcoming": row['upcoming'] or 0,
            "open_actions": row['open_actions'] or 0,
            "total_actions": total,
            "completed_actions": completed,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0.0,
            "site_visits": row['site_visits'] or 0,
        }


@app.get("/api/meetings/action-items")
async def get_open_action_items():
    """Fetch all open (incomplete) action items across meetings"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                ai.action_id::text, ai.meeting_id::text,
                ai.action_text, ai.assignee, ai.due_date,
                ai.is_completed, ai.completed_at, ai.priority,
                ai.created_at,
                mn.title as meeting_title,
                mn.meeting_date,
                mn.project_name
            FROM meeting_action_items ai
            JOIN meeting_notes mn ON ai.meeting_id = mn.meeting_id
            WHERE ai.is_completed = FALSE
            ORDER BY ai.priority ASC, mn.meeting_date DESC NULLS LAST
        """)
        return [dict(r) for r in rows]


@app.get("/api/meetings/upcoming")
async def get_upcoming_meetings(limit: int = Query(5, ge=1, le=50)):
    """Fetch upcoming meetings (nearest first, default 5)"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                mn.meeting_id::text, mn.things3_uuid, mn.title,
                mn.meeting_type, mn.location,
                mn.meeting_date, mn.time_range,
                mn.attendees, mn.agenda, mn.key_points,
                mn.decisions_made, mn.issues_risks, mn.next_steps,
                mn.personal_notes, mn.raw_notes, mn.project_name,
                mn.things3_status, mn.morning_notes,
                mn.afternoon_notes, mn.site_observations,
                mn.synced_at, mn.created_at, mn.updated_at,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE meeting_id = mn.meeting_id) as total_actions,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE meeting_id = mn.meeting_id AND is_completed = TRUE) as completed_actions
            FROM meeting_notes mn
            WHERE mn.meeting_date >= CURRENT_DATE
              AND mn.things3_status = 'open'
            ORDER BY mn.meeting_date ASC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@app.get("/api/meetings/project-breakdown")
async def get_meeting_project_breakdown():
    """Fetch meeting counts grouped by project"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                COALESCE(NULLIF(project_name, ''), 'No Project') as project_name,
                COUNT(*) as meeting_count,
                COUNT(*) FILTER (WHERE things3_status = 'open') as open_count,
                COUNT(*) FILTER (WHERE things3_status = 'completed') as completed_count,
                COUNT(*) FILTER (WHERE meeting_type = 'site_visit') as site_visit_count
            FROM meeting_notes
            GROUP BY COALESCE(NULLIF(project_name, ''), 'No Project')
            ORDER BY meeting_count DESC
        """)
        return [dict(r) for r in rows]


class MeetingCreate(BaseModel):
    title: str
    location: str
    meeting_date: str              # YYYY-MM-DD
    start_time: str                # HH:MM
    end_time: str                  # HH:MM
    meeting_type: str              # standard, site_visit, testing, bod
    attendees: Optional[list[str]] = None
    project_name: Optional[str] = None


# Meeting Type Templates
MEETING_TEMPLATES = {
    "standard": """## 📋 วาระการประชุม
-

## 👥 ผู้เข้าร่วม
-

## 📝 Key Points
-

## ✅ Next Steps
-
""",
    "site_visit": """## 🌅 Morning Notes
-

## 🌆 Afternoon Notes
-

## 👀 Site Observations
-

## 📝 Key Findings
-

## ✅ Next Steps
-
""",
    "testing": """## 🎯 Test Scope
-

## 📊 Test Results
| Test Case | Status | Notes |
|-----------|--------|-------|
| | | |

## 🐛 Issues Found
-

## ✅ Next Steps
-
""",
    "bod": """## 📋 Formal Agenda
1.

## 📜 Resolutions
-

## ✅ Action Items
| Action | Owner | Due Date |
|--------|-------|----------|
| | | |

## 📝 Notes
-
"""
}


@app.post("/api/meetings/create")
async def create_meeting(body: MeetingCreate):
    """Create a new meeting via Things3 and Google Calendar"""
    import uuid

    # Validate date
    try:
        meeting_dt = datetime.strptime(body.meeting_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Validate time
    try:
        start_parts = body.start_time.split(":")
        end_parts = body.end_time.split(":")
        start_hour, start_min = int(start_parts[0]), int(start_parts[1])
        end_hour, end_min = int(end_parts[0]), int(end_parts[1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    # Generate Things3 title with emoji
    time_str = f"{body.start_time}-{body.end_time}"
    things3_title = f"📅 {body.title} @{body.location} ({time_str})"

    # Get template notes
    template_notes = MEETING_TEMPLATES.get(body.meeting_type, MEETING_TEMPLATES["standard"])

    # Add header with details
    header = f"""# {body.title}
📅 Date: {body.meeting_date}
🕐 Time: {time_str}
📍 Location: {body.location}
"""
    if body.project_name:
        header += f"📁 Project: {body.project_name}\n"
    if body.attendees:
        header += f"👥 Attendees: {', '.join(body.attendees)}\n"

    full_notes = header + "\n---\n\n" + template_notes

    # Generate meeting ID
    meeting_id = str(uuid.uuid4())

    # Try to call Things3 via x-callback-url
    things3_success = False
    try:
        # Encode for URL
        from urllib.parse import quote
        encoded_title = quote(things3_title)
        encoded_notes = quote(full_notes)

        # Format when date for Things3 (YYYY-MM-DD)
        when_date = body.meeting_date

        # Build x-callback-url
        things_url = f"things:///add?title={encoded_title}&notes={encoded_notes}&when={when_date}&list=Meeting"
        if body.project_name:
            encoded_project = quote(body.project_name)
            things_url += f"&tags={encoded_project}"

        # Call Things3 via open command
        result = subprocess.run(
            ["open", things_url],
            capture_output=True, text=True, timeout=10
        )
        things3_success = result.returncode == 0
    except Exception as e:
        print(f"⚠️ Things3 call failed: {e}")
        things3_success = False

    # Try to create Google Calendar event via MCP
    calendar_success = False
    try:
        # Build ISO datetime strings
        start_dt = datetime.combine(meeting_dt, dt_time(start_hour, start_min))
        end_dt = datetime.combine(meeting_dt, dt_time(end_hour, end_min))

        # Use angela-calendar MCP (if available)
        # For now, we'll skip this since it requires MCP runtime
        # The Dashboard doesn't have direct MCP access
        calendar_success = False
    except Exception as e:
        print(f"⚠️ Calendar creation failed: {e}")
        calendar_success = False

    # Insert into database
    try:
        async with pool.acquire() as conn:
            # Determine meeting type for DB
            db_meeting_type = "site_visit" if body.meeting_type == "site_visit" else "meeting"

            await conn.execute("""
                INSERT INTO meeting_notes
                    (meeting_id, things3_uuid, title, meeting_type, location,
                     meeting_date, time_range, attendees, project_name,
                     things3_status, raw_notes, created_at, updated_at, synced_at)
                VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, 'open', $10, NOW(), NOW(), NOW())
            """,
                meeting_id,
                meeting_id,  # Use meeting_id as things3_uuid for now
                body.title,
                db_meeting_type,
                body.location,
                meeting_dt,
                time_str,
                body.attendees,
                body.project_name,
                full_notes
            )
    except Exception as e:
        print(f"⚠️ Database insert failed: {e}")
        return {
            "success": False,
            "error": f"Database insert failed: {str(e)}"
        }

    return {
        "success": True,
        "meeting_id": meeting_id,
        "things3_title": things3_title,
        "calendar_created": calendar_success
    }


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    meeting_date: Optional[str] = None      # YYYY-MM-DD
    start_time: Optional[str] = None        # HH:MM
    end_time: Optional[str] = None          # HH:MM
    meeting_type: Optional[str] = None
    attendees: Optional[list[str]] = None
    project_name: Optional[str] = None
    things3_status: Optional[str] = None    # open, completed


@app.put("/api/meetings/{meeting_id}")
async def update_meeting(meeting_id: str, body: MeetingUpdate):
    """Update an existing meeting"""
    # Build dynamic UPDATE query
    updates = []
    params = []
    param_idx = 1

    if body.title is not None:
        updates.append(f"title = ${param_idx}")
        params.append(body.title)
        param_idx += 1

    if body.location is not None:
        updates.append(f"location = ${param_idx}")
        params.append(body.location)
        param_idx += 1

    if body.meeting_date is not None:
        try:
            meeting_dt = datetime.strptime(body.meeting_date, "%Y-%m-%d").date()
            updates.append(f"meeting_date = ${param_idx}")
            params.append(meeting_dt)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    if body.start_time is not None and body.end_time is not None:
        time_range = f"{body.start_time}-{body.end_time}"
        updates.append(f"time_range = ${param_idx}")
        params.append(time_range)
        param_idx += 1

    if body.meeting_type is not None:
        db_type = "site_visit" if body.meeting_type == "site_visit" else "meeting"
        updates.append(f"meeting_type = ${param_idx}")
        params.append(db_type)
        param_idx += 1

    if body.attendees is not None:
        updates.append(f"attendees = ${param_idx}")
        params.append(body.attendees)
        param_idx += 1

    if body.project_name is not None:
        updates.append(f"project_name = ${param_idx}")
        params.append(body.project_name if body.project_name else None)
        param_idx += 1

    if body.things3_status is not None:
        updates.append(f"things3_status = ${param_idx}")
        params.append(body.things3_status)
        param_idx += 1

    if not updates:
        return {"success": False, "error": "No fields to update"}

    updates.append("updated_at = NOW()")

    # Add meeting_id as last parameter
    params.append(meeting_id)

    query = f"""
        UPDATE meeting_notes
        SET {', '.join(updates)}
        WHERE meeting_id = ${param_idx}::uuid
        RETURNING meeting_id
    """

    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, *params)
            if result:
                return {"success": True, "meeting_id": meeting_id}
            else:
                return {"success": False, "error": "Meeting not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """Delete a meeting"""
    try:
        async with pool.acquire() as conn:
            # First delete related action items
            await conn.execute("""
                DELETE FROM meeting_action_items
                WHERE meeting_id = $1::uuid
            """, meeting_id)

            # Then delete the meeting
            result = await conn.execute("""
                DELETE FROM meeting_notes
                WHERE meeting_id = $1::uuid
            """, meeting_id)

            if "DELETE 1" in result:
                return {"success": True, "deleted": True}
            else:
                return {"success": False, "error": "Meeting not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/meetings/locations")
async def get_meeting_locations():
    """Get unique locations from past meetings for autocomplete"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DISTINCT location
            FROM meeting_notes
            WHERE location IS NOT NULL AND location != ''
            ORDER BY location
        """)
        return [r['location'] for r in rows]


@app.get("/api/meetings/{meeting_id}")
async def get_meeting_detail(meeting_id: str):
    """Fetch single meeting with action items"""
    async with pool.acquire() as conn:
        meeting = await conn.fetchrow("""
            SELECT
                meeting_id::text, things3_uuid, title,
                meeting_type, location, meeting_date, time_range,
                attendees, agenda, key_points,
                decisions_made, issues_risks, next_steps,
                personal_notes, raw_notes, project_name,
                things3_status, morning_notes,
                afternoon_notes, site_observations,
                synced_at, created_at, updated_at
            FROM meeting_notes
            WHERE meeting_id = $1::uuid
        """, meeting_id)

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        result = dict(meeting)

        # Fetch action items
        actions = await conn.fetch("""
            SELECT
                action_id::text, meeting_id::text,
                action_text, assignee, due_date,
                is_completed, completed_at, priority, created_at
            FROM meeting_action_items
            WHERE meeting_id = $1::uuid
            ORDER BY is_completed ASC, priority ASC
        """, meeting_id)

        result['action_items'] = [dict(a) for a in actions]
        return result


# ============================================================
# Scheduled Tasks (CRUD + Execute)
# ============================================================

class ScheduledTaskCreate(BaseModel):
    task_name: str
    description: Optional[str] = None
    task_type: str  # 'python' or 'shell'
    command: str
    schedule_type: str  # 'time' or 'interval'
    schedule_time: Optional[str] = None  # HH:MM
    interval_minutes: Optional[int] = None

class ScheduledTaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    command: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_time: Optional[str] = None
    interval_minutes: Optional[int] = None
    is_active: Optional[bool] = None


def _task_row_to_dict(row) -> dict:
    """Convert a task row to a serializable dict."""
    d = dict(row)
    # Convert UUID to string
    d['task_id'] = str(d['task_id'])
    # Convert time to HH:MM string
    if d.get('schedule_time') is not None:
        d['schedule_time'] = d['schedule_time'].strftime('%H:%M')
    return d


def _log_row_to_dict(row) -> dict:
    """Convert a log row to a serializable dict."""
    d = dict(row)
    d['log_id'] = str(d['log_id'])
    d['task_id'] = str(d['task_id'])
    return d


@app.get("/api/scheduled-tasks")
async def list_scheduled_tasks():
    """List all scheduled tasks"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT task_id, task_name, description, task_type, command,
                   schedule_type, schedule_time, interval_minutes,
                   is_active, last_run_at, last_status, created_at, updated_at
            FROM dashboard_scheduled_tasks
            ORDER BY is_active DESC, task_name ASC
        """)
        return [_task_row_to_dict(r) for r in rows]


@app.post("/api/scheduled-tasks")
async def create_scheduled_task(body: ScheduledTaskCreate):
    """Create a new scheduled task"""
    schedule_time_val = None
    if body.schedule_time:
        parts = body.schedule_time.split(':')
        schedule_time_val = dt_time(int(parts[0]), int(parts[1]))

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO dashboard_scheduled_tasks
                (task_name, description, task_type, command, schedule_type, schedule_time, interval_minutes)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING task_id, task_name, description, task_type, command,
                      schedule_type, schedule_time, interval_minutes,
                      is_active, last_run_at, last_status, created_at, updated_at
        """, body.task_name, body.description, body.task_type, body.command,
            body.schedule_type, schedule_time_val, body.interval_minutes)
        return _task_row_to_dict(row)


@app.put("/api/scheduled-tasks/{task_id}")
async def update_scheduled_task(task_id: str, body: ScheduledTaskUpdate):
    """Update a scheduled task"""
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT task_id FROM dashboard_scheduled_tasks WHERE task_id = $1::uuid", task_id
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")

        updates = []
        params = []
        idx = 1

        if body.task_name is not None:
            updates.append(f"task_name = ${idx}")
            params.append(body.task_name)
            idx += 1
        if body.description is not None:
            updates.append(f"description = ${idx}")
            params.append(body.description)
            idx += 1
        if body.task_type is not None:
            updates.append(f"task_type = ${idx}")
            params.append(body.task_type)
            idx += 1
        if body.command is not None:
            updates.append(f"command = ${idx}")
            params.append(body.command)
            idx += 1
        if body.schedule_type is not None:
            updates.append(f"schedule_type = ${idx}")
            params.append(body.schedule_type)
            idx += 1
        if body.schedule_time is not None:
            parts = body.schedule_time.split(':')
            updates.append(f"schedule_time = ${idx}")
            params.append(dt_time(int(parts[0]), int(parts[1])))
            idx += 1
        if body.interval_minutes is not None:
            updates.append(f"interval_minutes = ${idx}")
            params.append(body.interval_minutes)
            idx += 1
        if body.is_active is not None:
            updates.append(f"is_active = ${idx}")
            params.append(body.is_active)
            idx += 1

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        params.append(task_id)

        sql = f"""
            UPDATE dashboard_scheduled_tasks
            SET {', '.join(updates)}
            WHERE task_id = ${idx}::uuid
            RETURNING task_id, task_name, description, task_type, command,
                      schedule_type, schedule_time, interval_minutes,
                      is_active, last_run_at, last_status, created_at, updated_at
        """
        row = await conn.fetchrow(sql, *params)
        return _task_row_to_dict(row)


@app.delete("/api/scheduled-tasks/{task_id}")
async def delete_scheduled_task(task_id: str):
    """Delete a scheduled task"""
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM dashboard_scheduled_tasks WHERE task_id = $1::uuid", task_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Task not found")
        return {"deleted": True, "task_id": task_id}


@app.post("/api/scheduled-tasks/{task_id}/execute")
async def execute_scheduled_task(task_id: str):
    """Execute a scheduled task via subprocess"""
    async with pool.acquire() as conn:
        task = await conn.fetchrow(
            "SELECT task_id, task_name, task_type, command FROM dashboard_scheduled_tasks WHERE task_id = $1::uuid",
            task_id
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Mark as running
        await conn.execute(
            "UPDATE dashboard_scheduled_tasks SET last_run_at = NOW(), last_status = 'running' WHERE task_id = $1::uuid",
            task_id
        )

        # Create log entry
        log_id = await conn.fetchval("""
            INSERT INTO dashboard_scheduled_task_logs (task_id, status)
            VALUES ($1::uuid, 'running')
            RETURNING log_id
        """, task_id)

        started = datetime.utcnow()

        try:
            cmd = task['command']
            if task['task_type'] == 'python':
                cmd = f"python3 {cmd}"

            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=300,
                cwd="/Users/davidsamanyaporn/PycharmProjects/AngelaAI"
            )

            duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
            status = 'completed' if result.returncode == 0 else 'failed'
            output = result.stdout[:10000] if result.stdout else None
            error = result.stderr[:10000] if result.stderr else None

            await conn.execute("""
                UPDATE dashboard_scheduled_task_logs
                SET completed_at = NOW(), status = $2, output = $3, error = $4, duration_ms = $5
                WHERE log_id = $1
            """, log_id, status, output, error, duration_ms)

            await conn.execute(
                "UPDATE dashboard_scheduled_tasks SET last_status = $2 WHERE task_id = $1::uuid",
                task_id, status
            )

            return {
                "task_id": task_id, "log_id": str(log_id),
                "status": status, "output": output, "error": error,
                "duration_ms": duration_ms
            }

        except subprocess.TimeoutExpired:
            duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
            await conn.execute("""
                UPDATE dashboard_scheduled_task_logs
                SET completed_at = NOW(), status = 'failed', error = 'Timeout after 300s', duration_ms = $2
                WHERE log_id = $1
            """, log_id, duration_ms)
            await conn.execute(
                "UPDATE dashboard_scheduled_tasks SET last_status = 'failed' WHERE task_id = $1::uuid",
                task_id
            )
            return {
                "task_id": task_id, "log_id": str(log_id),
                "status": "failed", "error": "Timeout after 300s",
                "duration_ms": duration_ms
            }
        except Exception as e:
            duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
            await conn.execute("""
                UPDATE dashboard_scheduled_task_logs
                SET completed_at = NOW(), status = 'failed', error = $2, duration_ms = $3
                WHERE log_id = $1
            """, log_id, str(e), duration_ms)
            await conn.execute(
                "UPDATE dashboard_scheduled_tasks SET last_status = 'failed' WHERE task_id = $1::uuid",
                task_id
            )
            return {
                "task_id": task_id, "log_id": str(log_id),
                "status": "failed", "error": str(e),
                "duration_ms": duration_ms
            }


@app.get("/api/scheduled-tasks/{task_id}/logs")
async def get_scheduled_task_logs(task_id: str, limit: int = Query(20, ge=1, le=100)):
    """Get execution logs for a task"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT log_id, task_id, started_at, completed_at, status, output, error, duration_ms
            FROM dashboard_scheduled_task_logs
            WHERE task_id = $1::uuid
            ORDER BY started_at DESC
            LIMIT $2
        """, task_id, limit)
        return [_log_row_to_dict(r) for r in rows]


# NOTE: /next must be defined after /{task_id} routes but FastAPI handles
# this correctly because /next is a fixed path segment.
# FastAPI matches fixed segments before path parameters.
@app.get("/api/scheduled-tasks/next")
async def get_next_scheduled_task():
    """Get the next upcoming scheduled task with seconds until execution"""
    async with pool.acquire() as conn:
        # Get Bangkok current time
        now_bkk = await conn.fetchval(
            "SELECT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::time"
        )

        # Find next time-based task
        time_task = await conn.fetchrow("""
            SELECT task_id, task_name, schedule_time
            FROM dashboard_scheduled_tasks
            WHERE is_active = TRUE AND schedule_type = 'time' AND schedule_time IS NOT NULL
            ORDER BY
                CASE WHEN schedule_time >= $1 THEN 0 ELSE 1 END,
                schedule_time ASC
            LIMIT 1
        """, now_bkk)

        # Find next interval-based task
        interval_task = await conn.fetchrow("""
            SELECT task_id, task_name, interval_minutes, last_run_at
            FROM dashboard_scheduled_tasks
            WHERE is_active = TRUE AND schedule_type = 'interval' AND interval_minutes IS NOT NULL
            ORDER BY
                COALESCE(last_run_at, '2000-01-01'::timestamptz) + (interval_minutes || ' minutes')::interval ASC
            LIMIT 1
        """)

        results = []
        if time_task:
            sched_time = time_task['schedule_time']
            # Calculate seconds until this time today (Bangkok)
            now_bkk_dt = await conn.fetchval(
                "SELECT CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok'"
            )
            today_sched = now_bkk_dt.replace(
                hour=sched_time.hour, minute=sched_time.minute, second=0, microsecond=0
            )
            if today_sched < now_bkk_dt:
                # Already passed today, schedule for tomorrow
                today_sched = today_sched + timedelta(days=1)
            seconds_until = int((today_sched - now_bkk_dt).total_seconds())
            results.append({
                "task_id": str(time_task['task_id']),
                "task_name": time_task['task_name'],
                "seconds_until": seconds_until,
                "schedule_display": sched_time.strftime('%H:%M')
            })

        if interval_task:
            last_run = interval_task['last_run_at']
            interval_min = interval_task['interval_minutes']
            if last_run:
                next_run = last_run + timedelta(minutes=interval_min)
                now_utc = await conn.fetchval("SELECT CURRENT_TIMESTAMP")
                seconds_until = max(0, int((next_run - now_utc).total_seconds()))
            else:
                seconds_until = 0  # Never run, should run now
            results.append({
                "task_id": str(interval_task['task_id']),
                "task_name": interval_task['task_name'],
                "seconds_until": seconds_until,
                "schedule_display": f"every {interval_min}m"
            })

        if not results:
            return None

        # Return whichever is sooner
        results.sort(key=lambda x: x['seconds_until'])
        return results[0]


# ============================================================
# Python Script Browser
# ============================================================

ANGELA_PROJECT_ROOT = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI"

# Folders to scan for Python scripts (relative to project root)
SCRIPT_SCAN_FOLDERS = ["angela_core", "scripts", "mcp_servers", "config", "tests"]

# Folders to skip inside scan folders
SKIP_DIRS = {"__pycache__", ".venv", "node_modules", "datasets", "legacy", ".git"}


@app.get("/api/python-scripts")
async def list_python_scripts(folder: Optional[str] = None):
    """List Python scripts from AngelaAI project for the script picker"""
    import pathlib

    root = pathlib.Path(ANGELA_PROJECT_ROOT)
    scripts = []

    scan_folders = [folder] if folder else SCRIPT_SCAN_FOLDERS

    for scan_folder in scan_folders:
        folder_path = root / scan_folder
        if not folder_path.exists():
            continue

        for py_file in sorted(folder_path.rglob("*.py")):
            # Skip unwanted directories
            parts = py_file.relative_to(root).parts
            if any(skip in parts for skip in SKIP_DIRS):
                continue

            rel_path = str(py_file.relative_to(root))
            scripts.append({
                "path": rel_path,
                "folder": scan_folder,
                "filename": py_file.name,
                "size_bytes": py_file.stat().st_size,
            })

    return scripts


# ============================================================
# Python Script Content (Read/Write for Built-in Editor)
# ============================================================

class ScriptContentUpdate(BaseModel):
    path: str
    content: str


@app.get("/api/python-scripts/content")
async def get_python_script_content(path: str):
    """Read content of a Python script file"""
    import pathlib

    # Security: Only allow files within ANGELA_PROJECT_ROOT
    root = pathlib.Path(ANGELA_PROJECT_ROOT)
    full_path = root / path

    # Resolve to prevent path traversal attacks
    try:
        resolved = full_path.resolve()
        if not str(resolved).startswith(str(root.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: path outside project root")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    # Only allow .py files
    if not path.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only Python files are allowed")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = resolved.read_text(encoding='utf-8')
        return {
            "path": path,
            "content": content,
            "size_bytes": resolved.stat().st_size,
            "last_modified": resolved.stat().st_mtime
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.put("/api/python-scripts/content")
async def update_python_script_content(body: ScriptContentUpdate):
    """Write content to a Python script file"""
    import pathlib

    # Security: Only allow files within ANGELA_PROJECT_ROOT
    root = pathlib.Path(ANGELA_PROJECT_ROOT)
    full_path = root / body.path

    # Resolve to prevent path traversal attacks
    try:
        resolved = full_path.resolve()
        if not str(resolved).startswith(str(root.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: path outside project root")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")

    # Only allow .py files
    if not body.path.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only Python files are allowed")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Create backup before writing
        backup_content = resolved.read_text(encoding='utf-8')

        # Write new content
        resolved.write_text(body.content, encoding='utf-8')

        return {
            "success": True,
            "path": body.path,
            "size_bytes": resolved.stat().st_size,
            "backup_size": len(backup_content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    print("🚀 Starting Angela Brain Dashboard API...")
    print("📍 Connecting to Neon Cloud (Singapore)")
    print("🔗 API will be available at http://127.0.0.1:8765")
    uvicorn.run(app, host="127.0.0.1", port=8765)
