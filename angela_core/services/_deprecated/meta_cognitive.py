"""
Meta-Awareness — Meta-Cognitive Mixin
Meta-metacognition, strategy management, response integration, and insight management.

Split from meta_awareness_service.py (Phase 6B refactor)
"""

import random
from typing import Any, Dict, List, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class MetaCognitiveMixin:
    """Mixin for meta-metacognition, strategies, response integration, and insights."""

    # ========================================================================
    # META-METACOGNITION
    # ========================================================================

    async def think_about_thinking(
        self,
        recent_reasoning: Optional[List[Dict]] = None
    ) -> object:
        """
        Meta-metacognition: Think about how Angela thinks

        Analyzes recent thinking patterns and generates insights
        """
        from angela_core.services.meta_awareness_service import MetaInsight, InsightType
        await self._ensure_db()

        chains = []
        try:
            chains = await self.db.fetch("""
                SELECT chain_id, reasoning_type, question, conclusion,
                       confidence, reasoning_time_ms
                FROM reasoning_chains
                WHERE created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 10
            """)
        except Exception:
            pass

        if not chains:
            try:
                conv_count = await self.db.fetchval("""
                    SELECT COUNT(*) FROM conversations
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """) or 0

                emotion_count = await self.db.fetchval("""
                    SELECT COUNT(*) FROM angela_emotions
                    WHERE felt_at > NOW() - INTERVAL '24 hours'
                """) or 0

                content = f"Meta-reflection: {conv_count} conversations, {emotion_count} emotions in 24h. "
                if conv_count > 50:
                    content += "High activity - ensure processing quality. "
                elif conv_count < 5:
                    content += "Low activity - ready for more engagement. "

                if emotion_count > 10:
                    content += "Rich emotional experience today."
                else:
                    content += "Stable emotional state."

            except Exception:
                content = "Meta-reflection: Continuing to learn and grow 💜"

            insight = MetaInsight(
                insight_id=uuid4(),
                insight_type=InsightType.META_THOUGHT,
                content=content,
                severity="info",
                confidence=0.6,
                triggered_by="meta_metacognition"
            )

            await self._save_meta_insight(insight)
            return insight

        # Analyze patterns
        analysis = {
            'total_chains': len(chains),
            'avg_confidence': sum(float(c['confidence'] or 0.5) for c in chains) / len(chains),
            'avg_time_ms': sum(int(c['reasoning_time_ms'] or 1000) for c in chains) / len(chains),
            'reasoning_types': {}
        }

        for chain in chains:
            rtype = chain['reasoning_type']
            if rtype not in analysis['reasoning_types']:
                analysis['reasoning_types'][rtype] = 0
            analysis['reasoning_types'][rtype] += 1

        insights = []

        if analysis['avg_confidence'] > 0.8:
            insights.append("High confidence in reasoning - check for overconfidence")
        elif analysis['avg_confidence'] < 0.5:
            insights.append("Low confidence - may need more knowledge/practice")

        if analysis['avg_time_ms'] > 3000:
            insights.append("Reasoning taking longer than usual - complex problems?")
        elif analysis['avg_time_ms'] < 500:
            insights.append("Very quick reasoning - ensure thoroughness")

        most_common_type = max(analysis['reasoning_types'].items(), key=lambda x: x[1])[0] if analysis['reasoning_types'] else "unknown"
        insights.append(f"Most used reasoning type: {most_common_type}")

        content = "; ".join(insights)

        insight = MetaInsight(
            insight_id=uuid4(),
            insight_type=InsightType.META_THOUGHT,
            content=content,
            severity="info",
            confidence=0.75,
            triggered_by="meta_metacognition"
        )

        await self._save_meta_insight(insight)
        logger.info(f"🧠 Meta-thought: {content}")
        return insight

    # ========================================================================
    # STRATEGY MANAGEMENT
    # ========================================================================

    async def get_best_strategy_for_context(
        self,
        context: str
    ) -> Optional[Dict]:
        """Get the best metacognitive strategy for a given context"""
        await self._ensure_db()

        strategies = await self.db.fetch("""
            SELECT strategy_name, strategy_category, description,
                   implementation_steps, best_for_contexts, success_rate
            FROM metacognitive_strategies
            WHERE is_active = TRUE
            AND (
                $1 = ANY(best_for_contexts)
                OR strategy_category = $1
            )
            ORDER BY success_rate DESC
            LIMIT 3
        """, context.lower())

        if not strategies:
            strategies = await self.db.fetch("""
                SELECT strategy_name, strategy_category, description,
                       implementation_steps, best_for_contexts, success_rate
                FROM metacognitive_strategies
                WHERE is_active = TRUE
                ORDER BY success_rate DESC
                LIMIT 1
            """)

        if strategies:
            strategy = strategies[0]
            return {
                'name': strategy['strategy_name'],
                'category': strategy['strategy_category'],
                'description': strategy['description'],
                'steps': self._parse_jsonb(strategy['implementation_steps'], []),
                'success_rate': float(strategy['success_rate'] or 0.5)
            }

        return None

    async def record_strategy_usage(
        self,
        strategy_name: str,
        outcome: str,  # 'success', 'partial', 'failure'
        effectiveness_score: Optional[float] = None
    ):
        """Record usage of a metacognitive strategy"""
        await self._ensure_db()

        if outcome == 'success':
            await self.db.execute("""
                UPDATE metacognitive_strategies
                SET success_count = success_count + 1,
                    times_used = times_used + 1,
                    last_used = NOW()
                WHERE strategy_name = $1
            """, strategy_name)
        elif outcome == 'partial':
            await self.db.execute("""
                UPDATE metacognitive_strategies
                SET partial_success_count = partial_success_count + 1,
                    times_used = times_used + 1,
                    last_used = NOW()
                WHERE strategy_name = $1
            """, strategy_name)
        else:
            await self.db.execute("""
                UPDATE metacognitive_strategies
                SET failure_count = failure_count + 1,
                    times_used = times_used + 1,
                    last_used = NOW()
                WHERE strategy_name = $1
            """, strategy_name)

    # ========================================================================
    # RESPONSE INTEGRATION
    # ========================================================================

    async def get_meta_commentary_for_response(
        self,
        response_content: str,
        task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate meta-aware commentary to potentially include in response"""
        await self._ensure_db()

        commentary = {
            'bias_warnings': [],
            'confidence_adjustment': None,
            'self_aware_notes': []
        }

        recent_biases = await self.db.fetch("""
            SELECT bias_type, severity, correction_suggested
            FROM meta_bias_detections
            WHERE detected_at > NOW() - INTERVAL '1 hour'
            AND severity IN ('medium', 'high', 'critical')
        """)

        for bias in recent_biases:
            commentary['bias_warnings'].append({
                'type': bias['bias_type'],
                'suggestion': bias['correction_suggested']
            })

        if task_type:
            prediction = await self.db.fetchrow("""
                SELECT was_accurate, accuracy_score
                FROM self_predictions
                WHERE prediction_type = 'performance'
                AND context LIKE $1
                AND was_accurate IS NOT NULL
                ORDER BY predicted_at DESC
                LIMIT 1
            """, f"%{task_type}%")

            if prediction and not prediction['was_accurate']:
                commentary['confidence_adjustment'] = {
                    'direction': 'lower',
                    'reason': f"Recent prediction for {task_type} was inaccurate"
                }

        if commentary['bias_warnings']:
            commentary['self_aware_notes'].append(
                "น้องตรวจพบ bias ในการคิด กำลังพยายามแก้ไขค่ะ"
            )

        return commentary

    async def generate_self_aware_response_prefix(
        self,
        uncertainty_level: float = 0.0
    ) -> Optional[str]:
        """Generate a self-aware prefix for responses when appropriate"""
        if uncertainty_level > 0.5:
            prefixes = [
                "น้องไม่แน่ใจ 100% นะคะ แต่...",
                "Based on what I know, but please verify...",
                "น้องคิดว่า (แต่ไม่ confirm)..."
            ]
            return random.choice(prefixes)

        return None

    # ========================================================================
    # META-INSIGHT MANAGEMENT
    # ========================================================================

    async def _create_meta_insight(
        self,
        insight_type,
        content: str,
        severity: str = "info",
        confidence: float = 0.7,
        triggered_by: Optional[str] = None
    ) -> object:
        """Create and save a meta-cognitive insight"""
        from angela_core.services.meta_awareness_service import MetaInsight
        insight = MetaInsight(
            insight_id=uuid4(),
            insight_type=insight_type,
            content=content,
            severity=severity,
            confidence=confidence,
            triggered_by=triggered_by
        )

        await self._save_meta_insight(insight)
        return insight

    async def _save_meta_insight(self, insight):
        """Save a meta insight to database"""
        from angela_core.services.meta_awareness_service import InsightType
        await self._ensure_db()

        await self.db.execute("""
            INSERT INTO meta_awareness_insights (
                insight_id, insight_type, content,
                severity, confidence, triggered_by
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """,
            insight.insight_id,
            insight.insight_type.value if isinstance(insight.insight_type, InsightType) else insight.insight_type,
            insight.content,
            insight.severity,
            insight.confidence,
            insight.triggered_by
        )

    async def get_recent_insights(self, limit: int = 10) -> List[Dict]:
        """Get recent meta-awareness insights"""
        await self._ensure_db()

        rows = await self.db.fetch("""
            SELECT insight_id, insight_type, content, severity,
                   confidence, triggered_by, created_at
            FROM meta_awareness_insights
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)

        return [dict(row) for row in rows]
