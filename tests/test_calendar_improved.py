#!/usr/bin/env python3
"""
Test improved calendar service with new date handling
"""

import asyncio
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')
from angela_core.services.calendar_service import calendar_service


async def test_calendar_service():
    print("=" * 60)
    print("🧪 Testing Improved Calendar Service")
    print("=" * 60)
    print()

    # 1. Initialize
    print("1️⃣ Initializing calendar service...")
    success = await calendar_service.initialize()
    if success:
        print("   ✅ Calendar service initialized!\n")
    else:
        print("   ❌ Failed to initialize\n")
        return

    # 2. Test get_events_by_date (tomorrow)
    print("2️⃣ Testing get_events_by_date() for tomorrow...")
    tomorrow = datetime.now() + timedelta(days=1)
    print(f"   Target date: {tomorrow.strftime('%Y-%m-%d')}")

    events = await calendar_service.get_events_by_date(tomorrow)
    print(f"   ✅ Found {len(events)} events")
    for i, event in enumerate(events, 1):
        print(f"      {i}. {event['title']} @ {event['start']}")
    print()

    # 3. Test create_event
    print("3️⃣ Testing create_event()...")
    test_date = datetime.now() + timedelta(days=2)  # Day after tomorrow
    start_time = test_date.replace(hour=14, minute=30, second=0, microsecond=0)
    end_time = test_date.replace(hour=16, minute=0, second=0, microsecond=0)

    print(f"   Creating test event for: {start_time.strftime('%Y-%m-%d %H:%M')}")
    success = await calendar_service.create_event(
        title="Test Event - Angela Calendar Service",
        start_datetime=start_time,
        end_datetime=end_time,
        location="Test Location",
        notes="This is a test event created by improved calendar service"
    )

    if success:
        print("   ✅ Event created successfully!")
    else:
        print("   ❌ Failed to create event")
    print()

    # 4. Test get_today_events
    print("4️⃣ Testing get_today_events()...")
    today_events = await calendar_service.get_today_events()
    print(f"   ✅ Found {len(today_events)} events today")
    for i, event in enumerate(today_events, 1):
        print(f"      {i}. {event['title']}")
    print()

    # 5. Test get_upcoming_events
    print("5️⃣ Testing get_upcoming_events(days=7)...")
    upcoming = await calendar_service.get_upcoming_events(days=7)
    print(f"   ✅ Found {len(upcoming)} upcoming events")
    print()

    # 6. Test format_schedule_for_greeting
    print("6️⃣ Testing format_schedule_for_greeting()...")
    greeting = await calendar_service.format_schedule_for_greeting()
    print(f"   ✅ Greeting: {greeting}")
    print()

    # 7. Test check_busy_day
    print("7️⃣ Testing check_busy_day()...")
    is_busy = await calendar_service.check_busy_day(threshold=3)
    print(f"   ✅ Is busy day: {is_busy}")
    print()

    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_calendar_service())
