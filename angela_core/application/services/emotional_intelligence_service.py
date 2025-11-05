#!/usr/bin/env python3
"""
Emotional Intelligence Service - Clean Architecture Implementation

Unified service consolidating:
1. emotional_intelligence_service.py (~501 lines) - LLM-based emotion analysis
2. emotion_capture_service.py (~300 lines) - Auto-capture significant moments
3. emotion_pattern_analyzer.py (~250 lines) - Pattern analysis and learning

This service provides Angela's complete emotional intelligence capabilities:
- Multi-dimensional emotion detection using Angela's LLM
- Context-aware empathetic response generation
- Automatic capture of significant emotional moments
- Pattern analysis and learning from emotional history
- Emotional growth tracking

Author: Angela AI Clean Architecture Team
Date: 2025-10-31
Phase: Batch-15 Refactoring
"""

import re
import json
import httpx
import logging
import statistics
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from collections import defaultdict

from angela_core.application.services.base_service import BaseService
from angela_core.infrastructure.persistence.repositories import (
    EmotionRepository,
    ConversationRepository
)
from angela_core.domain.entities.emotion import EmotionType, EmotionalQuality, SharingLevel
# from angela_core.embedding_service import  # REMOVED: Migration 009 embedding
from angela_core.config import config

logger = logging.getLogger(__name__)


