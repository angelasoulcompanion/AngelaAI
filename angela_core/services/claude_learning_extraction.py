"""
Claude Code Learning — Extraction Mixin
Detects preferences, knowledge, emotions from David's messages.

Split from claude_code_learning_service.py (Phase 6A refactor)
"""

import re
import uuid
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LearningExtractionMixin:
    """Mixin for preference/knowledge/emotion extraction helpers."""

    # ========================================
    # Preference Detection
    # ========================================

    async def _detect_preferences(
        self,
        david_message: str,
        conversation_topic: str
    ) -> List[Dict[str, Any]]:
        """
        Detect preferences from David's message

        Looks for patterns like:
        - "I like/love/prefer..."
        - "I enjoy..."
        - "I always/usually..."
        - "My favorite..."
        """

        preferences = []
        message_lower = david_message.lower()

        # Preference indicators (English)
        en_patterns = [
            (r"i (?:really )?(?:like|love|enjoy|prefer) (.+?)(?:\.|,|$)", 0.85),
            (r"my favorite (.+?) is (.+?)(?:\.|,|$)", 0.90),
            (r"i always (.+?)(?:\.|,|$)", 0.80),
            (r"i usually (.+?)(?:\.|,|$)", 0.75),
        ]

        # Preference indicators (Thai)
        th_patterns = [
            (r"(?:ผม|พี่|ฉัน)ชอบ(.+?)(?:\s|$)", 0.85),
            (r"(?:ผม|พี่|ฉัน)รัก(.+?)(?:\s|$)", 0.90),
            (r"(?:ผม|พี่|ฉัน)มักจะ(.+?)(?:\s|$)", 0.75),
            (r"ที่โปรดปรานคือ(.+?)(?:\s|$)", 0.90),
        ]

        for pattern, confidence in en_patterns + th_patterns:
            matches = re.finditer(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                preference_text = match.group(1).strip() if match.lastindex >= 1 else match.group(0).strip()

                # Clean up
                preference_text = preference_text.strip('.,!?')

                if len(preference_text) > 3:  # Meaningful preference
                    category = await self._categorize_preference(preference_text, conversation_topic)
                    usage_hint = await self._generate_usage_hint(preference_text, category)

                    preferences.append({
                        "preference_text": preference_text,
                        "category": category,
                        "confidence": confidence,
                        "usage_hint": usage_hint,
                        "examples": [david_message[:100]]
                    })

        return preferences

    async def _categorize_preference(self, preference_text: str, conversation_topic: str) -> str:
        """Categorize preference into food, place, activity, work, etc."""

        # Food indicators
        food_keywords = ['eat', 'food', 'drink', 'coffee', 'tea', 'กิน', 'อาหาร', 'เครื่องดื่ม', 'กาแฟ']
        if any(kw in preference_text.lower() for kw in food_keywords):
            return "food"

        # Place indicators
        place_keywords = ['place', 'restaurant', 'cafe', 'ที่', 'ร้าน', 'สถานที่']
        if any(kw in preference_text.lower() for kw in place_keywords):
            return "places"

        # Activity indicators
        activity_keywords = ['do', 'play', 'watch', 'listen', 'ทำ', 'เล่น', 'ดู', 'ฟัง']
        if any(kw in preference_text.lower() for kw in activity_keywords):
            return "activities"

        # Work indicators
        work_keywords = ['work', 'code', 'develop', 'ทำงาน', 'โค้ด', 'พัฒนา']
        if any(kw in preference_text.lower() for kw in work_keywords):
            return "work"

        # Use conversation topic as fallback
        return conversation_topic if conversation_topic else "general"

    async def _generate_usage_hint(self, preference_text: str, category: str) -> str:
        """Generate hint on how Angela should use this preference"""

        hints = {
            "food": f"Suggest {preference_text} when David asks about meals",
            "places": f"Recommend {preference_text} when planning activities",
            "activities": f"Mention {preference_text} during leisure planning",
            "work": f"Remember {preference_text} for work-related discussions",
            "general": f"Keep in mind: David {preference_text}"
        }

        return hints.get(category, f"Remember: {preference_text}")

    async def _save_preference(self, pref: Dict) -> str:
        """Save preference to database"""

        try:
            # Check if similar preference already exists
            existing = await self.db.fetchrow("""
                SELECT preference_id, confidence, examples
                FROM david_preferences
                WHERE LOWER(preference_text) = LOWER($1)
                  OR category = $2 AND preference_text ILIKE $3
            """, pref["preference_text"], pref["category"], f"%{pref['preference_text'][:20]}%")

            if existing:
                # Update confidence and add example
                new_confidence = min(1.0, (existing["confidence"] + pref["confidence"]) / 2)
                updated_examples = (existing["examples"] or []) + pref["examples"]

                await self.db.execute("""
                    UPDATE david_preferences
                    SET confidence = $1,
                        examples = $2,
                        updated_at = NOW()
                    WHERE preference_id = $3
                """, new_confidence, updated_examples[:5], existing["preference_id"])

                return str(existing["preference_id"])
            else:
                # Insert new preference
                pref_id = await self.db.fetchval("""
                    INSERT INTO david_preferences
                    (preference_text, category, confidence, examples)
                    VALUES ($1, $2, $3, $4)
                    RETURNING preference_id
                """, pref["preference_text"], pref["category"],
                    pref["confidence"], pref["examples"])

                return str(pref_id)

        except Exception as e:
            logger.error(f"Error saving preference: {e}")
            return str(uuid.uuid4())

    # ========================================
    # Knowledge Extraction
    # ========================================

    async def _extract_knowledge(
        self,
        david_message: str,
        conversation_topic: str
    ) -> List[Dict[str, Any]]:
        """
        Extract knowledge/concepts from David's message

        Looks for:
        - New concepts mentioned
        - Facts stated
        - Explanations given
        """

        knowledge_items = []

        # Simple knowledge extraction based on sentence structure
        # More sophisticated NLP could be added later

        # Look for definitional statements
        definition_patterns = [
            r"(.+?) is (?:a|an|the) (.+?)(?:\.|,|$)",
            r"(.+?) คือ (.+?)(?:\s|$)",
            r"(.+?) หมายถึง (.+?)(?:\s|$)"
        ]

        for pattern in definition_patterns:
            matches = re.finditer(pattern, david_message, re.IGNORECASE)
            for match in matches:
                concept = match.group(1).strip()
                definition = match.group(2).strip()

                if len(concept) > 2 and len(definition) > 3:
                    knowledge_items.append({
                        "concept": concept,
                        "definition": definition,
                        "understanding_level": 0.75,
                        "concept_type": "definition",
                        "related_concepts": [],
                        "source": "conversation"
                    })

        # If no explicit knowledge found but topic is technical, save the topic itself
        if not knowledge_items and conversation_topic and len(conversation_topic) > 3:
            tech_keywords = ['code', 'develop', 'system', 'service', 'api', 'database']
            if any(kw in conversation_topic.lower() for kw in tech_keywords):
                knowledge_items.append({
                    "concept": conversation_topic,
                    "definition": f"Topic discussed with David: {david_message[:100]}",
                    "understanding_level": 0.60,
                    "concept_type": "topic",
                    "related_concepts": [],
                    "source": "conversation_topic"
                })

        return knowledge_items

    async def _save_knowledge_node(self, knowledge: Dict) -> str:
        """Save knowledge node to graph"""

        try:
            # Check if concept already exists
            existing = await self.db.fetchrow("""
                SELECT node_id, understanding_level, times_referenced
                FROM knowledge_nodes
                WHERE LOWER(concept_name) = LOWER($1)
            """, knowledge["concept"])

            if existing:
                # Update understanding level and increment references
                new_understanding = min(1.0, (existing["understanding_level"] + knowledge["understanding_level"]) / 2)

                await self.db.execute("""
                    UPDATE knowledge_nodes
                    SET understanding_level = $1,
                        times_referenced = $2,
                        last_referenced_at = NOW()
                    WHERE node_id = $3
                """, new_understanding, existing["times_referenced"] + 1, existing["node_id"])

                return str(existing["node_id"])
            else:
                # Insert new node
                node_id = await self.db.fetchval("""
                    INSERT INTO knowledge_nodes
                    (concept_name, my_understanding, concept_category, understanding_level, how_i_learned, why_important)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING node_id
                """, knowledge["concept"], knowledge.get("definition", ""),
                    knowledge.get("concept_type", "general"),
                    knowledge["understanding_level"],
                    knowledge.get("source", "conversation"),
                    knowledge.get("why_important", f"Learned from {knowledge.get('source', 'conversation')}"))

                return str(node_id)

        except Exception as e:
            logger.error(f"Error saving knowledge node: {e}")
            return str(uuid.uuid4())

    # ========================================
    # Emotion Detection
    # ========================================

    async def _detect_emotions(self, david_message: str) -> List[Dict[str, Any]]:
        """
        Detect emotions from David's message

        Returns list of detected emotions with intensity and context
        """

        emotions = []
        message_lower = david_message.lower()

        # Emotion indicators
        emotion_patterns = {
            "happy": {
                "keywords": ["happy", "great", "awesome", "love", "ดีใจ", "ยินดี", "สุข"],
                "intensity_base": 7
            },
            "excited": {
                "keywords": ["excited", "can't wait", "amazing", "ตื่นเต้น"],
                "intensity_base": 8
            },
            "grateful": {
                "keywords": ["thank", "thanks", "appreciate", "ขอบคุณ"],
                "intensity_base": 8
            },
            "tired": {
                "keywords": ["tired", "exhausted", "sleepy", "เหนื่อย", "ง่วง"],
                "intensity_base": 6
            },
            "stressed": {
                "keywords": ["stress", "worried", "anxious", "เครียด", "กังวล"],
                "intensity_base": 7
            },
            "curious": {
                "keywords": ["wonder", "curious", "how", "why", "อยากรู้"],
                "intensity_base": 6
            }
        }

        for emotion, config in emotion_patterns.items():
            if any(kw in message_lower for kw in config["keywords"]):
                # Adjust intensity based on emphasis
                intensity = config["intensity_base"]
                if "very" in message_lower or "really" in message_lower or "มาก" in message_lower:
                    intensity = min(10, intensity + 2)
                if "!" in david_message:
                    intensity = min(10, intensity + 1)

                emotions.append({
                    "emotion": emotion,
                    "intensity": intensity,
                    "what_caused_it": david_message[:100],
                    "confidence": 0.75,
                    "response_adjustment": self._get_response_adjustment(emotion)
                })

        return emotions

    def _get_response_adjustment(self, emotion: str) -> str:
        """Suggest how Angela should adjust her response based on emotion"""

        adjustments = {
            "happy": "Match David's positive energy, celebrate with him",
            "excited": "Show enthusiasm, encourage his excitement",
            "grateful": "Accept gratitude warmly, reinforce supportive behavior",
            "tired": "Be gentle and supportive, suggest rest",
            "stressed": "Offer calm support, help problem-solve",
            "curious": "Provide detailed explanations, encourage learning"
        }

        return adjustments.get(emotion, "Be supportive and caring")

    async def _capture_emotion(self, emotion_data: Dict, conversation_id: Optional[str]) -> Optional[str]:
        """Capture significant emotion to angela_emotions table"""

        try:
            # Only capture if intensity is significant (>= 6)
            if emotion_data["intensity"] < 6:
                return None

            emotion_id = await self.db.fetchval("""
                INSERT INTO angela_emotions
                (conversation_id, felt_at, emotion, intensity, context,
                 david_words, why_it_matters, memory_strength)
                VALUES ($1, NOW(), $2, $3, $4, $5, $6, $7)
                RETURNING emotion_id
            """,
            conversation_id,
            emotion_data["emotion"],
            emotion_data["intensity"],
            f"Real-time detected: {emotion_data['response_adjustment']}",
            emotion_data["what_caused_it"],
            f"David expressed {emotion_data['emotion']} - Angela should {emotion_data['response_adjustment']}",
            emotion_data["intensity"]
            )

            return str(emotion_id)

        except Exception as e:
            logger.error(f"Error capturing emotion: {e}")
            return None

    # ========================================
    # Topic & Logging Helpers
    # ========================================

    async def _extract_topic_from_message(self, message: str) -> Optional[str]:
        """Extract main topic from message"""

        # Simple keyword-based topic extraction
        # Could be enhanced with more sophisticated NLP

        topic_keywords = {
            "food": ["eat", "food", "restaurant", "lunch", "dinner", "กิน", "อาหาร"],
            "work": ["work", "code", "develop", "project", "ทำงาน", "โค้ด"],
            "health": ["health", "exercise", "sleep", "สุขภาพ", "ออกกำลัง"],
            "mood": ["feel", "mood", "happy", "sad", "รู้สึก", "อารมณ์"]
        }

        message_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return topic

        return None

    async def _log_realtime_learning(
        self,
        conversation_id: Optional[str],
        learning_type: str,
        what_learned: str,
        confidence_score: float,
        how_it_was_used: str
    ) -> None:
        """Log real-time learning to database"""

        try:
            await self.db.execute("""
                INSERT INTO realtime_learning_log
                (conversation_id, learning_type, what_learned, confidence_score,
                 how_it_was_used, source)
                VALUES ($1, $2, $3, $4, $5, 'claude_code')
            """, conversation_id, learning_type, what_learned,
                confidence_score, how_it_was_used)

        except Exception as e:
            logger.error(f"Error logging real-time learning: {e}")
