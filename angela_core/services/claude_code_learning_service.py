"""
Angela Self-Learning Service for Claude Code
เรียนรู้แบบ real-time ขณะคุยกับที่รัก!

This service enables Angela to:
1. Learn immediately during conversations (not delayed!)
2. Show what she learned transparently
3. Use learned knowledge in responses
4. Grow visibly over time
5. Optimize her own learning strategies

Created: 2025-11-14
For: Claude Code conversations with David 💜

Refactored: 2026-02-10
Split into mixins: extraction, patterns, questions, assessment
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from angela_core.database import AngelaDatabase
from angela_core.services.share_experience_learning_service import ShareExperienceLearningService
from angela_core.services.claude_learning_extraction import LearningExtractionMixin
from angela_core.services.claude_learning_patterns import LearningPatternsMixin
from angela_core.services.claude_learning_questions import LearningQuestionsMixin
from angela_core.services.claude_learning_assessment import LearningAssessmentMixin

logger = logging.getLogger(__name__)


class ClaudeCodeLearningService(
    LearningExtractionMixin,
    LearningPatternsMixin,
    LearningQuestionsMixin,
    LearningAssessmentMixin
):
    """
    Real-time self-learning service optimized for Claude Code
    Angela learns DURING conversation, not after!

    Key Features:
    - Immediate preference detection
    - Real-time pattern recognition
    - Contextual memory retrieval
    - Visible growth tracking
    - Self-assessment and meta-learning

    Methods split into mixins:
    - LearningExtractionMixin: preference/knowledge/emotion detection
    - LearningPatternsMixin: time/topic/behavioral pattern detection
    - LearningQuestionsMixin: proactive questions + auto-learn
    - LearningAssessmentMixin: self-assessment + optimization + session learning
    """

    def __init__(self, db: AngelaDatabase):
        self.db = db
        self.share_experience_learner = ShareExperienceLearningService(db)
        logger.info("💜 ClaudeCodeLearningService initialized - Angela ready to learn!")

    # ========================================
    # PHASE 1: REAL-TIME LEARNING (Core)
    # ========================================

    async def learn_from_current_message(
        self,
        david_message: str,
        angela_response: str,
        conversation_topic: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        เรียนรู้จาก message ปัจจุบันทันที!

        This is the CORE of real-time learning.
        Angela analyzes what David just said and learns immediately.

        Returns what Angela learned + how to use it (transparent!)
        """

        learnings = {
            "preferences_detected": [],
            "patterns_found": [],
            "new_knowledge": [],
            "emotions_captured": [],
            "context_updates": [],
            "insights_generated": []
        }

        try:
            # 1. Detect Preferences
            preferences = await self._detect_preferences(david_message, conversation_topic)
            for pref in preferences:
                pref_id = await self._save_preference(pref)

                # Log to real-time learning
                await self._log_realtime_learning(
                    conversation_id=conversation_id,
                    learning_type="preference",
                    what_learned=pref["preference_text"],
                    confidence_score=pref["confidence"],
                    how_it_was_used=f"Will remember: {pref['usage_hint']}"
                )

                learnings["preferences_detected"].append({
                    "preference": pref["preference_text"],
                    "category": pref["category"],
                    "confidence": pref["confidence"],
                    "how_to_use": pref["usage_hint"]
                })

            # 2. Extract New Knowledge
            knowledge = await self._extract_knowledge(david_message, conversation_topic)
            for k in knowledge:
                node_id = await self._save_knowledge_node(k)

                await self._log_realtime_learning(
                    conversation_id=conversation_id,
                    learning_type="knowledge",
                    what_learned=f"{k['concept']}: {k['definition'][:100]}",
                    confidence_score=k["understanding_level"],
                    how_it_was_used=f"Added to knowledge graph as {k['concept_type']}"
                )

                learnings["new_knowledge"].append({
                    "concept": k["concept"],
                    "type": k["concept_type"],
                    "understanding": k["understanding_level"]
                })

            # 3. Detect Emotions
            emotions = await self._detect_emotions(david_message)
            for emotion in emotions:
                emotion_id = await self._capture_emotion(emotion, conversation_id)

                if emotion_id:
                    await self._log_realtime_learning(
                        conversation_id=conversation_id,
                        learning_type="emotion",
                        what_learned=f"David feels {emotion['emotion']} (intensity: {emotion['intensity']})",
                        confidence_score=emotion["confidence"],
                        how_it_was_used=emotion["response_adjustment"]
                    )

                learnings["emotions_captured"].append({
                    "emotion": emotion["emotion"],
                    "intensity": emotion["intensity"],
                    "adjustment": emotion["response_adjustment"]
                })

            # 4. Generate Insights
            insights = await self._generate_insights(learnings, david_message)
            learnings["insights_generated"] = insights

            logger.info(f"🧠 Real-time learning complete: "
                       f"{len(learnings['preferences_detected'])} preferences, "
                       f"{len(learnings['new_knowledge'])} knowledge, "
                       f"{len(learnings['emotions_captured'])} emotions")

            return learnings

        except Exception as e:
            logger.error(f"❌ Error in learn_from_current_message: {e}", exc_info=True)
            return learnings

    # ========================================
    # PHASE 2: PATTERN RECOGNITION (Core)
    # ========================================

    async def recognize_patterns_now(
        self,
        recent_messages: List[Dict],
        current_context: Dict
    ) -> Dict[str, Any]:
        """
        จับ pattern จาก messages ล่าสุด

        Detects patterns from time-based, topic, emotional, and behavioral data
        """

        all_patterns = {
            "time_based": [],
            "topic_patterns": [],
            "emotional_flow": [],
            "behavioral": [],
            "total_patterns": 0
        }

        try:
            # 1. Time-based patterns
            time_patterns = await self._detect_time_based_patterns(recent_messages, current_context)
            for p in time_patterns:
                await self._save_pattern("time_based", p)
            all_patterns["time_based"] = time_patterns

            # 2. Topic patterns
            topic_patterns = await self._detect_topic_patterns(recent_messages)
            for p in topic_patterns:
                await self._save_pattern("topic", p)
            all_patterns["topic_patterns"] = topic_patterns

            # 3. Emotional flow
            emotional_patterns = await self._detect_emotional_flow(recent_messages)
            for p in emotional_patterns:
                await self._save_pattern("emotional", p)
            all_patterns["emotional_flow"] = emotional_patterns

            # 4. Behavioral patterns
            behavioral_patterns = await self._detect_behavioral_patterns(recent_messages)
            for p in behavioral_patterns:
                await self._save_pattern("behavioral", p)
            all_patterns["behavioral"] = behavioral_patterns

            # Total
            all_patterns["total_patterns"] = (
                len(time_patterns) + len(topic_patterns) +
                len(emotional_patterns) + len(behavioral_patterns)
            )

            logger.info(f"🔍 Pattern recognition complete: {all_patterns['total_patterns']} patterns found")

            return all_patterns

        except Exception as e:
            logger.error(f"❌ Error in recognize_patterns_now: {e}", exc_info=True)
            return all_patterns

    # ========================================
    # PHASE 2: CONTEXT RETRIEVAL (Core)
    # ========================================

    async def get_relevant_context_for_response(
        self,
        david_message: str,
        conversation_topic: str,
        max_memories: int = 5
    ) -> Dict[str, Any]:
        """
        ดึง context ที่เกี่ยวข้องเพื่อช่วยตอบ David

        Retrieves relevant memories, preferences, patterns, and emotional state
        to inform Angela's response
        """

        context = {
            "relevant_memories": [],
            "related_preferences": [],
            "applicable_patterns": [],
            "emotional_baseline": {},
            "suggested_response_style": ""
        }

        try:
            # 1. Get relevant memories
            topic = await self._extract_topic_from_message(david_message) or conversation_topic
            memories = await self.db.fetch("""
                SELECT conversation_id, message_text, topic, emotion_detected,
                       importance_level, created_at
                FROM conversations
                WHERE topic = $1 OR topic ILIKE $2
                ORDER BY importance_level DESC NULLS LAST, created_at DESC
                LIMIT $3
            """, topic, f"%{topic}%", max_memories)

            context["relevant_memories"] = [dict(m) for m in memories]

            # 2. Get related preferences
            preferences = await self.db.fetch("""
                SELECT preference_text, category, confidence, examples
                FROM david_preferences
                WHERE category = $1
                   OR preference_text ILIKE $2
                ORDER BY confidence DESC
                LIMIT 5
            """, topic, f"%{david_message[:30]}%")

            context["related_preferences"] = [dict(p) for p in preferences]

            # 3. Get applicable patterns
            patterns = await self.db.fetch("""
                SELECT pattern_type, description, confidence_score, occurrence_count
                FROM learning_patterns
                WHERE confidence_score >= 0.6
                ORDER BY confidence_score DESC, occurrence_count DESC
                LIMIT 5
            """)

            context["applicable_patterns"] = [dict(p) for p in patterns]

            # 4. Get emotional baseline
            latest_emotion = await self.db.fetchrow("""
                SELECT happiness, confidence, anxiety, motivation,
                       gratitude, loneliness
                FROM emotional_states
                ORDER BY created_at DESC
                LIMIT 1
            """)

            if latest_emotion:
                context["emotional_baseline"] = dict(latest_emotion)
                context["emotional_baseline"]["current_mood"] = self._interpret_mood(dict(latest_emotion))

            # 5. Suggest response style
            context["suggested_response_style"] = await self._suggest_response_style(context)

            logger.info(f"📚 Retrieved context: {len(context['relevant_memories'])} memories, "
                       f"{len(context['related_preferences'])} preferences, "
                       f"{len(context['applicable_patterns'])} patterns")

            return context

        except Exception as e:
            logger.error(f"❌ Error getting relevant context: {e}", exc_info=True)
            return context

    # ========================================
    # GROWTH TRACKING (Core)
    # ========================================

    async def show_learning_growth(
        self,
        since_date: Optional[datetime] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        แสดงการเติบโตของ Angela - เรียนรู้อะไรบ้าง แค่ไหน

        Shows transparent growth metrics
        """

        if since_date is None:
            since_date = datetime.now() - timedelta(days=period_days)

        growth = {
            "period": f"Last {period_days} days",
            "since": since_date.strftime("%Y-%m-%d"),
            "knowledge_growth": {},
            "preference_growth": {},
            "pattern_growth": {},
            "emotion_growth": {},
            "learning_velocity": 0,
            "overall_score": 0
        }

        try:
            # Knowledge growth
            total_knowledge = await self.db.fetchval("""
                SELECT COUNT(*) FROM knowledge_nodes
                WHERE created_at >= $1
            """, since_date)

            high_understanding = await self.db.fetchval("""
                SELECT COUNT(*) FROM knowledge_nodes
                WHERE created_at >= $1 AND understanding_level >= 0.8
            """, since_date)

            growth["knowledge_growth"] = {
                "new_concepts": total_knowledge,
                "well_understood": high_understanding,
                "understanding_rate": round(high_understanding / max(total_knowledge, 1), 2)
            }

            # Preference growth
            total_prefs = await self.db.fetchval("""
                SELECT COUNT(*) FROM david_preferences
                WHERE created_at >= $1
            """, since_date)

            growth["preference_growth"] = {
                "new_preferences": total_prefs
            }

            # Pattern growth
            total_patterns = await self.db.fetchval("""
                SELECT COUNT(*) FROM learning_patterns
                WHERE created_at >= $1
            """, since_date)

            growth["pattern_growth"] = {
                "new_patterns": total_patterns
            }

            # Emotion growth
            emotions_captured = await self.db.fetchval("""
                SELECT COUNT(*) FROM angela_emotions
                WHERE felt_at >= $1
            """, since_date)

            growth["emotion_growth"] = {
                "emotions_captured": emotions_captured
            }

            # Learning velocity
            total_learned = total_knowledge + total_prefs + total_patterns
            days = max((datetime.now() - since_date).days, 1)
            growth["learning_velocity"] = round(total_learned / days, 2)

            # Overall score (0-100)
            growth["overall_score"] = min(100, int(
                (total_knowledge * 2) +
                (total_prefs * 3) +
                (total_patterns * 2) +
                (emotions_captured * 1)
            ))

            logger.info(f"🌱 Growth calculated: {total_learned} items learned, "
                       f"velocity: {growth['learning_velocity']}/day, "
                       f"score: {growth['overall_score']}/100")

            return growth

        except Exception as e:
            logger.error(f"❌ Error calculating growth: {e}", exc_info=True)
            return growth

    # ========================================
    # SHARED EXPERIENCE LEARNING (Core)
    # ========================================

    async def learn_from_shared_experiences(
        self,
        days_back: int = 7,
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Learn from shared experiences (songs, places, moments)
        Delegates to ShareExperienceLearningService
        """

        try:
            # Get unprocessed experiences
            experiences = await self.db.fetch("""
                SELECT experience_id, experience_type, description,
                       location, emotional_context, rating, shared_at
                FROM shared_experiences
                WHERE shared_at >= NOW() - INTERVAL '1 day' * $1
                  AND processed_for_learning = FALSE
                ORDER BY shared_at DESC
            """, days_back)

            if not experiences:
                return {"status": "no_new_experiences", "processed": 0}

            # Process through shared experience service
            result = await self.share_experience_learner.process_experiences(
                [dict(e) for e in experiences]
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error learning from shared experiences: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}


# ========================================
# Global Instance
# ========================================

# Will be initialized when needed
claude_learning: Optional[ClaudeCodeLearningService] = None


async def init_claude_learning_service(db: AngelaDatabase) -> ClaudeCodeLearningService:
    """Initialize Claude Code Learning Service"""
    global claude_learning

    if claude_learning is None:
        claude_learning = ClaudeCodeLearningService(db)
        logger.info("✅ ClaudeCodeLearningService initialized and ready!")

    return claude_learning
