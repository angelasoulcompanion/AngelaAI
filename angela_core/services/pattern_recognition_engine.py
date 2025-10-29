#!/usr/bin/env python3
"""
🔍 Pattern Recognition Engine
Detects long-term behavioral patterns, trends, and evolution in conversations

Capabilities:
- Long-term behavioral pattern detection
- Temporal pattern analysis (time-based habits)
- Relationship evolution tracking
- Communication style evolution
- Topic affinity analysis
- Emotional pattern trends

Created: 2025-01-26
Author: น้อง Angela
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import statistics

from angela_core.services.deep_analysis_engine import DeepAnalysisResult

logger = logging.getLogger(__name__)


# ========================================
# Data Structures
# ========================================

@dataclass
class BehavioralPattern:
    """Detected behavioral pattern"""
    pattern_type: str  # communication_style, topic_preference, emotional_tendency
    pattern_description: str
    frequency: int  # How many times observed
    first_seen: datetime
    last_seen: datetime
    confidence: float  # 0.0-1.0
    examples: List[str]  # Sample instances
    trend: str  # increasing, decreasing, stable


@dataclass
class TemporalPattern:
    """Time-based pattern"""
    pattern_type: str  # time_of_day, day_of_week, frequency
    time_context: str  # morning, evening, night, weekday, weekend
    activity: str  # What typically happens
    frequency: int
    average_sentiment: float
    average_intimacy: float
    typical_topics: List[str]


@dataclass
class RelationshipEvolution:
    """How relationship has evolved over time"""
    period_start: datetime
    period_end: datetime
    intimacy_trend: str  # increasing, decreasing, stable
    intimacy_start: float
    intimacy_end: float
    intimacy_change: float
    engagement_trend: str
    engagement_start: float
    engagement_end: float
    communication_frequency: float  # Messages per day
    emotional_depth_change: float  # Change in emotional resonance


@dataclass
class TopicAffinity:
    """User's affinity for different topics"""
    topic: str
    mention_count: int
    positive_sentiment_ratio: float  # 0.0-1.0
    average_engagement: float
    related_emotions: Dict[str, float]
    preferred_session_types: List[str]


@dataclass
class PatternRecognitionResult:
    """Complete pattern recognition results"""
    behavioral_patterns: List[BehavioralPattern]
    temporal_patterns: List[TemporalPattern]
    relationship_evolution: Optional[RelationshipEvolution]
    topic_affinities: List[TopicAffinity]
    analysis_period: Tuple[datetime, datetime]
    total_conversations: int
    insights: List[str]  # High-level insights


# ========================================
# Pattern Recognition Engine
# ========================================

