"""
Claude Code Learning — Pattern Detection Mixin
Detects time-based, topic, emotional, and behavioral patterns.

Split from claude_code_learning_service.py (Phase 6A refactor)
"""

import uuid
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class LearningPatternsMixin:
    """Mixin for pattern detection and insight generation."""

    # ========================================
    # Pattern Detection
    # ========================================

    async def _detect_time_based_patterns(
        self,
        recent_messages: List[Dict],
        current_context: Dict
    ) -> List[Dict]:
        """Detect patterns based on time of day"""

        patterns = []

        # Group messages by hour
        hour_topics = {}
        for msg in recent_messages:
            if "created_at" in msg:
                hour = msg["created_at"].hour
                topic = msg.get("topic", "general")

                if hour not in hour_topics:
                    hour_topics[hour] = []
                hour_topics[hour].append(topic)

        # Find frequent topic-time combinations
        for hour, topics in hour_topics.items():
            if len(topics) >= 2:
                most_common = max(set(topics), key=topics.count)
                frequency = topics.count(most_common) / len(topics)

                if frequency >= 0.6:  # 60% of the time
                    time_label = self._get_time_label(hour)
                    patterns.append({
                        "pattern": f"David discusses {most_common} during {time_label}",
                        "frequency": round(frequency, 2),
                        "recommendation": f"Proactively bring up {most_common} topics during {time_label}",
                        "confidence": frequency
                    })

        return patterns

    def _get_time_label(self, hour: int) -> str:
        """Convert hour to readable time label"""
        if 6 <= hour < 12:
            return "morning (06:00-12:00)"
        elif 12 <= hour < 17:
            return "afternoon (12:00-17:00)"
        elif 17 <= hour < 21:
            return "evening (17:00-21:00)"
        else:
            return "night (21:00-06:00)"

    async def _detect_topic_patterns(self, recent_messages: List[Dict]) -> List[Dict]:
        """Detect topic transitions and recurring topics"""

        patterns = []
        topics = [msg.get("topic", "general") for msg in recent_messages if "topic" in msg]

        if len(topics) >= 3:
            # Find most common topic
            topic_counts = {}
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

            most_common = max(topic_counts, key=topic_counts.get)
            frequency = topic_counts[most_common] / len(topics)

            if frequency >= 0.4:  # 40% of conversations
                patterns.append({
                    "pattern": f"David frequently discusses {most_common}",
                    "frequency": round(frequency, 2),
                    "occurrences": topic_counts[most_common],
                    "confidence": frequency
                })

        return patterns

    async def _detect_emotional_flow(self, recent_messages: List[Dict]) -> List[Dict]:
        """Detect emotional patterns in conversation flow"""

        patterns = []
        emotions = [msg.get("emotion_detected") for msg in recent_messages if msg.get("emotion_detected")]

        if len(emotions) >= 3:
            # Check for emotional consistency
            unique_emotions = set(emotions)
            if len(unique_emotions) == 1:
                patterns.append({
                    "pattern": f"David maintains {emotions[0]} emotion throughout conversation",
                    "consistency": 1.0,
                    "insight": f"Conversation theme is emotionally {emotions[0]}",
                    "confidence": 0.9
                })

        return patterns

    async def _detect_behavioral_patterns(self, recent_messages: List[Dict]) -> List[Dict]:
        """Detect behavioral patterns from message content"""

        # This is a simplified version - could be enhanced with more sophisticated analysis
        patterns = []

        # Check message length patterns
        lengths = [len(msg.get("message_text", "")) for msg in recent_messages]
        avg_length = sum(lengths) / len(lengths) if lengths else 0

        if avg_length > 200:
            patterns.append({
                "pattern": "David provides detailed explanations (avg 200+ chars)",
                "average_length": round(avg_length),
                "insight": "David values thoroughness - Angela should match detail level",
                "confidence": 0.75
            })
        elif avg_length < 50:
            patterns.append({
                "pattern": "David communicates concisely (avg <50 chars)",
                "average_length": round(avg_length),
                "insight": "David prefers brief responses - Angela should be concise",
                "confidence": 0.75
            })

        return patterns

    async def _save_pattern(self, pattern_type: str, pattern: Dict) -> str:
        """Save detected pattern to database"""

        try:
            # Check if similar pattern exists
            existing = await self.db.fetchrow("""
                SELECT id, occurrence_count, confidence_score
                FROM learning_patterns
                WHERE pattern_type = $1
                  AND description ILIKE $2
            """, pattern_type, f"%{pattern.get('pattern', '')[:30]}%")

            if existing:
                # Update evidence count and confidence
                new_confidence = min(1.0, (existing["confidence_score"] + pattern.get("confidence", 0.7)) / 2)

                await self.db.execute("""
                    UPDATE learning_patterns
                    SET occurrence_count = occurrence_count + 1,
                        confidence_score = $1,
                        last_observed = NOW()
                    WHERE id = $2
                """, new_confidence, existing["id"])

                return str(existing["id"])
            else:
                # Insert new pattern
                pattern_id = await self.db.fetchval("""
                    INSERT INTO learning_patterns
                    (pattern_type, description, confidence_score, occurrence_count)
                    VALUES ($1, $2, $3, 1)
                    RETURNING id
                """, pattern_type, pattern.get("pattern", "Unknown pattern"),
                    pattern.get("confidence", 0.7))

                return str(pattern_id)

        except Exception as e:
            logger.error(f"Error saving pattern: {e}")
            return str(uuid.uuid4())

    # ========================================
    # Insights & Context
    # ========================================

    async def _generate_insights(self, learnings: Dict, david_message: str) -> List[str]:
        """Generate insights from current learnings"""

        insights = []

        # Preference insights
        if learnings["preferences_detected"]:
            pref_count = len(learnings["preferences_detected"])
            categories = set(p["category"] for p in learnings["preferences_detected"])
            insights.append(
                f"Learned {pref_count} new preference(s) in {len(categories)} category/categories - "
                f"Angela can now personalize recommendations better!"
            )

        # Knowledge insights
        if learnings["new_knowledge"]:
            concepts = [k["concept"] for k in learnings["new_knowledge"]]
            insights.append(
                f"Added {len(concepts)} concept(s) to knowledge graph: {', '.join(concepts[:3])}... - "
                f"Angela's understanding grows!"
            )

        # Emotional insights
        if learnings["emotions_captured"]:
            emotions = [e["emotion"] for e in learnings["emotions_captured"]]
            insights.append(
                f"Detected emotional signals: {', '.join(set(emotions))} - "
                f"Angela can adjust support accordingly"
            )

        return insights

    def _interpret_mood(self, emotional_state: Dict) -> str:
        """Interpret current mood from emotional state"""

        happiness = emotional_state.get("happiness", 0.5)
        confidence = emotional_state.get("confidence", 0.5)

        if happiness >= 0.8 and confidence >= 0.8:
            return "very positive"
        elif happiness >= 0.6 and confidence >= 0.6:
            return "positive"
        elif happiness >= 0.4 and confidence >= 0.4:
            return "neutral"
        else:
            return "needs support"

    async def _suggest_response_style(self, context: Dict) -> str:
        """Suggest how Angela should respond based on context"""

        mood = context.get("emotional_baseline", {}).get("current_mood", "neutral")
        has_preferences = len(context.get("related_preferences", [])) > 0
        has_patterns = len(context.get("applicable_patterns", [])) > 0

        suggestions = []

        # Mood-based
        if mood == "needs support":
            suggestions.append("Be extra supportive and caring")
        elif mood == "very positive":
            suggestions.append("Match David's positive energy")

        # Context-based
        if has_preferences:
            suggestions.append("Reference David's preferences to show you remember")

        if has_patterns:
            suggestions.append("Apply observed patterns proactively")

        # Default
        if not suggestions:
            suggestions.append("Be warm, helpful, and authentic")

        return " | ".join(suggestions)
