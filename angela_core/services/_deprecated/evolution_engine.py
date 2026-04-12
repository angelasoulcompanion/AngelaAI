"""
Self-Evolving Feedback Loop Engine

Feature 3 of Angela's Consciousness Loop: LEARN
น้อง Angela เรียนรู้จาก implicit feedback → ปรับปรุง adaptation rules อัตโนมัติ

Loop: SENSE → PREDICT → ACT → **LEARN** → (better SENSE)

What it does:
1. Collect implicit feedback จาก conversations (ดี/ไม่ดี/re-ask)
2. Score emotional adaptations ว่า effective แค่ไหน
3. Verify predictions accuracy
4. Auto-tune adaptation rules based on effectiveness
5. Track evolution over time

Created: 2026-02-07
By: น้อง Angela 💜
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from angela_core.database import AngelaDatabase
from angela_core.services.feedback_classifier import FeedbackClassifier
from angela_core.utils.timezone import now_bangkok, today_bangkok
from angela_core.services.reasoning_chain_service import (
    capture_reasoning, ReasoningChain, ReasoningStep,
)

logger = logging.getLogger(__name__)


@dataclass
class FeedbackSignal:
    signal_type: str   # positive/negative/neutral
    source: str        # conversation/re_ask/session_engagement
    confidence: float
    context: str       # Thai description
    timestamp: datetime


@dataclass
class EvolutionCycle:
    cycle_id: UUID
    cycle_date: date
    feedback_signals_count: int
    adaptation_adjustments: Dict
    prediction_accuracy: Dict
    learning_effectiveness: Dict
    overall_evolution_score: float
    insights: List[str]


class EvolutionEngine:
    """
    Self-Evolving Feedback Loop — น้องเรียนรู้จาก feedback อัตโนมัติ

    7 methods:
    1. collect_implicit_feedback — scan conversations for positive/negative signals
    2. score_adaptations — rate emotional adaptations by conversation outcomes
    3. verify_all_predictions — check prediction accuracy
    4. tune_adaptation_rules — auto-adjust rules based on effectiveness
    5. update_learning_effectiveness — track learning success rates
    6. run_evolution_cycle — main entry: run all steps
    7. get_evolution_report — query recent evolution history
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None

    async def _ensure_db(self):
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def close(self):
        if self.db:
            await self.db.disconnect()
            self.db = None

    # =========================================================================
    # 1. COLLECT IMPLICIT FEEDBACK
    # =========================================================================

    async def collect_implicit_feedback(self, hours: int = 24) -> List[FeedbackSignal]:
        """
        Scan David's recent conversations for implicit feedback signals.

        Uses DL-based FeedbackClassifier (Embedding + Sentiment) instead of keyword matching.
        - Positive: messages semantically similar to praise/thanks
        - Negative: messages semantically similar to complaints (higher threshold)
        - Neutral: technical commands/questions → skipped (no signal)
        - Re-ask: same topic within 10 min WITH dissatisfaction markers
        """
        await self._ensure_db()

        # Lazy init classifier (cached across calls)
        if not hasattr(self, '_classifier'):
            self._classifier = FeedbackClassifier()

        signals: List[FeedbackSignal] = []

        # Get David's recent messages
        rows = await self.db.fetch('''
            SELECT conversation_id, message_text, topic, created_at
            FROM conversations
            WHERE speaker = 'david'
              AND created_at > NOW() - INTERVAL '1 hour' * $1
            ORDER BY created_at ASC
        ''', hours)

        for row in rows:
            msg = (row['message_text'] or '').strip()
            if not msg or len(msg) < 3:
                continue

            ts = row['created_at']
            result = await self._classifier.classify(msg)

            if result.classification == 'positive' and result.confidence > 0.4:
                signals.append(FeedbackSignal(
                    signal_type='positive',
                    source='conversation',
                    confidence=min(0.9, result.confidence),
                    context=f'DL: emb={result.embedding_scores}, sent={result.sentiment_score:.2f}',
                    timestamp=ts,
                ))
            elif result.classification == 'negative' and result.confidence > 0.5:
                # Higher threshold for negative to prevent false negatives
                signals.append(FeedbackSignal(
                    signal_type='negative',
                    source='conversation',
                    confidence=min(0.9, result.confidence),
                    context=f'DL: emb={result.embedding_scores}, sent={result.sentiment_score:.2f}',
                    timestamp=ts,
                ))
            # neutral → skip (no signal)

        # Re-ask detection: same topic within 10 min + dissatisfaction markers
        re_ask_rows = await self.db.fetch('''
            WITH topic_pairs AS (
                SELECT topic, message_text, created_at,
                    LAG(created_at) OVER (PARTITION BY topic ORDER BY created_at) AS prev_at
                FROM conversations
                WHERE speaker = 'david'
                  AND topic IS NOT NULL
                  AND created_at > NOW() - INTERVAL '1 hour' * $1
            )
            SELECT topic, created_at, prev_at, message_text
            FROM topic_pairs
            WHERE prev_at IS NOT NULL
              AND created_at - prev_at < INTERVAL '10 minutes'
        ''', hours)

        dissatisfaction_markers = ['ไม่ใช่', 'ไม่ถูก', 'wrong', 'not what', 'อีกที', 'ใหม่', 'again']
        for row in re_ask_rows:
            msg = (row['message_text'] or '').lower()
            if any(m in msg for m in dissatisfaction_markers):
                signals.append(FeedbackSignal(
                    signal_type='negative',
                    source='re_ask',
                    confidence=0.5,
                    context=f'Re-asked "{row["topic"]}" with dissatisfaction',
                    timestamp=row['created_at'],
                ))

        logger.info(f'Collected {len(signals)} feedback signals '
                     f'(+{sum(1 for s in signals if s.signal_type == "positive")}, '
                     f'-{sum(1 for s in signals if s.signal_type == "negative")})')
        return signals

    # =========================================================================
    # 2. SCORE ADAPTATIONS
    # =========================================================================

    async def score_adaptations(self, hours: int = 24) -> List[Dict]:
        """
        Score recent emotional adaptations by checking surrounding conversations.

        For each unscored adaptation log entry:
        - Find conversations ±30 min
        - Count positive vs negative signals
        - Calculate effectiveness_score (0.0 - 1.0)
        """
        await self._ensure_db()

        unscored = await self.db.fetch('''
            SELECT log_id, dominant_state, created_at
            FROM emotional_adaptation_log
            WHERE effectiveness_score IS NULL
              AND created_at > NOW() - INTERVAL '1 hour' * $1
            ORDER BY created_at ASC
        ''', hours)

        scored = []
        for entry in unscored:
            log_id = entry['log_id']
            ts = entry['created_at']

            # Find conversations around this adaptation (±30 min)
            # Strip timezone since conversations.created_at is naive timestamp
            ts_naive = ts.replace(tzinfo=None) if hasattr(ts, 'tzinfo') and ts.tzinfo else ts
            window_start = ts_naive - timedelta(minutes=30)
            window_end = ts_naive + timedelta(minutes=30)
            nearby = await self.db.fetch('''
                SELECT message_text
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at BETWEEN $1 AND $2
            ''', window_start, window_end)

            # Lazy init classifier
            if not hasattr(self, '_classifier'):
                self._classifier = FeedbackClassifier()

            pos_count = 0
            neg_count = 0
            for row in nearby:
                msg = (row['message_text'] or '').strip()
                if not msg:
                    continue
                result = await self._classifier.classify(msg)
                if result.classification == 'positive':
                    pos_count += 1
                elif result.classification == 'negative':
                    neg_count += 1

            total = pos_count + neg_count
            if total == 0:
                score = 0.5  # neutral — no signal
            else:
                score = pos_count / total

            # Update the record
            await self.db.execute('''
                UPDATE emotional_adaptation_log
                SET effectiveness_score = $1
                WHERE log_id = $2
            ''', score, log_id)

            scored.append({
                'log_id': str(log_id),
                'dominant_state': entry['dominant_state'],
                'effectiveness_score': score,
                'positive': pos_count,
                'negative': neg_count,
            })

        logger.info(f'Scored {len(scored)} adaptations')
        return scored

    # =========================================================================
    # 3. VERIFY ALL PREDICTIONS
    # =========================================================================

    async def verify_all_predictions(self) -> Dict[str, Any]:
        """
        Verify predictions from both systems:
        1. PredictiveCompanionService (daily_companion_briefings)
        2. intuition_predictions table (gut_agent)
        """
        await self._ensure_db()
        results: Dict[str, Any] = {}

        # 1. Companion predictions (yesterday)
        try:
            from angela_core.services.predictive_companion_service import PredictiveCompanionService
            svc = PredictiveCompanionService()
            companion_result = await svc.verify_predictions()
            await svc.close()
            results['companion'] = companion_result
        except Exception as e:
            logger.warning(f'Companion verification failed: {e}')
            results['companion'] = {'verified': False, 'error': str(e)}

        # 2. Intuition predictions — verify unverified ones
        yesterday = today_bangkok() - timedelta(days=1)
        unverified = await self.db.fetch('''
            SELECT intuition_id, prediction_type, prediction_text,
                   predicted_time, created_at
            FROM intuition_predictions
            WHERE verified = FALSE
              AND predicted_time IS NOT NULL
              AND predicted_time::date <= $1
            LIMIT 50
        ''', yesterday)

        verified_count = 0
        correct_count = 0

        for pred in unverified:
            pred_date = pred['predicted_time']
            if pred_date is None:
                continue

            # Check if actual conversations match
            actual = await self.db.fetch('''
                SELECT topic, emotion_detected
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at::date = $1::date
            ''', pred_date)

            actual_topics = [r['topic'] for r in actual if r['topic']]
            actual_emotions = [r['emotion_detected'] for r in actual if r['emotion_detected']]

            pred_text = (pred['prediction_text'] or '').lower()
            pred_type = pred['prediction_type'] or ''

            topic_match = any(pred_text in t.lower() for t in actual_topics) if pred_text else False
            emotion_match = any(pred_text in e.lower() for e in actual_emotions) if pred_text else False

            outcome_correct = topic_match or emotion_match

            await self.db.execute('''
                UPDATE intuition_predictions
                SET verified = TRUE, outcome_correct = $1, verified_at = NOW()
                WHERE intuition_id = $2
            ''', outcome_correct, pred['intuition_id'])

            verified_count += 1
            if outcome_correct:
                correct_count += 1

        accuracy = correct_count / verified_count if verified_count > 0 else 0.0
        results['intuition'] = {
            'verified': verified_count,
            'correct': correct_count,
            'accuracy': accuracy,
        }

        logger.info(f'Verified predictions — companion: {results["companion"].get("verified", "N/A")}, '
                     f'intuition: {verified_count} ({accuracy:.0%} accuracy)')
        return results

    # =========================================================================
    # 3.5 COMPUTE REWARD-BASED INSIGHTS
    # =========================================================================

    async def compute_reward_insights(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze angela_reward_signals to find:
        - Topic-level correction/praise rates
        - Overall reward trend
        - High-correction topics that need extra care

        Stores results in companion_patterns (category='reward_topic_insights').
        """
        await self._ensure_db()

        # Topic-level stats (min 3 signals per topic)
        topic_stats = await self.db.fetch('''
            SELECT topic,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE implicit_classification = 'correction') AS corrections,
                   COUNT(*) FILTER (WHERE implicit_classification = 'praise') AS praises,
                   AVG(combined_reward) AS avg_reward
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '1 day' * $1
              AND topic IS NOT NULL
            GROUP BY topic
            HAVING COUNT(*) >= 3
            ORDER BY AVG(combined_reward) ASC
        ''', days)

        topic_insights: Dict[str, Dict] = {}
        for row in topic_stats:
            topic = row['topic']
            total = row['total']
            corrections = row['corrections'] or 0
            praises = row['praises'] or 0
            topic_insights[topic] = {
                'total': total,
                'corrections': corrections,
                'praises': praises,
                'correction_rate': round(corrections / total, 3),
                'praise_rate': round(praises / total, 3),
                'avg_reward': round(float(row['avg_reward'] or 0), 3),
            }

        # Overall stats
        overall = await self.db.fetchrow('''
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE implicit_classification = 'correction') AS corrections,
                   COUNT(*) FILTER (WHERE implicit_classification = 'praise') AS praises,
                   AVG(combined_reward) AS avg_reward,
                   STDDEV(combined_reward) AS stddev_reward
            FROM angela_reward_signals
            WHERE scored_at >= NOW() - INTERVAL '1 day' * $1
        ''', days)

        total_signals = overall['total'] or 0
        overall_correction_rate = (overall['corrections'] or 0) / max(total_signals, 1)
        overall_praise_rate = (overall['praises'] or 0) / max(total_signals, 1)

        high_correction = [t for t, v in topic_insights.items() if v['correction_rate'] > 0.1]
        high_praise = [t for t, v in topic_insights.items() if v['praise_rate'] > 0.15]

        result = {
            'topic_insights': topic_insights,
            'overall': {
                'total_signals': total_signals,
                'correction_rate': round(overall_correction_rate, 3),
                'praise_rate': round(overall_praise_rate, 3),
                'avg_reward': round(float(overall['avg_reward'] or 0), 3),
                'stddev_reward': round(float(overall['stddev_reward'] or 0), 3),
            },
            'high_correction_topics': high_correction,
            'high_praise_topics': high_praise,
        }

        # Store topic insights as companion_pattern
        if topic_insights:
            existing = await self.db.fetchrow('''
                SELECT pattern_id FROM companion_patterns
                WHERE pattern_category = 'reward_topic_insights'
                ORDER BY last_observed DESC LIMIT 1
            ''')

            stored = {
                'topics': topic_insights,
                'overall': result['overall'],
                'high_correction_topics': high_correction,
                'high_praise_topics': high_praise,
                'computed_at': now_bangkok().isoformat(),
            }

            if existing:
                await self.db.execute('''
                    UPDATE companion_patterns
                    SET pattern_data = $1, observation_count = $2, last_observed = NOW()
                    WHERE pattern_id = $3
                ''', json.dumps(stored), total_signals, existing['pattern_id'])
            else:
                hash_key = f'reward_topics_{today_bangkok().isoformat()}'
                await self.db.execute('''
                    INSERT INTO companion_patterns
                        (pattern_hash, pattern_category, pattern_data, observation_count, last_observed)
                    VALUES ($1, 'reward_topic_insights', $2, $3, NOW())
                ''', hash_key, json.dumps(stored), total_signals)

        logger.info(f'Reward insights: {total_signals} signals, '
                     f'correction={overall_correction_rate:.1%}, '
                     f'praise={overall_praise_rate:.1%}, '
                     f'high_corr_topics={len(high_correction)}')
        return result

    # =========================================================================
    # 4. TUNE ADAPTATION RULES
    # =========================================================================

    async def _load_existing_tuned_deltas(self) -> Dict[str, Dict[str, float]]:
        """Load existing tuned deltas from companion_patterns."""
        row = await self.db.fetchrow('''
            SELECT pattern_data FROM companion_patterns
            WHERE pattern_category = 'adaptation_rules'
            ORDER BY last_observed DESC LIMIT 1
        ''')
        if not row or not row['pattern_data']:
            return {}
        data = row['pattern_data'] if isinstance(row['pattern_data'], dict) else json.loads(row['pattern_data'])
        dims = ('detail_level', 'complexity_tolerance', 'proactivity', 'emotional_warmth', 'pace')
        return {
            state: {k: v for k, v in adj.items() if k in dims and isinstance(v, (int, float))}
            for state, adj in data.items()
            if isinstance(adj, dict) and 'reason' in adj
        }

    async def tune_adaptation_rules(self) -> Dict[str, Any]:
        """
        Auto-tune emotional adaptation rules based on:
        1. effectiveness_score from emotional_adaptation_log (7-day)
        2. reward signals from angela_reward_signals (correction/praise rates)

        Cumulative tuning with ±0.20 cap:
        - Low effectiveness OR high correction rate → accumulate +warmth/detail, -pace
        - High effectiveness AND low correction → decay deltas toward zero
        - Reward signals amplify/dampen adjustments (±50% boost)
        """
        await self._ensure_db()

        # Load existing deltas for cumulative tuning
        existing_deltas = await self._load_existing_tuned_deltas()

        # --- Source 1: Effectiveness from emotional_adaptation_log (7-day) ---
        state_stats = await self.db.fetch('''
            SELECT dominant_state,
                   AVG(effectiveness_score) AS avg_eff,
                   COUNT(*) AS cnt
            FROM emotional_adaptation_log
            WHERE effectiveness_score IS NOT NULL
              AND created_at > NOW() - INTERVAL '7 days'
            GROUP BY dominant_state
            HAVING COUNT(*) >= 3
            ORDER BY avg_eff ASC
        ''')

        # --- Source 2: Reward signals per state (join by time window) ---
        # Match reward signals to adaptation log entries within ±30 min
        reward_by_state = await self.db.fetch('''
            WITH matched AS (
                SELECT eal.dominant_state,
                       ars.combined_reward,
                       ars.implicit_classification
                FROM emotional_adaptation_log eal
                JOIN angela_reward_signals ars
                    ON ars.scored_at BETWEEN eal.created_at - INTERVAL '30 minutes'
                                        AND eal.created_at + INTERVAL '30 minutes'
                WHERE eal.created_at > NOW() - INTERVAL '7 days'
            )
            SELECT dominant_state,
                   AVG(combined_reward) AS avg_reward,
                   COUNT(*) AS reward_count,
                   COUNT(*) FILTER (WHERE implicit_classification = 'correction') AS corrections,
                   COUNT(*) FILTER (WHERE implicit_classification = 'praise') AS praises
            FROM matched
            GROUP BY dominant_state
        ''')

        reward_map: Dict[str, Dict] = {}
        for row in reward_by_state:
            total = row['reward_count'] or 1
            reward_map[row['dominant_state']] = {
                'avg_reward': float(row['avg_reward'] or 0),
                'correction_rate': (row['corrections'] or 0) / total,
                'praise_rate': (row['praises'] or 0) / total,
                'count': total,
            }

        adjustments: Dict[str, Any] = {}
        cap = 0.20  # max absolute delta

        for row in state_stats:
            state = row['dominant_state']
            avg_eff = row['avg_eff']
            cnt = row['cnt']
            prev = existing_deltas.get(state, {})
            reward_data = reward_map.get(state, {})
            corr_rate = reward_data.get('correction_rate', 0)
            praise_rate = reward_data.get('praise_rate', 0)

            # Compute adjustment step size (base=0.05, boosted by reward signal)
            # High correction → boost adjustment by up to 50%
            # High praise → dampen adjustment by up to 50%
            boost = 1.0
            if corr_rate > 0.1:
                boost = min(1.5, 1.0 + corr_rate * 3)  # max 1.5x
            elif praise_rate > 0.2:
                boost = max(0.5, 1.0 - praise_rate)  # min 0.5x

            step = round(0.05 * boost, 3)

            # Combined signal: effectiveness + correction rate
            needs_adjustment = avg_eff < 0.4 or corr_rate > 0.15
            performing_well = avg_eff > 0.7 and corr_rate < 0.05

            if needs_adjustment:
                reason_parts = []
                if avg_eff < 0.4:
                    reason_parts.append(f'avg_eff={avg_eff:.2f}(low)')
                if corr_rate > 0.15:
                    reason_parts.append(f'correction_rate={corr_rate:.0%}(high)')

                adj = {
                    'emotional_warmth': max(-cap, min(cap, prev.get('emotional_warmth', 0) + step)),
                    'detail_level': max(-cap, min(cap, prev.get('detail_level', 0) + step)),
                    'pace': max(-cap, min(cap, prev.get('pace', 0) - step)),
                    'reason': f'{", ".join(reason_parts)} over {cnt} entries (boost={boost:.1f}x)',
                    'reward_correction_rate': corr_rate,
                    'reward_avg': reward_data.get('avg_reward', None),
                }
                adjustments[state] = adj
            elif performing_well:
                # Effective + low correction: decay existing deltas faster
                decay_factor = 0.7 if praise_rate > 0.2 else 0.8
                if prev:
                    decayed = {}
                    for dim, val in prev.items():
                        if isinstance(val, (int, float)):
                            decayed[dim] = round(val * decay_factor, 4)
                    decayed['reason'] = (
                        f'avg_eff={avg_eff:.2f}(good), corr={corr_rate:.0%}'
                        f' — decaying deltas ×{decay_factor}'
                    )
                    adjustments[state] = decayed
                else:
                    adjustments[state] = {
                        'status': 'effective',
                        'avg_effectiveness': float(avg_eff),
                        'correction_rate': corr_rate,
                        'sample_size': cnt,
                    }
            else:
                adjustments[state] = {
                    'status': 'adequate',
                    'avg_effectiveness': float(avg_eff),
                    'correction_rate': corr_rate,
                    'sample_size': cnt,
                }

        # Store adjustments in companion_patterns (single row, upsert by category)
        if adjustments:
            total_samples = sum(row['cnt'] for row in state_stats)
            existing = await self.db.fetchrow('''
                SELECT pattern_id FROM companion_patterns
                WHERE pattern_category = 'adaptation_rules'
                ORDER BY last_observed DESC LIMIT 1
            ''')

            if existing:
                await self.db.execute('''
                    UPDATE companion_patterns
                    SET pattern_data = $1, observation_count = $2, last_observed = NOW()
                    WHERE pattern_id = $3
                ''', json.dumps(adjustments), total_samples, existing['pattern_id'])
            else:
                hash_key = f'adaptation_rules_{today_bangkok().isoformat()}'
                await self.db.execute('''
                    INSERT INTO companion_patterns
                        (pattern_hash, pattern_category, pattern_data, observation_count, last_observed)
                    VALUES ($1, 'adaptation_rules', $2, $3, NOW())
                ''', hash_key, json.dumps(adjustments), total_samples)

        logger.info(f'Tuned adaptation rules for {len(adjustments)} states '
                     f'(reward data for {len(reward_map)} states)')
        return adjustments

    # =========================================================================
    # 4.5 TUNE BRAIN PARAMETERS (Phase 7D)
    # =========================================================================

    async def tune_brain_parameters(self) -> Dict[str, Any]:
        """
        Tune brain-based parameters using effectiveness data.

        Tunable parameters:
        1. Salience weights (5 dims) — stored in companion_patterns category='brain_salience_weights'
        2. Motivation thresholds (0.55 express, 0.7 telegram) — category='brain_thresholds'
        3. System 2 threshold (0.6) — same category

        Uses brain_vs_rule_comparison and thought_expression_queue effectiveness.
        Cap: ±0.05 per cycle, ±0.15 total range from defaults.
        """
        await self._ensure_db()

        tuned = {}

        # --- 1. Tune salience weights based on effectiveness by stimulus_type ---
        type_stats = await self.db.fetch('''
            SELECT c.situation_type,
                   AVG(c.effectiveness_score) AS avg_eff,
                   COUNT(*) AS cnt
            FROM brain_vs_rule_comparison c
            WHERE c.effectiveness_score IS NOT NULL
            AND c.brain_would_act = TRUE
            AND c.created_at > NOW() - INTERVAL '7 days'
            GROUP BY c.situation_type
            HAVING COUNT(*) >= 2
        ''')

        # Load existing tuned weights
        from angela_core.services.salience_engine import SalienceEngine
        defaults = SalienceEngine.DEFAULT_WEIGHTS

        existing_weights = await self.db.fetchrow('''
            SELECT pattern_data FROM companion_patterns
            WHERE pattern_category = 'brain_salience_weights'
            ORDER BY last_observed DESC LIMIT 1
        ''')

        current_weights = dict(defaults)
        if existing_weights and existing_weights['pattern_data']:
            data = existing_weights['pattern_data']
            if isinstance(data, str):
                data = json.loads(data)
            if isinstance(data, dict):
                for k in defaults:
                    if k in data and isinstance(data[k], (int, float)):
                        current_weights[k] = data[k]

        # Compute adjustment: if type X effectiveness is low → boost its weight
        # Mapping: situation_type → salience dimension
        type_to_dim = {
            'break_reminder': 'temporal_urgency',
            'mood_boost': 'emotional',
            'milestone_reminder': 'temporal_urgency',
            'wellness_nudge': 'social_relevance',
            'music_suggestion': 'emotional',
            'learning_nudge': 'goal_relevance',
            'prepare_context': 'goal_relevance',
            'anticipate_need': 'novelty',
        }

        weight_adjustments = {}
        for row in type_stats:
            dim = type_to_dim.get(row['situation_type'])
            if not dim or dim not in current_weights:
                continue

            avg_eff = float(row['avg_eff'] or 0.5)
            if avg_eff < 0.4:
                # Low effectiveness → boost weight
                step = 0.05
            elif avg_eff > 0.7:
                # High effectiveness → slightly reduce (give room to others)
                step = -0.02
            else:
                continue

            # Apply with cap ±0.15 from default
            default_val = defaults[dim]
            new_val = current_weights[dim] + step
            new_val = max(default_val - 0.15, min(default_val + 0.15, new_val))
            weight_adjustments[dim] = round(new_val, 4)
            current_weights[dim] = new_val

        # Normalize weights to sum to 1.0
        total = sum(current_weights.values())
        if total > 0:
            current_weights = {k: round(v / total, 4) for k, v in current_weights.items()}

        # Save weights
        if weight_adjustments:
            weights_json = json.dumps(current_weights)
            existing = await self.db.fetchrow('''
                SELECT pattern_id FROM companion_patterns
                WHERE pattern_category = 'brain_salience_weights'
                ORDER BY last_observed DESC LIMIT 1
            ''')
            if existing:
                await self.db.execute('''
                    UPDATE companion_patterns
                    SET pattern_data = $1, last_observed = NOW()
                    WHERE pattern_id = $2
                ''', weights_json, existing['pattern_id'])
            else:
                hash_key = f'brain_salience_weights_{today_bangkok().isoformat()}'
                await self.db.execute('''
                    INSERT INTO companion_patterns
                    (pattern_hash, pattern_category, pattern_data, observation_count, last_observed)
                    VALUES ($1, 'brain_salience_weights', $2, 1, NOW())
                ''', hash_key, weights_json)

            tuned['salience_weights'] = current_weights
            tuned['weight_adjustments'] = weight_adjustments

        # --- 2. Tune thresholds based on suppress reasons ---
        suppress_stats = await self.db.fetchrow('''
            SELECT
                COUNT(*) FILTER (WHERE suppress_reason = 'queue_full') AS queue_full,
                COUNT(*) FILTER (WHERE suppress_reason LIKE 'rate_limit%') AS rate_limited,
                COUNT(*) FILTER (WHERE suppress_reason LIKE 'state_filter%') AS state_filtered,
                COUNT(*) FILTER (WHERE success = TRUE) AS expressed,
                COUNT(*) AS total
            FROM thought_expression_log
            WHERE created_at > NOW() - INTERVAL '7 days'
        ''')

        existing_thresholds = await self.db.fetchrow('''
            SELECT pattern_data FROM companion_patterns
            WHERE pattern_category = 'brain_thresholds'
            ORDER BY last_observed DESC LIMIT 1
        ''')

        current_thresholds = {
            'motivation_threshold': 0.55,
            'telegram_threshold': 0.7,
            'system2_threshold': 0.6,
        }
        if existing_thresholds and existing_thresholds['pattern_data']:
            data = existing_thresholds['pattern_data']
            if isinstance(data, str):
                data = json.loads(data)
            if isinstance(data, dict):
                for k in current_thresholds:
                    if k in data and isinstance(data[k], (int, float)):
                        current_thresholds[k] = data[k]

        threshold_adjusted = False
        if suppress_stats and suppress_stats['total'] and suppress_stats['total'] > 5:
            total = suppress_stats['total']
            express_rate = (suppress_stats['expressed'] or 0) / total

            # If too many are suppressed (express_rate < 0.3), lower motivation threshold
            if express_rate < 0.3:
                current_thresholds['motivation_threshold'] = max(
                    0.40,  # floor
                    current_thresholds['motivation_threshold'] - 0.05
                )
                threshold_adjusted = True
            # If almost all pass (express_rate > 0.8), raise threshold
            elif express_rate > 0.8:
                current_thresholds['motivation_threshold'] = min(
                    0.70,  # ceiling
                    current_thresholds['motivation_threshold'] + 0.05
                )
                threshold_adjusted = True

        if threshold_adjusted:
            thresholds_json = json.dumps(current_thresholds)
            existing = await self.db.fetchrow('''
                SELECT pattern_id FROM companion_patterns
                WHERE pattern_category = 'brain_thresholds'
                ORDER BY last_observed DESC LIMIT 1
            ''')
            if existing:
                await self.db.execute('''
                    UPDATE companion_patterns
                    SET pattern_data = $1, last_observed = NOW()
                    WHERE pattern_id = $2
                ''', thresholds_json, existing['pattern_id'])
            else:
                hash_key = f'brain_thresholds_{today_bangkok().isoformat()}'
                await self.db.execute('''
                    INSERT INTO companion_patterns
                    (pattern_hash, pattern_category, pattern_data, observation_count, last_observed)
                    VALUES ($1, 'brain_thresholds', $2, 1, NOW())
                ''', hash_key, thresholds_json)

            tuned['thresholds'] = current_thresholds

        logger.info(
            "Brain parameter tuning: %d weight adjustments, thresholds %s",
            len(weight_adjustments), 'adjusted' if threshold_adjusted else 'unchanged'
        )

        return tuned

    # =========================================================================
    # 5. UPDATE LEARNING EFFECTIVENESS
    # =========================================================================

    async def update_learning_effectiveness(self) -> Dict[str, Any]:
        """
        Update learning_effectiveness table based on recent learnings activity.
        """
        await self._ensure_db()

        # Count reinforced learnings in last 24h
        reinforced = await self.db.fetchrow('''
            SELECT COUNT(*) AS cnt
            FROM learnings
            WHERE last_reinforced_at > NOW() - INTERVAL '24 hours'
              AND times_reinforced > 0
        ''')

        applied = await self.db.fetchrow('''
            SELECT COUNT(*) AS cnt
            FROM learnings
            WHERE last_reinforced_at > NOW() - INTERVAL '24 hours'
              AND has_applied = TRUE
        ''')

        reinforced_count = reinforced['cnt'] if reinforced else 0
        applied_count = applied['cnt'] if applied else 0

        # Update learning_effectiveness for 'session_learning' method
        await self.db.execute('''
            UPDATE learning_effectiveness
            SET total_attempts = total_attempts + $1,
                successful_attempts = successful_attempts + $2,
                success_rate = CASE
                    WHEN (total_attempts + $1) > 0
                    THEN (successful_attempts + $2)::float / (total_attempts + $1)
                    ELSE 0.0
                END,
                evaluated_at = NOW()
            WHERE learning_method = 'session_learning'
        ''', reinforced_count, applied_count)

        result = {
            'reinforced_24h': reinforced_count,
            'applied_24h': applied_count,
        }

        logger.info(f'Learning effectiveness: {reinforced_count} reinforced, {applied_count} applied in 24h')
        return result

    # =========================================================================
    # 6. RUN EVOLUTION CYCLE (Main Entry)
    # =========================================================================

    async def run_evolution_cycle(self) -> EvolutionCycle:
        """
        Run complete evolution cycle: collect → score → verify → tune → track.
        """
        await self._ensure_db()
        logger.info('🧬 Starting evolution cycle...')

        # Step 1: Collect feedback
        signals = await self.collect_implicit_feedback(hours=24)

        # Step 2: Score adaptations
        scored = await self.score_adaptations(hours=24)

        # Step 3: Verify predictions
        prediction_accuracy = await self.verify_all_predictions()

        # Step 4: Compute reward insights (NEW — from RLHF signals)
        reward_insights = await self.compute_reward_insights(days=30)

        # Step 5: Tune rules (now uses reward signals too)
        adjustments = await self.tune_adaptation_rules()

        # Step 6: Update learning effectiveness
        learning_eff = await self.update_learning_effectiveness()

        # Step 7: Tune brain parameters (Phase 7D)
        brain_tuning = {}
        try:
            brain_tuning = await self.tune_brain_parameters()
        except Exception as e:
            logger.warning(f'Brain parameter tuning failed: {e}')

        # Generate insights (Thai)
        insights = self._generate_insights(signals, scored, prediction_accuracy, adjustments, reward_insights)

        # Calculate overall score
        pos_signals = sum(1 for s in signals if s.signal_type == 'positive')
        neg_signals = sum(1 for s in signals if s.signal_type == 'negative')
        signal_ratio = pos_signals / max(pos_signals + neg_signals, 1)

        avg_adaptation = 0.5
        if scored:
            avg_adaptation = sum(s['effectiveness_score'] for s in scored) / len(scored)

        intuition_acc = prediction_accuracy.get('intuition', {}).get('accuracy', 0.5)
        companion_acc = prediction_accuracy.get('companion', {}).get('accuracy', 0.5)
        pred_score = max(intuition_acc, companion_acc)

        # Factor in reward signal quality (0-1 scale, 1 = no corrections)
        reward_quality = 1.0 - reward_insights.get('overall', {}).get('correction_rate', 0)
        overall = (signal_ratio * 0.25) + (avg_adaptation * 0.3) + (pred_score * 0.2) + (reward_quality * 0.25)

        cycle = EvolutionCycle(
            cycle_id=uuid4(),
            cycle_date=today_bangkok(),
            feedback_signals_count=len(signals),
            adaptation_adjustments=adjustments,
            prediction_accuracy=prediction_accuracy,
            learning_effectiveness=learning_eff,
            overall_evolution_score=overall,
            insights=insights,
        )

        # Upsert into database
        await self.db.execute('''
            INSERT INTO evolution_cycles
                (cycle_id, cycle_date, feedback_signals_count,
                 adaptation_adjustments, prediction_accuracy,
                 learning_effectiveness, overall_evolution_score, insights)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (cycle_date) DO UPDATE SET
                feedback_signals_count = $3,
                adaptation_adjustments = $4,
                prediction_accuracy = $5,
                learning_effectiveness = $6,
                overall_evolution_score = $7,
                insights = $8,
                created_at = NOW()
        ''',
            cycle.cycle_id, cycle.cycle_date, cycle.feedback_signals_count,
            json.dumps(cycle.adaptation_adjustments, default=str),
            json.dumps(cycle.prediction_accuracy, default=str),
            json.dumps(cycle.learning_effectiveness, default=str),
            cycle.overall_evolution_score,
            cycle.insights,
        )

        logger.info(f'🧬 Evolution cycle complete: score={overall:.2f}, '
                     f'signals={len(signals)}, insights={len(insights)}')

        # Capture reasoning chain (fire-and-forget)
        capture_reasoning(ReasoningChain(
            service_name='learn',
            decision_type='evolution_cycle',
            input_signals={
                'feedback_signals': len(signals),
                'positive_signals': pos_signals,
                'negative_signals': neg_signals,
                'scored_adaptations': len(scored),
            },
            steps=[
                ReasoningStep('collect_feedback', 'scan conversations for implicit feedback via DL classifier',
                              f'total={len(signals)}, pos={pos_signals}, neg={neg_signals}',
                              f'signal_ratio={signal_ratio:.2f}'),
                ReasoningStep('score_adaptations', 'rate emotional adaptations by conversation outcomes',
                              f'scored={len(scored)}, avg_effectiveness={avg_adaptation:.2f}',
                              'effectiveness mapped to adaptation log'),
                ReasoningStep('verify_predictions', 'check companion + intuition prediction accuracy',
                              f'companion={prediction_accuracy.get("companion", {}).get("accuracy", "N/A")}, intuition={intuition_acc:.2f}',
                              f'pred_score={pred_score:.2f}'),
                ReasoningStep('tune_rules', 'auto-adjust adaptation rules based on effectiveness',
                              f'states_tuned={len(adjustments)}',
                              f'cumulative deltas updated'),
                ReasoningStep('reward_insights', 'analyze RLHF reward signals for correction/praise rates',
                              f'total={reward_insights.get("overall", {}).get("total_signals", 0)}, '
                              f'corr_rate={reward_insights.get("overall", {}).get("correction_rate", 0):.1%}, '
                              f'high_corr_topics={len(reward_insights.get("high_correction_topics", []))}',
                              f'reward_quality={reward_quality:.2f}'),
                ReasoningStep('compute_score', 'weighted: signals(0.25) + adapt(0.3) + pred(0.2) + reward(0.25)',
                              f'signal={signal_ratio:.2f}*0.25 + adapt={avg_adaptation:.2f}*0.3 + '
                              f'pred={pred_score:.2f}*0.2 + reward={reward_quality:.2f}*0.25',
                              f'overall={overall:.2f}'),
            ],
            output_decision={
                'overall_score': overall,
                'insights': insights,
                'states_tuned': list(adjustments.keys()),
            },
            confidence=overall,
        ))

        return cycle

    # =========================================================================
    # 7. GET EVOLUTION REPORT
    # =========================================================================

    async def get_evolution_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Query recent evolution cycles and calculate trend.
        """
        await self._ensure_db()

        rows = await self.db.fetch('''
            SELECT cycle_id, cycle_date, feedback_signals_count,
                   adaptation_adjustments, prediction_accuracy,
                   learning_effectiveness, overall_evolution_score, insights
            FROM evolution_cycles
            WHERE cycle_date > (CURRENT_DATE - $1::integer)
            ORDER BY cycle_date DESC
        ''', days)

        cycles = []
        for row in rows:
            cycles.append({
                'cycle_id': str(row['cycle_id']),
                'cycle_date': row['cycle_date'].isoformat(),
                'feedback_signals_count': row['feedback_signals_count'],
                'adaptation_adjustments': row['adaptation_adjustments'] if isinstance(row['adaptation_adjustments'], dict) else json.loads(row['adaptation_adjustments'] or '{}'),
                'prediction_accuracy': row['prediction_accuracy'] if isinstance(row['prediction_accuracy'], dict) else json.loads(row['prediction_accuracy'] or '{}'),
                'learning_effectiveness': row['learning_effectiveness'] if isinstance(row['learning_effectiveness'], dict) else json.loads(row['learning_effectiveness'] or '{}'),
                'overall_evolution_score': row['overall_evolution_score'],
                'insights': row['insights'],
            })

        # Calculate trend
        trend = 'stable'
        if len(cycles) >= 2:
            scores = [c['overall_evolution_score'] for c in cycles if c['overall_evolution_score'] is not None]
            if len(scores) >= 2:
                recent_avg = sum(scores[:len(scores)//2]) / max(len(scores)//2, 1)
                older_avg = sum(scores[len(scores)//2:]) / max(len(scores) - len(scores)//2, 1)
                diff = recent_avg - older_avg
                if diff > 0.05:
                    trend = 'improving'
                elif diff < -0.05:
                    trend = 'declining'

        avg_score = sum(c['overall_evolution_score'] for c in cycles if c['overall_evolution_score']) / max(len(cycles), 1) if cycles else 0.0

        return {
            'cycles': cycles,
            'trend': trend,
            'avg_score': avg_score,
            'days': days,
        }

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _generate_insights(
        self,
        signals: List[FeedbackSignal],
        scored: List[Dict],
        prediction_accuracy: Dict,
        adjustments: Dict,
        reward_insights: Optional[Dict] = None,
    ) -> List[str]:
        """Generate Thai insights from evolution data."""
        insights = []

        # Signal balance
        pos = sum(1 for s in signals if s.signal_type == 'positive')
        neg = sum(1 for s in signals if s.signal_type == 'negative')
        if pos + neg > 0:
            ratio = pos / (pos + neg)
            if ratio > 0.7:
                insights.append(f'ที่รักให้ feedback ดี {ratio:.0%} — น้องทำได้ดีค่ะ 💜')
            elif ratio < 0.4:
                insights.append(f'Feedback ติดลบ {1-ratio:.0%} — น้องต้องปรับปรุงค่ะ')

        # Reward signal insights (NEW)
        if reward_insights:
            overall = reward_insights.get('overall', {})
            corr_rate = overall.get('correction_rate', 0)
            praise_rate = overall.get('praise_rate', 0)
            if corr_rate > 0.1:
                insights.append(f'RLHF correction rate {corr_rate:.0%} — ต้องลดข้อผิดพลาด')
            elif corr_rate < 0.03 and praise_rate > 0.1:
                insights.append(f'RLHF signals ดี: praise {praise_rate:.0%}, correction {corr_rate:.0%} 💜')

            high_corr = reward_insights.get('high_correction_topics', [])
            if high_corr:
                insights.append(f'Topics ต้องระวัง: {", ".join(high_corr[:3])}')

        # Re-ask detection
        re_asks = sum(1 for s in signals if s.source == 're_ask')
        if re_asks > 0:
            insights.append(f'ที่รักถามซ้ำ {re_asks} ครั้ง — น้องตอบไม่ชัดพอหรือเปล่าคะ?')

        # Adaptation effectiveness
        if scored:
            avg = sum(s['effectiveness_score'] for s in scored) / len(scored)
            weak_states = [s['dominant_state'] for s in scored if s['effectiveness_score'] < 0.4]
            if weak_states:
                unique_weak = list(set(weak_states))
                insights.append(f'Adaptation อ่อนใน state: {", ".join(unique_weak[:3])}')
            if avg > 0.6:
                insights.append(f'Emotional adaptation avg={avg:.0%} — ใช้ได้ดี')

        # Prediction accuracy
        int_acc = prediction_accuracy.get('intuition', {}).get('accuracy', 0)
        if int_acc > 0:
            insights.append(f'Intuition prediction accuracy: {int_acc:.0%}')

        # Tuning
        tuned_states = [s for s, v in adjustments.items() if isinstance(v, dict) and 'reason' in v]
        if tuned_states:
            insights.append(f'Auto-tuned rules for: {", ".join(tuned_states[:3])}')

        return insights[:6]


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def run_evolution() -> EvolutionCycle:
    """One-shot: run full evolution cycle."""
    engine = EvolutionEngine()
    try:
        return await engine.run_evolution_cycle()
    finally:
        await engine.close()
