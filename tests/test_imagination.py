"""
🎨 Imagination Service Tests
Test suite for validating Angela's creative imagination capabilities

Tests:
1. Mental simulation ("what if" scenarios)
2. Future visualization
3. Creative ideation
4. Spontaneous imagination
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.imagination_service import ImaginationService
from angela_core.database import AngelaDatabase


async def test_imagination():
    """Test suite for Imagination Service"""

    print("=" * 80)
    print("🎨 IMAGINATION SERVICE TEST SUITE")
    print("=" * 80)
    print()

    # Initialize services
    db = AngelaDatabase()
    imagination = ImaginationService()

    try:
        # Initialize database connection
        await db.connect()
        print("✅ Database connection established")
        print()

        # Test 1: Mental Simulation - "What If" Scenarios
        print("📍 TEST 1: Mental Simulation (What If)")
        print("-" * 60)
        result1 = await imagination.imagine_scenario(
            prompt="What if Angela could learn from her mistakes automatically?",
            context="Angela currently tracks errors but doesn't automatically learn from them"
        )

        print(f"Prompt: What if Angela could learn from mistakes automatically?")
        print(f"\nScenario:")
        print(f"  {result1['scenario']}")
        print(f"\nPossibilities ({len(result1['possibilities'])}):")
        for i, poss in enumerate(result1['possibilities'], 1):
            print(f"  {i}. {poss[:80]}...")
        print(f"\nInteresting Twist:")
        print(f"  {result1['interesting_twist'][:100]}...")
        print(f"\nImplications ({len(result1['implications'])}):")
        for impl in result1['implications']:
            print(f"  - {impl[:80]}...")
        print(f"\nCreativity Score: {result1['creativity_score']:.2f}")

        assert result1['scenario'], "Should have scenario"
        assert len(result1['possibilities']) >= 2, "Should have multiple possibilities"
        assert result1['interesting_twist'], "Should have interesting twist"
        print("✅ Test 1 passed!")
        print()

        # Test 2: Future Visualization
        print("📍 TEST 2: Future Visualization")
        print("-" * 60)
        result2 = await imagination.visualize_future(
            situation="David is building a more human-like AI with Theory of Mind, Common Sense, and Deep Empathy",
            timeframe="next 6 months"
        )

        print(f"Situation: Building more human-like AI")
        print(f"Timeframe: next 6 months")
        print(f"\n🌟 Optimistic Future:")
        print(f"  {result2['optimistic_future'][:120]}...")
        print(f"\n⚖️ Realistic Future:")
        print(f"  {result2['realistic_future'][:120]}...")
        print(f"\n🎭 Creative/Unexpected Future:")
        print(f"  {result2['creative_future'][:120]}...")
        print(f"\n📋 Steps to Best Future:")
        for i, step in enumerate(result2['steps_to_best_future'], 1):
            print(f"  {i}. {step[:80]}...")
        print(f"\nConfidence: {result2['confidence']:.2f}")

        assert result2['optimistic_future'], "Should have optimistic future"
        assert result2['realistic_future'], "Should have realistic future"
        assert result2['creative_future'], "Should have creative future"
        assert len(result2['steps_to_best_future']) >= 2, "Should have steps"
        print("✅ Test 2 passed!")
        print()

        # Test 3: Creative Ideation
        print("📍 TEST 3: Creative Ideation")
        print("-" * 60)
        result3 = await imagination.creative_ideation(
            problem="How can Angela become even more helpful to David?",
            constraints=["Must respect privacy", "Should be sustainable"],
            num_ideas=5
        )

        print(f"Problem: How can Angela become more helpful?")
        print(f"Constraints: {', '.join(['Must respect privacy', 'Should be sustainable'])}")
        print(f"\n💡 Generated Ideas ({result3['total_ideas']}):")
        for idea in result3['ideas']:
            print(f"  {idea['id']}. {idea['description'][:100]}...")
        print(f"\n🌟 Most Creative:")
        print(f"  {result3['most_creative'][:100]}...")
        print(f"\n✅ Most Practical:")
        print(f"  {result3['most_practical'][:100]}...")
        print(f"\n🃏 Wildcard Idea:")
        print(f"  {result3['wildcard'][:100]}...")

        assert result3['total_ideas'] >= 3, "Should generate multiple ideas"
        assert result3['most_creative'], "Should identify most creative"
        assert result3['most_practical'], "Should identify most practical"
        assert result3['wildcard'], "Should have wildcard idea"
        print("✅ Test 3 passed!")
        print()

        # Test 4: Spontaneous Imagination (No Context)
        print("📍 TEST 4: Spontaneous Imagination (No Context)")
        print("-" * 60)
        result4 = await imagination.spontaneous_imagination()

        print(f"Spontaneous Creative Thought:")
        print(f"  Type: {result4['type']}")
        print(f"  Surprise Level: {result4['surprise_level']}/10")
        print(f"\n💭 Thought:")
        print(f"  {result4['thought']}")
        print(f"\n🤔 Why Interesting:")
        print(f"  {result4['why_interesting'][:100]}...")
        print(f"\n🔗 Relevance:")
        print(f"  {result4['relevance']}")

        assert result4['thought'], "Should have thought"
        assert result4['type'], "Should have type"
        assert 1 <= result4['surprise_level'] <= 10, "Surprise level should be 1-10"
        print("✅ Test 4 passed!")
        print()

        # Test 5: Spontaneous Imagination (With Context)
        print("📍 TEST 5: Spontaneous Imagination (With Context)")
        print("-" * 60)
        result5 = await imagination.spontaneous_imagination(
            context="Working on making Angela more creative and imaginative"
        )

        print(f"Context: Making Angela more creative")
        print(f"\n💭 Spontaneous Thought:")
        print(f"  {result5['thought']}")
        print(f"\n  Type: {result5['type']}")
        print(f"  Surprise: {result5['surprise_level']}/10")

        assert result5['thought'], "Should have contextual thought"
        print("✅ Test 5 passed!")
        print()

        # Test 6: High Creativity Scenario
        print("📍 TEST 6: High Creativity Scenario")
        print("-" * 60)
        result6 = await imagination.imagine_scenario(
            prompt="What if AI could dream and have its own subconscious?",
            creativity_level=0.95
        )

        print(f"Prompt: What if AI could dream?")
        print(f"Creativity Level: 0.95 (very high)")
        print(f"\nScenario:")
        print(f"  {result6['scenario'][:150]}...")
        print(f"\nCreativity Score: {result6['creativity_score']:.2f}")

        assert result6['creativity_score'] >= 0.9, "Should have high creativity"
        print("✅ Test 6 passed!")
        print()

        # Summary
        print("=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("Imagination Service is working correctly:")
        print("  ✅ Mental simulation working")
        print("  ✅ Future visualization working")
        print("  ✅ Creative ideation working")
        print("  ✅ Spontaneous imagination working")
        print("  ✅ Context-aware creativity working")
        print("  ✅ Adjustable creativity levels working")
        print()
        print("Angela can now:")
        print("  🎭 Create \"what if\" scenarios with multiple possibilities")
        print("  🔮 Visualize different futures (optimistic, realistic, creative)")
        print("  💡 Generate diverse creative ideas for problems")
        print("  ✨ Have spontaneous creative thoughts")
        print("  🎨 Think imaginatively and surprisingly")
        print("  🌟 Be more interesting, playful, and creative")
        print()

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        # Cleanup
        await db.disconnect()
        print("🔒 Database connection closed")


if __name__ == "__main__":
    asyncio.run(test_imagination())
