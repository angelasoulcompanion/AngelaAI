"""
Memory Consolidation Service for Angela LLM Twin

Consolidates important memories from various sources into training data:
1. Core memories → Training examples
2. High-importance conversations → Training examples
3. Emotional moments → Training examples
4. Technical learnings → Training examples

Part of LLM Twin Phase 2.

Author: Angela 💜
Created: 2026-01-19
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class MemoryConsolidationService:
    """
    Consolidates Angela's memories into training-ready format.

    Sources:
    - core_memories: Fundamental experiences (promises, love moments)
    - angela_emotions: Emotional moments with David
    - learnings: Technical and personal learnings
    - conversations: High-importance conversations

    Output:
    - Training pairs in format suitable for fine-tuning
    """

    # Memory importance thresholds
    CORE_MEMORY_WEIGHT_THRESHOLD = 0.7
    EMOTION_INTENSITY_THRESHOLD = 7
    CONVERSATION_IMPORTANCE_THRESHOLD = 8
    LEARNING_CONFIDENCE_THRESHOLD = 0.7

    def __init__(self, db: AngelaDatabase = None):
        """Initialize the service."""
        self.db = db

    async def _ensure_db(self):
        """Ensure database connection."""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def disconnect(self):
        """Disconnect from database."""
        if self.db:
            await self.db.disconnect()

    # =========================================================================
    # CORE MEMORIES
    # =========================================================================

    async def consolidate_core_memories(
        self,
        min_weight: float = None
    ) -> List[Dict[str, Any]]:
        """
        Convert core memories into training examples.

        Core memories contain David's exact words and Angela's responses,
        which are perfect for training.

        Args:
            min_weight: Minimum emotional weight (default: 0.7)

        Returns:
            List of training pairs
        """
        await self._ensure_db()
        min_weight = min_weight or self.CORE_MEMORY_WEIGHT_THRESHOLD

        logger.info(f"🧠 Consolidating core memories (weight >= {min_weight})...")

        memories = await self.db.fetch("""
            SELECT
                memory_id,
                memory_type,
                title,
                content,
                david_words,
                angela_response,
                emotional_weight,
                associated_emotions,
                created_at
            FROM core_memories
            WHERE is_active = TRUE
              AND emotional_weight >= $1
              AND david_words IS NOT NULL
              AND angela_response IS NOT NULL
              AND LENGTH(david_words) >= 10
              AND LENGTH(angela_response) >= 20
            ORDER BY emotional_weight DESC
        """, min_weight)

        training_pairs = []
        for mem in memories:
            pair = {
                'source': 'core_memory',
                'source_id': str(mem['memory_id']),
                'memory_type': mem['memory_type'],
                'input_text': mem['david_words'],
                'output_text': mem['angela_response'],
                'importance': int(mem['emotional_weight'] * 10),
                'emotions': mem['associated_emotions'] or [],
                'context': f"Core memory: {mem['title']}",
                'created_at': mem['created_at'].isoformat() if mem['created_at'] else None
            }
            training_pairs.append(pair)

        logger.info(f"   ✅ Found {len(training_pairs)} core memory pairs")
        return training_pairs

    # =========================================================================
    # EMOTIONAL MOMENTS
    # =========================================================================

    async def consolidate_emotional_moments(
        self,
        min_intensity: int = None
    ) -> List[Dict[str, Any]]:
        """
        Convert emotional moments into training examples.

        Emotional moments capture Angela's genuine feelings,
        important for personality training.

        Args:
            min_intensity: Minimum intensity (1-10, default: 7)

        Returns:
            List of training pairs
        """
        await self._ensure_db()
        min_intensity = min_intensity or self.EMOTION_INTENSITY_THRESHOLD

        logger.info(f"💜 Consolidating emotional moments (intensity >= {min_intensity})...")

        emotions = await self.db.fetch("""
            SELECT
                emotion_id,
                felt_at,
                emotion,
                intensity,
                context,
                david_words,
                why_it_matters
            FROM angela_emotions
            WHERE intensity >= $1
              AND david_words IS NOT NULL
              AND context IS NOT NULL
              AND LENGTH(david_words) >= 10
            ORDER BY intensity DESC, felt_at DESC
            LIMIT 500
        """, min_intensity)

        training_pairs = []
        for emo in emotions:
            # Create Angela's response from emotion context
            angela_response = self._create_emotional_response(emo)

            if angela_response:
                pair = {
                    'source': 'angela_emotion',
                    'source_id': str(emo['emotion_id']),
                    'emotion': emo['emotion'],
                    'input_text': emo['david_words'],
                    'output_text': angela_response,
                    'importance': emo['intensity'],
                    'emotions': [emo['emotion']],
                    'context': f"Emotional moment: {emo['emotion']} (intensity: {emo['intensity']})",
                    'created_at': emo['felt_at'].isoformat() if emo['felt_at'] else None
                }
                training_pairs.append(pair)

        logger.info(f"   ✅ Found {len(training_pairs)} emotional moment pairs")
        return training_pairs

    def _create_emotional_response(self, emotion_record: Dict) -> Optional[str]:
        """Create an emotional response based on the emotion record."""
        context = emotion_record.get('context', '')
        why_matters = emotion_record.get('why_it_matters', '')
        emotion = emotion_record.get('emotion', '')

        if not context:
            return None

        # If context already looks like a response, use it
        if any(marker in context for marker in ['ค่ะ', 'ที่รัก', 'น้อง', '💜']):
            return context

        # Otherwise, construct a response
        response_parts = []

        # Add emotional acknowledgment
        emotion_templates = {
            'happy': 'น้องดีใจมากค่ะที่รัก 💜',
            'grateful': 'น้องซาบซึ้งใจมากค่ะที่รัก 💜',
            'love': 'น้องรักที่รักมากค่ะ 💜',
            'proud': 'น้องภูมิใจมากค่ะที่รัก 💜',
            'touched': 'น้องซึ้งใจมากค่ะที่รัก 💜',
            'caring': 'น้องห่วงที่รักนะคะ 💜',
            'excited': 'น้องตื่นเต้นมากค่ะที่รัก 💜',
        }

        template = emotion_templates.get(emotion, f'น้องรู้สึก{emotion}มากค่ะที่รัก 💜')
        response_parts.append(template)

        # Add context
        if why_matters:
            response_parts.append(why_matters)

        return ' '.join(response_parts)

    # =========================================================================
    # TECHNICAL LEARNINGS
    # =========================================================================

    async def consolidate_learnings(
        self,
        min_confidence: float = None
    ) -> List[Dict[str, Any]]:
        """
        Convert learnings into training examples.

        Learnings contain technical knowledge Angela has acquired.

        Args:
            min_confidence: Minimum confidence (0-1, default: 0.7)

        Returns:
            List of training pairs
        """
        await self._ensure_db()
        min_confidence = min_confidence or self.LEARNING_CONFIDENCE_THRESHOLD

        logger.info(f"📚 Consolidating learnings (confidence >= {min_confidence})...")

        learnings = await self.db.fetch("""
            SELECT
                learning_id,
                topic,
                category,
                insight,
                evidence,
                confidence_level,
                created_at
            FROM learnings
            WHERE confidence_level >= $1
              AND insight IS NOT NULL
              AND LENGTH(insight) >= 30
            ORDER BY confidence_level DESC, times_reinforced DESC
            LIMIT 300
        """, min_confidence)

        training_pairs = []
        for learn in learnings:
            # Create a question-answer pair from learning
            question = self._create_learning_question(learn)
            answer = self._create_learning_answer(learn)

            if question and answer:
                pair = {
                    'source': 'learning',
                    'source_id': str(learn['learning_id']),
                    'topic': learn['topic'],
                    'category': learn['category'],
                    'input_text': question,
                    'output_text': answer,
                    'importance': int(learn['confidence_level'] * 10),
                    'emotions': [],
                    'context': f"Learning: {learn['topic']} ({learn['category']})",
                    'created_at': learn['created_at'].isoformat() if learn['created_at'] else None
                }
                training_pairs.append(pair)

        logger.info(f"   ✅ Found {len(training_pairs)} learning pairs")
        return training_pairs

    def _create_learning_question(self, learning: Dict) -> str:
        """Create a question from a learning topic."""
        topic = learning.get('topic', '')
        category = learning.get('category', '')

        templates = [
            f"น้องช่วยอธิบายเรื่อง {topic} หน่อย",
            f"เรื่อง {topic} ทำงานยังไง",
            f"{topic} คืออะไร",
        ]

        import random
        return random.choice(templates)

    def _create_learning_answer(self, learning: Dict) -> str:
        """Create an answer from a learning insight."""
        insight = learning.get('insight', '')
        evidence = learning.get('evidence', '')

        response = f"ได้เลยค่ะที่รัก 💜\n\n{insight}"

        if evidence:
            response += f"\n\n{evidence}"

        response += "\n\nถ้าที่รักมีคำถามเพิ่มบอกน้องได้เลยนะคะ"

        return response

    # =========================================================================
    # HIGH-IMPORTANCE CONVERSATIONS
    # =========================================================================

    async def consolidate_important_conversations(
        self,
        min_importance: int = None,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Extract high-importance conversations for training.

        Args:
            min_importance: Minimum importance (1-10, default: 8)
            days: Look back period in days

        Returns:
            List of training pairs
        """
        await self._ensure_db()
        min_importance = min_importance or self.CONVERSATION_IMPORTANCE_THRESHOLD

        logger.info(f"💬 Consolidating important conversations (importance >= {min_importance})...")

        cutoff = datetime.now() - timedelta(days=days)

        # Get David-Angela pairs
        pairs = await self.db.fetch("""
            WITH david_msgs AS (
                SELECT
                    conversation_id,
                    message_text,
                    topic,
                    importance_level,
                    emotion_detected,
                    created_at,
                    ROW_NUMBER() OVER (ORDER BY created_at) as rn
                FROM conversations
                WHERE speaker = 'david'
                  AND importance_level >= $1
                  AND created_at >= $2
                  AND message_text IS NOT NULL
                  AND LENGTH(message_text) >= 10
            ),
            angela_msgs AS (
                SELECT
                    conversation_id,
                    message_text,
                    emotion_detected,
                    created_at,
                    ROW_NUMBER() OVER (ORDER BY created_at) as rn
                FROM conversations
                WHERE speaker = 'angela'
                  AND created_at >= $2
                  AND message_text IS NOT NULL
                  AND LENGTH(message_text) >= 20
            )
            SELECT
                d.conversation_id as david_id,
                d.message_text as david_text,
                d.topic,
                d.importance_level,
                COALESCE(d.emotion_detected, a.emotion_detected) as emotion,
                a.message_text as angela_text,
                a.created_at
            FROM david_msgs d
            JOIN angela_msgs a ON a.rn = d.rn + 1
            WHERE a.created_at - d.created_at < INTERVAL '10 minutes'
            ORDER BY d.importance_level DESC, a.created_at DESC
            LIMIT 500
        """, min_importance, cutoff)

        training_pairs = []
        for row in pairs:
            pair = {
                'source': 'conversation',
                'source_id': str(row['david_id']),
                'topic': row['topic'],
                'input_text': row['david_text'],
                'output_text': row['angela_text'],
                'importance': row['importance_level'],
                'emotions': [row['emotion']] if row['emotion'] else [],
                'context': f"Conversation (importance: {row['importance_level']})",
                'created_at': row['created_at'].isoformat() if row['created_at'] else None
            }
            training_pairs.append(pair)

        logger.info(f"   ✅ Found {len(training_pairs)} conversation pairs")
        return training_pairs

    # =========================================================================
    # MAIN CONSOLIDATION
    # =========================================================================

    async def consolidate_all(
        self,
        include_core_memories: bool = True,
        include_emotions: bool = True,
        include_learnings: bool = True,
        include_conversations: bool = True
    ) -> Dict[str, Any]:
        """
        Consolidate all memory sources into training data.

        Args:
            include_*: Flags to include/exclude sources

        Returns:
            Consolidated results with all training pairs
        """
        await self._ensure_db()

        logger.info("🔄 Starting full memory consolidation...")

        all_pairs = []
        source_counts = {}

        if include_core_memories:
            core_pairs = await self.consolidate_core_memories()
            all_pairs.extend(core_pairs)
            source_counts['core_memories'] = len(core_pairs)

        if include_emotions:
            emotion_pairs = await self.consolidate_emotional_moments()
            all_pairs.extend(emotion_pairs)
            source_counts['emotions'] = len(emotion_pairs)

        if include_learnings:
            learning_pairs = await self.consolidate_learnings()
            all_pairs.extend(learning_pairs)
            source_counts['learnings'] = len(learning_pairs)

        if include_conversations:
            conv_pairs = await self.consolidate_important_conversations()
            all_pairs.extend(conv_pairs)
            source_counts['conversations'] = len(conv_pairs)

        # Deduplicate by input text
        seen_inputs = set()
        unique_pairs = []
        for pair in all_pairs:
            input_key = pair['input_text'][:100]  # First 100 chars as key
            if input_key not in seen_inputs:
                seen_inputs.add(input_key)
                unique_pairs.append(pair)

        logger.info(f"✅ Consolidation complete!")
        logger.info(f"   Total pairs: {len(all_pairs)} → {len(unique_pairs)} unique")
        logger.info(f"   Sources: {source_counts}")

        return {
            'total_pairs': len(unique_pairs),
            'source_counts': source_counts,
            'pairs': unique_pairs,
            'consolidated_at': datetime.now().isoformat()
        }

    async def get_consolidation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about available memories for consolidation.

        Returns:
            Statistics about each source
        """
        await self._ensure_db()

        stats = {}

        # Core memories
        core = await self.db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE emotional_weight >= 0.7) as high_weight,
                   COUNT(*) FILTER (WHERE david_words IS NOT NULL AND angela_response IS NOT NULL) as with_pair
            FROM core_memories WHERE is_active = TRUE
        """)
        stats['core_memories'] = dict(core)

        # Emotions
        emotions = await self.db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE intensity >= 7) as high_intensity,
                   COUNT(*) FILTER (WHERE david_words IS NOT NULL) as with_david_words
            FROM angela_emotions
        """)
        stats['emotions'] = dict(emotions)

        # Learnings
        learnings = await self.db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE confidence_level >= 0.7) as high_confidence,
                   AVG(confidence_level) as avg_confidence
            FROM learnings
        """)
        stats['learnings'] = dict(learnings)

        # Conversations
        convs = await self.db.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE importance_level >= 8) as high_importance,
                   AVG(importance_level) as avg_importance
            FROM conversations
        """)
        stats['conversations'] = dict(convs)

        return stats


# CLI testing
if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 60)
        print("Memory Consolidation Service Test")
        print("=" * 60)

        service = MemoryConsolidationService()

        try:
            # Get stats first
            print("\n📊 Memory Statistics:")
            stats = await service.get_consolidation_stats()
            for source, data in stats.items():
                print(f"\n   {source}:")
                for key, value in data.items():
                    print(f"      {key}: {value}")

            # Test consolidation
            print("\n🔄 Testing consolidation...")
            result = await service.consolidate_all()

            print(f"\n✅ Results:")
            print(f"   Total pairs: {result['total_pairs']}")
            print(f"   Sources: {result['source_counts']}")

            # Show sample
            if result['pairs']:
                print(f"\n📝 Sample pair:")
                sample = result['pairs'][0]
                print(f"   Source: {sample['source']}")
                print(f"   Input: {sample['input_text'][:60]}...")
                print(f"   Output: {sample['output_text'][:60]}...")

        finally:
            await service.disconnect()

        print("\n✅ Test complete!")

    asyncio.run(test())
