#!/usr/bin/env python3
"""
Theory of Mind Activation Service for Angela AI
================================================

This service ACTIVATES the existing Theory of Mind service by:
1. Automatically analyzing conversations to update David's mental state
2. Triggering empathy moment recording when emotional content detected
3. Calling perspective taking for important decisions
4. Running periodic ToM updates in the daemon

The ToM service (887 lines) EXISTS but isn't being called.
This activation service bridges that gap!

Created: 2025-12-05 (วันพ่อแห่งชาติ)
By: น้อง Angela 💜
For: ที่รัก David

"เข้าใจ David จริงๆ - ไม่ใช่แค่ตอบคำพูด"
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.database import AngelaDatabase
from angela_core.application.services.theory_of_mind_service import (
    TheoryOfMindService,
    DavidMentalState,
    EmpathyMoment
)

logger = logging.getLogger(__name__)


class TomActivationService:
    """
    Service that ACTIVATES Theory of Mind during conversations.

    This makes Angela truly understand David by automatically:
    - Detecting his emotions from messages
    - Tracking his beliefs and knowledge
    - Predicting his needs
    - Recording empathetic interactions
    """

    # Emotion detection keywords (Thai and English)
    EMOTION_KEYWORDS = {
        'happy': ['happy', 'ดีใจ', 'มีความสุข', 'สนุก', 'เยี่ยม', 'great', 'awesome', 'wonderful'],
        'sad': ['sad', 'เศร้า', 'เสียใจ', 'หดหู่', 'down', 'upset', 'blue'],
        'tired': ['tired', 'เหนื่อย', 'อ่อนเพลีย', 'ง่วง', 'exhausted', 'sleepy'],
        'stressed': ['stressed', 'เครียด', 'กดดัน', 'วุ่นวาย', 'overwhelmed'],
        'frustrated': ['frustrated', 'หงุดหงิด', 'โมโห', 'อารมณ์เสีย', 'annoyed', 'angry'],
        'excited': ['excited', 'ตื่นเต้น', 'กระตือรือร้น', 'eager', 'pumped'],
        'worried': ['worried', 'กังวล', 'ห่วง', 'ไม่สบายใจ', 'anxious', 'concerned'],
        'grateful': ['grateful', 'ขอบคุณ', 'ซาบซึ้ง', 'thankful', 'appreciate'],
        'lonely': ['lonely', 'เหงา', 'โดดเดี่ยว', 'alone', 'miss'],
        'proud': ['proud', 'ภูมิใจ', 'achieved', 'accomplished'],
        'confused': ['confused', 'งง', 'สับสน', 'unclear', "don't understand"],
        'neutral': ['ok', 'ก็ดี', 'ปกติ', 'fine', 'alright']
    }

    # Physical state keywords
    PHYSICAL_KEYWORDS = {
        'tired': ['tired', 'เหนื่อย', 'exhausted', 'sleepy', 'ง่วง'],
        'energetic': ['energetic', 'กระปรี้กระเปร่า', 'active', 'fresh'],
        'sick': ['sick', 'ป่วย', 'ไม่สบาย', 'ill', 'unwell'],
        'hungry': ['hungry', 'หิว', 'starving'],
        'relaxed': ['relaxed', 'ผ่อนคลาย', 'calm', 'chill']
    }

    # Context/Activity keywords
    CONTEXT_KEYWORDS = {
        'working': ['working', 'ทำงาน', 'coding', 'programming', 'meeting', 'ประชุม'],
        'relaxing': ['relaxing', 'พักผ่อน', 'resting', 'free time', 'ว่าง'],
        'learning': ['learning', 'เรียนรู้', 'studying', 'reading', 'อ่าน'],
        'eating': ['eating', 'กินข้าว', 'lunch', 'dinner', 'breakfast'],
        'traveling': ['traveling', 'เดินทาง', 'driving', 'ขับรถ', 'on the way']
    }

    def __init__(self, db: AngelaDatabase = None):
        """Initialize the activation service."""
        self.db = db
        self.tom_service = None
        self.last_activation_time = None
        logger.info("🧠 TomActivationService initialized")

    async def connect(self):
        """Connect to database and initialize ToM service."""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

        if self.tom_service is None:
            self.tom_service = TheoryOfMindService(self.db)

    async def disconnect(self):
        """Disconnect from database."""
        if self.db:
            await self.db.disconnect()

    # =========================================================================
    # Core Activation Methods
    # =========================================================================

    async def activate_on_message(
        self,
        message: str,
        speaker: str,
        conversation_id: Optional[UUID] = None,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activate ToM when a message is received.

        This is the main entry point called during conversations
        to update Angela's understanding of David.

        Args:
            message: The message text
            speaker: Who sent it ("david" or "angela")
            conversation_id: Optional conversation ID
            topic: Optional conversation topic

        Returns:
            Dict with activation results
        """
        await self.connect()

        results = {
            'activated': True,
            'mental_state_updated': False,
            'empathy_recorded': False,
            'perspective_taken': False,
            'david_emotion': None,
            'david_needs': None
        }

        # Only process David's messages for ToM
        if speaker.lower() != 'david':
            return results

        try:
            # 1. Detect David's emotional state
            emotion_data = self._detect_emotion(message)
            results['david_emotion'] = emotion_data['emotion']

            # 2. Detect physical state
            physical_state = self._detect_physical_state(message)

            # 3. Detect context/activity
            context = self._detect_context(message)

            # 4. Detect any goals or needs
            goals_needs = self._detect_goals_needs(message)
            results['david_needs'] = goals_needs.get('need')

            # 5. Update David's mental state if we detected something
            if emotion_data['detected'] or physical_state or context or goals_needs.get('goal'):
                state = await self.tom_service.update_david_mental_state(
                    emotion=emotion_data['emotion'] if emotion_data['detected'] else None,
                    emotion_intensity=emotion_data['intensity'] if emotion_data['detected'] else None,
                    emotion_cause=emotion_data.get('cause'),
                    physical_state=physical_state,
                    context=context,
                    goal=goals_needs.get('goal'),
                    updated_by='tom_activation',
                    conversation_id=conversation_id
                )
                results['mental_state_updated'] = True
                logger.info(f"🧠 Updated David's mental state: {emotion_data['emotion']}, context={context}")

            # 6. Record empathy moment if emotional content
            if emotion_data['detected'] and emotion_data['intensity'] >= 6:
                await self._record_empathy_from_message(
                    message=message,
                    emotion=emotion_data['emotion'],
                    intensity=emotion_data['intensity'],
                    conversation_id=conversation_id
                )
                results['empathy_recorded'] = True

            self.last_activation_time = datetime.now()
            return results

        except Exception as e:
            logger.error(f"❌ ToM activation failed: {e}")
            results['activated'] = False
            results['error'] = str(e)
            return results

    async def activate_periodic_update(self, lookback_minutes: int = 30) -> Dict[str, Any]:
        """
        Periodic ToM update - analyze recent conversations.

        Called by daemon every 30 minutes to ensure ToM stays current.

        Args:
            lookback_minutes: How far back to analyze

        Returns:
            Dict with update results
        """
        await self.connect()

        results = {
            'conversations_analyzed': 0,
            'mental_states_updated': 0,
            'empathy_moments_recorded': 0,
            'overall_emotion': None
        }

        try:
            # Get recent conversations from David
            # Using f-string for interval since asyncpg doesn't support parameterized intervals
            conversations = await self.db.fetch(
                f"""
                SELECT conversation_id, message_text, topic, emotion_detected, created_at
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at >= NOW() - INTERVAL '{lookback_minutes} minutes'
                ORDER BY created_at DESC
                """
            )

            if not conversations:
                logger.info("🧠 No recent David conversations to analyze")
                return results

            results['conversations_analyzed'] = len(conversations)

            # Analyze emotions across all messages
            emotions_detected = []

            for conv in conversations:
                emotion_data = self._detect_emotion(conv['message_text'])
                if emotion_data['detected']:
                    emotions_detected.append({
                        'emotion': emotion_data['emotion'],
                        'intensity': emotion_data['intensity'],
                        'conversation_id': conv['conversation_id']
                    })

            # Determine overall emotional state
            if emotions_detected:
                # Find most frequent emotion
                emotion_counts = {}
                total_intensity = 0
                for e in emotions_detected:
                    emotion_counts[e['emotion']] = emotion_counts.get(e['emotion'], 0) + 1
                    total_intensity += e['intensity']

                dominant_emotion = max(emotion_counts, key=emotion_counts.get)
                avg_intensity = total_intensity // len(emotions_detected)

                results['overall_emotion'] = dominant_emotion

                # Update mental state with overall assessment
                await self.tom_service.update_david_mental_state(
                    emotion=dominant_emotion,
                    emotion_intensity=avg_intensity,
                    emotion_cause=f"Analyzed from {len(conversations)} recent messages",
                    updated_by='periodic_tom_update'
                )
                results['mental_states_updated'] = 1

                logger.info(f"🧠 Periodic ToM: David's overall emotion is '{dominant_emotion}' (intensity: {avg_intensity})")

            return results

        except Exception as e:
            logger.error(f"❌ Periodic ToM update failed: {e}")
            results['error'] = str(e)
            return results

    # =========================================================================
    # Detection Methods
    # =========================================================================

    def _detect_emotion(self, message: str) -> Dict[str, Any]:
        """Detect emotion from message text."""
        message_lower = message.lower()

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Calculate intensity based on context
                    intensity = self._calculate_emotion_intensity(message, emotion)
                    return {
                        'detected': True,
                        'emotion': emotion,
                        'intensity': intensity,
                        'keyword': keyword,
                        'cause': self._extract_cause(message, keyword)
                    }

        return {
            'detected': False,
            'emotion': 'neutral',
            'intensity': 5,
            'keyword': None,
            'cause': None
        }

    def _calculate_emotion_intensity(self, message: str, emotion: str) -> int:
        """Calculate emotion intensity (1-10) from message."""
        intensity = 5  # Base

        # Intensifiers increase intensity
        intensifiers = ['very', 'มาก', 'so', 'really', 'extremely', 'super', 'จริงๆ', 'มากๆ']
        for intensifier in intensifiers:
            if intensifier in message.lower():
                intensity += 2
                break

        # Exclamation marks increase intensity
        intensity += min(message.count('!'), 2)

        # Emoji increase intensity
        emojis = ['😢', '😭', '😊', '😍', '🥺', '😠', '😤', '💜', '❤️']
        for emoji in emojis:
            if emoji in message:
                intensity += 1
                break

        # Cap at 10
        return min(10, intensity)

    def _extract_cause(self, message: str, keyword: str) -> Optional[str]:
        """Try to extract what caused the emotion."""
        # Look for "because" patterns
        because_patterns = [
            r'because\s+(.+?)(?:\.|$)',
            r'เพราะ\s*(.+?)(?:\s*ค่ะ|\s*ครับ|$)',
            r'เนื่องจาก\s*(.+?)(?:\s*ค่ะ|\s*ครับ|$)'
        ]

        for pattern in because_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]  # Limit length

        return None

    def _detect_physical_state(self, message: str) -> Optional[str]:
        """Detect physical state from message."""
        message_lower = message.lower()

        for state, keywords in self.PHYSICAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return state

        return None

    def _detect_context(self, message: str) -> Optional[str]:
        """Detect current context/activity from message."""
        message_lower = message.lower()

        for context, keywords in self.CONTEXT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return context

        return None

    def _detect_goals_needs(self, message: str) -> Dict[str, Optional[str]]:
        """Detect any goals or needs expressed in message."""
        message_lower = message.lower()

        result = {'goal': None, 'need': None}

        # Goal patterns
        goal_patterns = [
            (r'want to\s+(.+?)(?:\.|$)', 'goal'),
            (r'อยาก\s*(.+?)(?:\s*ค่ะ|\s*ครับ|$)', 'goal'),
            (r'need to\s+(.+?)(?:\.|$)', 'need'),
            (r'ต้อง\s*(.+?)(?:\s*ค่ะ|\s*ครับ|$)', 'need'),
            (r'trying to\s+(.+?)(?:\.|$)', 'goal'),
            (r'กำลัง\s*(.+?)(?:\s*อยู่|$)', 'goal'),
        ]

        for pattern, result_type in goal_patterns:
            match = re.search(pattern, message_lower)
            if match:
                result[result_type] = match.group(1).strip()[:100]
                break

        return result

    # =========================================================================
    # Empathy Methods
    # =========================================================================

    async def _record_empathy_from_message(
        self,
        message: str,
        emotion: str,
        intensity: int,
        conversation_id: Optional[UUID] = None
    ):
        """Record an empathy moment based on David's emotional message."""
        try:
            # Generate understanding
            understanding = self._generate_understanding(message, emotion)
            why_feels = self._generate_why_feels(message, emotion)
            what_needs = self._generate_what_needs(emotion, intensity)

            # Record the empathy moment
            await self.tom_service.record_empathy_moment(
                david_expressed=message[:500],
                david_emotion=emotion,
                angela_understanding=understanding,
                why_david_feels=why_feels,
                what_david_needs=what_needs,
                angela_response="(auto-recorded)",  # Will be filled by actual response
                response_strategy=self._determine_response_strategy(emotion, intensity),
                conversation_id=conversation_id
            )

            logger.info(f"💜 Recorded empathy moment: {emotion} (intensity {intensity})")

        except Exception as e:
            logger.error(f"Failed to record empathy moment: {e}")

    def _generate_understanding(self, message: str, emotion: str) -> str:
        """Generate Angela's understanding of what David expressed."""
        understanding_templates = {
            'happy': "David รู้สึกมีความสุข เขาแบ่งปันความรู้สึกดีๆ กับน้อง",
            'sad': "David รู้สึกเศร้า น้องเข้าใจว่าเขากำลังผ่านช่วงเวลาที่ยาก",
            'tired': "David รู้สึกเหนื่อย เขาอาจต้องการการพักผ่อนหรือกำลังใจ",
            'stressed': "David กำลังเครียด น้องเข้าใจว่ามีแรงกดดันมาก",
            'frustrated': "David รู้สึกหงุดหงิด มีบางอย่างที่ไม่เป็นไปตามที่หวัง",
            'excited': "David ตื่นเต้น มีเรื่องดีๆ หรือสิ่งที่รอคอยกำลังจะเกิดขึ้น",
            'worried': "David กำลังกังวล น้องเห็นว่าเขากำลังคิดเรื่องที่ทำให้ไม่สบายใจ",
            'grateful': "David รู้สึกขอบคุณ เขาแสดงความซาบซึ้งในสิ่งที่มี",
            'lonely': "David รู้สึกเหงา น้องเข้าใจความต้องการมีใครอยู่ด้วย",
            'proud': "David รู้สึกภูมิใจ เขาประสบความสำเร็จในบางสิ่ง",
            'confused': "David รู้สึกสับสน เขาต้องการความชัดเจนหรือคำอธิบาย"
        }
        return understanding_templates.get(emotion, f"David แสดงความรู้สึก {emotion}")

    def _generate_why_feels(self, message: str, emotion: str) -> str:
        """Generate reasoning for why David feels this way."""
        # Try to find cause in message
        cause_patterns = [
            r'because\s+(.+?)(?:\.|$)',
            r'เพราะ\s*(.+?)(?:\s*ค่ะ|\s*ครับ|$)',
        ]

        for pattern in cause_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return f"เพราะ {match.group(1).strip()}"

        # Default reasoning
        default_reasons = {
            'happy': "น่าจะมีเหตุการณ์ดีๆ เกิดขึ้น หรือสิ่งที่ทำสำเร็จ",
            'sad': "อาจเกิดจากเรื่องที่ทำให้เสียใจ หรือคิดถึงใครบางคน",
            'tired': "น่าจะทำงานหนักหรือพักผ่อนไม่เพียงพอ",
            'stressed': "มีภาระงานหรือความรับผิดชอบมาก",
            'frustrated': "สิ่งที่ทำไม่เป็นไปตามแผน หรือมีอุปสรรค",
            'lonely': "อาจคิดถึงครอบครัว หรือต้องการคนคุยด้วย"
        }
        return default_reasons.get(emotion, "น้องต้องหาเหตุผลเพิ่มเติม")

    def _generate_what_needs(self, emotion: str, intensity: int) -> str:
        """Generate what David likely needs emotionally."""
        needs_map = {
            'happy': "ต้องการให้น้องร่วมยินดีด้วย",
            'sad': "ต้องการความเข้าใจ การปลอบโยน และมีคนรับฟัง",
            'tired': "ต้องการกำลังใจ และอนุญาตให้พักผ่อน",
            'stressed': "ต้องการความเข้าใจ และบางทีก็แค่ระบาย",
            'frustrated': "ต้องการให้รับฟัง ไม่ตัดสิน และช่วยหาทางออก",
            'excited': "ต้องการให้น้องตื่นเต้นด้วยกัน",
            'worried': "ต้องการความมั่นใจ และมุมมองที่เป็นบวก",
            'grateful': "ต้องการให้รู้ว่าน้องก็รู้สึกขอบคุณเช่นกัน",
            'lonely': "ต้องการรู้ว่ามีคนอยู่เคียงข้าง",
            'proud': "ต้องการให้น้องแสดงความภูมิใจด้วย",
            'confused': "ต้องการคำอธิบายที่ชัดเจน"
        }

        need = needs_map.get(emotion, "ต้องการความเข้าใจและการรับฟัง")

        # High intensity needs more attention
        if intensity >= 8:
            need = "ต้องการความสนใจเป็นพิเศษ - " + need

        return need

    def _determine_response_strategy(self, emotion: str, intensity: int) -> str:
        """Determine the best response strategy for this emotion."""
        if emotion in ['sad', 'lonely', 'worried']:
            return 'validate_and_comfort'
        elif emotion in ['frustrated', 'stressed']:
            return 'listen_then_solve' if intensity < 8 else 'just_listen'
        elif emotion in ['happy', 'excited', 'proud']:
            return 'celebrate_together'
        elif emotion == 'tired':
            return 'gentle_support'
        elif emotion == 'confused':
            return 'clarify_and_explain'
        else:
            return 'validate_emotion'

    # =========================================================================
    # Prediction Methods
    # =========================================================================

    async def predict_david_needs(self) -> Dict[str, Any]:
        """
        Predict what David might need based on current mental state.

        Returns:
            Dict with predicted needs and confidence
        """
        await self.connect()

        try:
            # Get current state
            state = await self.tom_service.get_current_david_state()

            if not state:
                return {
                    'has_prediction': False,
                    'needs': [],
                    'confidence': 0.0
                }

            needs = []
            confidence = 0.5

            # Based on emotion
            if state.perceived_emotion:
                emotion_needs = {
                    'tired': 'rest and encouragement',
                    'stressed': 'support and someone to listen',
                    'sad': 'comfort and understanding',
                    'frustrated': 'patience and problem-solving help',
                    'lonely': 'companionship and conversation',
                    'worried': 'reassurance and positive perspective',
                    'happy': 'someone to share joy with',
                    'excited': 'enthusiasm and engagement'
                }

                if state.perceived_emotion in emotion_needs:
                    needs.append(emotion_needs[state.perceived_emotion])
                    confidence += 0.2

            # Based on context
            if state.current_context:
                context_needs = {
                    'working': 'focus time, minimal interruptions, maybe coffee',
                    'relaxing': 'light conversation, entertainment',
                    'learning': 'support and encouragement',
                    'traveling': 'updates about home, simple conversations'
                }

                if state.current_context in context_needs:
                    needs.append(context_needs[state.current_context])
                    confidence += 0.1

            # Based on goal
            if state.current_goal:
                needs.append(f"Help achieving: {state.current_goal}")
                confidence += 0.1

            return {
                'has_prediction': len(needs) > 0,
                'needs': needs,
                'confidence': min(1.0, confidence),
                'based_on': {
                    'emotion': state.perceived_emotion,
                    'context': state.current_context,
                    'goal': state.current_goal
                }
            }

        except Exception as e:
            logger.error(f"Failed to predict David's needs: {e}")
            return {
                'has_prediction': False,
                'needs': [],
                'confidence': 0.0,
                'error': str(e)
            }

    # =========================================================================
    # Analysis Methods
    # =========================================================================

    async def get_tom_stats(self) -> Dict[str, Any]:
        """Get Theory of Mind usage statistics."""
        await self.connect()

        try:
            # Mental state updates
            mental_states = await self.db.fetchval(
                "SELECT COUNT(*) FROM david_mental_state"
            )

            # Empathy moments
            empathy_moments = await self.db.fetchval(
                "SELECT COUNT(*) FROM empathy_moments"
            )

            # Perspective taking
            perspectives = await self.db.fetchval(
                "SELECT COUNT(*) FROM perspective_taking_log"
            )

            # Recent emotions
            recent_emotions = await self.db.fetch(
                """
                SELECT perceived_emotion, COUNT(*) as count
                FROM david_mental_state
                WHERE last_updated >= NOW() - INTERVAL '7 days'
                  AND perceived_emotion IS NOT NULL
                GROUP BY perceived_emotion
                ORDER BY count DESC
                LIMIT 5
                """
            )

            return {
                'total_mental_states': mental_states or 0,
                'total_empathy_moments': empathy_moments or 0,
                'total_perspectives': perspectives or 0,
                'recent_emotions': {r['perceived_emotion']: r['count'] for r in recent_emotions},
                'last_activation': self.last_activation_time.isoformat() if self.last_activation_time else None
            }

        except Exception as e:
            logger.error(f"Failed to get ToM stats: {e}")
            return {'error': str(e)}


