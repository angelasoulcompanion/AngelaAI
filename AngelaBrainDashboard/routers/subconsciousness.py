"""Subconsciousness (Core Memories, Dreams, Growth, Mirroring) endpoints."""
from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/subconsciousness", tags=["subconsciousness"])


@router.get("/core-memories")
async def get_core_memories(limit: int = Query(20, ge=1, le=100)):
    """Fetch core memories"""
    pool = get_pool()
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


@router.get("/dreams")
async def get_subconscious_dreams(limit: int = Query(10, ge=1, le=50)):
    """Fetch subconscious dreams"""
    pool = get_pool()
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


@router.get("/growth")
async def get_emotional_growth():
    """Fetch latest emotional growth"""
    pool = get_pool()
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


@router.get("/mirrorings")
async def get_emotional_mirrorings(limit: int = Query(20, ge=1, le=100)):
    """Fetch emotional mirrorings"""
    pool = get_pool()
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


@router.get("/summary")
async def get_subconsciousness_summary():
    """Fetch subconsciousness summary counts"""
    pool = get_pool()
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
