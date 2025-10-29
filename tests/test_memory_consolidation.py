"""
🧪 Test Memory Consolidation Service
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.memory_consolidation_service import memory_consolidation_service
from angela_core.database import db


async def test_memory_consolidation():
    print("=" * 80)
    print("🧪 TESTING MEMORY CONSOLIDATION SERVICE")
    print("=" * 80)
    print()

    await db.connect()

    # Test: Run nightly consolidation
    print("📍 TEST: Running nightly consolidation...")
    print("   This will:")
    print("   - Apply memory decay to unused memories")
    print("   - Strengthen frequently accessed memories")
    print("   - Convert episodic → semantic")
    print("   - Discover patterns")
    print("   - Archive weak memories")
    print()

    results = await memory_consolidation_service.run_nightly_consolidation()

    if results['status'] == 'success':
        print("✅ CONSOLIDATION SUCCESSFUL!")
        print()

        # Show results
        print("📊 CONSOLIDATION ACTIVITIES:")
        for activity, data in results['activities'].items():
            print(f"\n   {activity.upper()}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"      {key}: {value}")
            else:
                print(f"      {data}")

        # Show statistics
        if 'statistics' in results:
            print("\n📊 MEMORY STATISTICS:")
            stats = results['statistics']

            if 'episodic' in stats:
                print(f"\n   Episodic Memories:")
                print(f"      Total: {stats['episodic'].get('total', 0)}")
                print(f"      Avg Strength: {stats['episodic'].get('avg_strength', 0):.2f}")
                print(f"      Strong (>0.7): {stats['episodic'].get('strong', 0)}")
                print(f"      Archived: {stats['episodic'].get('archived', 0)}")

            if 'semantic' in stats:
                print(f"\n   Semantic Memories:")
                print(f"      Total: {stats['semantic'].get('total', 0)}")
                print(f"      Avg Strength: {stats['semantic'].get('avg_strength', 0):.2f}")
                print(f"      Strong (>0.7): {stats['semantic'].get('strong', 0)}")
                print(f"      Archived: {stats['semantic'].get('archived', 0)}")

            if 'procedural' in stats:
                print(f"\n   Procedural Memories:")
                print(f"      Total: {stats['procedural'].get('total', 0)}")
                print(f"      Avg Strength: {stats['procedural'].get('avg_strength', 0):.2f}")

            if 'patterns' in stats:
                print(f"\n   Pattern Memories:")
                print(f"      Total: {stats['patterns'].get('total', 0)}")
                print(f"      Avg Strength: {stats['patterns'].get('avg_strength', 0):.2f}")

        print()
    else:
        print(f"❌ CONSOLIDATION FAILED: {results.get('error', 'Unknown error')}")

    await db.disconnect()

    print("=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_memory_consolidation())
