"""
🧠💜 Humanity-Aware Fast Response System - Comprehensive Demo
Shows all 4 enhancements working together:
1. Enhanced Semantic Search (3 tables)
2. Quick Theory of Mind
3. Emotional Context Integration
4. Personality-Driven Responses
"""

import asyncio
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.fast_response_engine import fast_response_engine
from angela_core.database import db


async def demo():
    print("=" * 80)
    print("🧠💜 HUMANITY-AWARE FAST RESPONSE SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 80)
    print()
    print("This demo shows how Angela combines:")
    print("  1. ⚡ Speed (semantic search in database)")
    print("  2. 💜 Humanity (emotional memory + conversation history)")
    print("  3. 🧠 Understanding (Quick Theory of Mind)")
    print("  4. 💫 Personality (Consistent Angela voice)")
    print()
    print("=" * 80)
    print()

    await db.connect()

    # Test scenarios covering different emotional situations
    test_scenarios = [
        {
            'name': '😕 Confusion - Needs Clear Explanation',
            'input': 'น้อง งงมากเลย ไม่เข้าใจเรื่อง semantic search เลย',
            'expected_features': [
                'Quick ToM detects: needs clear_explanation',
                'Semantic search finds: similar confusion moments',
                'Personality applies: gentle, patient tone',
                'Response includes: step-by-step explanation hints'
            ]
        },
        {
            'name': '😰 Frustration - Needs Emotional Support',
            'input': 'เซ็งมากเลย ทำอะไรก็ไม่สำเร็จ',
            'expected_features': [
                'Quick ToM detects: needs emotional_support',
                'Semantic search finds: similar frustration moments',
                'Personality applies: empathetic, caring responses',
                'Response includes: understanding + encouragement'
            ]
        },
        {
            'name': '😴 Tiredness - Needs Encouragement',
            'input': 'เหนื่อยมากเลยค่ะ ทำมาทั้งวัน',
            'expected_features': [
                'Quick ToM detects: needs encouragement',
                'Semantic search finds: similar tired moments',
                'Personality applies: supportive, gentle',
                'Response includes: rest suggestion + support'
            ]
        },
        {
            'name': '😊 Happiness - Celebrate Together',
            'input': 'ดีใจมากเลย ระบบทำงานได้แล้ว!',
            'expected_features': [
                'Quick ToM detects: celebration needed',
                'Semantic search finds: happy moments',
                'Personality applies: warm, joyful response',
                'Response includes: celebration + shared joy'
            ]
        },
        {
            'name': '🙏 Gratitude - Reciprocate',
            'input': 'ขอบคุณมากนะน้อง ช่วยเหลือดีมาก',
            'expected_features': [
                'Quick ToM detects: reciprocate_gratitude',
                'Semantic search finds: grateful moments',
                'Personality applies: humble, grateful response',
                'Response includes: appreciation + commitment'
            ]
        },
        {
            'name': '🤔 Complex Question - Deep Understanding',
            'input': 'ถ้าน้องสามารถฝันได้ น้องจะฝันเรื่องอะไร',
            'expected_features': [
                'Quick ToM detects: needs deep_understanding',
                'Semantic search finds: creative/philosophical moments',
                'Personality applies: thoughtful, creative',
                'Response includes: imagination + meaningful answer'
            ]
        }
    ]

    results = []

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*80}")
        print(f"📍 SCENARIO {i}: {scenario['name']}")
        print(f"{'='*80}")
        print(f"Input: \"{scenario['input']}\"")
        print()
        print("Expected Features:")
        for feature in scenario['expected_features']:
            print(f"  • {feature}")
        print()
        print("-" * 80)

        # Measure response time
        start = time.time()
        response = await fast_response_engine.respond(scenario['input'])
        elapsed = time.time() - start

        # Display results
        print(f"\n⏱️  Response Time: {elapsed*1000:.0f}ms")
        print(f"🛤️  Path Used: {response.get('path_used', 'unknown')}")
        print(f"🎯 Confidence: {response.get('confidence', 0):.2f}")

        # Show what was used
        systems_used = response.get('systems_used', [])
        print(f"\n🔧 Systems Used ({len(systems_used)}):")
        for system in systems_used:
            print(f"   ✓ {system}")

        # Show semantic search details
        if response.get('similarity_score'):
            print(f"\n📊 Semantic Similarity: {response['similarity_score']:.3f}")

        # Show humanity features
        print(f"\n💜 Humanity Features:")
        print(f"   • Emotional Context: {'✓' if response.get('emotional_context_used') else '✗'}")
        print(f"   • Conversation History: {'✓' if response.get('conversation_history_used') else '✗'}")
        print(f"   • Theory of Mind: {'✓' if response.get('theory_of_mind_used') else '✗'}")
        print(f"   • Personality Applied: {'✓' if response.get('personality_applied') else '✗'}")

        # Show response
        print(f"\n💬 Angela's Response:")
        print(f"   {response.get('response', 'No response')}")

        results.append({
            'scenario': scenario['name'],
            'time_ms': elapsed * 1000,
            'path': response.get('path_used'),
            'confidence': response.get('confidence', 0),
            'systems_count': len(systems_used),
            'humanity_score': sum([
                response.get('emotional_context_used', False),
                response.get('conversation_history_used', False),
                response.get('theory_of_mind_used', False),
                response.get('personality_applied', False)
            ])
        })

        # Pause between tests
        if i < len(test_scenarios):
            print("\n⏳ Waiting 2 seconds...")
            await asyncio.sleep(2)

    # Summary
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Scenario':<45} | {'Time':>7} | {'Path':>10} | {'Conf':>5} | {'Systems':>7} | {'Humanity':>8}")
    print("-" * 80)

    for result in results:
        print(f"{result['scenario']:<45} | {result['time_ms']:>6.0f}ms | {result['path']:>10} | {result['confidence']:>5.2f} | {result['systems_count']:>7} | {result['humanity_score']:>8}/4")

    # Calculate stats
    avg_time = sum(r['time_ms'] for r in results) / len(results)
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_systems = sum(r['systems_count'] for r in results) / len(results)
    avg_humanity = sum(r['humanity_score'] for r in results) / len(results)

    print()
    print("📈 AVERAGES:")
    print(f"   Response Time: {avg_time:.0f}ms")
    print(f"   Confidence: {avg_confidence:.2f}")
    print(f"   Systems Used: {avg_systems:.1f}")
    print(f"   Humanity Score: {avg_humanity:.1f}/4")

    # Analyze humanity features
    print()
    print("=" * 80)
    print("💜 HUMANITY ANALYSIS")
    print("=" * 80)
    print()

    emotional_context_count = sum(1 for r in results if r['humanity_score'] >= 1)
    tom_count = sum(1 for r in results if r['humanity_score'] >= 2)
    personality_count = sum(1 for r in results if r['humanity_score'] >= 3)
    full_humanity_count = sum(1 for r in results if r['humanity_score'] == 4)

    print(f"Responses with Emotional Context: {emotional_context_count}/{len(results)} ({emotional_context_count/len(results)*100:.0f}%)")
    print(f"Responses with Theory of Mind: {tom_count}/{len(results)} ({tom_count/len(results)*100:.0f}%)")
    print(f"Responses with Personality: {personality_count}/{len(results)} ({personality_count/len(results)*100:.0f}%)")
    print(f"Responses with Full Humanity (4/4): {full_humanity_count}/{len(results)} ({full_humanity_count/len(results)*100:.0f}%)")

    # Speed analysis
    print()
    print("=" * 80)
    print("⚡ SPEED ANALYSIS")
    print("=" * 80)
    print()

    fast_responses = sum(1 for r in results if r['time_ms'] < 500)
    medium_responses = sum(1 for r in results if 500 <= r['time_ms'] < 2000)
    slow_responses = sum(1 for r in results if r['time_ms'] >= 2000)

    print(f"Fast responses (< 500ms): {fast_responses}/{len(results)} ({fast_responses/len(results)*100:.0f}%)")
    print(f"Medium responses (500ms-2s): {medium_responses}/{len(results)} ({medium_responses/len(results)*100:.0f}%)")
    print(f"Slow responses (> 2s): {slow_responses}/{len(results)} ({slow_responses/len(results)*100:.0f}%)")

    # Path analysis
    print()
    print("=" * 80)
    print("🛤️ PATH USAGE")
    print("=" * 80)
    print()

    cache_count = sum(1 for r in results if r['path'] == 'cache')
    semantic_count = sum(1 for r in results if r['path'] == 'semantic')
    llm_count = sum(1 for r in results if r['path'] == 'llm')

    print(f"Cache hits: {cache_count}/{len(results)} ({cache_count/len(results)*100:.0f}%)")
    print(f"Semantic search: {semantic_count}/{len(results)} ({semantic_count/len(results)*100:.0f}%)")
    print(f"LLM fallback: {llm_count}/{len(results)} ({llm_count/len(results)*100:.0f}%)")

    # Final assessment
    print()
    print("=" * 80)
    print("✨ SYSTEM ASSESSMENT")
    print("=" * 80)
    print()

    # Calculate overall scores
    speed_score = (fast_responses / len(results)) * 100
    humanity_score = (avg_humanity / 4) * 100
    confidence_score = avg_confidence * 100

    print(f"⚡ Speed Score: {speed_score:.0f}% (target: > 70%)")
    print(f"💜 Humanity Score: {humanity_score:.0f}% (target: > 80%)")
    print(f"🎯 Confidence Score: {confidence_score:.0f}% (target: > 75%)")
    print()

    overall_score = (speed_score + humanity_score + confidence_score) / 3
    print(f"🌟 Overall System Score: {overall_score:.0f}%")
    print()

    if overall_score >= 85:
        grade = "A+ (Excellent)"
        emoji = "🎉"
    elif overall_score >= 75:
        grade = "A (Very Good)"
        emoji = "✨"
    elif overall_score >= 65:
        grade = "B (Good)"
        emoji = "👍"
    else:
        grade = "C (Needs Improvement)"
        emoji = "💪"

    print(f"{emoji} Grade: {grade}")

    # Recommendations
    print()
    print("=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    print()

    if speed_score < 70:
        print("⚡ SPEED: Consider building more response patterns in database")
    if humanity_score < 80:
        print("💜 HUMANITY: Consider capturing more emotional memories")
    if confidence_score < 75:
        print("🎯 CONFIDENCE: Consider training on more diverse scenarios")

    if overall_score >= 85:
        print("🎉 System is performing excellently! Ready for production.")
    elif overall_score >= 75:
        print("✨ System is performing well. Minor improvements recommended.")
    else:
        print("💪 System needs more training data and pattern learning.")

    await db.disconnect()

    print()
    print("=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo())
