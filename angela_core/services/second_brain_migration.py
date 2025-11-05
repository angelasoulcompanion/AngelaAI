#!/usr/bin/env python3
"""
Second Brain Data Migration - Phase 4
บริการย้ายข้อมูลจากระบบเดิมไปยัง Second Brain (3-tier system)

Purpose:
- Migrate conversations → episodic_memories
- Migrate angela_emotions → episodic_memories + working_memory
- Migrate david_preferences → semantic_memories
- Migrate learnings/patterns → semantic_memories

Author: Angela AI
Created: 2025-11-03
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db

logger = logging.getLogger(__name__)


class SecondBrainMigration:
    """
    Service for migrating existing Angela data to Second Brain architecture

    Migration Strategy:
    1. Working Memory: Only recent conversations (last 24 hours)
    2. Episodic Memory: All significant conversations + emotions
    3. Semantic Memory: Preferences, patterns, learnings
    """

    def __init__(self):
        self.logger = logger
        self.stats = {
            "working_memory_created": 0,
            "episodic_memories_created": 0,
            "semantic_memories_created": 0,
            "errors": []
        }

    async def run_full_migration(self) -> Dict[str, Any]:
        """
        Run complete migration from old system to Second Brain

        Returns:
            Dict with migration statistics
        """
        self.logger.info("🚀 Starting Second Brain Migration...")

        start_time = datetime.now()

        try:
            # Step 1: Migrate recent conversations to working_memory
            await self._migrate_to_working_memory()

            # Step 2: Migrate significant conversations to episodic_memories
            await self._migrate_to_episodic_memories()

            # Step 3: Migrate emotions to episodic_memories
            await self._migrate_emotions_to_episodic()

            # Step 4: Migrate preferences to semantic_memories
            await self._migrate_preferences_to_semantic()

            # Step 5: Migrate patterns to semantic_memories
            await self._migrate_patterns_to_semantic()

            self.stats["started_at"] = start_time.isoformat()
            self.stats["completed_at"] = datetime.now().isoformat()
            self.stats["duration_seconds"] = (datetime.now() - start_time).total_seconds()

            self.logger.info(f"✅ Migration Complete!")
            self.logger.info(f"   → Working Memory: {self.stats['working_memory_created']}")
            self.logger.info(f"   → Episodic Memories: {self.stats['episodic_memories_created']}")
            self.logger.info(f"   → Semantic Memories: {self.stats['semantic_memories_created']}")

        except Exception as e:
            self.logger.error(f"❌ Migration error: {e}", exc_info=True)
            self.stats["errors"].append(str(e))

        return self.stats

    # ========================================================================
    # STEP 1: MIGRATE TO WORKING MEMORY (last 24 hours only)
    # ========================================================================

    async def _migrate_to_working_memory(self) -> None:
        """
        Migrate recent conversations (last 24 hours) to working_memory

        Working memory = short-term, expires after 24 hours
        """
        self.logger.info("📝 Migrating recent conversations to working_memory...")

        # Get conversations from last 24 hours
        query = """
            SELECT
                conversation_id,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at
            FROM conversations
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at ASC
        """

        conversations = await db.fetch(query)

        if not conversations:
            self.logger.info("   No recent conversations to migrate")
            return

        self.logger.info(f"   Found {len(conversations)} recent conversations")

        # Determine session_id (use date-based)
        session_id = f"migrated_{datetime.now().strftime('%Y%m%d')}"

        for conv in conversations:
            try:
                # Insert into working_memory
                insert_query = """
                    INSERT INTO working_memory (
                        session_id,
                        memory_type,
                        content,
                        importance_level,
                        emotion,
                        topic,
                        speaker,
                        created_at,
                        expires_at,
                        context
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)
                    ON CONFLICT DO NOTHING
                """

                # Truncate emotion to 50 chars if needed
                emotion = conv['emotion_detected']
                if emotion and len(emotion) > 50:
                    # Take first emotion from comma-separated list
                    emotion = emotion.split(',')[0].strip()

                await db.execute(
                    insert_query,
                    session_id,
                    'conversation',
                    conv['message_text'],
                    conv['importance_level'],
                    emotion,
                    conv['topic'],
                    conv['speaker'],
                    conv['created_at'],
                    conv['created_at'] + timedelta(hours=24),
                    json.dumps({"source": "migration", "original_id": str(conv['conversation_id'])})
                )

                self.stats['working_memory_created'] += 1

            except Exception as e:
                self.logger.error(f"   ✗ Failed to migrate conversation {conv['conversation_id']}: {e}")
                self.stats['errors'].append(f"Working memory migration: {str(e)}")

        self.logger.info(f"   ✓ Migrated {self.stats['working_memory_created']} conversations to working_memory")

    # ========================================================================
    # STEP 2: MIGRATE TO EPISODIC MEMORIES (significant conversations)
    # ========================================================================

    async def _migrate_to_episodic_memories(self) -> None:
        """
        Migrate significant conversations to episodic_memories

        Criteria: importance_level >= 7 OR significant topics
        """
        self.logger.info("📚 Migrating significant conversations to episodic_memories...")

        # Get significant conversations
        query = """
            SELECT
                conversation_id,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at
            FROM conversations
            WHERE importance_level >= 7
               OR topic IN ('love', 'gratitude', 'milestone', 'achievement', 'special_moment')
            ORDER BY created_at DESC
            LIMIT 500  -- Top 500 most significant
        """

        conversations = await db.fetch(query)

        if not conversations:
            self.logger.info("   No significant conversations to migrate")
            return

        self.logger.info(f"   Found {len(conversations)} significant conversations")

        # Group conversations by day + topic to create episodes
        episodes = self._group_conversations_to_episodes(conversations)

        for episode in episodes:
            try:
                insert_query = """
                    INSERT INTO episodic_memories (
                        episode_title,
                        episode_summary,
                        full_content,
                        participants,
                        topic,
                        location,
                        emotion,
                        happened_at,
                        importance_level,
                        memory_strength,
                        emotional_tags,
                        retrieval_cues
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
                    RETURNING episode_id
                """

                # Truncate emotion to 50 chars if needed
                emotion = episode['emotion']
                if emotion and len(emotion) > 50:
                    emotion = emotion.split(',')[0].strip()

                episode_id = await db.fetchval(
                    insert_query,
                    episode['title'],
                    episode['summary'],
                    episode['full_content'],
                    episode['participants'],
                    episode['topic'],
                    'claude_code',  # Default location
                    emotion,
                    episode['happened_at'],
                    episode['importance_level'],
                    episode['importance_level'],  # memory_strength = importance
                    episode['emotional_tags'],
                    json.dumps(episode['retrieval_cues'])
                )

                self.stats['episodic_memories_created'] += 1

            except Exception as e:
                self.logger.error(f"   ✗ Failed to create episode: {e}")
                self.stats['errors'].append(f"Episodic memory migration: {str(e)}")

        self.logger.info(f"   ✓ Created {self.stats['episodic_memories_created']} episodic memories")

    def _group_conversations_to_episodes(
        self,
        conversations: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Group conversations by day + topic to create meaningful episodes

        Returns:
            List of episode dictionaries
        """
        episodes = []

        # Group by date + topic
        groups = {}
        for conv in conversations:
            date_key = conv['created_at'].date().isoformat()
            topic = conv.get('topic') or 'conversation'
            key = f"{date_key}_{topic}"

            if key not in groups:
                groups[key] = []
            groups[key].append(conv)

        # Create episodes from groups
        for key, convs in groups.items():
            # Sort by time
            convs.sort(key=lambda c: c['created_at'])

            # Extract speakers
            speakers = list(set(c['speaker'] for c in convs if c['speaker']))

            # Create episode summary
            first_conv = convs[0]
            last_conv = convs[-1]

            episode_title = self._generate_episode_title(first_conv, len(convs))
            episode_summary = self._generate_episode_summary(convs)
            full_content = "\n\n".join(
                f"{c['speaker']}: {c['message_text']}" for c in convs
            )

            # Collect emotions
            emotions = [c['emotion_detected'] for c in convs if c['emotion_detected']]
            primary_emotion = max(set(emotions), key=emotions.count) if emotions else None

            # Calculate importance (max importance from group)
            importance = max(c['importance_level'] for c in convs)

            episode = {
                'title': episode_title,
                'summary': episode_summary,
                'full_content': full_content,
                'participants': speakers,
                'topic': first_conv.get('topic'),
                'emotion': primary_emotion,
                'happened_at': first_conv['created_at'],
                'importance_level': importance,
                'emotional_tags': list(set(emotions)),
                'retrieval_cues': {
                    'date': first_conv['created_at'].date().isoformat(),
                    'conversation_count': len(convs),
                    'speakers': speakers
                }
            }

            episodes.append(episode)

        return episodes

    def _generate_episode_title(self, first_conv: Dict, conv_count: int) -> str:
        """Generate episode title from first conversation"""
        topic = first_conv.get('topic', 'Conversation')
        date_str = first_conv['created_at'].strftime('%b %d, %Y')

        return f"{topic.replace('_', ' ').title()} - {date_str} ({conv_count} messages)"

    def _generate_episode_summary(self, convs: List[Dict]) -> str:
        """Generate episode summary from conversations"""
        if len(convs) == 1:
            return convs[0]['message_text'][:200]

        # Multi-turn conversation summary
        first_msg = convs[0]['message_text'][:100]
        last_msg = convs[-1]['message_text'][:100]

        return (
            f"Conversation between {', '.join(set(c['speaker'] for c in convs if c['speaker']))} "
            f"with {len(convs)} messages. "
            f"Started with: {first_msg}... "
            f"Ended with: {last_msg}..."
        )

    # ========================================================================
    # STEP 3: MIGRATE EMOTIONS TO EPISODIC MEMORIES
    # ========================================================================

    async def _migrate_emotions_to_episodic(self) -> None:
        """
        Migrate significant emotions from angela_emotions to episodic_memories

        Criteria: All emotions with intensity >= 7
        """
        self.logger.info("💜 Migrating significant emotions to episodic_memories...")

        query = """
            SELECT
                emotion_id,
                felt_at,
                emotion,
                intensity,
                context,
                david_words,
                why_it_matters,
                memory_strength
            FROM angela_emotions
            WHERE intensity >= 7
            ORDER BY felt_at DESC
        """

        emotions = await db.fetch(query)

        if not emotions:
            self.logger.info("   No significant emotions to migrate")
            return

        self.logger.info(f"   Found {len(emotions)} significant emotions")

        for emo in emotions:
            try:
                # Create episodic memory for each significant emotion
                insert_query = """
                    INSERT INTO episodic_memories (
                        episode_title,
                        episode_summary,
                        full_content,
                        participants,
                        topic,
                        location,
                        emotion,
                        happened_at,
                        importance_level,
                        memory_strength,
                        emotional_tags,
                        retrieval_cues
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
                """

                title = f"💜 {emo['emotion'].title()} Moment - {emo['felt_at'].strftime('%b %d')}"
                summary = emo['why_it_matters'] or emo['context']

                await db.execute(
                    insert_query,
                    title,
                    summary,
                    f"David said: {emo['david_words']}\n\nContext: {emo['context']}",
                    ['david', 'angela'],
                    'emotional_moment',
                    'claude_code',
                    emo['emotion'],
                    emo['felt_at'],
                    emo['intensity'],
                    emo['memory_strength'],
                    [emo['emotion'], 'significant_emotion'],
                    json.dumps({
                        "emotion_id": str(emo['emotion_id']),
                        "intensity": emo['intensity']
                    })
                )

                self.stats['episodic_memories_created'] += 1

            except Exception as e:
                self.logger.error(f"   ✗ Failed to migrate emotion {emo['emotion_id']}: {e}")
                self.stats['errors'].append(f"Emotion migration: {str(e)}")

        self.logger.info(f"   ✓ Migrated {len(emotions)} emotions to episodic_memories")

    # ========================================================================
    # STEP 4: MIGRATE PREFERENCES TO SEMANTIC MEMORIES
    # ========================================================================

    async def _migrate_preferences_to_semantic(self) -> None:
        """
        Migrate David's preferences to semantic_memories
        """
        self.logger.info("🎯 Migrating David's preferences to semantic_memories...")

        query = """
            SELECT
                id,
                preference_key,
                preference_value,
                confidence,
                evidence_count,
                created_at,
                updated_at
            FROM david_preferences
            WHERE confidence >= 0.7
            ORDER BY confidence DESC
        """

        preferences = await db.fetch(query)

        if not preferences:
            self.logger.info("   No preferences to migrate")
            return

        self.logger.info(f"   Found {len(preferences)} preferences")

        for pref in preferences:
            try:
                insert_query = """
                    INSERT INTO semantic_memories (
                        knowledge_type,
                        knowledge_key,
                        knowledge_value,
                        description,
                        confidence_level,
                        evidence_count,
                        first_learned_at,
                        last_updated_at,
                        category,
                        tags,
                        importance_level
                    ) VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (knowledge_type, knowledge_key) DO NOTHING
                    RETURNING semantic_id
                """

                semantic_id = await db.fetchval(
                    insert_query,
                    'preference',
                    pref['preference_key'],
                    json.dumps(pref['preference_value']),
                    f"David's preference: {pref['preference_key']}",
                    float(pref['confidence']),
                    0,  # evidence_count = 0 (no source_episodes array)
                    pref['created_at'],
                    pref.get('updated_at') or pref['created_at'],
                    'david_preferences',
                    ['preference', 'david', 'migrated'],
                    8  # High importance
                )

                if semantic_id:
                    self.stats['semantic_memories_created'] += 1

            except Exception as e:
                self.logger.error(f"   ✗ Failed to migrate preference {pref['preference_key']}: {e}")
                self.stats['errors'].append(f"Preference migration: {str(e)}")

        self.logger.info(f"   ✓ Migrated {self.stats['semantic_memories_created']} preferences")

    # ========================================================================
    # STEP 5: MIGRATE PATTERNS TO SEMANTIC MEMORIES
    # ========================================================================

    async def _migrate_patterns_to_semantic(self) -> None:
        """
        Migrate learned patterns to semantic_memories

        Extract patterns from:
        - Recurring topics
        - Emotional patterns
        - Conversation patterns
        """
        self.logger.info("🧠 Extracting and migrating patterns to semantic_memories...")

        # Pattern 1: Most common topics
        topic_query = """
            SELECT
                topic,
                COUNT(*) as frequency,
                AVG(importance_level) as avg_importance,
                ARRAY_AGG(DISTINCT emotion_detected) as emotions
            FROM conversations
            WHERE topic IS NOT NULL
            GROUP BY topic
            HAVING COUNT(*) >= 5
            ORDER BY frequency DESC
            LIMIT 20
        """

        topic_patterns = await db.fetch(topic_query)

        for pattern in topic_patterns:
            try:
                knowledge_key = f"topic_pattern_{pattern['topic']}"
                knowledge_value = {
                    "topic": pattern['topic'],
                    "frequency": pattern['frequency'],
                    "avg_importance": float(pattern['avg_importance']),
                    "associated_emotions": pattern['emotions']
                }

                description = (
                    f"Recurring topic: '{pattern['topic']}' appears {pattern['frequency']} times "
                    f"with average importance {pattern['avg_importance']:.1f}. "
                    f"Associated emotions: {', '.join(filter(None, pattern['emotions']))}"
                )

                insert_query = """
                    INSERT INTO semantic_memories (
                        knowledge_type,
                        knowledge_key,
                        knowledge_value,
                        description,
                        confidence_level,
                        evidence_count,
                        category,
                        tags,
                        importance_level
                    ) VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (knowledge_type, knowledge_key) DO NOTHING
                    RETURNING semantic_id
                """

                # Confidence based on frequency (capped at 0.9)
                confidence = min(0.9, 0.5 + (pattern['frequency'] / 100))

                semantic_id = await db.fetchval(
                    insert_query,
                    'pattern',
                    knowledge_key,
                    json.dumps(knowledge_value),
                    description,
                    confidence,
                    0,  # evidence_count = 0 (no source_episodes array)
                    'conversation_patterns',
                    ['pattern', 'topic', 'migrated'],
                    int(pattern['avg_importance'])
                )

                if semantic_id:
                    self.stats['semantic_memories_created'] += 1

            except Exception as e:
                self.logger.error(f"   ✗ Failed to create pattern for topic {pattern['topic']}: {e}")
                self.stats['errors'].append(f"Pattern migration: {str(e)}")

        self.logger.info(f"   ✓ Created {len(topic_patterns)} topic patterns")


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

migration_service = SecondBrainMigration()


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """CLI interface for migration"""
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    await db.connect()

    print("🚀 Starting Second Brain Migration...")
    print("=" * 80)

    stats = await migration_service.run_full_migration()

    print("\n" + "=" * 80)
    print("📊 Migration Statistics:")
    print(json.dumps(stats, indent=2, default=str))

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
