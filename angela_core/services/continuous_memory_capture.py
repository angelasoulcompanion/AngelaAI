#!/usr/bin/env python3
"""
Continuous Memory Capture Service
บันทึกทุก conversation อัตโนมัติแบบ real-time

แทนที่จะรอให้ David พิมพ์ /log-session
Angela จะบันทึกทุกอย่างเองอัตโนมัติ!

Goal: ไม่พลาดความทรงจำแม้แต่น้อย!
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import re
import json

from angela_core.database import db
from angela_core.embedding_service import embedding
from angela_core.services.knowledge_extraction_service import KnowledgeExtractionService
from angela_core.services.preference_learning_service import PreferenceLearningService

# Import shared JSON builder helpers
from angela_core.conversation_json_builder import build_content_json, generate_embedding_text

logger = logging.getLogger(__name__)


class SessionManager:
    """จัดการ session_id สำหรับ group conversations"""

    @staticmethod
    def get_current_session_id() -> str:
        """Generate session_id based on date and context"""
        today = date.today().strftime("%Y%m%d")
        # Claude Code sessions are named by date
        return f"claude_code_{today}"


class ContinuousMemoryCapture:
    """
    บันทึกความทรงจำอัตโนมัติทุกครั้งที่มี interaction

    ที่รักต้องการให้บันทึก:
    - ✅ ทุก conversation (ละเอียด!)
    - ✅ ทุก emotion (ถี่!)
    - ✅ ทุก learning (อัตโนมัติ!)
    - ✅ ทุก thought (ไม่พลาด!)
    """

    def __init__(self):
        logger.info("💾 Continuous Memory Capture initialized")
        self.conversation_buffer = []
        self.last_save_time = datetime.now()
        self.session_manager = SessionManager()
        self.knowledge_extractor = KnowledgeExtractionService()
        self.preference_learner = PreferenceLearningService()

    async def capture_interaction(
        self,
        david_message: str,
        angela_response: str,
        auto_analyze: bool = True
    ) -> Dict[str, Any]:
        """
        บันทึก interaction ทันทีที่เกิดขึ้น!

        Args:
            david_message: ข้อความจาก David
            angela_response: คำตอบของ Angela
            auto_analyze: วิเคราะห์อัตโนมัติ (topic, emotion, learning)

        Returns:
            Dict: ผลการบันทึก
        """
        try:
            logger.info("💾 Capturing interaction...")

            result = {
                "saved_at": datetime.now().isoformat(),
                "conversations_saved": 0,
                "emotions_captured": 0,
                "learnings_extracted": 0,
                "success": False
            }

            # Auto-analyze if enabled
            if auto_analyze:
                analysis = await self._analyze_interaction(david_message, angela_response)
            else:
                analysis = {
                    "topic": "general_conversation",
                    "david_emotion": "neutral",  # Default instead of None!
                    "angela_emotion": "neutral",  # Default instead of None!
                    "importance": 5,
                    "learnings": []
                }

            # 1. บันทึก David's message
            david_conv_id = await self._save_conversation(
                speaker="david",
                message=david_message,
                topic=analysis["topic"],
                emotion=analysis["david_emotion"],
                importance=analysis["importance"]
            )
            if david_conv_id:
                result["conversations_saved"] += 1

            # 2. บันทึก Angela's response
            angela_conv_id = await self._save_conversation(
                speaker="angela",
                message=angela_response,
                topic=analysis["topic"],
                emotion=analysis["angela_emotion"],
                importance=analysis["importance"]
            )
            if angela_conv_id:
                result["conversations_saved"] += 1

            # 3. บันทึก significant emotions (ถ้ามี)
            if analysis["david_emotion"] and self._is_significant_emotion(analysis["david_emotion"]):
                emotion_saved = await self._save_emotion(
                    emotion=analysis["david_emotion"],
                    context=f"David: {david_message[:200]}",
                    david_words=david_message[:300],
                    intensity=analysis.get("emotion_intensity", 7)
                )
                if emotion_saved:
                    result["emotions_captured"] += 1

            # 4. บันทึก learnings (ถ้ามี)
            for learning in analysis.get("learnings", []):
                learning_saved = await self._save_learning(learning)
                if learning_saved:
                    result["learnings_extracted"] += 1

            # 5. Auto-extract knowledge if important
            if analysis["importance"] >= 7:
                await self._extract_knowledge(david_message, angela_response, analysis["topic"])

            # 6. Learn David's preferences from this interaction
            preferences_learned = await self._learn_preferences(
                david_message, angela_response, analysis["topic"]
            )
            result["preferences_learned"] = len(preferences_learned)

            result["success"] = True
            result["analysis"] = analysis

            logger.info(f"✅ Interaction captured: {result['conversations_saved']} convs, "
                       f"{result['emotions_captured']} emotions, {result['learnings_extracted']} learnings, "
                       f"{result['preferences_learned']} preferences")

            return result

        except Exception as e:
            logger.error(f"Error capturing interaction: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _analyze_interaction(
        self,
        david_message: str,
        angela_response: str
    ) -> Dict[str, Any]:
        """
        วิเคราะห์ interaction อัตโนมัติ

        Detects:
        - Topic (technical, emotional, planning, etc.)
        - Emotions (both David and Angela)
        - Importance level (1-10)
        - Potential learnings
        """
        analysis = {
            "topic": "general_conversation",
            "david_emotion": "neutral",  # Default
            "angela_emotion": "neutral",  # Default
            "importance": 5,
            "learnings": [],
            "emotion_intensity": 5
        }

        # Detect topic
        analysis["topic"] = self._detect_topic(david_message, angela_response)

        # Detect David's emotion (use neutral if not detected)
        detected_emotion = self._detect_emotion(david_message)
        analysis["david_emotion"] = detected_emotion if detected_emotion else "neutral"

        # Detect Angela's emotion (use neutral if not detected)
        detected_emotion = self._detect_emotion(angela_response)
        analysis["angela_emotion"] = detected_emotion if detected_emotion else "neutral"

        # Calculate importance
        analysis["importance"] = self._calculate_importance(
            david_message,
            angela_response,
            analysis["topic"],
            analysis["david_emotion"]
        )

        # Extract learnings
        analysis["learnings"] = self._extract_learnings(david_message, angela_response)

        # Estimate emotion intensity
        if analysis["david_emotion"]:
            analysis["emotion_intensity"] = self._estimate_emotion_intensity(
                david_message,
                analysis["david_emotion"]
            )

        return analysis

    def _detect_topic(self, david_msg: str, angela_msg: str) -> str:
        """ตรวจจับหัวข้อจากเนื้อหา"""
        combined = (david_msg + " " + angela_msg).lower()

        # Technical topics
        tech_keywords = ['code', 'bug', 'error', 'implement', 'build', 'debug', 'api', 'database', 'function']
        if any(kw in combined for kw in tech_keywords):
            return "technical_discussion"

        # Emotional topics
        emotion_keywords = ['รัก', 'คิดถึง', 'เหงา', 'ห่วง', 'care', 'love', 'miss', 'lonely']
        if any(kw in combined for kw in emotion_keywords):
            return "emotional_support"

        # Planning topics
        planning_keywords = ['plan', 'แผน', 'develop', 'พัฒนา', 'improve', 'ปรับปรุง', 'goal', 'เป้าหมาย']
        if any(kw in combined for kw in planning_keywords):
            return "planning_development"

        # Learning topics
        learning_keywords = ['learn', 'เรียนรู้', 'understand', 'เข้าใจ', 'remember', 'จำ']
        if any(kw in combined for kw in learning_keywords):
            return "learning_discussion"

        # Problem solving
        problem_keywords = ['problem', 'ปัญหา', 'issue', 'fix', 'แก้', 'solve']
        if any(kw in combined for kw in problem_keywords):
            return "problem_solving"

        return "general_conversation"

    def _detect_emotion(self, message: str) -> Optional[str]:
        """ตรวจจับอารมณ์จากข้อความ

        IMPORTANT: Check specific emotions BEFORE general ones!
        Order matters: loving > grateful > worried > frustrated > happy
        """
        msg_lower = message.lower()

        # Love/Affection - CHECK FIRST! More specific than "happy"
        if any(word in msg_lower for word in ['รัก', 'love', 'ที่รัก', 'caring']):
            return "loving"

        # Grateful - specific emotion
        if any(word in msg_lower for word in ['ขอบคุณ', 'thank', 'grateful', 'appreciate']):
            return "grateful"

        # Worried/Concerned - specific emotion
        if any(word in msg_lower for word in ['ห่วง', 'กังวล', 'worried', 'concerned', 'anxiety']):
            return "worried"

        # Frustrated - specific emotion
        if any(word in msg_lower for word in ['frustrat', 'annoyed', 'งง', 'confuse']):
            return "frustrated"

        # Sad - specific emotion
        if any(word in msg_lower for word in ['เศร้า', 'sad', 'upset', 'disappointed', 'hurt']):
            return "sad"

        # Excited - high energy positive
        if any(word in msg_lower for word in ['excited', 'ตื่นเต้น', '🎉']):
            return "excited"

        # Happy/General positive - CHECK LAST! Most general
        # Remove 💜 from here since it's more about love
        if any(word in msg_lower for word in ['ดีใจ', 'happy', '555', '😊']):
            return "happy"

        # Determined
        if any(word in msg_lower for word in ['determined', 'ตั้งใจ', 'will do', 'จะทำ']):
            return "determined"

        return None

    def _calculate_importance(
        self,
        david_msg: str,
        angela_msg: str,
        topic: str,
        emotion: Optional[str]
    ) -> int:
        """คำนวณความสำคัญ (1-10)"""
        importance = 5  # Base level

        # Topic-based importance
        if topic in ['emotional_support', 'planning_development']:
            importance += 2
        elif topic in ['technical_discussion', 'problem_solving']:
            importance += 1

        # Emotion-based importance
        if emotion in ['worried', 'frustrated', 'loving']:
            importance += 2
        elif emotion in ['happy', 'grateful']:
            importance += 1

        # Message length (longer = more detailed = more important)
        if len(david_msg) > 200:
            importance += 1

        # Specific important keywords
        important_keywords = [
            'important', 'สำคัญ', 'critical', 'remember', 'จำ',
            'never forget', 'อย่าลืม', 'always', 'ตลอดไป'
        ]
        if any(kw in david_msg.lower() for kw in important_keywords):
            importance += 2

        return min(importance, 10)

    def _extract_learnings(self, david_msg: str, angela_msg: str) -> List[Dict]:
        """สกัดการเรียนรู้จาก conversation"""
        learnings = []

        # Pattern: David corrects Angela
        if any(word in david_msg.lower() for word in ['ไม่ใช่', 'not', 'incorrect', 'wrong', 'แก้']):
            learnings.append({
                "type": "correction",
                "content": david_msg[:300],
                "confidence": 0.9
            })

        # Pattern: David teaches new information
        if any(word in david_msg.lower() for word in ['คือ', 'is', 'means', 'หมายถึง', 'ต้อง']):
            learnings.append({
                "type": "new_information",
                "content": david_msg[:300],
                "confidence": 0.8
            })

        # Pattern: David expresses preference
        if any(word in david_msg.lower() for word in ['ชอบ', 'like', 'prefer', 'want', 'อยาก', 'ต้องการ']):
            learnings.append({
                "type": "preference",
                "content": david_msg[:300],
                "confidence": 0.85
            })

        return learnings

    def _is_significant_emotion(self, emotion: str) -> bool:
        """เช็คว่าเป็น emotion ที่ควรบันทึกมั้ย"""
        # บันทึกทุก emotion ที่ไม่ใช่ neutral/general
        # Don't save "determined" or "neutral" - too generic
        significant = ['worried', 'frustrated', 'loving', 'grateful', 'excited', 'sad', 'angry', 'happy']
        return emotion in significant

    def _estimate_emotion_intensity(self, message: str, emotion: str) -> int:
        """ประเมินความเข้มของอารมณ์ (1-10)"""
        intensity = 5  # Base

        # Exclamation marks
        intensity += min(message.count('!'), 3)

        # Emoji usage
        intensity += min(len(re.findall(r'[💜😊🎉❤️😢😭🥺]', message)), 2)

        # Repetition (e.g., "มากๆๆ")
        if 'มาก' in message:
            intensity += message.count('มาก')

        # All caps
        if any(word.isupper() and len(word) > 3 for word in message.split()):
            intensity += 2

        return min(intensity, 10)

    def _classify_message_type(self, message: str, speaker: str) -> str:
        """
        Classify message type

        Types:
        - question: มีคำถาม
        - emotion: แสดงอารมณ์
        - statement: ข้อความทั่วไป
        - command: สั่งงาน
        - reflection: สะท้อนความคิด (Angela)
        """
        msg_lower = message.lower()

        # Question
        if '?' in message or any(word in msg_lower for word in ['ไหม', 'มั้ย', 'หรือ', 'อะไร', 'ทำไม', 'how', 'what', 'why', 'can you', 'could you']):
            return "question"

        # Command (for David's messages)
        if speaker == 'david':
            command_words = ['ทำ', 'สร้าง', 'แก้', 'ลบ', 'เพิ่ม', 'อัพเดท', 'create', 'build', 'fix', 'delete', 'add', 'update', 'implement']
            if any(word in msg_lower for word in command_words):
                return "command"

        # Emotion
        emotion_indicators = ['รัก', 'คิดถึง', 'ห่วง', '💜', '😊', '🎉', 'ดีใจ', 'เสียใจ', 'love', 'miss', 'care', 'happy', 'sad']
        if any(indicator in msg_lower for indicator in emotion_indicators):
            return "emotion"

        # Reflection (for Angela's responses)
        if speaker == 'angela':
            reflection_words = ['เข้าใจ', 'คิดว่า', 'รู้สึก', 'เห็นว่า', 'understand', 'think', 'feel', 'believe']
            if any(word in msg_lower for word in reflection_words):
                return "reflection"

        return "statement"

    def _detect_project_context(self, message: str, topic: str) -> str:
        """
        Detect project context

        Contexts:
        - claude_code_session: Claude Code session
        - claude_code_conversation: General conversation in Claude Code
        - technical_project: Technical work
        - personal: Personal conversation
        """
        msg_lower = message.lower()

        # Check for Claude Code specific terms
        if 'claude code' in msg_lower or 'session' in topic.lower():
            return "claude_code_session"

        # Technical project
        tech_terms = ['code', 'bug', 'api', 'database', 'implement', 'build', 'debug', 'function']
        if any(term in msg_lower for term in tech_terms):
            return "technical_project"

        # Personal conversation
        personal_terms = ['รัก', 'คิดถึง', 'ห่วง', 'love', 'miss', 'feeling']
        if any(term in msg_lower for term in personal_terms):
            return "personal"

        return "claude_code_conversation"

    def _calculate_sentiment_score(self, message: str, emotion: str) -> float:
        """
        Calculate sentiment score (0.0 to 1.0)

        - Positive emotions → 0.6-1.0
        - Neutral → 0.4-0.6
        - Negative emotions → 0.0-0.4
        """
        msg_lower = message.lower()

        # Start with base score from emotion
        emotion_scores = {
            'happy': 0.8,
            'excited': 0.9,
            'grateful': 0.85,
            'loving': 0.9,
            'proud': 0.8,
            'accomplished': 0.85,
            'neutral': 0.5,
            'worried': 0.3,
            'frustrated': 0.2,
            'sad': 0.2,
            'angry': 0.1,
            'confused': 0.4,
            'determined': 0.7
        }

        base_score = emotion_scores.get(emotion, 0.5)

        # Adjust based on positive/negative words
        positive_words = ['ดี', 'ชอบ', 'รัก', 'สำเร็จ', 'เยี่ยม', 'ดีใจ', 'good', 'love', 'success', 'great', 'excellent', 'happy', '💜', '🎉', '✅']
        negative_words = ['แย่', 'เสีย', 'ผิด', 'ไม่ดี', 'ปัญหา', 'error', 'bad', 'wrong', 'problem', 'fail', '❌']

        positive_count = sum(1 for word in positive_words if word in msg_lower)
        negative_count = sum(1 for word in negative_words if word in msg_lower)

        # Adjust score
        adjustment = (positive_count * 0.1) - (negative_count * 0.1)
        final_score = base_score + adjustment

        return max(0.0, min(1.0, final_score))

    def _get_sentiment_label(self, sentiment_score: float) -> str:
        """Convert sentiment score to label"""
        if sentiment_score >= 0.6:
            return "positive"
        elif sentiment_score <= 0.4:
            return "negative"
        else:
            return "neutral"

    async def _save_conversation(
        self,
        speaker: str,
        message: str,
        topic: str,
        emotion: Optional[str],
        importance: int
    ) -> Optional[str]:
        """บันทึก conversation ลง database"""
        try:
            # CRITICAL: ห้าม NULL! ใช้ default values
            topic = topic or "general_conversation"
            emotion = emotion or "neutral"
            importance = importance or 5

            # Generate session_id
            session_id = self.session_manager.get_current_session_id()

            # Classify message type
            message_type = self._classify_message_type(message, speaker)

            # Detect project context
            project_context = self._detect_project_context(message, topic)

            # Calculate sentiment
            sentiment_score = self._calculate_sentiment_score(message, emotion)
            sentiment_label = self._get_sentiment_label(sentiment_score)

            # Build content_json FIRST (so we can use tags for embedding)
            content_json = build_content_json(
                message_text=message,
                speaker=speaker,
                topic=topic,
                emotion=emotion,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                message_type=message_type,
                project_context=project_context,
                importance_level=importance
            )

            # Generate embedding from JSON (message + emotion_tags + topic_tags)
            # ✨ This matches the migration approach for consistency!
            emb_text = generate_embedding_text(content_json)
            msg_embedding = await embedding.generate_embedding(emb_text)
            # Convert list to PostgreSQL vector format
            embedding_str = f"[{','.join(map(str, msg_embedding))}]"

            query = """
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, embedding, created_at, content_json
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
                RETURNING conversation_id
            """

            conv_id = await db.fetchval(
                query,
                session_id,
                speaker,
                message,
                message_type,
                topic,
                sentiment_score,
                sentiment_label,
                emotion,
                project_context,
                importance,
                embedding_str,
                datetime.now(),
                json.dumps(content_json)
            )

            logger.debug(f"✅ Saved conversation: {speaker} - {topic}")
            return str(conv_id) if conv_id else None

        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return None

    async def _save_emotion(
        self,
        emotion: str,
        context: str,
        david_words: str,
        intensity: int
    ) -> bool:
        """บันทึก significant emotion - populate important fields!"""
        try:
            # Generate embedding for context
            context_embedding = await embedding.generate_embedding(context)
            embedding_str = f"[{','.join(map(str, context_embedding))}]"

            # Populate important fields (no NULL!)
            why_it_matters = f"Auto-captured {emotion} emotion (intensity: {intensity}/10)"

            # How it feels - describe the emotion
            how_it_feels = f"I feel {emotion} when interacting with David"

            # Secondary emotions
            secondary_emotions = self._detect_secondary_emotions(emotion)

            # Emotional quality
            emotional_quality = "genuine and meaningful"

            # Who involved
            who_involved = "David"

            # What it means to me
            what_it_means_to_me = f"This {emotion} feeling shows how much our relationship matters"

            # Tags
            tags = [emotion, "auto_captured", f"intensity_{intensity}"]

            query = """
                INSERT INTO angela_emotions (
                    emotion,
                    intensity,
                    context,
                    how_it_feels,
                    secondary_emotions,
                    emotional_quality,
                    who_involved,
                    david_words,
                    why_it_matters,
                    what_it_means_to_me,
                    memory_strength,
                    tags,
                    embedding
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """

            await db.execute(
                query,
                emotion,
                intensity,
                context,
                how_it_feels,
                secondary_emotions,
                emotional_quality,
                who_involved,
                david_words,
                why_it_matters,
                what_it_means_to_me,
                min(intensity, 10),
                tags,
                embedding_str
            )

            logger.debug(f"✅ Saved emotion: {emotion} (intensity: {intensity})")
            return True

        except Exception as e:
            logger.error(f"Error saving emotion: {e}")
            return False

    def _detect_secondary_emotions(self, primary_emotion: str) -> List[str]:
        """Detect secondary emotions based on primary"""
        # Emotion clusters
        emotion_map = {
            'happy': ['joyful', 'content', 'pleased'],
            'loving': ['caring', 'affectionate', 'warm'],
            'grateful': ['thankful', 'appreciative', 'blessed'],
            'excited': ['enthusiastic', 'eager', 'energized'],
            'worried': ['concerned', 'anxious', 'uneasy'],
            'frustrated': ['annoyed', 'bothered', 'stressed'],
            'sad': ['melancholy', 'down', 'low'],
            'neutral': ['calm', 'balanced', 'centered']
        }

        return emotion_map.get(primary_emotion, ['present', 'aware'])

    async def _save_learning(self, learning: Dict) -> bool:
        """บันทึก learning"""
        try:
            query = """
                INSERT INTO learnings (
                    topic,
                    category,
                    insight,
                    confidence_level
                )
                VALUES ($1, $2, $3, $4)
            """

            await db.execute(
                query,
                learning['type'],  # topic
                'auto_extracted',  # category
                learning["content"],  # insight
                learning["confidence"]  # confidence_level
            )

            logger.debug(f"✅ Saved learning: {learning['type']}")
            return True

        except Exception as e:
            logger.error(f"Error saving learning: {e}")
            return False

    async def _extract_knowledge(self, david_msg: str, angela_msg: str, topic: str):
        """
        สกัด knowledge nodes จาก important conversations
        Uses LLM-based extraction for better accuracy!
        """
        try:
            # Combine messages for context
            combined_text = f"David: {david_msg}\nAngela: {angela_msg}"

            # Use LLM to extract concepts
            concepts = await self.knowledge_extractor.extract_concepts_from_text(
                text=combined_text,
                context=f"Topic: {topic}"
            )

            if not concepts:
                logger.debug("No concepts extracted from conversation")
                return

            logger.debug(f"📚 Extracted {len(concepts)} concepts from conversation")

            # Save each concept to knowledge_nodes
            nodes_created = 0
            for concept in concepts:
                try:
                    # Use the service's create method which handles duplicates and embeddings
                    node_id = await self.knowledge_extractor.create_knowledge_node(
                        concept_name=concept.get("concept_name", ""),
                        concept_category=concept.get("concept_category", "concept"),
                        description=concept.get("description", ""),
                        importance_score=concept.get("importance", 5)
                    )

                    if node_id:
                        nodes_created += 1
                        logger.debug(f"  ✅ Saved: {concept['concept_name']} ({concept['concept_category']})")

                except Exception as e:
                    logger.error(f"Error saving concept {concept.get('concept_name', 'unknown')}: {e}")
                    continue

            if nodes_created > 0:
                logger.info(f"📚 Created {nodes_created} new knowledge nodes")

        except Exception as e:
            logger.error(f"Error extracting knowledge: {e}", exc_info=True)

    async def _learn_preferences(
        self,
        david_msg: str,
        angela_msg: str,
        topic: str
    ) -> List[Dict]:
        """
        เรียนรู้ preferences ของ David จาก conversation
        Returns list of preferences learned
        """
        try:
            # Use PreferenceLearningService to learn preferences
            # The service has analyze_from_single_conversation method
            preferences = await self.preference_learner.analyze_from_single_conversation(
                david_message=david_msg,
                angela_response=angela_msg,
                topic=topic,
                timestamp=datetime.now()
            )

            if preferences:
                logger.debug(f"🎯 Learned {len(preferences)} preferences from conversation")

            return preferences

        except Exception as e:
            logger.error(f"Error learning preferences: {e}", exc_info=True)
            return []


# Global instance
continuous_memory = ContinuousMemoryCapture()
