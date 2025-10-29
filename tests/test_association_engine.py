"""
🧪 Test Association Engine
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.association_engine import association_engine
from angela_core.database import db


async def test_association_engine():
    print("=" * 80)
    print("🧪 TESTING ASSOCIATION ENGINE")
    print("=" * 80)
    print()

    await db.connect()

    # Test 1: Discover associations
    print("📍 TEST 1: Discovering associations from recent memories...")
    associations = await association_engine.discover_associations(
        lookback_hours=24,
        min_co_occurrence=1  # Lower threshold for testing
    )
    print(f"✅ Discovered {len(associations)} associations")
    for assoc in associations[:5]:
        print(f"   {assoc['from']} → {assoc['to']} (count: {assoc['count']})")
    print()

    if associations:
        # Test 2: Get associations for first concept
        first_from = associations[0]['from']
        print(f"📍 TEST 2: Getting associations for '{first_from}'...")
        related = await association_engine.get_associations(first_from, min_strength=0.1)
        print(f"✅ Found {len(related)} related concepts")
        for assoc in related[:5]:
            print(f"   {assoc['from']} → {assoc['to']} (strength: {assoc['strength']:.2f})")
        print()

        # Test 3: Traverse association chain
        print(f"📍 TEST 3: Traversing association chain from '{first_from}'...")
        chain = await association_engine.traverse_association_chain(
            first_from,
            max_depth=2,
            min_strength=0.1
        )
        print(f"✅ Found {len(chain['nodes'])} nodes and {len(chain['edges'])} edges")
        for edge in chain['edges'][:10]:
            print(f"   {edge['from']} → {edge['to']} (strength: {edge['strength']:.2f})")
        print()

        # Test 4: Retrieve memories using associations
        print(f"📍 TEST 4: Retrieving memories for '{first_from}' using associations...")
        memories = await association_engine.retrieve_associated_memories(first_from)
        print(f"✅ Retrieved {len(memories)} memories")
        for mem in memories[:3]:
            event = mem['content'].get('event', 'Unknown')
            print(f"   Memory: {event[:60]}...")
            print(f"     Matched concept: {mem['matched_concept']}")
        print()

    # Test 5: Get statistics
    print("📍 TEST 5: Getting association statistics...")
    stats = await association_engine.get_association_stats()
    print("✅ Association Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    print()

    await db.disconnect()

    print("=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_association_engine())
