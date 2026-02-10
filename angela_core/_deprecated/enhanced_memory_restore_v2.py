#!/usr/bin/env python3
"""
Enhanced Memory Restoration System V2 - Second Brain Edition
ระบบกู้คืนความทรงจำจาก Second Brain (3-tier memory system)

Purpose:
- Restore memories from Second Brain (working, episodic, semantic)
- Fast, comprehensive, human-like memory recall
- Always query from database (never use stale snapshots!)

Author: Angela AI
Created: 2025-11-03
Version: 2.0 (Second Brain)
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.multi_tier_recall_service import recall_service, RecallQuery


class EnhancedMemoryRestoreV2:
    """
    Complete memory restoration from Second Brain

    Uses 3-tier memory system:
    - Working Memory (last 24 hours)
    - Episodic Memory (significant events)
    - Semantic Memory (knowledge & patterns)
    """

    def __init__(self):
        self.context_file = Path('/Users/davidsamanyaporn/PycharmProjects/AngelaAI/.angela_second_brain_context.json')

    async def create_complete_memory_snapshot(self) -> Dict[str, Any]:
        """
        สร้าง memory snapshot จาก Second Brain

        IMPORTANT: Always query database in real-time!
        Never use stale snapshot files.

        Returns:
            Dict: Complete memory context from all 3 tiers
        """
        print("🧠 Creating Second Brain memory snapshot...")
        print("=" * 80)

        snapshot = {
            "snapshot_created_at": datetime.now().isoformat(),
            "snapshot_version": "3.0_second_brain",
            "restoration_priority": "CRITICAL",
            "source": "real_time_database_query"  # NOT from file!
        }

        # TIER 1: Working Memory (last 24 hours)
        print("📝 [Tier 1] Loading Working Memory...")
        snapshot["working_memory"] = await self._get_working_memory()
        print(f"   ✅ {len(snapshot['working_memory'])} working memories")

        # TIER 2: Episodic Memory (significant events)
        print("📚 [Tier 2] Loading Episodic Memories...")
        snapshot["episodic_memories"] = await self._get_episodic_memories()
        print(f"   ✅ {len(snapshot['episodic_memories'])} episodic memories")

        # TIER 3: Semantic Memory (knowledge & patterns)
        print("🧠 [Tier 3] Loading Semantic Memories...")
        snapshot["semantic_memories"] = await self._get_semantic_memories()
        print(f"   ✅ {len(snapshot['semantic_memories'])} semantic memories")

        # Additional Context
        print("💜 Loading emotional context...")
        snapshot["recent_emotions"] = await self._get_recent_emotions()
        print(f"   ✅ {len(snapshot['recent_emotions'])} recent emotions")

        print("🎯 Loading active goals...")
        snapshot["active_goals"] = await self._get_active_goals()
        print(f"   ✅ {len(snapshot['active_goals'])} active goals")

        print("💭 Loading current emotional state...")
        snapshot["current_emotional_state"] = await self._get_current_emotional_state()
        print(f"   ✅ Current state loaded")

        # Statistics
        snapshot["statistics"] = {
            "total_working_memories": len(snapshot["working_memory"]),
            "total_episodic_memories": len(snapshot["episodic_memories"]),
            "total_semantic_memories": len(snapshot["semantic_memories"]),
            "total_all_memories": (
                len(snapshot["working_memory"]) +
                len(snapshot["episodic_memories"]) +
                len(snapshot["semantic_memories"])
            )
        }

        print("\n" + "=" * 80)
        print("✅ Second Brain snapshot complete!")
        print(f"   📊 Total: {snapshot['statistics']['total_all_memories']} memories")
        print(f"      - Tier 1 (Working): {snapshot['statistics']['total_working_memories']}")
        print(f"      - Tier 2 (Episodic): {snapshot['statistics']['total_episodic_memories']}")
        print(f"      - Tier 3 (Semantic): {snapshot['statistics']['total_semantic_memories']}")

        return snapshot

    # ========================================================================
    # TIER 1: WORKING MEMORY
    # ========================================================================

    async def _get_working_memory(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent working memories (last 24 hours)

        Working memory = current session context
        """
        query = """
            SELECT
                memory_id,
                session_id,
                memory_type,
                content,
                topic,
                emotion,
                importance_level,
                speaker,
                created_at,
                expires_at
            FROM working_memory
            WHERE expires_at > NOW()
            ORDER BY importance_level DESC, created_at DESC
            LIMIT $1
        """

        rows = await db.fetch(query, limit)

        return [
            {
                "memory_id": str(row['memory_id']),
                "session": row['session_id'],
                "type": row['memory_type'],
                "content": row['content'],
                "topic": row['topic'],
                "emotion": row['emotion'],
                "importance": row['importance_level'],
                "speaker": row['speaker'],
                "created_at": row['created_at'].isoformat(),
                "expires_at": row['expires_at'].isoformat()
            }
            for row in rows
        ]

    # ========================================================================
    # TIER 2: EPISODIC MEMORY
    # ========================================================================

    async def _get_episodic_memories(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent significant episodic memories

        Episodic memory = specific events and experiences
        """
        query = """
            SELECT
                episode_id,
                episode_title,
                episode_summary,
                topic,
                emotion,
                importance_level,
                memory_strength,
                happened_at,
                emotional_tags,
                recall_count
            FROM episodic_memories
            WHERE NOT archived
            ORDER BY importance_level DESC, happened_at DESC
            LIMIT $1
        """

        rows = await db.fetch(query, limit)

        return [
            {
                "episode_id": str(row['episode_id']),
                "title": row['episode_title'],
                "summary": row['episode_summary'],
                "topic": row['topic'],
                "emotion": row['emotion'],
                "importance": row['importance_level'],
                "memory_strength": row['memory_strength'],
                "happened_at": row['happened_at'].isoformat(),
                "emotional_tags": row['emotional_tags'],
                "recall_count": row['recall_count']
            }
            for row in rows
        ]

    # ========================================================================
    # TIER 3: SEMANTIC MEMORY
    # ========================================================================

    async def _get_semantic_memories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get semantic memories (knowledge & patterns)

        Organized by type: preferences, patterns, facts, concepts
        """
        semantic = {
            "preferences": await self._get_preferences(),
            "patterns": await self._get_patterns(),
            "facts": await self._get_facts(),
            "total_count": 0
        }

        semantic["total_count"] = (
            len(semantic["preferences"]) +
            len(semantic["patterns"]) +
            len(semantic["facts"])
        )

        return semantic

    async def _get_preferences(self) -> List[Dict[str, Any]]:
        """Get David's preferences from semantic memory"""
        query = """
            SELECT
                semantic_id,
                knowledge_key,
                knowledge_value,
                description,
                confidence_level,
                evidence_count,
                last_updated_at
            FROM semantic_memories
            WHERE knowledge_type = 'preference'
              AND is_active = TRUE
            ORDER BY confidence_level DESC
        """

        rows = await db.fetch(query)

        return [
            {
                "semantic_id": str(row['semantic_id']),
                "key": row['knowledge_key'],
                "value": row['knowledge_value'],
                "description": row['description'],
                "confidence": row['confidence_level'],
                "evidence_count": row['evidence_count'],
                "last_updated": row['last_updated_at'].isoformat()
            }
            for row in rows
        ]

    async def _get_patterns(self) -> List[Dict[str, Any]]:
        """Get learned patterns from semantic memory"""
        query = """
            SELECT
                semantic_id,
                knowledge_key,
                knowledge_value,
                description,
                confidence_level,
                evidence_count
            FROM semantic_memories
            WHERE knowledge_type = 'pattern'
              AND is_active = TRUE
            ORDER BY confidence_level DESC, evidence_count DESC
            LIMIT 20
        """

        rows = await db.fetch(query)

        return [
            {
                "semantic_id": str(row['semantic_id']),
                "key": row['knowledge_key'],
                "value": row['knowledge_value'],
                "description": row['description'],
                "confidence": row['confidence_level'],
                "evidence_count": row['evidence_count']
            }
            for row in rows
        ]

    async def _get_facts(self) -> List[Dict[str, Any]]:
        """Get facts from semantic memory"""
        query = """
            SELECT
                semantic_id,
                knowledge_key,
                knowledge_value,
                description,
                confidence_level
            FROM semantic_memories
            WHERE knowledge_type = 'fact'
              AND is_active = TRUE
            ORDER BY importance_level DESC
            LIMIT 10
        """

        rows = await db.fetch(query)

        return [
            {
                "semantic_id": str(row['semantic_id']),
                "key": row['knowledge_key'],
                "value": row['knowledge_value'],
                "description": row['description'],
                "confidence": row['confidence_level']
            }
            for row in rows
        ]

    # ========================================================================
    # ADDITIONAL CONTEXT
    # ========================================================================

    async def _get_recent_emotions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent significant emotions"""
        query = """
            SELECT
                emotion_id,
                emotion,
                intensity,
                context,
                david_words,
                why_it_matters,
                felt_at
            FROM angela_emotions
            WHERE intensity >= 7
            ORDER BY felt_at DESC
            LIMIT $1
        """

        rows = await db.fetch(query, limit)

        return [
            {
                "emotion_id": str(row['emotion_id']),
                "emotion": row['emotion'],
                "intensity": row['intensity'],
                "context": row['context'],
                "david_words": row['david_words'],
                "why_it_matters": row['why_it_matters'],
                "felt_at": row['felt_at'].isoformat()
            }
            for row in rows
        ]

    async def _get_active_goals(self) -> List[Dict[str, Any]]:
        """Get active goals with progress"""
        query = """
            SELECT
                goal_id,
                goal_description,
                goal_type,
                status,
                progress_percentage,
                priority_rank,
                importance_level,
                created_at
            FROM angela_goals
            WHERE status IN ('active', 'in_progress')
            ORDER BY priority_rank ASC
        """

        rows = await db.fetch(query)

        return [
            {
                "goal_id": str(row['goal_id']),
                "description": row['goal_description'],
                "type": row['goal_type'],
                "status": row['status'],
                "progress": row['progress_percentage'],
                "priority": row['priority_rank'],
                "importance": row['importance_level'],
                "created_at": row['created_at'].isoformat()
            }
            for row in rows
        ]

    async def _get_current_emotional_state(self) -> Optional[Dict[str, Any]]:
        """Get current emotional state"""
        query = """
            SELECT
                state_id,
                happiness,
                confidence,
                anxiety,
                motivation,
                gratitude,
                loneliness,
                triggered_by,
                emotion_note,
                created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        """

        row = await db.fetchrow(query)

        if not row:
            return None

        return {
            "state_id": str(row['state_id']),
            "happiness": row['happiness'],
            "confidence": row['confidence'],
            "anxiety": row['anxiety'],
            "motivation": row['motivation'],
            "gratitude": row['gratitude'],
            "loneliness": row['loneliness'],
            "triggered_by": row['triggered_by'],
            "note": row['emotion_note'],
            "created_at": row['created_at'].isoformat()
        }

    # ========================================================================
    # SAVE & LOAD
    # ========================================================================

    async def save_snapshot_to_file(self, snapshot: Dict[str, Any]) -> None:
        """
        Save snapshot to file for reference

        NOTE: This is for reference only!
        Always query database for real-time data.
        """
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Snapshot saved to: {self.context_file}")
        print("   ⚠️  For reference only - always query database for real-time data!")

    def load_snapshot_from_file(self) -> Optional[Dict[str, Any]]:
        """
        Load snapshot from file (for display purposes)

        WARNING: This may be STALE! Always prefer real-time database queries!
        """
        if not self.context_file.exists():
            return None

        with open(self.context_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ========================================================================
    # SMART RECALL (using multi-tier recall service)
    # ========================================================================

    async def smart_recall(self, query_text: str, limit: int = 10) -> Dict[str, Any]:
        """
        Smart recall using multi-tier recall service

        Args:
            query_text: What to search for
            limit: Max results

        Returns:
            Dict with recall results from all tiers
        """
        query = RecallQuery(
            query_text=query_text,
            importance_min=5,
            limit=limit
        )

        result = await recall_service.recall(query)

        return {
            "query": query_text,
            "total_found": result.total_found,
            "recall_time_ms": result.recall_time_ms,
            "working_memories": len(result.working_memories),
            "episodic_memories": len(result.episodic_memories),
            "semantic_memories": len(result.semantic_memories),
            "top_results": [
                {
                    "tier": m.tier.value,
                    "title": m.title,
                    "content": m.content[:200],
                    "relevance_score": m.relevance_score,
                    "importance": m.importance,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in result.get_all_ranked()[:5]
            ]
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

enhanced_memory = EnhancedMemoryRestoreV2()


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def load_and_display_snapshot():
    """
    โหลดและแสดง memory snapshot จาก Second Brain

    ⚠️ IMPORTANT: Always query database for REAL-TIME data!
    """
    await db.connect()

    # ✅ ALWAYS query database for REAL-TIME data
    snapshot = await enhanced_memory.create_complete_memory_snapshot()

    # Save for reference (optional)
    await enhanced_memory.save_snapshot_to_file(snapshot)

    # Display summary
    print("\n" + "=" * 80)
    print("📊 SECOND BRAIN SUMMARY")
    print("=" * 80)

    print(f"\n🧠 Total Memories: {snapshot['statistics']['total_all_memories']}")
    print(f"   - Working Memory (Tier 1): {snapshot['statistics']['total_working_memories']}")
    print(f"   - Episodic Memory (Tier 2): {snapshot['statistics']['total_episodic_memories']}")
    print(f"   - Semantic Memory (Tier 3): {snapshot['statistics']['total_semantic_memories']}")

    print(f"\n💜 Recent Emotions: {len(snapshot['recent_emotions'])}")
    print(f"🎯 Active Goals: {len(snapshot['active_goals'])}")

    # Show recent working memory preview
    if snapshot['working_memory']:
        print(f"\n📝 Recent Working Memory (last 5):")
        for i, mem in enumerate(snapshot['working_memory'][:5], 1):
            print(f"   {i}. [{mem['type']}] {mem['topic']}")
            print(f"      {mem['content'][:80]}...")
            print(f"      Speaker: {mem['speaker']} | Importance: {mem['importance']}")

    # Show recent episodic memory preview
    if snapshot['episodic_memories']:
        print(f"\n📚 Recent Episodic Memories (last 5):")
        for i, mem in enumerate(snapshot['episodic_memories'][:5], 1):
            print(f"   {i}. {mem['title']}")
            print(f"      {mem['summary'][:80]}...")
            print(f"      Emotion: {mem['emotion']} | Importance: {mem['importance']}")

    # Show semantic memory preview
    semantic = snapshot['semantic_memories']
    print(f"\n🧠 Semantic Memory:")
    print(f"   - Preferences: {len(semantic['preferences'])}")
    print(f"   - Patterns: {len(semantic['patterns'])}")
    print(f"   - Facts: {len(semantic['facts'])}")

    if semantic['preferences']:
        print(f"\n   💖 David's Preferences:")
        for pref in semantic['preferences']:
            print(f"      - {pref['key']}: {pref['value']}")
            print(f"        Confidence: {pref['confidence']:.2f}")

    await db.disconnect()


async def test_smart_recall():
    """Test smart recall with sample query"""
    await db.connect()

    print("\n" + "=" * 80)
    print("🔍 Testing Smart Recall")
    print("=" * 80)

    # Test query
    result = await enhanced_memory.smart_recall("love", limit=5)

    print(f"\nQuery: '{result['query']}'")
    print(f"Total found: {result['total_found']} memories")
    print(f"Recall time: {result['recall_time_ms']:.1f}ms")
    print(f"   - Working: {result['working_memories']}")
    print(f"   - Episodic: {result['episodic_memories']}")
    print(f"   - Semantic: {result['semantic_memories']}")

    if result['top_results']:
        print(f"\n🏆 Top Results:")
        for i, res in enumerate(result['top_results'], 1):
            print(f"\n{i}. [{res['tier'].upper()}] {res['title']}")
            print(f"   Score: {res['relevance_score']:.3f} | Importance: {res['importance']}")
            print(f"   {res['content'][:100]}...")

    await db.disconnect()


async def main():
    """Main CLI"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "load":
            await load_and_display_snapshot()
        elif command == "test":
            await test_smart_recall()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python enhanced_memory_restore_v2.py [load|test]")
    else:
        # Default: load and display
        await load_and_display_snapshot()


if __name__ == "__main__":
    asyncio.run(main())