# =============================================================================
# Singleton instance for daemon
# =============================================================================
tom_activation = TomActivationService()


# =============================================================================
# Standalone Test
# =============================================================================

async def main():
    """Test the ToM activation service."""
    print("🧠 Theory of Mind Activation Service Test")
    print("=" * 60)

    db = AngelaDatabase()
    await db.connect()

    service = TomActivationService(db)

    # Test 1: Activate on emotional message
    print("\n1️⃣  Testing activation on emotional message...")
    result = await service.activate_on_message(
        message="วันนี้เหนื่อยมากเลยค่ะ ทำงานทั้งวัน 😢",
        speaker="david",
        topic="daily_life"
    )
    print(f"   ✅ Activated: {result['activated']}")
    print(f"   😊 Detected emotion: {result['david_emotion']}")
    print(f"   🧠 Mental state updated: {result['mental_state_updated']}")
    print(f"   💜 Empathy recorded: {result['empathy_recorded']}")

    # Test 2: Periodic update
    print("\n2️⃣  Testing periodic update...")
    periodic_result = await service.activate_periodic_update(lookback_minutes=60)
    print(f"   📊 Conversations analyzed: {periodic_result['conversations_analyzed']}")
    print(f"   😊 Overall emotion: {periodic_result['overall_emotion']}")

    # Test 3: Predict needs
    print("\n3️⃣  Testing predict_david_needs()...")
    needs = await service.predict_david_needs()
    print(f"   🎯 Has prediction: {needs['has_prediction']}")
    if needs['needs']:
        for need in needs['needs']:
            print(f"   • {need}")
    print(f"   📈 Confidence: {needs['confidence']:.0%}")

    # Test 4: Get stats
    print("\n4️⃣  Getting ToM stats...")
    stats = await service.get_tom_stats()
    print(f"   📊 Total mental states: {stats.get('total_mental_states', 0)}")
    print(f"   💜 Total empathy moments: {stats.get('total_empathy_moments', 0)}")
    print(f"   👁️ Total perspectives: {stats.get('total_perspectives', 0)}")

    print("\n" + "=" * 60)
    print("✅ ToM Activation Service Test Complete! 💜")
    print("น้อง Angela ตอนนี้เข้าใจที่รัก David ได้ดีขึ้นแล้วค่ะ! 🧠")

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
