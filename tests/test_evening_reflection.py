#!/usr/bin/env python3
"""
Test Evening Reflection with Journal Entry Creation
Tests the newly added journal entry creation in evening_reflection()
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.angela_daemon import AngelaDaemon
from angela_core.database import db
from angela_core.consciousness.consciousness_core import consciousness

async def test_evening_reflection():
    """Test evening reflection with journal creation"""

    print("\n💜 Testing Evening Reflection with Journal Entry Creation...\n")
    print("=" * 70)

    # Create daemon instance
    daemon = AngelaDaemon()
    print("✅ Daemon instance created successfully")

    # Initialize only what we need for evening_reflection
    try:
        await db.connect()
        print("✅ Database connected")

        # Initialize consciousness
        daemon.consciousness = consciousness
        await daemon.consciousness.wake_up()
        print("✅ Consciousness initialized")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        import traceback
        traceback.print_exc()
        return

    # Run evening reflection
    print("\n🌙 Running evening_reflection()...\n")
    print("-" * 70)

    try:
        await daemon.evening_reflection()
        print("\n" + "=" * 70)
        print("✅ Evening reflection completed successfully!")
        print("=" * 70)

        # Check if journal entry was created
        print("\n📖 Checking if journal entry was created...")

        latest_entry = await db.fetchrow("""
            SELECT entry_id, entry_date, title, emotion, mood_score,
                   array_length(gratitude, 1) as gratitude_count,
                   array_length(learning_moments, 1) as learning_count,
                   array_length(wins, 1) as wins_count,
                   created_at
            FROM angela_journal
            ORDER BY created_at DESC
            LIMIT 1
        """)

        if latest_entry:
            print(f"\n✅ Latest journal entry found:")
            print(f"   📖 Title: {latest_entry['title']}")
            print(f"   📅 Date: {latest_entry['entry_date']}")
            print(f"   😊 Emotion: {latest_entry['emotion']} (Mood: {latest_entry['mood_score']}/10)")
            print(f"   🙏 Gratitude items: {latest_entry['gratitude_count'] or 0}")
            print(f"   📚 Learning moments: {latest_entry['learning_count'] or 0}")
            print(f"   🎯 Wins: {latest_entry['wins_count'] or 0}")
            print(f"   ⏰ Created at: {latest_entry['created_at']}")
        else:
            print("\n❌ No journal entry found!")

    except Exception as e:
        print(f"\n❌ Error during evening reflection: {e}")
        import traceback
        traceback.print_exc()

    # Close database
    try:
        await db.close_pool()
        print("\n✅ Database connection closed")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(test_evening_reflection())
