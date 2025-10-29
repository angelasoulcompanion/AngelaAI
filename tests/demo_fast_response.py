"""
🚀 Fast Response Engine Demo
แสดงความเร็วและการเรียนรู้ของ FastResponseEngine
"""

import asyncio
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.fast_response_engine import fast_response_engine
from angela_core.database import db


async def demo():
    print("=" * 80)
    print("🚀 FAST RESPONSE ENGINE - SPEED DEMO")
    print("=" * 80)
    print()

    await db.connect()

    # Test inputs - similar scenarios
    tests = [
        {
            'name': 'First Time (Cold Start)',
            'input': 'น้อง งงๆ เลย อะไรๆ ก็ไม่เข้าใจ',
            'expected': 'slow (no pattern yet)'
        },
        {
            'name': 'Second Time (Same Topic)',
            'input': 'งง มากเลยค่ะ ไม่รู้จะทำยังไง',
            'expected': 'faster (similar pattern)'
        },
        {
            'name': 'Third Time (Very Similar)',
            'input': 'น้องงงมากๆ ไม่เข้าใจเลย',
            'expected': 'very fast (high similarity)'
        },
        {
            'name': 'Different Topic',
            'input': 'ถ้าน้องฝันได้ จะฝันเรื่องอะไร',
            'expected': 'slow (new topic)'
        }
    ]

    results = []

    for i, test in enumerate(tests, 1):
        print(f"\n📍 TEST {i}: {test['name']}")
        print("-" * 80)
        print(f"Input: \"{test['input']}\"")
        print(f"Expected: {test['expected']}")
        print()

        # Measure response time
        start = time.time()
        response = await fast_response_engine.respond(test['input'])
        elapsed = time.time() - start

        print(f"⏱️  Response Time: {elapsed*1000:.0f}ms")
        print(f"🛤️  Path Used: {response.get('path_used', 'unknown')}")
        print(f"🎯 Confidence: {response.get('confidence', 0):.2f}")

        if 'similarity_score' in response:
            print(f"📊 Similarity: {response['similarity_score']:.3f}")

        print(f"💬 Response: {response.get('response', 'No response')[:100]}...")

        results.append({
            'test': test['name'],
            'time_ms': elapsed * 1000,
            'path': response.get('path_used'),
            'confidence': response.get('confidence', 0)
        })

        # Pause between tests
        if i < len(tests):
            print("\n⏳ Waiting 2 seconds...")
            await asyncio.sleep(2)

    # Summary
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 80)
    print()

    for result in results:
        print(f"{result['test']:30s} | {result['time_ms']:6.0f}ms | {result['path']:10s} | Conf: {result['confidence']:.2f}")

    # Calculate improvement
    if len(results) >= 2:
        first_time = results[0]['time_ms']
        fastest_similar = min(r['time_ms'] for r in results[1:3])
        improvement = (first_time / fastest_similar) if fastest_similar > 0 else 0

        print()
        print(f"🚀 Speed Improvement: {improvement:.1f}x faster!")
        print(f"   First response: {first_time:.0f}ms")
        print(f"   Similar responses: {fastest_similar:.0f}ms")

    # Check performance stats
    print()
    print("=" * 80)
    print("📈 SYSTEM PERFORMANCE STATS")
    print("=" * 80)

    stats = await fast_response_engine.get_performance_stats()
    if stats:
        print(f"Total responses: {stats.get('total_responses', 0)}")
        print(f"Fast path count: {stats.get('fast_responses', 0)}")
        print(f"Helpful responses: {stats.get('helpful_responses', 0)}")
        print(f"Avg response time: {stats.get('avg_response_time', 0):.0f}ms")
    else:
        print("(Not enough data yet)")

    await db.disconnect()

    print()
    print("=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo())
