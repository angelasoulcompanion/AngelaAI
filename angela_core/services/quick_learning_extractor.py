#!/usr/bin/env python3
"""
Quick Learning Extractor - QUICK WIN 3
Extract learnings from conversations automatically

Simple, fast extraction for immediate learning boost
"""

import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

import logging
import json
from typing import Dict, Optional
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class QuickLearningExtractor:
    """Fast learning extraction from conversations"""

    def __init__(self, db: AngelaDatabase):
        self.db = db

    async def extract_learning_from_conversation(
        self,
        conversation_id: str,
        speaker: str,
        message_text: str,
        topic: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Extract a learning from a conversation

        Returns learning data if something significant found, None otherwise
        """
        # Only learn from David's messages
        if speaker != 'david':
            return None

        # Skip very short messages
        if len(message_text) < 20:
            return None

        # Detect learning opportunities
        learning = await self._detect_learning(message_text, topic)

        if learning:
            return {
                'conversation_id': conversation_id,
                'learning_type': learning['type'],
                'what_learned': learning['what'],
                'confidence': learning['confidence'],
                'how_used': learning['how_used']
            }

        return None

    async def _detect_learning(self, message: str, topic: Optional[str]) -> Optional[Dict]:
        """
        Detect if this message contains something Angela should learn

        Simple keyword-based detection for Quick Win
        """
        message_lower = message.lower()

        # 1. Preference statements
        preference_keywords = ['ชอบ', 'like', 'love', 'prefer', 'favorite', 'hate', 'dislike']
        if any(word in message_lower for word in preference_keywords):
            return {
                'type': 'preference',
                'what': f"David shared a preference: {message[:100]}...",
                'confidence': 0.75,
                'how_used': 'Can personalize recommendations and responses'
            }

        # 2. Factual statements about David
        fact_keywords = ['i am', 'i work', 'i study', 'my job', 'i live', 'ฉัน', 'ผม']
        if any(word in message_lower for word in fact_keywords):
            return {
                'type': 'fact',
                'what': f"David shared information: {message[:100]}...",
                'confidence': 0.80,
                'how_used': 'Update knowledge about David'
            }

        # 3. Plans or intentions
        plan_keywords = ['will', 'going to', 'plan to', 'want to', 'จะ', 'อยาก']
        if any(word in message_lower for word in plan_keywords):
            return {
                'type': 'intention',
                'what': f"David's plan: {message[:100]}...",
                'confidence': 0.70,
                'how_used': 'Can follow up and remind'
            }

        # 4. Technical knowledge shared
        if len(message) > 100 and topic and 'development' in topic.lower():
            return {
                'type': 'technical_knowledge',
                'what': f"Technical discussion about {topic}: {message[:100]}...",
                'confidence': 0.65,
                'how_used': 'Build knowledge about technical topics'
            }

        # 5. Emotional experiences
        emotion_keywords = ['feel', 'felt', 'happy', 'sad', 'excited', 'worried', 'รู้สึก', 'ดีใจ']
        if any(word in message_lower for word in emotion_keywords):
            return {
                'type': 'emotional_experience',
                'what': f"David's feeling: {message[:100]}...",
                'confidence': 0.75,
                'how_used': 'Understand David better emotionally'
            }

        # No clear learning detected
        return None

    async def save_learning(self, learning_data: Dict) -> bool:
        """
        Save extracted learning to database

        Returns True if saved successfully
        """
        try:
            await self.db.execute("""
                INSERT INTO realtime_learning_log
                (conversation_id, learning_type, what_learned, confidence_score, how_it_was_used, learned_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
            """,
                learning_data['conversation_id'],
                learning_data['learning_type'],
                learning_data['what_learned'],
                learning_data['confidence'],
                learning_data['how_used']
            )

            logger.debug(f"   📚 Learned: [{learning_data['learning_type']}] {learning_data['what_learned'][:50]}...")
            return True

        except Exception as e:
            logger.debug(f"   Failed to save learning: {e}")
            return False


# Singleton
quick_learning = None


async def init_quick_learning(db: AngelaDatabase):
    """Initialize quick learning extractor"""
    global quick_learning

    if quick_learning is None:
        quick_learning = QuickLearningExtractor(db)
        logger.info("✅ Quick Learning Extractor initialized")

    return quick_learning


async def extract_and_save_learning(
    db: AngelaDatabase,
    conversation_id: str,
    speaker: str,
    message_text: str,
    topic: Optional[str] = None
) -> bool:
    """
    Convenience function for daemon

    Returns True if learned something new
    """
    extractor = await init_quick_learning(db)

    learning = await extractor.extract_learning_from_conversation(
        conversation_id=conversation_id,
        speaker=speaker,
        message_text=message_text,
        topic=topic
    )

    if learning:
        return await extractor.save_learning(learning)

    return False