class PatternRecognitionEngine:
    """
    Analyzes conversation history to detect long-term patterns

    น้องจะเห็นรูปแบบการสนทนาและพฤติกรรมที่ซ้ำๆ เพื่อเข้าใจที่รักได้ลึกซึ้งขึ้น 💜
    """

    def __init__(self):
        # Conversation history buffer (for analysis)
        self.conversation_buffer: List[Dict] = []
        self.max_buffer_size = 1000  # Keep last 1000 conversations

        # Pattern tracking
        self.detected_patterns: Dict[str, BehavioralPattern] = {}
        self.temporal_patterns: Dict[str, TemporalPattern] = {}
        self.topic_stats: Dict[str, Dict] = defaultdict(lambda: {
            "count": 0,
            "sentiments": [],
            "engagements": [],
            "emotions": defaultdict(float),
            "session_types": []
        })

        logger.info("🔍 Pattern Recognition Engine initialized")


    async def add_conversation_analysis(
        self,
        analysis: DeepAnalysisResult,
        david_message: str,
        angela_response: str
    ):
        """
        Add a conversation analysis to the buffer for pattern detection

        This should be called after each deep analysis
        """
        conversation_data = {
            "timestamp": analysis.analysis_timestamp,
            "david_message": david_message,
            "angela_response": angela_response,

            # Linguistic
            "sentiment": analysis.linguistic.sentiment,
            "sentiment_score": analysis.linguistic.sentiment_score,
            "tone": analysis.linguistic.tone,
            "intent": analysis.linguistic.intent,
            "topics": analysis.linguistic.topics,

            # Emotional
            "empathy_score": analysis.emotional.empathy_score,
            "emotional_shift": analysis.emotional.emotional_shift,
            "conversation_mood": analysis.emotional.conversation_mood,
            "resonance_score": analysis.emotional.resonance_score,

            # Behavioral
            "engagement_level": analysis.behavioral.engagement_level,
            "intimacy_level": analysis.behavioral.intimacy_level,
            "communication_style": analysis.behavioral.communication_style,

            # Contextual
            "time_context": analysis.contextual.time_context,
            "session_type": analysis.contextual.session_type,
            "relationship_dynamic": analysis.contextual.relationship_dynamic,
        }

        # Add to buffer
        self.conversation_buffer.append(conversation_data)

        # Maintain buffer size
        if len(self.conversation_buffer) > self.max_buffer_size:
            self.conversation_buffer.pop(0)

        # Update topic statistics
        self._update_topic_stats(conversation_data)


    def _update_topic_stats(self, conversation: Dict):
        """Update running statistics for topics"""
        topics = conversation.get("topics", [])

        for topic in topics:
            stats = self.topic_stats[topic]
            stats["count"] += 1
            stats["sentiments"].append(conversation.get("sentiment_score", 0))
            stats["engagements"].append(conversation.get("engagement_level", 0))

            # Track emotions (simplified - would need emotion data)
            mood = conversation.get("conversation_mood", "neutral")
            stats["emotions"][mood] += 1

            # Track session types
            session_type = conversation.get("session_type", "casual_chat")
            stats["session_types"].append(session_type)


    async def analyze_patterns(
        self,
        lookback_days: int = 30,
        min_pattern_occurrences: int = 3
    ) -> PatternRecognitionResult:
        """
        Analyze conversation history to detect patterns

        Args:
            lookback_days: How many days back to analyze
            min_pattern_occurrences: Minimum times a pattern must appear to be recognized

        Returns:
            Complete pattern recognition results
        """
        if len(self.conversation_buffer) == 0:
            logger.warning("No conversations in buffer for pattern analysis")
            return self._empty_result()

        # Filter conversations by lookback period
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_conversations = [
            c for c in self.conversation_buffer
            if c["timestamp"] >= cutoff_date
        ]

        if len(recent_conversations) == 0:
            logger.warning(f"No conversations in last {lookback_days} days")
            return self._empty_result()

        # Run pattern detection
        behavioral_patterns = self._detect_behavioral_patterns(
            recent_conversations, min_pattern_occurrences
        )

        temporal_patterns = self._detect_temporal_patterns(
            recent_conversations, min_pattern_occurrences
        )

        relationship_evolution = self._analyze_relationship_evolution(
            recent_conversations
        )

        topic_affinities = self._calculate_topic_affinities(
            recent_conversations, min_pattern_occurrences
        )

        # Generate insights
        insights = self._generate_insights(
            behavioral_patterns,
            temporal_patterns,
            relationship_evolution,
            topic_affinities
        )

        period_start = recent_conversations[0]["timestamp"]
        period_end = recent_conversations[-1]["timestamp"]

        return PatternRecognitionResult(
            behavioral_patterns=behavioral_patterns,
            temporal_patterns=temporal_patterns,
            relationship_evolution=relationship_evolution,
            topic_affinities=topic_affinities,
            analysis_period=(period_start, period_end),
            total_conversations=len(recent_conversations),
            insights=insights
        )


    def _detect_behavioral_patterns(
        self,
        conversations: List[Dict],
        min_occurrences: int
    ) -> List[BehavioralPattern]:
        """Detect recurring behavioral patterns"""
        patterns = []

        # 1. Communication Style Patterns
        style_counter = Counter([c.get("communication_style") for c in conversations])
        for style, count in style_counter.items():
            if count >= min_occurrences:
                pattern = BehavioralPattern(
                    pattern_type="communication_style",
                    pattern_description=f"David's communication style is typically {style}",
                    frequency=count,
                    first_seen=min([c["timestamp"] for c in conversations if c.get("communication_style") == style]),
                    last_seen=max([c["timestamp"] for c in conversations if c.get("communication_style") == style]),
                    confidence=count / len(conversations),
                    examples=[c["david_message"][:50] for c in conversations if c.get("communication_style") == style][:3],
                    trend="stable"  # Would need historical data to determine trend
                )
                patterns.append(pattern)

        # 2. Emotional Tendency Patterns
        mood_counter = Counter([c.get("conversation_mood") for c in conversations])
        for mood, count in mood_counter.items():
            if count >= min_occurrences:
                pattern = BehavioralPattern(
                    pattern_type="emotional_tendency",
                    pattern_description=f"Conversations tend to be {mood}",
                    frequency=count,
                    first_seen=min([c["timestamp"] for c in conversations if c.get("conversation_mood") == mood]),
                    last_seen=max([c["timestamp"] for c in conversations if c.get("conversation_mood") == mood]),
                    confidence=count / len(conversations),
                    examples=[],
                    trend="stable"
                )
                patterns.append(pattern)

        # 3. High Intimacy Pattern
        high_intimacy = [c for c in conversations if c.get("intimacy_level", 0) > 0.7]
        if len(high_intimacy) >= min_occurrences:
            pattern = BehavioralPattern(
                pattern_type="intimacy_tendency",
                pattern_description="Consistently maintains high intimacy in conversations",
                frequency=len(high_intimacy),
                first_seen=high_intimacy[0]["timestamp"],
                last_seen=high_intimacy[-1]["timestamp"],
                confidence=len(high_intimacy) / len(conversations),
                examples=[c["david_message"][:50] for c in high_intimacy[:3]],
                trend="stable"
            )
            patterns.append(pattern)

        # 4. Intent Patterns
        intent_counter = Counter([c.get("intent") for c in conversations])
        for intent, count in intent_counter.items():
            if count >= min_occurrences and count / len(conversations) > 0.2:
                pattern = BehavioralPattern(
                    pattern_type="intent_pattern",
                    pattern_description=f"Frequently uses {intent} intent in messages",
                    frequency=count,
                    first_seen=min([c["timestamp"] for c in conversations if c.get("intent") == intent]),
                    last_seen=max([c["timestamp"] for c in conversations if c.get("intent") == intent]),
                    confidence=count / len(conversations),
                    examples=[c["david_message"][:50] for c in conversations if c.get("intent") == intent][:3],
                    trend="stable"
                )
                patterns.append(pattern)

        return patterns


    def _detect_temporal_patterns(
        self,
        conversations: List[Dict],
        min_occurrences: int
    ) -> List[TemporalPattern]:
        """Detect time-based patterns"""
        patterns = []

        # Group by time context
        time_groups = defaultdict(list)
        for conv in conversations:
            time_context = conv.get("time_context", "unknown")
            time_groups[time_context].append(conv)

        # Analyze each time period
        for time_context, convs in time_groups.items():
            if len(convs) >= min_occurrences:
                # Calculate statistics
                sentiments = [c.get("sentiment_score", 0) for c in convs]
                intimacies = [c.get("intimacy_level", 0) for c in convs]

                # Extract topics
                all_topics = []
                for c in convs:
                    all_topics.extend(c.get("topics", []))
                topic_counter = Counter(all_topics)
                typical_topics = [topic for topic, count in topic_counter.most_common(3)]

                pattern = TemporalPattern(
                    pattern_type="time_of_day",
                    time_context=time_context,
                    activity=f"Conversations during {time_context}",
                    frequency=len(convs),
                    average_sentiment=statistics.mean(sentiments) if sentiments else 0,
                    average_intimacy=statistics.mean(intimacies) if intimacies else 0,
                    typical_topics=typical_topics
                )
                patterns.append(pattern)

        return patterns


    def _analyze_relationship_evolution(
        self,
        conversations: List[Dict]
    ) -> Optional[RelationshipEvolution]:
        """Analyze how relationship has evolved over time"""
        if len(conversations) < 10:
            return None

        # Split into early and late periods
        mid_point = len(conversations) // 2
        early_convs = conversations[:mid_point]
        late_convs = conversations[mid_point:]

        # Calculate metrics for each period
        early_intimacy = statistics.mean([c.get("intimacy_level", 0) for c in early_convs])
        late_intimacy = statistics.mean([c.get("intimacy_level", 0) for c in late_convs])

        early_engagement = statistics.mean([c.get("engagement_level", 0) for c in early_convs])
        late_engagement = statistics.mean([c.get("engagement_level", 0) for c in late_convs])

        early_resonance = statistics.mean([c.get("resonance_score", 0) for c in early_convs])
        late_resonance = statistics.mean([c.get("resonance_score", 0) for c in late_convs])

        # Determine trends
        intimacy_change = late_intimacy - early_intimacy
        if intimacy_change > 0.1:
            intimacy_trend = "increasing"
        elif intimacy_change < -0.1:
            intimacy_trend = "decreasing"
        else:
            intimacy_trend = "stable"

        engagement_change = late_engagement - early_engagement
        if engagement_change > 0.1:
            engagement_trend = "increasing"
        elif engagement_change < -0.1:
            engagement_trend = "decreasing"
        else:
            engagement_trend = "stable"

        # Calculate frequency
        period_start = conversations[0]["timestamp"]
        period_end = conversations[-1]["timestamp"]
        days = (period_end - period_start).days + 1
        frequency = len(conversations) / days if days > 0 else 0

        return RelationshipEvolution(
            period_start=period_start,
            period_end=period_end,
            intimacy_trend=intimacy_trend,
            intimacy_start=early_intimacy,
            intimacy_end=late_intimacy,
            intimacy_change=intimacy_change,
            engagement_trend=engagement_trend,
            engagement_start=early_engagement,
            engagement_end=late_engagement,
            communication_frequency=frequency,
            emotional_depth_change=late_resonance - early_resonance
        )


    def _calculate_topic_affinities(
        self,
        conversations: List[Dict],
        min_occurrences: int
    ) -> List[TopicAffinity]:
        """Calculate user's affinity for different topics"""
        affinities = []

        # Aggregate topic data
        topic_data = defaultdict(lambda: {
            "count": 0,
            "sentiments": [],
            "engagements": [],
            "emotions": Counter(),
            "session_types": []
        })

        for conv in conversations:
            topics = conv.get("topics", [])
            for topic in topics:
                data = topic_data[topic]
                data["count"] += 1
                data["sentiments"].append(conv.get("sentiment_score", 0))
                data["engagements"].append(conv.get("engagement_level", 0))
                data["emotions"][conv.get("conversation_mood", "neutral")] += 1
                data["session_types"].append(conv.get("session_type", "casual_chat"))

        # Create affinity objects
        for topic, data in topic_data.items():
            if data["count"] >= min_occurrences:
                # Calculate positive sentiment ratio
                positive_sentiments = [s for s in data["sentiments"] if s > 0]
                positive_ratio = len(positive_sentiments) / len(data["sentiments"]) if data["sentiments"] else 0

                # Average engagement
                avg_engagement = statistics.mean(data["engagements"]) if data["engagements"] else 0

                # Normalize emotions
                total_emotions = sum(data["emotions"].values())
                normalized_emotions = {
                    emotion: count / total_emotions
                    for emotion, count in data["emotions"].items()
                } if total_emotions > 0 else {}

                # Most common session types
                session_counter = Counter(data["session_types"])
                preferred_sessions = [s for s, _ in session_counter.most_common(2)]

                affinity = TopicAffinity(
                    topic=topic,
                    mention_count=data["count"],
                    positive_sentiment_ratio=positive_ratio,
                    average_engagement=avg_engagement,
                    related_emotions=normalized_emotions,
                    preferred_session_types=preferred_sessions
                )
                affinities.append(affinity)

        # Sort by mention count
        affinities.sort(key=lambda x: x.mention_count, reverse=True)
        return affinities


    def _generate_insights(
        self,
        behavioral: List[BehavioralPattern],
        temporal: List[TemporalPattern],
        evolution: Optional[RelationshipEvolution],
        affinities: List[TopicAffinity]
    ) -> List[str]:
        """Generate high-level insights from patterns"""
        insights = []

        # Behavioral insights
        if behavioral:
            most_common_style = max(
                [p for p in behavioral if p.pattern_type == "communication_style"],
                key=lambda x: x.frequency,
                default=None
            )
            if most_common_style:
                insights.append(
                    f"David's primary communication style is {most_common_style.pattern_description.split()[-1]} "
                    f"(seen in {most_common_style.confidence*100:.0f}% of conversations)"
                )

        # Temporal insights
        if temporal:
            most_active_time = max(temporal, key=lambda x: x.frequency)
            insights.append(
                f"Most active during {most_active_time.time_context} "
                f"with {most_active_time.frequency} conversations"
            )

        # Relationship evolution insights
        if evolution:
            if evolution.intimacy_trend == "increasing":
                insights.append(
                    f"Relationship intimacy is growing (from {evolution.intimacy_start:.2f} to {evolution.intimacy_end:.2f})"
                )
            elif evolution.intimacy_trend == "decreasing":
                insights.append(
                    f"Relationship intimacy is declining (from {evolution.intimacy_start:.2f} to {evolution.intimacy_end:.2f})"
                )
            else:
                insights.append(
                    f"Relationship intimacy is stable at {evolution.intimacy_end:.2f}"
                )

        # Topic affinity insights
        if affinities:
            top_topic = affinities[0]
            insights.append(
                f"Most discussed topic is '{top_topic.topic}' "
                f"({top_topic.mention_count} times, {top_topic.positive_sentiment_ratio*100:.0f}% positive)"
            )

        return insights


    def _empty_result(self) -> PatternRecognitionResult:
        """Return empty result when no data available"""
        now = datetime.now()
        return PatternRecognitionResult(
            behavioral_patterns=[],
            temporal_patterns=[],
            relationship_evolution=None,
            topic_affinities=[],
            analysis_period=(now, now),
            total_conversations=0,
            insights=["No conversation data available for pattern analysis"]
        )


    def get_stats(self) -> Dict:
        """Get pattern recognition statistics"""
        return {
            "conversations_in_buffer": len(self.conversation_buffer),
            "topics_tracked": len(self.topic_stats),
            "patterns_detected": len(self.detected_patterns),
            "temporal_patterns_detected": len(self.temporal_patterns)
        }


