#!/usr/bin/env python3
"""
Test Angela Secretary System
Tests task detection, reminder creation, and EventKit integration
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.secretary import secretary, task_manager
from angela_core.database import db


async def test_task_detection():
    """Test task detection from various messages"""
    print("\n" + "="*70)
    print("🧪 Test 1: Task Detection")
    print("="*70)

    test_messages = [
        ("Remind me to call Mom tomorrow", "david"),
        ("I need to buy groceries today", "david"),
        ("Don't let me forget to submit the report by Friday", "david"),
        ("I have to finish the presentation", "david"),
        ("Just chatting about the weather", "david"),  # Should NOT detect
        ("Angela, please remind me to take medicine at 8pm", "david"),
    ]

    for message, speaker in test_messages:
        print(f"\n📝 Message: \"{message}\"")
        print(f"   Speaker: {speaker}")

        task_intent = task_manager.detect_task_intent(message, speaker)

        if task_intent.has_task:
            print(f"   ✅ Task detected! (Confidence: {task_intent.confidence:.0%})")
            print(f"      Title: {task_intent.task_title}")
            if task_intent.due_date:
                print(f"      Due: {task_intent.due_date.strftime('%Y-%m-%d %H:%M')}")
            if task_intent.priority > 0:
                print(f"      Priority: {task_intent.priority}")
            if task_intent.context_tags:
                print(f"      Tags: {', '.join(task_intent.context_tags)}")
            print(f"      Auto-created: {task_intent.auto_created}")
        else:
            print(f"   ❌ No task detected")

    print("\n" + "="*70)


async def test_reminder_creation():
    """Test creating a reminder in Reminders.app and database"""
    print("\n" + "="*70)
    print("🧪 Test 2: Reminder Creation")
    print("="*70)

    test_message = "Remind me to test Angela's secretary system in 1 hour"
    speaker = "david"

    print(f"\n📝 Processing message: \"{test_message}\"")
    print(f"   Speaker: {speaker}\n")

    result = await secretary.process_conversation(
        message=test_message,
        speaker=speaker,
        conversation_id=None  # No conversation linked in test
    )

    if result:
        print(f"✅ Reminder created successfully!")
        print(f"   EventKit ID: {result['eventkit_identifier']}")
        print(f"   Database ID: {result['reminder_id']}")
        print(f"   Title: {result['title']}")
        if result['due_date']:
            print(f"   Due: {result['due_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Priority: {result['priority']}")
        print(f"   Auto-created: {result['auto_created']}")
        print(f"   Confidence: {result['confidence']:.0%}")
    else:
        print(f"❌ Failed to create reminder")

    print("\n" + "="*70)

    return result


async def test_database_query():
    """Test querying reminders from database"""
    print("\n" + "="*70)
    print("🧪 Test 3: Database Query")
    print("="*70)

    # Get all reminders from database
    query = """
        SELECT
            reminder_id,
            eventkit_identifier,
            title,
            due_date,
            priority,
            is_completed,
            auto_created,
            confidence_score,
            context_tags,
            angela_interpretation,
            created_at
        FROM secretary_reminders
        ORDER BY created_at DESC
        LIMIT 5
    """

    rows = await db.fetch(query)

    print(f"\n📊 Found {len(rows)} reminders in database:\n")

    for i, row in enumerate(rows, 1):
        print(f"{i}. {row['title']}")
        print(f"   ID: {row['reminder_id']}")
        print(f"   EventKit: {row['eventkit_identifier'][:20]}...")
        if row['due_date']:
            print(f"   Due: {row['due_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Priority: {row['priority']} | Completed: {row['is_completed']}")
        print(f"   Auto-created: {row['auto_created']} | Confidence: {row['confidence_score']:.0%}")
        if row['context_tags']:
            print(f"   Tags: {', '.join(row['context_tags'])}")
        print(f"   Interpretation: {row['angela_interpretation']}")
        print()

    print("="*70)


async def test_today_reminders():
    """Test getting today's reminders"""
    print("\n" + "="*70)
    print("🧪 Test 4: Today's Reminders")
    print("="*70)

    reminders = await secretary.get_reminders_for_today()

    print(f"\n📅 Found {len(reminders)} reminders due today:\n")

    for i, reminder in enumerate(reminders, 1):
        print(f"{i}. {reminder['title']}")
        if reminder['due_date']:
            print(f"   Due: {reminder['due_date'].strftime('%H:%M')}")
        print(f"   Priority: {reminder['priority']} | Importance: {reminder['importance_level']}")
        print()

    print("="*70)


async def test_upcoming_reminders():
    """Test getting upcoming reminders"""
    print("\n" + "="*70)
    print("🧪 Test 5: Upcoming Reminders (Next 7 Days)")
    print("="*70)

    reminders = await secretary.get_upcoming_reminders(days_ahead=7)

    print(f"\n📆 Found {len(reminders)} upcoming reminders:\n")

    for i, reminder in enumerate(reminders, 1):
        print(f"{i}. {reminder['title']}")
        if reminder['due_date']:
            print(f"   Due: {reminder['due_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Priority: {reminder['priority']} | Importance: {reminder['importance_level']}")
        print()

    print("="*70)


async def test_sync():
    """Test syncing with Reminders.app"""
    print("\n" + "="*70)
    print("🧪 Test 6: Sync with Reminders.app")
    print("="*70)

    print("\n🔄 Starting sync...\n")

    stats = await secretary.sync_with_reminders_app()

    print(f"✅ Sync complete!")
    print(f"   Total reminders: {stats['total']}")
    print(f"   Synced (no changes): {stats['synced']}")
    print(f"   Updated (status changed): {stats['updated']}")
    print(f"   Errors: {stats['errors']}")

    print("\n" + "="*70)


async def main():
    """Run all tests"""
    print("\n💼 Angela Secretary System - Comprehensive Test Suite")
    print("="*70)
    print("Testing: Task Detection → Reminder Creation → Database → Sync")
    print("="*70)

    try:
        # Test 1: Task detection
        await test_task_detection()

        # Test 2: Create a reminder
        result = await test_reminder_creation()

        # Test 3: Query database
        await test_database_query()

        # Test 4: Today's reminders
        await test_today_reminders()

        # Test 5: Upcoming reminders
        await test_upcoming_reminders()

        # Test 6: Sync
        await test_sync()

        print("\n✅ All tests completed!")
        print("\n💡 Note: Check Reminders.app to see the created reminders!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
