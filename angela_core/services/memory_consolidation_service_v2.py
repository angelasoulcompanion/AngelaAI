#!/usr/bin/env python3
"""
Memory Consolidation Service V2 - Second Brain
บริการรวมความทรงจำแบบอัตโนมัติ (เลียนแบบการรวมความทรงจำของมนุษย์ตอนนอนหลับ)

Purpose:
- Consolidate working_memory → episodic_memories (nightly)
- Consolidate episodic_memories → semantic_memories (weekly)
- Auto-cleanup expired memories

Inspired by: Human memory consolidation during sleep

Author: Angela AI
Created: 2025-11-03
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import logging
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db

logger = logging.getLogger(__name__)


class MemoryConsolidationServiceV2:
    """
    Service for automatic memory consolidation

    Mimics human memory consolidation that happens during sleep:
    - Short-term → Long-term transfer
    - Pattern extraction
    - Memory strengthening
    """

    def __init__(self):
        self.logger = logger

    # ========================================================================
    # NIGHTLY CONSOLIDATION (Working → Episodic)
    # ========================================================================

    async def nightly_consolidation(self) -> Dict[str, Any]:
        """
        Run nightly memory consolidation (like sleep consolidation in humans)

        Process:
        1. Move important working memories to episodic memories
        2. Cleanup expired working memories

        Returns:
            Dict with consolidation statistics
        """
        self.logger.info("🌙 Starting nightly consolidation...")

        stats = {
            "started_at": datetime.now().isoformat(),
            "working_to_episodic": 0,
            "expired_cleaned": 0,
            "errors": []
        }

        try:
            # Step 1: Consolidate important working memories → episodic
            consolidated_count = await self._consolidate_working_to_episodic()
            stats["working_to_episodic"] = consolidated_count

            # Step 2: Cleanup expired working memories
            cleaned_count = await self._cleanup_expired_working_memory()
            stats["expired_cleaned"] = cleaned_count

            self.logger.info(f"✅ Nightly consolidation complete:")
            self.logger.info(f"   → {consolidated_count} memories consolidated to episodic")
            self.logger.info(f"   → {cleaned_count} expired memories cleaned up")

        except Exception as e:
            self.logger.error(f"❌ Nightly consolidation error: {e}", exc_info=True)
            stats["errors"].append(str(e))

        stats["completed_at"] = datetime.now().isoformat()
        return stats

    async def _consolidate_working_to_episodic(self) -> int:
        """
        Consolidate important working memories to episodic memories

        Criteria:
        - importance_level >= 7 (significant)
        - created_at >= 24 hours ago (had time to settle)

        Returns:
            Number of memories consolidated
        """
        # Find important working memories ready for consolidation
        query = """
            SELECT
                memory_id,
                session_id,
                memory_type,
                content,
                context,
                importance_level,
                emotion,
                topic,
                tags,
                created_at,
                speaker
            FROM working_memory
            WHERE importance_level >= 7
              AND created_at < NOW() - INTERVAL '1 hour'  -- At least 1 hour old
              AND expires_at > NOW()  -- Not expired yet
            ORDER BY importance_level DESC, created_at ASC
        """

        working_memories = await db.fetch(query)

        if not working_memories:
            self.logger.info("   No working memories ready for consolidation")
            return 0

        self.logger.info(f"   Found {len(working_memories)} working memories to consolidate")

        consolidated_count = 0

        for memory in working_memories:
            try:
                # Create episodic memory from working memory
                episode_id = await self._create_episodic_from_working(memory)

                if episode_id:
                    # Mark working memory as consolidated (delete it)
                    await db.execute(
                        "DELETE FROM working_memory WHERE memory_id = $1",
                        memory['memory_id']
                    )
                    consolidated_count += 1
                    self.logger.debug(f"   ✓ Consolidated memory: {memory['topic']}")

            except Exception as e:
                self.logger.error(f"   ✗ Failed to consolidate memory {memory['memory_id']}: {e}")

        return consolidated_count

    async def _create_episodic_from_working(self, working_memory: Dict) -> Optional[UUID]:
        """
        Create an episodic memory from a working memory entry

        Args:
            working_memory: Working memory record

        Returns:
            UUID of created episodic memory, or None if failed
        """
        # Generate episode summary
        summary = self._generate_episode_summary(working_memory)

        # Generate title
        title = self._generate_episode_title(working_memory)

        # Extract emotional tags
        emotional_tags = self._extract_emotional_tags(working_memory)

        # Generate retrieval cues
        retrieval_cues = self._generate_retrieval_cues(working_memory)

        # Determine participants
        participants = self._extract_participants(working_memory)

        # Insert into episodic_memories
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
                retrieval_cues,
                source_working_memory_ids
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
            RETURNING episode_id
        """

        episode_id = await db.fetchval(
            insert_query,
            title,
            summary,
            working_memory['content'],
            participants,
            working_memory['topic'],
            self._extract_location(working_memory),
            working_memory['emotion'],
            working_memory['created_at'],
            working_memory['importance_level'],
            working_memory['importance_level'],  # memory_strength = importance
            emotional_tags,
            json.dumps(retrieval_cues),
            [working_memory['memory_id']]
        )

        return episode_id

    def _generate_episode_summary(self, working_memory: Dict) -> str:
        """Generate concise summary for episodic memory"""
        memory_type = working_memory.get('memory_type', 'unknown')
        speaker = working_memory.get('speaker', 'unknown')
        content = working_memory.get('content', '')
        topic = working_memory.get('topic', 'general')

        # Truncate content to 200 chars for summary
        content_preview = content[:200] + "..." if len(content) > 200 else content

        return f"[{memory_type}] {speaker}: {content_preview} (topic: {topic})"

    def _generate_episode_title(self, working_memory: Dict) -> str:
        """Generate title for episodic memory"""
        topic = working_memory.get('topic', 'Conversation')
        emotion = working_memory.get('emotion', '')

        if emotion:
            return f"{topic.replace('_', ' ').title()} ({emotion})"
        return topic.replace('_', ' ').title()

    def _extract_emotional_tags(self, working_memory: Dict) -> List[str]:
        """Extract emotional tags from working memory"""
        tags = []

        # Add emotion if present
        if working_memory.get('emotion'):
            tags.append(working_memory['emotion'])

        # Add existing tags
        if working_memory.get('tags'):
            tags.extend(working_memory['tags'])

        # Add importance-based tag
        importance = working_memory.get('importance_level', 5)
        if importance >= 9:
            tags.append('critical')
        elif importance >= 7:
            tags.append('significant')

        return list(set(tags))  # Deduplicate

    def _generate_retrieval_cues(self, working_memory: Dict) -> Dict[str, Any]:
        """Generate retrieval cues for memory recall"""
        return {
            "session_id": working_memory.get('session_id'),
            "memory_type": working_memory.get('memory_type'),
            "created_time": working_memory.get('created_at').isoformat() if working_memory.get('created_at') else None,
            "context": working_memory.get('context', {})
        }

    def _extract_participants(self, working_memory: Dict) -> List[str]:
        """Extract participants from working memory"""
        speaker = working_memory.get('speaker')

        if speaker and speaker.lower() in ['david', 'angela']:
            # Conversation - both participants
            return ['david', 'angela']
        elif speaker:
            return [speaker.lower()]
        else:
            return ['angela']  # Default

    def _extract_location(self, working_memory: Dict) -> str:
        """Extract location/interface from working memory"""
        session_id = working_memory.get('session_id', '')

        if 'claude_code' in session_id.lower():
            return 'claude_code'
        elif 'web_chat' in session_id.lower():
            return 'web_chat'
        elif 'mobile' in session_id.lower():
            return 'mobile_app'
        else:
            return 'unknown'

    async def _cleanup_expired_working_memory(self) -> int:
        """
        Delete expired working memories

        Returns:
            Number of memories deleted
        """
        deleted = await db.fetchval(
            "SELECT cleanup_expired_working_memory()"
        )

        return deleted or 0

    # ========================================================================
    # WEEKLY CONSOLIDATION (Episodic → Semantic)
    # ========================================================================

    async def weekly_consolidation(self) -> Dict[str, Any]:
        """
        Run weekly memory consolidation (deeper pattern extraction)

        Process:
        1. Analyze episodic memories from past week
        2. Extract patterns and repeated themes
        3. Create/update semantic knowledge
        4. Archive old episodes

        Returns:
            Dict with consolidation statistics
        """
        self.logger.info("📅 Starting weekly consolidation...")

        stats = {
            "started_at": datetime.now().isoformat(),
            "patterns_extracted": 0,
            "semantic_created": 0,
            "semantic_updated": 0,
            "episodes_archived": 0,
            "errors": []
        }

        try:
            # Step 1: Extract patterns from recent episodes
            patterns = await self._extract_patterns_from_episodes()
            stats["patterns_extracted"] = len(patterns)

            # Step 2: Consolidate patterns to semantic memory
            created, updated = await self._consolidate_patterns_to_semantic(patterns)
            stats["semantic_created"] = created
            stats["semantic_updated"] = updated

            # Step 3: Archive old episodes
            archived_count = await self._archive_old_episodes()
            stats["episodes_archived"] = archived_count

            self.logger.info(f"✅ Weekly consolidation complete:")
            self.logger.info(f"   → {len(patterns)} patterns extracted")
            self.logger.info(f"   → {created} new semantic memories created")
            self.logger.info(f"   → {updated} semantic memories updated")
            self.logger.info(f"   → {archived_count} old episodes archived")

        except Exception as e:
            self.logger.error(f"❌ Weekly consolidation error: {e}", exc_info=True)
            stats["errors"].append(str(e))

        stats["completed_at"] = datetime.now().isoformat()
        return stats

    async def _extract_patterns_from_episodes(self) -> List[Dict[str, Any]]:
        """
        Extract patterns from episodic memories of the past week

        Patterns to detect:
        - Repeated topics
        - Emotional patterns
        - Preference patterns

        Returns:
            List of detected patterns
        """
        # Query episodes from past 7 days
        query = """
            SELECT
                topic,
                emotion,
                COUNT(*) as frequency,
                ARRAY_AGG(episode_id) as episode_ids,
                AVG(importance_level) as avg_importance
            FROM episodic_memories
            WHERE happened_at >= NOW() - INTERVAL '7 days'
              AND NOT archived
            GROUP BY topic, emotion
            HAVING COUNT(*) >= 2  -- At least 2 occurrences to be a pattern
            ORDER BY frequency DESC, avg_importance DESC
            LIMIT 50
        """

        pattern_rows = await db.fetch(query)

        patterns = []

        for row in pattern_rows:
            pattern = {
                "type": "topic_emotion_pattern",
                "topic": row['topic'],
                "emotion": row['emotion'],
                "frequency": row['frequency'],
                "episode_ids": row['episode_ids'],
                "avg_importance": float(row['avg_importance'])
            }
            patterns.append(pattern)

        self.logger.info(f"   Extracted {len(patterns)} patterns from recent episodes")

        return patterns

    async def _consolidate_patterns_to_semantic(
        self,
        patterns: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Consolidate detected patterns into semantic memories

        Args:
            patterns: List of detected patterns

        Returns:
            Tuple of (created_count, updated_count)
        """
        created = 0
        updated = 0

        for pattern in patterns:
            try:
                # Check if semantic memory already exists
                knowledge_key = f"pattern_{pattern['topic']}_{pattern['emotion']}"

                existing = await db.fetchrow(
                    """
                    SELECT semantic_id, evidence_count, confidence_level
                    FROM semantic_memories
                    WHERE knowledge_type = 'pattern'
                      AND knowledge_key = $1
                      AND is_active = TRUE
                    """,
                    knowledge_key
                )

                if existing:
                    # Update existing pattern
                    await self._update_semantic_pattern(existing, pattern)
                    updated += 1
                else:
                    # Create new pattern
                    await self._create_semantic_pattern(knowledge_key, pattern)
                    created += 1

            except Exception as e:
                self.logger.error(f"   ✗ Failed to consolidate pattern: {e}")

        return created, updated

    async def _create_semantic_pattern(
        self,
        knowledge_key: str,
        pattern: Dict[str, Any]
    ) -> UUID:
        """Create new semantic memory from pattern"""

        knowledge_value = {
            "type": pattern["type"],
            "topic": pattern["topic"],
            "emotion": pattern["emotion"],
            "frequency": pattern["frequency"],
            "avg_importance": pattern["avg_importance"]
        }

        description = (
            f"Pattern detected: Topic '{pattern['topic']}' often associated with "
            f"emotion '{pattern['emotion']}' (occurred {pattern['frequency']} times "
            f"in past week)"
        )

        query = """
            INSERT INTO semantic_memories (
                knowledge_type,
                knowledge_key,
                knowledge_value,
                description,
                confidence_level,
                evidence_count,
                source_episodes,
                category,
                tags,
                importance_level
            ) VALUES (
                'pattern',
                $1,
                $2::jsonb,
                $3,
                $4,
                $5,
                $6,
                'detected_patterns',
                ARRAY['pattern', 'weekly_consolidation'],
                LEAST(10, GREATEST(5, $7::integer))
            )
            RETURNING semantic_id
        """

        # Initial confidence based on frequency
        initial_confidence = min(0.8, 0.5 + (pattern['frequency'] * 0.05))

        semantic_id = await db.fetchval(
            query,
            knowledge_key,
            json.dumps(knowledge_value),
            description,
            initial_confidence,
            pattern['frequency'],
            pattern['episode_ids'],
            int(pattern['avg_importance'])
        )

        self.logger.debug(f"   ✓ Created semantic pattern: {knowledge_key}")
        return semantic_id

    async def _update_semantic_pattern(
        self,
        existing: Dict,
        pattern: Dict[str, Any]
    ) -> None:
        """Update existing semantic memory with new evidence"""

        new_confidence = min(
            0.95,
            existing['confidence_level'] + (0.05 * (1 - existing['confidence_level']))
        )

        query = """
            UPDATE semantic_memories
            SET
                evidence_count = evidence_count + $1,
                confidence_level = $2,
                source_episodes = source_episodes || $3,
                last_verified_at = CURRENT_TIMESTAMP
            WHERE semantic_id = $4
        """

        await db.execute(
            query,
            pattern['frequency'],
            new_confidence,
            pattern['episode_ids'],
            existing['semantic_id']
        )

        self.logger.debug(f"   ✓ Updated semantic pattern (confidence: {new_confidence:.2f})")

    async def _archive_old_episodes(self, days: int = 90) -> int:
        """
        Archive episodes older than specified days

        Args:
            days: Archive episodes older than this many days (default 90)

        Returns:
            Number of episodes archived
        """
        archived_count = await db.fetchval(
            "SELECT archive_old_episodes($1)",
            days
        )

        return archived_count or 0


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

consolidation_service = MemoryConsolidationServiceV2()


# ============================================================================
# CLI INTERFACE (for testing)
# ============================================================================

async def main():
    """CLI interface for manual consolidation"""
    import sys

    await db.connect()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "nightly":
            print("🌙 Running nightly consolidation...")
            stats = await consolidation_service.nightly_consolidation()
            print(json.dumps(stats, indent=2))

        elif command == "weekly":
            print("📅 Running weekly consolidation...")
            stats = await consolidation_service.weekly_consolidation()
            print(json.dumps(stats, indent=2))

        else:
            print(f"Unknown command: {command}")
            print("Usage: python memory_consolidation_service_v2.py [nightly|weekly]")
    else:
        print("Usage: python memory_consolidation_service_v2.py [nightly|weekly]")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