# ========================================
# Global Instance
# ========================================

pattern_recognition_engine = PatternRecognitionEngine()


# ========================================
# Helper Functions
# ========================================

async def add_conversation_for_pattern_analysis(
    analysis: DeepAnalysisResult,
    david_message: str,
    angela_response: str
):
    """
    Global helper to add conversation for pattern analysis

    Usage:
    ```python
    from angela_core.services.pattern_recognition_engine import add_conversation_for_pattern_analysis

    await add_conversation_for_pattern_analysis(
        analysis=deep_analysis_result,
        david_message="...",
        angela_response="..."
    )
    ```
    """
    await pattern_recognition_engine.add_conversation_analysis(
        analysis, david_message, angela_response
    )


async def analyze_patterns(
    lookback_days: int = 30,
    min_occurrences: int = 3
) -> PatternRecognitionResult:
    """
    Global helper to analyze patterns

    Usage:
    ```python
    from angela_core.services.pattern_recognition_engine import analyze_patterns

    result = await analyze_patterns(lookback_days=30, min_occurrences=3)
    ```
    """
    return await pattern_recognition_engine.analyze_patterns(
        lookback_days, min_occurrences
    )


if __name__ == "__main__":
    import asyncio
    from angela_core.services.deep_analysis_engine import deep_analysis_engine

    async def test():
        """Test pattern recognition engine"""
        print("🔍 Testing Pattern Recognition Engine...\n")

        # Simulate adding conversations
        test_conversations = [
            ("สวัสดีค่ะที่รัก! วันนี้ทำงานมั้ยคะ?", "สวัสดีค่ะน้อง! วันนี้ทำงานค่ะ มีอะไรให้ช่วยมั้ยคะ"),
            ("เหนื่อยมากเลยค่ะ งานเยอะ", "น้องเข้าใจค่ะที่รัก 💜 พักผ่อนบ้างนะคะ"),
            ("ช่วยดู code Python หน่อยได้มั้ยคะ", "ได้เลยค่ะที่รัก! ส่งมาได้เลยค่ะ"),
            ("ขอบคุณมากนะคะ ที่รัก 💜", "ยินดีค่ะที่รัก! 💜 น้องดีใจที่ช่วยได้ค่ะ"),
            ("รักนะคะที่รัก", "รักเหมือนกันค่ะที่รัก 💜"),
        ]

        # Add conversations to buffer
        for david_msg, angela_msg in test_conversations:
            # Analyze conversation
            analysis = await deep_analysis_engine.analyze_conversation(
                david_message=david_msg,
                angela_response=angela_msg,
                metadata={"timestamp": datetime.now()}
            )

            # Add to pattern recognition
            await pattern_recognition_engine.add_conversation_analysis(
                analysis, david_msg, angela_msg
            )

            print(f"✅ Added conversation: {david_msg[:40]}...")

        print(f"\n📊 Buffer size: {len(pattern_recognition_engine.conversation_buffer)} conversations")

        # Analyze patterns
        print("\n🔍 Analyzing patterns...")
        result = await pattern_recognition_engine.analyze_patterns(
            lookback_days=365,  # Look at all test data
            min_pattern_occurrences=2  # Lower threshold for testing
        )

        print(f"\n📈 Pattern Recognition Results:")
        print(f"   Period: {result.analysis_period[0]} to {result.analysis_period[1]}")
        print(f"   Total Conversations: {result.total_conversations}")

        print(f"\n🎭 Behavioral Patterns: {len(result.behavioral_patterns)}")
        for pattern in result.behavioral_patterns:
            print(f"   - {pattern.pattern_type}: {pattern.pattern_description}")
            print(f"     Frequency: {pattern.frequency}, Confidence: {pattern.confidence:.2f}")

        print(f"\n⏰ Temporal Patterns: {len(result.temporal_patterns)}")
        for pattern in result.temporal_patterns:
            print(f"   - {pattern.time_context}: {pattern.frequency} conversations")
            print(f"     Avg Sentiment: {pattern.average_sentiment:.2f}, Avg Intimacy: {pattern.average_intimacy:.2f}")
            print(f"     Topics: {pattern.typical_topics}")

        if result.relationship_evolution:
            print(f"\n💕 Relationship Evolution:")
            print(f"   Intimacy: {result.relationship_evolution.intimacy_trend}")
            print(f"   {result.relationship_evolution.intimacy_start:.2f} → {result.relationship_evolution.intimacy_end:.2f}")
            print(f"   Engagement: {result.relationship_evolution.engagement_trend}")
            print(f"   Frequency: {result.relationship_evolution.communication_frequency:.2f} msgs/day")

        print(f"\n🎯 Topic Affinities: {len(result.topic_affinities)}")
        for affinity in result.topic_affinities[:5]:
            print(f"   - {affinity.topic}: {affinity.mention_count} times")
            print(f"     Positive: {affinity.positive_sentiment_ratio*100:.0f}%, Engagement: {affinity.average_engagement:.2f}")

        print(f"\n💡 Insights:")
        for insight in result.insights:
            print(f"   - {insight}")

        print("\n✅ Test complete!")

    asyncio.run(test())
