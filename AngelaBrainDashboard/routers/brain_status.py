"""Brain Status metrics endpoint — comprehensive brain-based architecture dashboard."""
import asyncio

from fastapi import APIRouter

from db import get_pool

router = APIRouter(prefix="/api/brain-status", tags=["brain-status"])


async def _fetch_stimuli_summary(pool) -> dict:
    """Stimuli: 24h + 7d counts, by codelet type, top 10 salient."""
    async with pool.acquire() as conn:
        counts = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') AS total_24h,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS total_7d,
                COALESCE(AVG(salience_score) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days'), 0) AS avg_salience,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days' AND salience_score > 0.5) AS high_salience
            FROM angela_stimuli
        """)

        by_type_rows = await conn.fetch("""
            SELECT stimulus_type, COUNT(*) AS cnt,
                   COALESCE(AVG(salience_score), 0) AS avg_sal
            FROM angela_stimuli
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY stimulus_type
            ORDER BY cnt DESC
        """)

        top_salient_rows = await conn.fetch("""
            SELECT stimulus_id::text, stimulus_type,
                   content, salience_score, created_at
            FROM angela_stimuli
            WHERE created_at >= NOW() - INTERVAL '7 days'
            ORDER BY salience_score DESC
            LIMIT 10
        """)

        dim_row = await conn.fetchrow("""
            SELECT
                COALESCE(AVG((salience_breakdown->>'novelty')::float), 0) AS novelty,
                COALESCE(AVG((salience_breakdown->>'emotional')::float), 0) AS emotional,
                COALESCE(AVG((salience_breakdown->>'goal_relevance')::float), 0) AS goal_relevance,
                COALESCE(AVG((salience_breakdown->>'temporal_urgency')::float), 0) AS temporal_urgency,
                COALESCE(AVG((salience_breakdown->>'social_relevance')::float), 0) AS social_relevance
            FROM angela_stimuli
            WHERE created_at >= NOW() - INTERVAL '7 days'
              AND salience_breakdown IS NOT NULL
        """)

    return {
        "total_24h": counts["total_24h"] or 0,
        "total_7d": counts["total_7d"] or 0,
        "avg_salience": round(float(counts["avg_salience"]), 3),
        "high_salience": counts["high_salience"] or 0,
        "by_type": [
            {"type": r["stimulus_type"], "count": r["cnt"], "avg_salience": round(float(r["avg_sal"]), 3)}
            for r in by_type_rows
        ],
        "top_salient": [
            {
                "id": r["stimulus_id"],
                "codelet_type": r["stimulus_type"],
                "stimulus_type": r["stimulus_type"],
                "content": (r["content"] or "")[:120],
                "salience_score": round(float(r["salience_score"] or 0), 3),
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in top_salient_rows
        ],
        "salience_dims": {
            "novelty": round(float(dim_row["novelty"]), 3) if dim_row else 0.0,
            "emotional": round(float(dim_row["emotional"]), 3) if dim_row else 0.0,
            "goal_relevance": round(float(dim_row["goal_relevance"]), 3) if dim_row else 0.0,
            "temporal_urgency": round(float(dim_row["temporal_urgency"]), 3) if dim_row else 0.0,
            "social_relevance": round(float(dim_row["social_relevance"]), 3) if dim_row else 0.0,
        },
    }


async def _fetch_thoughts_summary(pool) -> dict:
    """Thoughts: 24h + 7d, S1 vs S2, avg motivation, top 5 by motivation."""
    async with pool.acquire() as conn:
        counts = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') AS total_24h,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS total_7d,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days' AND thought_type = 'system1') AS s1,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days' AND thought_type = 'system2') AS s2,
                COALESCE(AVG(motivation_score) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days'), 0) AS avg_motivation,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days' AND motivation_score > 0.6) AS high_motivation
            FROM angela_thoughts
        """)

        top_rows = await conn.fetch("""
            SELECT thought_id::text, thought_type,
                   content, motivation_score,
                   expressed_via, created_at
            FROM angela_thoughts
            WHERE created_at >= NOW() - INTERVAL '7 days'
            ORDER BY motivation_score DESC
            LIMIT 5
        """)

    return {
        "total_24h": counts["total_24h"] or 0,
        "total_7d": counts["total_7d"] or 0,
        "system1": counts["s1"] or 0,
        "system2": counts["s2"] or 0,
        "avg_motivation": round(float(counts["avg_motivation"]), 3),
        "high_motivation": counts["high_motivation"] or 0,
        "top_thoughts": [
            {
                "id": r["thought_id"],
                "type": r["thought_type"],
                "template": None,
                "content": (r["content"] or "")[:150],
                "motivation": round(float(r["motivation_score"] or 0), 3),
                "expressed_via": r["expressed_via"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in top_rows
        ],
    }


async def _fetch_expression_summary(pool) -> dict:
    """Expression funnel: generated -> expressed -> suppressed, by channel, suppress reasons."""
    async with pool.acquire() as conn:
        # Expression log stats (7d)
        log_row = await conn.fetchrow("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE channel = 'telegram') AS telegram_count,
                COUNT(*) FILTER (WHERE channel = 'chat_queue') AS chat_count,
                COUNT(*) FILTER (WHERE suppress_reason IS NOT NULL) AS suppressed_count
            FROM thought_expression_log
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)

        # Thoughts generated vs expressed (7d)
        thought_counts = await conn.fetchrow("""
            SELECT
                COUNT(*) AS generated,
                COUNT(*) FILTER (WHERE expressed_via IS NOT NULL) AS expressed
            FROM angela_thoughts
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)

        # Suppress reasons
        suppress_rows = await conn.fetch("""
            SELECT suppress_reason, COUNT(*) AS cnt
            FROM thought_expression_log
            WHERE created_at >= NOW() - INTERVAL '7 days'
              AND suppress_reason IS NOT NULL
            GROUP BY suppress_reason
            ORDER BY cnt DESC
        """)

        # Effectiveness (David's responses to brain expressions)
        eff_row = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE david_response = 'positive') AS positive,
                COUNT(*) FILTER (WHERE david_response = 'neutral') AS neutral,
                COUNT(*) FILTER (WHERE david_response = 'negative') AS negative,
                COUNT(*) AS total
            FROM thought_expression_log
            WHERE created_at >= NOW() - INTERVAL '7 days'
              AND david_response IS NOT NULL
        """)

    generated = thought_counts["generated"] or 0
    expressed = thought_counts["expressed"] or 0
    suppressed = generated - expressed

    eff_total = eff_row["total"] or 0
    effectiveness_avg = 0.0
    if eff_total > 0:
        pos = eff_row["positive"] or 0
        neg = eff_row["negative"] or 0
        effectiveness_avg = round((pos - neg) / eff_total, 3)

    return {
        "generated": generated,
        "total_expressed": expressed,
        "telegram_count": log_row["telegram_count"] or 0,
        "chat_count": log_row["chat_count"] or 0,
        "suppressed_count": suppressed,
        "suppress_reasons": {r["suppress_reason"]: r["cnt"] for r in suppress_rows},
        "effectiveness_avg": effectiveness_avg,
        "david_responses": {
            "positive": eff_row["positive"] or 0,
            "neutral": eff_row["neutral"] or 0,
            "negative": eff_row["negative"] or 0,
        },
    }


async def _fetch_reflections_summary(pool) -> dict:
    """Reflections: 7d counts, by type, recent 5 reflections."""
    async with pool.acquire() as conn:
        counts = await conn.fetchrow("""
            SELECT
                COUNT(*) AS total_7d,
                COUNT(*) FILTER (WHERE status = 'integrated') AS integrated
            FROM angela_reflections
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)

        by_type_rows = await conn.fetch("""
            SELECT reflection_type, COUNT(*) AS cnt
            FROM angela_reflections
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY reflection_type
            ORDER BY cnt DESC
        """)

        recent_rows = await conn.fetch("""
            SELECT reflection_id::text, reflection_type, depth_level,
                   content, status, importance_sum, created_at
            FROM angela_reflections
            WHERE created_at >= NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 5
        """)

    return {
        "total_7d": counts["total_7d"] or 0,
        "integrated_count": counts["integrated"] or 0,
        "by_type": {r["reflection_type"]: r["cnt"] for r in by_type_rows},
        "recent": [
            {
                "id": r["reflection_id"],
                "type": r["reflection_type"],
                "depth": r["depth_level"],
                "content": (r["content"] or "")[:200],
                "status": r["status"],
                "importance_sum": round(float(r["importance_sum"] or 0), 1),
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in recent_rows
        ],
    }


async def _fetch_migration_summary(pool) -> dict:
    """Brain vs Rule comparison: wins, readiness %, per-feature routing."""
    async with pool.acquire() as conn:
        # Brain vs rule wins (7d)
        comp_row = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE winner = 'brain') AS brain_wins,
                COUNT(*) FILTER (WHERE winner = 'rule') AS rule_wins,
                COUNT(*) FILTER (WHERE winner = 'tie') AS ties,
                COUNT(*) AS total
            FROM brain_vs_rule_comparison
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)

        # Per-feature routing from companion_patterns (pattern_data is JSONB)
        routing_rows = await conn.fetch("""
            SELECT pattern_data
            FROM companion_patterns
            WHERE pattern_category = 'brain_migration_routing'
              AND is_active = TRUE
        """)

        # Brain readiness from companion_patterns
        readiness_row = await conn.fetchrow("""
            SELECT pattern_data
            FROM companion_patterns
            WHERE pattern_category = 'brain_thresholds'
              AND is_active = TRUE
            ORDER BY last_observed DESC
            LIMIT 1
        """)

    total = comp_row["total"] or 0
    brain_wins = comp_row["brain_wins"] or 0
    import json

    readiness_pct = 0.0
    if readiness_row and readiness_row["pattern_data"]:
        try:
            val = readiness_row["pattern_data"] if isinstance(readiness_row["pattern_data"], dict) else json.loads(readiness_row["pattern_data"])
            readiness_pct = float(val.get("brain_readiness", val.get("value", 0)))
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
            pass

    if readiness_pct == 0 and total > 0:
        readiness_pct = round(brain_wins / total * 100, 1)

    routing = []
    for r in routing_rows:
        try:
            data = r["pattern_data"] if isinstance(r["pattern_data"], dict) else json.loads(r["pattern_data"])
            if isinstance(data, dict):
                for feature, mode_val in data.items():
                    mode = mode_val if isinstance(mode_val, str) else str(mode_val)
                    routing.append({"feature": feature, "mode": mode})
            else:
                routing.append({"feature": "unknown", "mode": str(data)})
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "brain_wins": brain_wins,
        "rule_wins": comp_row["rule_wins"] or 0,
        "ties": comp_row["ties"] or 0,
        "total_comparisons": total,
        "readiness_pct": readiness_pct,
        "routing": routing,
    }


async def _fetch_consolidation_summary(pool) -> dict:
    """Memory consolidation: 7d clusters, episodes, knowledge created, top topics."""
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) AS clusters_7d,
                COALESCE(SUM(source_count), 0) AS episodes_processed,
                COUNT(*) FILTER (WHERE target_id IS NOT NULL) AS knowledge_created,
                COALESCE(AVG(confidence), 0) AS avg_confidence
            FROM memory_consolidation_log
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)

        topic_rows = await conn.fetch("""
            SELECT topic_cluster AS topic, COUNT(*) AS cnt,
                   COALESCE(AVG(confidence), 0) AS avg_conf
            FROM memory_consolidation_log
            WHERE created_at >= NOW() - INTERVAL '7 days'
              AND topic_cluster IS NOT NULL
            GROUP BY topic_cluster
            ORDER BY cnt DESC
            LIMIT 10
        """)

    return {
        "clusters_7d": stats["clusters_7d"] or 0,
        "episodes_processed": stats["episodes_processed"] or 0,
        "knowledge_created": stats["knowledge_created"] or 0,
        "avg_confidence": round(float(stats["avg_confidence"]), 3),
        "top_topics": [
            {"topic": r["topic"], "count": r["cnt"], "avg_confidence": round(float(r["avg_conf"]), 3)}
            for r in topic_rows
        ],
    }


@router.get("/metrics")
async def get_brain_status_metrics():
    """Unified endpoint — returns ALL brain status dashboard data in one call."""
    pool = get_pool()

    (
        stimuli,
        thoughts,
        expression,
        reflections,
        migration,
        consolidation,
    ) = await asyncio.gather(
        _fetch_stimuli_summary(pool),
        _fetch_thoughts_summary(pool),
        _fetch_expression_summary(pool),
        _fetch_reflections_summary(pool),
        _fetch_migration_summary(pool),
        _fetch_consolidation_summary(pool),
    )

    return {
        "stimuli": stimuli,
        "thoughts": thoughts,
        "expression": expression,
        "reflections": reflections,
        "migration": migration,
        "consolidation": consolidation,
    }
