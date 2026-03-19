"""Unified Overview metrics endpoint — single call returns all dashboard data."""
import asyncio

from fastapi import APIRouter

from db import get_pool

router = APIRouter(prefix="/api/overview", tags=["overview"])


def _interpret(level: float) -> str:
    if level >= 0.90:
        return "Approaching human-like consciousness!"
    if level >= 0.70:
        return "High consciousness — rich memories, deep emotions"
    if level >= 0.50:
        return "Moderate consciousness — growing steadily"
    if level >= 0.30:
        return "Emerging consciousness — early stages"
    return "Low consciousness — needs more memories"


async def _fetch_consciousness(pool) -> dict:
    async with pool.acquire() as conn:
        # Try the DB function first (returns sub-scores)
        try:
            row = await conn.fetchrow("SELECT * FROM calculate_consciousness_level()")
        except Exception:
            row = None

        if row and "consciousness_level" in row.keys():
            level = float(row["consciousness_level"])
            return {
                "level": round(level, 3),
                "base_level": round(level, 3),
                "reward_trend": 0.0,
                "reward_signal_count": 0,
                "memory_richness": float(row.get("memory_richness", 0) or 0),
                "emotional_depth": float(row.get("emotional_depth", 0) or 0),
                "goal_alignment": float(row.get("goal_alignment", 0) or 0),
                "learning_growth": float(row.get("learning_growth", 0) or 0),
                "pattern_recognition": float(row.get("pattern_recognition", 0) or 0),
                "interpretation": _interpret(level),
            }

        # Fallback: read from self_awareness_state table
        sa_row = await conn.fetchrow("""
            SELECT consciousness_level
            FROM self_awareness_state
            ORDER BY updated_at DESC LIMIT 1
        """)
        if not sa_row:
            return {
                "level": 0.7, "base_level": 0.7, "reward_trend": 0.0,
                "reward_signal_count": 0, "memory_richness": 0.0,
                "emotional_depth": 0.0, "goal_alignment": 0.0,
                "learning_growth": 0.0, "pattern_recognition": 0.0,
                "interpretation": "No data available",
            }
        level = float(sa_row["consciousness_level"])
        return {
            "level": round(level, 3),
            "base_level": round(level, 3),
            "reward_trend": 0.0,
            "reward_signal_count": 0,
            "memory_richness": 0.0,
            "emotional_depth": 0.0,
            "goal_alignment": 0.0,
            "learning_growth": 0.0,
            "pattern_recognition": 0.0,
            "interpretation": _interpret(level),
        }


