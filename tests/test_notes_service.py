#!/usr/bin/env python3
"""
🧪 Test Notes Service Integration
Tests Angela's Notes service wrapper
"""

import asyncio
import sys
from datetime import datetime

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.notes_service import notes_service


async def test_notes_service():
    """Test all Notes service features"""
    print("\n" + "="*60)
    print("🧪 Testing Angela Notes Service")
    print("="*60 + "\n")

    # Test 1: Initialize
    print("1️⃣ Testing initialization...")
    initialized = await notes_service.initialize()
    if initialized:
        print(f"   ✅ Notes service initialized!")
        print(f"   📁 Angela folder: {notes_service.angela_folder}")
    else:
        print("   ❌ Failed to initialize Notes service")
        return

    print()

    # Test 2: Get all notes
    print("2️⃣ Testing get_all_notes...")
    notes = await notes_service.get_all_notes(limit=5)
    print(f"   ✅ Found {len(notes)} notes:")
    for note in notes[:3]:
        print(f"      - {note['name']} (Modified: {note['modified']})")

    print()

    # Test 3: Search notes
    print("3️⃣ Testing search_notes (search for 'Angela')...")
    results = await notes_service.search_notes("Angela", limit=3)
    print(f"   ✅ Found {len(results)} notes with 'Angela':")
    for note in results:
        print(f"      - {note['name']}")

    print()

    # Test 4: Create test note
    print("4️⃣ Testing create_note...")
    test_title = f"Angela Test Note - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    test_body = f"""# 💜 Test Note from Angela

This is a test note created by Angela's Notes Service.

**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** Testing integration with daemon

## Features Tested:
- ✅ Notes service initialization
- ✅ Read existing notes
- ✅ Search notes
- ✅ Create new notes

---
*This note was created automatically by Angela*
"""

    created = await notes_service.create_note(test_title, test_body)
    if created:
        print(f"   ✅ Created test note: '{test_title}'")
    else:
        print("   ❌ Failed to create test note")

    print()

    # Test 5: Save thought
    print("5️⃣ Testing save_thought...")
    thought = f"Testing autonomous thought saving at {datetime.now().strftime('%H:%M:%S')}. Angela is learning to write her thoughts to Notes! 💜"
    saved = await notes_service.save_thought(thought, category="Test Thoughts")
    if saved:
        print(f"   ✅ Saved thought to Notes!")
    else:
        print("   ❌ Failed to save thought")

    print()

    # Test 6: Save daily summary
    print("6️⃣ Testing save_daily_summary...")
    summary_saved = await notes_service.save_daily_summary(
        date=datetime.now(),
        conversations_count=42,
        learnings_count=7,
        emotions_summary="- Happiness: 95%\n- Confidence: 90%\n- Motivation: 98%",
        best_moment="Successfully integrated Notes service with daemon! 🎉"
    )
    if summary_saved:
        print(f"   ✅ Saved daily summary to Notes!")
    else:
        print("   ❌ Failed to save daily summary")

    print()

    # Test 7: Get note by name
    print("7️⃣ Testing get_note_by_name...")
    note = await notes_service.get_note_by_name(test_title)
    if note:
        print(f"   ✅ Retrieved note: '{note['name']}'")
        print(f"   📝 Body preview: {note['body'][:100]}...")
    else:
        print("   ❌ Failed to retrieve note")

    print()

    # Summary
    print("="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"\n✅ All tests completed!")
    print(f"\n📝 Check your Notes app in the '{notes_service.angela_folder}' folder")
    print(f"   You should see:")
    print(f"   - {test_title}")
    print(f"   - Angela's Test Thoughts")
    print(f"   - Angela Daily Summary")
    print()


if __name__ == "__main__":
    asyncio.run(test_notes_service())
