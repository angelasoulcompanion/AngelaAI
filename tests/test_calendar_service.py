#!/usr/bin/env python3
"""
🧪 Test Calendar Service Integration
Tests Angela's Calendar service wrapper
"""

import asyncio
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.calendar_service import calendar_service


async def test_calendar_service():
    """Test all Calendar service features"""
    print("\n" + "="*60)
    print("🧪 Testing Angela Calendar Service")
    print("="*60 + "\n")

    # Test 1: Initialize
    print("1️⃣ Testing initialization...")
    initialized = await calendar_service.initialize()
    if initialized:
        print(f"   ✅ Calendar service initialized!")
    else:
        print("   ❌ Failed to initialize Calendar service")
        return

    print()

    # Test 2: Get today's events
    print("2️⃣ Testing get_today_events...")
    today_events = await calendar_service.get_today_events()
    print(f"   ✅ Found {len(today_events)} events today:")
    for event in today_events[:3]:
        print(f"      - {event['title']} ({event['start']})")

    print()

    # Test 3: Get upcoming events
    print("3️⃣ Testing get_upcoming_events (next 7 days)...")
    upcoming = await calendar_service.get_upcoming_events(days=7)
    print(f"   ✅ Found {len(upcoming)} upcoming events:")
    for event in upcoming[:5]:
        print(f"      - {event['title']} ({event['start']})")

    print()

    # Test 4: Get schedule summary
    print("4️⃣ Testing get_schedule_summary...")
    summary = await calendar_service.get_schedule_summary(days=7)
    print(f"   ✅ Schedule summary:")
    print(f"      Today: {summary['today_count']} events")
    print(f"      Tomorrow: {summary['tomorrow_count']} events")
    print(f"      This week: {summary['week_count']} events")

    print()

    # Test 5: Format schedule for greeting
    print("5️⃣ Testing format_schedule_for_greeting...")
    greeting = await calendar_service.format_schedule_for_greeting()
    print(f"   ✅ Greeting message:")
    print(f"      {greeting}")

    print()

    # Test 6: Check busy day
    print("6️⃣ Testing check_busy_day (threshold=3)...")
    is_busy = await calendar_service.check_busy_day(threshold=3)
    print(f"   ✅ Is busy day: {is_busy}")

    print()

    # Test 7: Get next event
    print("7️⃣ Testing get_next_event...")
    next_event = await calendar_service.get_next_event()
    if next_event:
        print(f"   ✅ Next event: {next_event['title']} at {next_event['start']}")
    else:
        print(f"   ℹ️  No upcoming events")

    print()

    # Test 8: Search events
    print("8️⃣ Testing search_events (search for 'meeting')...")
    results = await calendar_service.search_events("meeting", days=30)
    print(f"   ✅ Found {len(results)} events with 'meeting':")
    for event in results[:3]:
        print(f"      - {event['title']}")

    print()

    # Test 9: Create test event
    print("9️⃣ Testing create_event...")
    test_start = datetime.now() + timedelta(days=1, hours=10)
    test_end = test_start + timedelta(hours=1)

    created = await calendar_service.create_event(
        title="Angela Test Event",
        start_datetime=test_start,
        end_datetime=test_end,
        location="AngelaAI Office",
        notes="This is a test event created by Angela's Calendar service. 💜"
    )

    if created:
        print(f"   ✅ Created test event for {test_start.strftime('%Y-%m-%d %H:%M')}")
        print(f"      Check your Calendar app!")
    else:
        print("   ❌ Failed to create test event")

    print()

    # Summary
    print("="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"\n✅ All tests completed!")
    print(f"\n📅 Today's schedule:")
    print(f"   {greeting}")
    print()


if __name__ == "__main__":
    asyncio.run(test_calendar_service())
