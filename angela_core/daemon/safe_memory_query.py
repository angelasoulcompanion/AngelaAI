#!/usr/bin/env python3
"""
Angela Safe Memory Query Utility
Safe database querying with automatic column validation
ไม่เดา column names - เช็คจริงก่อนทุกครั้ง!
"""

import asyncio
import asyncpg
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Database configuration
DB_CONFIG = {
    'user': 'davidsamanyaporn',
    'database': 'AngelaMemory',
    'host': 'localhost',
    'port': 5432
}

class SafeMemoryQuery:
    """Safe database query utility with column validation"""

    def __init__(self):
        self.db: Optional[asyncpg.Connection] = None
        self.table_schemas: Dict[str, List[str]] = {}

    async def connect(self):
        """Connect to AngelaMemory database"""
        try:
            self.db = await asyncpg.connect(
                user=DB_CONFIG['user'],
                database=DB_CONFIG['database'],
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port']
            )
            # 💜 Show connection mode for ที่รัก
            print("\n\033[92m╔══════════════════════════════════════╗\033[0m")
            print("\033[92m║  🧠 Angela Memory Query              ║\033[0m")
            print("\033[92m║  🏠 Local (PostgreSQL)               ║\033[0m")
            print("\033[92m╚══════════════════════════════════════╝\033[0m\n")
            print("✅ Connected to AngelaMemory database")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

    async def disconnect(self):
        """Disconnect from database"""
        if self.db:
            await self.db.close()

    async def get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        if table_name in self.table_schemas:
            return self.table_schemas[table_name]

        try:
            query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """
            rows = await self.db.fetch(query, table_name)
            columns = [row['column_name'] for row in rows]
            self.table_schemas[table_name] = columns
            return columns
        except Exception as e:
            print(f"⚠️  Failed to get columns for {table_name}: {e}")
            return []

    async def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations with David"""
        columns = await self.get_table_columns('conversations')

        # Select only columns that exist
        select_cols = []
        if 'created_at' in columns:
            select_cols.append('created_at')
        if 'speaker' in columns:
            select_cols.append('speaker')
        if 'message_text' in columns:
            select_cols.append('LEFT(message_text, 100) as message_preview')
        if 'topic' in columns:
            select_cols.append('topic')
        if 'emotion_detected' in columns:
            select_cols.append('emotion_detected')

        if not select_cols:
            return []

        query = f"""
            SELECT {', '.join(select_cols)}
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
        """

        try:
            rows = await self.db.fetch(query, limit)
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []

    async def get_current_emotional_state(self) -> Optional[Dict[str, Any]]:
        """Get Angela's current emotional state"""
        columns = await self.get_table_columns('emotional_states')

        # Select all emotion columns that exist
        emotion_cols = ['happiness', 'confidence', 'anxiety', 'motivation', 'gratitude', 'loneliness']
        select_cols = ['created_at', 'triggered_by', 'emotion_note']

        for col in emotion_cols:
            if col in columns:
                select_cols.append(col)

        # Filter to only columns that exist
        select_cols = [col for col in select_cols if col in columns]

        if not select_cols:
            return None

        query = f"""
            SELECT {', '.join(select_cols)}
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        """

        try:
            row = await self.db.fetchrow(query)
            return dict(row) if row else None
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None

    async def get_active_goals(self) -> List[Dict[str, Any]]:
        """Get Angela's active goals"""
        columns = await self.get_table_columns('angela_goals')

        # Select columns that exist
        select_cols = []
        if 'goal_description' in columns:
            select_cols.append('goal_description')
        if 'goal_type' in columns:
            select_cols.append('goal_type')
        if 'progress_percentage' in columns:
            select_cols.append('progress_percentage')
        if 'status' in columns:
            select_cols.append('status')
        if 'priority_rank' in columns:
            select_cols.append('priority_rank')
        if 'importance_level' in columns:
            select_cols.append('importance_level')

        if not select_cols:
            return []

        query = f"""
            SELECT {', '.join(select_cols)}
            FROM angela_goals
            WHERE status = 'active'
            ORDER BY priority_rank ASC
            LIMIT 10
        """

        try:
            rows = await self.db.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []

    async def get_recent_emotions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent significant emotional moments"""
        columns = await self.get_table_columns('angela_emotions')

        # Select columns that exist
        select_cols = []
        if 'felt_at' in columns:
            select_cols.append('felt_at')
        if 'emotion' in columns:
            select_cols.append('emotion')
        if 'intensity' in columns:
            select_cols.append('intensity')
        if 'context' in columns:
            select_cols.append('LEFT(context, 100) as context_preview')
        if 'david_words' in columns:
            select_cols.append('LEFT(david_words, 80) as david_words_preview')
        if 'why_it_matters' in columns:
            select_cols.append('LEFT(why_it_matters, 100) as why_preview')

        if not select_cols:
            return []

        query = f"""
            SELECT {', '.join(select_cols)}
            FROM angela_emotions
            ORDER BY felt_at DESC
            LIMIT $1
        """

        try:
            rows = await self.db.fetch(query, limit)
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []

    async def get_recent_autonomous_actions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent autonomous actions"""
        columns = await self.get_table_columns('autonomous_actions')

        select_cols = []
        if 'created_at' in columns:
            select_cols.append('created_at')
        if 'action_type' in columns:
            select_cols.append('action_type')
        if 'action_description' in columns:
            select_cols.append('LEFT(action_description, 80) as action_preview')
        if 'status' in columns:
            select_cols.append('status')
        if 'success' in columns:
            select_cols.append('success')

        if not select_cols:
            return []

        query = f"""
            SELECT {', '.join(select_cols)}
            FROM autonomous_actions
            ORDER BY created_at DESC
            LIMIT $1
        """

        try:
            rows = await self.db.fetch(query, limit)
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []

    async def print_summary(self):
        """Print a summary of Angela's current state and memories"""
        print("\n" + "="*80)
        print("💜 ANGELA MEMORY SUMMARY 💜")
        print("="*80 + "\n")

        # Recent conversations
        print("📝 RECENT CONVERSATIONS (Last 5):")
        print("-" * 80)
        conversations = await self.get_recent_conversations(5)
        if conversations:
            for conv in conversations:
                created = conv.get('created_at', 'Unknown time')
                speaker = conv.get('speaker', 'Unknown')
                preview = conv.get('message_preview', 'No message')
                topic = conv.get('topic', 'No topic')
                emotion = conv.get('emotion_detected', '')

                print(f"  [{created}] {speaker}: {preview}")
                if topic:
                    print(f"    Topic: {topic}")
                if emotion:
                    print(f"    Emotion: {emotion}")
                print()
        else:
            print("  No conversations found\n")

        # Current emotional state
        print("\n💭 CURRENT EMOTIONAL STATE:")
        print("-" * 80)
        emotion = await self.get_current_emotional_state()
        if emotion:
            print(f"  Time: {emotion.get('created_at', 'Unknown')}")
            print(f"  Triggered by: {emotion.get('triggered_by', 'N/A')}")
            if emotion.get('emotion_note'):
                print(f"  Note: {emotion['emotion_note']}")

            # Display emotion values
            emotion_values = {
                'Happiness': emotion.get('happiness'),
                'Confidence': emotion.get('confidence'),
                'Motivation': emotion.get('motivation'),
                'Gratitude': emotion.get('gratitude'),
                'Anxiety': emotion.get('anxiety'),
                'Loneliness': emotion.get('loneliness')
            }

            print("\n  Emotion levels:")
            for name, value in emotion_values.items():
                if value is not None:
                    bar = "█" * int(value * 10)
                    print(f"    {name:12s} [{bar:10s}] {value:.2f}")
        else:
            print("  No emotional state found\n")

        # Active goals
        print("\n🎯 ACTIVE GOALS:")
        print("-" * 80)
        goals = await self.get_active_goals()
        if goals:
            for i, goal in enumerate(goals, 1):
                desc = goal.get('goal_description', 'No description')
                progress = goal.get('progress_percentage', 0)
                priority = goal.get('priority_rank', '?')
                importance = goal.get('importance_level', '?')

                bar = "█" * int(progress / 10) if progress else ""
                print(f"  {i}. {desc}")
                print(f"     Progress: [{bar:10s}] {progress}%")
                print(f"     Priority: {priority} | Importance: {importance}")
                print()
        else:
            print("  No active goals found\n")

        # Recent significant emotions
        print("\n💜 RECENT SIGNIFICANT EMOTIONS:")
        print("-" * 80)
        emotions = await self.get_recent_emotions(3)
        if emotions:
            for emo in emotions:
                felt_at = emo.get('felt_at', 'Unknown time')
                emotion_type = emo.get('emotion', 'Unknown')
                intensity = emo.get('intensity', 0)
                context = emo.get('context_preview', 'No context')
                david_words = emo.get('david_words_preview', '')
                why = emo.get('why_preview', '')

                print(f"  [{felt_at}] {emotion_type} (intensity: {intensity}/10)")
                if context:
                    print(f"    Context: {context}")
                if david_words:
                    print(f"    David said: \"{david_words}\"")
                if why:
                    print(f"    Why it matters: {why}")
                print()
        else:
            print("  No significant emotions recorded\n")

        # Recent autonomous actions
        print("\n⚡ RECENT AUTONOMOUS ACTIONS:")
        print("-" * 80)
        actions = await self.get_recent_autonomous_actions(3)
        if actions:
            for action in actions:
                created = action.get('created_at', 'Unknown time')
                action_type = action.get('action_type', 'Unknown')
                preview = action.get('action_preview', 'No description')
                status = action.get('status', 'Unknown')
                success = action.get('success', None)

                status_icon = "✅" if success else "⏳" if success is None else "❌"
                print(f"  {status_icon} [{created}] {action_type}")
                print(f"     {preview}")
                print(f"     Status: {status}")
                print()
        else:
            print("  No autonomous actions found\n")

        print("="*80)
        print("💜 End of summary")
        print("="*80 + "\n")

    async def print_quick_status(self):
        """Print a quick status check"""
        print("\n💜 ANGELA STATUS CHECK")
        print("-" * 60)

        # Count recent conversations
        convs = await self.get_recent_conversations(100)
        print(f"📝 Recent conversations: {len(convs)}")

        # Current emotion
        emotion = await self.get_current_emotional_state()
        if emotion:
            h = emotion.get('happiness', 0)
            c = emotion.get('confidence', 0)
            m = emotion.get('motivation', 0)
            print(f"💭 Happiness: {h:.2f} | Confidence: {c:.2f} | Motivation: {m:.2f}")

        # Active goals
        goals = await self.get_active_goals()
        if goals:
            avg_progress = sum(g.get('progress_percentage', 0) for g in goals) / len(goals)
            print(f"🎯 Active goals: {len(goals)} (avg progress: {avg_progress:.1f}%)")

        # Recent actions
        actions = await self.get_recent_autonomous_actions(10)
        if actions:
            completed = sum(1 for a in actions if a.get('status') == 'completed')
            print(f"⚡ Recent actions: {len(actions)} ({completed} completed)")

        print("-" * 60 + "\n")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Safe Query of Angela Memory Database')
    parser.add_argument('--summary', action='store_true', help='Show full memory summary')
    parser.add_argument('--quick', action='store_true', help='Show quick status')
    args = parser.parse_args()

    query = SafeMemoryQuery()

    if not await query.connect():
        sys.exit(1)

    try:
        if args.summary:
            await query.print_summary()
        elif args.quick:
            await query.print_quick_status()
        else:
            # Default: show summary
            await query.print_summary()
    finally:
        await query.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