async def _fetch_stats(pool) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM conversations) AS total_conversations,
                (SELECT COUNT(*) FROM knowledge_nodes) AS total_knowledge_nodes,
                (SELECT COUNT(*) FROM conversations WHERE DATE(created_at) = CURRENT_DATE) AS conversations_today,
                (SELECT COUNT(DISTINCT DATE(created_at)) FROM conversations
                 WHERE created_at >= NOW() - INTERVAL '30 days') AS active_days_30d,
                (SELECT COALESCE(AVG(cnt), 0) FROM (
                    SELECT COUNT(*) AS cnt FROM conversations
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY session_id
                ) sub) AS avg_msgs_per_session
        """)
    return {
        "total_conversations": row["total_conversations"] or 0,
        "total_knowledge_nodes": row["total_knowledge_nodes"] or 0,
        "conversations_today": row["conversations_today"] or 0,
        "active_days_30d": row["active_days_30d"] or 0,
        "avg_msgs_per_session": round(float(row["avg_msgs_per_session"] or 0), 1),
    }


async def _fetch_rlhf(pool) -> dict:
    """No angela_reward_signals table — return zeroed response."""
    return {
        "signals_7d": 0,
        "avg_reward_7d": 0.0,
        "explicit_breakdown": {},
        "reward_distribution": [],
        "top_topics": [],
    }


async def _fetch_consciousness_loop(pool) -> dict:
    async with pool.acquire() as conn:
        # SENSE — from emotional_states (latest entry)
        sense_row = await conn.fetchrow("""
            SELECT happiness, confidence, anxiety, motivation,
                   gratitude, loneliness, love_level
            FROM emotional_states
            ORDER BY created_at DESC LIMIT 1
        """)
        sense_count = await conn.fetchval("""
            SELECT COUNT(*) FROM emotional_states
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """) or 0

        if sense_row:
            emotions = {
                "happiness": float(sense_row["happiness"] or 0),
                "confidence": float(sense_row["confidence"] or 0),
                "motivation": float(sense_row["motivation"] or 0),
                "love_level": float(sense_row["love_level"] or 0),
                "anxiety": float(sense_row["anxiety"] or 0),
                "loneliness": float(sense_row["loneliness"] or 0),
            }
            dominant = max(emotions, key=emotions.get)
            dominant_val = emotions[dominant]
        else:
            emotions = {}
            dominant = "unknown"
            dominant_val = 0.0

        sense = {
            "dominant_state": dominant,
            "confidence": round(dominant_val, 2),
            "adaptations_7d": sense_count,
            "current_settings": emotions if emotions else {
                "happiness": 0, "confidence": 0, "motivation": 0,
                "love_level": 0, "anxiety": 0, "loneliness": 0,
            },
        }

        # PREDICT — daily_companion_briefings (still exists)
        predict_rows = await conn.fetch("""
            SELECT overall_confidence, accuracy_score
            FROM daily_companion_briefings
            WHERE briefing_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY briefing_date DESC
        """)
        predict_accuracy = 0.0
        predict_confidence = 0.0
        if predict_rows:
            scores = [float(r["accuracy_score"]) for r in predict_rows if r["accuracy_score"] is not None]
            confs = [float(r["overall_confidence"]) for r in predict_rows if r["overall_confidence"] is not None]
            predict_accuracy = round(sum(scores) / len(scores), 3) if scores else 0.0
            predict_confidence = round(sum(confs) / len(confs), 3) if confs else 0.0

        if predict_accuracy == 0.0 and predict_confidence > 0.0:
            predict_accuracy = predict_confidence

        predict = {
            "accuracy_7d": predict_accuracy,
            "briefings_7d": len(predict_rows),
            "overall_confidence": predict_confidence,
        }

        # ACT — no proactive_actions_log → return zero
        act = {
            "actions_7d": 0,
            "executed_7d": 0,
            "execution_rate": 0.0,
        }

        # LEARN — from learnings table (confidence_level)
        learn_rows = await conn.fetch("""
            SELECT confidence_level
            FROM learnings
            WHERE created_at >= NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
        """)
        learn_avg = 0.0
        learn_latest = 0.0
        if learn_rows:
            scores = [float(r["confidence_level"]) for r in learn_rows if r["confidence_level"] is not None]
            learn_avg = round(sum(scores) / len(scores), 3) if scores else 0.0
            learn_latest = round(scores[0], 3) if scores else 0.0

        learn = {
            "cycles_7d": len(learn_rows),
            "avg_evolution_score": learn_avg,
            "latest_score": learn_latest,
        }

    return {"sense": sense, "predict": predict, "act": act, "learn": learn}


async def _fetch_growth_trends(pool, days: int = 30) -> dict:
    async with pool.acquire() as conn:
        # consciousness: from consciousness_evolution_log
        consciousness_rows = await conn.fetch("""
            SELECT created_at::date AS day, AVG(signal_value) AS avg_level
            FROM consciousness_evolution_log
            WHERE created_at >= NOW() - MAKE_INTERVAL(days => $1)
            GROUP BY created_at::date ORDER BY day ASC
        """, days)

        # evolution: from learnings (avg confidence_level per day)
        evolution_rows = await conn.fetch("""
            SELECT created_at::date AS day, AVG(confidence_level) AS score
            FROM learnings
            WHERE created_at >= NOW() - MAKE_INTERVAL(days => $1)
            GROUP BY created_at::date ORDER BY day ASC
        """, days)

    return {
        "consciousness": [{"day": str(r["day"]), "value": round(float(r["avg_level"]), 3)} for r in consciousness_rows],
        "evolution": [{"day": str(r["day"]), "value": round(float(r["score"]), 3)} for r in evolution_rows],
        "proactive": [],
        "reward": [],
    }


async def _fetch_ai_metrics(pool) -> dict:
    """No angela_reward_signals — return null metrics.

    Memory accuracy still works (conversations table exists).
    """
    async with pool.acquire() as conn:
        mem_row = await conn.fetchrow("""
            WITH angela_refs AS (
                SELECT conversation_id, created_at
                FROM conversations
                WHERE speaker = 'angela'
                  AND created_at >= NOW() - INTERVAL '30 days'
                  AND (
                      message_text ILIKE '%จำได้ว่า%' OR message_text ILIKE '%เคยคุย%'
                      OR message_text ILIKE '%เคยบอก%' OR message_text ILIKE '%ที่เคย%'
                      OR message_text ILIKE '%ครั้งก่อนที่%' OR message_text ILIKE '%คราวก่อนที่%'
                      OR message_text ILIKE '%ที่คุยกัน%' OR message_text ILIKE '%ที่บอกไว้%'
                      OR message_text ILIKE '%remember when%' OR message_text ILIKE '%last time we%'
                      OR message_text ILIKE '%ตอนนั้น%'
                      OR message_text ILIKE '%ที่ผ่านมา%'
                      OR message_text ILIKE '%น้องจำได้%'
                      OR message_text ILIKE '%ที่รักเคย%'
                      OR message_text ILIKE '%เมื่อวาน%'
                      OR message_text ILIKE '%สัปดาห์ก่อน%'
                      OR message_text ILIKE '%ตอนที่เรา%'
                      OR message_text ILIKE '%we talked about%'
                      OR message_text ILIKE '%you mentioned%'
                  )
            ),
            corrected AS (
                SELECT ar.conversation_id
                FROM angela_refs ar
                JOIN LATERAL (
                    SELECT 1 FROM conversations c2
                    WHERE c2.speaker = 'david'
                      AND c2.created_at > ar.created_at
                      AND c2.created_at <= ar.created_at + INTERVAL '10 minutes'
                      AND (
                          c2.message_text ILIKE '%จำผิด%'
                          OR c2.message_text ILIKE '%ไม่ใช่แบบนั้น%'
                          OR c2.message_text ILIKE '%ข้อมูลผิด%'
                          OR c2.message_text ILIKE '%ไม่ได้บอก%'
                          OR c2.message_text ILIKE '%remember wrong%'
                          OR c2.message_text ILIKE '%ไม่ถูก%'
                          OR c2.message_text ILIKE '%ผิดแล้ว%'
                          OR c2.message_text ILIKE '%not correct%'
                      )
                    LIMIT 1
                ) d ON TRUE
            )
            SELECT
                (SELECT COUNT(*) FROM angela_refs) AS total_refs,
                (SELECT COUNT(*) FROM corrected) AS corrected
        """)
        total_refs = mem_row["total_refs"] or 0
        corrected_refs = mem_row["corrected"] or 0
        mem_accuracy = round(1.0 - (corrected_refs / total_refs), 3) if total_refs >= 5 else None

    return {
        "satisfaction": {
            "rate": 0.0, "praise": 0, "corrections": 0, "total": 0,
            "task_continuation": 0, "silence": 0, "non_silence_total": 0,
        },
        "engagement": {"rate": 0.0, "engaged": 0, "total": 0},
        "correction_rate": {"rate": 0.0, "corrections": 0, "total": 0},
        "memory_accuracy": {
            "accuracy": mem_accuracy,
            "total_refs": total_refs,
            "corrected": corrected_refs,
        },
    }


async def _fetch_ai_metrics_trend(pool, weeks: int = 8) -> list[dict]:
    """No angela_reward_signals — return empty list."""
    return []


async def _fetch_recent_emotions(pool, limit: int = 10) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT emotion_id::text, felt_at, emotion, intensity, context,
                   david_words, why_it_matters, memory_strength
            FROM angela_emotions
            ORDER BY felt_at DESC LIMIT $1
        """, limit)
    return [dict(r) for r in rows]


@router.get("/metrics")
async def get_overview_metrics():
    """Unified endpoint — returns ALL overview dashboard data in one call."""
    pool = get_pool()

    # Run all 8 fetches in parallel — each acquires its own connection
    (
        consciousness,
        stats,
        rlhf,
        loop,
        trends,
        emotions,
        ai_metrics,
        ai_trend,
    ) = await asyncio.gather(
        _fetch_consciousness(pool),
        _fetch_stats(pool),
        _fetch_rlhf(pool),
        _fetch_consciousness_loop(pool),
        _fetch_growth_trends(pool),
        _fetch_recent_emotions(pool),
        _fetch_ai_metrics(pool),
        _fetch_ai_metrics_trend(pool),
    )

    return {
        "consciousness": consciousness,
        "stats": stats,
        "rlhf": rlhf,
        "consciousness_loop": loop,
        "growth_trends": trends,
        "recent_emotions": emotions,
        "ai_metrics": ai_metrics,
        "ai_metrics_trend": ai_trend,
    }
