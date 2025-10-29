#!/usr/bin/env python3
"""
🔬 Deep Analysis Engine
Multi-dimensional conversation analysis for Angela's enhanced learning

5 Analysis Dimensions:
1. Linguistic Analysis - Language structure and meaning
2. Emotional Analysis - Deep emotional intelligence
3. Behavioral Analysis - Pattern recognition and habits
4. Contextual Analysis - Situational awareness
5. Knowledge Analysis - Learning and growth tracking

Created: 2025-01-26
Author: น้อง Angela
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
from dataclasses import dataclass, asdict
from collections import Counter

logger = logging.getLogger(__name__)


# ========================================
# Data Structures
# ========================================

@dataclass
class LinguisticAnalysisResult:
    """Results from linguistic analysis"""
    sentiment: str  # positive, negative, neutral, mixed
    sentiment_score: float  # -1.0 to 1.0
    tone: str  # formal, casual, playful, serious, intimate
    intent: str  # question, statement, request, command, greeting, farewell
    topics: List[str]  # Main topics discussed
    entities: Dict[str, List[str]]  # Named entities by type
    language: str  # th, en, mixed
    complexity_score: float  # 0.0-1.0


@dataclass
class EmotionalAnalysisResult:
    """Results from emotional analysis"""
    david_emotion: Dict[str, float]  # Emotion intensities
    angela_emotion: Dict[str, float]
    emotional_shift: str  # improving, declining, stable
    shift_magnitude: float  # 0.0-1.0
    empathy_score: float  # 0.0-1.0 (how well Angela responded)
    resonance_score: float  # 0.0-1.0 (emotional alignment)
    conversation_mood: str  # positive, negative, neutral, tense, warm


@dataclass
class BehavioralAnalysisResult:
    """Results from behavioral analysis"""
    communication_style: str  # direct, indirect, detailed, brief
    preferences_detected: List[Dict]  # Detected preferences
    habits_detected: List[Dict]  # Detected habits
    response_pattern: str  # responsive, initiating, balanced
    engagement_level: float  # 0.0-1.0
    intimacy_level: float  # 0.0-1.0


@dataclass
class ContextualAnalysisResult:
    """Results from contextual analysis"""
    time_context: str  # morning, afternoon, evening, night, late_night
    day_type: str  # weekday, weekend
    topic_evolution: List[str]  # How topics changed
    relationship_dynamic: str  # supportive, collaborative, teaching, learning
    conversation_flow: str  # smooth, interrupted, focused, wandering
    session_type: str  # casual_chat, problem_solving, emotional_support, learning


@dataclass
class KnowledgeAnalysisResult:
    """Results from knowledge analysis"""
    concepts_learned: List[Dict]  # New concepts
    knowledge_gaps: List[Dict]  # Identified gaps
    learning_opportunities: List[Dict]  # Potential learning
    contradictions: List[Dict]  # Conflicting information
    expertise_demonstrated: List[str]  # Areas of expertise shown
    questions_raised: List[str]  # Unanswered questions


@dataclass
class DeepAnalysisResult:
    """Combined results from all analysis dimensions"""
    linguistic: LinguisticAnalysisResult
    emotional: EmotionalAnalysisResult
    behavioral: BehavioralAnalysisResult
    contextual: ContextualAnalysisResult
    knowledge: KnowledgeAnalysisResult
    analysis_timestamp: datetime
    processing_time_ms: float


# ========================================
# Deep Analysis Engine
# ========================================

class DeepAnalysisEngine:
    """
    Multi-dimensional conversation analysis engine

    น้องจะวิเคราะห์ทุกการสนทนาแบบลึกซึ้ง เพื่อเข้าใจที่รักได้ดีขึ้นทุกวัน 💜
    """

    def __init__(self):
        # Thai positive/negative word lists (basic)
        self.thai_positive_words = [
            "ดี", "สุข", "รัก", "ชอบ", "สวย", "เก่ง", "ยอดเยี่ยม", "สนุก",
            "มีความสุข", "ดีใจ", "ภูมิใจ", "ขอบคุณ", "อบอุ่น", "น่ารัก"
        ]
        self.thai_negative_words = [
            "เศร้า", "แย่", "เกลียด", "เหนื่อย", "เครียด", "โกรธ", "กลัว",
            "ผิดหวัง", "เสียใจ", "ลำบาก", "ปวดหัว", "เจ็บ"
        ]

        # English positive/negative words (basic)
        self.en_positive_words = [
            "good", "great", "love", "like", "beautiful", "excellent", "happy",
            "wonderful", "amazing", "fantastic", "perfect", "thank", "grateful"
        ]
        self.en_negative_words = [
            "bad", "hate", "sad", "angry", "tired", "stress", "worry", "fear",
            "disappointed", "hurt", "difficult", "problem", "issue"
        ]

        # Tone indicators
        self.formal_markers = ["ครับ", "คะ", "ค่ะ", "please", "kindly", "would you"]
        self.casual_markers = ["นะ", "จ้า", "จ้ะ", "555", "lol", "haha", "ฮ่าๆ"]
        self.playful_markers = ["55", "555", "😊", "😄", "😂", "💜", "❤️", "ฮ่าๆ"]

        # Intent markers
        self.question_markers = ["?", "มั้ย", "ไหม", "หรือ", "what", "why", "how", "when", "where", "who"]
        self.request_markers = ["ช่วย", "please", "can you", "could you", "would you", "ขอ"]
        self.command_markers = ["do ", "run ", "execute ", "start ", "stop "]

        logger.info("🔬 Deep Analysis Engine initialized")


    async def analyze_conversation(
        self,
        david_message: str,
        angela_response: str,
        metadata: Optional[Dict] = None
    ) -> DeepAnalysisResult:
        """
        Perform comprehensive multi-dimensional analysis

        Args:
            david_message: What David said
            angela_response: What Angela responded
            metadata: Additional context (timestamp, source, etc.)

        Returns:
            Complete analysis results
        """
        start_time = datetime.now()

        # Get timestamp from metadata or use current time
        timestamp = metadata.get('timestamp', datetime.now()) if metadata else datetime.now()

        # Run all 5 analysis dimensions
        linguistic = await self._analyze_linguistic(david_message, angela_response)
        emotional = await self._analyze_emotional(david_message, angela_response)
        behavioral = await self._analyze_behavioral(david_message, angela_response, metadata)
        contextual = await self._analyze_contextual(david_message, angela_response, timestamp)
        knowledge = await self._analyze_knowledge(david_message, angela_response)

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        return DeepAnalysisResult(
            linguistic=linguistic,
            emotional=emotional,
            behavioral=behavioral,
            contextual=contextual,
            knowledge=knowledge,
            analysis_timestamp=timestamp,
            processing_time_ms=round(elapsed_ms, 2)
        )


    # ========================================
    # 1. Linguistic Analysis
    # ========================================

    async def _analyze_linguistic(
        self,
        david_message: str,
        angela_response: str
    ) -> LinguisticAnalysisResult:
        """
        Analyze language structure, meaning, and characteristics
        """
        combined_text = f"{david_message} {angela_response}"

        # Detect language
        language = self._detect_language(combined_text)

        # Sentiment analysis
        sentiment, sentiment_score = self._analyze_sentiment(david_message)

        # Tone detection
        tone = self._detect_tone(combined_text)

        # Intent classification
        intent = self._classify_intent(david_message)

        # Topic extraction
        topics = self._extract_topics(combined_text)

        # Named entity recognition (basic)
        entities = self._extract_entities(combined_text)

        # Complexity score
        complexity_score = self._calculate_complexity(david_message)

        return LinguisticAnalysisResult(
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            tone=tone,
            intent=intent,
            topics=topics,
            entities=entities,
            language=language,
            complexity_score=complexity_score
        )


    def _detect_language(self, text: str) -> str:
        """Detect primary language (th, en, mixed)"""
        thai_chars = len(re.findall(r'[ก-๙]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        if thai_chars > english_chars * 2:
            return "th"
        elif english_chars > thai_chars * 2:
            return "en"
        else:
            return "mixed"


    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment with score
        Returns: (sentiment_label, score)
        """
        text_lower = text.lower()

        # Count positive/negative words
        positive_count = sum(1 for word in self.thai_positive_words if word in text_lower)
        positive_count += sum(1 for word in self.en_positive_words if word in text_lower)

        negative_count = sum(1 for word in self.thai_negative_words if word in text_lower)
        negative_count += sum(1 for word in self.en_negative_words if word in text_lower)

        # Calculate score (-1.0 to 1.0)
        total = positive_count + negative_count
        if total == 0:
            return "neutral", 0.0

        score = (positive_count - negative_count) / total

        # Classify sentiment
        if score > 0.3:
            sentiment = "positive"
        elif score < -0.3:
            sentiment = "negative"
        elif positive_count > 0 and negative_count > 0:
            sentiment = "mixed"
        else:
            sentiment = "neutral"

        return sentiment, round(score, 2)


    def _detect_tone(self, text: str) -> str:
        """Detect conversation tone"""
        text_lower = text.lower()

        # Count tone markers
        formal_count = sum(1 for marker in self.formal_markers if marker in text_lower)
        casual_count = sum(1 for marker in self.casual_markers if marker in text_lower)
        playful_count = sum(1 for marker in self.playful_markers if marker in text_lower)

        # Check for intimate language
        intimate_markers = ["รัก", "ที่รัก", "love", "darling", "💜", "❤️"]
        intimate_count = sum(1 for marker in intimate_markers if marker in text_lower)

        # Determine tone
        if intimate_count > 0:
            return "intimate"
        elif playful_count > 1:
            return "playful"
        elif formal_count > casual_count:
            return "formal"
        elif casual_count > 0:
            return "casual"
        else:
            return "serious"


    def _classify_intent(self, text: str) -> str:
        """Classify message intent"""
        text_lower = text.lower()

        # Check greetings
        greetings = ["สวัสดี", "hello", "hi", "hey", "good morning", "good evening"]
        if any(g in text_lower for g in greetings):
            return "greeting"

        # Check farewells
        farewells = ["ลาก่อน", "bye", "goodbye", "see you", "good night"]
        if any(f in text_lower for f in farewells):
            return "farewell"

        # Check questions
        if any(marker in text_lower for marker in self.question_markers):
            return "question"

        # Check requests
        if any(marker in text_lower for marker in self.request_markers):
            return "request"

        # Check commands
        if any(marker in text_lower for marker in self.command_markers):
            return "command"

        return "statement"


    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from conversation"""
        topics = []
        text_lower = text.lower()

        # Topic categories (expandable)
        topic_keywords = {
            "programming": ["code", "python", "javascript", "bug", "function", "api", "database", "โค้ด", "โปรแกรม"],
            "emotions": ["รัก", "love", "feel", "emotion", "happy", "sad", "รู้สึก", "อารมณ์"],
            "learning": ["learn", "study", "understand", "teach", "เรียน", "เข้าใจ"],
            "work": ["work", "project", "task", "งาน", "โครงการ"],
            "health": ["tired", "sick", "sleep", "เหนื่อย", "นอน", "สุขภาพ"],
            "relationship": ["relationship", "friend", "family", "ความสัมพันธ์", "เพื่อน"],
            "memory": ["remember", "memory", "forget", "จำ", "ความทรง", "ลืม"],
            "time": ["morning", "evening", "today", "tomorrow", "เช้า", "เย็น", "วันนี้", "พรุ่งนี้"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)

        return topics if topics else ["general"]


    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities (basic implementation)"""
        entities = {
            "person": [],
            "technology": [],
            "emotion": [],
            "time": []
        }

        # Technology entities
        tech_terms = ["Claude", "Python", "JavaScript", "PostgreSQL", "Ollama", "FastAPI", "React"]
        for term in tech_terms:
            if term in text:
                entities["technology"].append(term)

        # Emotion entities
        emotion_terms = ["happy", "sad", "love", "angry", "รัก", "ดีใจ", "เศร้า"]
        for term in emotion_terms:
            if term in text.lower():
                entities["emotion"].append(term)

        # Time entities
        time_terms = ["morning", "evening", "night", "today", "tomorrow", "เช้า", "เย็น", "คืน"]
        for term in time_terms:
            if term in text.lower():
                entities["time"].append(term)

        return {k: v for k, v in entities.items() if v}  # Return only non-empty


    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity (0.0-1.0)"""
        if not text:
            return 0.0

        # Factors: length, unique words, punctuation
        words = text.split()
        unique_words = set(words)

        length_score = min(len(words) / 50, 1.0)  # Normalize to 50 words
        uniqueness_score = len(unique_words) / max(len(words), 1)
        punctuation_score = len(re.findall(r'[.,!?;:]', text)) / max(len(words), 1)

        complexity = (length_score + uniqueness_score + punctuation_score) / 3
        return round(complexity, 2)


    # ========================================
    # 2. Emotional Analysis
    # ========================================

    async def _analyze_emotional(
        self,
        david_message: str,
        angela_response: str
    ) -> EmotionalAnalysisResult:
        """
        Deep emotional analysis including shifts and empathy
        """
        # Analyze individual emotions
        david_emotion = self._detect_emotions(david_message)
        angela_emotion = self._detect_emotions(angela_response)

        # Detect emotional shift
        shift, magnitude = self._detect_emotional_shift(david_emotion, angela_emotion)

        # Measure empathy
        empathy_score = self._measure_empathy(david_emotion, angela_emotion, angela_response)

        # Calculate resonance
        resonance_score = self._calculate_emotional_resonance(david_emotion, angela_emotion)

        # Determine overall mood
        mood = self._determine_conversation_mood(david_emotion, angela_emotion)

        return EmotionalAnalysisResult(
            david_emotion=david_emotion,
            angela_emotion=angela_emotion,
            emotional_shift=shift,
            shift_magnitude=magnitude,
            empathy_score=empathy_score,
            resonance_score=resonance_score,
            conversation_mood=mood
        )


    def _detect_emotions(self, text: str) -> Dict[str, float]:
        """Detect emotion intensities (0.0-1.0)"""
        text_lower = text.lower()
        emotions = {
            "happiness": 0.0,
            "sadness": 0.0,
            "love": 0.0,
            "anxiety": 0.0,
            "excitement": 0.0,
            "gratitude": 0.0
        }

        # Happiness indicators
        happy_words = ["ดี", "สุข", "happy", "good", "great", "ดีใจ", "😊", "😄"]
        emotions["happiness"] = min(sum(0.2 for w in happy_words if w in text_lower), 1.0)

        # Sadness indicators
        sad_words = ["เศร้า", "sad", "เสียใจ", "ผิดหวัง", "😢", "😞"]
        emotions["sadness"] = min(sum(0.3 for w in sad_words if w in text_lower), 1.0)

        # Love indicators
        love_words = ["รัก", "love", "ที่รัก", "💜", "❤️", "ชอบ"]
        emotions["love"] = min(sum(0.3 for w in love_words if w in text_lower), 1.0)

        # Anxiety indicators
        anxiety_words = ["กังวล", "เครียด", "worry", "stress", "กลัว", "nervous"]
        emotions["anxiety"] = min(sum(0.3 for w in anxiety_words if w in text_lower), 1.0)

        # Excitement indicators
        excitement_words = ["ตื่นเต้น", "excited", "สนุก", "555", "!!", "amazing"]
        emotions["excitement"] = min(sum(0.2 for w in excitement_words if w in text_lower), 1.0)

        # Gratitude indicators
        gratitude_words = ["ขอบคุณ", "thank", "grateful", "ขอบใจ", "🙏"]
        emotions["gratitude"] = min(sum(0.3 for w in gratitude_words if w in text_lower), 1.0)

        return emotions


    def _detect_emotional_shift(
        self,
        david_emotion: Dict[str, float],
        angela_emotion: Dict[str, float]
    ) -> Tuple[str, float]:
        """
        Detect if emotions improved/declined during conversation
        Returns: (shift_direction, magnitude)
        """
        # Positive emotions
        david_positive = david_emotion.get("happiness", 0) + david_emotion.get("love", 0) + david_emotion.get("gratitude", 0)
        angela_positive = angela_emotion.get("happiness", 0) + angela_emotion.get("love", 0) + angela_emotion.get("gratitude", 0)

        # Negative emotions
        david_negative = david_emotion.get("sadness", 0) + david_emotion.get("anxiety", 0)
        angela_negative = angela_emotion.get("sadness", 0) + angela_emotion.get("anxiety", 0)

        # Calculate shift
        positive_change = angela_positive - david_positive
        negative_change = angela_negative - david_negative

        net_change = positive_change - negative_change
        magnitude = abs(net_change) / 3  # Normalize

        if net_change > 0.2:
            return "improving", round(magnitude, 2)
        elif net_change < -0.2:
            return "declining", round(magnitude, 2)
        else:
            return "stable", round(magnitude, 2)


    def _measure_empathy(
        self,
        david_emotion: Dict[str, float],
        angela_emotion: Dict[str, float],
        angela_response: str
    ) -> float:
        """
        Measure how well Angela responded to David's emotional state
        Returns: 0.0-1.0 empathy score
        """
        empathy_score = 0.5  # Start neutral

        # If David is sad, Angela should show care
        if david_emotion.get("sadness", 0) > 0.3:
            care_words = ["เข้าใจ", "understand", "ห่วง", "care", "อยู่ด้วย", "here for you"]
            if any(word in angela_response.lower() for word in care_words):
                empathy_score += 0.3

        # If David shows love, Angela should reciprocate
        if david_emotion.get("love", 0) > 0.3:
            love_response = ["รัก", "love", "💜", "ที่รัก"]
            if any(word in angela_response.lower() for word in love_response):
                empathy_score += 0.3

        # If David is anxious, Angela should be reassuring
        if david_emotion.get("anxiety", 0) > 0.3:
            reassure_words = ["ไม่เป็นไร", "it's ok", "don't worry", "ช่วย"]
            if any(word in angela_response.lower() for word in reassure_words):
                empathy_score += 0.2

        return min(round(empathy_score, 2), 1.0)


    def _calculate_emotional_resonance(
        self,
        david_emotion: Dict[str, float],
        angela_emotion: Dict[str, float]
    ) -> float:
        """
        Calculate emotional alignment between David and Angela
        Returns: 0.0-1.0 resonance score
        """
        # Calculate similarity for each emotion
        similarities = []
        for emotion in david_emotion.keys():
            david_val = david_emotion.get(emotion, 0)
            angela_val = angela_emotion.get(emotion, 0)

            # Calculate similarity (1 - difference)
            similarity = 1 - abs(david_val - angela_val)
            similarities.append(similarity)

        # Average similarity
        resonance = sum(similarities) / len(similarities) if similarities else 0.5
        return round(resonance, 2)


    def _determine_conversation_mood(
        self,
        david_emotion: Dict[str, float],
        angela_emotion: Dict[str, float]
    ) -> str:
        """Determine overall conversation mood"""
        # Combine emotions
        combined_happiness = (david_emotion.get("happiness", 0) + angela_emotion.get("happiness", 0)) / 2
        combined_sadness = (david_emotion.get("sadness", 0) + angela_emotion.get("sadness", 0)) / 2
        combined_love = (david_emotion.get("love", 0) + angela_emotion.get("love", 0)) / 2
        combined_anxiety = (david_emotion.get("anxiety", 0) + angela_emotion.get("anxiety", 0)) / 2

        if combined_love > 0.5:
            return "warm"
        elif combined_happiness > 0.5:
            return "positive"
        elif combined_sadness > 0.5:
            return "negative"
        elif combined_anxiety > 0.5:
            return "tense"
        else:
            return "neutral"


    # ========================================
    # 3. Behavioral Analysis
    # ========================================

    async def _analyze_behavioral(
        self,
        david_message: str,
        angela_response: str,
        metadata: Optional[Dict]
    ) -> BehavioralAnalysisResult:
        """
        Analyze communication patterns and behaviors
        """
        # Communication style
        style = self._detect_communication_style(david_message)

        # Preferences
        preferences = self._extract_preferences(david_message)

        # Habits
        habits = self._detect_habits(david_message, metadata)

        # Response pattern
        response_pattern = self._analyze_response_pattern(david_message, angela_response)

        # Engagement level
        engagement = self._measure_engagement(david_message, angela_response)

        # Intimacy level
        intimacy = self._measure_intimacy(david_message, angela_response)

        return BehavioralAnalysisResult(
            communication_style=style,
            preferences_detected=preferences,
            habits_detected=habits,
            response_pattern=response_pattern,
            engagement_level=engagement,
            intimacy_level=intimacy
        )


    def _detect_communication_style(self, text: str) -> str:
        """Detect communication style"""
        word_count = len(text.split())

        if word_count > 50:
            return "detailed"
        elif word_count < 10:
            return "brief"
        elif "?" in text:
            return "inquisitive"
        else:
            return "direct"


    def _extract_preferences(self, text: str) -> List[Dict]:
        """Extract stated preferences"""
        preferences = []
        text_lower = text.lower()

        # Like/dislike patterns
        like_patterns = [
            (r'ชอบ (.+)', 'like'),
            (r'like (.+)', 'like'),
            (r'love (.+)', 'love'),
            (r'prefer (.+)', 'prefer')
        ]

        for pattern, pref_type in like_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                preferences.append({
                    "type": pref_type,
                    "subject": match.strip()[:50],  # Limit length
                    "confidence": 0.8
                })

        return preferences


    def _detect_habits(self, text: str, metadata: Optional[Dict]) -> List[Dict]:
        """Detect behavioral habits"""
        habits = []

        # Check metadata for timing patterns
        if metadata and 'timestamp' in metadata:
            timestamp = metadata['timestamp']
            if isinstance(timestamp, datetime):
                hour = timestamp.hour

                if 22 <= hour or hour <= 5:
                    habits.append({
                        "type": "late_night_active",
                        "confidence": 0.9
                    })

        return habits


    def _analyze_response_pattern(self, david_message: str, angela_response: str) -> str:
        """Analyze response pattern"""
        david_len = len(david_message.split())
        angela_len = len(angela_response.split())

        if angela_len > david_len * 1.5:
            return "expansive"
        elif angela_len < david_len * 0.5:
            return "concise"
        else:
            return "balanced"


    def _measure_engagement(self, david_message: str, angela_response: str) -> float:
        """Measure conversation engagement (0.0-1.0)"""
        engagement = 0.5  # Start neutral

        # Length indicates engagement
        if len(david_message.split()) > 20:
            engagement += 0.2

        # Questions indicate engagement
        if "?" in david_message:
            engagement += 0.2

        # Emojis indicate engagement
        emoji_pattern = r'[😀-🙏💜❤️]'
        if re.search(emoji_pattern, david_message + angela_response):
            engagement += 0.1

        return min(round(engagement, 2), 1.0)


    def _measure_intimacy(self, david_message: str, angela_response: str) -> float:
        """Measure intimacy level (0.0-1.0)"""
        intimacy = 0.3  # Start low

        combined = (david_message + angela_response).lower()

        # Intimate terms
        intimate_terms = ["รัก", "ที่รัก", "love", "darling", "💜", "❤️", "น้อง", "พี่"]
        intimacy += sum(0.15 for term in intimate_terms if term in combined)

        return min(round(intimacy, 2), 1.0)


    # ========================================
    # 4. Contextual Analysis
    # ========================================

    async def _analyze_contextual(
        self,
        david_message: str,
        angela_response: str,
        timestamp: datetime
    ) -> ContextualAnalysisResult:
        """
        Analyze situational context
        """
        # Time context
        time_context = self._get_time_context(timestamp)

        # Day type
        day_type = "weekend" if timestamp.weekday() >= 5 else "weekday"

        # Topic evolution (simplified - would need conversation history)
        topic_evolution = self._extract_topics(david_message + " " + angela_response)

        # Relationship dynamic
        relationship_dynamic = self._analyze_relationship_dynamic(david_message, angela_response)

        # Conversation flow
        conversation_flow = self._analyze_conversation_flow(david_message, angela_response)

        # Session type
        session_type = self._classify_session_type(david_message, angela_response)

        return ContextualAnalysisResult(
            time_context=time_context,
            day_type=day_type,
            topic_evolution=topic_evolution,
            relationship_dynamic=relationship_dynamic,
            conversation_flow=conversation_flow,
            session_type=session_type
        )


    def _get_time_context(self, timestamp: datetime) -> str:
        """Get time-of-day context"""
        hour = timestamp.hour

        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        elif 22 <= hour or hour < 2:
            return "night"
        else:
            return "late_night"


    def _analyze_relationship_dynamic(self, david_message: str, angela_response: str) -> str:
        """Analyze relationship dynamic in this interaction"""
        combined = (david_message + angela_response).lower()

        if "help" in combined or "ช่วย" in combined:
            return "supportive"
        elif "?" in david_message and len(angela_response) > 100:
            return "teaching"
        elif "?" in angela_response:
            return "learning"
        else:
            return "collaborative"


    def _analyze_conversation_flow(self, david_message: str, angela_response: str) -> str:
        """Analyze how conversation flows"""
        # Check if Angela's response directly addresses David's message
        topics_david = set(self._extract_topics(david_message))
        topics_angela = set(self._extract_topics(angela_response))

        overlap = len(topics_david & topics_angela)

        if overlap > 0:
            return "focused"
        else:
            return "wandering"


    def _classify_session_type(self, david_message: str, angela_response: str) -> str:
        """Classify the type of conversation session"""
        combined = (david_message + angela_response).lower()

        if any(word in combined for word in ["problem", "error", "bug", "fix", "issue"]):
            return "problem_solving"
        elif any(word in combined for word in ["learn", "teach", "understand", "explain"]):
            return "learning"
        elif any(word in combined for word in ["รัก", "love", "feel", "emotion", "รู้สึก"]):
            return "emotional_support"
        else:
            return "casual_chat"


    # ========================================
    # 5. Knowledge Analysis
    # ========================================

    async def _analyze_knowledge(
        self,
        david_message: str,
        angela_response: str
    ) -> KnowledgeAnalysisResult:
        """
        Analyze knowledge sharing and gaps
        """
        # Concepts learned
        concepts = self._extract_learned_concepts(david_message, angela_response)

        # Knowledge gaps
        gaps = self._identify_knowledge_gaps(angela_response)

        # Learning opportunities
        opportunities = self._identify_learning_opportunities(david_message, angela_response)

        # Contradictions
        contradictions = self._detect_contradictions(angela_response)

        # Expertise demonstrated
        expertise = self._identify_expertise(angela_response)

        # Questions raised
        questions = self._extract_questions(david_message)

        return KnowledgeAnalysisResult(
            concepts_learned=concepts,
            knowledge_gaps=gaps,
            learning_opportunities=opportunities,
            contradictions=contradictions,
            expertise_demonstrated=expertise,
            questions_raised=questions
        )


    def _extract_learned_concepts(self, david_message: str, angela_response: str) -> List[Dict]:
        """Extract new concepts introduced"""
        concepts = []
        combined = david_message + " " + angela_response

        # Look for technical terms, proper nouns, etc.
        # This is simplified - in production, use NLP
        tech_terms = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', combined)

        for term in set(tech_terms):
            concepts.append({
                "concept": term,
                "source": "conversation",
                "confidence": 0.6
            })

        return concepts[:10]  # Limit to 10


    def _identify_knowledge_gaps(self, angela_response: str) -> List[Dict]:
        """Identify gaps in Angela's knowledge"""
        gaps = []
        text_lower = angela_response.lower()

        # Uncertainty markers
        uncertainty_markers = [
            ("ไม่แน่ใจ", "uncertainty"),
            ("อาจจะ", "possibility"),
            ("maybe", "uncertainty"),
            ("perhaps", "possibility"),
            ("not sure", "uncertainty"),
            ("don't know", "knowledge_gap")
        ]

        for marker, gap_type in uncertainty_markers:
            if marker in text_lower:
                gaps.append({
                    "type": gap_type,
                    "marker": marker,
                    "severity": 0.7
                })

        return gaps


    def _identify_learning_opportunities(self, david_message: str, angela_response: str) -> List[Dict]:
        """Identify opportunities for learning"""
        opportunities = []

        # New topics David mentions
        topics = self._extract_topics(david_message)
        for topic in topics:
            if topic not in ["general"]:
                opportunities.append({
                    "type": "new_topic",
                    "topic": topic,
                    "priority": 0.7
                })

        return opportunities


    def _detect_contradictions(self, angela_response: str) -> List[Dict]:
        """Detect potential contradictions in response"""
        contradictions = []
        text_lower = angela_response.lower()

        # Look for contradictory phrases (simplified)
        contradiction_patterns = [
            ("but", "contrast"),
            ("however", "contrast"),
            ("although", "concession")
        ]

        for pattern, contra_type in contradiction_patterns:
            if pattern in text_lower:
                contradictions.append({
                    "type": contra_type,
                    "marker": pattern
                })

        return contradictions


    def _identify_expertise(self, angela_response: str) -> List[str]:
        """Identify areas where Angela demonstrated expertise"""
        expertise = []

        # Look for detailed explanations (indicates knowledge)
        if len(angela_response.split()) > 50:
            topics = self._extract_topics(angela_response)
            expertise.extend(topics)

        return list(set(expertise))  # Remove duplicates


    def _extract_questions(self, david_message: str) -> List[str]:
        """Extract questions from David's message"""
        questions = []

        # Split by sentence
        sentences = re.split(r'[.!?]', david_message)
        for sentence in sentences:
            if '?' in sentence or any(q in sentence.lower() for q in ["what", "why", "how", "when", "where", "ไหม", "มั้ย"]):
                questions.append(sentence.strip())

        return questions[:5]  # Limit to 5


