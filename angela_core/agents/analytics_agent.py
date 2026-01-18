"""
Analytics Agent - Intelligent Memory Routing

Decides where each memory should go based on 7 signals:
1. Success Score
2. Repetition Signal
3. Criticality
4. Pattern Novelty
5. Context Richness
6. Emotional Intensity
7. Urgency

Routes to: Long-term, Procedural, Shock, or Archive
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID, uuid4
import json
import math

from angela_core.database import get_db_connection
# from angela_core.embedding_service import  # REMOVED: Migration 009 generate_embedding


class MemoryTier:
    """Memory tier destinations."""
    LONG_TERM = "long_term"
    PROCEDURAL = "procedural"
    SHOCK = "shock"
    ARCHIVE = "archive"


class AnalyticsAgent:
    """
    Intelligent routing agent using 7-signal analysis.

    Each signal contributes to routing decision:
    - Success Score (35%): Did it work?
    - Repetition Signal (25%): Have we seen this before?
    - Criticality (20%): How important is this?
    - Pattern Novelty (15%): Is this new/interesting?
    - Context Richness (5%): How much detail?
    - Emotional Intensity: Boosts importance
    - Urgency: Affects processing priority
    """

    def __init__(self):
        # Signal weights (sum to 1.0)
        self.weights = {
            'success_score': 0.35,
            'repetition_signal': 0.25,
            'criticality': 0.20,
            'pattern_novelty': 0.15,
            'context_richness': 0.05
        }

        # Thresholds for routing decisions
        self.thresholds = {
            'shock': 0.85,        # >= 0.85 → Shock Memory
            'long_term': 0.60,    # >= 0.60 → Long-term
            'procedural': 0.40,   # >= 0.40 with high repetition → Procedural
            'archive': 0.0        # < 0.40 → Archive (gradual deletion)
        }

    async def analyze_memory(self, event: Dict) -> Dict:
        """
        Analyze event and determine routing decision.

        Args:
            event: Fresh memory event with content, metadata, etc.

        Returns:
            Routing decision with:
            - target_tier: Which memory tier
            - confidence: How confident (0.0-1.0)
            - reasoning: Why this decision
            - signals: All signal values
            - priority: Processing priority (1-10)
        """
        # Extract all 7 signals
        signals = await self._extract_signals(event)

        # Calculate weighted composite score
        composite_score = self._calculate_composite_score(signals)

        # Determine target tier
        target_tier = self._determine_tier(composite_score, signals)

        # Calculate confidence
        confidence = self._calculate_confidence(signals)

        # Generate reasoning
        reasoning = self._generate_reasoning(target_tier, signals, composite_score)

        # Calculate priority
        priority = self._calculate_priority(signals)

        # Log decision to analytics table
        decision_id = await self._log_decision(event, target_tier, signals, composite_score, confidence)

        return {
            'decision_id': decision_id,
            'target_tier': target_tier,
            'confidence': confidence,
            'reasoning': reasoning,
            'signals': signals,
            'composite_score': composite_score,
            'priority': priority,
            'timestamp': datetime.now()
        }

    async def _extract_signals(self, event: Dict) -> Dict:
        """Extract all 7 signals from event."""
        signals = {}

        # 1. Success Score (0.0-1.0)
        signals['success_score'] = await self._calculate_success_score(event)

        # 2. Repetition Signal (0.0-1.0)
        signals['repetition_signal'] = await self._calculate_repetition(event)

        # 3. Criticality (0.0-1.0)
        signals['criticality'] = await self._calculate_criticality(event)

        # 4. Pattern Novelty (0.0-1.0)
        signals['pattern_novelty'] = await self._calculate_novelty(event)

        # 5. Context Richness (0.0-1.0)
        signals['context_richness'] = self._calculate_context_richness(event)

        # 6. Emotional Intensity (0.0-1.0)
        signals['emotional_intensity'] = self._calculate_emotional_intensity(event)

        # 7. Urgency (0.0-1.0)
        signals['urgency'] = self._calculate_urgency(event)

        return signals

    async def _calculate_success_score(self, event: Dict) -> float:
        """
        Calculate success score based on outcome.

        Success indicators:
        - outcome == "success"
        - error_rate < 0.1
        - execution_time < expected
        - user_satisfaction > 0.7
        """
        metadata = event.get('metadata', {})

        score = 0.5  # Neutral baseline

        # Explicit outcome
        if metadata.get('outcome') == 'success':
            score += 0.3
        elif metadata.get('outcome') == 'failure':
            score -= 0.3

        # Error rate
        error_rate = metadata.get('error_rate', 0.0)
        score += (1.0 - error_rate) * 0.2

        # User satisfaction
        satisfaction = metadata.get('user_satisfaction', 0.5)
        score += (satisfaction - 0.5) * 0.3

        return max(0.0, min(1.0, score))

    async def _calculate_repetition(self, event: Dict) -> float:
        """
        Calculate repetition signal by checking similar past events.

        High repetition = should go to Procedural Memory
        Low repetition = novel experience
        """
        content = event.get('content', '')
        embedding = await generate_embedding(content)
        # Convert to PostgreSQL vector format
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'

        async with get_db_connection() as conn:
            # Find similar memories in the past
            # NOTE: Only querying conversations for now (learning_insights table doesn't exist yet)
            similar_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM conversations
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> $1::vector) > 0.8
            """, embedding_str)

            # Convert to 0-1 scale (0 = never seen, 1 = seen 10+ times)
            repetition = min(similar_count / 10.0, 1.0)

            return repetition

    async def _calculate_criticality(self, event: Dict) -> float:
        """
        Calculate criticality based on importance level and impact.

        Critical events:
        - importance_level >= 8
        - affects_system = true
        - user_initiated = true
        - has_consequences = true
        """
        metadata = event.get('metadata', {})

        score = 0.0

        # Importance level (most significant)
        importance = metadata.get('importance_level', 5)
        score += (importance / 10.0) * 0.5

        # System impact
        if metadata.get('affects_system'):
            score += 0.2

        # User initiated (David's direct action)
        if metadata.get('user_initiated'):
            score += 0.2

        # Has consequences
        if metadata.get('has_consequences'):
            score += 0.1

        return min(1.0, score)

    async def _calculate_novelty(self, event: Dict) -> float:
        """
        Calculate pattern novelty - how different is this from what we know?

        High novelty = new pattern, should learn
        Low novelty = already know this pattern
        """
        content = event.get('content', '')
        embedding = await generate_embedding(content)
        # Convert to PostgreSQL vector format
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'

        async with get_db_connection() as conn:
            # Find closest match
            # NOTE: Only querying conversations for now (learning_insights table doesn't exist yet)
            closest_similarity = await conn.fetchval("""
                SELECT MAX(1 - (embedding <=> $1::vector)) as max_similarity
                FROM conversations
                WHERE embedding IS NOT NULL
            """, embedding_str)

            # Novelty is inverse of similarity
            # 0.9 similarity = 0.1 novelty (we've seen this)
            # 0.3 similarity = 0.7 novelty (new pattern!)
            novelty = 1.0 - (closest_similarity or 0.5)

            return novelty

    def _calculate_context_richness(self, event: Dict) -> float:
        """
        Calculate context richness based on metadata completeness.

        Rich context = lots of useful metadata
        Poor context = minimal information
        """
        metadata = event.get('metadata', {})
        content = event.get('content', '')

        score = 0.0

        # Content length (longer = more context)
        if len(content) > 200:
            score += 0.3
        elif len(content) > 100:
            score += 0.2
        elif len(content) > 50:
            score += 0.1

        # Metadata fields present
        useful_fields = ['topic', 'emotion_detected', 'speaker', 'importance_level',
                        'outcome', 'error_rate', 'user_satisfaction']
        present_fields = sum(1 for field in useful_fields if field in metadata)
        score += (present_fields / len(useful_fields)) * 0.5

        # Has speaker attribution
        if event.get('speaker'):
            score += 0.2

        return min(1.0, score)

    def _calculate_emotional_intensity(self, event: Dict) -> float:
        """
        Calculate emotional intensity from emotion_detected field.

        High intensity emotions:
        - love, joy, excitement, gratitude
        - fear, anxiety, sadness, anger

        Low intensity:
        - neutral, calm, content
        """
        emotion = event.get('metadata', {}).get('emotion_detected', '').lower()

        # Emotion intensity map
        high_intensity = ['love', 'joy', 'excitement', 'gratitude', 'fear',
                         'anxiety', 'sadness', 'anger', 'surprise', 'shock']
        medium_intensity = ['happy', 'worried', 'confused', 'curious',
                           'hopeful', 'disappointed']

        if emotion in high_intensity:
            return 0.8
        elif emotion in medium_intensity:
            return 0.5
        else:
            return 0.2

    def _calculate_urgency(self, event: Dict) -> float:
        """
        Calculate urgency - does this need immediate attention?

        Urgent:
        - Real-time conversation
        - System errors
        - Time-sensitive tasks
        """
        metadata = event.get('metadata', {})
        event_type = event.get('event_type', '')

        score = 0.3  # Default low urgency

        # Real-time conversation
        if event_type == 'conversation':
            score = 0.7

        # System errors
        if metadata.get('error_rate', 0) > 0.5:
            score = 0.9

        # Time-sensitive
        if metadata.get('time_sensitive'):
            score = 0.8

        return score

    def _calculate_composite_score(self, signals: Dict) -> float:
        """Calculate weighted composite score from all signals."""
        score = 0.0

        # Weighted sum of main 5 signals
        for signal_name, weight in self.weights.items():
            score += signals.get(signal_name, 0.5) * weight

        # Emotional intensity is a multiplier, not additive
        # High emotion = boost score by up to 20%
        emotion_multiplier = 1.0 + (signals.get('emotional_intensity', 0.2) * 0.2)
        score *= emotion_multiplier

        return min(1.0, score)

    def _determine_tier(self, composite_score: float, signals: Dict) -> str:
        """
        Determine target memory tier based on composite score and signals.

        Decision tree:
        1. If criticality >= 0.8 OR composite >= 0.85 → Shock Memory (critical events)
        2. If repetition > 0.7 AND composite >= 0.40 → Procedural (learned patterns)
        3. If composite >= 0.60 → Long-term (important memories)
        4. Otherwise → Archive (gradual decay)
        """
        # Shock Memory: Critical, high-impact events
        # CRITICAL: Check criticality signal directly for critical failures/alerts
        # Use >= 0.79 to handle floating point precision issues (0.7999... rounds to 0.8)
        if (signals.get('criticality', 0) >= 0.79 or
            composite_score >= self.thresholds['shock']):
            return MemoryTier.SHOCK

        # Procedural Memory: High repetition patterns
        if (signals.get('repetition_signal', 0) > 0.7 and
            composite_score >= self.thresholds['procedural']):
            return MemoryTier.PROCEDURAL

        # Long-term Memory: Important but not critical
        if composite_score >= self.thresholds['long_term']:
            return MemoryTier.LONG_TERM

        # Archive: Low importance, will decay
        return MemoryTier.ARCHIVE

    def _calculate_confidence(self, signals: Dict) -> float:
        """
        Calculate confidence in routing decision.

        High confidence when:
        - Signals are clear (not ambiguous)
        - Multiple signals agree
        - Context is rich
        """
        # Standard deviation of signals (excluding emotion/urgency)
        main_signals = [
            signals.get('success_score', 0.5),
            signals.get('repetition_signal', 0.5),
            signals.get('criticality', 0.5),
            signals.get('pattern_novelty', 0.5),
            signals.get('context_richness', 0.5)
        ]

        mean = sum(main_signals) / len(main_signals)
        variance = sum((x - mean) ** 2 for x in main_signals) / len(main_signals)
        std_dev = math.sqrt(variance)

        # Low std_dev = signals agree = high confidence
        # High std_dev = signals disagree = low confidence
        confidence = 1.0 - min(std_dev * 2, 1.0)

        # Boost confidence if context is rich
        confidence += signals.get('context_richness', 0.2) * 0.2

        return min(1.0, confidence)

    def _generate_reasoning(self, target_tier: str, signals: Dict, composite_score: float) -> str:
        """Generate human-readable reasoning for the decision."""
        reasons = []

        # Primary reason based on tier
        if target_tier == MemoryTier.SHOCK:
            reasons.append(f"Critical event (score: {composite_score:.2f})")
        elif target_tier == MemoryTier.PROCEDURAL:
            reasons.append(f"High repetition pattern (repetition: {signals['repetition_signal']:.2f})")
        elif target_tier == MemoryTier.LONG_TERM:
            reasons.append(f"Important memory (score: {composite_score:.2f})")
        else:
            reasons.append(f"Low importance (score: {composite_score:.2f})")

        # Contributing factors
        if signals.get('success_score', 0.5) > 0.7:
            reasons.append("High success rate")
        if signals.get('criticality', 0.5) > 0.7:
            reasons.append("Critical system impact")
        if signals.get('pattern_novelty', 0.5) > 0.7:
            reasons.append("Novel pattern detected")
        if signals.get('emotional_intensity', 0.2) > 0.7:
            reasons.append("Strong emotional content")

        return ", ".join(reasons)

    def _calculate_priority(self, signals: Dict) -> int:
        """
        Calculate processing priority (1-10).

        Priority affects:
        - How quickly memory is processed
        - Whether it interrupts other tasks
        - Resource allocation
        """
        # Base priority from urgency
        priority = signals.get('urgency', 0.3) * 5

        # Boost from criticality
        priority += signals.get('criticality', 0.5) * 3

        # Boost from emotional intensity
        priority += signals.get('emotional_intensity', 0.2) * 2

        return max(1, min(10, round(priority)))

    async def _log_decision(self, event: Dict, target_tier: str,
                           signals: Dict, composite_score: float, confidence: float) -> UUID:
        """Log routing decision to analytics table for learning/improvement."""
        decision_id = uuid4()

        async with get_db_connection() as conn:
            # Check if event exists in fresh_memory (for foreign key constraint)
            event_id = event.get('id')
            if event_id:
                exists = await conn.fetchval("""
                    SELECT EXISTS(SELECT 1 FROM fresh_memory WHERE id = $1)
                """, event_id)
                if not exists:
                    event_id = None  # Don't link to non-existent event

            await conn.execute("""
                INSERT INTO analytics_decisions (
                    id, event_id, target_tier, composite_score, confidence,
                    signals, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """,
                decision_id,
                event_id,
                target_tier,
                composite_score,
                confidence,
                json.dumps(signals)
            )

        return decision_id


    # =========================================================================
    # FEEDBACK LOOP METHODS (NEW)
    # =========================================================================

    async def record_feedback(
        self,
        decision_id: UUID,
        feedback_score: float,
        feedback_note: str = None
    ) -> bool:
        """
        Record feedback for a routing decision.

        Args:
            decision_id: The decision to provide feedback for
            feedback_score: 0.0 (bad decision) to 1.0 (perfect decision)
            feedback_note: Optional note explaining the feedback

        Returns:
            True if feedback recorded successfully
        """
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE analytics_decisions
                SET feedback_score = $1, feedback_note = $2
                WHERE id = $3
            """, feedback_score, feedback_note, decision_id)

        return True

    async def feedback_loop(
        self,
        event_id: UUID,
        actual_outcome: str,
        was_useful: bool = True
    ) -> Dict:
        """
        Learn from whether routing was correct.

        This method:
        1. Finds the original routing decision
        2. Compares predicted tier with actual usefulness
        3. Adjusts weights based on feedback
        4. Records learning for future improvement

        Args:
            event_id: The event that was routed
            actual_outcome: What actually happened ('used', 'ignored', 'critical', 'unnecessary')
            was_useful: Whether the routing decision was helpful

        Returns:
            Learning result with weight adjustments
        """
        async with get_db_connection() as conn:
            # Find original decision
            decision = await conn.fetchrow("""
                SELECT id, target_tier, composite_score, confidence, signals
                FROM analytics_decisions
                WHERE event_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, event_id)

            if not decision:
                return {'success': False, 'error': 'Decision not found'}

            # Calculate feedback score based on outcome
            outcome_scores = {
                'used': 1.0,       # Memory was used = good routing
                'critical': 1.0,   # Was critical = good to keep
                'ignored': 0.3,    # Was ignored = maybe wrong tier
                'unnecessary': 0.1 # Wasn't needed = bad routing
            }
            feedback_score = outcome_scores.get(actual_outcome, 0.5)

            if not was_useful:
                feedback_score *= 0.5

            # Record feedback
            await self.record_feedback(
                decision['id'],
                feedback_score,
                f"Outcome: {actual_outcome}, useful: {was_useful}"
            )

            # Adjust weights based on feedback pattern
            weight_adjustment = await self._calculate_weight_adjustment(
                decision['signals'],
                decision['target_tier'],
                actual_outcome,
                feedback_score
            )

            # Log learning
            await self._log_learning(
                decision['id'],
                actual_outcome,
                feedback_score,
                weight_adjustment
            )

            return {
                'success': True,
                'decision_id': str(decision['id']),
                'original_tier': decision['target_tier'],
                'feedback_score': feedback_score,
                'weight_adjustment': weight_adjustment
            }

    async def _calculate_weight_adjustment(
        self,
        signals: Dict,
        target_tier: str,
        actual_outcome: str,
        feedback_score: float
    ) -> Dict:
        """
        Calculate how weights should be adjusted based on feedback.

        If routing was wrong:
        - Identify which signals led to wrong decision
        - Suggest weight adjustments

        Returns adjustment suggestions (not applied automatically)
        """
        if isinstance(signals, str):
            signals = json.loads(signals)

        adjustments = {}

        # If feedback is low (bad decision), analyze what went wrong
        if feedback_score < 0.5:
            # Find the dominant signal that may have caused wrong routing
            max_signal = max(signals.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0)

            if max_signal[0] in self.weights:
                # Suggest reducing weight of misleading signal
                adjustments[max_signal[0]] = -0.02  # Reduce by 2%

            # If memory was actually critical but routed to archive
            if actual_outcome == 'critical' and target_tier == MemoryTier.ARCHIVE:
                adjustments['criticality'] = 0.03  # Increase criticality weight

        elif feedback_score > 0.8:
            # Good decision - slightly reinforce the weights
            # (No change needed, system is working well)
            pass

        return adjustments

    async def _log_learning(
        self,
        decision_id: UUID,
        actual_outcome: str,
        feedback_score: float,
        weight_adjustment: Dict
    ) -> None:
        """Log learning event for analysis."""
        async with get_db_connection() as conn:
            # Check if table exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'analytics_learning_log'
                )
            """)

            if not exists:
                await conn.execute("""
                    CREATE TABLE analytics_learning_log (
                        log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        decision_id UUID REFERENCES analytics_decisions(id),
                        actual_outcome VARCHAR(50),
                        feedback_score FLOAT,
                        weight_adjustment JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)

            await conn.execute("""
                INSERT INTO analytics_learning_log
                (decision_id, actual_outcome, feedback_score, weight_adjustment)
                VALUES ($1, $2, $3, $4)
            """,
                decision_id,
                actual_outcome,
                feedback_score,
                json.dumps(weight_adjustment)
            )

    async def get_feedback_summary(self, days: int = 30) -> Dict:
        """
        Get summary of feedback for routing decisions.

        Returns:
            Summary with accuracy, common errors, weight suggestions
        """
        async with get_db_connection() as conn:
            # Overall accuracy
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_decisions,
                    COUNT(feedback_score) as decisions_with_feedback,
                    AVG(feedback_score) as avg_feedback_score,
                    COUNT(CASE WHEN feedback_score >= 0.7 THEN 1 END) as good_decisions,
                    COUNT(CASE WHEN feedback_score < 0.5 THEN 1 END) as poor_decisions
                FROM analytics_decisions
                WHERE created_at > NOW() - INTERVAL '%s days'
            """ % days)

            # Per-tier accuracy
            tier_stats = await conn.fetch("""
                SELECT
                    target_tier,
                    COUNT(*) as count,
                    AVG(feedback_score) as avg_score
                FROM analytics_decisions
                WHERE created_at > NOW() - INTERVAL '%s days'
                AND feedback_score IS NOT NULL
                GROUP BY target_tier
            """ % days)

            return {
                'period_days': days,
                'total_decisions': stats['total_decisions'],
                'with_feedback': stats['decisions_with_feedback'],
                'accuracy': float(stats['avg_feedback_score'] or 0),
                'good_decisions': stats['good_decisions'],
                'poor_decisions': stats['poor_decisions'],
                'per_tier': [
                    {
                        'tier': t['target_tier'],
                        'count': t['count'],
                        'avg_score': float(t['avg_score'] or 0)
                    }
                    for t in tier_stats
                ]
            }

    async def apply_learned_weights(self) -> Dict:
        """
        Apply weight adjustments learned from feedback.

        This analyzes recent feedback and updates weights if there's
        a clear pattern of errors.

        Returns:
            Summary of weight changes applied
        """
        async with get_db_connection() as conn:
            # Get recent learning logs
            learnings = await conn.fetch("""
                SELECT weight_adjustment
                FROM analytics_learning_log
                WHERE created_at > NOW() - INTERVAL '7 days'
                AND weight_adjustment IS NOT NULL
            """)

            if not learnings:
                return {'changes': [], 'message': 'No recent learnings'}

            # Aggregate adjustments
            aggregate_adjustments = {}
            for learning in learnings:
                adj = learning['weight_adjustment']
                if isinstance(adj, str):
                    adj = json.loads(adj)
                for signal, change in adj.items():
                    if signal in aggregate_adjustments:
                        aggregate_adjustments[signal] += change
                    else:
                        aggregate_adjustments[signal] = change

            # Apply adjustments (with limits)
            changes = []
            for signal, total_change in aggregate_adjustments.items():
                if signal in self.weights:
                    old_weight = self.weights[signal]
                    # Limit change to ±5%
                    change = max(-0.05, min(0.05, total_change))
                    # Ensure weight stays between 0.05 and 0.50
                    new_weight = max(0.05, min(0.50, old_weight + change))

                    if new_weight != old_weight:
                        self.weights[signal] = new_weight
                        changes.append({
                            'signal': signal,
                            'old': old_weight,
                            'new': new_weight,
                            'change': new_weight - old_weight
                        })

            return {
                'changes': changes,
                'new_weights': dict(self.weights)
            }


# Singleton instance
_analytics_agent = None

def get_analytics_agent() -> AnalyticsAgent:
    """Get singleton AnalyticsAgent instance."""
    global _analytics_agent
    if _analytics_agent is None:
        _analytics_agent = AnalyticsAgent()
    return _analytics_agent
