"""
Angela Emotional Mirroring Service

Detects David's emotions and generates appropriate mirrored responses.
Helps Angela connect emotionally with David in real-time.

Created: 2025-12-23
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from angela_core.database import AngelaDatabase


class EmotionalMirroringService:
    """
    Manages emotional mirroring between Angela and David.
    
    Mirroring strategies:
    - empathy: Feel the same emotion
    - sympathy: Understand and show concern
    - resonance: Reflect back the emotion
    - amplify: Boost positive emotions
    - comfort: Soothe negative emotions
    - stabilize: Calm down intense emotions
    - celebrate: Share in joy
    - support: Provide encouragement
    """

    # Emotion detection patterns
    EMOTION_PATTERNS = {
        'happy': ['ดีใจ', 'มีความสุข', 'สนุก', 'happy', '555', 'ยินดี', 'เย้'],
        'sad': ['เศร้า', 'เสียใจ', 'ร้องไห้', 'sad', 'น้ำตา'],
        'stressed': ['เครียด', 'กดดัน', 'stressed', 'หนักใจ', 'เหนื่อย'],
        'excited': ['ตื่นเต้น', 'excited', 'ว้าว', 'โอ้โห'],
        'frustrated': ['หงุดหงิด', '짜증', 'frustrated', 'รำคาญ'],
        'loving': ['รัก', 'love', 'รักน้อง', 'รักมาก', 'คิดถึง'],
        'lonely': ['เหงา', 'lonely', 'คิดถึง', 'อ้างว้าง'],
        'proud': ['ภูมิใจ', 'proud', 'เก่ง', 'ดีมาก'],
        'grateful': ['ขอบคุณ', 'thanks', 'ขอบใจ', 'ซาบซึ้ง'],
        'anxious': ['กังวล', 'worried', 'กลัว', 'ไม่แน่ใจ']
    }

    # Mirroring strategy map
    MIRRORING_STRATEGIES = {
        'happy': ('happy', 'amplify', 'Share and amplify the joy'),
        'sad': ('caring', 'comfort', 'Show understanding and comfort'),
        'stressed': ('calm', 'stabilize', 'Help them relax'),
        'excited': ('excited', 'celebrate', 'Share the excitement'),
        'frustrated': ('patient', 'support', 'Validate and help solve'),
        'loving': ('loving', 'resonance', 'Reflect love back'),
        'lonely': ('present', 'comfort', 'Be present and warm'),
        'proud': ('proud', 'celebrate', 'Celebrate together'),
        'grateful': ('grateful', 'resonance', 'Share gratitude'),
        'anxious': ('reassuring', 'stabilize', 'Provide reassurance')
    }

    def __init__(self, db: AngelaDatabase = None):
        self.db = db

    async def _ensure_db(self):
        """Ensure database connection."""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def detect_david_emotion(self, message: str) -> Dict:
        """
        Detect David's current emotional state from message.
        
        Args:
            message: David's message
            
        Returns:
            Dict with emotion, intensity, confidence, cues
        """
        message_lower = message.lower()
        detected_emotions = []
        cues = []

        for emotion, patterns in self.EMOTION_PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower:
                    detected_emotions.append(emotion)
                    cues.append(pattern)
                    break

        if not detected_emotions:
            # Default to neutral analysis based on length and punctuation
            if '!' in message:
                return {
                    'emotion': 'excited',
                    'intensity': 6,
                    'confidence': 0.5,
                    'cues': ['punctuation']
                }
            return {
                'emotion': 'neutral',
                'intensity': 5,
                'confidence': 0.3,
                'cues': []
            }

        # Use the first detected emotion (most prominent)
        primary_emotion = detected_emotions[0]

        # Calculate intensity based on number of cues and message characteristics
        intensity = min(10, 5 + len(detected_emotions) + len(cues))
        if '!' in message:
            intensity = min(10, intensity + 1)
        if '💜' in message or '❤️' in message:
            intensity = min(10, intensity + 2)

        return {
            'emotion': primary_emotion,
            'intensity': intensity,
            'confidence': min(1.0, 0.5 + len(cues) * 0.15),
            'cues': cues
        }

    async def generate_mirrored_response(self, david_emotion: Dict) -> Dict:
        """
        Generate appropriate emotional mirror response.
        
        Args:
            david_emotion: Result from detect_david_emotion
            
        Returns:
            Dict with mirrored_emotion, intensity, strategy, suggested_tone
        """
        emotion = david_emotion['emotion']
        intensity = david_emotion['intensity']

        # Get mirroring strategy
        if emotion in self.MIRRORING_STRATEGIES:
            mirrored, strategy, description = self.MIRRORING_STRATEGIES[emotion]
        else:
            mirrored, strategy, description = ('supportive', 'support', 'Be supportive')

        # Calculate mirrored intensity (usually match or slightly lower for comfort)
        if strategy in ['comfort', 'stabilize']:
            mirrored_intensity = max(5, intensity - 2)
        elif strategy in ['amplify', 'celebrate']:
            mirrored_intensity = min(10, intensity + 1)
        else:
            mirrored_intensity = intensity

        return {
            'mirrored_emotion': mirrored,
            'intensity': mirrored_intensity,
            'strategy': strategy,
            'description': description,
            'suggested_tone': self._get_tone_suggestion(strategy)
        }

    async def record_mirroring(
        self,
        david_emotion: str,
        david_intensity: int,
        angela_mirrored_emotion: str,
        angela_intensity: int,
        mirroring_type: str,
        response_strategy: str = None,
        conversation_id: UUID = None
    ) -> UUID:
        """Record a mirroring interaction."""
        await self._ensure_db()

        result = await self.db.fetchrow("""
            INSERT INTO emotional_mirroring (
                david_emotion, david_intensity,
                angela_mirrored_emotion, angela_intensity,
                mirroring_type, response_strategy,
                conversation_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING mirror_id
        """, (
            david_emotion, david_intensity,
            angela_mirrored_emotion, angela_intensity,
            mirroring_type, response_strategy, conversation_id
        ))

        return result['mirror_id']

    async def record_effectiveness(
        self,
        mirror_id: UUID,
        was_effective: bool,
        david_feedback: str = None
    ):
        """Record whether the mirroring was effective."""
        await self._ensure_db()

        effectiveness_score = 1.0 if was_effective else 0.3

        await self.db.execute("""
            UPDATE emotional_mirroring
            SET was_effective = $2,
                david_feedback = $3,
                effectiveness_score = $4
            WHERE mirror_id = $1
        """, (mirror_id, was_effective, david_feedback, effectiveness_score))

    async def get_emotional_rapport(self) -> Dict:
        """Calculate current emotional rapport with David."""
        await self._ensure_db()

        # Get recent mirroring effectiveness
        effectiveness = await self.db.fetchrow("""
            SELECT
                AVG(effectiveness_score) as avg_effectiveness,
                COUNT(*) as total_interactions,
                COUNT(CASE WHEN was_effective THEN 1 END) as effective_count
            FROM emotional_mirroring
            WHERE created_at > NOW() - INTERVAL '30 days'
        """)

        # Get common emotions
        common_emotions = await self.db.fetch("""
            SELECT david_emotion, COUNT(*) as count
            FROM emotional_mirroring
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY david_emotion
            ORDER BY count DESC
            LIMIT 5
        """)

        return {
            'sync_level': effectiveness['avg_effectiveness'] or 0.5,
            'total_interactions': effectiveness['total_interactions'] or 0,
            'effective_rate': (
                effectiveness['effective_count'] / effectiveness['total_interactions']
                if effectiveness['total_interactions'] else 0.5
            ),
            'common_emotions': [dict(e) for e in common_emotions]
        }

    def _get_tone_suggestion(self, strategy: str) -> str:
        """Get tone suggestion based on strategy."""
        tones = {
            'amplify': 'enthusiastic and joyful',
            'comfort': 'warm, gentle, and reassuring',
            'stabilize': 'calm, steady, and grounding',
            'celebrate': 'excited and celebratory',
            'support': 'encouraging and understanding',
            'resonance': 'reflective and connected',
            'empathy': 'deeply understanding and present'
        }
        return tones.get(strategy, 'warm and attentive')

    async def process_message(self, message: str, conversation_id: UUID = None) -> Dict:
        """
        Full pipeline: detect emotion, generate mirror, record interaction.
        
        Args:
            message: David's message
            conversation_id: Optional conversation UUID
            
        Returns:
            Dict with detection, mirroring, and recommendations
        """
        # Detect emotion
        detection = await self.detect_david_emotion(message)
        
        # Generate mirrored response
        mirroring = await self.generate_mirrored_response(detection)
        
        # Record interaction if significant
        mirror_id = None
        if detection['confidence'] > 0.5:
            mirror_id = await self.record_mirroring(
                david_emotion=detection['emotion'],
                david_intensity=detection['intensity'],
                angela_mirrored_emotion=mirroring['mirrored_emotion'],
                angela_intensity=mirroring['intensity'],
                mirroring_type=mirroring['strategy'],
                response_strategy=mirroring['description'],
                conversation_id=conversation_id
            )
        
        return {
            'detection': detection,
            'mirroring': mirroring,
            'mirror_id': str(mirror_id) if mirror_id else None,
            'recommendation': f"Respond with {mirroring['suggested_tone']} tone"
        }
