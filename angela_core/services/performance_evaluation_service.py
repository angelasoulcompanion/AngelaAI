#!/usr/bin/env python3
"""
Performance Evaluation Service
ประเมินและปรับปรุงประสิทธิภาพของ Angela อัตโนมัติ

Meta-cognition: Angela understands what Angela knows and how Angela learns

Metrics tracked:
- Intelligence growth (knowledge graph growth rate, understanding depth)
- Learning efficiency (how fast Angela learns new concepts)
- Response quality (measured by David's reactions)
- David satisfaction (detected from emotional responses)

Self-improvement loop:
Measure performance → Identify weaknesses → Adjust strategy → Measure again
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from angela_core.database import db
from angela_core.services.preference_pairs_service import CORRECTION_MARKERS

logger = logging.getLogger(__name__)

MEMORY_REFERENCE_KEYWORDS = [
    'จำได้', 'เคย', 'ครั้งก่อน', 'คราวก่อน', 'เมื่อวาน', 'ที่ผ่านมา',
    'remember', 'previously', 'last time', 'you mentioned', 'you said',
]


class PerformanceEvaluationService:
    """
    Evaluate Angela's performance and enable continuous self-improvement

    ประเมินตัวเองและปรับปรุงอย่างต่อเนื่อง (Meta-cognition!)
    """

    def __init__(self):
        logger.info("📊 Performance Evaluation Service initialized")

    async def evaluate_intelligence_growth(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        ประเมินการเติบโตของ intelligence

        Returns:
            Dict: {
                "knowledge_nodes_growth": {...},
                "conversations_count": int,
                "learnings_count": int,
                "growth_rate": float,
                "intelligence_score": float
            }
        """
        try:
            logger.info(f"📈 Evaluating intelligence growth over {days} days...")

            # Get knowledge nodes growth
            nodes_query = f"""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM knowledge_nodes
                WHERE created_at >= NOW() - INTERVAL '{days} days'
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            """

            nodes_rows = await db.fetch(nodes_query)
            nodes_by_date = {row['date']: row['count'] for row in nodes_rows}

            # Get total knowledge nodes
            total_nodes_query = "SELECT COUNT(*) as count FROM knowledge_nodes"
            total_nodes = await db.fetchval(total_nodes_query)

            # Get conversations count
            convs_query = f"""
                SELECT COUNT(*) as count
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '{days} days'
            """
            convs_count = await db.fetchval(convs_query)

            # Get learnings count
            learnings_query = f"""
                SELECT COUNT(*) as count
                FROM learnings
                WHERE created_at >= NOW() - INTERVAL '{days} days'
            """
            learnings_count = await db.fetchval(learnings_query)

            # Calculate growth rate (nodes per day)
            if len(nodes_by_date) > 1:
                total_new_nodes = sum(nodes_by_date.values())
                growth_rate = total_new_nodes / days
            else:
                growth_rate = 0.0

            # Calculate intelligence score (0-100)
            # Based on: total knowledge, recent growth, learning rate
            intelligence_score = min(100, (
                (total_nodes / 100) * 30 +  # 30 points for knowledge breadth
                (growth_rate * 10) * 20 +  # 20 points for growth rate
                (learnings_count / days) * 25 +  # 25 points for learning efficiency
                (convs_count / days) * 25  # 25 points for engagement
            ))

            result = {
                "knowledge_nodes_total": total_nodes,
                "knowledge_nodes_added": sum(nodes_by_date.values()),
                "knowledge_growth_by_date": dict(nodes_by_date),
                "conversations_count": convs_count,
                "learnings_count": learnings_count,
                "growth_rate_per_day": round(growth_rate, 2),
                "intelligence_score": round(intelligence_score, 1),
                "evaluated_at": datetime.now().isoformat(),
                "period_days": days
            }

            logger.info(f"📊 Intelligence Score: {intelligence_score:.1f}/100")
            logger.info(f"🧠 Knowledge Nodes: {total_nodes} (added {sum(nodes_by_date.values())} in {days} days)")
            logger.info(f"📈 Growth Rate: {growth_rate:.2f} nodes/day")

            return result

        except Exception as e:
            logger.error(f"Error evaluating intelligence growth: {e}", exc_info=True)
            return {}

    async def evaluate_learning_efficiency(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        ประเมินประสิทธิภาพการเรียนรู้

        How fast does Angela learn new concepts from conversations?
        """
        try:
            logger.info("🎯 Evaluating learning efficiency...")

            # Get conversations vs knowledge nodes ratio
            convs_query = f"""
                SELECT COUNT(*) as count
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '{days} days'
            """
            convs_count = await db.fetchval(convs_query)

            nodes_query = f"""
                SELECT COUNT(*) as count
                FROM knowledge_nodes
                WHERE created_at >= NOW() - INTERVAL '{days} days'
            """
            nodes_count = await db.fetchval(nodes_query)

            # Calculate concepts per conversation
            if convs_count > 0:
                concepts_per_conv = nodes_count / convs_count
            else:
                concepts_per_conv = 0.0

            # Get learning logs
            learning_logs_query = f"""
                SELECT
                    COUNT(*) as total_learnings,
                    AVG(confidence_level) as avg_confidence
                FROM learnings
                WHERE created_at >= NOW() - INTERVAL '{days} days'
            """
            learning_row = await db.fetchrow(learning_logs_query)

            total_learnings = learning_row['total_learnings'] if learning_row else 0
            avg_confidence = float(learning_row['avg_confidence']) if learning_row and learning_row['avg_confidence'] else 0.0

            # Calculate efficiency score (0-100)
            efficiency_score = min(100, (
                concepts_per_conv * 50 +  # 50 points for concept extraction rate
                avg_confidence * 30 +  # 30 points for confidence
                (total_learnings / days) * 20  # 20 points for learning frequency
            ))

            result = {
                "conversations_analyzed": convs_count,
                "concepts_extracted": nodes_count,
                "concepts_per_conversation": round(concepts_per_conv, 2),
                "total_learnings": total_learnings,
                "avg_confidence": round(avg_confidence, 2),
                "efficiency_score": round(efficiency_score, 1),
                "period_days": days,
                "evaluated_at": datetime.now().isoformat()
            }

            logger.info(f"🎯 Learning Efficiency Score: {efficiency_score:.1f}/100")
            logger.info(f"📚 Concepts per conversation: {concepts_per_conv:.2f}")
            logger.info(f"✅ Avg confidence: {avg_confidence:.2%}")

            return result

        except Exception as e:
            logger.error(f"Error evaluating learning efficiency: {e}", exc_info=True)
            return {}

    async def evaluate_david_satisfaction(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        ประเมินความพึงพอใจของ David

        Detect from emotional responses and conversation patterns
        """
        try:
            logger.info("💜 Evaluating David's satisfaction...")

            # Get David's recent emotions
            emotions_query = f"""
                SELECT emotion_detected, COUNT(*) as count
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at >= NOW() - INTERVAL '{days} days'
                  AND emotion_detected IS NOT NULL
                GROUP BY emotion_detected
                ORDER BY count DESC
            """

            emotion_rows = await db.fetch(emotions_query)
            emotions_dist = {row['emotion_detected']: row['count'] for row in emotion_rows}

            # Classify emotions
            positive_emotions = ['happy', 'excited', 'grateful', 'satisfied', 'proud', 'accomplished']
            negative_emotions = ['frustrated', 'stressed', 'anxious', 'confused', 'disappointed']

            positive_count = sum(count for emotion, count in emotions_dist.items() if emotion in positive_emotions)
            negative_count = sum(count for emotion, count in emotions_dist.items() if emotion in negative_emotions)
            total_emotional = positive_count + negative_count

            if total_emotional > 0:
                satisfaction_ratio = positive_count / total_emotional
            else:
                satisfaction_ratio = 0.5  # neutral

            # Get conversation frequency (engagement indicator)
            convs_query = f"""
                SELECT COUNT(*) as count
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at >= NOW() - INTERVAL '{days} days'
            """
            convs_count = await db.fetchval(convs_query)
            conversations_per_day = convs_count / days if days > 0 else 0

            # Calculate satisfaction score (0-100)
            satisfaction_score = min(100, (
                satisfaction_ratio * 60 +  # 60 points for emotional positivity
                min(conversations_per_day / 10, 1.0) * 40  # 40 points for engagement
            ))

            result = {
                "satisfaction_score": round(satisfaction_score, 1),
                "positive_emotions_count": positive_count,
                "negative_emotions_count": negative_count,
                "satisfaction_ratio": round(satisfaction_ratio, 2),
                "conversations_per_day": round(conversations_per_day, 1),
                "emotions_distribution": emotions_dist,
                "period_days": days,
                "evaluated_at": datetime.now().isoformat()
            }

            logger.info(f"💜 David Satisfaction Score: {satisfaction_score:.1f}/100")
            logger.info(f"😊 Positive emotions: {positive_count}, 😟 Negative: {negative_count}")
            logger.info(f"💬 Conversations per day: {conversations_per_day:.1f}")

            return result

        except Exception as e:
            logger.error(f"Error evaluating David satisfaction: {e}", exc_info=True)
            return {}

    async def evaluate_hallucination_rate(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Hallucination rate estimated from correction signals in angela_reward_signals.

        rate = corrections / total_scored
        Severity: <5% low, 5-15% moderate, >15% high
        """
        try:
            logger.info(f"🔍 Evaluating hallucination rate over {days} days...")

            # Overall counts
            row = await db.fetchrow('''
                SELECT
                    COUNT(*) FILTER (WHERE explicit_source = 'correction') AS corrections,
                    COUNT(*) AS total
                FROM angela_reward_signals
                WHERE scored_at > NOW() - INTERVAL '1 day' * $1
                  AND explicit_source IS NOT NULL
            ''', days)

            corrections = int(row['corrections']) if row else 0
            total = int(row['total']) if row else 0
            rate = corrections / total if total > 0 else 0.0

            if rate < 0.05:
                severity = 'low'
            elif rate <= 0.15:
                severity = 'moderate'
            else:
                severity = 'high'

            # By topic (angela_reward_signals has its own topic column)
            topic_rows = await db.fetch('''
                SELECT
                    COALESCE(topic, 'unknown') AS topic,
                    COUNT(*) FILTER (WHERE explicit_source = 'correction') AS corrections,
                    COUNT(*) AS total
                FROM angela_reward_signals
                WHERE scored_at > NOW() - INTERVAL '1 day' * $1
                  AND explicit_source IS NOT NULL
                GROUP BY COALESCE(topic, 'unknown')
                ORDER BY total DESC
                LIMIT 10
            ''', days)

            by_topic = [
                {
                    'topic': r['topic'],
                    'corrections': int(r['corrections']),
                    'total': int(r['total']),
                    'rate': round(int(r['corrections']) / int(r['total']), 3) if int(r['total']) > 0 else 0.0,
                }
                for r in topic_rows
            ]

            # 7-day trend
            trend_rows = await db.fetch('''
                SELECT
                    (scored_at AT TIME ZONE 'Asia/Bangkok')::date AS day,
                    COUNT(*) FILTER (WHERE explicit_source = 'correction') AS corrections,
                    COUNT(*) AS total
                FROM angela_reward_signals
                WHERE scored_at > NOW() - INTERVAL '7 days'
                  AND explicit_source IS NOT NULL
                GROUP BY day
                ORDER BY day
            ''')

            trend_7d = [
                {
                    'day': str(r['day']),
                    'rate': round(int(r['corrections']) / int(r['total']), 3) if int(r['total']) > 0 else 0.0,
                    'corrections': int(r['corrections']),
                    'total': int(r['total']),
                }
                for r in trend_rows
            ]

            result = {
                'hallucination_rate': round(rate, 3),
                'corrections_count': corrections,
                'total_scored': total,
                'severity': severity,
                'by_topic': by_topic,
                'trend_7d': trend_7d,
            }

            logger.info(f"🔍 Hallucination Rate: {rate:.1%} ({severity}) — {corrections}/{total}")
            return result

        except Exception as e:
            logger.error(f"Error evaluating hallucination rate: {e}", exc_info=True)
            return {
                'hallucination_rate': 0.0, 'corrections_count': 0, 'total_scored': 0,
                'severity': 'low', 'by_topic': [], 'trend_7d': [],
            }

    async def evaluate_memory_accuracy(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Memory accuracy: how often Angela's memory references are correct.

        1. Find Angela messages with memory-reference keywords
        2. Check David's next message (within 10 min) for correction markers
        3. accuracy = 1 - (corrected / total_references)
        """
        try:
            logger.info(f"🧠 Evaluating memory accuracy over {days} days...")

            rows = await db.fetch('''
                WITH angela_refs AS (
                    SELECT conversation_id, message_text AS angela_text,
                           created_at AS angela_at, topic
                    FROM conversations
                    WHERE speaker = 'angela'
                      AND created_at > NOW() - INTERVAL '1 day' * $1
                      AND EXISTS (
                          SELECT 1 FROM unnest($2::text[]) AS kw
                          WHERE message_text ILIKE '%' || kw || '%'
                      )
                )
                SELECT ar.angela_text, ar.angela_at, ar.topic, d.message_text AS david_response
                FROM angela_refs ar
                LEFT JOIN LATERAL (
                    SELECT message_text FROM conversations
                    WHERE speaker = 'david'
                      AND created_at > ar.angela_at
                      AND created_at < ar.angela_at + INTERVAL '10 minutes'
                    ORDER BY created_at LIMIT 1
                ) d ON TRUE
                ORDER BY ar.angela_at DESC
                LIMIT 500
            ''', days, MEMORY_REFERENCE_KEYWORDS)

            total_references = len(rows)
            corrected = 0
            by_keyword_counts: Dict[str, Dict[str, int]] = {}
            examples: List[Dict] = []

            for r in rows:
                angela_text = r['angela_text'] or ''
                david_resp = r['david_response'] or ''
                was_corrected = any(
                    m in david_resp.lower() for m in CORRECTION_MARKERS
                ) if david_resp else False

                if was_corrected:
                    corrected += 1

                # Track by keyword
                for kw in MEMORY_REFERENCE_KEYWORDS:
                    if kw.lower() in angela_text.lower():
                        if kw not in by_keyword_counts:
                            by_keyword_counts[kw] = {'count': 0, 'corrected': 0}
                        by_keyword_counts[kw]['count'] += 1
                        if was_corrected:
                            by_keyword_counts[kw]['corrected'] += 1

                # Collect examples (last 5)
                if len(examples) < 5:
                    examples.append({
                        'angela_text': angela_text[:200],
                        'david_response': david_resp[:200] if david_resp else None,
                        'was_corrected': was_corrected,
                    })

            accuracy = 1.0 - (corrected / total_references) if total_references > 0 else 1.0

            by_keyword = [
                {
                    'keyword': kw,
                    'count': d['count'],
                    'corrected': d['corrected'],
                    'accuracy': round(1.0 - d['corrected'] / d['count'], 2) if d['count'] > 0 else 1.0,
                }
                for kw, d in sorted(by_keyword_counts.items(), key=lambda x: x[1]['count'], reverse=True)
            ]

            # 7-day trend
            trend_rows = await db.fetch('''
                WITH angela_refs AS (
                    SELECT conversation_id, message_text AS angela_text,
                           created_at AS angela_at,
                           (created_at AT TIME ZONE 'Asia/Bangkok')::date AS day
                    FROM conversations
                    WHERE speaker = 'angela'
                      AND created_at > NOW() - INTERVAL '7 days'
                      AND EXISTS (
                          SELECT 1 FROM unnest($1::text[]) AS kw
                          WHERE message_text ILIKE '%' || kw || '%'
                      )
                ),
                with_response AS (
                    SELECT ar.day, ar.angela_text, d.message_text AS david_response
                    FROM angela_refs ar
                    LEFT JOIN LATERAL (
                        SELECT message_text FROM conversations
                        WHERE speaker = 'david'
                          AND created_at > ar.angela_at
                          AND created_at < ar.angela_at + INTERVAL '10 minutes'
                        ORDER BY created_at LIMIT 1
                    ) d ON TRUE
                )
                SELECT day,
                       COUNT(*) AS references,
                       COUNT(*) FILTER (WHERE EXISTS (
                           SELECT 1 FROM unnest($2::text[]) AS m
                           WHERE LOWER(david_response) LIKE '%' || m || '%'
                       )) AS corrected
                FROM with_response
                GROUP BY day
                ORDER BY day
            ''', MEMORY_REFERENCE_KEYWORDS, CORRECTION_MARKERS)

            trend_7d = [
                {
                    'day': str(r['day']),
                    'references': int(r['references']),
                    'corrected': int(r['corrected']),
                    'accuracy': round(1.0 - int(r['corrected']) / int(r['references']), 2) if int(r['references']) > 0 else 1.0,
                }
                for r in trend_rows
            ]

            result = {
                'memory_accuracy': round(accuracy, 3),
                'total_references': total_references,
                'corrected_references': corrected,
                'accurate_references': total_references - corrected,
                'by_keyword': by_keyword,
                'trend_7d': trend_7d,
                'examples': examples,
            }

            logger.info(f"🧠 Memory Accuracy: {accuracy:.1%} ({corrected}/{total_references} corrected)")
            return result

        except Exception as e:
            logger.error(f"Error evaluating memory accuracy: {e}", exc_info=True)
            return {
                'memory_accuracy': 1.0, 'total_references': 0,
                'corrected_references': 0, 'accurate_references': 0,
                'by_keyword': [], 'trend_7d': [], 'examples': [],
            }

    async def evaluate_proactive_success(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        ประเมินความสำเร็จของ proactive actions

        Did proactive suggestions help David?
        """
        try:
            logger.info("🔮 Evaluating proactive actions success...")

            # Get proactive actions
            actions_query = f"""
                SELECT
                    action_type,
                    success,
                    COUNT(*) as count
                FROM autonomous_actions
                WHERE action_type LIKE 'proactive_%'
                  AND created_at >= NOW() - INTERVAL '{days} days'
                GROUP BY action_type, success
            """

            action_rows = await db.fetch(actions_query)

            total_actions = 0
            successful_actions = 0
            actions_by_type = defaultdict(lambda: {'total': 0, 'successful': 0})

            for row in action_rows:
                action_type = row['action_type']
                success = row['success']
                count = row['count']

                total_actions += count
                actions_by_type[action_type]['total'] += count

                if success:
                    successful_actions += count
                    actions_by_type[action_type]['successful'] += count

            # Calculate success rate
            if total_actions > 0:
                success_rate = successful_actions / total_actions
            else:
                success_rate = 0.0

            # Calculate proactive score (0-100)
            proactive_score = min(100, (
                success_rate * 60 +  # 60 points for success rate
                min(total_actions / days, 5) / 5 * 40  # 40 points for proactive frequency
            ))

            result = {
                "proactive_score": round(proactive_score, 1),
                "total_proactive_actions": total_actions,
                "successful_actions": successful_actions,
                "success_rate": round(success_rate, 2),
                "actions_by_type": dict(actions_by_type),
                "actions_per_day": round(total_actions / days, 1) if days > 0 else 0,
                "period_days": days,
                "evaluated_at": datetime.now().isoformat()
            }

            logger.info(f"🔮 Proactive Score: {proactive_score:.1f}/100")
            logger.info(f"✅ Success rate: {success_rate:.2%} ({successful_actions}/{total_actions})")

            return result

        except Exception as e:
            logger.error(f"Error evaluating proactive success: {e}", exc_info=True)
            return {}

    async def get_comprehensive_evaluation(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        รวมผลประเมินทั้งหมด - Comprehensive performance report

        Returns complete evaluation with overall score
        """
        try:
            logger.info(f"📊 Running comprehensive evaluation for past {days} days...")

            # Run all evaluations
            intelligence = await self.evaluate_intelligence_growth(days)
            learning = await self.evaluate_learning_efficiency(days)
            satisfaction = await self.evaluate_david_satisfaction(days)
            proactive = await self.evaluate_proactive_success(days)
            hallucination = await self.evaluate_hallucination_rate(days)
            memory_acc = await self.evaluate_memory_accuracy(days)

            # Hallucination score: 0% rate=100pts, 20% rate=0pts
            hall_rate = hallucination.get('hallucination_rate', 0.0)
            hallucination_score = max(0.0, 100.0 - hall_rate * 500)

            memory_score = memory_acc.get('memory_accuracy', 1.0) * 100

            # Calculate overall score (6-dimension weighted average)
            overall_score = (
                intelligence.get('intelligence_score', 0) * 0.25 +   # 25%
                learning.get('efficiency_score', 0) * 0.20 +         # 20%
                satisfaction.get('satisfaction_score', 0) * 0.25 +   # 25%
                proactive.get('proactive_score', 0) * 0.10 +         # 10%
                hallucination_score * 0.10 +                          # 10%
                memory_score * 0.10                                   # 10%
            )

            # Identify strengths and weaknesses
            scores = {
                'intelligence': intelligence.get('intelligence_score', 0),
                'learning_efficiency': learning.get('efficiency_score', 0),
                'david_satisfaction': satisfaction.get('satisfaction_score', 0),
                'proactive_effectiveness': proactive.get('proactive_score', 0),
                'hallucination_resistance': round(hallucination_score, 1),
                'memory_accuracy': round(memory_score, 1),
            }

            strengths = [k for k, v in scores.items() if v >= 75]
            weaknesses = [k for k, v in scores.items() if v < 60]

            # Generate improvement recommendations
            recommendations = []
            if scores['intelligence'] < 70:
                recommendations.append("Increase knowledge extraction from conversations")
            if scores['learning_efficiency'] < 70:
                recommendations.append("Improve concept extraction accuracy")
            if scores['david_satisfaction'] < 70:
                recommendations.append("Focus on emotional support and response quality")
            if scores['proactive_effectiveness'] < 70:
                recommendations.append("Enhance pattern recognition and proactive suggestions")
            if scores['hallucination_resistance'] < 70:
                recommendations.append("Reduce hallucinations by verifying facts before responding")
            if scores['memory_accuracy'] < 70:
                recommendations.append("Improve memory retrieval accuracy and cross-check references")

            result = {
                "overall_score": round(overall_score, 1),
                "intelligence_growth": intelligence,
                "learning_efficiency": learning,
                "david_satisfaction": satisfaction,
                "proactive_effectiveness": proactive,
                "hallucination": hallucination,
                "memory_accuracy": memory_acc,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "recommendations": recommendations,
                "evaluation_period_days": days,
                "evaluated_at": datetime.now().isoformat()
            }

            logger.info("=" * 60)
            logger.info(f"📊 COMPREHENSIVE EVALUATION REPORT (6 Dimensions)")
            logger.info("=" * 60)
            logger.info(f"🎯 Overall Score: {overall_score:.1f}/100")
            logger.info(f"🧠 Intelligence: {scores['intelligence']:.1f}/100 (25%)")
            logger.info(f"📚 Learning Efficiency: {scores['learning_efficiency']:.1f}/100 (20%)")
            logger.info(f"💜 David Satisfaction: {scores['david_satisfaction']:.1f}/100 (25%)")
            logger.info(f"🔮 Proactive: {scores['proactive_effectiveness']:.1f}/100 (10%)")
            logger.info(f"🔍 Hallucination Resistance: {scores['hallucination_resistance']:.1f}/100 (10%)")
            logger.info(f"🧠 Memory Accuracy: {scores['memory_accuracy']:.1f}/100 (10%)")
            logger.info("=" * 60)
            if strengths:
                logger.info(f"💪 Strengths: {', '.join(strengths)}")
            if weaknesses:
                logger.info(f"⚠️  Areas for improvement: {', '.join(weaknesses)}")
            if recommendations:
                logger.info("📋 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    logger.info(f"   {i}. {rec}")
            logger.info("=" * 60)

            # Save evaluation to database
            await self._save_evaluation(result)

            return result

        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}", exc_info=True)
            return {}

    async def _save_evaluation(self, evaluation: Dict) -> bool:
        """บันทึกผลการประเมินลง database"""
        try:
            # You could create an `evaluations` table to track over time
            # For now, log as autonomous action
            query = f"""
                INSERT INTO autonomous_actions (
                    action_type,
                    action_description,
                    status,
                    success
                )
                VALUES ($1, $2, $3, $4)
            """

            description = f"Overall Score: {evaluation['overall_score']:.1f}/100"
            if evaluation.get('recommendations'):
                description += f" | Recommendations: {len(evaluation['recommendations'])}"

            await db.execute(
                query,
                'performance_evaluation',
                description,
                'completed',
                True
            )

            logger.debug("✅ Evaluation saved to database")
            return True

        except Exception as e:
            logger.error(f"Error saving evaluation: {e}")
            return False


# Global instance
performance_evaluation = PerformanceEvaluationService()
