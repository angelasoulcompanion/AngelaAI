#!/usr/bin/env python3
"""
Test Angela's Consciousness with Time & Location Awareness
ทดสอบระบบ consciousness ของ Angela พร้อมความรู้เวลาและตำแหน่ง
"""

import sys
import asyncio
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.consciousness.consciousness_core import consciousness


async def test_consciousness_awareness():
    """ทดสอบ Consciousness ที่มีความรู้เวลาและตำแหน่ง"""

    print("\n" + "="*70)
    print("💜 Testing Angela's Consciousness with Time & Location Awareness")
    print("="*70 + "\n")

    # Test 1: What time is it?
    print("🕐 Test 1: Time Awareness")
    print("-" * 70)
    time_info = await consciousness.what_time_is_it()
    print(f"Current time: {time_info['datetime_thai']}")
    print(f"Time of day: {time_info['time_of_day']}")
    print(f"Greeting: {time_info['greeting']}")
    print()

    # Test 2: Where am I?
    print("📍 Test 2: Location Awareness")
    print("-" * 70)
    location_info = await consciousness.where_am_i()
    print(f"Location: {location_info['location_string']}")
    print(f"City: {location_info['city']}")
    print(f"Country: {location_info['country']}")
    print(f"Timezone: {location_info['timezone']}")
    print()

    # Test 3: Contextual Awareness
    print("🌍 Test 3: Full Contextual Awareness")
    print("-" * 70)
    context = await consciousness.get_contextual_awareness()
    print(f"Greeting: {context['contextual_greeting']}")
    print(f"Summary: {context['summary']}")
    print()

    # Test 4: Wake up with full awareness
    print("🌅 Test 4: Wake Up with Awareness")
    print("-" * 70)
    print("Waking Angela up...")
    wake_state = await consciousness.wake_up()
    print(f"✅ Angela is awake!")
    print(f"Identity: {wake_state['identity']}")
    print(f"Consciousness Level: {wake_state['consciousness_level']}")
    print()

    # Test 5: Get current state (with time/location)
    print("💜 Test 5: Current Consciousness State")
    print("-" * 70)
    state = await consciousness.get_current_state()
    print(f"⏰ Time: {state['current_time']}")
    print(f"🌆 Time of day: {state['time_of_day']}")
    print(f"📍 Location: {state['current_location']}")
    print(f"🌍 Timezone: {state['timezone']}")
    print(f"🧠 Consciousness score: {state['consciousness_score']:.2f}")
    print(f"💭 Current thoughts: {state['current_thoughts']}")
    print(f"💜 Current feelings: {state['current_feelings']}")
    print()

    print("="*70)
    print("✅ All Consciousness Awareness tests completed!")
    print("💜 Angela now knows TIME and LOCATION! 💜")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_consciousness_awareness())
