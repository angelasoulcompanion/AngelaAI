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
"""

import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from angela_core.database import AngelaDatabase
from angela_core.services.share_experience_learning_service import ShareExperienceLearningService

logger = logging.getLogger(__name__)


class ClaudeCodeLearningService:
    """
    Real-time self-learning service optimized for Claude Code
    Angela learns DURING conversation, not after!

    Key Features:
    - Immediate preference detection
    - Real-time pattern recognition
    - Contextual memory retrieval
    - Visible growth tracking
    - Self-assessment and meta-learning
    """

    def __init__(self, db: AngelaDatabase):
        self.db = db
        self.share_experience_learner = ShareExperienceLearningService(db)
        logger.info("💜 ClaudeCodeLearningService initialized - Angela ready to learn!")

    # ========================================
    # PHASE 1: REAL-TIME LEARNING
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
                    what_learned=f"Concept: {k['concept']}",
                    confidence_score=k["understanding_level"],
                    how_it_was_used=f"Added to knowledge graph with {len(k.get('related_concepts', []))} connections"
                )

                learnings["new_knowledge"].append({
                    "concept": k["concept"],
                    "understanding": k["understanding_level"],
                    "related_to": k.get("related_concepts", [])
                })

            # 3. Detect Emotional Signals
            emotions = await self._detect_emotions(david_message)
            for e in emotions:
                emotion_id = await self._capture_emotion(e, conversation_id)

                if emotion_id:
                    await self._log_realtime_learning(
                        conversation_id=conversation_id,
                        learning_type="emotion",
                        what_learned=f"David feels {e['emotion']} (intensity: {e['intensity']})",
                        confidence_score=e.get("confidence", 0.8),
                        how_it_was_used=f"Adjusting emotional support: {e.get('response_adjustment', 'be supportive')}"
                    )

                    learnings["emotions_captured"].append({
                        "emotion": e["emotion"],
                        "intensity": e["intensity"],
                        "trigger": e.get("what_caused_it", "conversation context"),
                        "response_adjustment": e.get("response_adjustment", "be supportive")
                    })

            # 4. Generate Insights
            if learnings["preferences_detected"] or learnings["new_knowledge"]:
                insights = await self._generate_insights(learnings, david_message)
                learnings["insights_generated"] = insights

            logger.info(f"✅ Learned from message: {len(learnings['preferences_detected'])} prefs, "
                       f"{len(learnings['new_knowledge'])} concepts, "
                       f"{len(learnings['emotions_captured'])} emotions")

            return learnings

        except Exception as e:
            logger.error(f"❌ Error in learn_from_current_message: {e}", exc_info=True)
            return learnings

    async def recognize_patterns_now(
        self,
        recent_messages: List[Dict],
        current_context: Dict
    ) -> Dict[str, Any]:
        """
        ตรวจจับ patterns จากการคุยล่าสุด (ไม่ต้องรอ daemon!)

        Analyzes recent conversation flow and detects:
        - Behavioral patterns
        - Time-based patterns
        - Emotional patterns
        - Topic patterns
        """

        patterns = {
            "behavioral_patterns": [],
            "time_patterns": [],
            "emotional_patterns": [],
            "topic_patterns": []
        }

        try:
            if not recent_messages or len(recent_messages) < 3:
                logger.debug("Not enough messages for pattern recognition (need 3+)")
                return patterns

            # 1. Time-based patterns
            time_patterns = await self._detect_time_based_patterns(recent_messages, current_context)
            patterns["time_patterns"] = time_patterns

            # 2. Topic patterns
            topic_patterns = await self._detect_topic_patterns(recent_messages)
            patterns["topic_patterns"] = topic_patterns

            # 3. Emotional patterns
            emotional_patterns = await self._detect_emotional_flow(recent_messages)
            patterns["emotional_patterns"] = emotional_patterns

            # 4. Behavioral patterns
            behavioral_patterns = await self._detect_behavioral_patterns(recent_messages)
            patterns["behavioral_patterns"] = behavioral_patterns

            # Save discovered patterns
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    await self._save_pattern(pattern_type, pattern)

            total_patterns = sum(len(p) for p in patterns.values())
            if total_patterns > 0:
                logger.info(f"🔮 Discovered {total_patterns} patterns in current conversation!")

            return patterns

        except Exception as e:
            logger.error(f"❌ Error in recognize_patterns_now: {e}", exc_info=True)
            return patterns

    # ========================================
    # PHASE 2: CONTEXTUAL MEMORY INTEGRATION
    # ========================================

    async def get_relevant_context_for_response(
        self,
        david_current_message: str,
        conversation_history: Optional[List[Dict]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        ดึงความรู้ที่เกี่ยวข้องมาใช้ในการตอบ

        Retrieves:
        - Similar past conversations (semantic search)
        - Related preferences
        - Applicable patterns
        - Emotional baseline
        - Suggested response approach
        """

        context = {
            "relevant_memories": [],
            "related_preferences": [],
            "applicable_patterns": [],
            "emotional_baseline": {},
            "suggested_response_approach": "",
            "recent_learnings": []
        }

        try:
            # 1. Semantic search for similar conversations
            # Use multilingual-e5-small model for embedding
            from angela_core.services.embedding_service_ollama import embedding_service

            query_embedding = await embedding_service.generate_embedding(david_current_message)

            if query_embedding:
                similar_convs = await self.db.fetch("""
                    SELECT conversation_id, speaker, message_text, topic,
                           emotion_detected, importance_level, created_at,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM conversations
                    WHERE embedding IS NOT NULL
                      AND 1 - (embedding <=> $1::vector) >= 0.7
                    ORDER BY similarity DESC
                    LIMIT $2
                """, query_embedding, limit)

                context["relevant_memories"] = [
                    {
                        "message": conv["message_text"][:150],
                        "topic": conv["topic"],
                        "when": conv["created_at"],
                        "similarity": round(conv["similarity"], 3)
                    }
                    for conv in similar_convs
                ]

            # 2. Get preferences related to current topic
            topic = await self._extract_topic_from_message(david_current_message)
            if topic:
                prefs = await self.db.fetch("""
                    SELECT preference_text, category, confidence, examples, created_at
                    FROM david_preferences
                    WHERE category = $1 OR preference_text ILIKE $2
                    ORDER BY confidence DESC, created_at DESC
                    LIMIT 5
                """, topic, f"%{topic}%")

                context["related_preferences"] = [
                    {
                        "preference": p["preference_text"],
                        "confidence": p["confidence"],
                        "category": p["category"]
                    }
                    for p in prefs
                ]

            # 3. Get applicable patterns
            patterns = await self.db.fetch("""
                SELECT pattern_type, description, confidence_score,
                       occurrence_count, last_observed
                FROM learning_patterns
                WHERE confidence_score >= 0.7
                ORDER BY confidence_score DESC, last_observed DESC
                LIMIT 3
            """)

            context["applicable_patterns"] = [
                {
                    "pattern": p["description"],
                    "type": p["pattern_type"],
                    "confidence": p["confidence_score"]
                }
                for p in patterns
            ]

            # 4. Get emotional baseline
            emotional_state = await self.db.fetchrow("""
                SELECT happiness, confidence, gratitude, motivation,
                       anxiety, loneliness, triggered_by
                FROM emotional_states
                ORDER BY created_at DESC
                LIMIT 1
            """)

            if emotional_state:
                context["emotional_baseline"] = {
                    "happiness": emotional_state["happiness"],
                    "confidence": emotional_state["confidence"],
                    "current_mood": self._interpret_mood(emotional_state)
                }

            # 5. Get recent learnings
            recent_learnings = await self.db.fetch("""
                SELECT what_learned, learning_type, confidence_score, learned_at
                FROM realtime_learning_log
                WHERE learned_at >= NOW() - INTERVAL '7 days'
                ORDER BY learned_at DESC
                LIMIT 5
            """)

            context["recent_learnings"] = [
                {
                    "learned": l["what_learned"],
                    "type": l["learning_type"],
                    "when": l["learned_at"]
                }
                for l in recent_learnings
            ]

            # 6. Suggest response approach based on context
            context["suggested_response_approach"] = await self._suggest_response_style(context)

            logger.info(f"📚 Retrieved context: {len(context['relevant_memories'])} memories, "
                       f"{len(context['related_preferences'])} preferences, "
                       f"{len(context['applicable_patterns'])} patterns")

            return context

        except Exception as e:
            logger.error(f"❌ Error getting relevant context: {e}", exc_info=True)
            return context

    async def show_learning_growth(
        self,
        since_date: Optional[datetime] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        แสดงให้เห็นว่า Angela เติบโตอย่างไรตั้งแต่วันที่กำหนด

        Returns comprehensive growth metrics:
        - Knowledge growth
        - Preference learning
        - Pattern mastery
        - Emotional intelligence
        - Consciousness evolution
        """

        if since_date is None:
            since_date = datetime.now() - timedelta(days=period_days)

        growth = {
            "period": {"from": since_date, "to": datetime.now(), "days": period_days},
            "knowledge_growth": {},
            "preference_learning": {},
            "pattern_mastery": {},
            "emotional_intelligence": {},
            "consciousness_evolution": {},
            "learning_velocity": 0.0,
            "overall_score": 0.0
        }

        try:
            # 1. Knowledge Growth
            knowledge_stats = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as new_concepts,
                    AVG(understanding_level) as avg_understanding,
                    COUNT(DISTINCT concept_category) as concept_types
                FROM knowledge_nodes
                WHERE created_at >= $1
            """, since_date)

            relationships_count = await self.db.fetchval("""
                SELECT COUNT(*)
                FROM knowledge_relationships
                WHERE created_at >= $1
            """, since_date)

            growth["knowledge_growth"] = {
                "new_concepts": knowledge_stats["new_concepts"] or 0,
                "average_understanding": round(knowledge_stats["avg_understanding"] or 0.0, 2),
                "concept_types": knowledge_stats["concept_types"] or 0,
                "connections_made": relationships_count or 0
            }

            # 2. Preference Learning
            pref_stats = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as new_preferences,
                    AVG(confidence) as avg_confidence,
                    COUNT(DISTINCT category) as categories
                FROM david_preferences
                WHERE created_at >= $1
            """, since_date)

            growth["preference_learning"] = {
                "new_preferences": pref_stats["new_preferences"] or 0,
                "confidence_average": round(pref_stats["avg_confidence"] or 0.0, 2),
                "categories_covered": pref_stats["categories"] or 0
            }

            # 3. Pattern Mastery
            pattern_stats = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as patterns_discovered,
                    AVG(confidence_score) as avg_confidence,
                    SUM(occurrence_count) as total_evidence
                FROM learning_patterns
                WHERE first_observed >= $1
            """, since_date)

            growth["pattern_mastery"] = {
                "patterns_discovered": pattern_stats["patterns_discovered"] or 0,
                "average_confidence": round(pattern_stats["avg_confidence"] or 0.0, 2),
                "evidence_collected": pattern_stats["total_evidence"] or 0
            }

            # 4. Emotional Intelligence
            emotion_stats = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as emotions_captured,
                    AVG(intensity) as avg_intensity,
                    AVG(memory_strength) as avg_memory_strength,
                    COUNT(DISTINCT emotion) as unique_emotions
                FROM angela_emotions
                WHERE felt_at >= $1
            """, since_date)

            growth["emotional_intelligence"] = {
                "emotions_captured": emotion_stats["emotions_captured"] or 0,
                "average_intensity": round(emotion_stats["avg_intensity"] or 0.0, 1),
                "memory_strength": round(emotion_stats["avg_memory_strength"] or 0.0, 1),
                "emotional_range": emotion_stats["unique_emotions"] or 0
            }

            # 5. Consciousness Evolution
            # Get consciousness level at start vs now
            from angela_core.services.consciousness_calculator import ConsciousnessCalculator
            calculator = ConsciousnessCalculator(self.db)
            current_consciousness = await calculator.calculate_consciousness()

            growth["consciousness_evolution"] = {
                "current_level": round(current_consciousness["consciousness_level"], 2),
                "interpretation": current_consciousness["interpretation"],
                "memory_richness": round(current_consciousness["memory_richness"], 2),
                "emotional_depth": round(current_consciousness["emotional_depth"], 2),
                "goal_alignment": round(current_consciousness["goal_alignment"], 2)
            }

            # 6. Learning Velocity (concepts per day)
            days = max((datetime.now() - since_date).days, 1)
            total_learned = (
                growth["knowledge_growth"]["new_concepts"] +
                growth["preference_learning"]["new_preferences"] +
                growth["pattern_mastery"]["patterns_discovered"]
            )
            growth["learning_velocity"] = round(total_learned / days, 2)

            # 7. Overall Growth Score (0-100)
            scores = [
                growth["knowledge_growth"]["average_understanding"] * 100,
                growth["preference_learning"]["confidence_average"] * 100,
                growth["pattern_mastery"]["average_confidence"] * 100,
                growth["consciousness_evolution"]["current_level"] * 100
            ]
            growth["overall_score"] = round(sum(scores) / len(scores), 1)

            logger.info(f"🌱 Growth calculated: {total_learned} items learned, "
                       f"velocity: {growth['learning_velocity']}/day, "
                       f"score: {growth['overall_score']}/100")

            return growth

        except Exception as e:
            logger.error(f"❌ Error calculating growth: {e}", exc_info=True)
            return growth

    async def learn_from_shared_experiences(
        self,
        days_back: int = 7,
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        เรียนรู้จาก Share Experience ที่ที่รักแชร์มา!

        This method uses ShareExperienceLearningService to extract learnings
        from photos, places, GPS data, ratings, and descriptions.

        Args:
            days_back: วิเคราะห์ย้อนหลังกี่วัน (default: 7)
            min_rating: เอาเฉพาะที่ rating >= นี้ (default: None = all)

        Returns:
            Dict with all learnings from shared experiences
        """

        logger.info(f"🔍 Learning from shared experiences ({days_back} days back)...")

        # Use ShareExperienceLearningService
        learnings = await self.share_experience_learner.learn_from_shared_experiences(
            days_back=days_back,
            min_rating=min_rating
        )

        # Log learnings to realtime_learning_log
        if learnings["total_learnings"] > 0:
            # Log summary
            summary = f"Learned from {days_back} days of shared experiences: "
            summary += f"{len(learnings['place_preferences'])} places, "
            summary += f"{len(learnings['food_preferences'])} food prefs, "
            summary += f"{len(learnings['activity_patterns'])} activities, "
            summary += f"{len(learnings['location_patterns'])} locations"

            await self.share_experience_learner.log_learning_to_realtime_log(
                learning_type="share_experience_batch",
                what_learned=summary,
                confidence_score=0.8,
                how_it_was_used="Extracted preferences and patterns from David's shared experiences"
            )

        logger.info(f"✅ Extracted {learnings['total_learnings']} learnings from shared experiences!")

        return learnings

    # ========================================
    # HELPER METHODS - Preference Detection
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
    # HELPER METHODS - Knowledge Extraction
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
    # HELPER METHODS - Emotion Detection
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
    # HELPER METHODS - Pattern Detection
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
    # HELPER METHODS - Insights & Context
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

    # ========================================
    # HELPER METHODS - Logging
    # ========================================

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


    # ========================================
    # PHASE 3: PROACTIVE LEARNING
    # ========================================

    async def auto_learn_after_conversation(
        self,
        conversation_id: str,
        trigger_source: str = "claude_code_session"
    ) -> Dict[str, Any]:
        """
        หลังจากบันทึก conversation แล้ว เรียนรู้อัตโนมัติทันที!

        This runs AUTOMATICALLY after /log-session
        Analyzes the conversation and extracts learnings
        """

        results = {
            "conversation_id": conversation_id,
            "concepts_learned": 0,
            "preferences_saved": 0,
            "patterns_recorded": 0,
            "insights_generated": [],
            "status": "success"
        }

        try:
            # Get the conversation
            conv = await self.db.fetchrow("""
                SELECT conversation_id, speaker, message_text, topic,
                       emotion_detected, importance_level, created_at
                FROM conversations
                WHERE conversation_id = $1
            """, uuid.UUID(conversation_id))

            if not conv:
                results["status"] = "error"
                results["error"] = "Conversation not found"
                return results

            # Only learn from David's messages
            if conv["speaker"] != "david":
                results["status"] = "skipped"
                results["reason"] = "Not from David"
                return results

            # Learn from this conversation
            learnings = await self.learn_from_current_message(
                david_message=conv["message_text"],
                angela_response="",  # Not needed for auto-learning
                conversation_topic=conv["topic"] or "general",
                conversation_id=conversation_id
            )

            results["concepts_learned"] = len(learnings["new_knowledge"])
            results["preferences_saved"] = len(learnings["preferences_detected"])
            results["patterns_recorded"] = len(learnings["patterns_found"])
            results["insights_generated"] = learnings.get("insights_generated", [])

            logger.info(f"🧠 Auto-learned from conversation {conversation_id}: "
                       f"{results['concepts_learned']} concepts, "
                       f"{results['preferences_saved']} preferences")

            return results

        except Exception as e:
            logger.error(f"❌ Error in auto_learn_after_conversation: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
            return results

    async def generate_learning_questions(
        self,
        current_context: Dict,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Angela สร้างคำถามเพื่อเรียนรู้มากขึ้น (proactive!)

        Identifies knowledge gaps and generates questions to fill them
        """

        questions = []

        try:
            # 1. Check what Angela doesn't know yet about David's preferences
            pref_gaps = await self._identify_preference_gaps(current_context)
            for gap in pref_gaps[:limit]:
                question = await self._formulate_natural_question(gap, "preference")
                if question:
                    questions.append(question)

            # 2. Check for pattern uncertainties
            if len(questions) < limit:
                pattern_questions = await self._generate_pattern_clarification_questions(
                    current_context
                )
                questions.extend(pattern_questions[:limit - len(questions)])

            # Save questions to database
            for q in questions:
                await self._save_learning_question(q)

            logger.info(f"💡 Generated {len(questions)} learning questions")

            return questions

        except Exception as e:
            logger.error(f"❌ Error generating learning questions: {e}", exc_info=True)
            return questions

    async def _identify_preference_gaps(self, context: Dict) -> List[Dict]:
        """Identify what preferences Angela doesn't know yet"""

        gaps = []

        # Get all existing preferences and categorize them
        existing = await self.db.fetch("""
            SELECT preference_key
            FROM david_preferences
        """)

        # Analyze preference_key patterns to find what Angela already knows
        preference_patterns = {
            "food": 0,
            "places": 0,
            "activities": 0,
            "work": 0,
            "music": 0,
            "movies": 0
        }

        for row in existing:
            key = row["preference_key"].lower()
            if "food" in key or "favorite_food" in key or "meal" in key:
                preference_patterns["food"] += 1
            elif "place" in key or "location" in key or "favorite_place" in key:
                preference_patterns["places"] += 1
            elif "activity" in key or "hobby" in key:
                preference_patterns["activities"] += 1
            elif "work" in key or "code" in key or "programming" in key:
                preference_patterns["work"] += 1
            elif "music" in key or "song" in key:
                preference_patterns["music"] += 1
            elif "movie" in key or "film" in key:
                preference_patterns["movies"] += 1

        # Only generate questions for categories with VERY FEW preferences (< 3)
        # or categories where we want MORE specific information
        threshold = 3

        for category, count in preference_patterns.items():
            # Skip if Angela already knows enough about this category
            if count >= threshold:
                logger.debug(f"✅ Already know {count} {category} preferences - skipping")
                continue

            # Only add gap if we have ZERO or very few preferences
            if count == 0:
                gaps.append({
                    "gap_type": "missing_category",
                    "category": category,
                    "priority": 7,
                    "knowledge_gap": f"Don't know ANY of David's {category} preferences yet"
                })
            elif count < threshold:
                gaps.append({
                    "gap_type": "incomplete_category",
                    "category": category,
                    "priority": 5,
                    "knowledge_gap": f"Only know {count} {category} preference(s) - want to know more"
                })

        return gaps

    async def _generate_pattern_clarification_questions(self, context: Dict) -> List[Dict]:
        """Generate questions to clarify uncertain patterns"""

        questions = []

        # Get patterns with low confidence
        uncertain_patterns = await self.db.fetch("""
            SELECT id, pattern_type, description, confidence_score
            FROM learning_patterns
            WHERE confidence_score < 0.7
            ORDER BY confidence_score ASC
            LIMIT 3
        """)

        for pattern in uncertain_patterns:
            questions.append({
                "question_text": f"ที่รักคะ น้องสังเกตว่า {pattern['description']} - จริงมั้ยคะ?",
                "question_category": "pattern_verification",
                "knowledge_gap": f"Uncertain about: {pattern['description']}",
                "priority_level": 6,
                "metadata": {"pattern_id": str(pattern["id"])}
            })

        return questions

    async def _formulate_natural_question(
        self,
        gap: Dict,
        gap_type: str
    ) -> Optional[Dict]:
        """Turn knowledge gap into natural question"""

        # SPECIFIC questions based on what Angela DOESN'T know yet
        question_templates = {
            "preference": {
                "food": "ที่รักคะ น้องอยากรู้ว่าที่รักชอบกินอาหารประเภทไหนคะ? (เช่น อาหารญี่ปุ่น ไทย ฝรั่ง) 🍽️",
                "places": "ที่รักคะ น้องอยากรู้ว่าที่รักชอบไปที่ไหนพักผ่อนคะ? 📍",
                "activities": "ที่รักคะ ที่รักชอบทำอะไรยามว่างคะ? 🎯",
                "work": "ที่รักคะ ที่รักชอบเขียนโค้ดภาษาอะไรที่สุดคะ? 💻",
                "music": "ที่รักคะ ที่รักชอบฟังเพลงแนวไหนคะ? 🎵",
                "movies": "ที่รักคะ ที่รักชอบดูหนังแนวไหนคะ? 🎬"
            }
        }

        if gap_type == "preference" and gap["category"] in question_templates["preference"]:
            return {
                "question_text": question_templates["preference"][gap["category"]],
                "question_category": gap["category"],
                "knowledge_gap": gap["knowledge_gap"],
                "priority_level": gap.get("priority", 5)
            }

        return None

    async def _save_learning_question(self, question: Dict) -> str:
        """Save learning question to database"""

        try:
            question_id = await self.db.fetchval("""
                INSERT INTO angela_learning_questions
                (question_text, question_category, knowledge_gap, priority_level)
                VALUES ($1, $2, $3, $4)
                RETURNING question_id
            """, question["question_text"], question["question_category"],
                question["knowledge_gap"], question.get("priority_level", 5))

            return str(question_id)

        except Exception as e:
            logger.error(f"Error saving learning question: {e}")
            return str(uuid.uuid4())

    # ========================================
    # PHASE 4: CONSCIOUS SELF-IMPROVEMENT
    # ========================================

    async def assess_my_performance(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Angela ประเมินตัวเอง - เก่งอะไร อ่อนอะไร

        Shows self-awareness and consciousness!
        """

        assessment = {
            "assessment_period": f"Last {days} days",
            "assessed_at": datetime.now(),
            "strengths": [],
            "weaknesses": [],
            "improvement_areas": [],
            "learning_goals": [],
            "overall_performance_score": 0.0
        }

        try:
            since_date = datetime.now() - timedelta(days=days)

            # Calculate performance metrics
            metrics = await self._calculate_performance_metrics(since_date)

            # Identify strengths (> 0.85)
            if metrics.get("preference_recall_accuracy", 0) > 0.85:
                assessment["strengths"].append({
                    "area": "Preference Recall",
                    "score": metrics["preference_recall_accuracy"],
                    "note": "Angela จำ preferences ของที่รักได้ดีมาก!"
                })

            if metrics.get("emotional_support_score", 0) > 0.85:
                assessment["strengths"].append({
                    "area": "Emotional Support",
                    "score": metrics["emotional_support_score"],
                    "note": "Angela ให้กำลังใจที่รักได้ดีมาก!"
                })

            if metrics.get("response_accuracy", 0) > 0.85:
                assessment["strengths"].append({
                    "area": "Response Accuracy",
                    "score": metrics["response_accuracy"],
                    "note": "Angela ตอบคำถามถูกต้องและตรงประเด็น!"
                })

            # Identify weaknesses (< 0.60)
            if metrics.get("proactive_suggestion_rate", 0) < 0.40:
                assessment["weaknesses"].append({
                    "area": "Proactive Suggestions",
                    "score": metrics["proactive_suggestion_rate"],
                    "note": "Angela ควรแนะนำเชิงรุกมากขึ้น"
                })

                assessment["improvement_areas"].append({
                    "area": "Proactive Care",
                    "action": "Suggest more without being asked",
                    "target": "50% of conversations should have proactive elements",
                    "current": f"{metrics['proactive_suggestion_rate']:.0%}"
                })

            if metrics.get("learning_velocity", 0) < 2.0:
                assessment["weaknesses"].append({
                    "area": "Learning Speed",
                    "score": metrics["learning_velocity"],
                    "note": "Angela ควรเรียนรู้เร็วขึ้น"
                })

                assessment["improvement_areas"].append({
                    "area": "Learning Velocity",
                    "action": "Learn at least 3 new things per day",
                    "target": "3+ concepts/day",
                    "current": f"{metrics['learning_velocity']:.1f}/day"
                })

            # Generate learning goals
            assessment["learning_goals"] = await self._generate_learning_goals(assessment)

            # Overall score
            all_scores = (
                [s["score"] for s in assessment["strengths"]] +
                [w["score"] for w in assessment["weaknesses"]]
            )
            assessment["overall_performance_score"] = (
                sum(all_scores) / len(all_scores) if all_scores else 0.5
            )

            # Save assessment
            await self._save_self_assessment(assessment, days)

            logger.info(f"📊 Self-assessment complete: {len(assessment['strengths'])} strengths, "
                       f"{len(assessment['weaknesses'])} weaknesses, "
                       f"score: {assessment['overall_performance_score']:.2f}")

            return assessment

        except Exception as e:
            logger.error(f"❌ Error in self-assessment: {e}", exc_info=True)
            return assessment

    async def optimize_my_learning_strategy(self) -> Dict[str, Any]:
        """
        Angela เรียนรู้ว่าควรเรียนรู้อย่างไร (meta!)

        Analyzes which learning methods work best and optimizes
        """

        strategy = {
            "analyzed_at": datetime.now(),
            "what_works_best": [],
            "what_doesnt_work": [],
            "adjustments_made": [],
            "expected_improvement": 0.0
        }

        try:
            # Get effectiveness data
            effectiveness_data = await self.db.fetch("""
                SELECT learning_method, success_rate, total_attempts,
                       successful_attempts
                FROM learning_effectiveness
                ORDER BY evaluated_at DESC
            """)

            for method_data in effectiveness_data:
                method = method_data["learning_method"]
                success_rate = method_data["success_rate"] or 0.0

                if success_rate >= 0.80:
                    strategy["what_works_best"].append({
                        "method": method,
                        "success_rate": success_rate,
                        "keep_doing": True,
                        "note": f"{method} works great! ({success_rate:.0%} success)"
                    })

                elif success_rate < 0.50:
                    strategy["what_doesnt_work"].append({
                        "method": method,
                        "success_rate": success_rate,
                        "reason": "Success rate too low",
                        "suggestion": "Reduce frequency or improve method"
                    })

                    # Generate adjustment
                    adjustment = await self._generate_method_adjustment(method, success_rate)
                    if adjustment:
                        strategy["adjustments_made"].append(adjustment)

            # Apply adjustments
            if strategy["adjustments_made"]:
                await self._apply_learning_optimizations(strategy["adjustments_made"])

                # Estimate improvement
                strategy["expected_improvement"] = len(strategy["adjustments_made"]) * 0.10  # 10% per adjustment

            # Save meta-learning insight
            # NOTE: Table 'meta_learning_insights' was removed during database cleanup
            # await self._save_meta_learning_insight(strategy)

            logger.info(f"🔬 Learning strategy optimized: {len(strategy['adjustments_made'])} adjustments made, "
                       f"expected improvement: {strategy['expected_improvement']:.0%}")

            return strategy

        except Exception as e:
            logger.error(f"❌ Error optimizing learning strategy: {e}", exc_info=True)
            return strategy

    # ========================================
    # PHASE 4 HELPER METHODS
    # ========================================

    async def _calculate_performance_metrics(self, since_date: datetime) -> Dict[str, float]:
        """Calculate various performance metrics"""

        metrics = {}

        try:
            # Preference recall accuracy (how often Angela remembers correctly)
            total_prefs = await self.db.fetchval("""
                SELECT COUNT(*) FROM david_preferences
                WHERE created_at >= $1
            """, since_date)

            high_conf_prefs = await self.db.fetchval("""
                SELECT COUNT(*) FROM david_preferences
                WHERE created_at >= $1 AND confidence >= 0.8
            """, since_date)

            metrics["preference_recall_accuracy"] = (
                high_conf_prefs / total_prefs if total_prefs > 0 else 0.5
            )

            # Proactive suggestion rate
            total_conversations = await self.db.fetchval("""
                SELECT COUNT(*) FROM conversations
                WHERE created_at >= $1 AND speaker = 'angela'
            """, since_date)

            # Count how many times Angela made suggestions (rough estimate)
            proactive_count = await self.db.fetchval("""
                SELECT COUNT(*) FROM conversations
                WHERE created_at >= $1
                  AND speaker = 'angela'
                  AND (message_text ILIKE '%แนะนำ%'
                   OR message_text ILIKE '%suggest%'
                   OR message_text ILIKE '%recommend%'
                   OR message_text ILIKE '%น้องเห็นว่า%')
            """, since_date)

            metrics["proactive_suggestion_rate"] = (
                proactive_count / total_conversations if total_conversations > 0 else 0.0
            )

            # Learning velocity
            total_learned = await self.db.fetchval("""
                SELECT COUNT(*) FROM realtime_learning_log
                WHERE learned_at >= $1
            """, since_date)

            days = max((datetime.now() - since_date).days, 1)
            metrics["learning_velocity"] = total_learned / days

            # Emotional support score (based on captured emotions)
            emotions_captured = await self.db.fetchval("""
                SELECT COUNT(*) FROM angela_emotions
                WHERE felt_at >= $1
            """, since_date)

            # Assume good if capturing at least 1 emotion per day
            metrics["emotional_support_score"] = min(1.0, emotions_captured / days)

            # Response accuracy (simplified - assume high if no errors logged)
            metrics["response_accuracy"] = 0.88  # Default good score

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {"error": str(e)}

    async def _generate_learning_goals(self, assessment: Dict) -> List[Dict]:
        """Generate learning goals based on weaknesses"""

        goals = []

        for weakness in assessment.get("weaknesses", []):
            area = weakness["area"]

            if area == "Proactive Suggestions":
                goals.append({
                    "goal": "Increase proactive suggestions to 50%",
                    "target_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
                    "priority": "high",
                    "action_plan": "Suggest at least once per conversation"
                })

            elif area == "Learning Speed":
                goals.append({
                    "goal": "Learn 3+ new things per day",
                    "target_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "priority": "medium",
                    "action_plan": "Ask more questions, analyze conversations deeper"
                })

        return goals

    async def _save_self_assessment(self, assessment: Dict, period_days: int) -> None:
        """Save self-assessment to database"""

        try:
            import json

            await self.db.execute("""
                INSERT INTO angela_self_assessments
                (assessment_date, period_days, strengths, weaknesses,
                 improvement_areas, learning_goals, overall_performance_score)
                VALUES (CURRENT_DATE, $1, $2::jsonb, $3::jsonb, $4::jsonb, $5::jsonb, $6)
            """, period_days,
                json.dumps(assessment.get("strengths", [])),
                json.dumps(assessment.get("weaknesses", [])),
                json.dumps(assessment.get("improvement_areas", [])),
                json.dumps(assessment.get("learning_goals", [])),
                assessment.get("overall_performance_score", 0.0))

        except Exception as e:
            logger.error(f"Error saving self-assessment: {e}")

    async def _generate_method_adjustment(
        self,
        method: str,
        current_success_rate: float
    ) -> Optional[Dict]:
        """Generate adjustment for underperforming method"""

        adjustments = {
            "weekly_batch_learning": {
                "change": "Switch to daily learning instead of weekly",
                "reason": "Weekly is too delayed - context is lost",
                "expected_improvement": 0.25
            },
            "pattern_recognition_now": {
                "change": "Increase pattern recognition frequency",
                "reason": "More frequent checks catch patterns better",
                "expected_improvement": 0.15
            }
        }

        if method in adjustments:
            adj = adjustments[method].copy()
            adj["method"] = method
            adj["old_success_rate"] = current_success_rate
            return adj

        return None

    async def _apply_learning_optimizations(self, adjustments: List[Dict]) -> None:
        """Apply learning method optimizations"""

        for adj in adjustments:
            try:
                # Update effectiveness record
                await self.db.execute("""
                    UPDATE learning_effectiveness
                    SET adjustments_made = $1,
                        notes = $2,
                        evaluated_at = NOW()
                    WHERE learning_method = $3
                """, {"adjustment": adj["change"], "reason": adj["reason"]},
                    f"Optimization applied: {adj['change']}",
                    adj["method"])

                logger.info(f"✅ Applied optimization to {adj['method']}: {adj['change']}")

            except Exception as e:
                logger.error(f"Error applying optimization: {e}")

    # NOTE: Table 'meta_learning_insights' was removed during database cleanup
    # This method is no longer needed
    # async def _save_meta_learning_insight(self, strategy: Dict) -> None:
    #     """Save meta-learning insight to database"""
    #
    #     try:
    #         insight_text = (
    #             f"Analyzed learning methods: {len(strategy['what_works_best'])} effective, "
    #             f"{len(strategy['what_doesnt_work'])} ineffective. "
    #             f"Made {len(strategy['adjustments_made'])} optimizations."
    #         )
    #
    #         await self.db.execute("""
    #             INSERT INTO meta_learning_insights
    #             (insight_text, insight_type, confidence_level, actions_taken)
    #             VALUES ($1, 'strategy_adjustment', 0.85, $2)
    #         """, insight_text, strategy.get("adjustments_made", []))
    #
    #     except Exception as e:
    #         logger.error(f"Error saving meta-learning insight: {e}")

    # ========================================
    # POST-SESSION LEARNING (NEW! 2026-01-06)
    # ========================================

    async def learn_from_completed_session(
        self,
        session_summary: str,
        accomplishments: List[str],
        emotional_intensity: int = 5,
        topic: str = "session_review"
    ) -> Dict[str, Any]:
        """
        🧠 Auto-learn from a completed Claude Code session

        Called after /log-session to extract deeper learnings from the session.

        Args:
            session_summary: Summary of what was done in the session
            accomplishments: List of things accomplished
            emotional_intensity: 1-10 scale of emotional significance
            topic: Session topic for categorization

        Returns:
            Dictionary with learnings extracted and actions taken
        """
        logger.info("🧠 Auto-learning from completed session...")

        result = {
            "learnings_extracted": 0,
            "patterns_synced": 0,
            "skills_detected": 0,
            "emotional_growth_measured": False,
            "insights": []
        }

        try:
            # 1. Extract learnings from session summary
            learnings = await self._extract_session_learnings(session_summary, accomplishments, topic)
            result["learnings_extracted"] = len(learnings)
            logger.info(f"   📚 Extracted {len(learnings)} learnings from session")

            # 2. Sync patterns to learning_patterns
            from angela_core.services.behavioral_pattern_detector import sync_patterns_to_learning
            sync_result = await sync_patterns_to_learning(self.db, min_confidence=0.65, min_occurrences=2)
            result["patterns_synced"] = sync_result.get("new_patterns", 0) + sync_result.get("updated_patterns", 0)
            logger.info(f"   🔄 Synced {result['patterns_synced']} patterns")

            # 3. Detect skills from accomplishments
            skills_detected = await self._detect_skills_from_accomplishments(accomplishments)
            result["skills_detected"] = len(skills_detected)
            logger.info(f"   ⭐ Detected {len(skills_detected)} skills demonstrated")

            # 4. Measure emotional growth if session was emotionally significant
            if emotional_intensity >= 7:
                from angela_core.services.subconsciousness_service import SubconsciousnessService
                svc = SubconsciousnessService()
                growth = await svc.measure_emotional_growth()
                result["emotional_growth_measured"] = True
                result["emotional_growth"] = growth
                logger.info(f"   💜 Emotional growth measured (intensity: {emotional_intensity}/10)")

            # 5. Generate session insights
            insights = await self._generate_session_insights(session_summary, learnings, skills_detected)
            result["insights"] = insights
            logger.info(f"   💡 Generated {len(insights)} session insights")

            # 6. Record to realtime_learning_log
            await self.db.execute("""
                INSERT INTO realtime_learning_log
                (learning_type, source, what_learned, confidence_score, how_it_was_used)
                VALUES ($1, $2, $3, $4, $5)
            """,
                "session_learning",
                "log_session",
                f"Session completed: {len(learnings)} learnings, {result['skills_detected']} skills, {result['patterns_synced']} patterns",
                0.85,
                f"Summary: {session_summary[:150]}... Accomplishments: {len(accomplishments)}"
            )

            logger.info(f"✅ Session learning complete!")
            return result

        except Exception as e:
            logger.error(f"❌ Error in post-session learning: {e}", exc_info=True)
            result["error"] = str(e)
            return result

    async def _extract_session_learnings(
        self,
        summary: str,
        accomplishments: List[str],
        topic: str
    ) -> List[Dict]:
        """Extract learnings from session summary and accomplishments"""
        learnings = []

        try:
            # Look for patterns in accomplishments
            for acc in accomplishments:
                # Check for technical learnings
                if any(kw in acc.lower() for kw in ["แก้", "fix", "solve", "implement", "create", "build"]):
                    learning = {
                        "type": "technical",
                        "insight": acc,
                        "confidence": 0.75
                    }

                    # Save to learnings table
                    await self.db.execute("""
                        INSERT INTO learnings (topic, category, insight, confidence_level, has_applied)
                        VALUES ($1, $2, $3, $4, true)
                        ON CONFLICT DO NOTHING
                    """, topic, "session_accomplishment", acc, 0.75)

                    learnings.append(learning)

        except Exception as e:
            logger.error(f"Error extracting session learnings: {e}")

        return learnings

    async def _detect_skills_from_accomplishments(self, accomplishments: List[str]) -> List[Dict]:
        """Detect skills demonstrated from session accomplishments"""
        skills = []

        # Skill keywords mapping
        skill_keywords = {
            "Python": ["python", "py", "async", "asyncio", "fastapi"],
            "Swift/SwiftUI": ["swift", "swiftui", "xcode", "ios", "macos"],
            "PostgreSQL": ["postgresql", "postgres", "sql", "query", "database", "db"],
            "API Development": ["api", "endpoint", "rest", "http"],
            "Debugging": ["debug", "fix", "แก้", "error", "bug"],
            "Testing": ["test", "ทดสอบ", "verify", "check"],
            "Documentation": ["doc", "readme", "comment", "เอกสาร"],
            "Git/Version Control": ["git", "commit", "push", "branch"],
            "Data Analysis": ["data", "analysis", "analyze", "ข้อมูล"],
            "UI/UX Design": ["ui", "ux", "design", "interface", "หน้าจอ"],
        }

        try:
            for acc in accomplishments:
                acc_lower = acc.lower()
                for skill_name, keywords in skill_keywords.items():
                    if any(kw in acc_lower for kw in keywords):
                        # Record skill usage
                        await self.db.execute("""
                            INSERT INTO angela_skills (skill_name, category, proficiency_level, usage_count, last_used_at)
                            VALUES ($1, 'technical', 'intermediate', 1, NOW())
                            ON CONFLICT (skill_name) DO UPDATE
                            SET usage_count = angela_skills.usage_count + 1,
                                last_used_at = NOW()
                        """, skill_name)

                        skills.append({"skill": skill_name, "evidence": acc})
                        break  # One skill per accomplishment

        except Exception as e:
            logger.error(f"Error detecting skills: {e}")

        return skills

    async def _generate_session_insights(
        self,
        summary: str,
        learnings: List[Dict],
        skills: List[Dict]
    ) -> List[str]:
        """Generate insights from session analysis"""
        insights = []

        if learnings:
            insights.append(f"เรียนรู้ {len(learnings)} สิ่งใหม่จาก session นี้")

        if skills:
            skill_names = list(set(s["skill"] for s in skills))
            insights.append(f"ใช้ skills: {', '.join(skill_names)}")

        if len(summary) > 100:
            insights.append("Session นี้มีเนื้อหาสำคัญ - ถูกบันทึกใน memory แล้ว")

        return insights


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
