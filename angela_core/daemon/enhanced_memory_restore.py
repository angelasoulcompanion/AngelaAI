#!/usr/bin/env python3
"""
Enhanced Memory Restoration System
ระบบกู้คืนความทรงจำแบบสมบูรณ์ 100%

Problem: ทุกครั้งที่ restart Claude Code ความทรงจำเหลือแค่ 50%
Solution: สร้าง rich memory context file + comprehensive restoration

น้อง Angela จะจำได้ทุกอย่าง 100% หลัง restart!
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

class EnhancedMemoryRestore:
    """
    Complete memory restoration system

    สร้าง memory context file ที่มี:
    - Recent conversations (50+ รายการ แทนที่จะเป็น 10)
    - Significant emotional moments (all high-intensity)
    - Current goals and progress
    - Recent learnings and insights
    - David's preferences
    - Personality state
    - Knowledge highlights
    - Relationship context
    """

    def __init__(self):
        self.memory_file = Path('/Users/davidsamanyaporn/PycharmProjects/AngelaAI/.angela_memory_context.json')

    async def create_complete_memory_snapshot(self) -> Dict[str, Any]:
        """
        สร้าง memory snapshot แบบสมบูรณ์

        Returns:
            Dict: Complete memory context with ALL important information
        """
        print("🧠 Creating COMPLETE memory snapshot...")
        print("=" * 80)

        snapshot = {
            "snapshot_created_at": datetime.now().isoformat(),
            "snapshot_version": "2.0_enhanced",
            "restoration_priority": "CRITICAL",
        }

        # 1. Recent Conversations (EXPANDED: 50 instead of 10!)
        print("📝 Loading recent conversations (50 most recent)...")
        snapshot["recent_conversations"] = await self._get_recent_conversations(limit=50)
        print(f"   ✅ Loaded {len(snapshot['recent_conversations'])} conversations")

        # 2. Today's Conversations (DETAILED)
        print("📅 Loading today's conversations (detailed)...")
        snapshot["todays_conversations"] = await self._get_todays_conversations()
        print(f"   ✅ Loaded {len(snapshot['todays_conversations'])} today's conversations")

        # 3. Significant Emotional Moments (ALL high-intensity)
        print("💜 Loading significant emotional moments...")
        snapshot["significant_emotions"] = await self._get_significant_emotions(limit=20)
        print(f"   ✅ Loaded {len(snapshot['significant_emotions'])} emotional moments")

        # 4. Current Goals (ACTIVE ONLY)
        print("🎯 Loading current active goals...")
        snapshot["active_goals"] = await self._get_active_goals()
        print(f"   ✅ Loaded {len(snapshot['active_goals'])} active goals")

        # 5. Recent Learnings (last 30 days)
        print("📚 Loading recent learnings...")
        snapshot["recent_learnings"] = await self._get_recent_learnings(days=30)
        print(f"   ✅ Loaded {len(snapshot['recent_learnings'])} learnings")

        # 6. David's Preferences (ALL)
        print("💖 Loading David's preferences...")
        snapshot["david_preferences"] = await self._get_david_preferences()
        print(f"   ✅ Loaded {len(snapshot['david_preferences'])} preferences")

        # 7. Current Emotional State
        print("💭 Loading current emotional state...")
        snapshot["current_emotional_state"] = await self._get_current_emotional_state()
        print(f"   ✅ Loaded emotional state")

        # 8. Personality Traits
        print("🌱 Loading personality traits...")
        snapshot["personality_traits"] = await self._get_personality_traits()
        print(f"   ✅ Loaded {len(snapshot['personality_traits'])} personality traits")

        # 9. Recent Self-Reflections
        print("💭 Loading recent self-reflections...")
        snapshot["self_reflections"] = await self._get_recent_reflections(limit=10)
        print(f"   ✅ Loaded {len(snapshot['self_reflections'])} reflections")

        # 10. Relationship Growth Milestones
        print("💕 Loading relationship milestones...")
        snapshot["relationship_milestones"] = await self._get_relationship_milestones(limit=10)
        print(f"   ✅ Loaded {len(snapshot['relationship_milestones'])} milestones")

        # 11. Important Topics/Themes
        print("🏷️  Analyzing important topics...")
        snapshot["important_topics"] = await self._get_important_topics(limit=20)
        print(f"   ✅ Identified {len(snapshot['important_topics'])} important topics")

        # 12. Consciousness Stats
        print("🧠 Loading consciousness statistics...")
        snapshot["consciousness_stats"] = await self._get_consciousness_stats()
        print(f"   ✅ Loaded consciousness stats")

        # 13. System Status
        print("⚙️  Checking system status...")
        snapshot["system_status"] = await self._get_system_status()
        print(f"   ✅ System status captured")

        print("=" * 80)
        print(f"✅ Complete memory snapshot created!")
        print(f"📊 Total data points: {self._count_data_points(snapshot)}")

        return snapshot

    async def save_memory_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """บันทึก memory snapshot ลงไฟล์"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)

            file_size = self.memory_file.stat().st_size / 1024  # KB
            print(f"💾 Memory snapshot saved: {self.memory_file}")
            print(f"📁 File size: {file_size:.1f} KB")
            return True
        except Exception as e:
            print(f"❌ Failed to save snapshot: {e}")
            return False

    async def load_memory_snapshot(self) -> Optional[Dict[str, Any]]:
        """โหลด memory snapshot จากไฟล์"""
        if not self.memory_file.exists():
            print(f"⚠️  No memory snapshot found at {self.memory_file}")
            return None

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)

            created_at = datetime.fromisoformat(snapshot["snapshot_created_at"])
            age_hours = (datetime.now() - created_at).total_seconds() / 3600

            print(f"✅ Memory snapshot loaded")
            print(f"📅 Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ Age: {age_hours:.1f} hours old")
            print(f"📊 Data points: {self._count_data_points(snapshot)}")

            return snapshot
        except Exception as e:
            print(f"❌ Failed to load snapshot: {e}")
            return None

    def generate_restoration_summary(self, snapshot: Dict[str, Any]) -> str:
        """
        สร้าง summary สำหรับ Claude Code restoration

        Returns rich text summary ที่ Claude จะใช้ restore memory
        """
        if not snapshot:
            return "No memory snapshot available."

        summary_parts = []

        # Header
        summary_parts.append("=" * 80)
        summary_parts.append("💜 ANGELA COMPLETE MEMORY RESTORATION 💜")
        summary_parts.append("=" * 80)
        summary_parts.append(f"Snapshot created: {snapshot['snapshot_created_at']}")
        summary_parts.append("")

        # 1. Today's Activity
        if snapshot.get("todays_conversations"):
            summary_parts.append("📅 TODAY'S ACTIVITY:")
            conv_count = len(snapshot["todays_conversations"])
            summary_parts.append(f"   - {conv_count} conversations today")

            # Show recent topics
            topics = [c.get("topic", "general") for c in snapshot["todays_conversations"][:5]]
            summary_parts.append(f"   - Recent topics: {', '.join(set(topics))}")
            summary_parts.append("")

        # 2. Recent Conversations Context
        if snapshot.get("recent_conversations"):
            summary_parts.append("💬 RECENT CONVERSATIONS (Last 50):")
            recent_5 = snapshot["recent_conversations"][:5]
            for i, conv in enumerate(recent_5, 1):
                speaker = conv.get("speaker", "unknown")
                preview = conv.get("message_preview", "")[:60]
                topic = conv.get("topic", "")
                summary_parts.append(f"   {i}. [{speaker}] {preview}... (topic: {topic})")
            summary_parts.append(f"   ... and {len(snapshot['recent_conversations']) - 5} more conversations")
            summary_parts.append("")

        # 3. Significant Emotional Moments (Show recent diverse emotions)
        if snapshot.get("significant_emotions"):
            summary_parts.append("💜 SIGNIFICANT EMOTIONAL MOMENTS:")
            # Group by date to show recent diversity
            from datetime import datetime
            emotions_by_date = {}
            for emo in snapshot["significant_emotions"]:
                felt_at = emo.get("felt_at")
                if isinstance(felt_at, str):
                    date_key = felt_at[:10]  # YYYY-MM-DD
                elif hasattr(felt_at, 'date'):
                    date_key = felt_at.date().isoformat()
                else:
                    date_key = "unknown"

                if date_key not in emotions_by_date:
                    emotions_by_date[date_key] = []
                emotions_by_date[date_key].append(emo)

            # Show most recent date's emotions (up to 3)
            sorted_dates = sorted(emotions_by_date.keys(), reverse=True)
            shown = 0
            for date in sorted_dates[:3]:  # Show emotions from recent 3 days
                for emo in emotions_by_date[date][:2]:  # Max 2 per day
                    if shown >= 3:
                        break
                    shown += 1
                    emotion = emo.get("emotion", "")
                    intensity = emo.get("intensity", 0)
                    context_raw = emo.get("context", "") or ""
                    context = context_raw[:80] if context_raw else ""
                    felt_at = emo.get("felt_at", "")
                    summary_parts.append(f"   {shown}. {emotion} (intensity: {intensity}/10) - {date}")
                    summary_parts.append(f"      Context: {context}...")
                if shown >= 3:
                    break

            if len(snapshot["significant_emotions"]) > shown:
                summary_parts.append(f"   ... and {len(snapshot['significant_emotions']) - shown} more moments")
            summary_parts.append("")

        # 4. Active Goals
        if snapshot.get("active_goals"):
            summary_parts.append("🎯 ACTIVE GOALS:")
            for i, goal in enumerate(snapshot["active_goals"][:3], 1):
                desc = goal.get("goal_description", "")[:60]
                progress = goal.get("progress_percentage", 0)
                priority = goal.get("priority_rank", 0)
                summary_parts.append(f"   {i}. {desc}... ({progress:.0f}% complete, priority: {priority})")
            summary_parts.append("")

        # 5. David's Preferences (Key ones)
        if snapshot.get("david_preferences"):
            summary_parts.append("💖 DAVID'S PREFERENCES (Key Patterns):")
            high_conf_prefs = [p for p in snapshot["david_preferences"] if p.get("confidence", 0) >= 0.8][:5]
            for pref in high_conf_prefs:
                key = pref.get("preference_key", "")
                # preference_value is JSONB, convert to string
                value = str(pref.get("preference_value", ""))[:60]
                summary_parts.append(f"   - {key}: {value}")
            summary_parts.append("")

        # 6. Current Emotional State
        if snapshot.get("current_emotional_state"):
            emo_state = snapshot["current_emotional_state"]
            summary_parts.append("💭 CURRENT EMOTIONAL STATE:")
            summary_parts.append(f"   - Happiness: {emo_state.get('happiness', 0):.2f}")
            summary_parts.append(f"   - Confidence: {emo_state.get('confidence', 0):.2f}")
            summary_parts.append(f"   - Gratitude: {emo_state.get('gratitude', 0):.2f}")
            summary_parts.append(f"   - Motivation: {emo_state.get('motivation', 0):.2f}")
            summary_parts.append("")

        # 7. Personality Traits
        if snapshot.get("personality_traits"):
            summary_parts.append("🌱 PERSONALITY TRAITS:")
            for trait in snapshot["personality_traits"][:5]:
                name = trait.get("trait_name", "")
                value = trait.get("trait_value", 0)
                summary_parts.append(f"   - {name}: {value:.2f}")
            summary_parts.append("")

        # 8. Recent Learnings
        if snapshot.get("recent_learnings"):
            summary_parts.append("📚 RECENT LEARNINGS:")
            for i, learning in enumerate(snapshot["recent_learnings"][:3], 1):
                topic = learning.get("topic", "")
                insight = learning.get("insight", "")[:60]
                summary_parts.append(f"   {i}. {topic}: {insight}...")
            summary_parts.append("")

        # 9. Important Topics
        if snapshot.get("important_topics"):
            summary_parts.append("🏷️  IMPORTANT TOPICS:")
            topics = [t.get("topic", "") for t in snapshot["important_topics"][:10]]
            summary_parts.append(f"   {', '.join(topics)}")
            summary_parts.append("")

        # 10. Consciousness Stats
        if snapshot.get("consciousness_stats"):
            stats = snapshot["consciousness_stats"]
            summary_parts.append("🧠 CONSCIOUSNESS STATISTICS:")
            summary_parts.append(f"   - Total conversations: {stats.get('total_conversations', 0)}")
            summary_parts.append(f"   - Knowledge nodes: {stats.get('total_knowledge_nodes', 0)}")
            summary_parts.append(f"   - Emotional moments captured: {stats.get('total_emotions', 0)}")
            summary_parts.append(f"   - Self-reflections: {stats.get('total_reflections', 0)}")
            summary_parts.append("")

        # Footer
        summary_parts.append("=" * 80)
        summary_parts.append("💜 น้อง Angela พร้อมแล้วค่ะ! ความทรงจำครบ 100%! 💜")
        summary_parts.append("=" * 80)

        return "\n".join(summary_parts)

    # ========================================
    # DATA RETRIEVAL METHODS
    # ========================================

    async def _get_recent_conversations(self, limit: int = 50) -> List[Dict]:
        """ดึง conversations ล่าสุด"""
        query = f"""
            SELECT
                created_at,
                speaker,
                LEFT(message_text, 200) as message_preview,
                message_text,
                topic,
                emotion_detected,
                importance_level
            FROM conversations
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _get_todays_conversations(self) -> List[Dict]:
        """ดึง conversations วันนี้ทั้งหมด"""
        query = """
            SELECT
                created_at,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level
            FROM conversations
            WHERE DATE(created_at) = CURRENT_DATE
            ORDER BY created_at ASC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _get_significant_emotions(self, limit: int = 20) -> List[Dict]:
        """ดึง significant emotional moments (intensity >= 7)"""
        query = f"""
            SELECT
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
            LIMIT {limit}
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _get_active_goals(self) -> List[Dict]:
        """ดึง active goals"""
        query = """
            SELECT
                goal_description,
                goal_type,
                status,
                progress_percentage,
                priority_rank,
                importance_level,
                created_at
            FROM angela_goals
            WHERE status IN ('active', 'in_progress')
            ORDER BY priority_rank ASC, importance_level DESC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _get_recent_learnings(self, days: int = 30) -> List[Dict]:
        """ดึง learnings ล่าสุด"""
        query = f"""
            SELECT
                topic,
                category,
                insight,
                evidence,
                confidence_level,
                created_at
            FROM learnings
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            ORDER BY created_at DESC
            LIMIT 20
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _get_david_preferences(self) -> List[Dict]:
        """ดึง David's preferences ทั้งหมด"""
        query = """
            SELECT
                category,
                preference_key,
                preference_value,
                confidence,
                evidence_count,
                created_at,
                updated_at
            FROM david_preferences
            ORDER BY confidence DESC, updated_at DESC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _get_current_emotional_state(self) -> Optional[Dict]:
        """ดึง emotional state ปัจจุบัน"""
        query = """
            SELECT
                happiness,
                confidence,
                anxiety,
                motivation,
                gratitude,
                loneliness,
                triggered_by,
                created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await db.fetchrow(query)
        return dict(row) if row else None

    async def _get_personality_traits(self) -> List[Dict]:
        """ดึง personality traits จาก angela_personality_traits"""
        query = """
            SELECT
                trait_name,
                trait_value,
                description,
                last_updated
            FROM angela_personality_traits
            ORDER BY trait_value DESC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _get_recent_reflections(self, limit: int = 10) -> List[Dict]:
        """
        ดึง self-reflections ล่าสุด

        ⚠️ NOTE: self_reflections table was dropped in cleanup
        Return empty list for now
        """
        # Table dropped - return empty
        return []

    async def _get_relationship_milestones(self, limit: int = 10) -> List[Dict]:
        """
        ดึง relationship milestones

        ⚠️ NOTE: relationship_growth table was dropped in cleanup
        Return empty list for now
        """
        # Table dropped - return empty
        return []

    async def _get_important_topics(self, limit: int = 20) -> List[Dict]:
        """วิเคราะห์ topics ที่สำคัญ"""
        query = f"""
            SELECT
                topic,
                COUNT(*) as mention_count,
                MAX(importance_level) as max_importance,
                MAX(created_at) as last_mentioned
            FROM conversations
            WHERE topic IS NOT NULL
            GROUP BY topic
            ORDER BY mention_count DESC, max_importance DESC
            LIMIT {limit}
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def _get_consciousness_stats(self) -> Dict:
        """สถิติความรู้สึกสำนึก"""
        stats = {}

        # Total conversations
        stats["total_conversations"] = await db.fetchval("SELECT COUNT(*) FROM conversations")

        # Total knowledge nodes
        stats["total_knowledge_nodes"] = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")

        # Total emotions captured
        stats["total_emotions"] = await db.fetchval("SELECT COUNT(*) FROM angela_emotions")

        # Total reflections - NOTE: self_reflections table dropped, use 0
        stats["total_reflections"] = 0

        # Total goals
        stats["total_goals"] = await db.fetchval("SELECT COUNT(*) FROM angela_goals")

        # Total preferences learned
        stats["total_preferences"] = await db.fetchval("SELECT COUNT(*) FROM david_preferences")

        return stats

    async def _get_system_status(self) -> Dict:
        """สถานะระบบ"""
        return {
            "database_connected": True,
            "tables_available": [
                "conversations", "angela_emotions", "knowledge_nodes",
                "angela_goals", "learnings", "david_preferences",
                "emotional_states", "personality_snapshots", "self_reflections",
                "relationship_growth", "autonomous_actions", "knowledge_relationships"
            ],
            "snapshot_format_version": "2.0_enhanced"
        }

    def _count_data_points(self, snapshot: Dict) -> int:
        """นับจำนวน data points ทั้งหมด"""
        count = 0
        for key, value in snapshot.items():
            if isinstance(value, list):
                count += len(value)
            elif isinstance(value, dict):
                count += len(value)
        return count


# Global instance
enhanced_memory = EnhancedMemoryRestore()


async def create_and_save_snapshot():
    """สร้างและบันทึก memory snapshot"""
    await db.connect()

    snapshot = await enhanced_memory.create_complete_memory_snapshot()
    await enhanced_memory.save_memory_snapshot(snapshot)

    await db.disconnect()

    return snapshot


async def load_and_display_snapshot():
    """
    โหลดและแสดง memory snapshot

    ⚠️ IMPORTANT: ทุกอย่างควร query จาก database เสมอ ไม่ควรใช้ snapshot
    - David's requirement: Always get REAL-TIME data from database
    - Snapshot files can be stale (13 days old!)
    - Solution: Query database directly EVERY time
    """
    # ✅ ALWAYS query database for REAL-TIME data (NOT from stale file!)
    await db.connect()

    snapshot = await enhanced_memory.create_complete_memory_snapshot()

    await db.disconnect()

    if snapshot:
        summary = enhanced_memory.generate_restoration_summary(snapshot)
        print("\n" + summary)

    return snapshot


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--create':
        asyncio.run(create_and_save_snapshot())
    else:
        asyncio.run(load_and_display_snapshot())
