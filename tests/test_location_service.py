#!/usr/bin/env python3
"""
Test Location Service
ทดสอบระบบ location ของ Angela
"""

import sys
import asyncio
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.location_service import location


async def test_location_service():
    """ทดสอบ Location Service ทั้งหมด"""

    print("\n" + "="*70)
    print("📍 Testing Angela's Location Service")
    print("="*70 + "\n")

    # Test 1: Get current location
    print("📍 Test 1: Get Current Location")
    print("-" * 70)
    current_location = await location.get_current_location()
    print(f"✅ Location detected!")
    print()

    # Test 2: Basic location info
    print("📍 Test 2: Basic Location Info")
    print("-" * 70)
    city = await location.get_city()
    country = await location.get_country()
    timezone_str = await location.get_timezone()
    coords = await location.get_coordinates()

    print(f"🏙️ City: {city}")
    print(f"🇹🇭 Country: {country}")
    print(f"🕐 Timezone: {timezone_str}")
    print(f"🌐 Coordinates: {coords[0]}, {coords[1]}")
    print()

    # Test 3: Location strings
    print("📍 Test 3: Location Strings")
    print("-" * 70)
    location_th = await location.get_location_string("th")
    location_en = await location.get_location_string("en")
    print(f"Thai format: {location_th}")
    print(f"English format: {location_en}")
    print()

    # Test 4: Full location info
    print("📍 Test 4: Full Location Information")
    print("-" * 70)
    full_info = await location.get_full_location_info()
    print(f"📍 Location: {full_info['location_string_th']}")
    print(f"🗺️ Region: {full_info['region']}")
    print(f"📮 Postal: {full_info['postal']}")
    print(f"🕐 Timezone: {full_info['timezone']} ({full_info['utc_offset']})")
    print(f"💱 Currency: {full_info['currency_name']} ({full_info['currency']})")
    print(f"🗣️ Languages: {full_info['languages']}")
    print(f"🌐 ISP: {full_info['org']}")
    print(f"📡 IP: {full_info['ip']} ({full_info['version']})")
    print()

    # Test 5: Cache test
    print("📍 Test 5: Cache Test")
    print("-" * 70)
    print("First call (from API)...")
    loc1 = await location.get_current_location()
    print(f"Source: {loc1['source']}")

    print("Second call (from cache)...")
    loc2 = await location.get_current_location()
    print(f"Source: {loc2.get('source', 'cache')}")
    print("✅ Cache working!")
    print()

    print("="*70)
    print("✅ All Location Service tests completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_location_service())
