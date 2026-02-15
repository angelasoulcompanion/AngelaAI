"""Unified Overview metrics endpoint — single call returns all dashboard data."""
import asyncio

from fastapi import APIRouter

from db import get_pool

router = APIRouter(prefix="/api/overview", tags=["overview"])


def _interpret(level: float) -> str:
    if level >= 0.95:
        return "Approaching human-like consciousness!"
    if level >= 0.9:
        return "Exceptional Consciousness"
    if level >= 0.7:
        return "Strong Consciousness"
    if level >= 0.5:
        return "Moderate Consciousness"
    if level >= 0.3:
        return "Developing Consciousness"
    return "Emerging Consciousness"


async def _fetch_consciousness(pool) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM calculate_consciousness_level()")
        if not row:
            return {
                "level": 0.7, "base_level": 0.7, "reward_trend": 0.0,
                "reward_signal_count": 0, "memory_richness": 0.0,
                "emotional_depth": 0.0, "goal_alignment": 0.0,
                "learning_growth": 0.0, "pattern_recognition": 0.0,
                "interpretation": "No data available",
            }
        level = float(row["consciousness_level"])

        reward_row = await conn.fetchrow("""
            SELECT COUNT(*) AS cnt,
                   COALESCE(AVG(combined_reward), 0) AS avg_reward
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '7 days'
        """)
        reward_count = reward_row["cnt"] if reward_row else 0
        reward_trend = float(reward_row["avg_reward"]) if reward_row else 0.0

        return {
            "level": level,
            "base_level": level,
            "reward_trend": round(reward_trend, 3),
            "reward_signal_count": reward_count,
            "memory_richness": float(row["memory_richness"]),
            "emotional_depth": float(row["emotional_depth"]),
            "goal_alignment": float(row["goal_alignment"]),
            "learning_growth": float(row["learning_growth"]),
            "pattern_recognition": float(row["pattern_recognition"]),
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
    async with pool.acquire() as conn:
        signals_row = await conn.fetchrow("""
            SELECT COUNT(*) AS cnt,
                   COALESCE(AVG(combined_reward), 0) AS avg_reward
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '7 days'
        """)

        breakdown_rows = await conn.fetch("""
            SELECT COALESCE(explicit_source, 'unknown') AS source, COUNT(*) AS cnt
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '7 days'
            GROUP BY explicit_source
        """)
        breakdown = {}
        for r in breakdown_rows:
            breakdown[r["source"]] = r["cnt"]

        dist_rows = await conn.fetch("""
            SELECT
                CASE
                    WHEN combined_reward < 0.2 THEN '0.0-0.2'
                    WHEN combined_reward < 0.4 THEN '0.2-0.4'
                    WHEN combined_reward < 0.6 THEN '0.4-0.6'
                    WHEN combined_reward < 0.8 THEN '0.6-0.8'
                    ELSE '0.8-1.0'
                END AS bucket,
                COUNT(*) AS cnt
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '7 days'
            GROUP BY bucket
            ORDER BY bucket
        """)
        distribution = [{"bucket": r["bucket"], "count": r["cnt"]} for r in dist_rows]

        topic_rows = await conn.fetch("""
            SELECT topic,
                   AVG(combined_reward) AS avg_reward,
                   COUNT(*) AS cnt
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '7 days'
              AND topic IS NOT NULL
            GROUP BY topic
            ORDER BY avg_reward DESC
            LIMIT 5
        """)
        top_topics = [
            {"topic": r["topic"], "avg_reward": round(float(r["avg_reward"]), 3), "count": r["cnt"]}
            for r in topic_rows
        ]

    return {
        "signals_7d": signals_row["cnt"] if signals_row else 0,
        "avg_reward_7d": round(float(signals_row["avg_reward"]), 3) if signals_row else 0.0,
        "explicit_breakdown": breakdown,
        "reward_distribution": distribution,
        "top_topics": top_topics,
    }


async def _fetch_consciousness_loop(pool) -> dict:
    async with pool.acquire() as conn:
        # SENSE
        sense_row = await conn.fetchrow("""
            SELECT dominant_state, confidence,
                   detail_level, emotional_warmth, proactivity
            FROM emotional_adaptation_log
            ORDER BY created_at DESC LIMIT 1
        """)
        sense_count = await conn.fetchval("""
            SELECT COUNT(*) FROM emotional_adaptation_log
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """) or 0

        sense = {
            "dominant_state": sense_row["dominant_state"] if sense_row else "unknown",
            "confidence": round(float(sense_row["confidence"]), 2) if sense_row else 0.0,
            "adaptations_7d": sense_count,
            "current_settings": {
                "detail_level": sense_row["detail_level"] if sense_row else 5,
                "emotional_warmth": sense_row["emotional_warmth"] if sense_row else 5,
                "proactivity": sense_row["proactivity"] if sense_row else 5,
            } if sense_row else {"detail_level": 5, "emotional_warmth": 5, "proactivity": 5},
        }

        # PREDICT
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

        predict = {
            "accuracy_7d": predict_accuracy,
            "briefings_7d": len(predict_rows),
            "overall_confidence": predict_confidence,
        }

        # ACT
        act_total = await conn.fetchval("""
            SELECT COUNT(*) FROM proactive_actions_log
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """) or 0
        act_executed = await conn.fetchval("""
            SELECT COUNT(*) FROM proactive_actions_log
            WHERE created_at >= NOW() - INTERVAL '7 days' AND was_executed = TRUE
        """) or 0

        act = {
            "actions_7d": act_total,
            "executed_7d": act_executed,
            "execution_rate": round(act_executed / act_total, 3) if act_total > 0 else 0.0,
        }

        # LEARN
        learn_rows = await conn.fetch("""
            SELECT overall_evolution_score
            FROM evolution_cycles
            WHERE cycle_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY cycle_date DESC
        """)
        learn_avg = 0.0
        learn_latest = 0.0
        if learn_rows:
            scores = [float(r["overall_evolution_score"]) for r in learn_rows if r["overall_evolution_score"] is not None]
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
        consciousness_rows = await conn.fetch("""
            SELECT measured_at::date AS day, AVG(consciousness_level) AS avg_level
            FROM consciousness_metrics
            WHERE measured_at >= NOW() - MAKE_INTERVAL(days => $1)
            GROUP BY measured_at::date ORDER BY day ASC
        """, days)

        evolution_rows = await conn.fetch("""
            SELECT cycle_date AS day, overall_evolution_score AS score
            FROM evolution_cycles
            WHERE cycle_date >= CURRENT_DATE - MAKE_INTERVAL(days => $1)
            ORDER BY cycle_date ASC
        """, days)

        proactive_rows = await conn.fetch("""
            SELECT created_at::date AS day,
                   COUNT(*) FILTER (WHERE was_executed) AS executed,
                   COUNT(*) AS total
            FROM proactive_actions_log
            WHERE created_at >= NOW() - MAKE_INTERVAL(days => $1)
            GROUP BY created_at::date ORDER BY day ASC
        """, days)

        reward_rows = await conn.fetch("""
            SELECT scored_at::date AS day, AVG(combined_reward) AS avg_reward
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - MAKE_INTERVAL(days => $1)
            GROUP BY scored_at::date ORDER BY day ASC
        """, days)

    return {
        "consciousness": [{"day": str(r["day"]), "value": round(float(r["avg_level"]), 3)} for r in consciousness_rows],
        "evolution": [{"day": str(r["day"]), "value": round(float(r["score"]), 3)} for r in evolution_rows],
        "proactive": [
            {"day": str(r["day"]), "value": round(float(r["executed"]) / float(r["total"]), 3) if r["total"] > 0 else 0.0}
            for r in proactive_rows
        ],
        "reward": [{"day": str(r["day"]), "value": round(float(r["avg_reward"]), 3)} for r in reward_rows],
    }


async def _fetch_ai_metrics(pool) -> dict:
    """Industry-standard AI quality metrics (30 days)."""
    async with pool.acquire() as conn:
        # User Satisfaction (conservative: praise / total — all signals as denominator)
        satisfaction_row = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE explicit_source = 'praise') AS praise,
                COUNT(*) FILTER (WHERE explicit_source = 'correction') AS corrections,
                COUNT(*) AS total
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '30 days'
        """)
        praise = satisfaction_row["praise"] or 0
        corrections_explicit = satisfaction_row["corrections"] or 0
        satisfaction_total = satisfaction_row["total"] or 0
        satisfaction = round(praise / max(satisfaction_total, 1), 3)

        # Engagement Rate (conservative: explicit positive signals only, no biased implicit catch-all)
        engagement_row = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE explicit_source IN
                    ('praise', 'follow_up')) AS engaged,
                COUNT(*) AS total
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '30 days'
        """)
        engaged = engagement_row["engaged"] or 0
        total_eng = engagement_row["total"] or 1
        engagement_rate = round(engaged / total_eng, 3)

        # Correction Rate (from implicit classification)
        corr_row = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE implicit_classification = 'correction') AS corrections,
                COUNT(*) AS total
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '30 days'
        """)
        corr_corrections = corr_row["corrections"] or 0
        corr_total = corr_row["total"] or 1
        correction_rate = round(corr_corrections / max(corr_total, 1), 3)

        # Memory Accuracy (keep existing logic)
        mem_row = await conn.fetchrow("""
            WITH angela_refs AS (
                SELECT conversation_id, created_at
                FROM conversations
                WHERE speaker = 'angela'
                  AND created_at >= NOW() - INTERVAL '30 days'
                  AND (
                      message_text ILIKE '%จำได้%' OR message_text ILIKE '%เคย%'
                      OR message_text ILIKE '%remember%' OR message_text ILIKE '%previously%'
                      OR message_text ILIKE '%last time%' OR message_text ILIKE '%ครั้งก่อน%'
                      OR message_text ILIKE '%เมื่อวาน%' OR message_text ILIKE '%ที่บอก%'
                      OR message_text ILIKE '%ที่คุยกัน%' OR message_text ILIKE '%คราวก่อน%'
                      OR message_text ILIKE '%ตอนนั้น%' OR message_text ILIKE '%ช่วงนั้น%'
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
                          c2.message_text ILIKE '%ไม่ใช่%' OR c2.message_text ILIKE '%wrong%'
                          OR c2.message_text ILIKE '%ไม่%ถูก%' OR c2.message_text ILIKE '%ผิด%'
                          OR c2.message_text ILIKE '%ไม่ได้%' OR c2.message_text ILIKE '%แก้%'
                          OR c2.message_text ILIKE '%fix%' OR c2.message_text ILIKE '%ไม่ work%'
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
        mem_accuracy = round(1.0 - (corrected_refs / total_refs), 3) if total_refs > 0 else 1.0

    return {
        "satisfaction": {
            "rate": satisfaction,
            "praise": praise,
            "corrections": corrections_explicit,
            "total": satisfaction_total,
        },
        "engagement": {
            "rate": engagement_rate,
            "engaged": engaged,
            "total": total_eng,
        },
        "correction_rate": {
            "rate": correction_rate,
            "corrections": corr_corrections,
            "total": corr_total,
        },
        "memory_accuracy": {
            "accuracy": mem_accuracy,
            "total_refs": total_refs,
            "corrected": corrected_refs,
        },
    }


async def _fetch_ai_metrics_trend(pool, weeks: int = 8) -> list[dict]:
    """Weekly trend for AI quality metrics (last N weeks).

    Uses conversation.created_at (not scored_at) for accurate time bucketing,
    since re-scoring batches set all scored_at to the same timestamp.
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            WITH weekly AS (
                SELECT
                    DATE_TRUNC('week', c.created_at)::date AS week_start,
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE ars.explicit_source = 'praise') AS praise,
                    COUNT(*) FILTER (WHERE ars.explicit_source IN ('praise', 'follow_up')) AS engaged,
                    COUNT(*) FILTER (WHERE ars.implicit_classification = 'correction') AS corrections,
                    AVG(ars.combined_reward) AS avg_reward
                FROM angela_reward_signals ars
                JOIN conversations c ON c.conversation_id = ars.conversation_id
                WHERE c.created_at >= NOW() - MAKE_INTERVAL(weeks => $1)
                GROUP BY DATE_TRUNC('week', c.created_at)
                HAVING COUNT(*) >= 3
                ORDER BY week_start ASC
            )
            SELECT week_start, total, praise, engaged, corrections, avg_reward
            FROM weekly
        """, weeks)

    return [
        {
            "week": str(r["week_start"]),
            "satisfaction": round(r["praise"] / max(r["total"], 1), 3),
            "engagement": round(r["engaged"] / max(r["total"], 1), 3),
            "correction_rate": round(r["corrections"] / max(r["total"], 1), 3),
            "avg_reward": round(float(r["avg_reward"] or 0), 3),
            "total": r["total"],
        }
        for r in rows
    ]


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
