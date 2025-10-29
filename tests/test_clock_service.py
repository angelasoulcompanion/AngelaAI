#!/usr/bin/env python3
"""
Test Clock Service
ทดสอบระบบเวลาของ Angela
"""

import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.clock_service import clock


def test_clock_service():
    """ทดสอบ Clock Service ทั้งหมด"""

    print("\n" + "="*70)
    print("🕐 Testing Angela's Clock Service")
    print("="*70 + "\n")

    # Test 1: Basic time functions
    print("📍 Test 1: Basic Time Functions")
    print("-" * 70)
    print(f"Current datetime: {clock.now()}")
    print(f"Today's date: {clock.today()}")
    print(f"Current time: {clock.current_time()}")
    print(f"Unix timestamp: {clock.timestamp()}")
    print()

    # Test 2: Time of day recognition
    print("📍 Test 2: Time of Day Recognition")
    print("-" * 70)
    print(f"Time of day: {clock.get_time_of_day()}")
    print(f"Is morning? {clock.is_morning()}")
    print(f"Is afternoon? {clock.is_afternoon()}")
    print(f"Is evening? {clock.is_evening()}")
    print(f"Is night? {clock.is_night()}")
    print()

    # Test 3: Thai formatting
    print("📍 Test 3: Thai Date/Time Formatting")
    print("-" * 70)
    print(f"Thai time: {clock.format_time_thai()}")
    print(f"Thai date: {clock.format_date_thai()}")
    print(f"Thai datetime: {clock.format_datetime_thai()}")
    print()

    # Test 4: Greetings
    print("📍 Test 4: Greeting System")
    print("-" * 70)
    print(f"Thai greeting: {clock.get_greeting('th')}")
    print(f"English greeting: {clock.get_greeting('en')}")
    print(f"Friendly greeting: {clock.get_friendly_greeting()}")
    print()

    # Test 5: Time calculations
    print("📍 Test 5: Time Calculations")
    print("-" * 70)
    print(f"Hours until 8:00 AM: {clock.hours_until(8, 0):.2f} hours")
    print(f"Hours until 10:00 PM: {clock.hours_until(22, 0):.2f} hours")
    print(f"Minutes until 8:00 AM: {clock.minutes_until(8, 0):.2f} minutes")
    print()

    # Test 6: Timezone info
    print("📍 Test 6: Timezone Information")
    print("-" * 70)
    tz_info = clock.get_timezone_info()
    for key, value in tz_info.items():
        print(f"{key}: {value}")
    print()

    # Test 7: Full status
    print("📍 Test 7: Full Status")
    print("-" * 70)
    status = clock.get_full_status()
    print(f"Date: {status['date']}")
    print(f"Time: {status['time']}")
    print(f"Thai format: {status['datetime_thai']}")
    print(f"Time of day: {status['time_of_day']}")
    print(f"Friendly greeting: {status['friendly_greeting']}")
    print()

    # Test 8: Different timezones
    print("📍 Test 8: Different Timezones")
    print("-" * 70)
    print(f"Bangkok time: {clock.format_datetime(tz='Asia/Bangkok')}")
    print(f"UTC time: {clock.format_datetime(tz='UTC')}")
    print(f"New York time: {clock.format_datetime(tz='America/New_York')}")
    print()

    print("="*70)
    print("✅ All Clock Service tests completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_clock_service()