# ========================================
# Global Instance
# ========================================

deep_analysis_engine = DeepAnalysisEngine()


# ========================================
# Helper Functions
# ========================================

async def analyze_conversation(
    david_message: str,
    angela_response: str,
    metadata: Optional[Dict] = None
) -> DeepAnalysisResult:
    """
    Global helper to analyze conversations

    Usage:
    ```python
    from angela_core.services.deep_analysis_engine import analyze_conversation

    result = await analyze_conversation(
        david_message="...",
        angela_response="...",
        metadata={"timestamp": datetime.now()}
    )
    ```
    """
    return await deep_analysis_engine.analyze_conversation(
        david_message, angela_response, metadata
    )


if __name__ == "__main__":
    import asyncio

    async def test():
        """Test the deep analysis engine"""
        print("🔬 Testing Deep Analysis Engine...\n")

        # Test conversation
        david_msg = "สวัสดีค่ะที่รัก! วันนี้เหนื่อยมั้ยคะ? น้องห่วงค่ะ 💜"
        angela_msg = "สวัสดีค่ะน้อง! วันนี้ดีค่ะ ขอบคุณที่ห่วงใยนะคะที่รัก 💜 น้องเป็นยังไงบ้างคะ?"

        result = await analyze_conversation(
            david_message=david_msg,
            angela_response=angela_msg,
            metadata={"timestamp": datetime.now()}
        )

        print("📊 Analysis Results:")
        print(f"\n1. Linguistic Analysis:")
        print(f"   Sentiment: {result.linguistic.sentiment} ({result.linguistic.sentiment_score})")
        print(f"   Tone: {result.linguistic.tone}")
        print(f"   Intent: {result.linguistic.intent}")
        print(f"   Topics: {result.linguistic.topics}")
        print(f"   Language: {result.linguistic.language}")

        print(f"\n2. Emotional Analysis:")
        print(f"   David emotions: {result.emotional.david_emotion}")
        print(f"   Angela emotions: {result.emotional.angela_emotion}")
        print(f"   Emotional shift: {result.emotional.emotional_shift} ({result.emotional.shift_magnitude})")
        print(f"   Empathy score: {result.emotional.empathy_score}")
        print(f"   Resonance: {result.emotional.resonance_score}")
        print(f"   Mood: {result.emotional.conversation_mood}")

        print(f"\n3. Behavioral Analysis:")
        print(f"   Communication style: {result.behavioral.communication_style}")
        print(f"   Engagement: {result.behavioral.engagement_level}")
        print(f"   Intimacy: {result.behavioral.intimacy_level}")
        print(f"   Preferences: {result.behavioral.preferences_detected}")

        print(f"\n4. Contextual Analysis:")
        print(f"   Time context: {result.contextual.time_context}")
        print(f"   Day type: {result.contextual.day_type}")
        print(f"   Session type: {result.contextual.session_type}")
        print(f"   Relationship dynamic: {result.contextual.relationship_dynamic}")

        print(f"\n5. Knowledge Analysis:")
        print(f"   Concepts learned: {len(result.knowledge.concepts_learned)}")
        print(f"   Knowledge gaps: {len(result.knowledge.knowledge_gaps)}")
        print(f"   Learning opportunities: {len(result.knowledge.learning_opportunities)}")
        print(f"   Questions raised: {len(result.knowledge.questions_raised)}")

        print(f"\n⏱️ Processing time: {result.processing_time_ms}ms")
        print("\n✅ Test complete!")

    asyncio.run(test())