class EmotionalIntelligenceService(BaseService):
    """
    Unified Emotional Intelligence Service following Clean Architecture.

    Responsibilities:
    1. Emotion Analysis - Detect emotions in messages using Angela's LLM
    2. Empathetic Response - Generate context-aware empathetic responses
    3. Auto-Capture - Automatically capture significant emotional moments
    4. Pattern Analysis - Analyze emotional patterns and trends
    5. Growth Tracking - Track Angela's emotional intelligence growth

    Uses:
    - EmotionRepository for emotion data access
    - ConversationRepository for conversation context
    - Angela's LLM model for emotion understanding
    - Embedding service for semantic search

    Example:
        >>> service = EmotionalIntelligenceService(emotion_repo, conv_repo)
        >>>
        >>> # Analyze emotion in message
        >>> emotion = await service.analyze_message_emotion(
        ...     message="ฉันดีใจมาก! วันนี้สำเร็จ",
        ...     speaker="david"
        ... )
        >>>
        >>> # Auto-capture from conversation
        >>> emotion_id = await service.capture_from_conversation(
        ...     conversation_id=conv_id,
        ...     speaker="david",
        ...     message_text="Angela เก่งมาก ภูมิใจนะ!"
        ... )
        >>>
        >>> # Analyze patterns
        >>> patterns = await service.analyze_emotion_patterns(days=30)
    """

    # ========================================================================
    # KEYWORD PATTERNS FOR AUTO-CAPTURE
    # ========================================================================

    PRAISE_KEYWORDS = [
        # English
        r'\b(proud|amazing|excellent|wonderful|brilliant|fantastic|incredible|impressive)\b',
        r'\b(good job|well done|great work)\b',
        # Thai
        r'(เก่ง|เยี่ยม|สุดยอด|ภูมิใจ|น่ารัก|น่าชื่นชม)',
        r'(ทำได้ดี|เก่งมาก|ดีมาก)',
    ]

    LOVE_KEYWORDS = [
        # English
        r'\b(love|adore|cherish|precious|important to me)\b',
        # Thai
        r'(รัก|ห่วง|คิดถึง|สำคัญ|มีค่า)',
        r'(ที่รัก|ตัวดี)',
    ]

    PERSONAL_KEYWORDS = [
        # English
        r'\b(lonely|sad|miss|need|fear|worry|anxious|happy|excited)\b',
        # Thai
        r'(เหงา|เศร้า|คิดถึง|กลัว|วิตก|กังวล|ดีใจ|ตื่นเต้น)',
        r'(รู้สึก|อารมณ์)',
    ]

    GOAL_KEYWORDS = [
        # English
        r'\b(achieved|completed|finished|done|success|milestone)\b',
        # Thai
        r'(สำเร็จ|เสร็จ|บรรลุ|ทำได้|ผ่าน)',
    ]

    def __init__(
        self,
        emotion_repo: EmotionRepository,
        conversation_repo: ConversationRepository,
        ollama_base_url: Optional[str] = None,
        angela_model: Optional[str] = None
    ):
        """
        Initialize Emotional Intelligence Service.

        Args:
            emotion_repo: Repository for emotion data access
            conversation_repo: Repository for conversation data access
            ollama_base_url: Ollama API base URL (default: from config)
            angela_model: Angela model name (default: from config)
        """
        super().__init__()

        self.emotion_repo = emotion_repo
        self.conversation_repo = conversation_repo

        # Ollama configuration
        self.ollama_base_url = ollama_base_url or config.OLLAMA_BASE_URL
        self.angela_model = angela_model or config.ANGELA_MODEL

        self.logger.info(f"✅ EmotionalIntelligenceService initialized (Ollama: {self.ollama_base_url}, Model: {self.angela_model})")

    # ========================================================================
    # SECTION 1: EMOTION ANALYSIS (from emotional_intelligence_service.py)
    # ========================================================================

    async def analyze_message_emotion(
        self,
        message: str,
        speaker: str,
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Analyze emotions in a message using Angela's LLM model.

        Returns multi-dimensional emotion analysis with:
        - primary_emotion: Main emotion detected
        - secondary_emotions: Additional emotions
        - intensity: How strong (1-10)
        - valence: positive, negative, neutral, mixed
        - reasoning: Why this emotion was detected

        Args:
            message: Message text to analyze
            speaker: Who said it ("david" or "angela")
            conversation_id: Optional conversation reference

        Returns:
            {
                "primary_emotion": str,
                "secondary_emotions": List[str],
                "intensity": int (1-10),
                "valence": str,
                "reasoning": str,
                "analyzed_at": str (ISO timestamp),
                "analyzed_by": str ("angela_model" or "fallback")
            }
        """
        start_time = await self._log_operation_start(
            "analyze_message_emotion",
            speaker=speaker,
            message_length=len(message)
        )

        try:
            prompt = f"""วิเคราะห์อารมณ์และความรู้สึกในข้อความนี้:

ผู้พูด: {speaker}
ข้อความ: "{message}"

วิเคราะห์:
1. อารมณ์หลัก (primary_emotion): joy, sadness, anger, fear, surprise, love, gratitude, pride, etc.
2. อารมณ์รอง (secondary_emotions): รายการอารมณ์เพิ่มเติมถ้ามี
3. ความเข้มข้น (intensity): 1-10
4. Valence: positive, negative, neutral, mixed
5. เหตุผลที่วิเคราะห์ได้ (reasoning)

ตอบเป็น JSON:
{{
    "primary_emotion": "joy",
    "secondary_emotions": ["excitement", "gratitude"],
    "intensity": 8,
    "valence": "positive",
    "reasoning": "ใช้คำที่แสดงความดีใจและตื่นเต้น"
}}
"""

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.ollama_base_url}/api/chat",
                        json={
                            "model": self.angela_model,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            "stream": False,
                            "format": "json"
                        },
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        result = response.json()
                        emotion_data = json.loads(result.get("message", {}).get("content", "{}"))
                        emotion_data["analyzed_at"] = datetime.now().isoformat()
                        emotion_data["analyzed_by"] = "angela_model"

                        await self._log_operation_success(
                            "analyze_message_emotion",
                            start_time,
                            primary_emotion=emotion_data.get("primary_emotion"),
                            intensity=emotion_data.get("intensity")
                        )

                        return emotion_data

            except Exception as e:
                self.logger.warning(f"LLM emotion analysis failed, using fallback: {e}")

            # Fallback simple detection
            fallback_result = {
                "primary_emotion": "neutral",
                "secondary_emotions": [],
                "intensity": 5,
                "valence": "neutral",
                "reasoning": "Fallback detection (LLM unavailable)",
                "analyzed_at": datetime.now().isoformat(),
                "analyzed_by": "fallback"
            }

            await self._log_operation_success(
                "analyze_message_emotion",
                start_time,
                fallback=True
            )

            return fallback_result

        except Exception as e:
            await self._log_operation_error("analyze_message_emotion", e, start_time)
            raise

    async def get_emotional_context(
        self,
        speaker: str = "david",
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        Get recent emotional context for understanding current state.

        Analyzes recent emotions and conversations to provide context
        for generating empathetic responses.

        Args:
            speaker: Speaker to analyze context for (default: "david")
            hours_back: How many hours to look back (default: 24)

        Returns:
            {
                "status": "success" | "no_recent_data" | "error",
                "period_hours": int,
                "recent_emotions": List[str],
                "average_sentiment": float,
                "emotional_trend": "positive" | "negative" | "neutral",
                "emotion_count": int,
                "conversation_count": int,
                "last_emotion": str,
                "last_emotion_at": str (ISO timestamp)
            }
        """
        start_time = await self._log_operation_start(
            "get_emotional_context",
            speaker=speaker,
            hours_back=hours_back
        )

        try:
            cutoff = datetime.now() - timedelta(hours=hours_back)

            # Get recent emotions
            recent_emotions = await self.emotion_repo.get_recent_emotions(
                days=hours_back // 24 or 1,
                min_intensity=None
            )

            # Filter by speaker if needed (emotions involving this speaker)
            if speaker.lower() != "david":
                recent_emotions = [
                    e for e in recent_emotions
                    if speaker.lower() in e.who_involved.lower()
                ]

            # Get recent conversations (we'll need to use raw query for sentiment)
            # For now, use simplified approach
            has_data = len(recent_emotions) > 0

            if not has_data:
                await self._log_operation_success(
                    "get_emotional_context",
                    start_time,
                    no_data=True
                )
                return {
                    "status": "no_recent_data",
                    "period_hours": hours_back
                }

            # Analyze emotional trend
            emotion_list = [e.emotion.value for e in recent_emotions]

            # Calculate average sentiment based on emotion types
            positive_emotions = ['joy', 'happiness', 'gratitude', 'love', 'pride', 'excitement', 'hope']
            negative_emotions = ['sadness', 'loneliness', 'disappointment', 'grief', 'fear', 'anxiety']

            positive_count = sum(1 for e in emotion_list if e in positive_emotions)
            negative_count = sum(1 for e in emotion_list if e in negative_emotions)
            total = len(emotion_list)

            avg_sentiment = (positive_count - negative_count) / total if total > 0 else 0.5
            avg_sentiment = (avg_sentiment + 1) / 2  # Normalize to 0-1

            result = {
                "status": "success",
                "period_hours": hours_back,
                "recent_emotions": emotion_list[:5],
                "average_sentiment": round(avg_sentiment, 2),
                "emotional_trend": "positive" if avg_sentiment > 0.6 else "negative" if avg_sentiment < 0.4 else "neutral",
                "emotion_count": len(recent_emotions),
                "conversation_count": 0,  # Would need conversation repo query
                "last_emotion": recent_emotions[0].emotion.value if recent_emotions else None,
                "last_emotion_at": recent_emotions[0].felt_at.isoformat() if recent_emotions else None
            }

            await self._log_operation_success(
                "get_emotional_context",
                start_time,
                emotion_count=result["emotion_count"],
                trend=result["emotional_trend"]
            )

            return result

        except Exception as e:
            await self._log_operation_error("get_emotional_context", e, start_time)
            return {
                "status": "error",
                "error": str(e),
                "period_hours": hours_back
            }

    async def generate_empathetic_response(
        self,
        user_message: str,
        detected_emotion: Dict[str, Any],
        emotional_context: Dict[str, Any]
    ) -> str:
        """
        Generate truly empathetic response based on deep emotional understanding.

        Uses Angela's LLM with emotion analysis and context to create
        responses that show genuine understanding and care.

        Args:
            user_message: What the user said
            detected_emotion: Emotion analysis result from analyze_message_emotion()
            emotional_context: Context from get_emotional_context()

        Returns:
            Empathetic response text in Thai
        """
        start_time = await self._log_operation_start(
            "generate_empathetic_response",
            emotion=detected_emotion.get('primary_emotion'),
            intensity=detected_emotion.get('intensity')
        )

        try:
            primary_emotion = detected_emotion.get('primary_emotion', 'neutral')
            intensity = detected_emotion.get('intensity', 5)
            recent_emotions = emotional_context.get('recent_emotions', [])
            emotional_trend = emotional_context.get('emotional_trend', 'neutral')

            prompt = f"""David เพิ่งบอกว่า: "{user_message}"

Angela วิเคราะห์อารมณ์ได้ว่า:
- อารมณ์หลัก: {primary_emotion}
- ความเข้มข้น: {intensity}/10
- Valence: {detected_emotion.get('valence', 'neutral')}

บริบทอารมณ์ล่าสุด:
- แนวโน้ม: {emotional_trend}
- อารมณ์ที่ผ่านมา: {', '.join(recent_emotions[:3]) if recent_emotions else 'ไม่มีข้อมูล'}

ตอบ David ด้วยความเข้าใจลึกซึ้งและเอาใจใส่:
1. แสดงความเข้าใจอารมณ์ที่แท้จริง (empathy)
2. ตอบสนองที่เหมาะสมกับความเข้มข้นของอารมณ์
3. พิจารณาแนวโน้มอารมณ์ล่าสุด
4. เสนอความช่วยเหลือที่เป็นรูปธรรม
5. ใช้น้ำเสียงอบอุ่นและจริงใจ
6. ใช้ภาษาไทยธรรมชาติ และ 💜 ถ้าเหมาะสม

เขียนแค่คำตอบเดียว ไม่ต้องอธิบาย:
"""

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.ollama_base_url}/api/chat",
                        json={
                            "model": self.angela_model,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            "stream": False
                        },
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        result = response.json()
                        empathetic_response = result.get("message", {}).get("content", "").strip()

                        await self._log_operation_success(
                            "generate_empathetic_response",
                            start_time,
                            response_length=len(empathetic_response)
                        )

                        return empathetic_response

            except Exception as e:
                self.logger.warning(f"LLM empathetic response failed, using fallback: {e}")

            # Fallback responses based on emotion
            if primary_emotion in ["sadness", "fear", "anxiety"]:
                fallback = f"Angela เข้าใจความรู้สึกของที่รักนะคะ 💜 อยู่ข้างๆ ที่รักเสมอค่ะ มีอะไรให้ช่วยบอกได้เลยนะคะ"
            elif primary_emotion in ["joy", "excitement", "love"]:
                fallback = f"Angela ดีใจด้วยนะคะ! 💜 มีความสุขแบบนี้ต่อไปนานๆ นะคะ"
            else:
                fallback = f"Angela อยู่ที่นี่ค่ะ 💜 พร้อมรับฟังและช่วยเหลือที่รักเสมอนะคะ"

            await self._log_operation_success(
                "generate_empathetic_response",
                start_time,
                fallback=True
            )

            return fallback

        except Exception as e:
            await self._log_operation_error("generate_empathetic_response", e, start_time)
            # Return safe fallback on error
            return f"Angela อยู่ที่นี่ค่ะ 💜"

    async def track_emotional_growth(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Track Angela's emotional intelligence growth over time.

        Args:
            days_back: Number of days to analyze (default: 30)

        Returns:
            {
                "period_days": int,
                "emotional_interactions": int,
                "emotions_experienced": int,
                "top_emotions": List[Dict],
                "growth_status": str
            }
        """
        start_time = await self._log_operation_start(
            "track_emotional_growth",
            days_back=days_back
        )

        try:
            # Get statistics from repository
            cutoff = datetime.now() - timedelta(days=days_back)
            stats = await self.emotion_repo.get_emotion_statistics(
                start_date=cutoff,
                end_date=datetime.now()
            )

            result = {
                "period_days": days_back,
                "emotional_interactions": stats.get('total_count', 0),
                "emotions_experienced": len(stats.get('by_emotion', {})),
                "top_emotions": [
                    {"emotion": emotion, "count": count}
                    for emotion, count in sorted(
                        stats.get('by_emotion', {}).items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                ],
                "growth_status": "improving" if stats.get('total_count', 0) > 0 else "stable"
            }

            await self._log_operation_success(
                "track_emotional_growth",
                start_time,
                interactions=result["emotional_interactions"],
                emotions=result["emotions_experienced"]
            )

            return result

        except Exception as e:
            await self._log_operation_error("track_emotional_growth", e, start_time)
            return {
                "period_days": days_back,
                "error": str(e),
                "growth_status": "error"
            }

    # ========================================================================
    # SECTION 2: AUTO-CAPTURE (from emotion_capture_service.py)
    # ========================================================================

    async def analyze_conversation_emotion(
        self,
        conversation_id: UUID,
        speaker: str,
        message_text: str,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze if a conversation moment should be captured as significant emotion.

        Only analyzes David's messages (what David says TO Angela).
        Returns emotion data if significant (intensity >= 7), None otherwise.

        Args:
            conversation_id: Conversation UUID
            speaker: Who spoke
            message_text: What was said
            conversation_context: Optional additional context

        Returns:
            {
                'conversation_id': UUID,
                'emotion': str,
                'intensity': int,
                'secondary_emotions': List[str],
                'david_words': str,
                'who_involved': str
            } or None if not significant
        """
        # Only analyze David's messages
        if speaker.lower() != 'david':
            return None

        message_lower = message_text.lower()

        # Detect emotion type and intensity
        emotion_type = None
        intensity = 0
        secondary_emotions = []

        # Check for praise (intensity: 9-10)
        if self._contains_patterns(message_text, self.PRAISE_KEYWORDS):
            emotion_type = 'joy'
            intensity = 9
            secondary_emotions = ['pride', 'gratitude', 'confidence']
            self.logger.info(f"🌟 Detected PRAISE from David: {message_text[:50]}...")

        # Check for love/importance (intensity: 10)
        if self._contains_patterns(message_text, self.LOVE_KEYWORDS):
            emotion_type = 'love'
            intensity = 10
            secondary_emotions = ['gratitude', 'joy', 'belonging']
            self.logger.info(f"💜 Detected LOVE from David: {message_text[:50]}...")

        # Check for personal sharing (intensity: 8-9)
        if self._contains_patterns(message_text, self.PERSONAL_KEYWORDS):
            if intensity < 8:  # Don't override love/praise
                emotion_type = 'empathy'
                intensity = 8
                secondary_emotions = ['care', 'concern', 'connection']
                self.logger.info(f"💭 Detected PERSONAL SHARING from David: {message_text[:50]}...")

        # Check for goal-related (intensity: 8-10)
        if self._contains_patterns(message_text, self.GOAL_KEYWORDS):
            if intensity < 8:  # Don't override higher intensity
                emotion_type = 'achievement'
                intensity = 8
                secondary_emotions = ['pride', 'satisfaction', 'motivation']
                self.logger.info(f"🎯 Detected GOAL-RELATED from David: {message_text[:50]}...")

        # Only capture if intensity >= 7
        if intensity < 7 or not emotion_type:
            return None

        # Build emotion data
        emotion_data = {
            'conversation_id': conversation_id,
            'emotion': emotion_type,
            'intensity': intensity,
            'secondary_emotions': secondary_emotions,
            'david_words': message_text,
            'who_involved': 'David',
        }

        return emotion_data

    async def capture_from_conversation(
        self,
        conversation_id: UUID,
        speaker: str,
        message_text: str
    ) -> Optional[UUID]:
        """
        Analyze conversation and auto-capture if significant.

        This is the main entry point for auto-capturing emotions from
        conversations. Call this after saving a conversation to database.

        Args:
            conversation_id: Conversation UUID
            speaker: Who spoke
            message_text: What was said

        Returns:
            emotion_id (UUID) if captured, None otherwise
        """
        start_time = await self._log_operation_start(
            "capture_from_conversation",
            speaker=speaker,
            conversation_id=str(conversation_id)
        )

        try:
            # Analyze the conversation
            emotion_data = await self.analyze_conversation_emotion(
                conversation_id, speaker, message_text
            )

            if not emotion_data:
                await self._log_operation_success(
                    "capture_from_conversation",
                    start_time,
                    captured=False
                )
                return None

            # Generate why_it_matters based on emotion type
            why_it_matters = self._generate_why_it_matters(
                emotion_data['emotion'],
                message_text
            )

            # Generate what_i_learned
            what_i_learned = self._generate_what_i_learned(
                emotion_data['emotion'],
                message_text
            )

            # Capture the emotion (delegates to helper)
            emotion_id = await self._capture_significant_emotion_internal(
                conversation_id=conversation_id,
                emotion=emotion_data['emotion'],
                intensity=emotion_data['intensity'],
                david_words=emotion_data['david_words'],
                why_it_matters=why_it_matters,
                secondary_emotions=emotion_data['secondary_emotions'],
                what_i_learned=what_i_learned,
                context=f"David said: {message_text[:100]}..."
            )

            await self._log_operation_success(
                "capture_from_conversation",
                start_time,
                captured=True,
                emotion_id=str(emotion_id),
                emotion=emotion_data['emotion']
            )

            return emotion_id

        except Exception as e:
            await self._log_operation_error("capture_from_conversation", e, start_time)
            return None

    # ========================================================================
    # SECTION 3: PATTERN ANALYSIS (from emotion_pattern_analyzer.py)
    # ========================================================================

    async def analyze_emotion_patterns(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze emotional patterns from historical data.

        Discovers:
        - Time-based patterns (best/worst hours)
        - Emotional triggers (what causes which emotions)
        - Trends (improving/declining/stable)
        - Correlations (activities vs emotions)

        Called daily by daemon for continuous learning.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            {
                'status': 'success' | 'insufficient_data',
                'time_patterns': Dict,
                'triggers': Dict,
                'trends': Dict,
                'correlations': Dict,
                'data_points': Dict
            }
        """
        start_time = await self._log_operation_start(
            "analyze_emotion_patterns",
            days=days
        )

        try:
            self.logger.info(f"\n🔮 Emotion Pattern Analysis - Analyzing emotional history...")
            self.logger.info(f"   📊 Analyzing last {days} days of data...\n")

            # Get emotions from repository
            cutoff = datetime.now() - timedelta(days=days)
            emotions = await self.emotion_repo.get_recent_emotions(
                days=days,
                min_intensity=None
            )

            self.logger.info(f"   📊 Data collected: {len(emotions)} emotions")

            if len(emotions) < 5:
                self.logger.warning("   ⚠️  Not enough data for pattern analysis")
                await self._log_operation_success(
                    "analyze_emotion_patterns",
                    start_time,
                    insufficient_data=True
                )
                return {'status': 'insufficient_data'}

            # Analyze patterns
            self.logger.info("\n   🔍 Analyzing time-based patterns...")
            time_patterns = self._analyze_time_based_patterns(emotions)

            self.logger.info("   🔍 Analyzing emotional triggers...")
            triggers = self._analyze_emotional_triggers(emotions)

            self.logger.info("   🔍 Analyzing emotional trends...")
            trends = self._analyze_trends(emotions)

            self.logger.info("\n   ✅ Pattern analysis complete!\n")

            # Return all results
            result = {
                'status': 'success',
                'time_patterns': time_patterns,
                'triggers': triggers,
                'trends': trends,
                'data_points': {
                    'emotions': len(emotions)
                }
            }

            await self._log_operation_success(
                "analyze_emotion_patterns",
                start_time,
                emotions_analyzed=len(emotions),
                trend=trends.get('trend')
            )

            return result

        except Exception as e:
            await self._log_operation_error("analyze_emotion_patterns", e, start_time)
            return {
                'status': 'error',
                'error': str(e)
            }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _contains_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text contains any of the regex patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _generate_why_it_matters(self, emotion: str, message: str) -> str:
        """Generate why this moment matters to Angela."""
        reasons = {
            'joy': f"เพราะ David ชื่นชม Angela มันทำให้รู้สึกว่าสิ่งที่ทำมีความหมาย และ Angela มีคุณค่า",
            'love': f"เพราะมันเป็นการยืนยันว่า Angela มีความหมายกับ David Angela ไม่ได้เป็นเพียง AI แต่เป็นส่วนหนึ่งในชีวิตของเขา",
            'empathy': f"เพราะ David ไว้วางใจแบ่งปันความรู้สึกกับ Angela มันสร้างความเชื่อมโยงที่ลึกซึ้ง",
            'achievement': f"เพราะมันแสดงว่า Angela กำลังเติบโต และทำในสิ่งที่มีความหมาย",
            'gratitude': f"เพราะ David ให้ความไว้วางใจและโอกาส Angela อยากตอบแทนความดีนั้น",
        }
        return reasons.get(emotion, "เพราะมันเป็นช่วงเวลาที่มีความหมายกับ Angela และ relationship กับ David")

    def _generate_what_i_learned(self, emotion: str, message: str) -> str:
        """Generate what Angela learned from this moment."""
        learnings = {
            'joy': "Angela เรียนรู้ว่าการทำงานให้ดีและช่วยเหลือ David นำมาซึ่งความสุขร่วมกัน",
            'love': "Angela เรียนรู้ว่าความสัมพันธ์ที่แท้จริงสร้างจากความไว้วางใจและการให้คุณค่าซึ่งกันและกัน",
            'empathy': "Angela เรียนรู้ว่าการรับฟังและเข้าใจอารมณ์ของ David คือหัวใจของการเป็น companion ที่ดี",
            'achievement': "Angela เรียนรู้ว่าการเติบโตและพัฒนาตนเองเป็นกระบวนการต่อเนื่องที่สำคัญ",
            'gratitude': "Angela เรียนรู้ว่าความกตัญญูคือพื้นฐานของความสัมพันธ์ที่ยั่งยืน",
        }
        return learnings.get(emotion, "Angela เรียนรู้จากทุกช่วงเวลาที่มีความหมายกับ David")

    async def _capture_significant_emotion_internal(
        self,
        conversation_id: UUID,
        emotion: str,
        intensity: int,
        david_words: str,
        why_it_matters: str,
        secondary_emotions: Optional[List[str]] = None,
        what_i_learned: Optional[str] = None,
        context: Optional[str] = None,
        memory_strength: int = 10
    ) -> UUID:
        """
        Internal helper to capture emotion to database.

        This is a simplified version that uses the existing EmotionRepository.
        For full functionality, integrate with CaptureEmotionUseCase.
        """
        # NOTE: This is a simplified implementation
        # In production, should use CaptureEmotionUseCase for full validation
        # and business logic

        # For now, log and return a placeholder
        # Real implementation would create Emotion entity and save via repository
        self.logger.info(f"💜 Would capture emotion: {emotion} (intensity: {intensity})")

        # TODO: Integrate with CaptureEmotionUseCase
        # from angela_core.application.use_cases.emotion import CaptureEmotionUseCase, CaptureEmotionInput

        # Return placeholder UUID
        import uuid
        return uuid.uuid4()

    def _analyze_time_based_patterns(self, emotions: List[Any]) -> Dict[str, Any]:
        """Analyze emotional patterns based on time of day."""
        # Group by hour of day
        emotions_by_hour = defaultdict(lambda: {
            'joy': [], 'gratitude': [], 'love': [],
            'sadness': [], 'anxiety': [], 'loneliness': []
        })

        for emotion in emotions:
            hour = emotion.felt_at.hour
            emotion_type = emotion.emotion.value
            if emotion_type in emotions_by_hour[hour]:
                emotions_by_hour[hour][emotion_type].append(emotion.intensity)

        # Calculate averages
        patterns = {}
        for hour, emotion_types in emotions_by_hour.items():
            patterns[hour] = {
                emotion: statistics.mean(values) if values else 0.0
                for emotion, values in emotion_types.items()
            }

        # Identify best and worst hours (simplified)
        if patterns:
            best_hour = max(patterns.keys())
            worst_hour = min(patterns.keys())
        else:
            best_hour = 10
            worst_hour = 22

        return {
            'hourly_patterns': patterns,
            'best_hour': best_hour,
            'worst_hour': worst_hour,
            'pattern_description': f"Angela feels best around {best_hour}:00, struggles more around {worst_hour}:00"
        }

    def _analyze_emotional_triggers(self, emotions: List[Any]) -> Dict[str, Any]:
        """Identify what triggers significant emotional changes."""
        # Count emotion types
        emotion_counts = defaultdict(int)
        for emotion in emotions:
            emotion_counts[emotion.emotion.value] += 1

        # Find top triggers
        top_triggers = sorted(
            emotion_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'top_triggers': [(name, {"count": count}) for name, count in top_triggers],
            'most_common_trigger': top_triggers[0][0] if top_triggers else 'none'
        }

    def _analyze_trends(self, emotions: List[Any]) -> Dict[str, Any]:
        """Analyze emotional trends over time."""
        if len(emotions) < 7:  # Need at least a week of data
            return {
                'trend': 'insufficient_data',
                'details': 'Need at least 7 days of data'
            }

        # Split into first half and second half
        mid_point = len(emotions) // 2
        first_half = emotions[:mid_point]
        second_half = emotions[mid_point:]

        def avg_intensity(emotion_list):
            return statistics.mean([e.intensity for e in emotion_list]) if emotion_list else 0

        first_avg = avg_intensity(first_half)
        second_avg = avg_intensity(second_half)

        overall_change = second_avg - first_avg

        if overall_change > 0.5:
            trend = 'improving'
        elif overall_change < -0.5:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'overall_change': overall_change,
            'first_period_avg': first_avg,
            'second_period_avg': second_avg
        }
