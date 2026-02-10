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
                (SELECT COUNT(*) FROM angela_emotions) AS total_emotions,
                (SELECT COUNT(*) FROM learnings) AS total_learnings,
                (SELECT COUNT(*) FROM knowledge_nodes) AS total_knowledge_nodes,
                (SELECT COUNT(*) FROM conversations WHERE DATE(created_at) = CURRENT_DATE) AS conversations_today,
                (SELECT COUNT(*) FROM angela_emotions WHERE DATE(felt_at) = CURRENT_DATE) AS emotions_today
        """)
    return {
        "total_conversations": row["total_conversations"] or 0,
        "total_emotions": row["total_emotions"] or 0,
        "total_learnings": row["total_learnings"] or 0,
        "total_knowledge_nodes": row["total_knowledge_nodes"] or 0,
        "conversations_today": row["conversations_today"] or 0,
        "emotions_today": row["emotions_today"] or 0,
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


async def _fetch_constitutional(pool) -> dict:
    async with pool.acquire() as conn:
        # Check if evals table exists
        has_evals = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'angela_constitutional_evals'
            )
        """)

        if has_evals:
            rows = await conn.fetch("""
                SELECT c.principle_name,
                       c.weight,
                       COALESCE(AVG(e.score), 0) AS avg_score_7d
                FROM angela_constitution c
                LEFT JOIN angela_constitutional_evals e
                    ON e.principle_id = c.principle_id
                   AND e.evaluated_at >= NOW() - INTERVAL '7 days'
                GROUP BY c.principle_name, c.weight
                ORDER BY c.weight DESC
            """)
        else:
            rows = await conn.fetch("""
                SELECT principle_name, weight
                FROM angela_constitution
                WHERE is_active = TRUE
                ORDER BY weight DESC
            """)

    principles = [
        {
            "name": r["principle_name"],
            "weight": round(float(r["weight"]), 3),
            "avg_score_7d": round(float(r.get("avg_score_7d", 0)), 3) if "avg_score_7d" in r.keys() else 0.0,
        }
        for r in rows
    ]
    return {"principles": principles}


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


async def _fetch_meta_awareness(pool) -> dict:
    async with pool.acquire() as conn:
        biases = await conn.fetchval("""
            SELECT COUNT(*) FROM meta_bias_detections
            WHERE detected_at >= NOW() - INTERVAL '30 days'
        """) or 0

        anomalies = await conn.fetchval("""
            SELECT COUNT(*) FROM consciousness_anomalies
            WHERE is_resolved = FALSE
        """) or 0

        identity_row = await conn.fetchrow("""
            SELECT identity_drift_score, is_healthy
            FROM identity_checkpoints
            ORDER BY created_at DESC LIMIT 1
        """)
        drift = round(float(identity_row["identity_drift_score"]), 3) if identity_row else 0.0
        healthy = identity_row["is_healthy"] if identity_row else True

    return {
        "biases_detected_30d": biases,
        "anomalies_unresolved": anomalies,
        "identity_drift_score": drift,
        "identity_healthy": healthy,
    }


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
        constitutional,
        loop,
        meta,
        trends,
        emotions,
    ) = await asyncio.gather(
        _fetch_consciousness(pool),
        _fetch_stats(pool),
        _fetch_rlhf(pool),
        _fetch_constitutional(pool),
        _fetch_consciousness_loop(pool),
        _fetch_meta_awareness(pool),
        _fetch_growth_trends(pool),
        _fetch_recent_emotions(pool),
    )

    return {
        "consciousness": consciousness,
        "stats": stats,
        "rlhf": rlhf,
        "constitutional": constitutional,
        "consciousness_loop": loop,
        "meta_awareness": meta,
        "growth_trends": trends,
        "recent_emotions": emotions,
    }
