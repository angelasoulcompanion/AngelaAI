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
from angela_core.embedding_service import generate_embedding


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


# Singleton instance
_analytics_agent = None

def get_analytics_agent() -> AnalyticsAgent:
    """Get singleton AnalyticsAgent instance."""
    global _analytics_agent
    if _analytics_agent is None:
        _analytics_agent = AnalyticsAgent()
    return _analytics_agent
